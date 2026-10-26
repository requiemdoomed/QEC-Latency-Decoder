"""Render index.html in Chromium (Author: Swayam Shakya): overflow, console errors, tabs, theme toggle, copy, screenshots."""
import os
import sys

from playwright.sync_api import sync_playwright

PAGE = 'file://' + os.path.abspath(sys.argv[1])
SHOTS = sys.argv[2]
os.makedirs(SHOTS, exist_ok=True)
EXE = os.environ.get('CHROMIUM')            # optional: path to a Chromium binary
TABS = ['overview', 'theory', 'w1', 'w2', 'w3', 'w4', 'analysis']

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EXE) if EXE else p.chromium.launch()
    for scheme, width in (('dark', 1280), ('light', 1280), ('light', 390), ('dark', 390)):
        ctx = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme=scheme,
                                  permissions=['clipboard-read', 'clipboard-write'])
        page = ctx.new_page()
        errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(PAGE)
        page.wait_for_timeout(400)
        bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
        label = page.inner_text('#themeBtn')
        overflow = {}
        for t in TABS:
            page.click(f'.tab[data-tab="{t}"]')
            page.wait_for_timeout(80)
            visible = page.evaluate("document.querySelector('.page.active').id")
            assert visible == t, (t, visible)
            sw = page.evaluate("document.documentElement.scrollWidth")
            if sw > width:
                wide = page.evaluate("""() => { const W = innerWidth; const out = [];
                    document.querySelectorAll('.page.active *').forEach(el => { const r = el.getBoundingClientRect();
                      if (r.right > W + 1 && !el.closest('.tbl-wrap, pre, .nav')) out.push(el.tagName + '.' + el.className); });
                    return out.slice(0, 5); }""")
                overflow[t] = (sw, wide)
            page.screenshot(path=f'{SHOTS}/{scheme}_{width}_{t}.png', full_page=False)
        # copy button round trip on Weekend 1's first code block
        page.click('.tab[data-tab="w1"]')
        page.click('#w1 .copy-btn >> nth=1')
        page.wait_for_timeout(200)
        clip = page.evaluate("navigator.clipboard.readText()")
        expect = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'src', 'experiment_1_1_coherence.py'), encoding='utf-8').read().rstrip('\n')
        # theme toggle flips the effective theme
        page.click('#themeBtn')
        after = page.evaluate("document.documentElement.getAttribute('data-theme')")
        bg2 = page.evaluate("getComputedStyle(document.body).backgroundColor")
        # deep link
        page.goto(PAGE + '#w3'); page.wait_for_timeout(200)
        deep = page.evaluate("document.querySelector('.page.active').id")
        fresh = ctx.new_page(); fresh.goto(PAGE + '#w4'); fresh.wait_for_timeout(300)
        deep += '/' + fresh.evaluate("document.querySelector('.page.active').id"); fresh.close()
        print(f"{scheme:5s} {width:4d}px  body={bg}  button='{label}'  toggle→{after} body={bg2}  "
              f"copy_ok={clip == expect}  deeplink={deep}  overflow={overflow or 'none'}  errors={errors or 'none'}")
        ctx.close()
    browser.close()
