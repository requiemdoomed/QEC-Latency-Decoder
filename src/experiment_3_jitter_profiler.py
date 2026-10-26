"""
experiment_3_jitter_profiler.py - Weekend 3, Experiment 3.2
How long does decoding take, and how often does it miss the deadline?
Author: Swayam Shakya

I time the same syndrome lookup three ways:
  Python       measured   dict lookup between two time.perf_counter_ns() calls
  C extension  measured   LUT in C, timed inside C with clock_gettime(CLOCK_MONOTONIC),
                          so no Python overhead ends up in the numbers
  Bare-metal   MODELLED   a Cortex-M7 at 480 MHz: 41-cycle WCET = 85.4 ns plus 5%
                          Gaussian jitter. I don't own the board, so this tier is
                          only there for scale and never goes into a statistical test.

Both measured tiers also get a "timer floor": two clock reads with nothing
in between. At these speeds the clock itself is a big part of what you see,
so the floor tells me how much of the latency is real decode work.

The violation rate VR(tau) = P(latency > tau) gets exact Clopper-Pearson 95%
intervals. I started with bootstrap intervals, but with zero misses they
collapse to [0, 0], which is plainly wrong; the exact interval still gives an
honest upper bound (about 3.7/N). Bootstrap intervals are kept at four
deadlines so you can see the difference yourself.

Usage
  python experiment_3_jitter_profiler.py               main run + Figure
  python experiment_3_jitter_profiler.py --repeats 10  how stable is the tail?

Needs the compiled C library (run_all.sh builds it into build/):
  gcc -O2 -shared -fPIC -o qec_decode.so qec_decode.c
Writes: fig3_main_result.pdf/.png, w3_latencies.json  (or w3_repeats.json)
"""
import argparse
import ctypes
import json
import os
import platform
import sys
import time
import warnings

import numpy as np
from scipy.stats import bootstrap
from statsmodels.stats.proportion import proportion_confint

import qec_style

qec_style.apply()
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import gridspec  # noqa: E402

N = 10_000                       # timed cycles per tier
WARMUP = 1_000                   # thrown away first, so caches and branch predictors are warm
RNG = np.random.default_rng(seed=0)
SYNDROME_TABLE = {'00': None, '10': 0, '11': 1, '01': 2}
TAU_DD_NS = 40_000               # 40 µs deadline
P_TH_PCT = 1.0                   # ~1% surface-code threshold, used as my error budget for VR
KEY_TAUS_NS = [1_000, 5_000, 10_000, 40_000]
TAU_GRID_NS = np.logspace(1, 5, 121)        # 10 ns … 100 µs


# --- tier 1: plain Python ---
def python_tier(n: int) -> np.ndarray:
    syndromes = RNG.choice(list(SYNDROME_TABLE), n + WARMUP).tolist()
    lat = np.empty(n + WARMUP)
    for i, s in enumerate(syndromes):
        t0 = time.perf_counter_ns()
        _ = SYNDROME_TABLE[s]
        lat[i] = time.perf_counter_ns() - t0
    return lat[WARMUP:]


def python_floor(n: int) -> np.ndarray:
    lat = np.empty(n + WARMUP)
    for i in range(n + WARMUP):
        t0 = time.perf_counter_ns()
        lat[i] = time.perf_counter_ns() - t0
    return lat[WARMUP:]


