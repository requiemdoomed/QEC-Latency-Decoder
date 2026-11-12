"""Page content, part A: Overview and Background. Author: Swayam Shakya
Placeholders the builder fills in:
  {{code:FILE}}            a highlighted copy of that file from the repository
  {{fig:KEY|Caption}}      a figure from reference_results/ (or paper/figures/), embedded
"""

OVERVIEW = r"""
<section class="page active" id="overview" aria-labelledby="h-overview">
  <header class="hero">
    <div class="hero-tag">
      <span>Quantum error correction</span><span>Real-time decoding</span><span>Qiskit · IBM Quantum</span>
    </div>
    <h1 id="h-overview">How Fast Does a Quantum Error-Correction Decoder Need to Be?</h1>
    <p class="hero-sub">Measuring classical feedback latency in software QEC decoders, from simulation to IBM
      device replicas.</p>
    <dl class="hero-meta">
      <div><dt>Author</dt><dd>Swayam Shakya · Algoma University</dd></div>
      <div><dt>Stack</dt><dd>Python 3.11–3.13 · Qiskit 2.5 · Aer 0.17 · qiskit-ibm-runtime 0.50 · C</dd></div>
      <div><dt>Devices</dt><dd>Calibrated replicas of IBM Heron r2 and Eagle r3; any IBM device with dynamic circuits</dd></div>
      <div><dt>Paper</dt><dd><a href="paper/QEC_Research_Paper.pdf">IEEE-format research paper (PDF)</a></dd></div>
      <div><dt>Notebook</dt><dd><a href="QEC_Latency_Decoder.ipynb">QEC_Latency_Decoder.ipynb</a>: every experiment, check and test in one runnable file</dd></div>
      <div><dt>Code</dt><dd><a href="https://github.com/requiemdoomed/QEC-Latency-Decoder" target="_blank" rel="noopener">github.com/requiemdoomed/QEC-Latency-Decoder</a></dd></div>
    </dl>
  </header>

  <h2>The question</h2>
  <p>A quantum error-correcting code only protects anything while its loop keeps running: measure the
    syndrome, decode it, apply the correction. Each turn has to finish before the qubits lose coherence.
    In a simulation the decoder is a function call and costs nothing; on real hardware it is a program
    running on a real computer, and it can be late.</p>
  <p>This project measures that classical step for the simplest code that runs the whole loop, the
    three-qubit bit-flip code. Its decoder is a four-entry look-up table, so the decoding itself takes a few
    nanoseconds and almost everything in the latency distribution comes from the language runtime and the
    operating system. With a dephasing time T₂ = 120 µs and N = 3 syndrome rounds per logical cycle, each
    round has a budget of τ<sub>DD</sub> = T₂/N = 40 µs.</p>
  {{fig:pipeline|Figure 1. One round of the error-correction loop. This project times the decode step on the host computer; the whole loop must fit in τ<sub>DD</sub>. On the device replicas an explicit wait stands in for the classical part.}}

  <h2>Headline results</h2>
  <p class="lede">The reference run (14 October 2026) is saved in <code>reference_results/</code>; the pooled
    numbers combine six complete timing runs on two host CPUs.</p>
  <div class="card-grid">
    <div class="stat-card"><div class="val">113 / 31 ns</div><div class="lbl">Median decode, Python / C</div>
      <div class="sub">About 50 ns and 5 ns of real work once the cost of reading the clock is removed</div></div>
    <div class="stat-card"><div class="val">≤ 0.0036%</div><div class="lbl">Python misses at 40 µs</div>
      <div class="sub">14 misses in 660,000 cycles (95% upper bound); C: 1 miss, ≤ 0.00084%</div></div>
    <div class="stat-card"><div class="val">up to 1.39 ms</div><div class="lbl">Host stalls (most likely the OS)</div>
      <div class="sub">Rare, isolated, in both languages; no fitted distribution predicts them</div></div>
    <div class="stat-card"><div class="val">8–13 µs</div><div class="lbl">Wait that doubles logical error</div>
      <div class="sub">On Heron r2 / Eagle r3 replicas, far below the 40 µs deadline</div></div>
  </div>

  <h2>Research questions</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th></th><th>Question</th><th>Short answer</th></tr></thead>
    <tbody>
      <tr><td>RQ1</td><td>Where does the violation rate VR(τ) = P(L &gt; τ) cross a 1% budget?</td><td>At 268 ns (Python) and 46 ns (C); at 40 µs, VR ≤ 0.0036% and ≤ 0.00084%.</td></tr>
      <tr><td>RQ2</td><td>Is the latency tail light or heavy?</td><td>Two-part: a roughly log-normal body plus a separate plateau of stalls.</td></tr>
      <tr><td>RQ3</td><td>Does the code keep its benefit under device noise, and what does latency cost?</td><td>Yes, +1.6–1.7 points; but the error doubles after 8–13 µs of decoder wait.</td></tr>
      <tr><td>RQ4</td><td>How much does a C decoder improve on Python?</td><td>3.6× faster and far fewer misses, but the stalls remain.</td></tr>
    </tbody>
  </table></div>

  <h2>How the project is organised</h2>
  <ol class="timeline">
    <li class="tl-item"><div class="tl-left">Part 1</div><div class="tl-line"><span class="tl-dot"></span></div>
      <div class="tl-body"><h3>Physical layer</h3><p>A Ramsey experiment recovers T₂ from the noise model, and a Pauli
      experiment shows which errors a superposition can feel.</p></div></li>
    <li class="tl-item"><div class="tl-left">Part 2</div><div class="tl-line"><span class="tl-dot d2"></span></div>
      <div class="tl-body"><h3>The code</h3><p>The bit-flip code with ancilla syndrome extraction and a timed
      look-up-table decoder; logical versus physical error.</p></div></li>
    <li class="tl-item"><div class="tl-left">Part 3</div><div class="tl-line"><span class="tl-dot d3"></span></div>
      <div class="tl-body"><h3>Decoder latency</h3><p>Python, C and a modelled microcontroller; timer floors; VR(τ)
      with exact intervals; the shape of the tail.</p></div></li>
    <li class="tl-item"><div class="tl-left">Part 4</div><div class="tl-line"><span class="tl-dot d4"></span></div>
      <div class="tl-body"><h3>Device replicas</h3><p>Real-time feed-forward on calibrated IBM replicas, and a sweep of
      logical error against decoder wait.</p></div></li>
  </ol>

  <h2>Run it yourself</h2>
  <p>Clone the repository and run <code>setup.sh</code>, which creates a virtual environment with the pinned
    versions below. Then either open the notebook <code>QEC_Latency_Decoder.ipynb</code>, which reruns every
    experiment, re-checks each result with independent code, runs the test suite and confirms that this page and
    the paper agree with the data (about 5 minutes on 2 cores), or run <code>run_all.sh</code>, which reruns the
    experiments alone (about 6 minutes). Everything lands in <code>outputs/</code>. Nothing here needs an IBM
    account. On Windows, use WSL, because the C decoder needs gcc and a POSIX clock.</p>
  <pre class="cmd"><code>git clone https://github.com/requiemdoomed/QEC-Latency-Decoder.git
cd QEC-Latency-Decoder
bash setup.sh &amp;&amp; source qec-env/bin/activate
jupyter lab QEC_Latency_Decoder.ipynb      # the whole project, step by step
bash run_all.sh &amp;&amp; pytest                  # or: experiments and tests only</code></pre>
  {{code:requirements.txt}}
  {{code:setup.sh}}
  {{code:run_all.sh}}

  <h2>What I learned along the way</h2>
  <p class="lede">The first version of this project ran without errors, but several results were quietly
    wrong. These were the most instructive fixes.</p>
  <ul>
    <li><strong>Start the Ramsey experiment in |+⟩.</strong> Thermal relaxation never moves |0⟩, so a qubit started
      there showed no decay and the fit ran off to T₂ = 44,142 µs.</li>
    <li><strong>Spread random seeds.</strong> When Aer simulates shot by shot it seeds shot k with seed + k, so
      seeds 7 and 8 replay the same random stream one shot apart. <code>numpy.random.SeedSequence</code> fixes it.</li>
    <li><strong>Use exact intervals for rare events.</strong> A bootstrap interval collapses to [0, 0] when nothing
      misses; the Clopper–Pearson interval still gives an honest upper bound.</li>
    <li><strong>Pin the qubit layout.</strong> Letting the transpiler place circuits separately produced a fake
      0.42-point gap between offline and real-time correction.</li>
    <li><strong>Pad with a delay, not identity gates.</strong> The transpiler deletes <code>id</code> gates, so the
      "time-matched" bare qubit was not time-matched.</li>
    <li><strong>Measure the clock.</strong> Two back-to-back clock reads cost 63 ns in Python and 26 ns in C, more
      than most of the decoding itself.</li>
  </ul>
</section>
"""

