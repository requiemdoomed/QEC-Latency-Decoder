"""Page content, part B: the four experiment parts and reproducibility. Author: Swayam Shakya"""

W1 = r"""
<section class="page" id="physical" aria-labelledby="h-physical">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-blue">Part 1</span><span>Coherence and error sensitivity</span></div>
    <h1 id="h-physical">Physical layer</h1>
    <p class="lede">Before timing anything, it helps to see the clock the decoder is racing: a Ramsey measurement
      recovers T₂ from the noise model, and a Pauli experiment shows which errors a superposition can feel.</p>
  </header>

  <h2>Shared figure style</h2>
  <p>Every plotting script imports this small module, so all figures share fonts, colours and file formats
    (a vector PDF and a PNG preview). Its three series colours stay distinguishable under the common forms of
    colour-vision deficiency.</p>
  {{code:qec_style.py}}

  <h2>Experiment 1.1 — Ramsey coherence decay</h2>
  <p>Prepare |+⟩, idle for d gates of 50 ns each, rotate back and measure. Only the idle gates carry thermal
    relaxation, so the idle time t = d × 50 ns is exact and a one-parameter fit of equation [1] returns T₂.
    Twenty-five idle times span 0–300 µs, enough to see the full decay.</p>
  {{code:experiment_1_1_coherence.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <p>Fitted <strong>T₂ = 121.5 ± 1.3 µs</strong> against a model value of 120 µs (1.2 standard errors). At the
      40 µs deadline the fidelity is <strong>0.860</strong>; after a full three-round cycle (120 µs) it is 0.686,
      which is why the deadline divides T₂ instead of spending it in one round.</p>
    {{fig:fig1|Figure 2. Ramsey decay: 25 idle times, 4,096 shots each, with the fitted curve and the 40 µs deadline.}}
  </div>
  <div class="warn-box"><strong>Why |+⟩ and not |0⟩.</strong> Thermal relaxation pulls qubits toward |0⟩, so a
    qubit that starts there never decays, and the fit runs off to the optimiser's bound (T₂ = 44,142 µs).</div>

  <h2>Experiment 1.2 — Which Pauli errors does |+⟩ feel?</h2>
  <p>Put one idle gate between two Hadamards and give it a Pauli channel: operator P with probability p,
    identity otherwise. X leaves |+⟩ unchanged; Y and Z turn it into |−⟩. The noise must sit on the idle gate
    only: on the Hadamards, an X error after the second one flips the readout and fakes a sensitivity to X.</p>
  {{code:experiment_1_2_pauli_sensitivity.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <p><strong>X: survival 1.000 at every p.</strong> Y and Z: every point within 0.0123 of 1 − p. The bit-flip
      code corrects exactly the error |+⟩ cannot feel and is blind to the ones it can, which is why codes that
      protect superpositions also need phase checks.</p>
    {{fig:fig2|Figure 3. Survival of |+⟩ under one Pauli channel; 11 values of p, 8,192 shots each.}}
  </div>
</section>
"""

