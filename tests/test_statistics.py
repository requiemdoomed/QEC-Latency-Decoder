"""The statistics, checked on data where I know the right answer.
Author: Swayam Shakya"""
import numpy as np
import pytest

import analysis_paper_ready as analysis
import experiment_1_1_coherence as exp11
import experiment_3_jitter_profiler as prof
import fit_distribution as fd


def test_hill_estimator_recovers_a_known_pareto_tail():
    rng = np.random.default_rng(0)
    alpha = 3.0
    x = (1.0 / rng.random(200_000)) ** (1.0 / alpha)      # Pareto, tail index 3
    assert fd.hill_tail_index(x) == pytest.approx(alpha, rel=0.08)
    assert analysis.hill_alpha(x) == pytest.approx(fd.hill_tail_index(x))


def test_tail_classes():
    assert fd.tail_class(5) == 'light'
    assert fd.tail_class(3) == 'moderate'
    assert fd.tail_class(1.5) == 'heavy'


def test_lognormal_data_is_recognised_as_lognormal():
    lat = np.random.default_rng(1).lognormal(mean=6.0, sigma=0.3, size=5000)
    out = fd.fit_and_report(lat)
    assert out['best_ks'] == 'lognorm'


def test_zero_misses_still_gets_an_honest_upper_bound():
    lat = np.full(10_000, 100.0)                           # nothing ever misses
    vr, lo, hi, k = prof.vr_exact(lat, 40_000)
    assert k == 0 and vr == 0 and lo == 0
    assert hi == pytest.approx(100 * 3.689 / 10_000, rel=0.01)   # about 3.7 / n
    assert prof.vr_bootstrap(lat, 40_000) is None          # bootstrap can't say anything


def test_one_miss_exact_interval_contains_the_estimate():
    lat = np.full(10_000, 100.0)
    lat[123] = 50_000.0
    vr, lo, hi, k = prof.vr_exact(lat, 40_000)
    assert k == 1 and lo < vr < hi


def test_tau_star_is_the_99th_percentile():
    x = np.arange(1, 10_001, dtype=float)
    t, (lo, hi) = analysis.tau_star(x, np.random.default_rng(0))
    assert t == pytest.approx(np.percentile(x, 99))
    assert lo <= t <= hi


def test_ramsey_model_and_deadline():
    assert exp11.fidelity_model(0, 120) == pytest.approx(1.0)
    assert exp11.fidelity_model(1e9, 120) == pytest.approx(0.5)
    assert exp11.TAU_DD_US == pytest.approx(40.0)


def test_bare_metal_model_is_around_its_wcet():
    lat = prof.bare_metal_model(20_000)
    assert np.median(lat) == pytest.approx(41 / 480e6 * 1e9, rel=0.01)
