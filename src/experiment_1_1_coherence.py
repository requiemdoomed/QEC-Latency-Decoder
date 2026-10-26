"""
experiment_1_1_coherence.py - Weekend 1, Experiment 1.1: Ramsey decay
Author: Swayam Shakya

Before timing any decoder I wanted to see the clock I'm racing against:
how fast does a qubit lose its phase under the noise model I use everywhere?

Circuit:   |0> -- H -- [id] x d -- H -- measure

The first H puts the qubit in |+>. Every idle (id) gate lasts GATE_NS and lets
it dephase a little. The second H turns whatever phase is left into a Z-basis
population, so

    P(0) = 0.5 + 0.5 * exp(-t / T2),     with t = d * GATE_NS

Only the idle gates are noisy, so t is known exactly and a one-parameter fit
gives T2 back.

A mistake worth remembering: my first version prepared |0> instead of |+>.
Thermal relaxation never moves |0>, so the "decay" was flat and the fit ran off
to T2 = 44,142 us. Starting in |+> fixes it.

Writes: fig1_coherence_decay.pdf/.png, w1_coherence.json
"""
import json

import numpy as np
from scipy.optimize import curve_fit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error

import qec_style

qec_style.apply()
import matplotlib.pyplot as plt  # noqa: E402  (pyplot has to come after the backend is set)

# Project-wide noise numbers. T2 = 120 us is deliberately on the pessimistic
# side: the calibrated IBM replicas in Weekend 4 have medians of 144-170 us.
T1_US = 250.0      # energy relaxation time (us)
T2_US = 120.0      # dephasing time (us), physics needs T2 <= 2*T1
GATE_NS = 50.0     # length of one idle gate (ns)
N_ROUNDS = 3       # syndrome rounds in one logical cycle
TAU_DD_US = T2_US / N_ROUNDS   # time budget per round: the 40 us "deadline"

SHOTS = 4096
SEED = 1234
DEPTHS = np.linspace(0, 6000, 25).astype(int)   # 0 to 300 us of idling

# One seed per depth, spread out with SeedSequence. Aer seeds shot k with
# seed + k, so re-using one seed (or seeds 1, 2, 3...) makes the points
# share random numbers, and curve_fit assumes they are independent.
SEEDS = np.random.SeedSequence(SEED).generate_state(len(DEPTHS))


def build_noise_model(t1_ns: float, t2_ns: float, gate_ns: float) -> NoiseModel:
    """Thermal relaxation on the idle gates only; the two H gates are perfect."""
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(
        thermal_relaxation_error(t1_ns, t2_ns, gate_ns), ['id'])
    return nm


def ramsey_circuit(depth: int) -> QuantumCircuit:
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    for _ in range(depth):
        qc.id(0)
    qc.h(0)
    qc.measure(0, 0)
    return qc


def fidelity_model(t_us, t2_us):
    """F(t) = 0.5 + 0.5 * exp(-t / T2)"""
    return 0.5 + 0.5 * np.exp(-np.asarray(t_us, dtype=float) / t2_us)


def main() -> dict:
    nm = build_noise_model(T1_US * 1e3, T2_US * 1e3, GATE_NS)
    sim = AerSimulator(noise_model=nm)

    t_us = DEPTHS * GATE_NS / 1e3
    fids = []
    for d, seed in zip(DEPTHS, SEEDS):
        counts = sim.run(ramsey_circuit(int(d)), shots=SHOTS,
                         seed_simulator=int(seed)).result().get_counts()
        fids.append(counts.get('0', 0) / SHOTS)
    fids = np.array(fids)

    popt, pcov = curve_fit(fidelity_model, t_us, fids, p0=[100.0], bounds=(1.0, 1e4))
    t2_fit, t2_err = float(popt[0]), float(np.sqrt(pcov[0, 0]))
    f_at_deadline = float(fidelity_model(TAU_DD_US, t2_fit))

    print(f"Fitted T2          : {t2_fit:.1f} ± {t2_err:.1f} µs  (model input {T2_US} µs)")
    print(f"Deadline τ_DD      : {TAU_DD_US:.0f} µs  (T2 / {N_ROUNDS})")
    print(f"Fidelity at τ_DD   : {f_at_deadline:.3f}")

    # --- figure ---
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    t_fine = np.linspace(0, t_us.max(), 400)
    ax.plot(t_fine, fidelity_model(t_fine, t2_fit), color=qec_style.BLUE,
            label=f'Fit: T$_2$ = {t2_fit:.1f} ± {t2_err:.1f} µs')
    ax.scatter(t_us, fids, s=22, color=qec_style.BLUE, edgecolor='white',
               linewidth=0.8, zorder=3, label=f'Aer simulation ({SHOTS} shots)')
    ax.axhline(0.5, color=qec_style.MUTED, ls='--', lw=1)
    ax.text(t_us.max(), 0.508, 'maximally mixed (0.5)', ha='right',
            va='bottom', fontsize=8.5, color=qec_style.MUTED)
    ax.axvline(TAU_DD_US, color=qec_style.INK, ls=':', lw=1.2)
    ax.annotate(f'τ$_{{DD}}$ = {TAU_DD_US:.0f} µs\nF = {f_at_deadline:.3f}',
                xy=(TAU_DD_US, f_at_deadline), xytext=(TAU_DD_US + 18, 0.93),
                fontsize=8.5, color=qec_style.INK,
                arrowprops=dict(arrowstyle='-', color=qec_style.MUTED, lw=0.8))
    ax.set_xlabel('Idle time t (µs)')
    ax.set_ylabel('P(0) after Ramsey sequence')
    ax.set_ylim(0.45, 1.02)
    ax.set_title(f'Coherence falls to F = {f_at_deadline:.2f} at the '
                 f'{TAU_DD_US:.0f} µs deadline', loc='left')
    ax.legend(loc='upper right', fontsize=8.5)
    qec_style.save(fig, 'fig1_coherence_decay')

    out = {
        'author': 'Swayam Shakya',
        'experiment': 'Weekend 1.1 — Ramsey coherence decay',
        'params': {'T1_us': T1_US, 'T2_us': T2_US, 'gate_ns': GATE_NS,
                   'shots': SHOTS, 'seed': SEED},
        'depths': DEPTHS.tolist(),
        't_us': t_us.tolist(),
        'fidelity': fids.tolist(),
        'T2_fit_us': t2_fit,
        'T2_fit_err_us': t2_err,
        'tau_dd_us': TAU_DD_US,
        'fidelity_at_tau_dd': f_at_deadline,
    }
    with open('w1_coherence.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print('Saved: w1_coherence.json')
    return out


if __name__ == '__main__':
    main()
