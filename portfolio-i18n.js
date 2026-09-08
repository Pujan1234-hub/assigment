(()=>{
  if(window.__pcPortfolioI18nV4) return;
  window.__pcPortfolioI18nV4=true;

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
    .sathi-preview{background:#11151b;color:#dfe7f3;border:1px solid var(--ink,#17191d);min-height:320px;padding:18px;font-family:"SFMono-Regular",Consolas,monospace;box-shadow:5px 6px 0 rgba(23,25,29,.09)}
    .sathi-preview .sp-head{display:flex;justify-content:space-between;gap:16px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,.13);font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:#9ca8b9}
    .sathi-preview .sp-status{color:#67d7ab}.sathi-preview .sp-lines{display:grid;gap:11px;padding-top:18px;font-size:.75rem}.sathi-preview .sp-line{display:grid;grid-template-columns:92px 1fr;gap:12px}.sathi-preview .sp-key{color:#7894ff}.sathi-preview .sp-value{color:#dfe7f3}.sathi-preview .sp-pulse{display:inline-block;width:7px;height:7px;border-radius:50%;background:#67d7ab;margin-right:7px;box-shadow:0 0 0 5px rgba(103,215,171,.08)}
    @media(max-width:1050px){.lang-switch{margin-left:auto}}
    @media(max-width:700px){.lang-switch{font-size:.67rem}.lang-switch button{padding:6px 8px}.sathi-preview{min-height:280px}}
  `;
  document.head.appendChild(style);

  const T={
    hero:{
      kicker:['Software portfolio · 2026','सफ्टवेयर पोर्टफोलियो · २०२६'],
      title:['I build small software that fixes <em>real-world friction.</em>','म वास्तविक जीवनका समस्या घटाउने <em>उपयोगी सफ्टवेयर बनाउँछु।</em>'],
      copy:['Five real projects are currently in the portfolio. SATHI AI is shown only as the FloodSafe Nepal companion prototype that is being built and tested now, alongside the other working product directions.','पोर्टफोलियोमा अहिले पाँच वास्तविक प्रोजेक्ट छन्। SATHI AI लाई अहिले बनाइँदै र परीक्षण हुँदै गरेको FloodSafe Nepal companion prototype को रूपमा मात्र देखाइएको छ।'],
      board:['On my desk right now','अहिले म बनाइरहेको'],
      builds:['Current builds','हालका प्रोजेक्ट']
    },
    nav:{work:['Work','काम'],team:['Team Tracker','टिम ट्र्याकर'],fix:['FixCheck','फिक्सचेक'],date:['DateMate','डेटमेट'],flood:['FloodSafe Nepal','फ्लडसेफ नेपाल'],sathi:['SATHI AI','SATHI AI'],about:['About','मेरो बारेमा'],contact:['Contact','सम्पर्क']},
    work:{small:['Selected work','मुख्य काम'],title:['Projects with a reason to exist.','काम लाग्ने उद्देश्य भएका प्रोजेक्टहरू।'],copy:['Each build starts with a practical problem, then moves through system design, interface work, testing and repeated refinement.','हरेक प्रोजेक्ट वास्तविक समस्याबाट सुरु हुन्छ, त्यसपछि system design, interface, testing र पटक-पटक सुधार हुँदै अगाडि बढ्छ।']},
    about:{small:['About','मेरो बारेमा'],title:['How I approach software.','म सफ्टवेयर कसरी बनाउँछु।'],copy:['A Computer Science mindset: break the problem down, model the flow, test the system and refine the interface.','Computer Science को सोच: समस्यालाई भागमा छुट्याउने, flow बनाउने, system परीक्षण गर्ने र interface सुधार्ने।']},
    contact:{small:['Contact','सम्पर्क'],title:["Let’s talk software.",'सफ्टवेयरबारे कुरा गरौं।'],copy:['For software, product, prototype, or collaboration enquiries.','सफ्टवेयर, प्रोडक्ट, प्रोटोटाइप वा सहकार्यका लागि सम्पर्क गर्नुहोस्।']},
    projects:{
      team:{status:['Working web app','चलिरहेको वेब एप'],desc:['A browser-based workflow product for live team status, task flow and a clear operations view. The public portfolio version uses sample data only.','Live team status, task flow र स्पष्ट operations view का लागि बनाइएको browser-based workflow product। सार्वजनिक portfolio version मा sample data मात्र प्रयोग हुन्छ।'],privacy:['Public interactive build · sample data only · no private operational records.','सार्वजनिक interactive build · sample data मात्र · कुनै निजी operational record छैन।']},
      fix:{status:['In development','विकासमा'],desc:['A no-login connectivity diagnostic utility that turns network signals into a clear next step instead of a wall of technical information.','Login नचाहिने connectivity diagnostic utility जसले जटिल network signal लाई बुझ्न सजिलो next step मा बदल्छ।']},
      date:{status:['Active development','सक्रिय विकास'],desc:['An expiry-date reminder app for capturing important dates and receiving useful reminders before items expire.','महत्त्वपूर्ण expiry date राख्ने र म्याद सकिनुअघि उपयोगी reminder दिने app।']},
      flood:{status:['Active development','सक्रिय विकास'],desc:['A Nepal-focused flood and river awareness platform built around local context, map-first information and frequently refreshed official river data.','नेपाल केन्द्रित बाढी तथा नदी जानकारी platform, जसले local context, map-first information र बारम्बार refresh हुने आधिकारिक river data मा ध्यान दिन्छ।']},
      sathi:{
        status:['Early prototype · FloodSafe companion','प्रारम्भिक prototype · FloodSafe companion'],
        desc:['SATHI AI is currently a limited companion prototype inside the FloodSafe Nepal experience. When the companion is installed or enabled, it is designed to request the permissions it needs and run alongside FloodSafe in the background. The current work is focused on helping users interact with FloodSafe-related river, flood and weather information more naturally, without changing the working FloodSafe core.','SATHI AI अहिले FloodSafe Nepal भित्रको सीमित companion prototype हो। Companion install वा enable गर्दा आवश्यक permissions माग्ने र FloodSafe सँगै background मा चल्ने गरी design गरिएको छ। अहिलेको काम FloodSafe को working core नबिगारी river, flood र weather जानकारीलाई user ले अझ सहज तरिकाले बुझ्न र सोध्न सक्ने बनाउनेमा केन्द्रित छ।'],
        bullets:[
          ['Current scope: FloodSafe Nepal companion prototype.','हालको scope: FloodSafe Nepal companion prototype।'],
          ['Permission-based setup when the companion is installed or enabled.','Companion install वा enable गर्दा permission-based setup।'],
          ['Designed to run in the background alongside FloodSafe Nepal.','FloodSafe Nepal सँगै background मा चल्ने गरी design।'],
          ['Uses FloodSafe river and flood context for more natural assistance.','FloodSafe को river र flood context प्रयोग गरेर सहज सहायता दिने direction।'],
          ['Uses available weather context to explain rain timing more clearly.','उपलब्ध weather context प्रयोग गरेर पानीको timing अझ स्पष्ट बुझाउने direction।'],
          ['Presented only as the limited capability currently being built and tested.','अहिले बनाइँदै र परीक्षण हुँदै गरेको सीमित capability मात्र देखाइएको छ।']
        ],
        link:['Project contact ↗','प्रोजेक्ट सम्पर्क ↗']
      }
    }
  };

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
    const host=q('.navin');if(!host)return;
    const box=document.createElement('div');box.className='lang-switch';box.setAttribute('aria-label','Language');
    box.innerHTML='<button type="button" data-lang="en">EN</button><button type="button" data-lang="np">नेपाली</button>';
    const note=q('.open-note',host);if(note)host.insertBefore(box,note);else host.appendChild(box);
    box.addEventListener('click',e=>{const b=e.target.closest('button[data-lang]');if(!b)return;lang=b.dataset.lang===NP?NP:EN;localStorage.setItem('pc-portfolio-lang',lang);apply()});
  }

  function ensureSathi(){
    const nav=q('.navlinks');
    if(nav&&!q('a[href="#sathi-ai"]',nav)){
      const a=document.createElement('a');a.href='#sathi-ai';a.textContent='SATHI AI';
      const about=q('a[href="#about"]',nav);if(about)nav.insertBefore(a,about);else nav.appendChild(a);
    }

    const aside=q('.hero-aside');
    if(aside&&!q('[data-product="sathi-ai"]',aside)){
      const card=document.createElement('div');card.className='ticket';card.dataset.product='sathi-ai';card.style.background='#eef3ff';card.style.transform='rotate(-.25deg)';
      card.innerHTML='<div class="ticket-head"><h3>SATHI AI</h3><span class="tag">EARLY PROTOTYPE</span></div><p>FloodSafe Nepal companion prototype with permission-based background operation and flood/weather context.</p><a href="#sathi-ai">View build notes →</a>';
      aside.appendChild(card);
    }

    if(!q('#sathi-ai')){
      const after=q('#datemate')||q('#floodsafe');
      if(after){
        const article=document.createElement('article');article.className='project';article.id='sathi-ai';
        article.innerHTML=`<div class="project-side"><div><div class="project-index">05 / FloodSafe companion prototype</div><h3>SATHI AI</h3><div class="project-status"><span class="dot"></span> Early prototype</div></div><div class="side-links"><a href="#contact">Project contact ↗</a></div></div><div class="project-main"><div class="project-copy"><p></p><div class="bullets"><div class="bullet"><i>01</i><span></span></div><div class="bullet"><i>02</i><span></span></div><div class="bullet"><i>03</i><span></span></div><div class="bullet"><i>04</i><span></span></div><div class="bullet"><i>05</i><span></span></div><div class="bullet"><i>06</i><span></span></div></div></div><div class="sathi-preview"><div class="sp-head"><span>SATHI / FLOODSAFE COMPANION</span><span class="sp-status"><span class="sp-pulse"></span>PROTOTYPE</span></div><div class="sp-lines"><div class="sp-line"><b class="sp-key">scope</b><span class="sp-value">FloodSafe companion prototype</span></div><div class="sp-line"><b class="sp-key">permission</b><span class="sp-value">user-granted setup</span></div><div class="sp-line"><b class="sp-key">background</b><span class="sp-value">runs alongside FloodSafe</span></div><div class="sp-line"><b class="sp-key">river</b><span class="sp-value">FloodSafe river context</span></div><div class="sp-line"><b class="sp-key">weather</b><span class="sp-value">rain timing context</span></div><div class="sp-line"><b class="sp-key">status</b><span class="sp-value">limited prototype</span></div></div></div></div>`;
        after.insertAdjacentElement('afterend',article);
      }
    }

    const contactNumber=q('#contact .section-number');if(contactNumber)contactNumber.textContent='06';
    const foot=q('.footlinks');if(foot&&!q('a[href="#sathi-ai"]',foot)){const a=document.createElement('a');a.href='#sathi-ai';a.textContent='SATHI AI';foot.appendChild(a)}
  }

  function setStatus(project,pair){
    const el=q('.project-status',project);if(!el)return;
    const dot=q('.dot',el)?.cloneNode(true);el.textContent='';if(dot)el.appendChild(dot);el.append(document.createTextNode(' '+pick(pair)));
  }

  function translateProject(selector,data){
    const p=q(selector);if(!p)return;
    setStatus(p,data.status);set(q('.project-copy > p',p),data.desc);
    if(data.bullets)qa('.bullet span',p).forEach((el,i)=>{if(data.bullets[i])set(el,data.bullets[i])});
    if(data.link){const a=q('.side-links a',p);if(a)set(a,data.link)}
  }

  function translateTicket(name,data){
    qa('.hero-aside .ticket').forEach(card=>{
      if((q('h3',card)?.textContent||'').trim()!==name)return;
      set(q('.tag',card),data.status);set(q('p',card),data.desc);
      const a=q('a',card);if(a)a.textContent=lang===NP?'विवरण हेर्नुहोस् →':'View build notes →';
    });
  }

  function apply(){
    removeFalseProjects();ensureSathi();
    document.documentElement.lang=lang===NP?'ne':'en';qa('.lang-switch button').forEach(b=>b.classList.toggle('active',b.dataset.lang===lang));
    html(q('.hero .kicker'),T.hero.kicker);html(q('.hero h1'),T.hero.title);set(q('.hero-copy'),T.hero.copy);set(q('.board-title b'),T.hero.board);set(q('.board-title span'),T.hero.builds);
    const navMap={'#work':T.nav.work,'#team-tracker':T.nav.team,'#fixcheck':T.nav.fix,'#datemate':T.nav.date,'#floodsafe':T.nav.flood,'#sathi-ai':T.nav.sathi,'#about':T.nav.about,'#contact':T.nav.contact};
    qa('.navlinks a').forEach(a=>{const p=navMap[a.getAttribute('href')];if(p)set(a,p)});
    const work=q('#work .section-title');if(work){set(q('small',work),T.work.small);set(q('h2',work),T.work.title);set(q('p',work),T.work.copy)}
    const about=q('#about .section-title');if(about){set(q('small',about),T.about.small);set(q('h2',about),T.about.title);set(q('p',about),T.about.copy)}
    const contact=q('#contact .section-title');if(contact){set(q('small',contact),T.contact.small);set(q('h2',contact),T.contact.title);set(q('p',contact),T.contact.copy)}
    translateProject('#team-tracker',T.projects.team);translateProject('#fixcheck',T.projects.fix);translateProject('#datemate',T.projects.date);translateProject('#floodsafe',T.projects.flood);translateProject('#sathi-ai',T.projects.sathi);translateTicket('SATHI AI',T.projects.sathi);
    const team=q('#team-tracker');if(team){let note=q('.portfolio-privacy-note',team);if(!note){note=document.createElement('p');note.className='portfolio-privacy-note';q('.project-copy',team)?.appendChild(note)}set(note,T.projects.team.privacy)}
    document.dispatchEvent(new CustomEvent('portfolio:language',{detail:{lang}}));
  }

  function boot(){removeFalseProjects();ensureSathi();ensureSwitch();apply();setTimeout(apply,250);setTimeout(apply,1200)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();