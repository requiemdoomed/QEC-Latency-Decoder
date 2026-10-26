"""
bit_flip_code.py - Weekend 2, Experiment 2.1
The 3-qubit bit-flip code, two ancillas for the syndrome, and a look-up-table
(LUT) decoder that I time on every cycle.
Author: Swayam Shakya

Encoding:   |0>_L = |000>,  |1>_L = |111>
Syndrome:   ancilla 1 measures the Z0*Z1 parity, ancilla 0 measures Z1*Z2.

The bit order tripped me up for a while. Qiskit prints classical bits right to
left, so the 2-character syndrome string reads (Z0Z1)(Z1Z2):

    '00' no error   '10' flip qubit 0   '11' flip qubit 1   '01' flip qubit 2

Each cycle is a full noisy simulation (one shot), but the stopwatch only
runs around the decode step itself: syndrome string in, correction out,
timed with time.perf_counter_ns().

Writes: w2_latencies.json
"""
import json
import time
from typing import Optional, Tuple

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error


class BitFlipCode:
    """3-qubit bit-flip code. It can fix any single X error on the data qubits."""

    SYNDROME_TABLE = {
        '00': None,   # nothing to fix
        '10': 0,      # data qubit 0 flipped
        '11': 1,      # data qubit 1 flipped
        '01': 2,      # data qubit 2 flipped
    }

    def __init__(self, t1_us: float = 250.0, t2_us: float = 120.0,
                 gate_ns: float = 50.0, cx_ns: float = 500.0,
                 seed: Optional[int] = None):
        self.t1_ns = t1_us * 1e3
        self.t2_ns = t2_us * 1e3
        self.gate_ns = gate_ns
        self.cx_ns = cx_ns
        self._sim = AerSimulator(noise_model=self._build_noise_model())
        # Every cycle gets its own simulator seed drawn from this generator.
        # With one fixed seed, Aer would replay the exact same noise each cycle.
        self._rng = np.random.default_rng(seed)
        self._cache = {}

    def _build_noise_model(self) -> NoiseModel:
        nm = NoiseModel()
        err_1q = thermal_relaxation_error(self.t1_ns, self.t2_ns, self.gate_ns)
        nm.add_all_qubit_quantum_error(err_1q, ['id', 'x', 'h'])
        # CNOTs are slow (500 ns), so both qubits relax independently for that long
        err_q = thermal_relaxation_error(self.t1_ns, self.t2_ns, self.cx_ns)
        nm.add_all_qubit_quantum_error(err_q.expand(err_q), ['cx'])
        return nm

    def encode(self, logical_state: str = '0') -> QuantumCircuit:
        """Data qubits q[0:3] in |000> or |111>."""
        if logical_state not in ('0', '1'):
            raise ValueError("logical_state must be '0' or '1'")
        qd = QuantumRegister(3, 'q')
        qc = QuantumCircuit(qd)
        if logical_state == '1':
            qc.x(qd[0])
        qc.cx(qd[0], qd[1])
        qc.cx(qd[0], qd[2])
        return qc

    @staticmethod
    def inject_error(qc: QuantumCircuit, qubit: int) -> QuantumCircuit:
        """Flip one data qubit on purpose (an X gate) to fake a bit-flip error."""
        if qubit not in (0, 1, 2):
            raise ValueError(f"qubit must be 0, 1 or 2; got {qubit}")
        qc.x(qc.qregs[0][qubit])
        return qc

    @staticmethod
    def syndrome_circuit(qc: QuantumCircuit) -> QuantumCircuit:
        """Add the two parity checks. Only the ancillas get measured, so a
        superposition of |000> and |111> would survive the check."""
        qd = qc.qregs[0]
        qa = QuantumRegister(2, 'anc')
        cr = ClassicalRegister(2, 'syn')
        qc.add_register(qa)
        qc.add_register(cr)
        qc.cx(qd[0], qa[1])    # ancilla 1 picks up Z0*Z1
        qc.cx(qd[1], qa[1])
        qc.cx(qd[1], qa[0])    # ancilla 0 picks up Z1*Z2
        qc.cx(qd[2], qa[0])
        qc.measure(qa, cr)
        return qc

    def decode_syndrome(self, syndrome_str: str) -> Optional[int]:
        """The whole decoder: one dictionary lookup. Returns the qubit to flip or None."""
        return self.SYNDROME_TABLE[syndrome_str]

    def _circuit(self, logical_state: str, inject_qubit: Optional[int]) -> QuantumCircuit:
        # only 8 different circuits exist, so build each one once
        key = (logical_state, inject_qubit)
        if key not in self._cache:
            qc = self.encode(logical_state)
            if inject_qubit is not None:
                self.inject_error(qc, inject_qubit)
            self._cache[key] = self.syndrome_circuit(qc)
        return self._cache[key]

    def run_cycle(self, logical_state: str = '1',
                  inject_qubit: Optional[int] = None
                  ) -> Tuple[str, Optional[int], float, bool]:
        """
        One QEC cycle: simulate a single shot, then decode with the clock running.
        Returns (syndrome, correction, decode time in ns, decoded == injected).
        """
        counts = self._sim.run(self._circuit(logical_state, inject_qubit), shots=1,
                               seed_simulator=int(self._rng.integers(1, 2**31 - 1))
                               ).result().get_counts()
        syndrome_str = next(iter(counts))

        t0 = time.perf_counter_ns()
        correction = self.decode_syndrome(syndrome_str)
        t1 = time.perf_counter_ns()

        return syndrome_str, correction, float(t1 - t0), correction == inject_qubit


