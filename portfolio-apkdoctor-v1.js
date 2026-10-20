/* APKDoctor — an additive PJBUILTS product showcase. Nothing else is modified. */
(()=>{
  if(window.__pjApkDoctorPortfolio) return;
  window.__pjApkDoctorPortfolio=true;
  const stylesheet = document.createElement('style');
  stylesheet.id = 'pj-apkdoctor-product-style';
  stylesheet.textContent = `
    #work #apkdoctor.project{grid-column:1/-1!important;--accent:#168b69!important;}
    #work #apkdoctor.project .project-visual{background:radial-gradient(circle at 50% 50%,#ebfaf4 0%,#f5f8f2 55%,#e9efe8 100%)!important;}
    #work #apkdoctor .apk-preview-stage{position:relative;display:grid;place-items:center;width:100%;height:100%;isolation:isolate;overflow:hidden;}
    #work #apkdoctor .apk-preview-stage:before,#work #apkdoctor .apk-preview-stage:after{content:"";position:absolute;width:310px;height:310px;border:1px solid rgba(21,129,94,.15);border-radius:50%;pointer-events:none;animation:apkOrbit 14s linear infinite;}
    #work #apkdoctor .apk-preview-stage:after{width:410px;height:410px;border-style:dashed;animation-duration:22s;animation-direction:reverse;}
    #work #apkdoctor .apk-screenshot{position:relative;z-index:2;display:block;max-width:100%;height:auto;width:min(220px,54%);border:7px solid #17251e;border-radius:21px;overflow:hidden;background:#fbfcf9;box-shadow:0 22px 48px rgba(12,56,39,.23),0 0 0 1px rgba(16,94,69,.13);animation:apkLift 5s ease-in-out infinite;transform-origin:center;}
    #work #apkdoctor .apk-screenshot img{width:100%;height:auto;display:block;background:#fffaf1;border-radius:14px;}
    #work #apkdoctor .apk-scan-glow{position:absolute;z-index:3;top:25%;height:2px;width:min(260px,60%);background:linear-gradient(90deg,transparent,#31aa81,transparent);box-shadow:0 0 17px #31aa81;pointer-events:none;opacity:.48;animation:apkScanner 6s ease-in-out infinite;}
    #work #apkdoctor .apk-preview-chip{position:absolute;z-index:4;background:#fff;color:#206b51;border:1px solid #b6dacd;box-shadow:0 9px 22px rgba(33,103,81,.09);border-radius:9px;padding:9px 13px;font:800 11px/1.4 system-ui,sans-serif;letter-spacing:.03em;}
    #work #apkdoctor .apk-preview-chip.a{top:22%;left:8%;animation:apkLift 6s ease-in-out infinite;}
    #work #apkdoctor .apk-preview-chip.b{bottom:22%;right:8%;animation:apkLift 6s ease-in-out -2s infinite;}
    #work #apkdoctor .apk-preview-chip i{display:inline-block;width:7px;height:7px;background:#1b9874;border-radius:50%;margin-right:6px;}
    @keyframes apkLift{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
    @keyframes apkOrbit{to{transform:rotate(360deg)}}
    @keyframes apkScanner{0%,100%{top:18%;opacity:0}50%{top:80%;opacity:.7}}
    @media(min-width:920px){
      html[data-pj-layout="editorial-v4"] body #work #apkdoctor.project{display:grid!important;grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr)!important;min-height:475px!important;}
      html[data-pj-layout="editorial-v4"] body #work #apkdoctor .project-copy{order:0!important;padding:37px 42px!important;}
      html[data-pj-layout="editorial-v4"] body #work #apkdoctor .project-visual{order:1!important;height:auto!important;min-height:475px!important;border-bottom:0!important;border-left:1px solid #e0ece4!important;}
    }
    @media(max-width:919px){
      html[data-pj-layout="editorial-v4"] body #work #apkdoctor.project{grid-column:1/-1!important;}
      html[data-pj-layout="editorial-v4"] body #work #apkdoctor .project-visual{height:365px!important;min-height:365px!important;}
      #work #apkdoctor .apk-screenshot{width:min(172px,55%)!important;}
      #work #apkdoctor .apk-preview-chip.a{left:4%}#work #apkdoctor .apk-preview-chip.b{right:4%}
    }
    @media(prefers-reduced-motion:reduce){#work #apkdoctor *{animation:none!important;transition:none!important;}}
  `;
  document.head.appendChild(stylesheet);

  const mount=()=>{
    const grid=document.querySelector('#work .project-list');
    if(!grid || document.getElementById('apkdoctor'))return;
    const card=document.createElement('article');
    card.className='project reveal on apkdoctor-feature';
    card.id='apkdoctor';
    card.style.setProperty('--accent','#168b69');
    card.innerHTML=`
      <div class="project-copy">
        <div class="project-no">Featured product · Android quality</div>
        <h3>APKDoctor</h3>
        <div class="status"><i></i> Free web tool · Live</div>
        <p>Upload an Android APK or project ZIP to check its health before release. APKDoctor runs static analysis locally in your browser, helping you spot common build problems without uploading your file to a server.</p>
        <div class="features">
          <div class="feature"><b>01</b>APK & ZIP inspection</div>
          <div class="feature"><b>02</b>Manifest & permissions</div>
          <div class="feature"><b>03</b>Security & secret checks</div>
          <div class="feature"><b>04</b>Gradle & release blockers</div>
        </div>
        <div class="project-links">
          <a href="https://apkdoctor-pujan7.vercel.app/" target="_blank" rel="noopener noreferrer">Open APKDoctor ↗</a>
        </div>
      </div>
      <div class="project-visual" aria-label="APKDoctor website screenshot">
        <div class="apk-preview-stage">
          <div class="apk-preview-chip a"><i></i>LOCAL ANALYSIS</div>
          <div class="apk-screenshot"><img src="https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/assets/portfolio/apkdoctor-preview.svg" alt="Screenshot of the APKDoctor web app uploaded by the project owner" loading="lazy" width="270" height="551"></div>
          <div class="apk-scan-glow"></div>
          <div class="apk-preview-chip b"><i></i>APK · PROJECT ZIP</div>
        </div>
      </div>`;
    grid.prepend(card);
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();
