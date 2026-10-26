"""Page content, part A: Overview and Theory. Author: Swayam Shakya
Placeholders the builder fills in:
  {{code:FILE}}            a highlighted copy of that file from the repository
  {{fig:KEY|Caption}}      a figure from reference_results/, embedded
"""

OVERVIEW = r"""
<section class="page active" id="overview" aria-labelledby="h-overview">
  <header class="hero">
    <div class="hero-tag">
      <span>Quantum error correction</span><span>Classical feedback timing</span><span>Qiskit · IBM Quantum</span>
    </div>
    <h1 id="h-overview">Characterising Classical Feedback Latency in Software-Based QEC Decoders</h1>
    <p class="hero-sub">A four-weekend project of mine: I measured how long a software decoder takes to turn
      a syndrome into a correction, how often it misses the qubits' coherence deadline, and how much logical
      error each microsecond of delay costs.</p>
    <dl class="hero-meta">
      <div><dt>Author</dt><dd>Swayam Shakya</dd></div>
      <div><dt>Stack</dt><dd>Python 3.11–3.13 · Qiskit 2.5 · Aer 0.17 · qiskit-ibm-runtime 0.50</dd></div>
      <div><dt>Devices</dt><dd>IBM Heron r2 and Eagle r3 calibration replicas; any IBM device with dynamic circuits</dd></div>
      <div><dt>Tested</dt><dd>Every script run end to end · 32 unit tests</dd></div>
    </dl>
  </header>

  <h2>Headline results</h2>
  <p class="lede">These come from my reference run (14 October 2026), saved in <code>reference_results/</code>.
    If you rerun the project, the seeded simulations will match (on a different CPU type, Aer's floating point
    can move the odd shot; I saw a one-in-4,000 shift in one sweep). The timing numbers will only be close,
    since they depend on your machine.</p>
  <div class="card-grid">
    <div class="stat-card"><div class="val">268 ns</div><div class="lbl">τ* for the Python decoder</div>
      <div class="sub">Deadline where VR(τ) drops to 1% — 149× inside the 40 µs budget</div></div>
    <div class="stat-card"><div class="val">≤ 0.005%</div><div class="lbl">VR at 40 µs, Python</div>
      <div class="sub">1 miss in 110,000 cycles (95% upper bound); C: 0 misses</div></div>
    <div class="stat-card"><div class="val">4–42 µs</div><div class="lbl">Operating-system stalls</div>
      <div class="sub">Rare plateau that hits Python and C alike; no fitted tail predicts it</div></div>
    <div class="stat-card"><div class="val">8–13 µs</div><div class="lbl">Wait that doubles logical error</div>
      <div class="sub">Heron r2 / Eagle r3 replicas — far below the 40 µs deadline</div></div>
  </div>

  <h2>Why I did this</h2>
  <p>A quantum error-correcting code only protects anything if the loop <em>measure syndrome → decode →
    apply correction</em> closes before the qubits decohere. Most simulations quietly assume the classical
    part is instant, and I wanted to know if that is fair. Take a dephasing time T₂ = 120 µs (a conservative
    figure for IBM superconducting qubits) and N = 3 syndrome rounds per logical cycle: each round's classical
    work must fit within τ<sub>DD</sub> = T₂/N = 40 µs.</p>
  <p><strong>The question:</strong> does a decoder running as ordinary software meet that deadline, how often
    does it miss, and what does a late correction cost? The violation rate VR(τ) = P(L &gt; τ) is compared with
    the surface-code threshold p<sub>th</sub> ≈ 1% (Fowler et al. 2012), used here as an error budget.</p>

  <h2>Four research questions</h2>
  <div class="card-grid">
    <div class="stat-card"><div class="val">RQ1</div><div class="lbl">Violation rate</div>
      <div class="sub">What is VR(τ) across deadlines from 10 ns to 100 µs, and where does it cross 1%?</div></div>
    <div class="stat-card"><div class="val">RQ2</div><div class="lbl">Tail behaviour</div>
      <div class="sub">Is the latency tail light (log-normal) or heavy (power law)?</div></div>
    <div class="stat-card"><div class="val">RQ3</div><div class="lbl">Device noise</div>
      <div class="sub">Does the code still help under realistic device noise, and what does feedback latency cost?</div></div>
    <div class="stat-card"><div class="val">RQ4</div><div class="lbl">Implementation tier</div>
      <div class="sub">How much does a compiled C decoder improve on pure Python?</div></div>
  </div>

  <h2>What's in the project</h2>
  <ul>
    <li><strong>C1 — Latency dataset.</strong> 10,000 timed decode cycles per tier (Python, C via ctypes,
      modelled bare-metal), with measured timer floors and a 10-run repeat study, saved as JSON.</li>
    <li><strong>C2 — Statistical framework.</strong> Exact Clopper–Pearson intervals for VR(τ), bootstrap
      intervals for τ*, Anderson–Darling and Kolmogorov–Smirnov fits, the Hill tail index, and Mann–Whitney U
      with rank-biserial effect size.</li>
    <li><strong>C3 — Device-level protocol.</strong> A bare qubit, offline decoding and real-time feed-forward
      compared on one fixed physical layout, with Wilson intervals and χ² tests; runs locally on calibration
      replicas or on IBM hardware.</li>
    <li><strong>C4 — Threshold crossover.</strong> τ* = the deadline where VR(τ*) = 1%, per tier, with its headroom
      against τ<sub>DD</sub>.</li>
    <li><strong>C5 — Latency sweep.</strong> Logical error as a function of decoder wait, connecting the measured
      latency tail to its cost in fidelity.</li>
  </ul>

  <h2>Project schedule</h2>
  <ol class="timeline">
    <li class="tl-item"><div class="tl-left">Wknd 1</div><div class="tl-line"><span class="tl-dot"></span></div>
      <div class="tl-body"><h3>Physical foundation</h3><p>Ramsey decay recovers T₂ from the noise model; a Pauli
      experiment shows which errors a superposition can feel.</p></div></li>
    <li class="tl-item"><div class="tl-left">Wknd 2</div><div class="tl-line"><span class="tl-dot d2"></span></div>
      <div class="tl-body"><h3>The code works</h3><p>A complete bit-flip code class with ancilla syndrome
      extraction and a timed look-up-table decoder; logical versus physical error.</p></div></li>
    <li class="tl-item"><div class="tl-left">Wknd 3</div><div class="tl-line"><span class="tl-dot d3"></span></div>
      <div class="tl-body"><h3>Timing analysis</h3><p>Three tiers, timer floors, VR(τ) with exact intervals,
      jitter traces, distribution fits and a repeat study.</p></div></li>
    <li class="tl-item"><div class="tl-left">Wknd 4</div><div class="tl-line"><span class="tl-dot d4"></span></div>
      <div class="tl-body"><h3>Device validation</h3><p>Dynamic-circuit protocol on calibrated replicas (or real
      hardware), plus the latency sweep; the final statistics and the LaTeX table.</p></div></li>
  </ol>

  <h2>Run it yourself</h2>
  <p>Clone the repository and run two scripts. <code>setup.sh</code> makes a virtual environment with the pinned
    versions below, and <code>run_all.sh</code> reruns every experiment into <code>outputs/</code> (about
    6 minutes on 2 cores). <code>pytest</code> runs the unit tests. Weekends 1–3 and the local Weekend 4 runs
    need no IBM account. On Windows, use WSL, because the C decoder needs gcc and a POSIX clock.</p>
  <pre class="cmd"><code>git clone &lt;this repository&gt; qec-decoder-latency
cd qec-decoder-latency
bash setup.sh
bash run_all.sh
source qec-env/bin/activate &amp;&amp; pytest</code></pre>
  {{code:requirements.txt}}
  {{code:setup.sh}}
  {{code:run_all.sh}}
  <div class="note"><strong>IBM Quantum access (Weekend 4 hardware only).</strong> The platform moved to
    <a href="https://quantum.cloud.ibm.com" target="_blank" rel="noopener">quantum.cloud.ibm.com</a> in 2025, and the
    old <code>ibm_quantum</code> channel was removed in qiskit-ibm-runtime 0.41. Create an API key there and save
    it once with <code>python src/save_ibm_account.py</code> (it asks for the key, so the key never sits in a file). The free Open Plan includes 10 minutes of
    quantum-computer time per 28 days.</div>

  <h2>Bugs I hit along the way</h2>
  <p class="lede">My first version of this project ran, but several results were quietly wrong. Running every
    script and checking it against theory turned up the problems below. I'm keeping the list because most of
    them are easy mistakes to repeat.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th>#</th><th>Where</th><th>Defect</th><th>Fix</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Exp 1.1</td><td>Prepared |0⟩, which thermal relaxation never moves; the fit hit its bound and reported T₂ = 44,142 µs (368× the input).</td><td>Ramsey sequence on |+⟩, noise on idle gates only: T₂ = 121.5 ± 1.3 µs.</td></tr>
      <tr><td>2</td><td>Exp 1.2</td><td>Noise on both H gates let an X error after the second H flip the readout, so |+⟩ looked 49% sensitive to X.</td><td>One noisy idle gate between the two H gates: X has no effect, as theory says.</td></tr>
      <tr><td>3</td><td>fit_distribution.py</td><td><code>kstest(lat, 'weibull')</code> names a distribution SciPy does not have: crash.</td><td>Pass each distribution's <code>cdf</code>.</td></tr>
      <tr><td>4</td><td>fit_distribution.py</td><td>Docstring and printout used different tail-index thresholds (α &gt; 2 vs α &gt; 4).</td><td>One three-band rule: light, moderate, heavy.</td></tr>
      <tr><td>5</td><td>Weekend 3 · Analysis</td><td><code>anderson()</code> critical values are deprecated in SciPy 1.17 and removed in 1.19.</td><td><code>method='interpolate'</code> p-values.</td></tr>
      <tr><td>6</td><td>analysis_paper_ready.py</td><td>Five <code>ff"…"</code> typos (syntax error); all warnings silenced; a promised figure never drawn; effect-size sign undocumented.</td><td>Rewritten; draws the tail-diagnostics figure; r = 2U₁/(n₁n₂) − 1 documented.</td></tr>
      <tr><td>7</td><td>All Aer runs</td><td>Aer seeds shot k with seed + k, so seeds 7, 8, 9… overlap and produced correlated 3σ deviations; a fixed seed in the code class replayed identical noise every cycle.</td><td>Seeds spread with <code>numpy.random.SeedSequence</code>; a fresh seed per cycle.</td></tr>
      <tr><td>8</td><td>Profiler</td><td>Silently substituted invented C-tier data when the library was missing; computed every bootstrap twice; plotted VR = 0 on a log axis; the 1% line shared the Python series colour.</td><td>A missing library is now an error; one pass; zeros handled; neutral reference lines.</td></tr>
      <tr><td>9</td><td>VR intervals</td><td>Bootstrap intervals collapse to [0, 0] with no misses and under-cover with one.</td><td>Exact Clopper–Pearson intervals (bootstrap kept for τ*).</td></tr>
      <tr><td>10</td><td>Exp 4</td><td>The “depth-matched” baseline padded with <code>id</code> gates, which the transpiler deletes; offline and real-time circuits landed on different qubits.</td><td>A delay equal to the encoded stage's estimated duration; one pinned layout for all circuits.</td></tr>
      <tr><td>11</td><td>Exp 4</td><td>Channel <code>ibm_quantum</code> no longer exists; <code>retrieve</code> used a placeholder token; <code>SamplerV2</code> is deprecated in runtime 0.50.</td><td><code>ibm_quantum_platform</code>, saved account, the new client-side <code>Sampler</code>.</td></tr>
      <tr><td>12</td><td>requirements.txt</td><td>Pinned Qiskit 1.3 / runtime 0.23, which cannot reach IBM's current platform; matplotlib 3.9.1 is a yanked release.</td><td>Current, mutually compatible pins, verified with <code>pip check</code>.</td></tr>
      <tr><td>13</td><td>qec_decode.c</td><td>Did not compile under <code>-std=c11</code>: <code>clock_gettime</code> undeclared.</td><td><code>_POSIX_C_SOURCE 200809L</code>; clean under c99, c11, c17 and gnu17.</td></tr>
      <tr><td>14</td><td>This page</td><td>Bare <code>&lt;</code> characters inside code, no charset or doctype, a theme button that misread a light OS, low-contrast code colours in light mode, a placeholder abstract.</td><td>The page is now built from the repository files by <code>site/build_html.py</code>; fixed toggle and colours; real summary.</td></tr>
    </tbody>
  </table></div>
</section>
"""

