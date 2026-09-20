(()=>{
  const VERSION_URL='./build-version.txt';
  const STATUS_URL='./data/portfolio-status.json';
  let current=null;
  let reloading=false;

  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;

  function addPolish(){
    if(document.getElementById('portfolio-polish')) return;
    const style=document.createElement('style');
    style.id='portfolio-polish';
    style.textContent=`
      :focus-visible{outline:2px solid var(--cyan);outline-offset:4px;border-radius:8px}
      .project{transition:transform .35s cubic-bezier(.2,.7,.2,1),border-color .35s,box-shadow .35s}
      .project:hover{border-color:color-mix(in srgb,var(--accent) 32%,rgba(255,255,255,.10));box-shadow:0 34px 100px rgba(0,0,0,.30)}
      .project-copy>p{max-width:62ch}
      .project-sync{display:flex;align-items:center;gap:7px;width:max-content;max-width:100%;margin-top:10px;color:#718096;font:750 .66rem/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.045em}
      .project-sync:before{content:"";width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px color-mix(in srgb,var(--accent) 65%,transparent);flex:0 0 auto}
      .project-sync strong{color:#aeb9c8;font-weight:850}
      .nav.scrolled{box-shadow:0 12px 36px rgba(0,0,0,.18)}
      @media(min-width:1051px){.project{content-visibility:auto;contain-intrinsic-size:580px}}
      @media(max-width:700px){.project-sync{font-size:.61rem}.project-copy>p{line-height:1.62}}
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
      status.innerHTML='<i></i> Android v'+data.version+' · field test';
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
  load('./portfolio-netsathi.js?v=20260920-netsathi-v1','pjbuilts-netsathi-v1');
  refreshProjectStatus();
  window.addEventListener('focus',check);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden) check();});
  window.addEventListener('online',check);
  setInterval(check,60000);
  check();
})();

// Portfolio runtime sync enabled and published.
