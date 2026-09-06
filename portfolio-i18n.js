(()=>{
  const EN='en', NP='np';
  const current=()=>localStorage.getItem('pc-portfolio-lang')===NP?NP:EN;
  let lang=current();
  let manifest=null;

  const style=document.createElement('style');
  style.textContent=`
    .lang-switch{display:inline-flex;align-items:center;gap:3px;padding:4px;border:1px solid var(--ink,#17191d);border-radius:999px;background:rgba(255,253,248,.82);box-shadow:2px 3px 0 rgba(23,25,29,.07);font-size:.72rem;font-weight:900;letter-spacing:.03em;white-space:nowrap}
    .lang-switch button{border:0;background:transparent;color:#68707b;border-radius:999px;padding:6px 9px;font:inherit;cursor:pointer;transition:.18s ease}
    .lang-switch button.active{background:var(--ink,#17191d);color:var(--paper,#f2eee6)}
    .lang-switch button:focus-visible{outline:2px solid var(--blue,#3157d5);outline-offset:2px}
    .portfolio-privacy-note{margin:14px 0 0;padding:9px 11px;border-left:3px solid var(--blue,#3157d5);background:rgba(49,87,213,.055);font-size:.77rem!important;line-height:1.55!important;color:#5d6570!important}
    .auto-projects{padding-top:78px}.auto-build-note{font-size:.8rem;color:#69717b;margin-top:10px;font-family:"SFMono-Regular",Consolas,monospace}
    .auto-project .project-main{grid-template-columns:1fr .95fr}.auto-system-card{border:1px solid var(--ink,#17191d);background:#11151b;color:#dfe7f3;padding:16px;min-height:240px;font-family:"SFMono-Regular",Consolas,monospace;box-shadow:5px 6px 0 rgba(23,25,29,.09)}
    .auto-system-card .bar{display:flex;justify-content:space-between;gap:12px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.12);font-size:.67rem;color:#98a5b7;text-transform:uppercase;letter-spacing:.08em}
    .auto-system-card .code{display:grid;gap:9px;padding-top:14px;font-size:.74rem}.auto-system-card .code span{display:flex;gap:10px}.auto-system-card .key{color:#6e8cff}.auto-system-card .ok{color:#66d6aa}.auto-system-card .muted{color:#a5b0bf}
    .auto-tech{display:flex;flex-wrap:wrap;gap:7px;margin-top:16px}.auto-tech span{border:1px solid #cac2b6;background:rgba(255,253,248,.78);padding:5px 7px;font-family:"SFMono-Regular",Consolas,monospace;font-size:.65rem;color:#525b67}
    @media(max-width:1050px){.lang-switch{margin-left:auto}}
    @media(max-width:700px){.navin{gap:10px}.lang-switch{font-size:.67rem}.lang-switch button{padding:6px 8px}.auto-project .project-main{grid-template-columns:1fr}}
  `;
  document.head.appendChild(style);

  const T={
    hero:{
      kicker:{en:'Software portfolio · 2026',np:'सफ्टवेयर पोर्टफोलियो · २०२६'},
      title:{en:'I build small software that fixes <em>real-world friction.</em>',np:'म वास्तविक जीवनका समस्या घटाउने <em>उपयोगी सफ्टवेयर बनाउँछु।</em>'},
      copy:{en:'Four products, four practical problems: coordinating people at work, diagnosing internet trouble, reducing avoidable waste, and making flood information more useful for people in Nepal. I design, build, test and keep improving each one hands-on.',np:'चार वटा प्रोडक्ट, चार फरक वास्तविक समस्या: कामको समन्वय, इन्टरनेट समस्या पहिचान, अनावश्यक फोहोर घटाउने र नेपालका मानिसका लागि बाढीसम्बन्धी जानकारी उपयोगी बनाउने। म प्रत्येक प्रोडक्टलाई आफैं डिजाइन, निर्माण, परीक्षण र निरन्तर सुधार गर्छु।'},
      board:{en:'On my desk right now',np:'अहिले म बनाइरहेको'},
      builds:{en:'Current builds',np:'हालका प्रोजेक्ट'}
    },
    nav:{work:['Work','काम'],team:['Team Tracker','टिम ट्र्याकर'],fix:['FixCheck','फिक्सचेक'],date:['DateMate','डेटमेट'],flood:['FloodSafe Nepal','फ्लडसेफ नेपाल'],about:['About','मेरो बारेमा'],contact:['Contact','सम्पर्क']},
    sections:{
      work:{small:['Selected work','मुख्य काम'],title:['Projects with a reason to exist.','काम लाग्ने उद्देश्य भएका प्रोजेक्टहरू।'],p:['Each build starts with a practical problem, then moves through system design, interface work, testing and repeated refinement.','हरेक प्रोजेक्ट वास्तविक समस्याबाट सुरु हुन्छ र त्यसपछि system design, interface, testing र पटक-पटक सुधार हुँदै अगाडि बढ्छ।']},
      about:{small:['About','मेरो बारेमा'],title:['How I approach software.','म सफ्टवेयर कसरी बनाउँछु।'],p:['A Computer Science mindset: break the problem down, model the flow, test the system and refine the interface.','Computer Science को सोच: समस्यालाई भागमा छुट्याउने, flow बनाउने, system परीक्षण गर्ने र interface सुधार्ने।']},
      contact:{small:['Contact','सम्पर्क'],title:["Let’s talk software.",'सफ्टवेयरबारे कुरा गरौं।'],p:['For software, product, prototype, or collaboration enquiries.','सफ्टवेयर, प्रोडक्ट, प्रोटोटाइप वा सहकार्यका लागि सम्पर्क गर्नुहोस्।']},
      new:{small:['Auto-detected builds','स्वतः भेटिएका नयाँ प्रोजेक्ट'],title:['New work enters here automatically.','नयाँ वास्तविक काम यहाँ आफैं थपिन्छ।'],p:['When a new real project is started in the repository, the portfolio can detect its project files and add a safe public build summary without editing this page by hand.','Repository मा नयाँ वास्तविक project सुरु भएपछि यसको project files भेटेर यो portfolio ले page हातैले edit नगरी सुरक्षित public summary आफैं थप्न सक्छ।']}
    },
    projects:{
      'team-tracker':{
        index:['Workflow system','कार्यप्रवाह प्रणाली'],status:['Working web app','चलिरहेको वेब एप'],
        desc:['A browser-based workflow product for live team status, task flow and a clear operations view. The public portfolio version uses sample data and keeps private operational records out of the site.','Live team status, task flow र स्पष्ट operations view का लागि बनाइएको browser-based workflow product। सार्वजनिक portfolio version मा नमुना data मात्र प्रयोग हुन्छ र निजी operational record समावेश हुँदैन।'],
        bullets:[['Live status and task progress in one place.','Live status र task progress एउटै ठाउँमा।'],['Clear assignment-to-completion workflow.','Task assign देखि complete सम्म स्पष्ट workflow।'],['Responsive browser experience for desktop and mobile.','Desktop र mobile दुवैमा responsive browser experience।'],['Public interactive build uses sample data only.','Public interactive build मा sample data मात्र।']],
        link:['Open product ↗','प्रोडक्ट खोल्नुहोस् ↗'],privacy:['Public interactive build · sample data only · no private operational records.','सार्वजनिक interactive build · नमुना data मात्र · कुनै निजी operational record समावेश छैन।']
      },
      fixcheck:{
        index:['Network diagnostics','नेटवर्क परीक्षण'],status:['In development','विकासमा'],
        desc:['A no-login connectivity diagnostic utility that turns network signals into a clear next step instead of a wall of technical information.','Login नचाहिने connectivity diagnostic utility जसले जटिल network signal लाई बुझ्न सजिलो next step मा बदल्छ।'],
        bullets:[['Checks likely device, connection and DNS problems.','Device, connection र DNS सम्बन्धी सम्भावित समस्या जाँच गर्छ।'],['Separates local connectivity from target-service issues.','Local connectivity र target service समस्या छुट्याउन मद्दत गर्छ।'],['Explains results in human-readable language.','Result लाई सजिलो भाषामा देखाउँछ।'],['Web/PWA direction with no account required first.','पहिलो प्रयोगमा account नचाहिने Web/PWA direction।']],
        link:['Open product ↗','प्रोडक्ट खोल्नुहोस् ↗']
      },
      datemate:{
        index:['Expiry reminders','म्याद सम्झाउने'],status:['Android app','एन्ड्रोइड एप'],
        desc:['An Android expiry-date reminder app for capturing important dates and receiving useful reminders before items expire.','महत्त्वपूर्ण expiry date राख्ने र म्याद सकिनुअघि उपयोगी reminder दिने Android app।'],
        bullets:[['Camera-assisted expiry-date capture.','Camera प्रयोग गरेर expiry date capture गर्ने।'],['Manual date entry when needed.','आवश्यक पर्दा manual date entry।'],['Reminder notifications before expiry.','Expiry अघि reminder notification।'],['Designed to reduce avoidable waste.','अनावश्यक waste घटाउन बनाइएको।']],
        link:['Project contact ↗','प्रोजेक्ट सम्पर्क ↗']
      },
      floodsafe:{
        index:['Flood awareness','बाढी जानकारी'],status:['Active development','सक्रिय विकास'],
        desc:['A Nepal-focused flood and river awareness platform built around local context, map-first information and frequently refreshed official river data.','नेपाल केन्द्रित बाढी तथा नदी जानकारी platform, जसले local context, map-first information र बारम्बार refresh हुने आधिकारिक river data मा ध्यान दिन्छ।'],
        bullets:[['Nepal-focused map and nearby river context.','नेपाल केन्द्रित map र नजिकका नदीको context।'],['Official river-station and warning data where available.','उपलब्ध ठाउँमा आधिकारिक river-station र warning data।'],['Visible update time and data-freshness cues.','Update time र data freshness स्पष्ट देखिने।'],['Safety information should be cross-checked with official emergency guidance.','सुरक्षा जानकारीलाई आधिकारिक emergency guidance सँग cross-check गर्नुपर्छ।']],
        link:['Open product ↗','प्रोडक्ट खोल्नुहोस् ↗']
      }
    },
    common:{
      emailLabel:['Email','इमेल'],location:['Based in the United Kingdom · Software products & working prototypes','United Kingdom मा आधारित · Software products र working prototypes'],
      contactCopy:['Building practical software, testing it properly, and improving it through real use.','काम लाग्ने software बनाउने, राम्रोसँग test गर्ने र वास्तविक प्रयोगबाट सुधार गर्ने।'],
      updated:['Last project update','अन्तिम project update'],detected:['Detected technology','भेटिएको technology'],active:['Active development','सक्रिय विकास'],details:['Build details','प्रोजेक्ट विवरण'],noPublicLink:['Public build link will appear when the project is ready.','Project तयार भएपछि public build link यहाँ देखिन्छ।']
    }
  };

  const txt=(pair,l=lang)=>Array.isArray(pair)?pair[l===NP?1:0]:pair;
  const q=(s,r=document)=>r.querySelector(s);
  const qa=(s,r=document)=>[...r.querySelectorAll(s)];
  const set=(el,pair)=>{if(el) el.textContent=txt(pair)};
  const setHtml=(el,pair)=>{if(el) el.innerHTML=txt(pair)};
  const setStatus=(el,pair)=>{if(!el)return; const dot=el.querySelector('.dot'); el.textContent=''; if(dot) el.appendChild(dot); el.append(document.createTextNode(' '+txt(pair)));};
  const numbered=(el,label)=>{if(!el)return; const raw=(el.textContent||'').trim(); const m=raw.match(/^([^/]+)\//); const prefix=m?m[1].trim():(raw.match(/^\d+/)||[''])[0]; el.textContent=(prefix?prefix+' / ':'')+txt(label);};

  function addLanguageSwitch(){
    if(q('.lang-switch')) return;
    const nav=q('.navin'); if(!nav) return;
    const box=document.createElement('div'); box.className='lang-switch'; box.setAttribute('role','group'); box.setAttribute('aria-label','Language');
    box.innerHTML='<button type="button" data-lang="en">EN</button><button type="button" data-lang="np">नेपाली</button>';
    const note=q('.open-note',nav);
    if(note) nav.insertBefore(box,note); else nav.appendChild(box);
    qa('button',box).forEach(b=>b.addEventListener('click',()=>changeLanguage(b.dataset.lang)));
  }

  function translateNav(){
    const map={"#work":T.nav.work,"#team-tracker":T.nav.team,"#fixcheck":T.nav.fix,"#datemate":T.nav.date,"#floodsafe":T.nav.flood,"#about":T.nav.about,"#contact":T.nav.contact};
    qa('.navlinks a').forEach(a=>{const pair=map[a.getAttribute('href')]; if(pair) set(a,pair)});
  }

  function translateHero(){
    set(q('.hero .kicker'),T.hero.kicker); setHtml(q('.hero h1'),T.hero.title); set(q('.hero-copy'),T.hero.copy);
    const board=q('.board-title'); if(board){set(q('b',board),T.hero.board);set(q('span',board),T.hero.builds)}
    qa('.hero-actions a').forEach(a=>{const href=a.getAttribute('href')||''; if(href.includes('#work')) a.textContent=lang===NP?'प्रोजेक्टहरू हेर्नुहोस्':'See the work'; if(href.includes('floodsafe-nepal')) a.textContent=lang===NP?'FloodSafe खोल्नुहोस् ↗':'Open FloodSafe ↗';});
    const ticketText={
      'Team Tracker':T.projects['team-tracker'],'FixCheck':T.projects.fixcheck,'DateMate':T.projects.datemate,'FloodSafe Nepal':T.projects.floodsafe
    };
    qa('.hero-aside .ticket').forEach(card=>{
      const h=q('h3',card); if(!h)return; const p=ticketText[(h.textContent||'').trim()]; if(!p)return;
      set(q('.tag',card),p.status); set(q('p',card),p.desc); set(q('a',card),p.link);
    });
  }

  function translateSectionHead(sectionId,data){
    const sec=q(sectionId); if(!sec)return; const head=q('.section-head',sec); if(!head)return;
    set(q('.section-title small',head),data.small); set(q('.section-title h2',head),data.title); set(q('.section-title p',head),data.p);
  }

  function translateProject(id,data){
    const sec=q('#'+id); if(!sec)return;
    numbered(q('.project-index',sec),data.index); setStatus(q('.project-status',sec),data.status);
    const p=q('.project-copy > p',sec); if(p) set(p,data.desc);
    const bullets=qa('.bullet span',sec); data.bullets.forEach((pair,i)=>{if(bullets[i]) set(bullets[i],pair)});
    qa('.side-links a',sec).forEach((a,i)=>{if(i===0) set(a,data.link)});
    if(id==='team-tracker'){
      let note=q('.portfolio-privacy-note',sec);
      if(!note){note=document.createElement('p');note.className='portfolio-privacy-note';const copy=q('.project-copy',sec);if(copy)copy.appendChild(note)}
      set(note,data.privacy);
    }
    const screenshots=q('.screens-head h4',sec); if(screenshots) screenshots.textContent=lang===NP?'स्क्रिनसटहरू':'Screenshots';
  }

  function translateAboutContact(){
    translateSectionHead('#about',T.sections.about); translateSectionHead('#contact',T.sections.contact);
    const contact=q('#contact'); if(contact){
      qa('.about-card strong',contact).forEach(el=>{if((el.textContent||'').trim().toLowerCase()==='email'||(el.textContent||'').trim()==='इमेल') set(el,T.common.emailLabel)});
      const paras=qa('.about-copy p',contact); if(paras[0]) set(paras[0],T.common.contactCopy); if(paras[1]) set(paras[1],T.common.location);
    }
    const about=q('#about'); if(about){
      const small=q('.about-copy .small',about); if(small) small.textContent=lang===NP?'म idea लाई system मा बदल्दा problem definition, flow, testing, debugging र usable interface मा ध्यान दिन्छु।':'I turn ideas into working systems by focusing on problem definition, flow, testing, debugging and a usable interface.';
    }
  }

  function translateRuleBand(){
    const items=qa('.rule-item');
    const pairs=[
      [['Hands-on build','आफैं निर्माण'],['Design → build → test → refine','Design → build → test → सुधार']],
      [['Computer Science','कम्प्युटर साइन्स'],['Systems, networking and software thinking','Systems, networking र software सोच']],
      [['Cross-platform','बहु-प्लेटफर्म'],['Web, PWA and mobile direction','Web, PWA र mobile direction']],
      [['Current work','हालको काम'],['Working products and active prototypes','चलिरहेका products र active prototypes']]
    ];
    items.forEach((el,i)=>{if(!pairs[i])return;set(q('strong',el),pairs[i][0]); const nodes=[...el.childNodes].filter(n=>n.nodeType===3&&n.nodeValue.trim()); if(nodes.length)nodes[nodes.length-1].nodeValue=' '+txt(pairs[i][1]);});
  }

  function translateTechnicalLayer(){
    qa('.cs-node').forEach(n=>{
      const s=(n.textContent||'').trim().toLowerCase();
      const map={input:['Input','इनपुट'],logic:['Logic','लजिक'],data:['Data','डाटा'],interface:['Interface','इन्टरफेस']};
      Object.entries(map).forEach(([key,pair])=>{if(s.includes(key)||s.includes(txt(pair,NP).toLowerCase())){const i=q('i',n);n.textContent='';if(i)n.appendChild(i);n.append(' '+txt(pair));}});
    });
    const foot=q('.cs-console-foot span'); if(foot) foot.textContent=lang===NP?'Computer Science · Software Systems · Build / Test / Refine':'Computer Science · Software Systems · Build / Test / Refine';
  }

  function applyLanguage(){
    document.documentElement.lang=lang===NP?'ne':'en';
    qa('.lang-switch button').forEach(b=>b.classList.toggle('active',b.dataset.lang===lang));
    translateNav();translateHero();translateRuleBand();
    translateSectionHead('#work',T.sections.work);
    translateProject('team-tracker',T.projects['team-tracker']);translateProject('fixcheck',T.projects.fixcheck);translateProject('datemate',T.projects.datemate);translateProject('floodsafe',T.projects.floodsafe);
    translateAboutContact();translateTechnicalLayer();translateAutoProjects();
    document.dispatchEvent(new CustomEvent('portfolio:language',{detail:{lang}}));
  }

  function changeLanguage(next){
    lang=next===NP?NP:EN; localStorage.setItem('pc-portfolio-lang',lang); applyLanguage();
  }

  function safeText(v){return String(v||'').replace(/[<>]/g,'').trim()}
  function translateAutoProjects(){
    qa('.auto-project').forEach(sec=>{
      const idx=q('.project-index',sec),status=q('.project-status',sec),desc=q('.project-copy > p',sec),updated=q('[data-auto-updated]',sec),det=q('[data-auto-detected]',sec),nolink=q('[data-auto-nolink]',sec);
      if(idx){const base=idx.dataset.number||'';idx.textContent=(base?base+' / ':'')+(lang===NP?'स्वतः भेटिएको प्रोजेक्ट':'Auto-detected project')}
      if(status) setStatus(status,T.common.active);
      if(desc) desc.textContent=lang===NP?(desc.dataset.np||desc.dataset.en):(desc.dataset.en||'');
      if(updated) updated.textContent=txt(T.common.updated)+': '+(updated.dataset.value||'—');
      if(det) det.textContent=txt(T.common.detected);
      if(nolink) set(nolink,T.common.noPublicLink);
    });
    const sec=q('#new-projects'); if(sec) translateSectionHead('#new-projects',T.sections.new);
  }

  function renderAutoProjects(){
    if(!manifest||!Array.isArray(manifest.projects))return;
    const extras=manifest.projects.filter(p=>p.auto===true);
    const old=q('#new-projects'); if(old)old.remove();
    if(!extras.length)return;
    const about=q('#about')||q('#contact')||document.querySelector('footer'); if(!about)return;
    const sec=document.createElement('section');sec.id='new-projects';sec.className='auto-projects';
    sec.innerHTML=`<div class="wrap"><div class="section-head"><div class="section-number">05</div><div class="section-title"><small></small><h2></h2><p></p><div class="auto-build-note">repo scan → project signature → safe public summary</div></div></div><div data-auto-list></div></div>`;
    about.parentNode.insertBefore(sec,about);
    const list=q('[data-auto-list]',sec);
    extras.forEach((p,i)=>{
      const title=safeText(p.title||'New Project');const en=safeText(p.description_en||`${title} is an active software project currently being built and tested.`);const np=safeText(p.description_np||`${title} अहिले विकास र परीक्षण भइरहेको software project हो।`);const tech=Array.isArray(p.tech)?p.tech.map(safeText).filter(Boolean):[];const updated=safeText(p.updated||'—');
      const article=document.createElement('article');article.className='project auto-project';article.id='auto-'+safeText(p.slug||('project-'+i)).toLowerCase().replace(/[^a-z0-9-]/g,'-');
      article.innerHTML=`<div class="project-side"><div><div class="project-index" data-number="${String(i+5).padStart(2,'0')}"></div><h3>${title}</h3><div class="project-status"><span class="dot"></span></div></div><div class="side-links"><span data-auto-nolink style="font-size:.78rem;color:#6b727b"></span></div></div><div class="project-main"><div class="project-copy"><p data-en="${en.replace(/"/g,'&quot;')}" data-np="${np.replace(/"/g,'&quot;')}"></p><div class="auto-tech">${tech.map(t=>`<span>${t}</span>`).join('')}</div><p data-auto-updated data-value="${updated.replace(/"/g,'&quot;')}" style="font-size:.76rem;margin-top:15px"></p></div><div class="auto-system-card"><div class="bar"><span>${title}</span><span class="ok">BUILD DETECTED</span></div><div class="code"><span><b class="key">project</b><i class="muted">${safeText(p.slug||title)}</i></span><span><b class="key">status</b><i class="ok">active-development</i></span><span><b class="key">source</b><i class="muted">repository project files</i></span><span><b class="key">public</b><i class="muted">safe summary only</i></span><span><b class="key" data-auto-detected>Detected technology</b><i class="muted">${tech.join(' · ')||'software project'}</i></span></div></div></div>`;
      list.appendChild(article);
    });
    translateAutoProjects();
    if(window.IntersectionObserver){qa('.auto-project',sec).forEach(el=>el.classList.add('motion-reveal','is-visible'))}
  }

  async function loadManifest(){
    try{const r=await fetch('./projects-manifest.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)return;manifest=await r.json();renderAutoProjects();}catch(_){/* portfolio remains fully usable without manifest */}
  }

  function boot(){
    addLanguageSwitch();applyLanguage();loadManifest();
    const observer=new MutationObserver(()=>{if(!q('.lang-switch'))addLanguageSwitch();applyLanguage()});
    const footer=document.querySelector('footer'); if(footer)observer.observe(footer.parentNode,{childList:true,subtree:false});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();