W2 = r"""
<section class="page" id="code" aria-labelledby="h-code">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-purple">Part 2</span><span>Syndrome extraction and decoding</span></div>
    <h1 id="h-code">The three-qubit code</h1>
    <p class="lede">Build the code, check that its decoder picks the right correction under noise, and confirm that
      it actually suppresses errors.</p>
  </header>

  <h2>Experiment 2.1 — The BitFlipCode class</h2>
  <p>Each cycle encodes |1⟩<sub>L</sub>, injects no error or one random X error, extracts the syndrome on two
    ancillas under thermal-relaxation noise, runs one shot and decodes. Only the decode step sits between the
    two clock reads. Every cycle gets a fresh simulator seed: with one fixed seed, Aer would replay the same
    noise every cycle.</p>
  {{code:bit_flip_code.py}}
  <div class="result">
    <div class="result-head">Reference run · 10,000 cycles</div>
    <p>The decoder chose the matching correction in <strong>98.61%</strong> of cycles (Wilson 95% CI
      98.36–98.82%). Failures are spread evenly over every injected case, so they come from relaxation during
      the six 500 ns CNOTs, not from the table.</p>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Injected ↓ / decoded →</th><th>none</th><th>q₀</th><th>q₁</th><th>q₂</th><th>Correct</th></tr></thead>
      <tbody>
        <tr><td>none</td><td><strong>2,499</strong></td><td>12</td><td>11</td><td>12</td><td>98.62%</td></tr>
        <tr><td>q₀</td><td>15</td><td><strong>2,482</strong></td><td>23</td><td>7</td><td>98.22%</td></tr>
        <tr><td>q₁</td><td>10</td><td>7</td><td><strong>2,459</strong></td><td>10</td><td>98.91%</td></tr>
        <tr><td>q₂</td><td>15</td><td>8</td><td>9</td><td><strong>2,421</strong></td><td>98.70%</td></tr>
      </tbody>
    </table></div>
    <p>Decode time inside the full cycle: median 716 ns, P99 1,193 ns. One cycle took 104 µs and missed the
      40 µs deadline, a first sign of the tail studied in Part 3.</p>
  </div>

  <h2>Experiment 2.2 — Logical versus physical error</h2>
  <p>Does the code help? Give each data qubit an independent X error with probability p, extract the
    syndrome, correct in real time with <code>if_test</code>, and read out. Theory (equation [4]) predicts
    3p² − 2p³.</p>
  {{code:experiment_2_2_logical_error.py}}
  <div class="result">
    <div class="result-head">Reference run · 11 values of p × 100,000 shots</div>
    <p>All 11 points contain the theory value inside their 95% interval. At p = 1% the logical failure rate is
      <strong>0.039%</strong> (95% CI 0.029–0.053%), <strong>25× fewer failures</strong> than a bare qubit; at
      p = 10% the gain is 3.6×; at p = 50% it is gone.</p>
    {{fig:fig2b|Figure 4. Logical failure versus physical bit-flip probability, log-log; bars are Wilson 95% intervals.}}
  </div>
</section>
"""

