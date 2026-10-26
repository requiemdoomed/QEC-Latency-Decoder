"""Page content, part B: Weekends 1-4 and the Analysis tab. Author: Swayam Shakya"""

W1 = r"""
<section class="page" id="w1" aria-labelledby="h-w1">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-blue">Weekend 1</span><span>Coherence and error sensitivity</span><span>≈ 5 hours</span></div>
    <h1 id="h-w1">Physical foundation</h1>
    <p class="lede">Before timing anything I wanted to see the clock I'm racing: a Ramsey measurement recovers T₂
      from the noise model, and a Pauli experiment shows which errors a superposition can actually feel.</p>
  </header>

  <h2>Shared figure style</h2>
  <p>Every plotting script imports this small module, so all figures share fonts, colours and file formats
    (a vector PDF and a PNG preview). Its three series colours stay distinguishable under the common
    forms of colour-vision deficiency.</p>
  {{code:qec_style.py}}

  <h2>Experiment 1.1 — Ramsey coherence decay</h2>
  <p>Prepare |+⟩, idle for d gates of 50 ns each, rotate back and measure. Only the idle gates carry thermal
    relaxation, so the idle time t = d × 50 ns is exact and the one-parameter fit of equation [1] returns T₂ directly.
    Twenty-five idle times span 0–300 µs, enough to see the full decay.</p>
  {{code:experiment_1_1_coherence.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <p>Fitted <strong>T₂ = 121.5 ± 1.3 µs</strong> against a model value of 120 µs (1.2 standard errors). At the
      40 µs deadline the fidelity is <strong>0.860</strong>; after a full three-round cycle (120 µs) it is 0.686.</p>
    {{fig:fig1|Figure 1. Ramsey decay: 25 idle times, 4,096 shots each, with the fitted curve and the 40 µs deadline.}}
  </div>
  <div class="warn-box"><strong>Why |+⟩ and not |0⟩.</strong> Thermal relaxation pulls qubits toward |0⟩, so a qubit
    that starts there never decays. My first version did exactly that, and the fit ran off to the optimiser's
    bound: T₂ = 44,142 µs.</div>

  <h2>Experiment 1.2 — Which Pauli errors does |+⟩ feel?</h2>
  <p>Insert one idle gate between two Hadamards and give it a Pauli channel: operator P with probability p, identity
    otherwise. X leaves |+⟩ unchanged; Y and Z turn it into |−⟩. The noise must sit on the idle gate only: on the
    Hadamards, an X error after the second one flips the readout and fakes a sensitivity to X.</p>
  {{code:experiment_1_2_pauli_sensitivity.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <p><strong>X: survival 1.000 at every p.</strong> Y and Z: every point within 0.0123 of 1 − p. The bit-flip code
      corrects exactly the error |+⟩ cannot feel and is blind to the ones it can, which is why codes that protect
      superpositions also need phase checks.</p>
    {{fig:fig2|Figure 2. Survival of |+⟩ under one Pauli channel; 11 values of p, 8,192 shots each.}}
  </div>

  <h2>Weekend 1 checklist</h2>
  <ul class="check">
    <li>Fitted T₂ within about 2 standard errors of 120 µs</li>
    <li>X curve flat at 1.0; Y and Z on the line 1 − p</li>
    <li><code>fig1_coherence_decay.pdf</code>, <code>fig2_pauli_sensitivity.pdf</code>, <code>w1_coherence.json</code>, <code>w1_pauli.json</code> saved</li>
  </ul>
</section>
"""

