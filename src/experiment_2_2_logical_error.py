"""
experiment_2_2_logical_error.py - Weekend 2, Experiment 2.2
Does the code actually help? Logical vs physical error rate.
Author: Swayam Shakya

The simplest honest test ("code capacity" noise): encode |1>_L = |111>, give
each data qubit an independent X error with probability p, read the syndrome
with perfect checks, fix it in real time with if_test, then read out the data.
The logical qubit only dies when two or three qubits flip:

    P_L(p) = 3p^2 - 2p^3        (one bare qubit: P = p)

So the code should win for every p < 1/2, and by roughly 1/(3p) when p is small.

Writes: fig2b_logical_error.pdf/.png, w2_logical_error.json
"""
import json

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, pauli_error
from statsmodels.stats.proportion import proportion_confint

import qec_style

qec_style.apply()
import matplotlib.pyplot as plt  # noqa: E402

SHOTS = 100_000
SEED = 7
P_VALUES = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
# I originally used seeds 7, 8, 9... one per p. Because Aer seeds shot k with
# seed + k, those streams overlap almost completely and the "independent"
# points came out correlated. SeedSequence spreads them properly.
SEEDS = [int(s) for s in np.random.SeedSequence(SEED).generate_state(len(P_VALUES))]


def noise(p: float) -> NoiseModel:
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(pauli_error([('X', p), ('I', 1 - p)]), ['id'])
    return nm


def encoded_circuit() -> QuantumCircuit:
    qd = QuantumRegister(3, 'data')
    qa = QuantumRegister(2, 'anc')
    syn = ClassicalRegister(2, 'syn')
    out = ClassicalRegister(3, 'out')
    qc = QuantumCircuit(qd, qa, syn, out)
    qc.x(qd[0]); qc.cx(qd[0], qd[1]); qc.cx(qd[0], qd[2])     # |111>
    qc.id(qd)                                                 # the noisy moment
    qc.cx(qd[0], qa[1]); qc.cx(qd[1], qa[1])                  # Z0*Z1
    qc.cx(qd[1], qa[0]); qc.cx(qd[2], qa[0])                  # Z1*Z2
    qc.measure(qa, syn)
    # real-time correction: the syndrome decides which X (if any) to apply
    with qc.if_test((syn, 0b10)):
        qc.x(qd[0])
    with qc.if_test((syn, 0b11)):
        qc.x(qd[1])
    with qc.if_test((syn, 0b01)):
        qc.x(qd[2])
    qc.measure(qd, out)
    return qc


def bare_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(QuantumRegister(1, 'q'), ClassicalRegister(1, 'out'))
    qc.x(0)
    qc.id(0)                                                  # same noise, no protection
    qc.measure(0, 0)
    return qc


def failures(counts: dict) -> int:
    """Shots where the majority of the three data bits is not 1."""
    return sum(n for bits, n in counts.items()
               if bits.split()[0].count('1') < 2)    # 'out' is the left-most register


def main() -> dict:
    enc, bare = encoded_circuit(), bare_circuit()
    rows = []
    for i, p in enumerate(P_VALUES):
        sim = AerSimulator(noise_model=noise(p), seed_simulator=SEEDS[i])
        c_enc = sim.run(enc, shots=SHOTS).result().get_counts()
        c_bare = sim.run(bare, shots=SHOTS).result().get_counts()
        k_enc = failures(c_enc)
        k_bare = c_bare.get('0', 0)
        lo, hi = proportion_confint(k_enc, SHOTS, alpha=0.05, method='wilson')
        theory = 3 * p**2 - 2 * p**3
        rows.append({'p': p, 'logical_fail': k_enc / SHOTS, 'ci': [lo, hi],
                     'bare_fail': k_bare / SHOTS, 'theory': theory})
        print(f"p = {p:5.2f}   P_L = {k_enc / SHOTS:.5f}  [{lo:.5f}, {hi:.5f}]"
              f"   theory {theory:.5f}   bare {k_bare / SHOTS:.4f}"
              f"   gain ×{(k_bare / max(k_enc, 1)):.1f}")

    # --- figure (log-log, so the quadratic suppression shows up as a steeper line) ---
    p = np.array([r['p'] for r in rows])
    pl = np.array([r['logical_fail'] for r in rows])
    lo = np.array([r['ci'][0] for r in rows])
    hi = np.array([r['ci'][1] for r in rows])
    pf = np.logspace(-2, np.log10(0.5), 200)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(pf, pf, color=qec_style.MUTED, ls='--', lw=1.2)
    ax.text(0.0105, 0.036, 'unencoded qubit: P = p', color=qec_style.MUTED,
            fontsize=8.5, va='bottom')
    ax.plot(pf, 3 * pf**2 - 2 * pf**3, color=qec_style.BLUE, lw=1.4)
    ax.text(0.075, 0.0062, 'theory: 3p² − 2p³', color=qec_style.BLUE,
            fontsize=8.5, va='top')
    ax.errorbar(p, pl, yerr=[pl - lo, hi - pl], fmt='o', ms=4.5,
                color=qec_style.BLUE, mec='white', mew=0.8, capsize=0, lw=1.2,
                zorder=3)
    ax.text(0.47, 1.25e-4, f'dots: 3-qubit code in Aer, {SHOTS:,} shots each · '
            'bars: Wilson 95% CI', ha='right', fontsize=8, color=qec_style.MUTED)
    ax.text(0.0122, pl[0] * 0.92,
            f'p = 1%: P$_L$ = {pl[0] * 100:.3f}%  '
            f'({rows[0]["bare_fail"] / pl[0]:.0f}× fewer failures)',
            fontsize=8.5, va='center', color=qec_style.INK)
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('Physical bit-flip probability p')
    ax.set_ylabel('Failure probability')
    ax.set_title(f'The code turns a {p[0]:.0%} bit-flip rate into a '
                 f'{pl[0]:.2%} logical failure rate', loc='left')
    ax.set_ylim(1e-4, 0.8)
    qec_style.save(fig, 'fig2b_logical_error')

    out = {'author': 'Swayam Shakya',
           'experiment': 'Weekend 2.2 — logical vs physical error (code capacity)',
           'shots': SHOTS, 'seed': SEED, 'rows': rows}
    with open('w2_logical_error.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print('Saved: w2_logical_error.json')
    return out


if __name__ == '__main__':
    main()