W3 = r"""
<section class="page" id="latency" aria-labelledby="h-latency">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-green">Part 3</span><span>Timing analysis</span></div>
    <h1 id="h-latency">Decoder latency</h1>
    <p class="lede">How long does decoding take, how often is it late, and what shape does the tail have?</p>
  </header>

  <h2>Experiment 3.1 — Distribution fitting</h2>
  <p>Fit log-normal, gamma and Weibull distributions to the Experiment 2.1 latencies and estimate the tail
    index. Kolmogorov–Smirnov p-values are too kind once the parameters come from the same data, so the KS
    distance D is used to rank the families.</p>
  {{code:fit_distribution.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <p>Closest family by KS distance: <strong>log-normal</strong> (D = 0.103, against 0.177 for gamma and 0.333
      for Weibull). Anderson–Darling still rejects exact log-normality (A² = 245, p ≤ 0.01). Hill index on the
      top 5%: <strong>α = 4.09</strong>, at the light/moderate boundary.</p>
  </div>

  <h2>Experiment 3.2 — Three tiers, timer floors and VR(τ)</h2>
  <p>The same look-up table runs as a Python dictionary and as compiled C called through ctypes; a modelled
    microcontroller tier (Cortex-M7, 41-cycle worst case = 85.4 ns, 5% jitter) sets the scale. Each measured
    tier also records its timer floor, two clock reads with nothing between them, and every run stores the
    CPU model and Python version it came from. The C library:</p>
  {{code:qec_decode.c}}
  <pre class="cmd"><code>mkdir -p build
gcc -O2 -shared -fPIC -o build/qec_decode.so src/qec_decode.c    # run_all.sh does this for you</code></pre>
  {{code:experiment_3_jitter_profiler.py}}
  <div class="result">
    <div class="result-head">Reference run · 10,000 timed cycles per tier after 1,000 warm-up</div>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Tier</th><th>Median</th><th>Timer floor</th><th>P99 = τ*</th><th>P99.9</th><th>Max</th><th>Misses at 40 µs</th><th>VR@40 µs, 95% CI</th></tr></thead>
      <tbody>
        <tr><td>Python</td><td class="mono">113 ns</td><td class="mono">63 ns</td><td class="mono">268 ns</td><td class="mono">481 ns</td><td class="mono">41.8 µs</td><td>1 of 10,000</td><td class="mono">0.01% [0.0003, 0.056]</td></tr>
        <tr><td>C</td><td class="mono">31 ns</td><td class="mono">26 ns</td><td class="mono">46 ns</td><td class="mono">113 ns</td><td class="mono">23.0 µs</td><td>0 of 10,000</td><td class="mono">0% [0, 0.037]</td></tr>
        <tr><td>Microcontroller (modelled)</td><td class="mono">85 ns</td><td class="mono">—</td><td class="mono">95 ns</td><td class="mono">99 ns</td><td class="mono">0.10 µs</td><td>0 of 10,000</td><td class="mono">0% [0, 0.037]</td></tr>
      </tbody>
    </table></div>
    <p>Typical decodes are about 350× (Python) and 1,300× (C) inside the budget, and most of what both tiers
      measure is the clock itself: about 50 ns and 5 ns of real work. The risk sits in a separate population
      of stalls (7 Python cycles and 1 C cycle over 1 µs in this run) that strike both tiers.</p>
    {{fig:fig3|Figure 5. (A) latency distributions, (B) every cycle in order, (C) VR(τ) with exact 95% bands, (D) summary.}}
  </div>
  <div class="note"><strong>Exact versus bootstrap intervals.</strong> With one observed miss, the bootstrap
    interval for VR@40 µs is [0, 0.03%] and the exact interval is [0.0003, 0.056%]: resampling cannot invent
    misses it never saw. With zero misses the bootstrap collapses to [0, 0].</div>

  <h2>Final statistics</h2>
  <p>One script turns the timing data into the final statistics: τ* with bootstrap intervals, tail
    diagnostics, the Python-versus-C test and a LaTeX table.</p>
  {{code:analysis_paper_ready.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Tier</th><th>τ* = P99, 95% CI</th><th>Headroom vs 40 µs</th><th>Hill α</th><th>Stalls &gt; 1 µs</th></tr></thead>
      <tbody>
        <tr><td>Python</td><td class="mono">268 ns [248, 290]</td><td class="mono">149×</td><td class="mono">3.95</td><td>7 (median 13.1 µs)</td></tr>
        <tr><td>C</td><td class="mono">46 ns [45, 47]</td><td class="mono">870×</td><td class="mono">7.93</td><td>1 (23.0 µs)</td></tr>
        <tr><td>Microcontroller (modelled)</td><td class="mono">95 ns [95, 96]</td><td class="mono">420×</td><td class="mono">52.7</td><td>0</td></tr>
      </tbody>
    </table></div>
    <p>Python versus C: Mann–Whitney p &lt; 10⁻³⁰⁰, rank-biserial r = +0.998, median ratio 3.6×. Below a
      survival probability of about 10⁻³ the curves leave the Hill fit and flatten into the stall plateau, so
      VR at large τ has to be counted directly, never extrapolated from a fitted tail.</p>
    {{fig:fig4|Figure 6. (A) survival curves with Hill power-law fits to the top 5%; (B) τ* per tier against the deadline.}}
  </div>
</section>
"""

