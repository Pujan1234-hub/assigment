(()=>{
  const VERSION_URL='./build-version.txt';
  let current=null;
  let reloading=false;

  async function getVersion(){
    try{
      const r=await fetch(VERSION_URL+'?t='+Date.now(),{cache:'no-store'});
      if(!r.ok) return null;
      return (await r.text()).trim();
    }catch{return null;}
  }

  async function check(){
    if(reloading) return;
    const v=await getVersion();
    if(!v) return;
    if(current===null){ current=v; return; }
    if(v!==current){
      reloading=true;
      const clean=location.pathname;
      sessionStorage.setItem('portfolio-clean-url','1');
      location.replace(clean+'?build='+encodeURIComponent(v));
    }
  }

  if(sessionStorage.getItem('portfolio-clean-url')==='1'){
    sessionStorage.removeItem('portfolio-clean-url');
    history.replaceState(null,'',location.pathname+location.hash);
  }

  window.addEventListener('focus',check);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden) check();});
  window.addEventListener('online',check);
  setInterval(check,15000);
  check();
})();

// Portfolio contact refresh: 2026-09-02