# --- tier 2: the C library through ctypes ---
def find_c_library() -> str:
    """Look for qec_decode.so in the usual places, first match wins:
    $QEC_DECODE_LIB, the current folder, next to this script, ../build/."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.environ.get('QEC_DECODE_LIB', ''),
                  os.path.join(os.getcwd(), 'qec_decode.so'),
                  os.path.join(here, 'qec_decode.so'),
                  os.path.join(here, os.pardir, 'build', 'qec_decode.so')]
    for path in candidates:
        if path and os.path.exists(path):
            return os.path.abspath(path)
    # I'd rather stop loudly here than quietly carry on without the C tier
    raise FileNotFoundError(
        'qec_decode.so not found. Build it first:\n'
        '    gcc -O2 -shared -fPIC -o qec_decode.so qec_decode.c\n'
        'or point QEC_DECODE_LIB at it. (On Windows, run the project inside WSL.)')


def load_c_library(path: str = None) -> ctypes.CDLL:
    lib = ctypes.CDLL(path or find_c_library())
    i64p = ctypes.POINTER(ctypes.c_int64)
    lib.decode_batch.argtypes = [ctypes.POINTER(ctypes.c_uint8), i64p, ctypes.c_int]
    lib.decode_batch.restype = None
    lib.timer_floor_batch.argtypes = [i64p, ctypes.c_int]
    lib.timer_floor_batch.restype = None
    return lib


def c_tier(lib: ctypes.CDLL, n: int) -> np.ndarray:
    syn = RNG.integers(0, 4, n + WARMUP, dtype=np.uint8)
    out = np.empty(n + WARMUP, dtype=np.int64)
    lib.decode_batch(syn.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                     out.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)), n + WARMUP)
    return out[WARMUP:].astype(float)


def c_floor(lib: ctypes.CDLL, n: int) -> np.ndarray:
    out = np.empty(n + WARMUP, dtype=np.int64)
    lib.timer_floor_batch(out.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)), n + WARMUP)
    return out[WARMUP:].astype(float)


# --- tier 3: bare-metal, modelled (not measured!) ---
def bare_metal_model(n: int) -> np.ndarray:
    wcet_ns = 41 / 480e6 * 1e9                       # 41 cycles at 480 MHz = 85.4 ns
    return np.clip(RNG.normal(wcet_ns, 0.05 * wcet_ns, n), 0.8 * wcet_ns, None)


# --- violation rate ---
def vr_exact(lat: np.ndarray, tau: float):
    """VR(τ) in % with its exact (Clopper–Pearson) 95 % interval."""
    k, n = int(np.sum(lat > tau)), lat.size
    lo, hi = proportion_confint(k, n, alpha=0.05, method='beta')
    return 100 * k / n, 100 * lo, 100 * hi, k


def vr_bootstrap(lat: np.ndarray, tau: float, n_resamples: int = 2000):
    """Percentile bootstrap 95 % interval for VR(τ) in %; None if degenerate."""
    misses = (lat > tau).astype(float)
    if misses.min() == misses.max():                 # all 0 (or all 1): nothing to resample
        return None
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        res = bootstrap((misses,), np.mean, n_resamples=n_resamples,
                        confidence_level=0.95, method='percentile',
                        rng=np.random.default_rng(1))
    return [100 * float(res.confidence_interval.low),
            100 * float(res.confidence_interval.high)]


def main() -> dict:
    lib = load_c_library()
    tiers = {
        'Python': python_tier(N),
        'C extension': c_tier(lib, N),
        'Bare-metal (modelled)': bare_metal_model(N),
    }
    floors = {'Python': python_floor(N), 'C extension': c_floor(lib, N)}
    colour = {'Python': qec_style.BLUE, 'C extension': qec_style.ORANGE,
              'Bare-metal (modelled)': qec_style.AQUA}

    # --- numbers ---
    summary, curves = {}, {}
    for name, lat in tiers.items():
        vr, lo, hi, k = vr_exact(lat, TAU_DD_NS)
        summary[name] = {
            'kind': 'modelled' if 'modelled' in name else 'measured',
            'median_ns': float(np.median(lat)),
            'p99_ns': float(np.percentile(lat, 99)),
            'p999_ns': float(np.percentile(lat, 99.9)),
            'max_ns': float(lat.max()),
            'misses_at_tau_dd': k,
            'vr_at_tau_dd_pct': vr, 'vr_at_tau_dd_ci_pct': [lo, hi],
            'key_deadlines': {},
        }
        for t in KEY_TAUS_NS:
            vr_t, lo_t, hi_t, _ = vr_exact(lat, t)
            summary[name]['key_deadlines'][str(t)] = {
                'vr_pct': vr_t, 'exact_ci_pct': [lo_t, hi_t],
                'bootstrap_ci_pct': vr_bootstrap(lat, t)}
        if name in floors:
            f = floors[name]
            summary[name]['timer_floor_median_ns'] = float(np.median(f))
            summary[name]['net_decode_median_ns'] = float(np.median(lat) - np.median(f))
        curves[name] = np.array([vr_exact(lat, t) for t in TAU_GRID_NS])

    print(f"{'Tier':<23}{'median':>9}{'P99':>9}{'P99.9':>10}{'max':>11}"
          f"{'floor':>8}{'misses@40µs':>13}")
    for name, s in summary.items():
        floor_txt = f"{s.get('timer_floor_median_ns', float('nan')):8.0f}"
        print(f"{name:<23}{s['median_ns']:9.0f}{s['p99_ns']:9.0f}{s['p999_ns']:10.0f}"
              f"{s['max_ns']:11.0f}{floor_txt}{s['misses_at_tau_dd']:>8d} / {N}")

    # --- the four-panel figure ---
    fig = plt.figure(figsize=(12.5, 8.6))
    gs = gridspec.GridSpec(2, 2, hspace=0.42, wspace=0.28)
    ax_a, ax_b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    ax_c, ax_d = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])

    # (A) histograms on log-spaced bins (the tails span 4 decades)
    lo_all = min(t.min() for t in tiers.values())
    hi_all = max(t.max() for t in tiers.values())
    bins = np.logspace(np.log10(max(lo_all, 1)), np.log10(hi_all), 90)
    for name, lat in tiers.items():
        ax_a.hist(lat, bins=bins, histtype='step', lw=1.6, color=colour[name],
                  ls='--' if 'modelled' in name else '-', label=name)
    ax_a.set_xscale('log'); ax_a.set_yscale('log')
    ax_a.set_xlabel('Decode latency (ns)'); ax_a.set_ylabel('Cycles per bin')
    ax_a.set_title('(A) Latency distributions', loc='left')
    ax_a.legend(fontsize=8)

    # (B) every cycle in order; anything over 1 µs is drawn bigger so the stalls stand out
    idx = np.arange(N)
    for name in ('Python', 'C extension'):
        lat = tiers[name]
        spike = lat > 1_000
        ax_b.scatter(idx[~spike], lat[~spike], s=1.2, color=colour[name], alpha=0.5,
                     lw=0, rasterized=True)
        ax_b.scatter(idx[spike], lat[spike], s=16, color=colour[name],
                     edgecolor='white', lw=0.6, zorder=3, label=name)
    worst = int(np.argmax(tiers['Python']))
    left_half = worst < N / 2                  # put the label wherever there is room
    ax_b.annotate(f"Python max {tiers['Python'][worst] / 1e3:.1f} µs",
                  xy=(worst, tiers['Python'][worst]),
                  xytext=(worst + (900 if left_half else -900), 2.5e3),
                  ha='left' if left_half else 'right', fontsize=8.5,
                  arrowprops=dict(arrowstyle='-', color=qec_style.MUTED, lw=0.8))
    ax_b.axhline(TAU_DD_NS, color=qec_style.INK, ls=':', lw=1.2)
    ax_b.text(N, TAU_DD_NS * 1.15, 'τ$_{DD}$ = 40 µs', ha='right', fontsize=8.5)
    ax_b.set_yscale('log')
    ax_b.set_ylim(15, 1.2e5)
    ax_b.set_xlabel('Cycle index'); ax_b.set_ylabel('Decode latency (ns)')
    ax_b.set_title('(B) Jitter: every cycle in order; spikes > 1 µs enlarged', loc='left')
    ax_b.legend(fontsize=8, loc='center right', bbox_to_anchor=(1.0, 0.36))

    # (C) VR(τ) with exact 95 % bands
    floor_pct = 100 * 0.3 / N                         # bottom of the plot, just under 1 miss
    for name, cur in curves.items():
        vr, lo, hi = cur[:, 0], cur[:, 1], cur[:, 2]
        seen = vr > 0                                  # log axis: only draw where there were misses
        ax_c.fill_between(TAU_GRID_NS / 1e3, np.maximum(lo, floor_pct), hi,
                          where=seen, color=colour[name], alpha=0.15, lw=0)
        ax_c.plot(TAU_GRID_NS / 1e3, np.where(seen, vr, np.nan), color=colour[name],
                  ls='--' if 'modelled' in name else '-', lw=1.8, label=name)
    zero_hi = 100 * proportion_confint(0, N, alpha=0.05, method='beta')[1]
    ax_c.axhline(zero_hi, color=qec_style.MUTED, ls=(0, (1, 2)), lw=1)
    ax_c.axhline(P_TH_PCT, color=qec_style.INK, ls='--', lw=1)
    ax_c.text(1.5, P_TH_PCT * 1.25, 'p$_{th}$ = 1%', fontsize=8.5)
    ax_c.axvline(TAU_DD_NS / 1e3, color=qec_style.INK, ls=':', lw=1.2)
    ax_c.text(TAU_DD_NS / 1e3 * 0.88, floor_pct * 1.6, 'τ$_{DD}$', ha='right',
              fontsize=8.5)
    ax_c.set_xscale('log'); ax_c.set_yscale('log')
    ax_c.set_ylim(floor_pct, 150)
    ax_c.set_xlabel('Deadline τ (µs)'); ax_c.set_ylabel('VR(τ) = P(L > τ)  (%)')
    ax_c.set_title('(C) Violation rate; bands = exact 95% CI', loc='left')
    ax_c.legend(fontsize=8, loc='upper right')

    # (D) a small summary table
    ax_d.axis('off')
    rows = []
    for name, s in summary.items():
        ci = s['vr_at_tau_dd_ci_pct']
        rows.append([name.replace(' (modelled)', '*'),
                     f"{s['median_ns']:.0f}",
                     f"{s.get('timer_floor_median_ns', float('nan')):.0f}"
                     if 'timer_floor_median_ns' in s else '—',
                     f"{s['p99_ns']:.0f}", f"{s['max_ns']:,.0f}",
                     f"{s['vr_at_tau_dd_pct']:.2f} [{ci[0]:.2f}, {ci[1]:.3f}]"])
    tbl = ax_d.table(cellText=rows,
                     colLabels=['Tier', 'Median', 'Timer\nfloor', 'P99', 'Max',
                                'VR@40 µs (%)\n[95% CI]'],
                     colWidths=[0.21, 0.12, 0.11, 0.09, 0.14, 0.33],
                     loc='center', cellLoc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(8.5); tbl.scale(1, 2.0)
    for (r, _c), cell in tbl.get_celld().items():
        cell.set_edgecolor(qec_style.GRID)
        if r == 0:
            cell.set_text_props(weight='bold')
    ax_d.set_title('(D) Summary (ns unless stated)', loc='left')
    ax_d.text(0.0, 0.10, '* modelled, not measured: Cortex-M7 at 480 MHz, 41-cycle WCET',
              transform=ax_d.transAxes, fontsize=8, color=qec_style.MUTED)
    ax_d.text(0.0, 0.03, f'Dotted line in (C): 95% upper bound on VR when 0 of {N:,} '
              f'cycles miss ({zero_hi:.3f}%)', transform=ax_d.transAxes, fontsize=8,
              color=qec_style.MUTED)

    fig.suptitle(f'Decode latency, {N:,} cycles per tier — Swayam Shakya',
                 x=0.06, y=0.97, ha='left', fontsize=12, fontweight='bold')
    fig.subplots_adjust(top=0.90)
    qec_style.save(fig, 'fig3_main_result')

    # --- save the raw data too, plus enough about the machine to compare runs ---
    clock = time.get_clock_info('perf_counter')
    save = {
        'author': 'Swayam Shakya',
        'experiment': 'Weekend 3.2 — three-tier decode latency',
        'n': N, 'warmup': WARMUP, 'tau_dd_ns': TAU_DD_NS,
        'environment': {
            'python': sys.version.split()[0],
            'platform': platform.platform(),
            'machine': platform.machine(),
            'cpu_count': os.cpu_count(),
            'perf_counter_resolution_s': clock.resolution,
            'perf_counter_implementation': clock.implementation,
        },
        'latencies_ns': {k: v.tolist() for k, v in tiers.items()},
        'timer_floor_ns': {k: v.tolist() for k, v in floors.items()},
        'summary': summary,
        'vr_curve': {'tau_ns': TAU_GRID_NS.tolist(),
                     **{k: v[:, :3].tolist() for k, v in curves.items()}},
    }
    with open('w3_latencies.json', 'w') as fh:
        json.dump(save, fh)
    print('Saved: w3_latencies.json')
    return save


def repeat_study(repeats: int) -> dict:
    """Run the two measured tiers again `repeats` times. One run's worst stall
    turned out to be a pretty random number, so I wanted to see the spread."""
    lib = load_c_library()
    runs = {'Python': [], 'C extension': []}
    for r in range(repeats):
        for name, lat in (('Python', python_tier(N)), ('C extension', c_tier(lib, N))):
            runs[name].append({'median_ns': float(np.median(lat)),
                               'p99_ns': float(np.percentile(lat, 99)),
                               'p999_ns': float(np.percentile(lat, 99.9)),
                               'max_ns': float(lat.max()),
                               'misses_at_tau_dd': int(np.sum(lat > TAU_DD_NS))})
        print(f"run {r + 1}/{repeats}: " + "   ".join(
            f"{k}: median {v[-1]['median_ns']:.0f} ns, max {v[-1]['max_ns'] / 1e3:.1f} µs, "
            f"misses {v[-1]['misses_at_tau_dd']}" for k, v in runs.items()))
    pooled = {k: {'total_misses': sum(x['misses_at_tau_dd'] for x in v),
                  'total_cycles': N * repeats} for k, v in runs.items()}
    for k, v in pooled.items():
        lo, hi = proportion_confint(v['total_misses'], v['total_cycles'], method='beta')
        v['vr_pct'] = 100 * v['total_misses'] / v['total_cycles']
        v['vr_ci_pct'] = [100 * lo, 100 * hi]
        print(f"{k:<12} pooled VR@40 µs = {v['vr_pct']:.4f}%  "
              f"(95% CI {100 * lo:.4f}–{100 * hi:.4f}%, {v['total_misses']} of "
              f"{v['total_cycles']:,})")
    out = {'author': 'Swayam Shakya', 'repeats': repeats, 'n_per_run': N,
           'runs': runs, 'pooled': pooled}
    with open('w3_repeats.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print('Saved: w3_repeats.json')
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Decode-latency profiler (Weekend 3.2).')
    parser.add_argument('--repeats', type=int, metavar='N',
                        help='repeat the measured tiers N times instead of the main run')
    args = parser.parse_args()
    if args.repeats is not None:
        if args.repeats < 1:
            parser.error('--repeats must be at least 1')
        repeat_study(args.repeats)
    else:
        main()
