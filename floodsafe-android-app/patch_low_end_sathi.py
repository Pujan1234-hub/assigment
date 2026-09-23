from pathlib import Path
import re

ROOT = Path('floodsafe-android-app/app/build/generated/floodsafe-assets/floodsafe-nepal/v25')


def read(rel):
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f'missing generated asset: {rel}')
    return p, p.read_text(encoding='utf-8')


def write(p, text):
    p.write_text(text, encoding='utf-8')


# SATHI composer: remove forced synchronous layout on every keystroke and avoid
# expensive glass blur/viewport churn while the Android keyboard is animating.
p, text = read('sathi-flood-ai/live.js')
text = text.replace('backdrop-filter:blur(2px)', 'backdrop-filter:none')
text = text.replace('-webkit-backdrop-filter:blur(2px)', '-webkit-backdrop-filter:none')
old_resize = "const resize=()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,120)+'px'};"
new_resize = "let resizeFrame=0;const resize=()=>{if(resizeFrame)return;resizeFrame=requestAnimationFrame(()=>{resizeFrame=0;if(input.style.height!=='48px')input.style.height='48px'})};"
if old_resize not in text and new_resize not in text:
    raise SystemExit('SATHI resize marker missing')
text = text.replace(old_resize, new_resize, 1)

old_vv = "if(window.visualViewport){\n  const adjust=()=>{if(!panel.classList.contains('open'))return;const vv=visualViewport;const bottom=Math.max(0,innerHeight-vv.height-vv.offsetTop);panel.style.bottom=bottom+'px';panel.style.maxHeight=Math.max(360,vv.height-8)+'px'}\n  visualViewport.addEventListener('resize',adjust);\n  visualViewport.addEventListener('scroll',adjust);\n}"
new_vv = "if(window.visualViewport){\n  let vvFrame=0;\n  const adjust=()=>{if(vvFrame||!panel.classList.contains('open'))return;vvFrame=requestAnimationFrame(()=>{vvFrame=0;const vv=visualViewport;const bottom=Math.max(0,innerHeight-vv.height-vv.offsetTop);panel.style.bottom=bottom+'px';panel.style.maxHeight=Math.max(360,vv.height-8)+'px'})};\n  visualViewport.addEventListener('resize',adjust,{passive:true});\n}"
if old_vv in text:
    text = text.replace(old_vv, new_vv, 1)

focus_anchor = "input.addEventListener('input',resize);"
focus_code = "input.addEventListener('input',resize);input.addEventListener('focus',()=>{window.__fsSathiTyping=true;document.documentElement.classList.add('fsSathiTyping')},{passive:true});input.addEventListener('blur',()=>{window.__fsSathiTyping=false;document.documentElement.classList.remove('fsSathiTyping');setTimeout(()=>window.FloodSafeRiverRealtime?.refresh?.(),80)},{passive:true});"
if focus_code not in text:
    if focus_anchor not in text:
        raise SystemExit('SATHI input listener marker missing')
    text = text.replace(focus_anchor, focus_code, 1)

if '__FS_LOW_END_SATHI_V1__' not in text:
    marker = "if(window.__fsSathiFloodLiveV1)return;"
    if marker in text:
        text = text.replace(marker, marker + "window.__FS_LOW_END_SATHI_V1__=true;", 1)
    else:
        text = "window.__FS_LOW_END_SATHI_V1__=true;" + text

perf_css = "html.fsSathiTyping #riverMapGL{visibility:hidden!important}#sathiFloodPanel{contain:layout paint style}#sathiFloodInput{height:48px!important;max-height:48px!important;overflow-y:auto!important}"
if perf_css not in text:
    tail = "})();"
    inject = "const __fsPerfStyle=document.createElement('style');__fsPerfStyle.textContent='" + perf_css + "';document.head.appendChild(__fsPerfStyle);"
    if tail not in text:
        raise SystemExit('SATHI wrapper marker missing')
    text = text.rsplit(tail, 1)[0] + inject + tail
write(p, text)

# Floating shell glass blur is expensive on budget GPUs.
p, text = read('sathi-flood-ai/floating-ui-v2.js')
text = text.replace('backdrop-filter:blur(10px)', 'backdrop-filter:none')
text = text.replace('-webkit-backdrop-filter:blur(10px)', '-webkit-backdrop-filter:none')
write(p, text)

# Pause heavy official-river network/merge work while the user is actively typing.
# v0.8.77 changed some runtime function bodies/signatures, so patch by function
# signature rather than requiring the old exact body. This is a performance
# optimization only and must never block a release if the runtime is refactored.
p, text = read('trusted-river-runtime-v3.js')
delay_guard = "if(window.__fsSathiTyping)return 60000;"
refresh_guard = "if(window.__fsSathiTyping){schedule(60000);return}"

if delay_guard not in text:
    text, delay_count = re.subn(
        r'(function\s+nextDelay\s*\([^)]*\)\s*\{)',
        lambda m: m.group(1) + delay_guard,
        text,
        count=1,
    )
    if delay_count == 0:
        print('Low-end Android: nextDelay runtime signature changed; optional typing delay guard skipped')

if refresh_guard not in text:
    text, refresh_count = re.subn(
        r'(async\s+function\s+refresh\s*\([^)]*\)\s*\{)',
        lambda m: m.group(1) + refresh_guard,
        text,
        count=1,
    )
    if refresh_count == 0:
        # Some newer bundles drop `async` or expose refresh as a plain function.
        text, refresh_count = re.subn(
            r'(function\s+refresh\s*\([^)]*\)\s*\{)',
            lambda m: m.group(1) + refresh_guard,
            text,
            count=1,
        )
    if refresh_count == 0:
        print('Low-end Android: refresh runtime signature changed; optional typing refresh guard skipped')
write(p, text)

# Startup cache does not need to scan/write DOM every 1.2s forever.
p, text = read('startup-cache-30m-v1.js')
old = "setInterval(()=>{show();capture()},1200)"
new = "setInterval(()=>{if(!window.__fsSathiTyping){show();capture()}},15000)"
if old in text:
    text = text.replace(old, new)
if new not in text:
    raise SystemExit('startup cache interval patch failed')
write(p, text)

print('Low-end Android SATHI performance patch PASS')