W2 = r"""
<section class="page" id="w2" aria-labelledby="h-w2">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-purple">Weekend 2</span><span>Syndrome extraction and decoding</span><span>≈ 6 hours</span></div>
    <h1 id="h-w2">The 3-qubit code in full</h1>
    <p class="lede">Build the code, check that its decoder picks the right correction under noise, and confirm that
      it actually suppresses errors.</p>
  </header>

  <h2>Experiment 2.1 — The BitFlipCode class</h2>
  <p>Each cycle encodes |1⟩<sub>L</sub>, injects no error or one X error at random, extracts the syndrome on two
    ancillas under thermal-relaxation noise, runs one shot, and decodes. Only the decode step sits between the two
    clock reads. Every cycle gets a fresh simulator seed: Aer seeds shot k with <code>seed + k</code>, so one fixed
    seed would replay identical noise every cycle.</p>
  {{code:bit_flip_code.py}}
  <div class="result">
    <div class="result-head">Reference run · 10,000 cycles</div>
    <p>The decoder chose the matching correction in <strong>98.61%</strong> of cycles (Wilson 95% CI
      98.36–98.82%). Failures spread evenly over every injected case, so they come from relaxation during the six
      500 ns CNOTs, not from the table.</p>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Injected ↓ / decoded →</th><th>none</th><th>q₀</th><th>q₁</th><th>q₂</th><th>Correct</th></tr></thead>
      <tbody>
        <tr><td>none</td><td><strong>2,499</strong></td><td>12</td><td>11</td><td>12</td><td>98.62%</td></tr>
        <tr><td>q₀</td><td>15</td><td><strong>2,482</strong></td><td>23</td><td>7</td><td>98.22%</td></tr>
        <tr><td>q₁</td><td>10</td><td>7</td><td><strong>2,459</strong></td><td>10</td><td>98.91%</td></tr>
        <tr><td>q₂</td><td>15</td><td>8</td><td>9</td><td><strong>2,421</strong></td><td>98.70%</td></tr>
      </tbody>
    </table></div>
    <p>Decode time inside the full cycle: median 716 ns, P99 1,193 ns. One cycle took 104 µs and missed the 40 µs
      deadline. Weekend 3 isolates that tail.</p>
  </div>

  <h2>Experiment 2.2 — Logical versus physical error</h2>
  <p>Does the code help? Give each data qubit an independent X error with probability p, extract the syndrome,
    correct in real time with <code>if_test</code>, and read out. Theory (equation [4]) predicts 3p² − 2p³.</p>
  {{code:experiment_2_2_logical_error.py}}
  <div class="result">
    <div class="result-head">Reference run · 11 values of p × 100,000 shots</div>
    <p>All 11 points contain the theory value inside their 95% interval. At p = 1% the logical failure rate is
      <strong>0.039%</strong> (95% CI 0.029–0.053%), <strong>25× fewer failures</strong> than a bare qubit; at p = 10% the
      gain is 3.6×; at p = 50% it is gone.</p>
    {{fig:fig2b|Figure 3. Logical failure versus physical bit-flip probability, log-log; bars are Wilson 95% intervals.}}
  </div>

  <h2>Weekend 2 checklist</h2>
  <ul class="check">
    <li>Syndrome table verified against the confusion matrix: no off-diagonal pattern</li>
    <li>Every logical-error point contains 3p² − 2p³ inside its 95% interval</li>
    <li><code>w2_latencies.json</code> and <code>w2_logical_error.json</code> saved</li>
  </ul>
</section>
"""

