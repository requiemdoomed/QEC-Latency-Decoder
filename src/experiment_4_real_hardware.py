"""
experiment_4_real_hardware.py - Weekend 4
The bit-flip code with real-time feed-forward, on IBM Quantum hardware or, if
you don't have an account, on a local replica built from a real device's
calibration data.
Author: Swayam Shakya

One job, three circuits, all starting from logical |1>:
  bare      a single physical qubit: X, then a delay exactly as long as the
            encoded circuit's encode + syndrome stage, then measure
  offline   |111>, measure the syndrome, no feed-forward. I decode the
            syndrome afterwards in software, shot by shot
  realtime  |111>, measure the syndrome, and fix the error in real time with
            if_test (feed-forward) before reading the data qubits

That gives four numbers: bare; majority vote alone (offline data, syndrome
ignored); offline decode + majority; real-time correction + majority.
The last two differ only in *when* the correction happens, so comparing them
isolates the cost of the classical feedback window.

Usage
  python experiment_4_real_hardware.py local [FakeKingston]
        noisy local run on a device calibration snapshot, no account needed
  python experiment_4_real_hardware.py sweep [FakeKingston]
        local only: wait 0-80 us before the real-time correction and watch
        the logical error grow as the decoder gets slower
  python experiment_4_real_hardware.py draw
        draws the protected circuit (fig0_protected_circuit.png)
  python experiment_4_real_hardware.py submit
        the least-busy real device that supports dynamic circuits, using the
        key saved by save_ibm_account.py; writes w4_job_manifest.json
  python experiment_4_real_hardware.py retrieve <job_id>
        fetch a finished hardware job and analyse it

All three circuits sit on the same physical qubits (the bare qubit is data
qubit 0's qubit). Early on I let the transpiler pick layouts separately and got
a 0.42-point "difference" between offline and real-time on Eagle that was
really just better qubits. Pinning the layout made it vanish.

Writes: w4_results_<backend>.json, fig5_hardware_<backend>.pdf/.png,
        w4_sweep_<backend>.json, fig6_latency_sweep_<backend>.pdf/.png
"""
import json
import sys
import time

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, fake_provider
# The new client-side Sampler (qiskit-ibm-runtime >= 0.50). SamplerV2 still
# works but is deprecated in 0.50, so I moved over.
from qiskit_ibm_runtime.executor_sampler import Sampler
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportion_confint

import qec_style

qec_style.apply()
import matplotlib.pyplot as plt  # noqa: E402

SHOTS = 4000
SEED = 1234
SWEEP_US = [0, 0.5, 1, 2, 5, 10, 20, 40, 80]   # decoder waits tried in the sweep (µs)
N_ROUNDS = 3
CIRCUITS = ['bare', 'offline', 'realtime']
LUT = {'00': None, '10': 0, '11': 1, '01': 2}


# --- circuits ---
def encoded(feedforward: bool, wait_dt: int = 0) -> QuantumCircuit:
    """The encoded circuit. wait_dt > 0 parks the data qubits for that long
    between reading the syndrome and fixing the error - my stand-in for a slow
    classical decoder. (Aer only adds noise to instructions, so an explicit
    delay is the only way the replica can "see" latency.)"""
    qd = QuantumRegister(3, 'data')
    qa = QuantumRegister(2, 'anc')
    syn = ClassicalRegister(2, 'syn')
    out = ClassicalRegister(3, 'out')
    qc = QuantumCircuit(qd, qa, syn, out,
                        name='realtime' if feedforward else 'offline')
    qc.x(qd[0]); qc.cx(qd[0], qd[1]); qc.cx(qd[0], qd[2])      # |111>
    qc.cx(qd[0], qa[1]); qc.cx(qd[1], qa[1])                   # ancilla 1 ← Z0·Z1
    qc.cx(qd[1], qa[0]); qc.cx(qd[2], qa[0])                   # ancilla 0 ← Z1·Z2
    qc.measure(qa, syn)
    if wait_dt > 0:
        qc.delay(wait_dt, qd, unit='dt')
    if feedforward:
        with qc.if_test((syn, 0b10)):
            qc.x(qd[0])
        with qc.if_test((syn, 0b11)):
            qc.x(qd[1])
        with qc.if_test((syn, 0b01)):
            qc.x(qd[2])
    qc.barrier(qd)
    qc.measure(qd, out)
    return qc


