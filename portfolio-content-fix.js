(()=>{
  if(window.__pcPortfolioContentFixV1) return;
  window.__pcPortfolioContentFixV1=true;

  const CSS=`
    /* Keep the page light, but make intentionally dark product mockups readable. */
    .browser{color:#eef4fb!important}
    .browserbar{color:#8f9bad!important}
    .metric span{color:#8e9bad!important}
    .metric strong{color:#f5f8fc!important}
    .metric strong em{color:var(--accent)!important}
    .browser .task{color:#b7c2cf!important;background:rgba(255,255,255,.035)!important;border-color:rgba(255,255,255,.09)!important}
    .browser .task b{color:var(--accent)!important}

    .river-card{background:rgba(7,12,19,.91)!important;color:#f4f7fb!important;border-color:rgba(255,255,255,.10)!important}
    .river-card small{color:#8f9db0!important}
    .river-card strong{color:#f7f9fc!important}
    .river-card .reading{color:var(--accent)!important}
    .river-card .task{color:#b7c2cf!important;background:rgba(255,255,255,.035)!important;border-color:rgba(255,255,255,.08)!important}
    .river-card .task b{color:var(--accent)!important}

    .scan-result{color:#aeb8c6!important}
    .scan-result b{color:var(--accent)!important}

    .os-core b{color:#f7f9fc!important}
    .orbit-card{background:rgba(12,18,29,.92)!important;color:#f5f8fc!important;border-color:rgba(255,255,255,.10)!important}
    .orbit-card small{color:#8c9aae!important}
    .orbit-card strong{color:#f7f9fc!important}
    .orbit-card strong.money{color:#52f2a8!important}
    .orbit-card strong.due{color:#ffad66!important}

    .float-expiry,.ai-chip{background:rgba(10,16,26,.92)!important;color:#8f9caf!important;border-color:rgba(255,255,255,.10)!important}
    .float-expiry b,.ai-chip b{color:#f7f9fc!important}

    /* Sathi AI is a FloodSafe Nepal feature, not a separate education/voice app. */
    #sathi .voice{display:none!important}
    #sathi .sathi-chat{position:absolute;left:7%;right:7%;bottom:7%;z-index:5;display:grid;gap:8px}
    #sathi .sathi-bubble{padding:11px 13px;border-radius:14px;font-size:.70rem;line-height:1.42;box-shadow:0 12px 28px rgba(30,36,48,.12)}
    #sathi .sathi-bubble.user{justify-self:end;max-width:78%;background:#20293a;color:#f4f7fb;border:1px solid rgba(255,255,255,.09)}
    #sathi .sathi-bubble.ai{justify-self:start;max-width:88%;background:rgba(255,253,248,.96);color:#273142;border:1px solid rgba(26,32,44,.12)}
    #sathi .sathi-bubble.ai b{color:#3157d5}

    @media(max-width:700px){
      .browser .metric strong{font-size:.96rem!important}
      .river-card strong{font-size:.82rem!important}
      #sathi .sathi-chat{left:4%;right:4%;bottom:5%}
      #sathi .sathi-bubble{font-size:.62rem;padding:9px 10px}
      #sathi .ai-stage{min-height:470px!important}
    }
  `;

  function ensureStyle(){
    let style=document.getElementById('portfolio-content-fix-v1');
    if(!style){
      style=document.createElement('style');
      style.id='portfolio-content-fix-v1';
      style.textContent=CSS;
      document.head.appendChild(style);
    }
  }

  function patchSathi(){
    const s=document.getElementById('sathi');
    if(!s) return;

    const no=s.querySelector('.project-no');
    if(no) no.textContent='06 · FloodSafe Nepal · Flood assistant';

    const status=s.querySelector('.status');
    if(status) status.innerHTML='<i></i> Built into FloodSafe Nepal';

    const desc=s.querySelector('.project-copy > p');
    if(desc) desc.textContent='Sathi AI is the Nepali flood assistant inside FloodSafe Nepal. It is designed to answer typed questions using FloodSafe river, station, rainfall and weather context — for example which nearby river is rising or when rain is expected to start and stop.';

    const features=[
      ['01','Typed flood questions'],
      ['02','River & station context'],
      ['03','Rain timing & weather'],
      ['04','FloodSafe data context']
    ];
    s.querySelectorAll('.feature').forEach((el,i)=>{
      if(!features[i]) return;
      el.innerHTML='<b>'+features[i][0]+'</b>'+features[i][1];
    });

    const links=s.querySelector('.project-links');
    if(links) links.innerHTML='<a href="./floodsafe-nepal/">Open FloodSafe Nepal ↗</a><a href="#floodsafe">View FloodSafe project</a>';

    const a1=s.querySelector('.ai-chip.a1');
    const a2=s.querySelector('.ai-chip.a2');
    const a3=s.querySelector('.ai-chip.a3');
    if(a1) a1.innerHTML='FLOOD AI<b>Nepali flood help</b>';
    if(a2) a2.innerHTML='RIVER<b>Station context</b>';
    if(a3) a3.innerHTML='WEATHER<b>Rain timing</b>';

    const stage=s.querySelector('.ai-stage');
    if(stage && !stage.querySelector('.sathi-chat')){
      const chat=document.createElement('div');
      chat.className='sathi-chat';
      chat.innerHTML='<div class="sathi-bubble user">Which nearby river is rising?</div><div class="sathi-bubble ai"><b>Sathi</b> checks FloodSafe river + weather context for the answer.</div>';
      stage.appendChild(chat);
    }
  }

  function patchPortfolioCopy(){
    const meta=document.querySelector('meta[name="description"]');
    if(meta) meta.setAttribute('content','Pujan Chapagain — software developer portfolio featuring Team Tracker, FixCheck, DateMate, FloodSafe Nepal, LifeOS AI and Sathi AI inside FloodSafe Nepal.');

    const stats=document.querySelectorAll('.hero-stats .stat');
    if(stats[0]){
      const strong=stats[0].querySelector('strong');
      const span=stats[0].querySelector('span');
      if(strong) strong.textContent='5 + 1';
      if(span) span.textContent='products + AI feature';
    }

    const workCopy=document.querySelector('#work .section-title p');
    if(workCopy) workCopy.textContent='Five standalone products plus Sathi AI integrated inside FloodSafe Nepal — each presented around the experience it is designed to create. The motion supports the story without sacrificing readability.';
  }

  function apply(){
    ensureStyle();
    patchSathi();
    patchPortfolioCopy();
  }

  apply();
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',apply,{once:true});
  setTimeout(apply,250);
  setTimeout(apply,1200);
})();