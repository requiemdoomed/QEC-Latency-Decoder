"""
analysis_paper_ready.py - the final statistics, Table 1 and Figure 4
Author: Swayam Shakya

Reads  : w3_latencies.json (needed), w3_repeats.json (used if it's there)
Writes : paper_stats.json, table1.tex, fig4_tail_diagnostics.pdf/.png

For every tier I report
  * median, P99, P99.9 and max
  * the Hill tail index alpha (top 5%) and Anderson-Darling on log(latency)
  * stalls: cycles slower than 1 us. These look like a separate population
    (OS preemption, interrupts, hypervisor steal time), not just "a slow decode"
  * tau* = the deadline where VR(tau*) = 1%, which is simply the 99th
    percentile, with a percentile-bootstrap 95% CI. Bootstrap is fine for a
    quantile; for VR at a fixed deadline I use the exact binomial interval.
  * headroom = 40 us / tau*: how many times over the budget is met

Python vs C (both measured) gets a Mann-Whitney U test with the rank-biserial
effect size r = 2*U1/(n1*n2) - 1. r > 0 means Python tends to be slower, and
r = 1 would mean every single Python cycle was slower than every C cycle.
The modelled bare-metal tier is shown for scale only and never tested.
"""
import json
import os

import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportion_confint

import qec_style

qec_style.apply()
import matplotlib.pyplot as plt  # noqa: E402

P_TH = 0.01
TAU_DD_NS = 40_000
STALL_NS = 1_000      # slower than 1 µs = a stall, not just a slow lookup


def hill_alpha(x: np.ndarray, k_frac: float = 0.05) -> float:
    s = np.sort(x[x > 0])[::-1]
    k = max(2, int(len(s) * k_frac))
    m = float(np.mean(np.log(s[:k]) - np.log(s[k])))
    return float('inf') if m == 0 else 1.0 / m


def tau_star(x: np.ndarray, rng: np.random.Generator):
    """P99 plus a bootstrap 95 % CI (5,000 resamples)."""
    res = stats.bootstrap((x,), lambda a, axis: np.percentile(a, 99, axis=axis),
                          n_resamples=5000, method='percentile', rng=rng)
    return (float(np.percentile(x, 99)),
            [float(res.confidence_interval.low), float(res.confidence_interval.high)])