def stage_duration_s(backend, pm) -> float:
    """How long encode + syndrome + ancilla readout takes on this device.
    The bare qubit idles for exactly this long, so the comparison is fair."""
    qd, qa, syn = QuantumRegister(3, 'data'), QuantumRegister(2, 'anc'), ClassicalRegister(2, 'syn')
    qc = QuantumCircuit(qd, qa, syn)
    qc.x(qd[0]); qc.cx(qd[0], qd[1]); qc.cx(qd[0], qd[2])
    qc.cx(qd[0], qa[1]); qc.cx(qd[1], qa[1]); qc.cx(qd[1], qa[0]); qc.cx(qd[2], qa[0])
    qc.measure(qa, syn)
    return float(pm.run(qc).estimate_duration(backend.target, unit='s'))


def to_dt(seconds: float, backend) -> int:
    """Seconds -> whole device time steps (dt), snapped to the timing grid."""
    grain = max(1, int(getattr(backend.target, 'granularity', 1) or 1))
    return grain * int(round(seconds / backend.target.dt / grain))


def bare(delay_s: float, backend) -> QuantumCircuit:
    """One unprotected qubit holding |1> for delay_s. I used id gates for
    padding at first, but the transpiler just deletes them; a delay stays."""
    n_dt = to_dt(delay_s, backend)
    qc = QuantumCircuit(QuantumRegister(1, 'q'), ClassicalRegister(1, 'out'), name='bare')
    qc.x(0)
    qc.delay(n_dt, 0, unit='dt')
    qc.measure(0, 0)
    return qc


def fixed_layout_pms(backend):
    """Pick the layout once, for the encoded circuit, and reuse it for all three."""
    pm0 = generate_preset_pass_manager(optimization_level=2, backend=backend,
                                       seed_transpiler=SEED)
    layout = pm0.run(encoded(False)).layout.initial_index_layout(filter_ancillas=True)
    pm = generate_preset_pass_manager(optimization_level=2, backend=backend,
                                      initial_layout=layout, seed_transpiler=SEED)
    pm_bare = generate_preset_pass_manager(optimization_level=2, backend=backend,
                                           initial_layout=[layout[0]],
                                           seed_transpiler=SEED)
    return pm, pm_bare, layout


def build_job(backend):
    pm, pm_bare, _ = fixed_layout_pms(backend)
    delay = stage_duration_s(backend, pm)
    isa = [pm_bare.run(bare(delay, backend)), pm.run(encoded(False)),
           pm.run(encoded(True))]
    stats = {}
    for name, c in zip(CIRCUITS, isa):
        ops = c.count_ops()
        stats[name] = {'depth': c.depth(),
                       'two_qubit_gates': int(sum(ops.get(g, 0) for g in ('cx', 'ecr', 'cz'))),
                       'physical_qubits': sorted({c.find_bit(q).index for inst in c.data
                                                  for q in inst.qubits})}
    return isa, delay, stats


# --- analysis ---
def majority_is_one(bits: str) -> bool:
    return bits.count('1') >= 2


def decode_offline(syn: str, data: str) -> str:
    """Apply the LUT correction to the 3 data bits. Careful: the string is q2 q1 q0."""
    q = LUT[syn]
    if q is None:
        return data
    i = 2 - q
    return data[:i] + ('0' if data[i] == '1' else '1') + data[i + 1:]