THEORY = r"""
<section class="page" id="background" aria-labelledby="h-background">
  <header class="page-head">
    <div class="hero-tag"><span class="badge badge-purple">Background</span><span>The theory behind the measurements</span></div>
    <h1 id="h-background">Background</h1>
    <p class="lede">How qubit coherence turns into a classical timing budget, and how the measurements are judged.</p>
  </header>

  <h2>1. Coherence and the decoherence deadline</h2>
  <p>A qubit loses information in two ways. Energy relaxation (T₁) takes |1⟩ to |0⟩; dephasing (T₂) scrambles
    the phase of a superposition without changing populations, and physics requires T₂ ≤ 2T₁. A qubit prepared
    in |+⟩, left idle for a time t and rotated back with a Hadamard gate is still |+⟩ with probability</p>
  <div class="eq-box">F(t) = ½ + ½ · exp(−t / T₂)<span class="eq-label">[1] Ramsey decay</span></div>
  <p>With N syndrome rounds per logical cycle, each round's classical work has a budget of</p>
  <div class="eq-box">τ<sub>DD</sub> = T₂ / N = 120 µs / 3 = 40 µs<span class="eq-label">[2] decoherence deadline</span></div>

  <h2>2. The three-qubit bit-flip code</h2>
  <div class="eq-box">|0⟩<sub>L</sub> = |000⟩ · |1⟩<sub>L</sub> = |111⟩ · |ψ⟩<sub>L</sub> = α|000⟩ + β|111⟩<span class="eq-label">[3] encoding</span></div>
  <p>The code corrects any single X (bit-flip) error and cannot see Z (phase-flip) errors; the surface code
    handles both with a two-dimensional lattice of checks. Two ancillas measure the parities Z₀Z₁ and Z₁Z₂
    without measuring the data qubits, so a superposition survives the check. Qiskit prints classical bits
    right to left, so the syndrome string reads (Z₀Z₁)(Z₁Z₂):</p>
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

  <h2>3. Violation rate and the error budget</h2>
  <div class="eq-box">VR(τ) = P(L &gt; τ) ≈ (1/n) Σ 1[L<sub>i</sub> &gt; τ]<span class="eq-label">[5] violation rate</span></div>
  <div class="eq-box">τ* = inf { τ : VR(τ) ≤ 1% } = the 99th percentile<span class="eq-label">[6] threshold crossover</span></div>
  <p>Comparing VR with the roughly 1% surface-code threshold treats a missed deadline as one more error
    event. That is a modelling choice: the threshold is a per-operation physical error rate, used here as a
    budget. Meeting it is necessary but, as the device replicas show, far from sufficient.</p>
  <p>VR is a binomial proportion, so its interval comes from the exact Clopper–Pearson method. When none of
    n cycles misses, the 95% upper bound is about 3.7/n (0.037% for n = 10,000), whereas a bootstrap interval
    collapses to [0, 0].</p>

  <h2>4. Models for the latency distribution</h2>
  <ul>
    <li><strong>Log-normal:</strong> ln L ~ N(µ, σ²). Many small multiplicative delays (cache misses, branch
      mispredictions) produce it, and every moment is finite.</li>
    <li><strong>Power-law tail:</strong> P(L &gt; x) ~ x<sup>−α</sup>. The Hill estimator measures α from the largest
      observations: α &gt; 4 light, 2 &lt; α ≤ 4 moderate, α ≤ 2 heavy (infinite variance).</li>
    <li><strong>Mixture:</strong> a fast body plus a rare, separate population of long stalls (scheduler
      preemption, interrupts, hypervisor steal time). Neither model above predicts it; on a log-log survival
      plot it shows up as a plateau. This is what the measurements show.</li>
  </ul>

  <h2>5. Parameters</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Parameter</th><th>Project model</th><th>Heron r2 replica</th><th>Eagle r3 replica</th></tr></thead>
    <tbody>
      <tr><td>T₁ (median)</td><td class="mono">250 µs</td><td class="mono">283 µs</td><td class="mono">278 µs</td></tr>
      <tr><td>T₂ (median)</td><td class="mono">120 µs</td><td class="mono">144 µs</td><td class="mono">170 µs</td></tr>
      <tr><td>τ<sub>DD</sub> = T₂/3</td><td class="mono">40 µs</td><td class="mono">48 µs</td><td class="mono">57 µs</td></tr>
      <tr><td>Single-qubit gate</td><td class="mono">50 ns</td><td class="mono">32 ns (√X)</td><td class="mono">57 ns (√X)</td></tr>
      <tr><td>Two-qubit gate</td><td class="mono">500 ns (CNOT)</td><td class="mono">68 ns (CZ)</td><td class="mono">533 ns (ECR)</td></tr>
      <tr><td>Readout</td><td class="mono">—</td><td class="mono">2.28 µs</td><td class="mono">1.22 µs</td></tr>
      <tr><td>Median two-qubit / readout error</td><td class="mono">—</td><td class="mono">0.18% / 0.95%</td><td class="mono">0.78% / 1.98%</td></tr>
    </tbody>
  </table></div>
  <p class="small">Replica values are medians over all qubits of the snapshots shipped with qiskit-ibm-runtime
    0.50 (<code>FakeKingston</code>, <code>FakeSherbrooke</code>). Live devices drift from them.</p>

  <h2>6. Key references</h2>
  <ol class="refs">
    <li>Fowler, A. G., Mariantoni, M., Martinis, J. M. &amp; Cleland, A. N. (2012). Surface codes: Towards practical large-scale quantum computation. <em>Phys. Rev. A</em> 86, 032324. <a href="https://doi.org/10.1103/PhysRevA.86.032324" target="_blank" rel="noopener">doi:10.1103/PhysRevA.86.032324</a></li>
    <li>Battistel, F. et al. (2023). Real-time decoding for fault-tolerant quantum computing: Progress, challenges and outlook. <em>Nano Futures</em> 7, 032003. <a href="https://doi.org/10.1088/2399-1984/aceba6" target="_blank" rel="noopener">doi:10.1088/2399-1984/aceba6</a></li>
    <li>Google Quantum AI and Collaborators (2025). Quantum error correction below the surface code threshold. <em>Nature</em> 638, 920–926. <a href="https://doi.org/10.1038/s41586-024-08449-y" target="_blank" rel="noopener">doi:10.1038/s41586-024-08449-y</a></li>
    <li>Dean, J. &amp; Barroso, L. A. (2013). The tail at scale. <em>Commun. ACM</em> 56(2), 74–80. <a href="https://doi.org/10.1145/2408776.2408794" target="_blank" rel="noopener">doi:10.1145/2408776.2408794</a></li>
    <li>Terhal, B. M. (2015). Quantum error correction for quantum memories. <em>Rev. Mod. Phys.</em> 87, 307. <a href="https://doi.org/10.1103/RevModPhys.87.307" target="_blank" rel="noopener">doi:10.1103/RevModPhys.87.307</a></li>
    <li>Hill, B. M. (1975). A simple general approach to inference about the tail of a distribution. <em>Ann. Statist.</em> 3(5), 1163–1174. <a href="https://doi.org/10.1214/aos/1176343247" target="_blank" rel="noopener">doi:10.1214/aos/1176343247</a></li>
    <li>Clopper, C. J. &amp; Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated in the case of the binomial. <em>Biometrika</em> 26(4), 404–413. <a href="https://doi.org/10.1093/biomet/26.4.404" target="_blank" rel="noopener">doi:10.1093/biomet/26.4.404</a></li>
    <li>Javadi-Abhari, A. et al. (2024). Quantum computing with Qiskit. <a href="https://arxiv.org/abs/2405.08810" target="_blank" rel="noopener">arXiv:2405.08810</a></li>
  </ol>
  <p class="small">The full list of 32 references is in the paper.</p>
</section>
"""
