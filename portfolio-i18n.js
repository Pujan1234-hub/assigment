(()=>{
  if(window.__pcPortfolioI18nV3) return;
  window.__pcPortfolioI18nV3=true;

  const EN='en', NP='np';
  let lang=localStorage.getItem('pc-portfolio-lang')===NP?NP:EN;
  const q=(s,r=document)=>r.querySelector(s);
  const qa=(s,r=document)=>[...r.querySelectorAll(s)];
  const pick=p=>Array.isArray(p)?(p[lang===NP?1:0]??p[0]??''):(p==null?'':String(p));
  const set=(el,p)=>{if(el) el.textContent=pick(p)};
  const html=(el,p)=>{if(el) el.innerHTML=pick(p)};

  const style=document.createElement('style');
  style.textContent=`
    .lang-switch{display:inline-flex;align-items:center;gap:3px;padding:4px;border:1px solid var(--ink,#17191d);border-radius:999px;background:rgba(255,253,248,.9);box-shadow:2px 3px 0 rgba(23,25,29,.07);font-size:.72rem;font-weight:900;white-space:nowrap}
    .lang-switch button{border:0;background:transparent;color:#68707b;border-radius:999px;padding:6px 9px;font:inherit;cursor:pointer}
    .lang-switch button.active{background:var(--ink,#17191d);color:var(--paper,#f2eee6)}
    .portfolio-privacy-note{margin:14px 0 0;padding:9px 11px;border-left:3px solid var(--blue,#3157d5);background:rgba(49,87,213,.055);font-size:.77rem!important;line-height:1.55!important;color:#5d6570!important}
    @media(max-width:1050px){.lang-switch{margin-left:auto}}
    @media(max-width:700px){.lang-switch{font-size:.67rem}.lang-switch button{padding:6px 8px}}
  `;
  document.head.appendChild(style);

  const T={
    hero:{
      kicker:['Software portfolio · 2026','सफ्टवेयर पोर्टफोलियो · २०२६'],
      title:['I build small software that fixes <em>real-world friction.</em>','म वास्तविक जीवनका समस्या घटाउने <em>उपयोगी सफ्टवेयर बनाउँछु।</em>'],
      copy:['Four products, four practical problems: coordinating work, diagnosing internet trouble, remembering important expiry dates, and making flood information more useful for people in Nepal. I design, build, test and keep improving each one hands-on.','चार प्रोजेक्ट, चार वास्तविक समस्या: काम समन्वय गर्ने, इन्टरनेट समस्या बुझ्ने, महत्त्वपूर्ण म्याद सम्झने र नेपालमा बाढीसम्बन्धी जानकारी अझ उपयोगी बनाउने। म प्रत्येकलाई आफैं डिजाइन, निर्माण, परीक्षण र सुधार गर्दै लैजान्छु।'],
      board:['On my desk right now','अहिले म बनाइरहेको'],
      builds:['Current builds','हालका प्रोजेक्ट']
    },
    nav:{work:['Work','काम'],team:['Team Tracker','टिम ट्र्याकर'],fix:['FixCheck','फिक्सचेक'],date:['DateMate','डेटमेट'],flood:['FloodSafe Nepal','फ्लडसेफ नेपाल'],about:['About','मेरो बारेमा'],contact:['Contact','सम्पर्क']},
    work:{small:['Selected work','मुख्य काम'],title:['Projects with a reason to exist.','काम लाग्ने उद्देश्य भएका प्रोजेक्टहरू।'],copy:['Each build starts with a practical problem, then moves through system design, interface work, testing and repeated refinement.','हरेक प्रोजेक्ट वास्तविक समस्याबाट सुरु हुन्छ, त्यसपछि system design, interface, testing र पटक-पटक सुधार हुँदै अगाडि बढ्छ।']},
    about:{small:['About','मेरो बारेमा'],title:['How I approach software.','म सफ्टवेयर कसरी बनाउँछु।'],copy:['A Computer Science mindset: break the problem down, model the flow, test the system and refine the interface.','Computer Science को सोच: समस्यालाई भागमा छुट्याउने, flow बनाउने, system परीक्षण गर्ने र interface सुधार्ने।']},
    contact:{small:['Contact','सम्पर्क'],title:["Let’s talk software.",'सफ्टवेयरबारे कुरा गरौं।'],copy:['For software, product, prototype, or collaboration enquiries.','सफ्टवेयर, प्रोडक्ट, प्रोटोटाइप वा सहकार्यका लागि सम्पर्क गर्नुहोस्।']},
    projects:{
      team:{status:['Working web app','चलिरहेको वेब एप'],desc:['A browser-based workflow product for live team status, task flow and a clear operations view. The public portfolio version uses sample data only.','Live team status, task flow र स्पष्ट operations view का लागि बनाइएको browser-based workflow product। सार्वजनिक portfolio version मा sample data मात्र प्रयोग हुन्छ।'],privacy:['Public interactive build · sample data only · no private operational records.','सार्वजनिक interactive build · sample data मात्र · कुनै निजी operational record छैन।']},
      fix:{status:['In development','विकासमा'],desc:['A no-login connectivity diagnostic utility that turns network signals into a clear next step instead of a wall of technical information.','Login नचाहिने connectivity diagnostic utility जसले जटिल network signal लाई बुझ्न सजिलो next step मा बदल्छ।']},
      date:{status:['Active development','सक्रिय विकास'],desc:['An expiry-date reminder app for capturing important dates and receiving useful reminders before items expire.','महत्त्वपूर्ण expiry date राख्ने र म्याद सकिनुअघि उपयोगी reminder दिने app।']},
      flood:{status:['Active development','सक्रिय विकास'],desc:['A Nepal-focused flood and river awareness platform built around local context, map-first information and frequently refreshed official river data.','नेपाल केन्द्रित बाढी तथा नदी जानकारी platform, जसले local context, map-first information र बारम्बार refresh हुने आधिकारिक river data मा ध्यान दिन्छ।']}
    }
  };

  // Remove anything previously inferred from generic folders/platforms.
  function removeFalseProjects(){
    q('#new-projects')?.remove();
    q('#sathi')?.remove();
    qa('.auto-project').forEach(el=>el.remove());
    qa('.project').forEach(el=>{
      const title=(q('.project-side h3',el)?.textContent||'').trim().toLowerCase();
      const index=(q('.project-index',el)?.textContent||'').trim().toLowerCase();
      const bogus=['site','ios app','windows app','android app','web app'];
      if(index.includes('auto-detected project') || bogus.includes(title)) el.remove();
    });
    qa('.ticket').forEach(el=>{
      const title=(q('h3',el)?.textContent||'').trim().toLowerCase();
      if(['site','ios app','windows app','android app','web app'].includes(title)) el.remove();
    });
    qa('.navlinks a').forEach(a=>{
      const href=a.getAttribute('href')||'';
      if(href==='#sathi' || /site|ios-app|windows-app|android-app/i.test(href)) a.remove();
    });
  }

  function ensureSwitch(){
    if(q('.lang-switch')) return;
    const host=q('.navin'); if(!host) return;
    const box=document.createElement('div'); box.className='lang-switch'; box.setAttribute('aria-label','Language');
    box.innerHTML='<button type="button" data-lang="en">EN</button><button type="button" data-lang="np">नेपाली</button>';
    host.appendChild(box);
    box.addEventListener('click',e=>{
      const b=e.target.closest('button[data-lang]'); if(!b)return;
      lang=b.dataset.lang===NP?NP:EN;
      localStorage.setItem('pc-portfolio-lang',lang);
      apply();
    });
  }

  function setStatus(project,pair){
    const el=q('.project-status',project); if(!el)return;
    const dot=q('.dot',el)?.cloneNode(true);
    el.textContent=''; if(dot)el.appendChild(dot); el.append(document.createTextNode(' '+pick(pair)));
  }

  function translateProject(selector,data){
    const p=q(selector); if(!p)return;
    setStatus(p,data.status);
    const desc=q('.project-copy > p',p); set(desc,data.desc);
  }

  function apply(){
    removeFalseProjects();
    document.documentElement.lang=lang===NP?'ne':'en';
    qa('.lang-switch button').forEach(b=>b.classList.toggle('active',b.dataset.lang===lang));

    html(q('.hero .kicker'),T.hero.kicker);
    html(q('.hero h1'),T.hero.title);
    set(q('.hero-copy'),T.hero.copy);
    set(q('.board-title b'),T.hero.board);
    set(q('.board-title span'),T.hero.builds);

    const navMap={'#work':T.nav.work,'#team-tracker':T.nav.team,'#fixcheck':T.nav.fix,'#datemate':T.nav.date,'#floodsafe':T.nav.flood,'#about':T.nav.about,'#contact':T.nav.contact};
    qa('.navlinks a').forEach(a=>{const p=navMap[a.getAttribute('href')];if(p)set(a,p)});

    const work=q('#work .section-title'); if(work){set(q('small',work),T.work.small);set(q('h2',work),T.work.title);set(q('p',work),T.work.copy)}
    const about=q('#about .section-title'); if(about){set(q('small',about),T.about.small);set(q('h2',about),T.about.title);set(q('p',about),T.about.copy)}
    const contact=q('#contact .section-title'); if(contact){set(q('small',contact),T.contact.small);set(q('h2',contact),T.contact.title);set(q('p',contact),T.contact.copy)}

    translateProject('#team-tracker',T.projects.team);
    translateProject('#fixcheck',T.projects.fix);
    translateProject('#datemate',T.projects.date);
    translateProject('#floodsafe',T.projects.flood);

    const team=q('#team-tracker');
    if(team){
      let note=q('.portfolio-privacy-note',team);
      if(!note){note=document.createElement('p');note.className='portfolio-privacy-note';q('.project-copy',team)?.appendChild(note)}
      set(note,T.projects.team.privacy);
    }
  }

  function boot(){
    removeFalseProjects();
    ensureSwitch();
    apply();
    // Run once more after other portfolio modules have finished injecting their known sections.
    setTimeout(apply,250);
    setTimeout(apply,1200);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();