def analyse(pubs, backend_name: str, meta: dict) -> dict:
    up, off, rt = pubs
    n = SHOTS
    good = {}
    good['bare'] = up.data.out.get_counts().get('1', 0)
    syn_bits = off.data.syn.get_bitstrings()
    data_bits = off.data.out.get_bitstrings()
    good['majority vote only'] = sum(majority_is_one(d) for d in data_bits)
    good['offline decode'] = sum(majority_is_one(decode_offline(s, d))
                                 for s, d in zip(syn_bits, data_bits))
    good['real-time feed-forward'] = sum(n_ for bits, n_ in rt.data.out.get_counts().items()
                                         if majority_is_one(bits))

    rows = {}
    for name, k in good.items():
        lo, hi = proportion_confint(k, n, alpha=0.05, method='wilson')
        rows[name] = {'correct': int(k), 'shots': n, 'fidelity': k / n, 'ci': [lo, hi]}

    def chi2(a: str, b: str) -> dict:
        ka, kb = good[a], good[b]
        stat, p, _, _ = chi2_contingency([[ka, n - ka], [kb, n - kb]])
        return {'chi2': float(stat), 'p': float(p),
                'difference_pct_points': 100 * (kb - ka) / n}

    tests = {'bare vs real-time': chi2('bare', 'real-time feed-forward'),
             'bare vs offline decode': chi2('bare', 'offline decode'),
             'offline vs real-time': chi2('offline decode', 'real-time feed-forward')}

    print(f"\n── Results on {backend_name} ({n} shots per circuit) ──")
    for name, r in rows.items():
        print(f"{name:<24} F = {r['fidelity'] * 100:6.2f}%   "
              f"95% CI [{r['ci'][0] * 100:.2f}, {r['ci'][1] * 100:.2f}]")
    for name, t in tests.items():
        print(f"{name:<24} Δ = {t['difference_pct_points']:+.2f} pp   "
              f"χ² = {t['chi2']:.2f}   p = {t['p']:.3g}")

    out = {'author': 'Swayam Shakya', 'backend': backend_name, 'shots': n,
           **meta, 'logical': rows, 'tests': tests}
    stem = backend_name.replace(' ', '_')
    with open(f'w4_results_{stem}.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print(f'Saved: w4_results_{stem}.json')
    plot(out, stem)
    return out


def plot(res: dict, stem: str) -> None:
    rows = res['logical']
    names = list(rows)
    y = np.arange(len(names))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    for yi, name in zip(y, names):
        r = rows[name]
        c = qec_style.MUTED if name == 'bare' else qec_style.BLUE
        ax.errorbar(r['fidelity'] * 100, yi,
                    xerr=[[100 * (r['fidelity'] - r['ci'][0])],
                          [100 * (r['ci'][1] - r['fidelity'])]],
                    fmt='o', color=c, ms=6, capsize=3, lw=1.4)
        ax.text(r['ci'][1] * 100 + 0.15, yi, f"{r['fidelity'] * 100:.2f}%",
                va='center', fontsize=8.5)
    ax.set_yticks(y, names)
    ax.set_xlabel('Logical |1⟩ fidelity (%) with Wilson 95% CI')
    ax.grid(axis='y', visible=False)
    lo = min(r['ci'][0] for r in rows.values()) * 100
    ax.set_xlim(lo - 0.6, 100.4)
    b, r = rows['bare']['fidelity'] * 100, rows['real-time feed-forward']['fidelity'] * 100
    ax.set_title(f"The code lifts |1⟩ fidelity from {b:.2f}% to {r:.2f}%\n",
                 loc='left', fontsize=11)
    ax.text(0, 1.02, f"{res['backend']} · {res['mode']} · {res['shots']} shots per circuit",
            transform=ax.transAxes, fontsize=8.5, color=qec_style.MUTED)
    qec_style.save(fig, f'fig5_hardware_{stem}')


def device_meta(backend, delay_s: float, stats: dict, mode: str) -> dict:
    qp = [backend.target.qubit_properties[i] for i in range(backend.num_qubits)]
    t2 = np.array([q.t2 for q in qp if q is not None and q.t2])
    t1 = np.array([q.t1 for q in qp if q is not None and q.t1])
    t2_med = float(np.median(t2))
    print(f"Device {backend.name}: median T1 = {np.median(t1) * 1e6:.0f} µs, "
          f"median T2 = {t2_med * 1e6:.0f} µs → τ_DD = T2/{N_ROUNDS} = "
          f"{t2_med / N_ROUNDS * 1e6:.0f} µs")
    print(f"Encode + syndrome stage = {delay_s * 1e6:.2f} µs (bare-qubit delay)")
    for k, v in stats.items():
        print(f"  {k:<9} depth {v['depth']:>3}   2-qubit gates {v['two_qubit_gates']:>2}"
              f"   qubits {v['physical_qubits']}")
    return {'mode': mode, 'median_T1_us': float(np.median(t1) * 1e6),
            'median_T2_us': t2_med * 1e6, 'tau_dd_us': t2_med / N_ROUNDS * 1e6,
            'stage_duration_us': delay_s * 1e6, 'transpiled': stats}


# --- entry points ---
def make_sampler(backend) -> Sampler:
    """I want raw numbers: twirling off, dynamical decoupling off (DD can't be
    combined with dynamic circuits anyway)."""
    sampler = Sampler(mode=backend)
    sampler.options.twirling.enable_gates = False
    sampler.options.twirling.enable_measure = False
    sampler.options.dynamical_decoupling.enable = False
    return sampler


def run_local(fake_name: str = 'FakeKingston') -> dict:
    backend = getattr(fake_provider, fake_name)()
    isa, delay, stats = build_job(backend)
    meta = device_meta(backend, delay, stats, 'local calibrated simulation')
    sampler = make_sampler(backend)
    sampler.options.simulator.seed_simulator = SEED
    result = sampler.run(isa, shots=SHOTS).result()
    return analyse(result, backend.name, meta)


def run_sweep(fake_name: str = 'FakeKingston') -> dict:
    """Logical error vs decoder wait, on the local replica only."""
    backend = getattr(fake_provider, fake_name)()
    pm, pm_bare, _ = fixed_layout_pms(backend)
    stage = stage_duration_s(backend, pm)
    dt = backend.target.dt
    pubs, waits = [], []
    for w_us in SWEEP_US:
        w = to_dt(w_us * 1e-6, backend)
        waits.append(w * dt * 1e6)
        pubs += [pm.run(encoded(True, w)), pm_bare.run(bare(stage + w * dt, backend))]
    sampler = make_sampler(backend)
    sampler.options.simulator.seed_simulator = SEED
    res = sampler.run(pubs, shots=SHOTS).result()

    rows = []
    for i, w_us in enumerate(waits):
        k_enc = sum(n for b, n in res[2 * i].data.out.get_counts().items()
                    if majority_is_one(b))
        k_bare = res[2 * i + 1].data.out.get_counts().get('1', 0)
        e_lo, e_hi = proportion_confint(SHOTS - k_enc, SHOTS, alpha=0.05, method='wilson')
        b_lo, b_hi = proportion_confint(SHOTS - k_bare, SHOTS, alpha=0.05, method='wilson')
        rows.append({'wait_us': w_us,
                     'encoded_error': 1 - k_enc / SHOTS, 'encoded_ci': [e_lo, e_hi],
                     'bare_error': 1 - k_bare / SHOTS, 'bare_ci': [b_lo, b_hi]})
        print(f"wait {w_us:6.2f} µs   encoded error {100 * (1 - k_enc / SHOTS):6.2f}%   "
              f"bare error {100 * (1 - k_bare / SHOTS):6.2f}%")

    # the wait where the encoded error doubles, interpolated on a log scale
    e = np.array([r['encoded_error'] for r in rows])
    w = np.array(waits)
    above = np.nonzero(e >= 2 * e[0])[0]
    l2x = None
    if above.size and above[0] > 0:
        j = above[0]
        l2x = float(np.interp(np.log(2 * e[0]), np.log(e[j - 1:j + 1]), w[j - 1:j + 1]))
        print(f"Encoded logical error doubles at a decoder wait of ≈ {l2x:.1f} µs")

    t2 = np.median([q.t2 for q in backend.target.qubit_properties if q and q.t2])
    out = {'author': 'Swayam Shakya', 'backend': backend.name, 'shots': SHOTS,
           'mode': 'local calibrated simulation', 'stage_duration_us': stage * 1e6,
           'tau_dd_us': float(t2 / N_ROUNDS * 1e6), 'doubling_wait_us': l2x, 'rows': rows}
    stem = backend.name
    with open(f'w4_sweep_{stem}.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print(f'Saved: w4_sweep_{stem}.json')
    plot_sweep(out, stem)
    return out


def plot_sweep(res: dict, stem: str) -> None:
    rows = res['rows']
    w = np.array([r['wait_us'] for r in rows])
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for key, c, label in (('bare', qec_style.MUTED, 'bare qubit (idles for the same time)'),
                          ('encoded', qec_style.BLUE, '3-qubit code, real-time correction')):
        y = np.array([r[f'{key}_error'] for r in rows]) * 100
        lo = np.array([r[f'{key}_ci'][0] for r in rows]) * 100
        hi = np.array([r[f'{key}_ci'][1] for r in rows]) * 100
        ax.errorbar(w, y, yerr=[y - lo, hi - y], fmt='o-', color=c, ms=4.5, lw=1.6,
                    capsize=0, mec='white', mew=0.8)
        ax.text(w[-1] * 1.03, y[-1], label, va='center', fontsize=8.5, color=c)
    ax.vlines(res['tau_dd_us'], 0.1, 40, color=qec_style.INK, ls=':', lw=1.2)
    ax.text(res['tau_dd_us'] + 0.9, 0.14, f"device τ$_{{DD}}$ = {res['tau_dd_us']:.0f} µs",
            rotation=90, va='bottom', fontsize=7.5)
    try:                                   # mark the worst stalls from Weekend 3, if available
        with open('w3_latencies.json') as fh:
            summ = json.load(fh)['summary']
        for name, c in (('Python', qec_style.BLUE), ('C extension', qec_style.ORANGE)):
            m = summ[name]['max_ns'] / 1e3
            ax.vlines(m, 0.1, 40, color=c, ls='--', lw=0.9)
            ax.text(m + 0.9, 0.14, f"{name.split()[0]} worst stall {m:.1f} µs",
                    rotation=90, va='bottom', fontsize=7.5, color=c)
    except FileNotFoundError:
        pass
    ax.set_yscale('log')
    ax.set_ylim(0.1, 100)
    ax.set_xlim(-2, w[-1] * 1.45)
    ax.set_xlabel('Decoder wait before the correction (µs)')
    ax.set_ylabel('Logical error (%)')
    title = 'Every microsecond of decoder latency costs logical fidelity'
    if res['doubling_wait_us']:
        title = (f"Logical error doubles after ≈ {res['doubling_wait_us']:.0f} µs "
                 f"of decoder latency")
    ax.set_title(title, loc='left')
    ax.text(w[-1] * 1.43, 60, f"{res['backend']} replica · {res['shots']} shots/point"
            ' · Wilson 95% CI', ha='right', fontsize=7.5, color=qec_style.MUTED)
    qec_style.save(fig, f'fig6_latency_sweep_{stem}')


def draw_circuit() -> None:
    """Draw the real-time circuit for the write-up (needs pylatexenc)."""
    fig = encoded(True).draw('mpl', style='bw', fold=-1)
    fig.savefig('fig0_protected_circuit.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print('Saved: fig0_protected_circuit.png')


def connect() -> QiskitRuntimeService:
    """Load the account saved by save_ibm_account.py."""
    try:
        return QiskitRuntimeService()
    except Exception as exc:                  # no saved key, a wrong key, or no internet
        raise SystemExit(f'Could not connect to IBM Quantum: {exc}\n'
                         'Run save_ibm_account.py once, then try again.') from exc


def submit() -> str:
    service = connect()
    backend = service.least_busy(operational=True, simulator=False,
                                 min_num_qubits=5, dynamic_circuits=True)
    isa, delay, stats = build_job(backend)
    meta = device_meta(backend, delay, stats, 'IBM Quantum hardware')
    job = make_sampler(backend).run(isa, shots=SHOTS)
    manifest = {'author': 'Swayam Shakya', 'experiment': 'Weekend 4 — hardware QEC',
                'backend': backend.name, 'job_id': job.job_id(), 'shots': SHOTS,
                'submitted_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                **meta}
    with open('w4_job_manifest.json', 'w') as fh:
        json.dump(manifest, fh, indent=2)
    print(f"Submitted job {job.job_id()} to {backend.name}; "
          f"saved w4_job_manifest.json")
    return job.job_id()


def retrieve(job_id: str) -> dict:
    service = connect()
    job = service.job(job_id)
    try:
        with open('w4_job_manifest.json') as fh:
            meta = json.load(fh)
    except FileNotFoundError:
        meta = {'mode': 'IBM Quantum hardware'}
    meta = {k: v for k, v in meta.items() if k not in ('author', 'experiment', 'shots')}
    return analyse(job.result(), job.backend().name, meta)


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['local']:
        run_local(args[1] if len(args) > 1 else 'FakeKingston')
    elif args[:1] == ['sweep']:
        run_sweep(args[1] if len(args) > 1 else 'FakeKingston')
    elif args[:1] == ['submit']:
        submit()
    elif args[:1] == ['draw']:
        draw_circuit()
    elif args[:1] == ['retrieve'] and len(args) == 2:
        retrieve(args[1])
    else:
        sys.exit(__doc__)          # wrong usage: show the help and exit with status 1
