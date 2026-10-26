"""
build_html.py - rebuilds index.html, the project's demo page.
Author: Swayam Shakya

Every code block on the page is read straight from the repository files and
highlighted with Pygments (which also escapes < and &), so the page can never
drift away from the code that actually ran. Figures come from
reference_results/ and are embedded, so index.html is a single file.

Usage (from the repository root):
    pip install pygments pillow
    python site/build_html.py
"""
import base64
import os
import html
import io
import re
import sys

from PIL import Image
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import BashLexer, CLexer, PythonLexer, TextLexer

from content_a import OVERVIEW, THEORY
from content_b import W1, W2, W3, W4, ANALYSIS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SEARCH = [ROOT, os.path.join(ROOT, 'src')]          # where code files may live
FIG = os.path.join(ROOT, 'reference_results')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'index.html')

LANG = {'.py': ('Python', PythonLexer), '.c': ('C', CLexer),
        '.sh': ('Bash', BashLexer), '.txt': ('pip', TextLexer)}
FIGS = {'fig0': 'fig0_protected_circuit.png', 'fig1': 'fig1_coherence_decay.png',
        'fig2': 'fig2_pauli_sensitivity.png', 'fig2b': 'fig2b_logical_error.png',
        'fig3': 'fig3_main_result.png', 'fig4': 'fig4_tail_diagnostics.png',
        'fig5': 'fig5_hardware_fake_kingston.png', 'fig6': 'fig6_latency_sweep_fake_kingston.png'}
FMT = HtmlFormatter(nowrap=True, classprefix='t-')
used_files = []


def code_block(name: str) -> str:
    path = next(os.path.join(d, name) for d in SEARCH if os.path.exists(os.path.join(d, name)))
    shown = os.path.relpath(path, ROOT)
    text = open(path, encoding='utf-8').read().rstrip('\n')
    ext = '.' + name.rsplit('.', 1)[-1]
    label, lexer = LANG[ext]
    body = highlight(text, lexer(), FMT).rstrip('\n')
    used_files.append(name)
    n = text.count('\n') + 1
    return (f'<figure class="code-wrap">'
            f'<figcaption class="code-hdr"><span class="fname">{html.escape(shown)}</span>'
            f'<span class="lang">{label} · {n} lines</span>'
            f'<button type="button" class="copy-btn" aria-label="Copy {html.escape(name)}">copy</button>'
            f'</figcaption><pre><code>{body}</code></pre></figure>')


