from pathlib import Path

p = Path('floodsafe-android-app/app/build/generated/floodsafe-assets/floodsafe-nepal/v25/index.html')
text = p.read_text(encoding='utf-8')

if 'id="pjbuiltsIntro"' not in text:
    style = '''<style id="pjbuiltsIntroStyle">
#pjbuiltsIntro{position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;background:linear-gradient(160deg,#f7fcff 0%,#eaf6ff 52%,#dff3ff 100%);overflow:hidden;pointer-events:none;opacity:1;transition:opacity .28s ease}
#pjbuiltsIntro.pj-out{opacity:0}
#pjbuiltsIntro .pj-wrap{display:flex;flex-direction:column;align-items:center;gap:12px;transform:translateY(-2vh)}
#pjbuiltsIntro .pj-mark{display:flex;align-items:center;justify-content:center;font:900 clamp(58px,18vw,92px)/.9 system-ui,-apple-system,Segoe UI,sans-serif;letter-spacing:-.12em;color:#0878b9;filter:drop-shadow(0 9px 18px rgba(8,120,185,.16))}
#pjbuiltsIntro .pj-p{opacity:0;transform:translate3d(-70px,0,0) scale(.9)}
#pjbuiltsIntro .pj-j{opacity:0;transform:translate3d(70px,0,0) scale(.9)}
#pjbuiltsIntro.pj-go .pj-p,#pjbuiltsIntro.pj-go .pj-j{opacity:1;transform:translate3d(0,0,0) scale(1);transition:transform .46s cubic-bezier(.2,.9,.2,1),opacity .28s ease}
#pjbuiltsIntro .pj-name{font:800 clamp(18px,5vw,26px)/1 system-ui,-apple-system,Segoe UI,sans-serif;letter-spacing:.28em;color:#0b5f91;opacity:0;transform:translateY(12px);margin-left:.28em}
#pjbuiltsIntro.pj-go .pj-name{opacity:1;transform:translateY(0);transition:opacity .32s ease .38s,transform .38s cubic-bezier(.2,.9,.2,1) .38s}
#pjbuiltsIntro .pj-line{width:0;height:2px;border-radius:2px;background:#0aa7cf;opacity:.7}
#pjbuiltsIntro.pj-go .pj-line{width:118px;transition:width .42s ease .58s}
@media (prefers-reduced-motion:reduce){#pjbuiltsIntro *{transition:none!important;animation:none!important}#pjbuiltsIntro .pj-p,#pjbuiltsIntro .pj-j,#pjbuiltsIntro .pj-name{opacity:1;transform:none}#pjbuiltsIntro .pj-line{width:118px}}
</style>'''
    splash = '''<div id="pjbuiltsIntro" aria-hidden="true"><div class="pj-wrap"><div class="pj-mark"><span class="pj-p">P</span><span class="pj-j">J</span></div><div class="pj-name">BUILTS</div><div class="pj-line"></div></div></div><script id="pjbuiltsIntroScript">(()=>{const e=document.getElementById('pjbuiltsIntro');if(!e)return;requestAnimationFrame(()=>requestAnimationFrame(()=>e.classList.add('pj-go')));const reduced=matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;setTimeout(()=>{e.classList.add('pj-out');setTimeout(()=>e.remove(),300)},reduced?420:1450)})();</script>'''
    if '</head>' not in text or '<body>' not in text:
        raise SystemExit('HTML markers missing for PJBUILTS intro')
    text = text.replace('</head>', style + '</head>', 1)
    text = text.replace('<body>', '<body>' + splash, 1)

p.write_text(text, encoding='utf-8')
if 'id="pjbuiltsIntro"' not in text or 'PJBUILTS' in text:
    pass
print('PJBUILTS smooth launch intro applied')
