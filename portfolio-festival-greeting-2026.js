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

  // Nepal calendar 2083: keep the same Dashain–Tihar–Chhath greeting
  // continuously through Chhath's final sunrise rituals (16 Nov 2026).
  // Hide automatically on new page loads from 17 Nov, Nepal local time.
  const day = nepalDate();
  const isDashain = day >= "2026-10-11" && day <= "2026-10-25";
  if (day < "2026-10-11" || day > "2026-11-16") return;
  const dismissKey = "pjb-festival-2083-dashain-tihar-chhath-malshree-v4";
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
      <h2 id="pjb-festival-title">बडादशैँ, तिहार तथा छठ पर्व २०८३</h2>
      <p class="pjb-festival-sub">हार्दिक मंगलमय शुभकामना</p>
      <div class="pjb-festival-content">
        <div class="pjb-festival-portrait"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Goddess_Durga-_Early_1900_print_Durga_is_depicted_in_the_Hindu_pantheon_as_a_Goddess_riding_a_lion_and_with_many_arms%2C_each_carrying_a_weapon_to_defeat_Mahishasura_or_the_buffalo_demon.jpg/250px-thumbnail.jpg" alt="माता दुर्गाको मनमोहक चित्र" width="128" height="192"></div>
        <p id="pjb-festival-copy" class="pjb-festival-copy">
          <span class="pjb-festival-blessing">शुभ विजयादशमी • शुभ तिहार • शुभ छठ पर्व</span>
          माता दुर्गाको असीम कृपाले तपाईं तथा तपाईंको परिवारमा सुख, शान्ति, सुस्वास्थ्य र समृद्धि सधैँ रहिरहोस्।
          मान्यजनबाट प्राप्त टीका, जमरा र आशीर्वादले पारिवारिक सम्बन्धमा माया, सद्भाव र आत्मीयता अझ प्रगाढ बनाओस्।
          तिहारका दीपहरूले हरेक घर उज्यालो बनाऊन्। जीवनमा नयाँ आशा, उमङ्ग र सफलताको उज्यालो छाओस्।
        </p>
      </div>
      <p style="font-size:13px;line-height:1.7;color:#845833;margin:15px 0 0">
        स्वदेश तथा विदेशमा रहनुभएका सम्पूर्ण नेपाली दाजुभाइ तथा दिदीबहिनीहरूमा बडादशैँ, तिहार तथा छठ पर्वको हार्दिक शुभकामना।
      </p>
      <div class="pjb-festival-divider" aria-hidden="true">❀</div>
      <div class="pjb-festival-signature">हार्दिक शुभेच्छासहित<strong>Pujan</strong></div>
      <p id="pjb-festival-audio-hint" role="status" aria-live="polite" hidden
        style="font-size:12px;color:#8c5322;margin:12px 0 0;font-weight:650;line-height:1.6">♪ धुन सुन्न शुभकामना बक्समा एकपटक छुनुहोस्</p>
    </section>`;
  // One popup and one audio lifecycle per page load. The intro completion
  // event and its 5-second safety fallback can both call mount(). Once the
  // user closes the popup, NEVER start a second audio player from a timer.
  let didMountOrDismiss = false;
  function mount() {
    if (didMountOrDismiss || document.getElementById("pjb-festival-overlay")) return;
    didMountOrDismiss = true;
    document.body.appendChild(overlay);
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const close = overlay.querySelector("#pjb-festival-close");
    const audioHint = overlay.querySelector("#pjb-festival-audio-hint");
    function hint(visible, unavailable = false) {
      if (!audioHint) return;
      audioHint.hidden = !visible;
      if (visible) audioHint.textContent = unavailable
        ? "धुन अहिले उपलब्ध छैन"
        : "♪ धुन सुन्न शुभकामना बक्समा एकपटक छुनुहोस्";
    }


    // Audio recordings supplied by public music archive links referenced on
    // EkendraOnLine's Dashain/Malshree collection. This is real recorded music.
    // Some browsers disallow automatic audio with sound. In that case, the first
    // touch within the card retries the same recording without a play button.
    const audioTracks = isDashain ? [
      "https://www.newar.com.np/wp-content/uploads/2021/09/malshree_dhun.mp3",
      "https://archive.org/download/dashaindhoon_201910/Dashain%20Dhoon.mp3"
    ] : [
      "https://www.newar.com.np/wp-content/uploads/2021/09/malshree_dhun.mp3",
      "https://archive.org/download/dashaindhoon_201910/Dashain%20Dhoon.mp3"
    ];
    let sound = null;
    let soundTry = 1;
    let soundTimer = null;
    let allowGestureRetry = false;
    let isClosed = false;
    function clearTimer() {
      if (soundTimer !== null) { clearTimeout(soundTimer); soundTimer = null; }
    }
    function releaseSound() {
      clearTimer();
      if (!sound) return;
      sound.onerror = null;
      sound.onplaying = null;
      sound.pause();
      sound.removeAttribute("src");
      sound.load();
      sound = null;
    }
    function stopMusic() {
      isClosed = true;
      ++soundTry;
      allowGestureRetry = false;
      hint(false);
      releaseSound();
      overlay.removeEventListener("pointerdown", onFirstGesture, true);
      overlay.removeEventListener("pointerup", onFirstGesture, true);
      overlay.removeEventListener("touchend", onFirstGesture, true);
      overlay.removeEventListener("keydown", onFirstGesture, true);
    }
    function tryRecording(index, token) {
      if (isClosed || token !== soundTry) return;
      releaseSound();
      if (index >= audioTracks.length) { allowGestureRetry = false; hint(true, true); return; }
      const item = new Audio();
      item.src = audioTracks[index];
      item.preload = "auto";
      item.loop = true;
      item.volume = 0.8;
      sound = item;
      function nextAudio() {
        if (!isClosed && token === soundTry && sound === item) {
          allowGestureRetry = false;
          tryRecording(index + 1, token);
        }
      }
      item.onerror = nextAudio;
      item.onplaying = () => {
        if (token !== soundTry || isClosed) return;
        clearTimer();
        allowGestureRetry = false;
        hint(false);
      };
      soundTimer = setTimeout(nextAudio, 12500);
      try {
        const promise = item.play();
        if (promise && typeof promise.catch === "function") {
          promise.catch(error => {
            if (isClosed || token !== soundTry || sound !== item) return;
            if (error && error.name === "NotAllowedError") {
              clearTimer();
              allowGestureRetry = true;
              hint(true);
            } else if (error && error.name !== "AbortError") {
              nextAudio();
            }
          });
        }
      } catch (error) {
        if (error && error.name === "NotAllowedError") {
          clearTimer();
          allowGestureRetry = true;
          hint(true);
        } else nextAudio();
      }
    }
    // Mobile Chrome grants transient audio activation on POINTERUP/TOUCHEND,
    // not on touchstart/pointerdown. Starting before that made the first tap fail.
    let gesturePending = false;
    function onFirstGesture(event) {
      if (isClosed || !sound || !sound.paused || gesturePending) return;
      if (event.target.closest && event.target.closest("#pjb-festival-close")) return;
      if (event.type === "pointerdown" && event.pointerType !== "mouse") return;
      if (event.type === "pointerup" && event.pointerType === "mouse") return;
      if (event.type === "keydown" && !["Enter", " "].includes(event.key)) return;
      gesturePending = true;
      allowGestureRetry = false;
      const activeSound = sound;
      try {
        const promise = activeSound.play();
        if (promise && typeof promise.then === "function") {
          promise.then(() => {
            if (activeSound === sound && !isClosed) hint(false);
          }).catch(error => {
            if (activeSound !== sound || isClosed) return;
            if (error && error.name === "NotAllowedError") {
              allowGestureRetry = true;
              hint(true);
            } else if (error && error.name !== "AbortError") {
              tryRecording(1, soundTry);
            }
          }).finally(() => { gesturePending = false; });
        } else gesturePending = false;
      } catch (_) {
        gesturePending = false;
        allowGestureRetry = true;
        hint(true);
      }
    }
    overlay.addEventListener("pointerdown", onFirstGesture, true);
    overlay.addEventListener("pointerup", onFirstGesture, true);
    if (!window.PointerEvent) overlay.addEventListener("touchend", onFirstGesture, {capture:true,passive:true});
    overlay.addEventListener("keydown", onFirstGesture, true);
    // Start together with the popup, never continue after it closes.
    tryRecording(0, soundTry);
    function dismiss() {
      if (isClosed) return; // Repeated close/touch events must remain inert.
      didMountOrDismiss = true;
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
  // The original PJBUILTS opening intro always goes first. Mounting the
  // festival dialog (and starting its music) before this would cover the
  // intro because both overlays are top-level fixed elements.
  function mountAfterIntro() {
    if (window.__pjbuiltsIntroFinished || !document.getElementById("pjbuilts-original-intro")) {
      mount();
      return;
    }
    document.addEventListener("pjbuilts:intro-complete", mount, {once:true});
    // Safety fallback only if the intro's JavaScript could not dispatch its
    // completion event; the CSS animation has already finished by this point.
    window.setTimeout(() => {
      const intro = document.getElementById("pjbuilts-original-intro");
      if (!intro || getComputedStyle(intro).visibility === "hidden") mount();
    }, 5000);
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mountAfterIntro,{once:true});
  else mountAfterIntro();
})();