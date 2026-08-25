(()=>{
  const $=s=>document.querySelector(s);
  let dnsFailed=false;

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

  function siteMode(){
    const old=$('#site');
    if(old)return !old.classList.contains('hide');
    const modern=$('#sitePanel');
    return !!(modern&&!modern.classList.contains('hidden'));
  }

  function inputEl(){return $('#url')||$('#customUrl')}
  function runEl(){return $('#run')||$('#runBtn')}
  function dnsTextEl(){return $('#t-dns')||document.querySelector('[data-txt="dns"]')}
  function targetTextEl(){return $('#t-target')||document.querySelector('[data-txt="target"]')}
  function targetStatusEl(){return $('#s-target')||document.querySelector('[data-st="target"]')}

  function ensureValidation(){
    const site=$('#site')||$('#sitePanel'); if(!site)return null;
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
    const online=$('#online')||$('#onlinePill');if(!online)return;
    const p=document.createElement('div');p.id='linkPill';p.style.cssText='display:inline-flex;gap:7px;align-items:center;margin:8px 0 0 7px;padding:8px 11px;border:1px solid #ffffff14;border-radius:999px;color:#8da5a1;font-size:11px;vertical-align:top';
    p.innerHTML='<span style="width:8px;height:8px;border-radius:50%;background:#73f5bd;box-shadow:0 0 12px #73f5bd"></span><span id="linkText">Current connection · speed not tested</span>';
    online.insertAdjacentElement('afterend',p);
  }

  function updateLink(speed=null){
    ensureLinkPill();const e=$('#linkText');if(!e)return;
    const x=connectionInfo();let text=x.label;
    text+=speed!=null?' · '+speed+' Mbps':' · speed not tested';
    e.textContent=text;
    e.title=x.known?'Connection type exposed by this browser':'Browser does not expose whether this is Wi‑Fi or mobile data; FixCheck does not guess.';
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

  function forceInvalidTarget(){
    if(!dnsFailed||!siteMode())return;
    const t=targetTextEl(),s=targetStatusEl();
    if(t&&t.textContent!=='Target result ignored — DNS did not resolve')t.textContent='Target result ignored — DNS did not resolve';
    if(s){s.className=(s.id?'st fail':'st fail');s.textContent='×'}
    const out=$('#targetResponse');if(out)out.textContent='--';
  }

  function updateTargetResponse(){
    const t=targetTextEl(),out=$('#targetResponse');if(!t||!out)return;
    if(dnsFailed){out.textContent='--';return}
    const txt=t.textContent||'';const m=txt.match(/(?:reachable|response)[^0-9]*(\d+)\s*ms/i);out.textContent=m?m[1]+' ms':'--';
  }

  function updateSpeed(){
    const t=$('#t-speed')||document.querySelector('[data-txt="speed"]');if(!t)return;const m=(t.textContent||'').match(/([0-9]+(?:\.[0-9]+)?)\s*Mbps/i);updateLink(m?Number(m[1]):null);
  }

  function installGuards(){
    relabel();ensureLinkPill();updateLink();
    showValidation('Enter a real public domain such as example.com. Random text is rejected before any test starts.');

    const run=runEl();
    if(run&&!run.dataset.trustGuard){
      run.dataset.trustGuard='1';
      run.addEventListener('click',e=>{
        dnsFailed=false;
        if(!siteMode())return;
        const input=inputEl();const host=hostFromInput(input?.value||'');
        if(!host){
          e.preventDefault();e.stopImmediatePropagation();
          showValidation('Not a valid public website. Use something like bbc.co.uk or example.com.',true);
          try{if(typeof window.tone==='function')window.tone(220,.1)}catch{}
          return;
        }
        showValidation('Valid domain format: '+host+'. DNS must resolve before any target response is trusted.');
      },true);
    }

    const input=inputEl();
    if(input&&!input.dataset.trustGuard){input.dataset.trustGuard='1';input.addEventListener('input',()=>{const h=hostFromInput(input.value);showValidation(h?'Valid domain format: '+h+'.':input.value?'Not a valid public website. Use something like bbc.co.uk.':'Enter a real public domain such as example.com.',!!input.value&&!h)})}

    const target=targetTextEl(),speed=$('#t-speed')||document.querySelector('[data-txt="speed"]'),dns=dnsTextEl();
    if(target)new MutationObserver(()=>{if(dnsFailed)queueMicrotask(forceInvalidTarget);else updateTargetResponse()}).observe(target,{childList:true,characterData:true,subtree:true});
    if(speed)new MutationObserver(updateSpeed).observe(speed,{childList:true,characterData:true,subtree:true});
    if(dns)new MutationObserver(()=>{
      if(!siteMode())return;
      const txt=dns.textContent||'';
      dnsFailed=/does not exist|not confirmed|could not|failed/i.test(txt);
      if(dnsFailed){
        showValidation('DNS did not confirm this website. Target response is ignored. Latency/jitter below describe your network, not this website.',true);
        queueMicrotask(forceInvalidTarget);
      }else if(/resolved/i.test(txt)){
        dnsFailed=false;
        const h=hostFromInput(inputEl()?.value||'');if(h)showValidation('DNS confirmed '+h+'. Target response can now be evaluated.');
      }
    }).observe(dns,{childList:true,characterData:true,subtree:true});

    const c=navigator.connection||navigator.mozConnection||navigator.webkitConnection;if(c&&c.addEventListener)c.addEventListener('change',()=>{relabel();updateSpeed()});
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installGuards);else installGuards();
})();