W3 = r"""
<section class="page" id="w3" aria-labelledby="h-w3">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-green">Weekend 3</span><span>Timing analysis</span><span>≈ 6 hours</span></div>
    <h1 id="h-w3">The latency distribution</h1>
    <p class="lede">How long does decoding take, how often is it late, and what shape does the tail have?</p>
  </header>

  <h2>Experiment 3.1 — Distribution fitting</h2>
  <p>Fit log-normal, gamma and Weibull distributions to the Weekend 2 latencies and estimate the tail index.
    Kolmogorov–Smirnov p-values are optimistic once parameters are fitted from the same data, so compare the KS
    distance D; with 10,000 samples, every simple family is formally rejected.</p>
  {{code:fit_distribution.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <p>Closest family by KS distance: <strong>log-normal</strong> (D = 0.103, against 0.177 for gamma and 0.333 for
      Weibull). Anderson–Darling still rejects exact log-normality (A² = 245, p ≤ 0.01). Hill index on the top 5%:
      <strong>α = 4.09</strong>, at the light/moderate boundary.</p>
  </div>

  <h2>Experiment 3.2 — Three tiers, timer floors and VR(τ)</h2>
  <p>The same look-up table runs as a Python dictionary and as compiled C called through ctypes; a modelled
    bare-metal tier (Cortex-M7, 41-cycle WCET = 85.4 ns, 5% jitter) sets the scale. Each measured tier also
    records its timer floor: two clock reads with nothing between them. Build the C library first:</p>
  {{code:qec_decode.c}}
  <pre class="cmd"><code>mkdir -p build
gcc -O2 -shared -fPIC -o build/qec_decode.so src/qec_decode.c    # run_all.sh does this for you</code></pre>
  {{code:experiment_3_jitter_profiler.py}}
  <div class="result">
    <div class="result-head">Reference run · 10,000 timed cycles per tier after 1,000 warm-up</div>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Tier</th><th>Median</th><th>Timer floor</th><th>P99</th><th>P99.9</th><th>Max</th><th>Misses at 40 µs</th><th>VR@40 µs, 95% CI</th></tr></thead>
      <tbody>
        <tr><td>Python</td><td class="mono">113 ns</td><td class="mono">63 ns</td><td class="mono">268 ns</td><td class="mono">481 ns</td><td class="mono">41.8 µs</td><td>1 of 10,000</td><td class="mono">0.01% [0.0003, 0.056]</td></tr>
        <tr><td>C extension</td><td class="mono">31 ns</td><td class="mono">26 ns</td><td class="mono">46 ns</td><td class="mono">113 ns</td><td class="mono">23.0 µs</td><td>0 of 10,000</td><td class="mono">0% [0, 0.037]</td></tr>
        <tr><td>Bare-metal (modelled)</td><td class="mono">85 ns</td><td class="mono">—</td><td class="mono">95 ns</td><td class="mono">99 ns</td><td class="mono">0.10 µs</td><td>0 of 10,000</td><td class="mono">0% [0, 0.037]</td></tr>
      </tbody>
    </table></div>
    <p>Typical decodes are 350× (Python) and 1,300× (C) inside the budget, and most of what both tiers measure is
      the clock itself: about 50 ns and 5 ns of real work. The risk sits in a separate population of stalls
      (7 Python cycles and 1 C cycle over 1 µs) that strike both tiers alike.</p>
    {{fig:fig3|Figure 4. (A) latency distributions, (B) every cycle in order, (C) VR(τ) with exact 95% bands, (D) summary.}}
    <p><strong>Repeat study</strong> (<code>--repeats 10</code>, 100,000 further cycles per tier): no misses in either
      tier. Pooled over 110,000 cycles, Python's VR@40 µs is at most 0.0051% and C's at most 0.0034% (95% upper
      bounds). Python medians ranged 113–148 ns and worst stalls 11–42 µs between runs, so single-run maxima on a
      shared machine are not reproducible numbers.</p>
  </div>
  <div class="note"><strong>Exact versus bootstrap intervals.</strong> With one observed miss, the bootstrap interval
    for VR@40 µs is [0, 0.03%] and the exact interval is [0.0003, 0.056%]: resampling cannot invent misses it never
    saw. With zero misses the bootstrap collapses to [0, 0]. Use exact binomial intervals for rare events.</div>

  <h2>Weekend 3 checklist</h2>
  <ul class="check">
    <li><code>qec_decode.so</code> builds without warnings</li>
    <li>Timer floors recorded; net decode cost = median − floor</li>
    <li>Repeat study run; misses pooled with an exact interval</li>
    <li><code>fig3_main_result.pdf</code>, <code>w3_latencies.json</code>, <code>w3_repeats.json</code>, <code>w3_fit.json</code> saved</li>
  </ul>
</section>
"""

