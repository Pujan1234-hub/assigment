from pathlib import Path

p = Path('floodsafe-android-app/app/build/generated/floodsafe-assets/floodsafe-nepal/v25/index.html')
text = p.read_text(encoding='utf-8')

if 'id="pjbuiltsIntro"' not in text:
    style = '''<style id="pjbuiltsIntroStyle">
#pjbuiltsIntro{position:fixed;inset:0;z-index:2147483647;display:grid;place-items:center;background:radial-gradient(circle at 50% 47%,#082038 0%,#030b18 46%,#020713 100%);overflow:hidden;pointer-events:none;opacity:1;transition:opacity .22s ease}
#pjbuiltsIntro.pj-out{opacity:0}
#pjbuiltsIntro .pj-wrap{position:relative;display:flex;flex-direction:column;align-items:center;transform:translateY(-2vh)}
#pjbuiltsIntro .pujan{position:absolute;top:12px;font:950 clamp(42px,14vw,76px)/1 system-ui,-apple-system,Segoe UI,sans-serif;letter-spacing:.08em;color:#e9fbff;text-shadow:0 0 10px #28d9ff,0 0 26px rgba(39,211,255,.65);opacity:0;transform:scale(.82)}
#pjbuiltsIntro.pj-go .pujan{animation:pujanIn .28s ease .05s forwards,pujanSplit .32s ease .48s forwards}
#pjbuiltsIntro .pj-mark{position:relative;display:flex;align-items:center;justify-content:center;margin-top:4px;font:950 clamp(72px,22vw,116px)/.86 system-ui,-apple-system,Segoe UI,sans-serif;letter-spacing:-.14em;color:#e9fbff;filter:drop-shadow(0 0 8px #28d9ff) drop-shadow(0 0 20px rgba(39,211,255,.65))}
#pjbuiltsIntro .pj-p,#pjbuiltsIntro .pj-j{display:inline-block;opacity:0;transform:scale(.65)}
#pjbuiltsIntro.pj-go .pj-p{animation:pjZapIn .28s cubic-bezier(.14,.9,.18,1) .64s forwards}
#pjbuiltsIntro.pj-go .pj-j{animation:pjZapIn .28s cubic-bezier(.14,.9,.18,1) .72s forwards}
#pjbuiltsIntro .pj-bolt{position:absolute;height:2px;border-radius:5px;background:linear-gradient(90deg,transparent,#fff 30%,#49e8ff 62%,transparent);box-shadow:0 0 5px #fff,0 0 12px #24d8ff;opacity:0;transform-origin:left center}
#pjbuiltsIntro .b1{width:96px;left:50%;top:9px;transform:translateX(-105px) rotate(12deg)}
#pjbuiltsIntro .b2{width:88px;right:50%;top:52px;transform:translateX(102px) rotate(-15deg)}
#pjbuiltsIntro .b3{width:70px;left:50%;bottom:5px;transform:translateX(-76px) rotate(-8deg)}
#pjbuiltsIntro.pj-go .pj-bolt{animation:pjCurrent .65s steps(2,end) .63s both}
#pjbuiltsIntro .pj-name{margin-top:18px;font:850 clamp(18px,5vw,27px)/1 system-ui,-apple-system,Segoe UI,sans-serif;letter-spacing:.3em;color:#aeeeff;opacity:0;transform:translateY(8px) scale(.96);margin-left:.3em;text-shadow:0 0 12px rgba(57,211,255,.6)}
#pjbuiltsIntro.pj-go .pj-name{animation:pjBuilt .3s ease .93s forwards}
#pjbuiltsIntro .pj-line{margin-top:10px;width:0;height:2px;border-radius:2px;background:linear-gradient(90deg,transparent,#38dfff,transparent);box-shadow:0 0 10px #23d6ff}
#pjbuiltsIntro.pj-go .pj-line{animation:pjLine .28s ease 1.02s forwards}
#pjbuiltsIntro .pj-tag{margin-top:9px;font:650 9px/1 system-ui,-apple-system,Segoe UI,sans-serif;letter-spacing:.18em;color:rgba(172,231,247,.72);opacity:0}
#pjbuiltsIntro.pj-go .pj-tag{animation:pjFade .2s ease 1.08s forwards}
@keyframes pujanIn{to{opacity:1;transform:scale(1)}}
@keyframes pujanSplit{0%{opacity:1;transform:scale(1)}55%{letter-spacing:.2em;filter:brightness(2.3)}100%{opacity:0;transform:scale(1.12);letter-spacing:.34em}}
@keyframes pjZapIn{0%{opacity:0;transform:scale(.65);filter:brightness(3)}50%{opacity:1;transform:scale(1.12);filter:brightness(2.8)}100%{opacity:1;transform:scale(1);filter:brightness(1)}}
@keyframes pjCurrent{0%,9%,21%,39%,58%,76%{opacity:0}5%,14%,29%,46%,66%,82%{opacity:1}100%{opacity:0}}
@keyframes pjBuilt{to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes pjLine{to{width:136px}}
@keyframes pjFade{to{opacity:1}}
</style>'''
    splash = '''<div id="pjbuiltsIntro" aria-hidden="true"><div class="pj-wrap"><div class="pujan">PUJAN</div><div class="pj-mark"><span class="pj-p">P</span><span class="pj-j">J</span><i class="pj-bolt b1"></i><i class="pj-bolt b2"></i><i class="pj-bolt b3"></i></div><div class="pj-name">BUILTS</div><div class="pj-line"></div><div class="pj-tag">IDEA • BUILD • INNOVATE</div></div></div><script id="pjbuiltsIntroScript">(()=>{const e=document.getElementById('pjbuiltsIntro');if(!e)return;requestAnimationFrame(()=>requestAnimationFrame(()=>e.classList.add('pj-go')));setTimeout(()=>{e.classList.add('pj-out');setTimeout(()=>e.remove(),240)},1450)})();</script>'''
    if '</head>' not in text or '<body>' not in text: raise SystemExit('HTML markers missing for PJBUILTS intro')
    text=text.replace('</head>',style+'</head>',1).replace('<body>','<body>'+splash,1)

p.write_text(text,encoding='utf-8')
if 'id="pjbuiltsIntro"' not in text or '>PUJAN<' not in text or 'class="pj-name">BUILTS<' not in text: raise SystemExit('PJBUILTS intro marker missing')
print('PUJAN -> electric PJBUILTS launch intro applied')