def run_latency_experiment(n_cycles: int = 10_000,
                           output_file: str = 'w2_latencies.json') -> dict:
    """n_cycles cycles; each one gets no error or one random X error."""
    code = BitFlipCode(seed=42)
    rng = np.random.default_rng(seed=42)
    choices = [None, 0, 1, 2]

    latencies, successes, injected, decoded = [], [], [], []
    print(f"Running {n_cycles:,} QEC cycles...")
    for i in range(n_cycles):
        inject = choices[int(rng.integers(0, 4))]
        _, corr, lat, ok = code.run_cycle('1', inject)
        latencies.append(lat)
        successes.append(ok)
        injected.append(-1 if inject is None else inject)
        decoded.append(-1 if corr is None else corr)
        if (i + 1) % 2000 == 0:
            print(f"  {i + 1:>6,}/{n_cycles:,}   success {np.mean(successes) * 100:5.2f}%"
                  f"   median decode {np.median(latencies):.0f} ns")

    lat = np.array(latencies)
    labels = ['none', 'q0', 'q1', 'q2']
    # confusion matrix: rows = what I injected, columns = what the decoder said
    confusion = np.zeros((4, 4), dtype=int)
    for a, b in zip(injected, decoded):
        confusion[a + 1, b + 1] += 1

    out = {
        'author': 'Swayam Shakya',
        'experiment': 'Weekend 2.1 — bit-flip code, Python LUT decode latency',
        'n_cycles': n_cycles,
        'latencies_ns': latencies,
        'success_rate': float(np.mean(successes)),
        'confusion_labels': labels,
        'confusion_injected_by_decoded': confusion.tolist(),
        'median_ns': float(np.median(lat)),
        'mean_ns': float(np.mean(lat)),
        'p95_ns': float(np.percentile(lat, 95)),
        'p99_ns': float(np.percentile(lat, 99)),
        'max_ns': float(np.max(lat)),
    }
    with open(output_file, 'w') as fh:
        json.dump(out, fh, indent=2)

    print(f"\nSaved {n_cycles:,} latency samples → {output_file}")
    print(f"Decode latency  median {out['median_ns']:.0f} ns · P99 {out['p99_ns']:.0f} ns"
          f" · max {out['max_ns']:.0f} ns")
    print(f"Syndrome → correction success: {out['success_rate'] * 100:.2f}%")
    print("Confusion (rows injected none/q0/q1/q2, cols decoded):")
    for lab, row in zip(labels, confusion):
        print(f"  {lab:>4}: {row.tolist()}")
    return out


if __name__ == '__main__':
    run_latency_experiment(n_cycles=10_000)
