(()=>{
  const $=s=>document.querySelector(s);
  function validHost(raw){
    raw=(raw||'').trim();
    if(!raw||/\s/.test(raw))return null;
    if(!/^https?:\/\//i.test(raw))raw='https://'+raw;
    try{
      const h=new URL(raw).hostname.toLowerCase().replace(/\.$/,'');
      if(!h.includes('.')||h.length>253)return null;
      const p=h.split('.');
      if(p.some(x=>!x||x.length>63||!/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i.test(x)))return null;
      if(!/^[a-z]{2,63}$/i.test(p[p.length-1])&&!/^xn--/i.test(p[p.length-1]))return null;
      return h;
    }catch{return null}
  }
  function siteMode(){const s=$('#site');return !!(s&&!s.classList.contains('hide'))}
  function message(text,bad=false){
    const box=$('#site');if(!box)return;
    let e=$('#siteValidation');
    if(!e){e=document.createElement('div');e.id='siteValidation';e.style.cssText='margin-top:8px;font-size:11px;line-height:1.4';box.appendChild(e)}
    e.textContent=text;e.style.color=bad?'#ff8b90':'#8da5a1';
  }
  function markTargetSkipped(){
    const t=$('#t-target'),s=$('#s-target');
    if(t&&t.textContent!=='Not tested — domain did not resolve')t.textContent='Not tested — domain did not resolve';
    if(s){s.className='st warn';s.textContent='!'}
    const tr=$('#targetResponse');if(tr)tr.textContent='--';
  }
  function installStrictGuard(){
    const run=$('#run,#runBtn'),input=$('#url');
    if(input&&!input.dataset.strict){
      input.dataset.strict='1';
      input.addEventListener('input',()=>{
        const h=validHost(input.value);
        message(h?'Valid domain format: '+h:'Enter a real domain such as bbc.co.uk or example.com',!!input.value&&!h);
      });
    }
    if(run&&!run.dataset.strict){
      run.dataset.strict='1';
      run.addEventListener('click',e=>{
        if(!siteMode())return;
        const h=validHost(input?.value||'');
        if(!h){e.preventDefault();e.stopImmediatePropagation();message('Invalid website. Random text is not tested.',true);return}
        message('Checking '+h+' — DNS must resolve before any target result is trusted.');
      },true);
    }
    const dns=$('#t-dns'),target=$('#t-target');
    let dnsFailed=false;
    if(dns)new MutationObserver(()=>{
      if(!siteMode())return;
      const x=(dns.textContent||'').toLowerCase();
      dnsFailed=/not confirmed|does not exist|failed|could not|nxdomain/.test(x);
      if(dnsFailed){markTargetSkipped();message('DNS did not resolve this domain. Network speed/latency below describe your connection only.',true)}
    }).observe(dns,{childList:true,subtree:true,characterData:true});
    if(target)new MutationObserver(()=>{if(siteMode()&&dnsFailed&&/reachable|\d+\s*ms/i.test(target.textContent||''))markTargetSkipped()}).observe(target,{childList:true,subtree:true,characterData:true});
  }

  let wasOffline=!navigator.onLine,reconnectTimer=null;
  function hideInstall(){const installed=matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;const b=$('#install,#installBtn');if(b&&installed)b.style.display='none'}
  hideInstall();window.addEventListener('appinstalled',hideInstall);
  window.addEventListener('offline',()=>{wasOffline=true;clearTimeout(reconnectTimer)});
  window.addEventListener('online',()=>{
    if(!wasOffline)return;wasOffline=false;clearTimeout(reconnectTimer);
    const pill=$('#online span,#onlineText');if(pill)pill.textContent='Connection restored — rechecking automatically…';
    reconnectTimer=setTimeout(()=>{if(!navigator.onLine)return;const b=$('#run,#runBtn');if(b&&!b.disabled)b.click()},1500);
  });
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installStrictGuard);else installStrictGuard();
})();