def figure(key: str, caption: str) -> str:
    img = Image.open(os.path.join(FIG, FIGS[key])).convert('RGB')
    if img.width > 1400:
        img = img.resize((1400, round(img.height * 1400 / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    alt = html.escape(caption.split('. ', 1)[-1], quote=True)
    return (f'<figure class="fig"><img src="data:image/png;base64,{data}" alt="{alt}" '
            f'width="{img.width}" height="{img.height}" loading="lazy">'
            f'<figcaption>{caption}</figcaption></figure>')


def expand(page: str) -> str:
    page = re.sub(r'\{\{code:([^}]+)\}\}', lambda m: code_block(m.group(1)), page)
    return re.sub(r'\{\{fig:([^|}]+)\|([^}]+)\}\}', lambda m: figure(m.group(1), m.group(2)), page)


CSS = r"""
:root{
  --bg:#07090f;--bg2:#0d1117;--bg3:#131c2e;--bg4:#1a2540;
  --border:#1e2d45;--border2:#2b3d5c;
  --fg:#dde4f0;--fg2:#a3b1c8;--fg3:#7d8ea8;
  --accent:#38bdf8;--accent2:#a5b4fc;--accent3:#34d399;--warn:#fbbf24;--crit:#f87171;
  --note-bg:rgba(56,189,248,.07);--note-bd:rgba(56,189,248,.25);
  --warn-bg:rgba(251,191,36,.07);--warn-bd:rgba(251,191,36,.25);
  --good-bg:rgba(52,211,153,.07);--good-bd:rgba(52,211,153,.28);
  --c-kw:#a5b4fc;--c-fn:#7dd3fc;--c-str:#6ee7b7;--c-num:#fcd34d;--c-cm:#7d8ea8;--c-cls:#f9a8d4;--c-bi:#93c5fd;
  --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --sans:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --serif:'IBM Plex Serif',Georgia,'Times New Roman',serif;
  color-scheme:dark;
}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]){
  --bg:#f6f8fb;--bg2:#ffffff;--bg3:#eef2f7;--bg4:#e3e9f2;
  --border:#d9e1ec;--border2:#c3cfdf;
  --fg:#0f172a;--fg2:#334766;--fg3:#5b6b82;
  --accent:#0369a1;--accent2:#4338ca;--accent3:#047857;--warn:#a16207;--crit:#b91c1c;
  --note-bg:rgba(3,105,161,.06);--note-bd:rgba(3,105,161,.25);
  --warn-bg:rgba(161,98,7,.07);--warn-bd:rgba(161,98,7,.28);
  --good-bg:rgba(4,120,87,.06);--good-bd:rgba(4,120,87,.25);
  --c-kw:#4338ca;--c-fn:#0369a1;--c-str:#047857;--c-num:#b45309;--c-cm:#64748b;--c-cls:#be185d;--c-bi:#1d4ed8;
  color-scheme:light;
}}
:root[data-theme="light"]{
  --bg:#f6f8fb;--bg2:#ffffff;--bg3:#eef2f7;--bg4:#e3e9f2;
  --border:#d9e1ec;--border2:#c3cfdf;
  --fg:#0f172a;--fg2:#334766;--fg3:#5b6b82;
  --accent:#0369a1;--accent2:#4338ca;--accent3:#047857;--warn:#a16207;--crit:#b91c1c;
  --note-bg:rgba(3,105,161,.06);--note-bd:rgba(3,105,161,.25);
  --warn-bg:rgba(161,98,7,.07);--warn-bd:rgba(161,98,7,.28);
  --good-bg:rgba(4,120,87,.06);--good-bd:rgba(4,120,87,.25);
  --c-kw:#4338ca;--c-fn:#0369a1;--c-str:#047857;--c-num:#b45309;--c-cm:#64748b;--c-cls:#be185d;--c-bi:#1d4ed8;
  color-scheme:light;
}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:15px;line-height:1.7;min-height:100vh}
img{max-width:100%;height:auto}
[hidden]{display:none!important}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* nav: a full-width band with its own gutter */
.nav{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--border);
  display:flex;align-items:stretch;overflow-x:auto;scrollbar-width:none;
  padding-top:env(safe-area-inset-top,0px);
  padding-left:max(8px,env(safe-area-inset-left,0px));padding-right:max(8px,env(safe-area-inset-right,0px))}
.nav::-webkit-scrollbar{display:none}
.nav-brand{font-family:var(--mono);font-size:11px;font-weight:500;color:var(--accent);letter-spacing:.1em;
  white-space:nowrap;padding:0 16px 0 8px;border-right:1px solid var(--border);display:flex;align-items:center;flex-shrink:0}
.tab{font:500 12px/1 var(--sans);color:var(--fg3);background:none;border:0;border-bottom:2px solid transparent;
  padding:0 13px;cursor:pointer;white-space:nowrap;height:46px;transition:color .15s,border-color .15s}
.tab:hover{color:var(--fg2)}
.tab[aria-selected="true"]{color:var(--accent);border-bottom-color:var(--accent)}
.nav-right{margin-left:auto;display:flex;align-items:center;padding:0 8px 0 14px;flex-shrink:0}
.theme-btn{font:11px var(--mono);color:var(--fg2);background:none;border:1px solid var(--border);border-radius:4px;
  padding:4px 10px;cursor:pointer}
.theme-btn:hover{color:var(--fg);border-color:var(--border2)}

/* pages: one centred column with a side gutter of at least 16px */
.page{display:none;max-width:1000px;margin:0 auto;padding-block:36px 80px;
  padding-left:max(20px,env(safe-area-inset-left,0px));padding-right:max(20px,env(safe-area-inset-right,0px))}
.page.active{display:block}
.page>*{min-width:0}

h1{font-family:var(--serif);font-size:2rem;font-weight:600;line-height:1.25;text-wrap:balance;margin:0 0 .6rem}
h2{font-family:var(--serif);font-size:1.35rem;font-weight:500;margin:2.6rem 0 .8rem;padding-bottom:.45rem;
  border-bottom:1px solid var(--border);text-wrap:balance}
h3{font-size:1rem;font-weight:600;margin:1.6rem 0 .5rem;color:var(--accent)}
p{margin:0 0 1rem;max-width:74ch}
ul,ol{padding-left:1.4rem;margin:0 0 1rem;max-width:78ch}
li{margin-bottom:.4rem}
strong{font-weight:600}
code{font-family:var(--mono);font-size:.86em;background:var(--bg3);border:1px solid var(--border);border-radius:3px;padding:0 .3em}
.lede{color:var(--fg2);font-size:15.5px}
.small{font-size:12.5px;color:var(--fg3)}

.hero{padding:28px 0 32px;border-bottom:1px solid var(--border);margin-bottom:1rem}
.page-head{margin-bottom:.5rem}
.hero-tag{font:11px var(--mono);color:var(--accent);letter-spacing:.06em;margin-bottom:1rem;display:flex;gap:8px;flex-wrap:wrap}
.hero-tag>span:not(.badge){background:var(--bg3);border:1px solid var(--border);border-radius:3px;padding:3px 8px}
.hero h1{font-size:2.25rem}
.hero-sub{font-size:1.02rem;color:var(--fg2);max-width:64ch;line-height:1.6;margin-bottom:1.4rem}
.hero-meta{font:12px var(--mono);color:var(--fg3);display:flex;gap:10px 28px;flex-wrap:wrap;margin:0}
.hero-meta div{display:flex;gap:8px}
.hero-meta dt{color:var(--fg2);font-weight:500}
.hero-meta dd{margin:0}

.card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:18px 22px;margin-bottom:1rem}
.abstract p{font-family:var(--serif);font-size:14.5px;line-height:1.8;color:var(--fg2);max-width:none;margin:0}
.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-bottom:1.4rem}
.stat-card{background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:16px 18px;min-width:0}
.stat-card .val{font:500 1.55rem/1.1 var(--mono);color:var(--accent)}
.stat-card .val.small{font-size:1.05rem}
.stat-card .lbl{font-size:12px;color:var(--fg);margin-top:6px;font-weight:500}
.stat-card .sub{font-size:12px;color:var(--fg3);margin-top:6px;line-height:1.5}

/* code */
.code-wrap{margin:1.2rem 0;min-width:0}
.code-hdr{background:var(--bg4);border:1px solid var(--border);border-bottom:0;border-radius:6px 6px 0 0;
  padding:7px 12px;display:flex;gap:12px;align-items:center}
.code-hdr .fname{font:500 12px var(--mono);color:var(--accent3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.code-hdr .lang{font:10.5px var(--mono);color:var(--fg3);margin-left:auto;white-space:nowrap}
.copy-btn{font:10.5px var(--mono);color:var(--fg2);background:none;border:1px solid var(--border2);border-radius:3px;
  padding:3px 9px;cursor:pointer;flex-shrink:0}
.copy-btn:hover{color:var(--fg)}
.copy-btn.ok{color:var(--accent3);border-color:var(--accent3)}
pre{background:var(--bg2);border:1px solid var(--border);border-radius:0 0 6px 6px;padding:14px 16px;
  overflow-x:auto;margin:0;max-height:620px;overflow-y:auto;font:12.5px/1.65 var(--mono)}
pre code{font:inherit;color:var(--fg);background:none;border:0;padding:0;white-space:pre}
pre.cmd{border-radius:6px;margin:1rem 0;max-height:none}
.t-k,.t-kn,.t-kc,.t-kd,.t-kr,.t-kt,.t-ow{color:var(--c-kw)}
.t-nf,.t-fm{color:var(--c-fn)}
.t-nc,.t-nd{color:var(--c-cls)}
.t-nb,.t-bp{color:var(--c-bi)}
.t-s,.t-s1,.t-s2,.t-sd,.t-sa,.t-si,.t-se,.t-sb,.t-sh,.t-sc{color:var(--c-str)}
.t-m,.t-mi,.t-mf,.t-mh,.t-mb,.t-mo,.t-il{color:var(--c-num)}
.t-c,.t-c1,.t-cm,.t-cs,.t-ch,.t-cp,.t-cpf{color:var(--c-cm);font-style:italic}
.t-nv{color:var(--c-fn)}

/* figures */
.fig{margin:1.2rem 0;background:#ffffff;border:1px solid var(--border);border-radius:6px;padding:10px}
.fig img{display:block;margin:0 auto}
.fig figcaption{font-size:12.5px;color:#334766;margin-top:8px;line-height:1.5}

/* equations, callouts, results */
.eq-box{background:var(--bg3);border-left:3px solid var(--accent);border-radius:0 6px 6px 0;padding:12px 16px;
  margin:1.1rem 0;font:13.5px/1.8 var(--mono);color:var(--fg);display:flex;flex-wrap:wrap;gap:4px 16px;
  justify-content:space-between;align-items:baseline}
.eq-label{font-size:11px;color:var(--fg3)}
.note,.warn-box{border-radius:6px;padding:13px 17px;margin:1.2rem 0}
.note{background:var(--note-bg);border:1px solid var(--note-bd)}
.note strong{color:var(--accent)}
.warn-box{background:var(--warn-bg);border:1px solid var(--warn-bd)}
.warn-box strong{color:var(--warn)}
.result{background:var(--good-bg);border:1px solid var(--good-bd);border-radius:8px;padding:6px 18px 4px;margin:1.4rem 0}
.result-head{font:600 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent3);margin:10px 0 8px}

/* tables */
.tbl-wrap{overflow-x:auto;margin:1.1rem 0;border-radius:6px;border:1px solid var(--border);background:var(--bg2)}
table{width:100%;border-collapse:collapse;font-size:13px}
thead tr{background:var(--bg3)}
th{text-align:left;padding:9px 12px;font-weight:500;color:var(--fg2);font-size:11.5px;letter-spacing:.03em;
  border-bottom:1px solid var(--border);white-space:nowrap}
td{padding:8px 12px;border-bottom:1px solid var(--border);vertical-align:top}
tr:last-child td{border-bottom:0}
.mono{font-family:var(--mono);font-size:12px;white-space:nowrap}

/* timeline, badges, lists */
.timeline{list-style:none;padding:0;margin:1.4rem 0}
.tl-item{display:flex;margin:0}
.tl-left{width:84px;flex-shrink:0;text-align:right;padding:3px 16px 0 0;font:11px var(--mono);color:var(--fg3)}
.tl-line{width:1px;background:var(--border2);flex-shrink:0;position:relative}
.tl-dot{width:9px;height:9px;border-radius:50%;background:var(--accent);position:absolute;left:-4px;top:7px}
.tl-dot.d2{background:var(--accent2)}.tl-dot.d3{background:var(--accent3)}.tl-dot.d4{background:var(--warn)}
.tl-body{padding:0 0 22px 16px;flex:1;min-width:0}
.tl-body h3{margin:0 0 .3rem}
.tl-body p{font-size:13.5px;color:var(--fg2);margin:0}
.badge{display:inline-block;font:500 10.5px var(--mono);padding:3px 8px;border-radius:3px;letter-spacing:.04em;border:1px solid}
.badge-blue{color:var(--accent);border-color:var(--note-bd);background:var(--note-bg)}
.badge-purple{color:var(--accent2);border-color:var(--border2);background:var(--bg3)}
.badge-green{color:var(--accent3);border-color:var(--good-bd);background:var(--good-bg)}
.badge-yellow{color:var(--warn);border-color:var(--warn-bd);background:var(--warn-bg)}
ul.check{list-style:none;padding-left:0}
ul.check li{padding-left:1.6rem;position:relative}
ul.check li::before{content:"☐";position:absolute;left:0;color:var(--fg3)}
ol.refs li{font-size:13.5px}

/* footer: shown under every tab */
.site-foot{border-top:1px solid var(--border);padding-block:18px 28px;font:12px/1.6 var(--mono);color:var(--fg3)}
.site-foot>div{max-width:1000px;margin:0 auto;display:flex;flex-wrap:wrap;gap:4px 20px;
  padding-left:max(20px,env(safe-area-inset-left,0px));padding-right:max(20px,env(safe-area-inset-right,0px))}
.site-foot strong{color:var(--fg2);font-weight:500}

@media (max-width:640px){
  .hero h1{font-size:1.65rem}
  h1{font-size:1.6rem}
  .tl-left{width:60px;font-size:10px;padding-right:10px}
  .code-hdr .lang{display:none}
  pre{font-size:11.5px}
}
@media print{
  .nav,.copy-btn{display:none}
  .site-foot{break-before:avoid}
  .page{display:block!important;max-width:none;padding:0 0 24px}
  pre{max-height:none;overflow:visible;white-space:pre-wrap}
  pre code{white-space:pre-wrap}
  .page+.page{break-before:page}
}
"""

JS = r"""
(function () {
  var root = document.documentElement;
  var themeBtn = document.getElementById('themeBtn');
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));

  function effectiveTheme() {
    var set = root.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  function labelTheme() {
    var t = effectiveTheme();
    themeBtn.textContent = t === 'dark' ? '☀ light' : '◑ dark';
    themeBtn.setAttribute('aria-label', 'Switch to ' + (t === 'dark' ? 'light' : 'dark') + ' theme');
  }
  themeBtn.addEventListener('click', function () {
    var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('qec_theme', next); } catch (e) {}
    labelTheme();
  });
  if (window.matchMedia) {
    var mq = window.matchMedia('(prefers-color-scheme: light)');
    if (mq.addEventListener) mq.addEventListener('change', labelTheme);
  }

  function show(id, push) {
    var page = document.getElementById(id);
    if (!page || !page.classList.contains('page')) return;
    document.querySelectorAll('.page').forEach(function (p) { p.classList.toggle('active', p === page); });
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.dataset.tab === id ? 'true' : 'false'); });
    if (push) {
      try { history.replaceState(null, '', '#' + id); } catch (e) {}
      window.scrollTo(0, 0);
    }
    try { localStorage.setItem('qec_tab', id); } catch (e) {}
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { show(t.dataset.tab, true); }); });
  window.addEventListener('hashchange', function () { show((location.hash || '').slice(1), false); });

  function copied(btn) {
    btn.textContent = 'copied'; btn.classList.add('ok');
    setTimeout(function () { btn.textContent = 'copy'; btn.classList.remove('ok'); }, 1600);
  }
  function selectCode(code) {
    var r = document.createRange(); r.selectNodeContents(code);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var code = btn.closest('.code-wrap').querySelector('pre code');
      var text = code.textContent;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { copied(btn); }, function () {
          selectCode(code);
          try { if (document.execCommand('copy')) copied(btn); } catch (e) {}
        });
      } else {
        selectCode(code);
        try { if (document.execCommand('copy')) copied(btn); } catch (e) {}
      }
    });
  });

  try {
    var saved = localStorage.getItem('qec_theme');
    if (saved === 'light' || saved === 'dark') root.setAttribute('data-theme', saved);
  } catch (e) {}
  labelTheme();
  var start = (location.hash || '').slice(1);
  if (!document.getElementById(start)) {
    try { start = localStorage.getItem('qec_tab') || 'overview'; } catch (e) { start = 'overview'; }
  }
  show(document.getElementById(start) ? start : 'overview', false);
})();
"""

NAV = [('overview', 'Overview'), ('theory', 'Theory'), ('w1', 'Weekend 1'), ('w2', 'Weekend 2'),
       ('w3', 'Weekend 3'), ('w4', 'Weekend 4'), ('analysis', 'Analysis')]

nav_html = ('<nav class="nav" aria-label="Sections"><div class="nav-brand">QEC · LATENCY</div>'
            + ''.join(f'<button type="button" class="tab" data-tab="{k}" aria-selected="{"true" if i == 0 else "false"}">{v}</button>'
                      for i, (k, v) in enumerate(NAV))
            + '<div class="nav-right"><button type="button" class="theme-btn" id="themeBtn">☀ light</button></div></nav>')

pages = ''.join(expand(p) for p in (OVERVIEW, THEORY, W1, W2, W3, W4, ANALYSIS))

doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>QEC Latency Research — Swayam Shakya</title>
<meta name="description" content="A four-weekend research notebook on classical decoder latency in quantum error correction, by Swayam Shakya. Every script runs end to end and is covered by unit tests.">
<meta name="author" content="Swayam Shakya">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&amp;family=IBM+Plex+Serif:wght@400;500;600&amp;display=swap">
<style>{CSS}</style>
</head>
<body>
{nav_html}
<main>
{pages}
</main>
<footer class="site-foot"><div><span><strong>Swayam Shakya</strong></span><span>QEC Decoder Latency Study · four-weekend research notebook</span><span>Reference run 14 Oct 2026 · re-run and tested 26 Oct 2026</span></div></footer>
<script>{JS}</script>
</body>
</html>
"""
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write(doc)
print(f'Wrote {OUT}: {len(doc.encode()):,} bytes; code blocks: {len(used_files)} → {used_files}')
