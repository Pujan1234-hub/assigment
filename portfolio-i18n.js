(()=>{
  if(window.__pcPortfolioI18nV2) return;
  window.__pcPortfolioI18nV2=true;

  const EN='en', NP='np';
  let lang=localStorage.getItem('pc-portfolio-lang')===NP?NP:EN;

  const style=document.createElement('style');
  style.textContent=`
    .lang-switch{display:inline-flex;align-items:center;gap:3px;padding:4px;border:1px solid var(--ink,#17191d);border-radius:999px;background:rgba(255,253,248,.86);box-shadow:2px 3px 0 rgba(23,25,29,.07);font-size:.72rem;font-weight:900;letter-spacing:.03em;white-space:nowrap}
    .lang-switch button{border:0;background:transparent;color:#68707b;border-radius:999px;padding:6px 9px;font:inherit;cursor:pointer;transition:.18s ease}
    .lang-switch button.active{background:var(--ink,#17191d);color:var(--paper,#f2eee6)}
    .lang-switch button:focus-visible{outline:2px solid var(--blue,#3157d5);outline-offset:2px}
    .portfolio-privacy-note{margin:14px 0 0;padding:9px 11px;border-left:3px solid var(--blue,#3157d5);background:rgba(49,87,213,.055);font-size:.77rem!important;line-height:1.55!important;color:#5d6570!important}
    @media(max-width:1050px){.lang-switch{margin-left:auto}}
    @media(max-width:700px){.navin{gap:10px}.lang-switch{font-size:.67rem}.lang-switch button{padding:6px 8px}}
  `;
  document.head.appendChild(style);

  const T={
    hero:{
      kicker:['Software portfolio · 2026','सफ्टवेयर पोर्टफोलियो · २०२६'],
      title:['I build small software that fixes <em>real-world friction.</em>','म वास्तविक जीवनका समस्या घटाउने <em>उपयोगी सफ्टवेयर बनाउँछु।</em>'],
      copy:['Four products, four practical problems: coordinating people at work, diagnosing internet trouble, remembering important expiry dates, and making flood information more useful for people in Nepal. I design, build, test and keep improving each one hands-on.','चार वटा प्रोडक्ट, चार वास्तविक समस्या: कामको समन्वय, इन्टरनेट समस्या पहिचान, महत्त्वपूर्ण म्याद सम्झने र नेपालका मानिसका लागि बाढीसम्बन्धी जानकारी उपयोगी बनाउने। म प्रत्येक प्रोडक्टलाई आफैं डिजाइन, निर्माण, परीक्षण र निरन्तर सुधार गर्छु।'],
      board:['On my desk right now','अहिले म बनाइरहेको'],
      builds:['Current builds','हालका प्रोजेक्ट']
    },
    nav:{work:['Work','काम'],team:['Team Tracker','टिम ट्र्याकर'],fix:['FixCheck','फिक्सचेक'],date:['DateMate','डेटमेट'],flood:['FloodSafe Nepal','फ्लडसेफ नेपाल'],about:['About','मेरो बारेमा'],contact:['Contact','सम्पर्क']},
    sections:{
      work:{small:['Selected work','मुख्य काम'],title:['Projects with a reason to exist.','काम लाग्ने उद्देश्य भएका प्रोजेक्टहरू।'],p:['Each build starts with a practical problem, then moves through system design, interface work, testing and repeated refinement.','हरेक प्रोजेक्ट वास्तविक समस्याबाट सुरु हुन्छ र त्यसपछि system design, interface, testing र पटक-पटक सुधार हुँदै अगाडि बढ्छ।']},
      about:{small:['About','मेरो बारेमा'],title:['How I approach software.','म सफ्टवेयर कसरी बनाउँछु।'],p:['A Computer Science mindset: break the problem down, model the flow, test the system and refine the interface.','Computer Science को सोच: समस्यालाई भागमा छुट्याउने, flow बनाउने, system परीक्षण गर्ने र interface सुधार्ने।']},
      contact:{small:['Contact','सम्पर्क'],title:["Let’s talk software.",'सफ्टवेयरबारे कुरा गरौं।'],p:['For software, product, prototype, or collaboration enquiries.','सफ्टवेयर, प्रोडक्ट, प्रोटोटाइप वा सहकार्यका लागि सम्पर्क गर्नुहोस्।']}
    },
    projects:{
      team:{index:['Workflow system','कार्यप्रवाह प्रणाली'],status:['Working web app','चलिरहेको वेब एप'],desc:['A browser-based workflow product for live team status, task flow and a clear operations view. The public portfolio version uses sample data and keeps private operational records out of the site.','Live team status, task flow र स्पष्ट operations view का लागि बनाइएको browser-based workflow product। सार्वजनिक portfolio version मा नमुना data मात्र प्रयोग हुन्छ र निजी operational record समावेश हुँदैन।'],bullets:[['Live status and task progress in one place.','Live status र task progress एउटै ठाउँमा।'],['Clear assignment-to-completion workflow.','Task assign देखि complete सम्म स्पष्ट workflow।'],['Responsive browser experience for desktop and mobile.','Desktop र mobile दुवैमा responsive browser experience।'],['Public interactive build uses sample data only.','Public interactive build मा sample data मात्र।']],link:['Open product ↗','प्रोडक्ट खोल्नुहोस् ↗'],privacy:['Public interactive build · sample data only · no private operational records.','सार्वजनिक interactive build · नमुना data मात्र · कुनै निजी operational record समावेश छैन।']},
      fix:{index:['Network diagnostics','नेटवर्क परीक्षण'],status:['In development','विकासमा'],desc:['A no-login connectivity diagnostic utility that turns network signals into a clear next step instead of a wall of technical information.','Login नचाहिने connectivity diagnostic utility जसले जटिल network signal लाई बुझ्न सजिलो next step मा बदल्छ।'],bullets:[['Checks likely device, connection and DNS problems.','Device, connection र DNS सम्बन्धी सम्भावित समस्या जाँच गर्छ।'],['Separates local connectivity from target-service issues.','Local connectivity र target service समस्या छुट्याउन मद्दत गर्छ।'],['Explains results in human-readable language.','Result लाई सजिलो भाषामा देखाउँछ।'],['Web/PWA direction with no account required first.','पहिलो प्रयोगमा account नचाहिने Web/PWA direction।']],link:['Open product ↗','प्रोडक्ट खोल्नुहोस् ↗']},
      date:{index:['Expiry reminders','म्याद सम्झाउने'],status:['Android app','एन्ड्रोइड एप'],desc:['An Android expiry-date reminder app for capturing important dates and receiving useful reminders before items expire.','महत्त्वपूर्ण expiry date राख्ने र म्याद सकिनुअघि उपयोगी reminder दिने Android app।'],bullets:[['Camera-assisted expiry-date capture.','Camera प्रयोग गरेर expiry date capture गर्ने।'],['Manual date entry when needed.','आवश्यक पर्दा manual date entry।'],['Reminder notifications before expiry.','Expiry अघि reminder notification।'],['Simple mobile-first flow for everyday use.','दैनिक प्रयोगका लागि सरल mobile-first flow।']],link:['Project contact ↗','प्रोजेक्ट सम्पर्क ↗']},
      flood:{index:['Flood awareness','बाढी जानकारी'],status:['Active development','सक्रिय विकास'],desc:['A Nepal-focused flood and river awareness platform built around local context, map-first information and frequently refreshed official river data.','नेपाल केन्द्रित बाढी तथा नदी जानकारी platform, जसले local context, map-first information र बारम्बार refresh हुने आधिकारिक river data मा ध्यान दिन्छ।'],bullets:[['Nepal-focused map and nearby river context.','नेपाल केन्द्रित map र नजिकका नदीको context।'],['Official river-station and warning data where available.','उपलब्ध ठाउँमा आधिकारिक river-station र warning data।'],['Visible update time and data-freshness cues.','Update time र data freshness स्पष्ट देखिने।'],['Safety information should be cross-checked with official emergency guidance.','सुरक्षा जानकारीलाई आधिकारिक emergency guidance सँग cross-check गर्नुपर्छ।']],link:['Open product ↗','प्रोडक्ट खोल्नुहोस् ↗']}
    },
    common:{email:['Email','इमेल'],contact:['Building practical software, testing it properly, and improving it through real use.','काम लाग्ने software बनाउने, राम्रोसँग test गर्ने र वास्तविक प्रयोगबाट सुधार गर्ने।'],location:['Based in the United Kingdom · Software products & working prototypes','United Kingdom मा आधारित · Software products र working prototypes']}
  };

  const text=(pair,l=lang)=>{
    if(Array.isArray(pair)) return pair[l===NP?1:0] ?? pair[0] ?? '';
    if(pair && typeof pair==='object') return pair[l] ?? pair.en ?? pair.np ?? '';
    return pair==null?'':String(pair);
  };
  const q=(s,r=document)=>r.querySelector(s);
  const qa=(s,r=document)=>[...r.querySelectorAll(s)];
  const set=(el,pair)=>{if(el)el.textContent=text(pair)};
  const html=(el,pair)=>{if(el)el.innerHTML=text(pair)};
  const status=(el,pair)=>{if(!el)return;const dot=q('.dot',el);el.textContent='';if(dot)el.appendChild(dot);el.append(document.createTextNode(' '+text(pair)))};
  const numbered=(el,pair)=>{if(!el)return;const raw=(el.textContent||'').trim();const m=raw.match(/^([^/]+)\//);const prefix=m?m[1].trim():(raw.match(/^\d+/)||[''])[0];el.textContent=(prefix?prefix+' / ':'')+text(pair)};

  function removeFalseProjects(){
    q('#new-projects')?.remove();
    qa('.auto-project').forEach(el=>el.remove());
  }

  function addSwitch(){
    if(q('.lang-switch'))return;
    const nav=q('.navin');if(!nav)return;
    const box=document.createElement('div');box.className='lang-switch';box.setAttribute('role','group');box.setAttribute('aria-label','Language');
    box.innerHTML='<button type="button" data-lang="en">EN</button><button type="button" data-lang="np">नेपाली</button>';
    const note=q('.open-note',nav);if(note)nav.insertBefore(box,note);else nav.appendChild(box);
    qa('button',box).forEach(b=>b.addEventListener('click',()=>{lang=b.dataset.lang===NP?NP:EN;localStorage.setItem('pc-portfolio-lang',lang);apply()}));
  }

  function section(id,data){const sec=q(id);if(!sec)return;const head=q('.section-head',sec);if(!head)return;set(q('.section-title small',head),data.small);set(q('.section-title h2',head),data.title);set(q('.section-title p',head),data.p)}

  function project(id,data){
    const sec=q(id);if(!sec)return;
    numbered(q('.project-index',sec),data.index);status(q('.project-status',sec),data.status);set(q('.project-copy > p',sec),data.desc);
    const bs=qa('.bullet span',sec);data.bullets.forEach((p,i)=>{if(bs[i])set(bs[i],p)});
    const link=q('.side-links a',sec);if(link)set(link,data.link);
    if(id==='#team-tracker'){
      let note=q('.portfolio-privacy-note',sec);if(!note){note=document.createElement('p');note.className='portfolio-privacy-note';q('.project-copy',sec)?.appendChild(note)}set(note,data.privacy);
    }
    const sh=q('.screens-head h4',sec);if(sh)sh.textContent=lang===NP?'स्क्रिनसटहरू':'Screenshots';
  }

  function hero(){
    set(q('.hero .kicker'),T.hero.kicker);html(q('.hero h1'),T.hero.title);set(q('.hero-copy'),T.hero.copy);
    const board=q('.board-title');if(board){set(q('b',board),T.hero.board);set(q('span',board),T.hero.builds)}
    qa('.hero-actions a').forEach(a=>{const href=a.getAttribute('href')||'';if(href.includes('#work'))a.textContent=lang===NP?'प्रोजेक्टहरू हेर्नुहोस्':'See the work';if(href.includes('team-tracker'))a.textContent=lang===NP?'Team Tracker खोल्नुहोस्':'Open Team Tracker';if(href.includes('fixcheck'))a.textContent=lang===NP?'FixCheck खोल्नुहोस्':'Open FixCheck';if(href.includes('#datemate'))a.textContent=lang===NP?'DateMate हेर्नुहोस्':'See DateMate';if(href.includes('floodsafe-nepal'))a.textContent=lang===NP?'FloodSafe खोल्नुहोस् ↗':'Open FloodSafe ↗'});
    const map={'Team Tracker':T.projects.team,'FixCheck':T.projects.fix,'DateMate':T.projects.date,'FloodSafe Nepal':T.projects.flood};
    qa('.hero-aside .ticket').forEach(card=>{const h=q('h3',card);if(!h)return;const d=map[(h.textContent||'').trim()];if(!d)return;set(q('.tag',card),d.status);set(q('p',card),d.desc);set(q('a',card),d.link)});
  }

  function nav(){
    const map={'#work':T.nav.work,'#team-tracker':T.nav.team,'#fixcheck':T.nav.fix,'#datemate':T.nav.date,'#floodsafe':T.nav.flood,'#about':T.nav.about,'#contact':T.nav.contact};
    qa('.navlinks a').forEach(a=>{const p=map[a.getAttribute('href')];if(p)set(a,p)});
  }

  function extras(){
    const rules=qa('.rule-item');
    const pairs=[[['Hands-on build','आफैं निर्माण'],['Design → build → test → refine','Design → build → test → सुधार']],[['Computer Science','कम्प्युटर साइन्स'],['Systems, networking and software thinking','Systems, networking र software सोच']],[['Cross-platform','बहु-प्लेटफर्म'],['Web, PWA and mobile direction','Web, PWA र mobile direction']],[['Current work','हालको काम'],['Working products and active prototypes','चलिरहेका products र active prototypes']]];
    rules.forEach((el,i)=>{if(!pairs[i])return;set(q('strong',el),pairs[i][0]);const nodes=[...el.childNodes].filter(n=>n.nodeType===3&&n.nodeValue.trim());if(nodes.length)nodes[nodes.length-1].nodeValue=' '+text(pairs[i][1])});
    const nodeMap={input:['Input','इनपुट'],logic:['Logic','लजिक'],data:['Data','डाटा'],interface:['Interface','इन्टरफेस']};
    qa('.cs-node').forEach(n=>{const s=(n.textContent||'').trim().toLowerCase();for(const [key,pair] of Object.entries(nodeMap)){if(s.includes(key)||s.includes(text(pair,NP).toLowerCase())){const i=q('i',n);n.textContent='';if(i)n.appendChild(i);n.append(' '+text(pair));break}}});
  }

  function aboutContact(){
    section('#about',T.sections.about);section('#contact',T.sections.contact);
    const contact=q('#contact');if(contact){qa('.about-card strong',contact).forEach(el=>{if(['email','इमेल'].includes((el.textContent||'').trim().toLowerCase()))set(el,T.common.email)});const ps=qa('.about-copy p',contact);if(ps[0])set(ps[0],T.common.contact);if(ps[1])set(ps[1],T.common.location)}
    const small=q('#about .about-copy .small');if(small)small.textContent=lang===NP?'म idea लाई working system मा बदल्दा problem definition, flow, testing, debugging र usable interface मा ध्यान दिन्छु।':'I turn ideas into working systems by focusing on problem definition, flow, testing, debugging and a usable interface.';
  }

  function apply(){
    removeFalseProjects();
    document.documentElement.lang=lang===NP?'ne':'en';qa('.lang-switch button').forEach(b=>b.classList.toggle('active',b.dataset.lang===lang));
    nav();hero();section('#work',T.sections.work);project('#team-tracker',T.projects.team);project('#fixcheck',T.projects.fix);project('#datemate',T.projects.date);project('#floodsafe',T.projects.flood);aboutContact();extras();
    document.dispatchEvent(new CustomEvent('portfolio:language',{detail:{lang}}));
  }

  function boot(){addSwitch();apply();setTimeout(()=>{addSwitch();apply()},80)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();