(()=>{
  /* Portfolio presentation compatibility + light premium theme — v5 */
  if(window.__pcPortfolioMotionV5) return;
  window.__pcPortfolioMotionV5=true;

  // The current index owns the layout and animation system. Prevent the older
  // enhancer/i18n bundle from repainting it with incompatible legacy styles.
  window.__pcPortfolioI18nV6=true;

  const LIGHT_CSS=`
    :root{
      --bg:#f7f3eb!important;
      --bg2:#eee8dd!important;
      --panel:#fffdf8!important;
      --panel2:#f5f0e7!important;
      --text:#171b23!important;
      --muted:#667085!important;
      --line:rgba(26,32,44,.12)!important;
      --cyan:#0d9fb4!important;
      --blue:#4967e8!important;
      --purple:#7b5ce1!important;
      --green:#168a68!important;
      --orange:#d77b2c!important;
      --red:#d94f70!important;
    }

    html,body{background:#f7f3eb!important;color:#171b23!important;color-scheme:light!important}
    body:before{
      background:
        radial-gradient(850px circle at var(--mx) var(--my),rgba(73,103,232,.075),transparent 46%),
        radial-gradient(680px circle at 12% 76%,rgba(13,159,180,.07),transparent 50%),
        linear-gradient(180deg,#fbf8f2 0%,#f4efe6 48%,#f8f4ed 100%)!important;
    }
    body:after{
      opacity:.5!important;
      background-image:linear-gradient(rgba(40,48,62,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(40,48,62,.035) 1px,transparent 1px)!important;
    }
    .cursor-glow{background:radial-gradient(circle,rgba(73,103,232,.08),transparent 68%)!important}

    .nav.scrolled{background:rgba(250,247,240,.92)!important;border-bottom-color:rgba(26,32,44,.10)!important;box-shadow:0 8px 30px rgba(30,35,45,.06)!important}
    .brand{color:#171b23!important}.brandmark{color:#fff!important;box-shadow:0 10px 25px rgba(73,103,232,.18)!important}
    .navlinks{color:#616b7b!important}.navlinks a:hover,.navlinks a.active{color:#171b23!important}
    .status-pill{background:#edf8f3!important;border-color:#b9e5d3!important;color:#166b50!important}

    .eyebrow{background:rgba(255,255,255,.74)!important;border-color:rgba(26,32,44,.12)!important;color:#505b6c!important;box-shadow:0 8px 24px rgba(32,38,48,.04)!important}
    h1{color:#171b23!important}
    h1 .grad{background:linear-gradient(95deg,#171b23 5%,#3157d5 46%,#7655d6 92%)!important;-webkit-background-clip:text!important;background-clip:text!important;color:transparent!important}
    h1 .thin{color:#596476!important}.hero-copy{color:#596476!important}
    .stat span{color:#697486!important}.hero-stats{border-top-color:rgba(26,32,44,.11)!important}
    .btn{background:rgba(255,255,255,.78)!important;border-color:rgba(26,32,44,.13)!important;color:#202632!important;box-shadow:0 7px 20px rgba(30,35,45,.035)!important}
    .btn:hover{border-color:rgba(73,103,232,.35)!important;background:#fff!important}
    .btn.primary{background:linear-gradient(135deg,#39c8dc,#7581f2)!important;color:#071019!important;border:0!important;box-shadow:0 14px 34px rgba(73,103,232,.16)!important}

    /* Keep the hero code card intentionally dark so the page still has depth. */
    .dev-card{border-color:rgba(26,32,44,.15)!important;box-shadow:0 28px 75px rgba(35,42,55,.17)!important}
    .float-chip{background:rgba(255,253,248,.90)!important;border-color:rgba(26,32,44,.12)!important;color:#667085!important;box-shadow:0 15px 38px rgba(30,35,45,.10)!important}
    .float-chip b{color:#1c2230!important}
    .orbit{border-color:rgba(73,103,232,.17)!important}

    .marquee{background:rgba(255,255,255,.42)!important;border-color:rgba(26,32,44,.10)!important}.marquee span{color:#687385!important}
    .section-index{color:#7b8492!important}.section-title small{color:#3157d5!important}.section-title h2{color:#171b23!important}.section-title p{color:#667085!important}

    .project{
      background:linear-gradient(145deg,rgba(255,253,248,.97),rgba(250,247,241,.94))!important;
      border-color:rgba(26,32,44,.12)!important;
      box-shadow:0 22px 60px rgba(34,40,52,.08)!important;
    }
    .project:before{background:radial-gradient(700px circle at 74% 48%,color-mix(in srgb,var(--accent) 10%,transparent),transparent 50%)!important}
    .project h3{color:#171b23!important}.project-copy>p{color:#5e6879!important}.project-no{color:var(--accent)!important}
    .status{background:color-mix(in srgb,var(--accent) 9%,white)!important;color:color-mix(in srgb,var(--accent) 74%,#1a2330)!important;border-color:color-mix(in srgb,var(--accent) 28%,#d9dce2)!important}
    .feature{background:rgba(255,255,255,.72)!important;border-color:rgba(26,32,44,.10)!important;color:#596476!important}.feature b{color:#202632!important}
    .project-links a{background:rgba(255,255,255,.72)!important;border-color:rgba(26,32,44,.12)!important;color:#202632!important}.project-links a:hover{background:color-mix(in srgb,var(--accent) 8%,white)!important}
    .project-visual{background:linear-gradient(135deg,rgba(255,255,255,.70),rgba(238,242,248,.62))!important;border-left-color:rgba(26,32,44,.10)!important}
    .visual-grid{opacity:.55!important}

    /* Product mockups can stay dark/colourful. They now sit on a bright card. */
    .browser{box-shadow:0 24px 58px rgba(30,36,48,.19)!important}
    .phone-shell{box-shadow:0 28px 60px rgba(30,36,48,.20)!important}
    .float-expiry,.river-card,.orbit-card,.ai-chip{box-shadow:0 16px 38px rgba(30,36,48,.18)!important}

    .gallery figure{background:#fffdf8!important;border-color:rgba(26,32,44,.11)!important;box-shadow:0 12px 30px rgba(34,40,52,.05)!important}.gallery img{background:#f1f3f6!important}.gallery figcaption{color:#626d7e!important;border-top-color:rgba(26,32,44,.09)!important}
    .process-card,.about-card,.contact-card{background:linear-gradient(145deg,#fffdf8,#f7f2e9)!important;border-color:rgba(26,32,44,.11)!important;box-shadow:0 14px 38px rgba(34,40,52,.055)!important}
    .process-card h3,.about-card .big,.contact-card h3{color:#171b23!important}.process-card p,.about-card p,.contact-card p{color:#616c7d!important}.skills span{background:rgba(255,255,255,.7)!important;color:#505b6c!important;border-color:rgba(26,32,44,.11)!important}.contact-email{color:#202632!important}
    .foot{border-top-color:rgba(26,32,44,.10)!important;color:#697486!important}

    @media(max-width:700px){
      body:before{background:linear-gradient(180deg,#fbf8f2 0%,#f5f0e7 52%,#faf7f1 100%)!important}
      .project{box-shadow:0 14px 34px rgba(34,40,52,.075)!important}
      .project-copy{background:rgba(255,253,248,.72)!important}
      .project-visual{border-left:0!important;border-top:1px solid rgba(26,32,44,.09)!important}
      .section-title p,.project-copy>p{color:#556071!important}
      .feature{color:#4f5b6c!important}
      .btn,.project-links a{background:#fff!important}
      .float-chip{background:rgba(255,253,248,.94)!important}
    }
  `;

  const apply=()=>{
    document.documentElement.dataset.motionReady='5';
    document.body?.classList.remove('portfolio-v3');

    let style=document.getElementById('portfolio-light-v5');
    if(!style){style=document.createElement('style');style.id='portfolio-light-v5';style.textContent=LIGHT_CSS;document.head.appendChild(style)}

    const theme=document.querySelector('meta[name="theme-color"]');
    if(theme) theme.setAttribute('content','#f7f3eb');

    // Remove any cached legacy enhancer artefacts without touching the current
    // page's own animations or product mockups.
    document.getElementById('portfolio-motion-v3-style')?.remove();
    document.querySelector('.motion-progress')?.remove();
    document.querySelectorAll('.cs-stack,.cs-pipeline,.hero-system,.cs-project-meta,.cs-preview-label,.portfolio-privacy-note,.lang-switch').forEach(el=>el.remove());

    if(document.querySelector('.project-list')){
      document.querySelectorAll('.navlinks a[href="#datemate"]').forEach(a=>a.remove());
      const meta=document.querySelector('meta[name="description"]');
      if(meta) meta.setAttribute('content','Pujan Chapagain — software developer portfolio featuring Team Tracker, FixCheck, DateMate, FloodSafe Nepal, LifeOS AI and Sathi AI.');
    }
  };

  apply();
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',apply,{once:true});

  const observer=new MutationObserver(()=>apply());
  observer.observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  setTimeout(()=>observer.disconnect(),4000);
})();