(()=>{
  const VERSION_URL='./build-version.txt';
  const STATUS_URL='./data/portfolio-status.json';
  const FLOODSAFE_BETA_APK='https://github.com/Pujan1234-hub/assigment/releases/download/floodsafe-v0.9.18-android-test/FloodSafe-Nepal-Beta-Test.apk';
  let current=null;
  let reloading=false;

  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;

  function applyRequestedFixes(){
    const heroLine=document.querySelector('h1 .thin');
    if(heroLine) heroLine.textContent='I build practical software for everyday needs — web, Android, AI and real-time products.';
    document.querySelectorAll('.project').forEach(project=>{project.style.contentVisibility='visible';});
    const betaLink=document.querySelector('#floodsafe .floodsafe-android-test a');
    if(betaLink) betaLink.href=FLOODSAFE_BETA_APK;
  }

  function addPolish(){
    applyRequestedFixes();
    if(document.getElementById('portfolio-polish')) return;
    const style=document.createElement('style');
    style.id='portfolio-polish';
    style.textContent=`
      :focus-visible{outline:2px solid var(--cyan);outline-offset:4px;border-radius:8px}
      .project{transition:transform .35s cubic-bezier(.2,.7,.2,1),border-color .35s,box-shadow .35s;content-visibility:visible!important}
      .project:hover{border-color:color-mix(in srgb,var(--accent) 32%,rgba(255,255,255,.10));box-shadow:0 34px 100px rgba(0,0,0,.30)}
      .project-copy>p{max-width:62ch}
      .project-sync{display:flex;align-items:center;gap:7px;width:max-content;max-width:100%;margin-top:10px;color:#718096;font:750 .66rem/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.045em}
      .project-sync:before{content:"";width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px color-mix(in srgb,var(--accent) 65%,transparent);flex:0 0 auto}
      .project-sync strong{color:#aeb9c8;font-weight:850}
      .floodsafe-android-test{margin-top:16px;padding:14px 15px;border:1px solid rgba(70,231,255,.22);border-radius:15px;background:linear-gradient(135deg,rgba(70,231,255,.075),rgba(110,140,255,.055));color:#9eacbd;font-size:.78rem;line-height:1.5}
      .floodsafe-android-test strong{display:block;color:#eafcff;font-size:.8rem;margin-bottom:3px}
      .floodsafe-android-test .android-only{display:inline-flex;align-items:center;margin-right:7px;color:#8ff4d0;font-weight:900;text-transform:uppercase;letter-spacing:.06em}
      .floodsafe-android-test a{display:inline-flex;align-items:center;justify-content:center;margin-top:10px;padding:10px 13px;border-radius:12px;background:linear-gradient(135deg,#33dffb,#6e8cff);color:#071019;font-weight:900;text-decoration:none;transition:transform .2s,filter .2s}
      .floodsafe-android-test a:hover{transform:translateY(-2px);filter:brightness(1.06)}
      .nav.scrolled{box-shadow:0 12px 36px rgba(0,0,0,.18)}
      @media(max-width:700px){.project-sync{font-size:.61rem}.project-copy>p{line-height:1.62}.floodsafe-android-test{font-size:.74rem}.floodsafe-android-test a{width:100%}}
      @media(prefers-reduced-motion:reduce){.project{transition:none!important}}
    `;
    document.head.appendChild(style);

    document.querySelectorAll('a[href^="#"]').forEach(a=>{
      a.addEventListener('click',()=>{
        const id=a.getAttribute('href');
        if(id&&id.length>1) history.replaceState(null,'',id);
      },{passive:true});
    });

    if(!reduced && 'IntersectionObserver' in window){
      const obs=new IntersectionObserver(entries=>entries.forEach(entry=>{
        if(entry.isIntersecting) entry.target.style.willChange='transform';
        else entry.target.style.willChange='auto';
      }),{rootMargin:'180px 0px'});
      document.querySelectorAll('.project').forEach(el=>obs.observe(el));
    }
  }

  function addFloodSafeAndroidTest(){
    const card=document.getElementById('floodsafe');
    if(!card) return;
    const existing=card.querySelector('.floodsafe-android-test');
    if(existing){
      const a=existing.querySelector('a');
      if(a) a.href=FLOODSAFE_BETA_APK;
      return;
    }
    const links=card.querySelector('.project-links');
    if(!links) return;
    const box=document.createElement('div');
    box.className='floodsafe-android-test';
    box.innerHTML='<strong><span class="android-only">Android only · Test build</span> FloodSafe Nepal native app</strong>Try the latest FloodSafe Nepal Android build on your device and help test the current version. The web app remains available above.<br><a href="'+FLOODSAFE_BETA_APK+'" target="_blank" rel="noopener noreferrer" download>Download Android APK ↓</a>';
    links.insertAdjacentElement('afterend',box);
  }

  async function getText(url){
    try{
      const r=await fetch(url+(url.includes('?')?'&':'?')+'t='+Date.now(),{cache:'no-store'});
      if(!r.ok) return null;
      return (await r.text()).trim();
    }catch{return null;}
  }

  async function getStatus(){
    try{
      const r=await fetch(STATUS_URL+'?t='+Date.now(),{cache:'no-store'});
      if(!r.ok) return null;
      return await r.json();
    }catch{return null;}
  }

  function prettyDate(value){
    if(!value) return '';
    const d=new Date(value);
    if(Number.isNaN(d.getTime())) return '';
    return new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric'}).format(d);
  }

  function upsertProjectSync(id,data){
    const card=document.getElementById(id);
    if(!card||!data) return;
    const status=card.querySelector('.status');
    if(id==='floodsafe' && status && data.version){
      status.innerHTML='<i></i> Web v'+data.version+' · latest mirror';
    }
    let note=card.querySelector('.project-sync');
    if(!note){
      note=document.createElement('div');
      note.className='project-sync';
      (status||card.querySelector('h3')).insertAdjacentElement('afterend',note);
    }
    const parts=[];
    if(data.updatedAt) parts.push('Updated '+prettyDate(data.updatedAt));
    if(data.source) parts.push(data.source);
    note.innerHTML=parts.length?'<strong>Repo sync</strong> · '+parts.join(' · '):'<strong>Repo sync enabled</strong>';
  }

  async function refreshProjectStatus(){
    const data=await getStatus();
    if(!data||!data.projects) return;
    Object.entries(data.projects).forEach(([id,value])=>upsertProjectSync(id,value));
    applyRequestedFixes();
    addFloodSafeAndroidTest();
  }

  async function check(){
    if(reloading) return;
    const v=await getText(VERSION_URL);
    if(v){
      if(current===null) current=v;
      else if(v!==current){
        reloading=true;
        const clean=location.pathname;
        sessionStorage.setItem('portfolio-clean-url','1');
        location.replace(clean+'?build='+encodeURIComponent(v)+location.hash);
        return;
      }
    }
    refreshProjectStatus();
  }

  if(sessionStorage.getItem('portfolio-clean-url')==='1'){
    sessionStorage.removeItem('portfolio-clean-url');
    history.replaceState(null,'',location.pathname+location.hash);
  }

  function load(src,id){
    if(document.getElementById(id)) return;
    const el=document.createElement('script');
    el.id=id;
    el.src=src;
    el.defer=true;
    document.head.appendChild(el);
  }

  addPolish();
  addFloodSafeAndroidTest();
  load('./portfolio-netsathi.js?v=20260920-netsathi-v2','pjio-netsathi-v2');
  load('./assets/portfolio/netsathi-photo-fix.js?v=20260921-real-photos-v1','pjio-netsathi-photo-fix-v1');
  load('./assets/portfolio/netsathi-real-gallery-compact.js?v=20260922-compact-v1','pjio-netsathi-compact-v1');
  refreshProjectStatus();
  setTimeout(()=>{applyRequestedFixes();addFloodSafeAndroidTest();},1200);
  window.addEventListener('focus',check);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden) check();});
  window.addEventListener('online',check);
  setInterval(check,60000);
  check();
})();

// Portfolio runtime sync enabled and published.

/* PJBUILTS contact form restore */
(()=>{
  if(document.getElementById('pjbuilts-contact-v3')) return;
  const el=document.createElement('script');
  el.id='pjbuilts-contact-v3';
  el.src='./portfolio-contact.js?v=20260929-contact-v3';
  el.defer=true;
  document.head.appendChild(el);
})();
