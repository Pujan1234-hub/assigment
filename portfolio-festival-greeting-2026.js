/* PJBUILTS — seasonal greeting 2083; isolated from portfolio sections. */
(() => {
  "use strict";
  if (!/^\/(?:index\.html)?$/.test(location.pathname) || document.getElementById("pjb-festival-overlay")) return;

  function nepalDate() {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kathmandu", year: "numeric", month: "2-digit", day: "2-digit"
    }).formatToParts(new Date());
    const values = {};
    for (const part of parts) values[part.type] = part.value;
    return values.year + "-" + values.month + "-" + values.day;
  }

  // Nepal festival calendar 2083: separate, self-expiring festive windows.
  const day = nepalDate();
  const isDashain = day >= "2026-10-11" && day <= "2026-10-25";
  const isTihar = day >= "2026-11-07" && day <= "2026-11-12";
  if (!isDashain && !isTihar) return;
  const season = isDashain ? "dashain" : "tihar";
  const dismissKey = "pjb-festival-2083-" + season;
  try { if (sessionStorage.getItem(dismissKey) === "dismissed") return; } catch (_) {}

  const style = document.createElement("style");
  style.id = "pjb-festival-styles";
  style.textContent = `
    #pjb-festival-overlay{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;
      padding:20px;background:rgba(8,9,14,.73);backdrop-filter:blur(9px);-webkit-backdrop-filter:blur(9px);overflow-y:auto;
      opacity:0;transition:opacity .5s ease}
    #pjb-festival-overlay.pjb-visible{opacity:1}
    #pjb-festival-overlay *{box-sizing:border-box}
    #pjb-festival-card{position:relative;width:min(100%,505px);max-height:min(92dvh,780px);overflow:auto;
      margin:auto;padding:28px 28px 23px;border:1px solid rgba(171,99,21,.33);border-radius:24px;
      background:radial-gradient(ellipse at 54% -16%,#fff3d8 0%,transparent 56%),linear-gradient(156deg,#fffaf0 0%,#fff4df 60%,#f6e6c7 100%);
      color:#55301a;text-align:center;box-shadow:0 25px 95px #000a,0 0 0 6px #fff3 inset;
      font-family:system-ui,-apple-system,"Noto Sans Devanagari",sans-serif;
      transform:translateY(24px) scale(.96);transition:transform .6s cubic-bezier(.18,.9,.15,1)}
    #pjb-festival-overlay.pjb-visible #pjb-festival-card{transform:none}
    #pjb-festival-card:before{content:"";position:absolute;inset:10px;pointer-events:none;border:1px solid #c7913d4d;border-radius:16px}
    #pjb-festival-close{position:absolute;right:13px;top:12px;width:38px;height:38px;border-radius:50%;
      border:1px solid #9c6b3345;background:#ffffffd9;color:#73431a;font:400 28px/1 system-ui;cursor:pointer;
      display:grid;place-items:center;z-index:2}
    #pjb-festival-close:hover,#pjb-festival-close:focus-visible{background:#f8d9a4;outline:2px solid #b87c29;outline-offset:2px}
    .pjb-festival-top{font-size:12px;letter-spacing:.22em;font-weight:800;color:#9a6b2b;margin-bottom:6px}
    .pjb-festival-symbol{color:#bb7827;font-size:18px;letter-spacing:9px;margin-bottom:2px}
    #pjb-festival-title{font-size:clamp(23px,5.3vw,31px);line-height:1.25;color:#912f23;font-weight:850;margin:6px 18px 4px;letter-spacing:-.03em}
    .pjb-festival-sub{font-size:14px;color:#91682e;font-weight:750;margin:0 0 17px}
    .pjb-festival-content{display:flex;align-items:center;text-align:left;gap:19px}
    .pjb-festival-portrait{flex:none;width:130px;height:177px;position:relative;border-radius:14px;overflow:hidden;
      box-shadow:0 7px 26px #8f471d3f;border:2px solid #ddb367}
    .pjb-festival-portrait img{display:block;width:100%;height:100%;object-fit:cover;object-position:center}
    .pjb-festival-copy{font-size:14.5px;line-height:1.85;color:#58391e;margin:0;font-weight:520}
    .pjb-festival-blessing{display:block;font-size:14px;font-weight:750;color:#934522;margin-bottom:8px}
    .pjb-festival-divider{display:flex;align-items:center;gap:12px;justify-content:center;color:#b87931;margin:20px 0 13px}
    .pjb-festival-divider:before,.pjb-festival-divider:after{content:"";height:1px;flex:1;background:linear-gradient(90deg,transparent,#c38c44 70%,transparent)}
    .pjb-festival-signature{font-size:13px;color:#90683b;line-height:1.55}
    .pjb-festival-signature strong{display:block;letter-spacing:.12em;font-size:15px;color:#693518;margin-top:2px}
    #pjb-festival-music{font:700 13px/1.3 system-ui,-apple-system,sans-serif;cursor:pointer;display:inline-flex;align-items:center;
      gap:8px;justify-content:center;border:1px solid #c38b42;padding:10px 17px;border-radius:30px;
      background:#fffaf0;color:#7d481c;box-shadow:0 4px 14px #9d6f2022;margin-top:14px}
    #pjb-festival-music:hover,#pjb-festival-music:focus-visible{background:#ffe7bb;outline:2px solid #d5a65a;outline-offset:2px}
    .pjb-festival-light{position:absolute;pointer-events:none;top:12%;color:#d99243;font-size:16px;opacity:.7;animation:pjb-festival-float 5s ease-in-out infinite alternate}
    .pjb-festival-light.a{left:7%;animation-delay:-2s}.pjb-festival-light.b{right:7%;animation-delay:-.6s}
    @keyframes pjb-festival-float{from{transform:translateY(0) rotate(-15deg);opacity:.35}to{transform:translateY(-16px) rotate(20deg);opacity:.8}}
    @media(max-width:480px){#pjb-festival-overlay{padding:12px}#pjb-festival-card{padding:22px 18px 20px;border-radius:21px}
      .pjb-festival-content{gap:13px;align-items:flex-start}.pjb-festival-portrait{width:104px;height:148px}
      .pjb-festival-copy{font-size:13px;line-height:1.74}#pjb-festival-title{margin:6px 22px 5px}
      .pjb-festival-sub{font-size:12.5px;margin-bottom:15px}.pjb-festival-blessing{font-size:13px}}
    @media(max-width:345px){.pjb-festival-content{flex-direction:column;align-items:center;text-align:center}
      .pjb-festival-portrait{height:132px;width:100px}.pjb-festival-copy{text-align:center}}
    @media(prefers-reduced-motion:reduce){#pjb-festival-overlay,#pjb-festival-card{transition:none}
      .pjb-festival-light{animation:none}}
  `;
  document.head.appendChild(style);

  const overlay = document.createElement("div");
  overlay.id = "pjb-festival-overlay";
  overlay.setAttribute("role", "presentation");
  overlay.innerHTML = `
    <section id="pjb-festival-card" role="dialog" aria-modal="true" aria-labelledby="pjb-festival-title" aria-describedby="pjb-festival-copy" lang="ne">
      <button id="pjb-festival-close" type="button" aria-label="शुभकामना सन्देश बन्द गर्नुहोस्">&times;</button>
      <span class="pjb-festival-light a" aria-hidden="true">✦</span><span class="pjb-festival-light b" aria-hidden="true">✦</span>
      <div class="pjb-festival-top">PJBUILTS • २०८३</div>
      <div class="pjb-festival-symbol" aria-hidden="true">✦ ❀ ✦</div>
      <h2 id="pjb-festival-title">${isDashain ? "बडादशैँ तथा शुभ दीपावली" : "शुभ दीपावली तथा तिहार"}</h2>
      <p class="pjb-festival-sub">हार्दिक मंगलमय शुभकामना</p>
      <div class="pjb-festival-content">
        <div class="pjb-festival-portrait"><img src="./assets/pjbuilts-durga-2083.jpg" alt="माता दुर्गाको मनमोहक चित्र" width="128" height="192"></div>
        <p id="pjb-festival-copy" class="pjb-festival-copy">
          <span class="pjb-festival-blessing">शुभ विजयादशमी • शुभ तिहार</span>
          माता दुर्गाको कृपाले हरेक मनमा साहस, हरेक घरमा सुख र हरेक यात्रामा उज्यालो छाओस्।
          टीकाको आशीर्वादले सम्बन्ध अझ आत्मीय बनाओस्, तिहारका दीपहरूले आशा र समृद्धिका नयाँ ढोका खोलून्।
        </p>
      </div>
      <p style="font-size:13px;line-height:1.7;color:#845833;margin:15px 0 0">
        स्वदेश तथा विदेशमा रहनुभएका सम्पूर्ण नेपालीजनमा सुस्वास्थ्य, शान्ति, प्रेम र सफलताको हार्दिक कामना।
      </p>
      <div class="pjb-festival-divider" aria-hidden="true">❀</div>
      <div class="pjb-festival-signature">सप्रेम, शुभेच्छासहित<strong>PJBUILTS</strong></div>
      <button type="button" id="pjb-festival-music" aria-pressed="false"><span aria-hidden="true">♫</span><span id="pjb-festival-music-label">मधुर चाडपर्वको धुन सुन्नुहोस्</span></button>
    </section>`;
  function mount() {
    if (document.getElementById("pjb-festival-overlay")) return;
    document.body.appendChild(overlay);
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const close = overlay.querySelector("#pjb-festival-close");
    const music = overlay.querySelector("#pjb-festival-music");
    const musicLabel = overlay.querySelector("#pjb-festival-music-label");
    let ctx = null, loop = null, playing = false;
    const melody = [293.66,369.99,440,493.88,440,369.99,329.63,293.66,
      329.63,369.99,440,587.33,493.88,440,369.99,293.66,329.63,369.99,440,329.63];

    function scheduleTune() {
      if (!ctx) return;
      const start = ctx.currentTime + .08;
      for (let i=0;i<melody.length;i++) {
        const t = start + i*.39, note = melody[i];
        const o=ctx.createOscillator(), overtone=ctx.createOscillator(), v=ctx.createGain();
        o.type="sine";o.frequency.value=note;
        overtone.type="triangle";overtone.frequency.value=note*2;
        const overtoneVol=ctx.createGain();overtoneVol.gain.value=.10;
        o.connect(v);overtone.connect(overtoneVol);overtoneVol.connect(v);
        v.connect(ctx.destination);
        v.gain.setValueAtTime(.0001,t);v.gain.exponentialRampToValueAtTime(.052,t+.045);
        v.gain.exponentialRampToValueAtTime(.0001,t+.35);
        o.start(t);o.stop(t+.36);overtone.start(t);overtone.stop(t+.36);
        if(i%4===0) {
          const drum=ctx.createOscillator(),g=ctx.createGain();drum.type="sine";
          drum.frequency.setValueAtTime(140,t);drum.frequency.exponentialRampToValueAtTime(72,t+.18);
          g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.025,t+.015);
          g.gain.exponentialRampToValueAtTime(.0001,t+.22);
          drum.connect(g);g.connect(ctx.destination);drum.start(t);drum.stop(t+.23);
        }
      }
    }
    async function stopMusic() {
      playing = false;music.setAttribute("aria-pressed","false");
      musicLabel.textContent="मधुर चाडपर्वको धुन सुन्नुहोस्";
      if(loop){clearInterval(loop);loop=null;}
      const previous=ctx;ctx=null;
      if(previous)try{await previous.close()}catch(_){}
    }
    music.addEventListener("click",async () => {
      if(playing){await stopMusic();return;}
      const Audio = window.AudioContext || window.webkitAudioContext;
      if(!Audio){musicLabel.textContent="यस ब्राउजरमा धुन उपलब्ध छैन";music.disabled=true;return;}
      try {
        ctx=new Audio();await ctx.resume();playing=true;scheduleTune();
        loop=setInterval(scheduleTune,melody.length*390);
        music.setAttribute("aria-pressed","true");musicLabel.textContent="धुन बन्द गर्नुहोस्";
      }catch(_){await stopMusic();musicLabel.textContent="धुन बजाउन सकिएन";}
    });
    function dismiss() {
      try{sessionStorage.setItem(dismissKey,"dismissed")}catch(_){}
      stopMusic();document.body.style.overflow=oldOverflow;
      overlay.remove();style.remove();document.removeEventListener("keydown",onKey);
    }
    function onKey(e){if(e.key==="Escape")dismiss()}
    close.addEventListener("click",dismiss);
    overlay.addEventListener("click",e=>{if(e.target===overlay)dismiss()});
    document.addEventListener("keydown",onKey);
    requestAnimationFrame(()=>{overlay.classList.add("pjb-visible");close.focus({preventScroll:true})});
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mount,{once:true});
  else mount();
})();