W4 = r"""
<section class="page" id="devices" aria-labelledby="h-devices">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-yellow">Part 4</span><span>Dynamic circuits on device noise</span></div>
    <h1 id="h-devices">Device replicas</h1>
    <p class="lede">Run the code with real-time feed-forward on a calibrated replica of an IBM device (no account
      needed), or on the device itself, and measure what decoder latency costs.</p>
  </header>

  <h2>The protocol</h2>
  <p>One job holds three circuits, each prepared in logical |1⟩, on one fixed physical layout:</p>
  <ul>
    <li><strong>bare</strong>: one physical qubit (the one data qubit 0 uses) idling exactly as long as the
      encoded circuit's encode-and-syndrome stage, with a <code>delay</code> the transpiler cannot remove;</li>
    <li><strong>offline</strong>: encoded, syndrome measured, no feed-forward; the syndrome is decoded afterwards
      in software, shot by shot;</li>
    <li><strong>realtime</strong>: encoded, syndrome measured, correction applied by three <code>if_test</code> blocks.</li>
  </ul>
  <p>They give four read-outs: bare, majority vote alone, offline decode and real-time correction. The
    <code>sweep</code> mode inserts a wait of 0–80 µs between the syndrome readout and the correction, a stand-in
    for decoder latency that the replica's noise model can see.</p>
  {{fig:fig0|Figure 7. The protected circuit: encode |111⟩, two parity checks, real-time correction, readout.}}
  {{code:experiment_4_real_hardware.py}}

  <h2>Run it</h2>
  <pre class="cmd"><code>python src/experiment_4_real_hardware.py local FakeKingston      # Heron r2 replica
python src/experiment_4_real_hardware.py local FakeSherbrooke    # Eagle r3 replica
python src/experiment_4_real_hardware.py sweep FakeKingston      # latency sweep
python src/experiment_4_real_hardware.py draw                    # the circuit figure</code></pre>

  <div class="result">
    <div class="result-head">Reference run · 4,000 shots per circuit</div>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Device replica</th><th>Bare</th><th>Majority only</th><th>Offline decode</th><th>Real-time</th><th>Real-time − bare</th><th>Real-time − offline</th></tr></thead>
      <tbody>
        <tr><td>Heron r2 (FakeKingston)</td><td class="mono">97.88%</td><td class="mono">99.72%</td><td class="mono">99.70%</td><td class="mono">99.55%</td><td class="mono">+1.68 pp, p = 6×10⁻¹¹</td><td class="mono">−0.15 pp, p = 0.36</td></tr>
        <tr><td>Eagle r3 (FakeSherbrooke)</td><td class="mono">97.38%</td><td class="mono">99.28%</td><td class="mono">99.10%</td><td class="mono">99.00%</td><td class="mono">+1.62 pp, p = 8×10⁻⁸</td><td class="mono">−0.10 pp, p = 0.73</td></tr>
      </tbody>
    </table></div>
    <p>The code helps clearly on both devices. Real-time and offline correction tie because the replica adds
      no noise during the feedback window. In one round that ends with reading the data qubits, a majority
      vote already undoes any single flip, so the syndrome adds nothing here; it matters when the state must
      survive further rounds.</p>
    {{fig:fig5|Figure 8. Logical |1⟩ fidelity by protocol on the Heron r2 replica, Wilson 95% intervals.}}
    <p><strong>Latency sweep.</strong> Logical error starts at 0.45% (Heron) and 1.00% (Eagle), <strong>doubles
      after a 7.6 µs and 12.8 µs wait</strong>, and reaches 5.6–5.7% at 40 µs. The 40 µs deadline is a ceiling,
      not a safe operating point: a correction that lands "on time" at 30 µs has already lost most of the
      code's benefit.</p>
    {{fig:fig6|Figure 9. Logical error versus decoder wait on the Heron r2 replica, with the worst stalls of the reference timing run marked.}}
  </div>

  <h2>Real hardware</h2>
  <p>Save an API key once, submit, and retrieve when the job is done. The job is 12,000 shots, well within the
    free Open Plan's 10 minutes per 28 days. On hardware, the real-time-versus-offline comparison includes
    the controller's true feed-forward delay, which no replica models. This step has not been run yet.</p>
  {{code:save_ibm_account.py}}
  <pre class="cmd"><code>python src/save_ibm_account.py
python src/experiment_4_real_hardware.py submit
python src/experiment_4_real_hardware.py retrieve &lt;job_id&gt;</code></pre>
  <div class="note"><strong>API note.</strong> The platform moved to
    <a href="https://quantum.cloud.ibm.com" target="_blank" rel="noopener">quantum.cloud.ibm.com</a> in 2025, and the
    old <code>ibm_quantum</code> channel was removed in qiskit-ibm-runtime 0.41. Version 0.50 deprecates
    <code>SamplerV2</code>; this script uses the client-side <code>Sampler</code> with twirling and dynamical
    decoupling switched off, so results are raw.</div>
</section>
"""