THEORY = r"""
<section class="page" id="theory" aria-labelledby="h-theory">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-purple">Theory</span><span>Read once, refer back often</span></div>
    <h1 id="h-theory">Theoretical background</h1>
    <p class="lede">The mathematics that connects qubit coherence to a classical timing budget.</p>
  </header>

  <h2>1. Coherence and the decoherence deadline</h2>
  <p>A qubit loses information through two channels. Energy relaxation (T₁) takes |1⟩ to |0⟩; dephasing (T₂)
    scrambles the phase of a superposition without changing populations. Physics requires T₂ ≤ 2T₁. A state
    prepared in |+⟩, left idle for time t and rotated back with a Hadamard gate is still |+⟩ with probability</p>
  <div class="eq-box">F(t) = ½ + ½ · exp(−t / T₂)<span class="eq-label">[1] Ramsey decay</span></div>
  <p>A ground-state qubit |0⟩ shows no decay at all under relaxation, which is why Experiment 1.1 must start from
    |+⟩. With N syndrome rounds per logical cycle, each round's classical work has a budget of</p>
  <div class="eq-box">τ<sub>DD</sub> = T₂ / N = 120 µs / 3 = 40 µs<span class="eq-label">[2] decoherence deadline</span></div>

  <h2>2. The 3-qubit bit-flip code</h2>
  <div class="eq-box">|0⟩<sub>L</sub> = |000⟩ · |1⟩<sub>L</sub> = |111⟩ · |ψ⟩<sub>L</sub> = α|000⟩ + β|111⟩<span class="eq-label">[3] encoding</span></div>
  <p>The code corrects any single X (bit-flip) error and is blind to Z (phase-flip) errors; the surface code
    handles both with a two-dimensional lattice of checks. Two ancillas measure the parities Z₀Z₁ and Z₁Z₂ without
    measuring the data qubits, so a superposition survives the check. Qiskit prints classical bits right to left,
    so the syndrome string reads (Z₀Z₁)(Z₁Z₂):</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Syndrome string</th><th>Z₀Z₁</th><th>Z₁Z₂</th><th>Diagnosis</th><th>Correction</th></tr></thead>
    <tbody>
      <tr><td class="mono">00</td><td>0</td><td>0</td><td>no error</td><td>none</td></tr>
      <tr><td class="mono">10</td><td>1</td><td>0</td><td>qubit 0 flipped</td><td>X on q₀</td></tr>
      <tr><td class="mono">11</td><td>1</td><td>1</td><td>qubit 1 flipped</td><td>X on q₁</td></tr>
      <tr><td class="mono">01</td><td>0</td><td>1</td><td>qubit 2 flipped</td><td>X on q₂</td></tr>
    </tbody>
  </table></div>
  <p>If each data qubit flips independently with probability p, the logical qubit fails when two or three flip:</p>
  <div class="eq-box">P<sub>L</sub>(p) = 3p²(1 − p) + p³ = 3p² − 2p³<span class="eq-label">[4] logical error</span></div>
  <p>The code beats a bare qubit for every p &lt; ½, by a factor of about 1/(3p) when p is small.</p>

  <h2>3. Violation rate and the threshold budget</h2>
  <div class="eq-box">VR(τ) = P(L &gt; τ) ≈ (1/n) Σ 1[L<sub>i</sub> &gt; τ]<span class="eq-label">[5] violation rate</span></div>
  <div class="eq-box">τ* = inf { τ : VR(τ) ≤ p<sub>th</sub> } = the 99th percentile when p<sub>th</sub> = 1%<span class="eq-label">[6] threshold crossover</span></div>
  <p>Comparing VR with p<sub>th</sub> ≈ 1% treats a missed deadline as one more error event. That is a modelling
    choice, not a theorem: p<sub>th</sub> is a per-operation physical error rate, used here as a budget. A tier is
    viable when τ* ≤ τ<sub>DD</sub>; Weekend 4 shows why that condition is necessary but far from sufficient.</p>
  <p>VR is a binomial proportion, so its interval comes from the exact Clopper–Pearson method. When 0 of n cycles
    miss, the 95% upper bound is about 3.7/n (0.037% for n = 10,000), whereas a bootstrap interval collapses to [0, 0].</p>

  <h2>4. Latency distribution models</h2>
  <ul>
    <li><strong>Log-normal:</strong> ln L ~ N(µ, σ²). Multiplicative small delays (cache misses, branch
      mispredictions) produce it; every moment is finite.</li>
    <li><strong>Power-law tail:</strong> P(L &gt; x) ~ x<sup>−α</sup>. The Hill estimator measures α from the largest
      observations: α &gt; 4 light, 2 &lt; α ≤ 4 moderate, α ≤ 2 heavy (infinite variance).</li>
    <li><strong>Mixture:</strong> a fast body plus a rare, separate population of long stalls (scheduler
      preemption, interrupts, hypervisor steal time). Neither model above predicts it; it appears as a plateau on
      a log-log survival plot. This is what the measurements in Weekend 3 show.</li>
  </ul>

  <h2>5. Parameters used in this project</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Parameter</th><th>Project model</th><th>Heron r2 replica</th><th>Eagle r3 replica</th></tr></thead>
    <tbody>
      <tr><td>T₁ (median)</td><td class="mono">250 µs</td><td class="mono">283 µs</td><td class="mono">278 µs</td></tr>
      <tr><td>T₂ (median)</td><td class="mono">120 µs</td><td class="mono">144 µs</td><td class="mono">170 µs</td></tr>
      <tr><td>τ<sub>DD</sub> = T₂/3</td><td class="mono">40 µs</td><td class="mono">48 µs</td><td class="mono">57 µs</td></tr>
      <tr><td>1-qubit gate</td><td class="mono">50 ns</td><td class="mono">32 ns (√X)</td><td class="mono">57 ns (√X)</td></tr>
      <tr><td>2-qubit gate</td><td class="mono">500 ns (CNOT)</td><td class="mono">68 ns (CZ)</td><td class="mono">533 ns (ECR)</td></tr>
      <tr><td>Readout</td><td class="mono">—</td><td class="mono">2.28 µs</td><td class="mono">1.22 µs</td></tr>
      <tr><td>Median 2-qubit error / readout error</td><td class="mono">—</td><td class="mono">0.18% / 0.95%</td><td class="mono">0.78% / 1.98%</td></tr>
    </tbody>
  </table></div>
  <p class="small">Replica values are medians over all qubits of the calibration snapshots shipped with
    qiskit-ibm-runtime 0.50 (<code>FakeKingston</code>, <code>FakeSherbrooke</code>). Live devices drift from them.</p>

  <h2>6. Key references</h2>
  <ol class="refs">
    <li>Fowler, A. G., Mariantoni, M., Martinis, J. M. &amp; Cleland, A. N. (2012). Surface codes: Towards practical large-scale quantum computation. <em>Phys. Rev. A</em> 86, 032324. <a href="https://doi.org/10.1103/PhysRevA.86.032324" target="_blank" rel="noopener">doi:10.1103/PhysRevA.86.032324</a></li>
    <li>Terhal, B. M. (2015). Quantum error correction for quantum memories. <em>Rev. Mod. Phys.</em> 87, 307. <a href="https://doi.org/10.1103/RevModPhys.87.307" target="_blank" rel="noopener">doi:10.1103/RevModPhys.87.307</a></li>
    <li>Nielsen, M. A. &amp; Chuang, I. L. (2010). <em>Quantum Computation and Quantum Information</em>, 10th anniversary ed. Cambridge University Press.</li>
    <li>Hill, B. M. (1975). A simple general approach to inference about the tail of a distribution. <em>Ann. Statist.</em> 3(5), 1163–1174. <a href="https://doi.org/10.1214/aos/1176343247" target="_blank" rel="noopener">doi:10.1214/aos/1176343247</a></li>
    <li>Clopper, C. J. &amp; Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated in the case of the binomial. <em>Biometrika</em> 26(4), 404–413. <a href="https://doi.org/10.1093/biomet/26.4.404" target="_blank" rel="noopener">doi:10.1093/biomet/26.4.404</a></li>
    <li>Javadi-Abhari, A. et al. (2024). Quantum computing with Qiskit. <a href="https://arxiv.org/abs/2405.08810" target="_blank" rel="noopener">arXiv:2405.08810</a></li>
  </ol>
</section>
"""
