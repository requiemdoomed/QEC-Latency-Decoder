# Reproducibility runs

Summaries of six complete runs of the timing experiments (Experiment 3.2 plus its ten-run repeat study, 110,000 cycles per tier each). The paper pools these in its reproducibility table.

| Run | Date | Host | Python | Note |
|---|---|---|---|---|
| `run0_reference` | 2026-10-14 | Intel Xeon 2.1 GHz, 2 vCPUs | 3.12.3 | reference run, identical to `reference_results/` |
| `run1` | 2026-10-14 | Intel Xeon 2.1 GHz, 2 vCPUs | 3.13.16 | clean rerun of the published code |
| `run2` | 2026-10-14 | Intel Xeon 2.1 GHz, 2 vCPUs | 3.13.16 | clean rerun of the published code |
| `run3` | 2026-10-26 | Intel Xeon 2.8 GHz, 2 vCPUs | 3.13.16 | clean rerun after the repository refactor |
| `run4` | 2026-11-11 | Intel Xeon 2.1 GHz, 2 vCPUs | 3.13.16 | fresh clone of this GitHub repository |
| `run5` | 2026-11-11 | Intel Xeon 2.1 GHz, 2 vCPUs | 3.13.16 | final audit of the finished repository (CPU model recorded automatically) |

Each folder has `paper_stats.json` (main run), `w3_repeats.json` (repeat study) and `environment.json`. The raw per-cycle latencies of the reference run are in `reference_results/w3_latencies.json`.