ANALYSIS = r"""
<section class="page" id="repro" aria-labelledby="h-repro">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-blue">Reproducibility</span><span>Six complete timing runs</span></div>
    <h1 id="h-repro">Reproducibility</h1>
    <p class="lede">Seeded simulations reproduce exactly. Timings do not, so the timing experiment was repeated as
      six complete runs, each with the main run and the ten-run repeat study (110,000 cycles per tier).</p>
  </header>

  <div class="tbl-wrap"><table>
    <thead><tr><th>Run</th><th>Date (2026)</th><th>Host CPU</th><th>Python τ*</th><th>Python worst</th><th>Python misses</th><th>C τ*</th><th>C worst</th><th>C misses</th></tr></thead>
    <tbody>
      <tr><td>R0 (ref.)</td><td>14 Oct</td><td>Xeon 2.1 GHz</td><td class="mono">268 ns</td><td class="mono">41.8 µs</td><td>1</td><td class="mono">46 ns</td><td class="mono">26.5 µs</td><td>0</td></tr>
      <tr><td>R1</td><td>14 Oct</td><td>Xeon 2.1 GHz</td><td class="mono">216 ns</td><td class="mono">74.3 µs</td><td>5</td><td class="mono">40 ns</td><td class="mono">67.4 µs</td><td>1</td></tr>
      <tr><td>R2</td><td>14 Oct</td><td>Xeon 2.1 GHz</td><td class="mono">189 ns</td><td class="mono">1,388.3 µs</td><td>2</td><td class="mono">29 ns</td><td class="mono">30.5 µs</td><td>0</td></tr>
      <tr><td>R3</td><td>26 Oct</td><td>Xeon 2.8 GHz</td><td class="mono">399 ns</td><td class="mono">67.2 µs</td><td>3</td><td class="mono">110 ns</td><td class="mono">26.0 µs</td><td>0</td></tr>
      <tr><td>R4</td><td>11 Nov</td><td>Xeon 2.1 GHz</td><td class="mono">105 ns</td><td class="mono">170.9 µs</td><td>2</td><td class="mono">27 ns</td><td class="mono">29.5 µs</td><td>0</td></tr>
      <tr><td>R5</td><td>11 Nov</td><td>Xeon 2.1 GHz</td><td class="mono">197 ns</td><td class="mono">42.9 µs</td><td>1</td><td class="mono">40 ns</td><td class="mono">37.6 µs</td><td>0</td></tr>
      <tr><td><strong>Pooled</strong></td><td colspan="2">660,000 cycles per tier</td><td>—</td><td class="mono">1.39 ms</td><td><strong>14</strong></td><td>—</td><td class="mono">67.4 µs</td><td><strong>1</strong></td></tr>
    </tbody>
  </table></div>
  <p class="small">All runs are two-vCPU Linux virtual machines. R4 and R5 are clean reproductions from the public
    repository. The per-run summaries are in <code>reproducibility_runs/</code>, and
    <code>paper/make_paper_figures.py</code> recomputes the pooled numbers from them.</p>

  <div class="result">
    <div class="result-head">What the six runs show</div>
    <p>Pooled over 660,000 cycles, Python's VR at 40 µs is 0.0021% (95% upper bound <strong>0.0036%</strong>) and C's is
      0.00015% (upper bound <strong>0.00084%</strong>), both far below the 1% budget. C misses significantly less often
      (Fisher exact p &lt; 0.001), consistent with its shorter timed window.</p>
    <p>The single slowest cycle is not a reproducible number: it ranged from 41.8 µs to 1.39 ms in Python and
      from 26.0 µs to 67.4 µs in C. Nothing in a general-purpose operating system bounds it, which is why
      real-time decoders run on dedicated hardware or isolated cores.</p>
  </div>

  <h2>Seeded results</h2>
  <p>Two clean reproductions on 11 November 2026 matched every seeded result file in
    <code>reference_results/</code> byte for byte, and the notebook repeats that comparison every time it runs. On
    a different CPU type, Aer's floating point can move the odd shot: on the 2.8 GHz host the Eagle sweep shifted by
    one shot in 4,000 per point, and the original code shows the same shift there.</p>
</section>
"""