def main() -> dict:
    with open('w3_latencies.json') as fh:
        raw = json.load(fh)
    tiers = {k: np.asarray(v, dtype=float) for k, v in raw['latencies_ns'].items()}
    kinds = {k: raw['summary'][k]['kind'] for k in tiers}
    rng = np.random.default_rng(2026)

    results = {}
    print(f"{'Tier':<23}{'median':>8}{'P99=τ*':>9}{'95% CI of τ*':>18}{'headroom':>10}"
          f"{'Hill α':>8}{'VR@40µs':>10}")
    for name, lat in tiers.items():
        ad = stats.anderson(np.log(lat[lat > 0]), dist='norm', method='interpolate')
        t_star, t_ci = tau_star(lat, rng)
        k = int(np.sum(lat > TAU_DD_NS))
        lo, hi = proportion_confint(k, lat.size, alpha=0.05, method='beta')
        results[name] = {
            'kind': kinds[name], 'n': int(lat.size),
            'median_ns': float(np.median(lat)),
            'p99_ns': t_star, 'p999_ns': float(np.percentile(lat, 99.9)),
            'max_ns': float(lat.max()),
            'tau_star_ns': t_star, 'tau_star_ci_ns': t_ci,
            'headroom_x': TAU_DD_NS / t_star,
            'hill_alpha': hill_alpha(lat),
            'ad_stat': float(ad.statistic), 'ad_p': float(ad.pvalue),
            'misses_at_tau_dd': k,
            'stalls_over_1us': int(np.sum(lat > STALL_NS)),
            'stall_median_ns': (float(np.median(lat[lat > STALL_NS]))
                                if np.any(lat > STALL_NS) else None),
            'vr_at_tau_dd_pct': 100 * k / lat.size,
            'vr_at_tau_dd_ci_pct': [100 * lo, 100 * hi],
        }
        r = results[name]
        print(f"{name:<23}{r['median_ns']:8.0f}{t_star:9.0f}"
              f"{f'[{t_ci[0]:.0f}, {t_ci[1]:.0f}]':>18}{r['headroom_x']:9.0f}×"
              f"{r['hill_alpha']:8.2f}{r['vr_at_tau_dd_pct']:9.2f}%")

    print(f"\nStalls (L > {STALL_NS / 1e3:.0f} µs): " + "   ".join(
        f"{n}: {r['stalls_over_1us']} of {r['n']:,}"
        + (f", median {r['stall_median_ns'] / 1e3:.1f} µs" if r['stall_median_ns'] else '')
        for n, r in results.items()))

    # --- Python vs C ---
    a, b = tiers['Python'], tiers['C extension']
    mw = stats.mannwhitneyu(a, b, alternative='two-sided')
    r_rb = 2 * mw.statistic / (a.size * b.size) - 1
    comparison = {'comparison': 'Python vs C extension', 'U': float(mw.statistic),
                  'p': float(mw.pvalue), 'rank_biserial_r': float(r_rb),
                  'median_ratio': float(np.median(a) / np.median(b))}
    print(f"\nMann–Whitney U (Python vs C): U = {mw.statistic:.0f}, p = {mw.pvalue:.2e}, "
          f"r_rb = {r_rb:+.3f}, median ratio = {comparison['median_ratio']:.1f}×")

    repeats = None
    if os.path.exists('w3_repeats.json'):
        with open('w3_repeats.json') as fh:
            repeats = json.load(fh)['pooled']
        for name, v in repeats.items():
            print(f"Repeats, {name}: {v['total_misses']} misses in {v['total_cycles']:,} "
                  f"cycles → VR@40 µs ≤ {v['vr_ci_pct'][1]:.4f}% (95% upper bound)")

    # --- Figure 4: survival curves on log-log axes, and τ* per tier ---
    colour = {'Python': qec_style.BLUE, 'C extension': qec_style.ORANGE,
              'Bare-metal (modelled)': qec_style.AQUA}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.6),
                                   gridspec_kw={'width_ratios': [1.25, 1]})
    for name, lat in tiers.items():
        s = np.sort(lat)
        surv = 1.0 - np.arange(s.size) / s.size
        ls = '--' if kinds[name] == 'modelled' else '-'
        ax1.step(s, surv, where='post', color=colour[name], ls=ls, lw=1.6, label=name)
        if kinds[name] == 'measured':                 # the power law Hill fitted to the top 5 %
            k = int(0.05 * s.size)
            x0 = s[-k - 1]
            xs = np.logspace(np.log10(x0), np.log10(s[-1]), 50)
            ax1.plot(xs, 0.05 * (xs / x0) ** (-results[name]['hill_alpha']),
                     color=colour[name], lw=0.9, ls=':')
    ax1.axvline(TAU_DD_NS, color=qec_style.INK, ls=':', lw=1.2)
    ax1.text(TAU_DD_NS * 0.85, 0.5, 'τ$_{DD}$', ha='right', fontsize=8.5)
    ax1.axhline(P_TH, color=qec_style.INK, ls='--', lw=1)
    ax1.text(22, P_TH * 1.3, 'p$_{th}$ = 1%', fontsize=8.5)
    ax1.set_xscale('log'); ax1.set_yscale('log')
    ax1.set_ylim(5e-5, 1.5)
    ax1.set_xlabel('Latency L (ns)'); ax1.set_ylabel('P(L > x)')
    ax1.set_title('(A) Survival curves; dotted = Hill power-law fit to top 5%', loc='left')
    ax1.legend(fontsize=8, loc='lower left')

    names = list(tiers)
    ypos = np.arange(len(names))[::-1]
    for y, name in zip(ypos, names):
        r = results[name]
        ax2.errorbar(r['tau_star_ns'], y,
                     xerr=[[r['tau_star_ns'] - r['tau_star_ci_ns'][0]],
                           [r['tau_star_ci_ns'][1] - r['tau_star_ns']]],
                     fmt='o', color=colour[name], ms=7, capsize=3, lw=1.5)
        ax2.text(r['tau_star_ns'] * 1.6, y + 0.18,
                 f"τ* = {r['tau_star_ns']:.0f} ns  ({r['headroom_x']:,.0f}× headroom)",
                 fontsize=8.5, color=qec_style.INK)
    ax2.axvline(TAU_DD_NS, color=qec_style.INK, ls=':', lw=1.2)
    ax2.text(TAU_DD_NS * 0.85, ypos[-1] - 0.42, 'τ$_{DD}$ = 40 µs', ha='right', fontsize=8.5)
    ax2.set_yticks(ypos, [n.replace(' (modelled)', '*') for n in names])
    ax2.set_xscale('log'); ax2.set_xlim(20, 1.5e5); ax2.set_ylim(-0.7, len(names) - 0.3)
    ax2.set_xlabel('τ* = deadline where VR(τ*) = 1%  (ns, log scale)')
    ax2.set_title('(B) Threshold crossover τ* with bootstrap 95% CI', loc='left')
    ax2.grid(axis='y', visible=False)
    fig.text(0.53, -0.02, '* modelled, not measured', fontsize=8, color=qec_style.MUTED)
    fig.tight_layout()
    qec_style.save(fig, 'fig4_tail_diagnostics')

    # --- LaTeX Table 1, ready to paste (needs booktabs, amsmath, textcomp) ---
    lines = []
    for name, r in results.items():
        lo, hi = r['vr_at_tau_dd_ci_pct']
        label = name.replace(' (modelled)', '$^{*}$')
        lines.append(f"    {label} & {r['median_ns']:.0f} & {r['p99_ns']:.0f} & "
                     f"{r['max_ns']:,.0f} & {r['vr_at_tau_dd_pct']:.2f} "
                     f"[{lo:.2f}, {hi:.3f}] & {r['hill_alpha']:.2f} \\\\")
    latex = "\n".join([
        "% Table 1 — QEC decode latency summary. Author: Swayam Shakya",
        "% Requires \\usepackage{booktabs, amsmath, textcomp}",
        "\\begin{table}[t]",
        "  \\centering",
        "  \\caption{Decode latency by implementation tier ($n = 10\\,000$ cycles each).",
        "    VR is the share of cycles slower than $\\tau_{\\mathrm{DD}} = T_2/N = "
        "40\\,\\text{\\textmu s}$,",
        "    with an exact (Clopper--Pearson) 95\\% interval. $^{*}$Modelled, not measured.}",
        "  \\label{tab:latency}",
        "  \\begin{tabular}{lrrrlr}",
        "    \\toprule",
        "    Tier & Median (ns) & P99 (ns) & Max (ns) & VR@40\\,\\textmu s (\\%) "
        "& Hill $\\alpha$ \\\\",
        "    \\midrule",
        *lines,
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
        ""])
    with open('table1.tex', 'w') as fh:
        fh.write(latex)
    print('Saved: table1.tex')

    out = {'author': 'Swayam Shakya', 'tiers': results, 'mann_whitney': comparison,
           'repeats_pooled': repeats}
    with open('paper_stats.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print('Saved: paper_stats.json')
    return out


if __name__ == '__main__':
    main()
