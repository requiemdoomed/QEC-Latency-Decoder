"""
experiment_1_2_pauli_sensitivity.py - Weekend 1, Experiment 1.2
Which Pauli errors can a |+> state actually feel?
Author: Swayam Shakya

Circuit:   |0> -- H -- [id with a Pauli channel] -- H -- measure

H makes |+>, the idle gate applies Pauli P with probability p, and the second H
rotates back so that P(0) = "the state is still |+>". What I expect:

    X|+> = |+>     -> P(0) = 1        (X does nothing to |+>)
    Z|+> = |->     -> P(0) = 1 - p
    Y|+> = -i|->   -> P(0) = 1 - p

This is the reason the bit-flip code is only half a code: it fixes X errors,
which |+> can't even feel, and it is blind to Z, which is what hurts |+>.

Gotcha I hit: in my first draft the noise sat on both H gates. An X error
right after the second H flips the measured bit, so |+> looked about 49%
"sensitive" to X. The noise has to be on the idle gate only.

Writes: fig2_pauli_sensitivity.pdf/.png, w1_pauli.json
"""
import json

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, pauli_error

import qec_style

qec_style.apply()
import matplotlib.pyplot as plt  # noqa: E402

SHOTS = 8192
SEED = 2024
PROBS = np.linspace(0.0, 0.5, 11)
PAULIS = ['X', 'Y', 'Z']
# A separate, well spread seed for every (Pauli, p) run - see the note on
# Aer seeding in experiment_1_1_coherence.py.
SEEDS = np.random.SeedSequence(SEED).generate_state(len(PAULIS) * len(PROBS))


def make_noise_model(op: str, prob: float) -> NoiseModel:
    """`op` with probability p on the idle gate, identity the rest of the time."""
    nm = NoiseModel()
    if prob > 0:
        nm.add_all_qubit_quantum_error(
            pauli_error([(op, prob), ('I', 1.0 - prob)]), ['id'])
    return nm


def plus_state_survival(op: str, prob: float, seed: int) -> float:
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.id(0)          # the error goes in here and only here
    qc.h(0)
    qc.measure(0, 0)
    sim = AerSimulator(noise_model=make_noise_model(op, prob), seed_simulator=seed)
    counts = sim.run(qc, shots=SHOTS).result().get_counts()
    return counts.get('0', 0) / SHOTS


def main() -> dict:
    results = {op: [plus_state_survival(op, float(p), int(SEEDS[j * len(PROBS) + i]))
                    for i, p in enumerate(PROBS)]
               for j, op in enumerate(PAULIS)}

    for op in PAULIS:
        expected = np.ones_like(PROBS) if op == 'X' else 1.0 - PROBS
        max_dev = float(np.max(np.abs(np.array(results[op]) - expected)))
        print(f"Pauli {op}: P(|+> survives) at p = 0.5 → {results[op][-1]:.3f}   "
              f"max |sim − theory| = {max_dev:.4f}")

    # --- figure ---
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot(PROBS * 100, 1.0 - PROBS, color=qec_style.GRID, lw=6, zorder=1)
    ax.text(30, 1 - 0.30 - 0.045, 'theory 1 − p', color=qec_style.MUTED,
            fontsize=8.5, rotation=-24, rotation_mode='anchor')
    style = {'X': (qec_style.BLUE, 'o', '-'),
             'Y': (qec_style.ORANGE, 's', '--'),
             'Z': (qec_style.AQUA, '^', ':')}
    for op in PAULIS:
        c, m, ls = style[op]
        ax.plot(PROBS * 100, results[op], color=c, marker=m, ms=5, ls=ls,
                lw=1.6, label=f'Pauli {op}', zorder=3)
    ax.text(50, results['X'][-1] - 0.035, 'X: no effect on |+⟩', ha='right',
            color=qec_style.BLUE, fontsize=9)
    ax.text(51, results['Z'][-1], 'Y, Z', va='center', color=qec_style.INK, fontsize=9)
    ax.set_xlabel('Error probability p (%)')
    ax.set_ylabel('P(state is still |+⟩)')
    ax.set_xlim(-1, 55)
    ax.set_ylim(0.4, 1.05)
    ax.set_title('|+⟩ ignores X errors; Y and Z flip it with probability p', loc='left')
    ax.legend(loc='lower left', fontsize=8.5)
    qec_style.save(fig, 'fig2_pauli_sensitivity')

    out = {'author': 'Swayam Shakya',
           'experiment': 'Weekend 1.2 — Pauli sensitivity of |+>',
           'shots': SHOTS, 'seed': SEED,
           'p': PROBS.tolist(), 'survival': results}
    with open('w1_pauli.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print('Saved: w1_pauli.json')
    return out


if __name__ == '__main__':
    main()
