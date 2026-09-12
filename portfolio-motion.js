(()=>{
  /*
   * Portfolio compatibility shim — v4.
   * The current index.html already owns all premium motion, dark-theme styling,
   * reveal effects, mobile layouts and project animations. The previous v3
   * enhancer injected an old light theme after page load, which caused dark
   * text tokens and project cards to lose contrast on mobile/Facebook browsers.
   */
  if(window.__pcPortfolioMotionV4) return;
  window.__pcPortfolioMotionV4=true;

  // Prevent the old i18n bundle from rewriting the new hero/project DOM with
  // legacy light-theme content. A new bilingual pass can be added specifically
  // for the v4 layout without touching the visual system.
  window.__pcPortfolioI18nV6=true;

  const clean=()=>{
    document.documentElement.dataset.motionReady='4';
    document.body?.classList.remove('portfolio-v3');

    // Remove any legacy enhancer artefacts if a cached script executed first.
    document.getElementById('portfolio-motion-v3-style')?.remove();
    document.querySelector('.motion-progress')?.remove();
    document.querySelectorAll('.cs-stack,.cs-pipeline,.hero-system,.cs-project-meta,.cs-preview-label,.portfolio-privacy-note,.lang-switch').forEach(el=>el.remove());

    // portfolio-floodsafe.js runs before this shim in the Pages bundle and can
    // add a legacy DateMate nav item. Keep the v4 navigation intentionally clean.
    if(document.querySelector('.project-list')){
      document.querySelectorAll('.navlinks a[href="#datemate"]').forEach(a=>a.remove());
      const meta=document.querySelector('meta[name="description"]');
      if(meta) meta.setAttribute('content','Pujan Chapagain — software developer portfolio featuring Team Tracker, FixCheck, DateMate, FloodSafe Nepal, LifeOS AI and Sathi AI.');
    }
  };

  clean();
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',clean,{once:true});

  // Defensive cleanup for cached Facebook/in-app browser sessions that may
  // briefly re-inject the old enhancer style during script evaluation.
  const observer=new MutationObserver(()=>clean());
  observer.observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  setTimeout(()=>observer.disconnect(),3500);
})();
