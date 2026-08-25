(()=>{
  const $=s=>document.querySelector(s);
  function validPublicHost(host){
    host=(host||'').toLowerCase().replace(/\.$/,'');
    if(!host||host.length>253)return false;
    const ipv4=/^(?:\d{1,3}\.){3}\d{1,3}$/.test(host);
    if(ipv4)return host.split('.').every(x=>+x>=0&&+x<=255);
    if(!host.includes('.'))return false;
    const parts=host.split('.');
    if(parts.length<2)return false;
    if(parts.some(x=>!x||x.length>63||!(/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i.test(x))))return false;
    const tld=parts[parts.length-1];
    return /^[a-z]{2,63}$/i.test(tld)||/^xn--/i.test(tld);
  }
  function hostFromInput(raw){
    raw=(raw||'').trim();
    if(!raw||/\s/.test(raw))return null;
    let v=raw;
    if(!/^https?:\/\//i.test(v))v='https://'+v;
    try{const u=new URL(v);return validPublicHost(u.hostname)?u.hostname.toLowerCase():null}catch{return null}
  }
  function siteMode(){const e=$('#site');return !!(e&&!e.classList.contains('hide'))}
  function ensureValidation(){
    const site=$('#site'); if(!site)return null;
    let e=$('#siteValidation');
    if(!e){e=document.createElement('div');e.id='siteValidation';e.style.cssText='margin-top:8px;font-size:11px;line-height:1.4;color:#8da5a1';site.appendChild(e)}
    return e;
  }
  function showValidation(msg,bad=false){const e=ensureValidation();if(!e)return;e.textContent=msg;e.style.color=bad?'#ff8b90':'#8da5a1'}
  function connectionInfo(){
    const c=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
    let type=(c&&c.type)||'',label='Current connection',known=false;
    if(type==='wifi'){label='Wi‑Fi';known=true}
    else if(type==='cellular'){label='Mobile data';known=true}
    else if(type==='ethernet'){label='Ethernet';known=true}
    else if(type){label=type.charAt(0).toUpperCase()+type.slice(1);known=true}
    return{label,known};
  }
  function ensureLinkPill(){
    if($('#linkPill'))return;
    const online=$('#online');if(!online)return;
    const p=document.createElement('div');p.id='linkPill';p.style.cssText='display:inline-flex;gap:7px;align-items:center;margin:8px 0 0 7px;padding:8px 11px;border:1px solid #ffffff14;border-radius:999px;color:#8da5a1;font-size:11px;vertical-align:top';
    p.innerHTML='<span style="width:8px;height:8px;border-radius:50%;background:#73f5bd;box-shadow:0 0 12px #73f5bd"></span><span id="linkText">Current connection · speed not tested</span>';
    online.insertAdjacentElement('afterend',p);
  }
  function updateLink(speed=null){
    ensureLinkPill();const e=$('#linkText');if(!e)return;
    const x=connectionInfo();let text=x.label;
    if(speed!=null)text+=' · '+speed+' Mbps';
    else text+=' · speed not tested';
    e.textContent=text;
    e.title=x.known?'Connection type exposed by this browser':'Browser does not expose whether this is Wi‑Fi or mobile data; FixCheck will not guess.';
  }
  function relabel(){
    const checks=[...document.querySelectorAll('.check')];
    checks.forEach(row=>{const b=row.querySelector('b');if(!b)return;if(b.textContent.trim()==='Quality')b.textContent='Network quality';if(b.textContent.trim()==='Speed')b.textContent='Current connection speed';if(b.textContent.trim()==='Target')b.textContent='Website / service'});
    const metrics=[...document.querySelectorAll('.metric')];
    metrics.forEach(m=>{const s=m.querySelector('span');if(!s)return;const t=s.textContent.trim().toLowerCase();if(t==='latency')s.textContent='NETWORK LATENCY';if(t==='jitter')s.textContent='NETWORK JITTER';if(t==='download')s.textContent='CURRENT DOWNLOAD'});
    const box=document.querySelector('.metrics');
    if(box&&!$('#targetResponse')){const m=document.createElement('div');m.className='metric';m.innerHTML='<span>TARGET RESPONSE</span><b id="targetResponse">--</b><em>only when target is confirmed</em>';box.appendChild(m)}
    if(box&&!$('#connectionType')){const m=document.createElement('div');m.className='metric';m.innerHTML='<span>CURRENT LINK</span><b id="connectionType">--</b><em id="connectionTypeNote">browser-visible connection info</em>';box.appendChild(m)}
    const ci=connectionInfo();const ct=$('#connectionType'),cn=$('#connectionTypeNote');if(ct)ct.textContent=ci.label;if(cn)cn.textContent=ci.known?'Physical link type exposed by browser':'Wi‑Fi/mobile type hidden by browser — not guessed';
  }
  function updateTargetResponse(){
    const t=$('#t-target'),out=$('#targetResponse');if(!t||!out)return;
    const txt=t.textContent||'';const m=txt.match(/(?:reachable|response)[^0-9]*(\d+)\s*ms/i);out.textContent=m?m[1]+' ms':'--';
  }
  function updateSpeed(){
    const t=$('#t-speed');if(!t)return;const m=(t.textContent||'').match(/([0-9]+(?:\.[0-9]+)?)\s*Mbps/i);updateLink(m?Number(m[1]):null);
  }
  function installGuards(){
    relabel();ensureLinkPill();updateLink();
    showValidation('Enter a real public domain such as example.com. Random text is rejected before any test starts.');
    const run=$('#run');
    if(run&&!run.dataset.trustGuard){
      run.dataset.trustGuard='1';
      run.addEventListener('click',e=>{
        if(!siteMode())return;
        const host=hostFromInput($('#url')?.value||'');
        if(!host){e.preventDefault();e.stopImmediatePropagation();showValidation('Not a valid public website. Use something like bbc.co.uk or example.com.',true);try{tone(220,.1)}catch{};return}
        showValidation('Valid domain format: '+host+'. DNS and target reachability will be checked separately.');
      },true);
    }
    const input=$('#url');if(input&&!input.dataset.trustGuard){input.dataset.trustGuard='1';input.addEventListener('input',()=>{const h=hostFromInput(input.value);showValidation(h?'Valid domain format: '+h+'.':'Enter a real public domain such as example.com.',!!input.value&&!h)})}
    const target=$('#t-target'),speed=$('#t-speed'),dns=$('#t-dns');
    if(target)new MutationObserver(updateTargetResponse).observe(target,{childList:true,characterData:true,subtree:true});
    if(speed)new MutationObserver(updateSpeed).observe(speed,{childList:true,characterData:true,subtree:true});
    if(dns)new MutationObserver(()=>{if(!siteMode())return;const txt=dns.textContent||'';if(/does not exist|not confirmed|could not/i.test(txt))showValidation('DNS did not confirm this website. Any latency/jitter shown below is your network quality — not a ping to this website.',true)}).observe(dns,{childList:true,characterData:true,subtree:true});
    const c=navigator.connection||navigator.mozConnection||navigator.webkitConnection;if(c&&c.addEventListener)c.addEventListener('change',()=>{relabel();updateSpeed()});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installGuards);else installGuards();
})();