W4 = r"""
<section class="page" id="w4" aria-labelledby="h-w4">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-yellow">Weekend 4</span><span>Device validation</span><span>≈ 5 hours</span></div>
    <h1 id="h-w4">Dynamic circuits on device noise</h1>
    <p class="lede">Run the code with real-time feed-forward on a calibrated replica of an IBM device (no account
      needed), or on the device itself, and measure what decoder latency costs.</p>
  </header>

  <h2>The protocol</h2>
  <p>One job holds three circuits, each prepared in logical |1⟩, on one fixed physical layout:</p>
  <ul>
    <li><strong>bare</strong> — one physical qubit (the same one as data qubit 0) idling for exactly as long as the
      encoded circuit's encode-and-syndrome stage, using a <code>delay</code> the transpiler cannot remove;</li>
    <li><strong>offline</strong> — encoded, syndrome measured, no feed-forward; the syndrome is decoded afterwards
      in software, shot by shot;</li>
    <li><strong>realtime</strong> — encoded, syndrome measured, correction applied by three <code>if_test</code> blocks.</li>
  </ul>
  <p>Four read-outs come from them: bare, majority vote alone, offline decode and real-time correction. The
    <code>sweep</code> mode inserts a wait of 0–80 µs between the syndrome readout and the correction, a stand-in
    for decoder latency that the replica's noise model can see.</p>
  {{fig:fig0|Figure 5. The protected circuit: encode |111⟩, two parity checks, real-time correction, readout.}}
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
    <p>The code helps clearly on both devices; real-time and offline correction tie because the replica adds no
      feed-forward delay. In one round that ends with reading the data qubits, a majority vote already undoes any
      single flip, so the syndrome adds nothing here; it matters when the state must survive further rounds.</p>
    {{fig:fig5|Figure 6. Logical |1⟩ fidelity by protocol on the Heron r2 replica, Wilson 95% intervals.}}
    <p><strong>Latency sweep.</strong> Logical error starts at 0.45% (Heron) and 1.00% (Eagle), <strong>doubles after
      a 7.6 µs and 12.8 µs wait</strong>, and reaches 5.6–5.7% at 40 µs. The 40 µs deadline is a ceiling, not a safe
      operating point: a correction that lands “on time” at 30 µs has already lost most of the code's benefit.</p>
    {{fig:fig6|Figure 7. Logical error versus decoder wait on the Heron r2 replica, with the worst stalls measured in Weekend 3.}}
  </div>

  <h2>Real hardware</h2>
  <p>Save your API key once, then submit, and retrieve when the job is done. I haven't run this part on a real
    device yet, since it needs my IBM credentials. The job is 12,000 shots, well within the free Open Plan's
    10 minutes per 28 days. On hardware, the real-time-versus-offline comparison includes the
    controller's true feed-forward latency, which no replica models.</p>
  {{code:save_ibm_account.py}}
  <pre class="cmd"><code>python src/save_ibm_account.py
python src/experiment_4_real_hardware.py submit
python src/experiment_4_real_hardware.py retrieve &lt;job_id&gt;</code></pre>
  <div class="note"><strong>API note.</strong> qiskit-ibm-runtime 0.50 deprecates <code>SamplerV2</code>; this script
    uses the client-side <code>Sampler</code> from <code>qiskit_ibm_runtime.executor_sampler</code>, with twirling and
    dynamical decoupling switched off so results are raw (decoupling cannot be combined with dynamic circuits anyway).</div>

  <h2>Weekend 4 checklist</h2>
  <ul class="check">
    <li>Both replicas run; all three circuits share one layout (check the printed qubit lists)</li>
    <li>Sweep run; doubling wait recorded</li>
    <li>Optional: hardware job submitted, job ID in <code>w4_job_manifest.json</code></li>
  </ul>
</section>
"""

ANALYSIS = r"""
<section class="page" id="analysis" aria-labelledby="h-analysis">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-blue">Analysis</span><span>Statistics, Table 1, Figure 8</span></div>
    <h1 id="h-analysis">Full statistical analysis</h1>
    <p class="lede">One script turns the Weekend 3 data into the final statistics: τ* with bootstrap intervals,
      tail diagnostics, the Python-versus-C test and a ready-to-paste LaTeX table.</p>
  </header>
  {{code:analysis_paper_ready.py}}
  <div class="result">
    <div class="result-head">Reference run</div>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Tier</th><th>τ* = P99, 95% CI</th><th>Headroom vs 40 µs</th><th>Hill α</th><th>Stalls &gt; 1 µs</th></tr></thead>
      <tbody>
        <tr><td>Python</td><td class="mono">268 ns [248, 290]</td><td class="mono">149×</td><td class="mono">3.95</td><td>7 (median 13.1 µs)</td></tr>
        <tr><td>C extension</td><td class="mono">46 ns [45, 47]</td><td class="mono">870×</td><td class="mono">7.93</td><td>1 (23.0 µs)</td></tr>
        <tr><td>Bare-metal (modelled)</td><td class="mono">95 ns [95, 96]</td><td class="mono">420×</td><td class="mono">52.7</td><td>0</td></tr>
      </tbody>
    </table></div>
    <p>Python versus C: Mann–Whitney p &lt; 10⁻³⁰⁰, rank-biserial r = +0.998, median ratio 3.6×. Below a survival
      probability of about 10⁻³ the curves leave the Hill fit and flatten into the stall plateau, so VR at large τ
      must be counted directly, never extrapolated from a fitted tail.</p>
    {{fig:fig4|Figure 8. (A) survival curves with Hill power-law fits to the top 5%; (B) τ* per tier against the deadline.}}
  </div>
</section>
"""
