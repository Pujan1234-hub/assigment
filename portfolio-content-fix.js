(()=>{
  if(window.__pcPortfolioContentFixV5) return;
  window.__pcPortfolioContentFixV5=true;

  const CSS=`
    .browser{color:#eef4fb!important}.browserbar{color:#8f9bad!important}.metric span{color:#8e9bad!important}.metric strong{color:#f5f8fc!important}.metric strong em{color:var(--accent)!important}
    .browser .task{color:#b7c2cf!important;background:rgba(255,255,255,.035)!important;border-color:rgba(255,255,255,.09)!important}.browser .task b{color:var(--accent)!important}
    .river-card{background:rgba(7,12,19,.91)!important;color:#f4f7fb!important;border-color:rgba(255,255,255,.10)!important}.river-card small{color:#8f9db0!important}.river-card strong{color:#f7f9fc!important}.river-card .reading{color:var(--accent)!important}
    .river-card .task{color:#b7c2cf!important;background:rgba(255,255,255,.035)!important;border-color:rgba(255,255,255,.08)!important}.river-card .task b{color:var(--accent)!important}
    .scan-result{color:#aeb8c6!important}.scan-result b{color:var(--accent)!important}.os-core b{color:#f7f9fc!important}
    .orbit-card{background:rgba(12,18,29,.92)!important;color:#f5f8fc!important;border-color:rgba(255,255,255,.10)!important}.orbit-card small{color:#8c9aae!important}.orbit-card strong{color:#f7f9fc!important}.orbit-card strong.money{color:#52f2a8!important}.orbit-card strong.due{color:#ffad66!important}
    .float-expiry,.ai-chip{background:rgba(10,16,26,.92)!important;color:#8f9caf!important;border-color:rgba(255,255,255,.10)!important}.float-expiry b,.ai-chip b{color:#f7f9fc!important}
    .pjbuilds-signoff{display:inline-flex;align-items:center;gap:9px;padding:9px 13px;border:1px solid rgba(49,87,213,.18);border-radius:999px;background:linear-gradient(135deg,rgba(49,87,213,.08),rgba(123,85,214,.08));color:#26334b;font-weight:900;letter-spacing:.02em;box-shadow:0 10px 28px rgba(38,51,75,.06)}
    .pjbuilds-signoff:before{content:'PJB';display:grid;place-items:center;width:24px;height:24px;border-radius:8px;background:linear-gradient(135deg,#39c8dc,#7581f2);color:#071019;font-size:.62rem;font-weight:1000}
    #sathi .voice{display:none!important}#sathi .sathi-chat{position:absolute;left:7%;right:7%;bottom:7%;z-index:5;display:grid;gap:8px}#sathi .sathi-bubble{padding:11px 13px;border-radius:14px;font-size:.70rem;line-height:1.42;box-shadow:0 12px 28px rgba(30,36,48,.12)}#sathi .sathi-bubble.user{justify-self:end;max-width:78%;background:#20293a;color:#f4f7fb;border:1px solid rgba(255,255,255,.09)}#sathi .sathi-bubble.ai{justify-self:start;max-width:88%;background:rgba(255,253,248,.96);color:#273142;border:1px solid rgba(26,32,44,.12)}#sathi .sathi-bubble.ai b{color:#3157d5}
    #netsathi .ns-visual-wrap{height:auto!important;min-height:500px!important;padding:16px!important}
    #netsathi .ns-visual-wrap img{width:auto!important;max-width:92%!important;height:auto!important;max-height:460px!important;object-fit:contain!important;background:#07101a!important}
    @media(max-width:700px){.browser .metric strong{font-size:.96rem!important}.river-card strong{font-size:.82rem!important}#sathi .sathi-chat{left:4%;right:4%;bottom:5%}#sathi .sathi-bubble{font-size:.62rem;padding:9px 10px}#sathi .ai-stage{min-height:470px!important}.pjbuilds-signoff{margin-top:4px}#netsathi .ns-visual-wrap{min-height:420px!important}#netsathi .ns-visual-wrap img{max-height:390px!important;max-width:96%!important}#work .reveal{opacity:1!important;transform:none!important}}
  `;

  function ensureStyle(){let style=document.getElementById('portfolio-content-fix-v5');if(!style){style=document.createElement('style');style.id='portfolio-content-fix-v5';style.textContent=CSS;document.head.appendChild(style);}}

  function patchSathi(){
    const s=document.getElementById('sathi'); if(!s) return;
    const no=s.querySelector('.project-no'); if(no) no.textContent='06 · FloodSafe Nepal · Flood assistant';
    const status=s.querySelector('.status'); if(status) status.innerHTML='<i></i> Built into FloodSafe Nepal';
    const desc=s.querySelector('.project-copy > p'); if(desc) desc.textContent='Sathi AI is the Nepali flood assistant inside FloodSafe Nepal. It is designed to answer typed questions using FloodSafe river, station, rainfall and weather context — for example which nearby river is rising or when rain is expected to start and stop.';
    const features=[['01','Typed flood questions'],['02','River & station context'],['03','Rain timing & weather'],['04','FloodSafe data context']];
    s.querySelectorAll('.feature').forEach((el,i)=>{if(features[i]) el.innerHTML='<b>'+features[i][0]+'</b>'+features[i][1];});
    const links=s.querySelector('.project-links'); if(links) links.innerHTML='<a href="./floodsafe-nepal/">Open FloodSafe Nepal ↗</a><a href="#floodsafe">View FloodSafe project</a>';
    const a1=s.querySelector('.ai-chip.a1'),a2=s.querySelector('.ai-chip.a2'),a3=s.querySelector('.ai-chip.a3'); if(a1) a1.innerHTML='FLOOD AI<b>Nepali flood help</b>'; if(a2) a2.innerHTML='RIVER<b>Station context</b>'; if(a3) a3.innerHTML='WEATHER<b>Rain timing</b>';
    const stage=s.querySelector('.ai-stage'); if(stage && !stage.querySelector('.sathi-chat')){const chat=document.createElement('div');chat.className='sathi-chat';chat.innerHTML='<div class="sathi-bubble user">Which nearby river is rising?</div><div class="sathi-bubble ai"><b>Sathi</b> checks FloodSafe river + weather context for the answer.</div>';stage.appendChild(chat);}
  }

  function patchBrand(){
    document.querySelectorAll('a[href*="github.com"],a[href*="github.io"]').forEach(a=>a.remove());
    const codeLabel=document.querySelector('.dev-card .code-label'); if(codeLabel) codeLabel.textContent='PJBuilds';
    const meta=document.querySelector('meta[name="description"]'); if(meta) meta.setAttribute('content','PJBuilds — Pujan Chapagain software developer portfolio featuring Team Tracker, FixCheck, DateMate, FloodSafe Nepal, LifeOS AI, Sathi AI and NetSathi.');
    const foot=document.querySelector('footer .foot'); if(foot){const first=foot.querySelector(':scope > span');if(first) first.textContent='© 2026 Pujan Chapagain · Software Developer Portfolio';if(!foot.querySelector('.pjbuilds-signoff')){const mark=document.createElement('span');mark.className='pjbuilds-signoff';mark.textContent='PJBuilds';foot.appendChild(mark);}}
  }

  function patchPortfolioCopy(){
    const stats=document.querySelectorAll('.hero-stats .stat'); if(stats[0]){const strong=stats[0].querySelector('strong'),span=stats[0].querySelector('span');if(strong) strong.textContent='7';if(span) span.textContent='featured products';}
    const workCopy=document.querySelector('#work .section-title p'); if(workCopy) workCopy.textContent='Seven products, each presented around the experience it is designed to create. The motion supports the story without sacrificing readability.';
  }

  let initialNetSathiLinkHandled=false;
  function restoreNetSathiAnchor(){
    if(initialNetSathiLinkHandled || !/^#netsathi(?:-showcase)?$/.test(location.hash))return;
    const target=document.getElementById(location.hash.slice(1));
    if(!target)return;
    initialNetSathiLinkHandled=true;
    requestAnimationFrame(()=>target.scrollIntoView({block:'start',behavior:'auto'}));
  }

  function apply(){ensureStyle();patchSathi();patchBrand();patchPortfolioCopy();restoreNetSathiAnchor();}
  apply();
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',apply,{once:true});
  window.addEventListener('load',()=>{apply();setTimeout(apply,300);setTimeout(apply,1400);});
  setTimeout(apply,250);setTimeout(apply,1200);setTimeout(apply,3000);
})();