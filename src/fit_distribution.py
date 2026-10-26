"""
fit_distribution.py - Weekend 3, Experiment 3.1
What shape does the decode-latency distribution have, and how fat is its tail?
Author: Swayam Shakya

Usage:  python fit_distribution.py [w2_latencies.json]

What I check:
  * Anderson-Darling on log(latency): is it log-normal?
  * Kolmogorov-Smirnov against log-normal, gamma and Weibull. The parameters
    are fitted to the same data first, which makes the KS p-values too kind,
    so I mostly look at D (the KS distance) to rank the families.
  * Hill estimator on the slowest 5% of cycles -> tail index alpha:
        alpha > 4       light tail (all the usual moments are finite)
        2 < alpha <= 4  moderate tail (variance OK, higher moments shaky)
        alpha <= 2      heavy tail (infinite variance, rare huge stalls dominate)

Writes: w3_fit.json
"""
import json
import sys

import numpy as np
from scipy import stats


def load_latencies(path: str = 'w2_latencies.json') -> np.ndarray:
    with open(path) as fh:
        return np.asarray(json.load(fh)['latencies_ns'], dtype=float)


def hill_tail_index(x: np.ndarray, k_frac: float = 0.05) -> float:
    """Hill (1975) estimator using the k = k_frac * n largest values."""
    s = np.sort(x[x > 0])[::-1]                       # largest first
    k = max(2, int(len(s) * k_frac))
    log_excess = np.log(s[:k]) - np.log(s[k])        # s[k] is the (k+1)-th largest
    mean_excess = float(np.mean(log_excess))
    return float('inf') if mean_excess == 0 else 1.0 / mean_excess


def tail_class(alpha: float) -> str:
    if alpha > 4:
        return 'light'
    if alpha > 2:
        return 'moderate'
    return 'heavy'


def fit_and_report(lat: np.ndarray) -> dict:
    lat = lat[lat > 0]
    # SciPy 1.17 deprecated the old critical-value output of anderson().
    # method='interpolate' gives a p-value read off the published tables; it is
    # clipped to [0.01, 0.15], so a value of 0.01 really means "p <= 0.01".
    ad = stats.anderson(np.log(lat), dist='norm', method='interpolate')
    ad_pass = bool(ad.pvalue > 0.05)

    ks = {}
    for name, dist in [('lognorm', stats.lognorm),
                       ('gamma', stats.gamma),
                       ('weibull_min', stats.weibull_min)]:
        params = dist.fit(lat, floc=0)
        # pass the cdf itself - kstest(lat, 'weibull') crashes, SciPy has no such name
        res = stats.kstest(lat, dist.cdf, args=params)
        ks[name] = {'D': float(res.statistic), 'p': float(res.pvalue)}

    alpha = hill_tail_index(lat)
    print('--- Distribution fitting ---')
    print(f"n = {lat.size:,}   median = {np.median(lat):.0f} ns")
    p_txt = f"≤ {ad.pvalue:.2f}" if ad.pvalue <= 0.01 else f"= {ad.pvalue:.2f}"
    print(f"Anderson–Darling on log(L): A² = {ad.statistic:.2f}   p {p_txt}   "
          f"log-normal accepted at 5%: {ad_pass}")
    for name, r in ks.items():
        print(f"KS {name:<12} D = {r['D']:.4f}   p = {r['p']:.2e}")
    best = min(ks, key=lambda n: ks[n]['D'])
    print(f"Closest family by KS distance: {best}")
    print(f"Hill tail index (top 5%): α = {alpha:.2f}  → {tail_class(alpha)} tail")
    return {'n': int(lat.size), 'ad_stat': float(ad.statistic), 'ad_p': float(ad.pvalue),
            'ad_lognormal_pass': ad_pass, 'ks': ks, 'best_ks': best,
            'hill_alpha': alpha, 'tail_class': tail_class(alpha)}


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'w2_latencies.json'
    out = fit_and_report(load_latencies(path))
    out['source'] = path
    out['author'] = 'Swayam Shakya'
    with open('w3_fit.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print('Saved: w3_fit.json')
