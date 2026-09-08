(()=>{
  if(window.__pcPortfolioI18nV6) return;
  window.__pcPortfolioI18nV6=true;

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
    .sathi-preview .sp-head{display:flex;justify-content:space-between;gap:16px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,.13);font-size:.68rem;text-transform:none;letter-spacing:.06em;color:#9ca8b9}
    .sathi-preview .sp-status{color:#67d7ab}.sathi-preview .sp-lines{display:grid;gap:11px;padding-top:18px;font-size:.75rem}.sathi-preview .sp-line{display:grid;grid-template-columns:92px 1fr;gap:12px}.sathi-preview .sp-key{color:#7894ff}.sathi-preview .sp-value{color:#dfe7f3}.sathi-preview .sp-pulse{display:inline-block;width:7px;height:7px;border-radius:50%;background:#67d7ab;margin-right:7px;box-shadow:0 0 0 5px rgba(103,215,171,.08)}
    @media(max-width:1050px){.lang-switch{margin-left:auto}}
    @media(max-width:700px){.lang-switch{font-size:.67rem}.lang-switch button{padding:6px 8px}.sathi-preview{min-height:280px}}
  `;
  document.head.appendChild(style);

  const T={
    hero:{
      kicker:['Software portfolio · 2026','सफ्टवेयर पोर्टफोलियो · २०२६'],
      title:['I build small software that fixes <em>real-world friction.</em>','म वास्तविक जीवनका समस्या घटाउने <em>उपयोगी सफ्टवेयर बनाउँछु।</em>'],
      copy:['Five real projects are currently in the portfolio. SATHI AI is shown only as the FloodSafe Nepal companion prototype that is being built and tested now, alongside the other working product directions.','पोर्टफोलियोमा अहिले पाँच वास्तविक प्रोजेक्ट छन्। SATHI AI लाई हाल निर्माण र परीक्षण भइरहेको FloodSafe Nepal को सहायक नमुनाका रूपमा मात्र देखाइएको छ।'],
      board:['On my desk right now','अहिले म बनाइरहेको'],
      builds:['Current builds','हाल निर्माणमा'],
      open:['Building in public','सार्वजनिक रूपमा निर्माण'],
      actions:[['See the work','काम हेर्नुहोस्'],['Open Team Tracker','Team Tracker खोल्नुहोस्'],['Open FixCheck','FixCheck खोल्नुहोस्'],['See DateMate','DateMate हेर्नुहोस्']]
    },
    nav:{work:['Work','काम'],team:['Team Tracker','Team Tracker'],fix:['FixCheck','FixCheck'],date:['DateMate','DateMate'],flood:['FloodSafe Nepal','FloodSafe Nepal'],sathi:['SATHI AI','SATHI AI'],about:['About','मेरो बारेमा'],contact:['Contact','सम्पर्क']},
    work:{small:['Selected work','मुख्य काम'],title:['Projects with a reason to exist.','उद्देश्यसहित बनाइएका प्रोजेक्टहरू।'],copy:['Each build starts with a practical problem, then moves through system design, interface work, testing and repeated refinement.','हरेक प्रोजेक्ट वास्तविक समस्याबाट सुरु हुन्छ। त्यसपछि प्रणालीको संरचना, प्रयोगकर्ता अनुभव, परीक्षण र निरन्तर सुधार हुँदै अगाडि बढ्छ।']},
    about:{small:['About','मेरो बारेमा'],title:['How I approach software.','म सफ्टवेयर कसरी बनाउँछु।'],copy:['A Computer Science mindset: break the problem down, model the flow, test the system and refine the interface.','कम्प्युटर विज्ञानको सोच: समस्यालाई भागमा छुट्याउने, कामको प्रवाह बनाउने, प्रणाली परीक्षण गर्ने र प्रयोगकर्ता अनुभव सुधार्ने।']},
    contact:{small:['Contact','सम्पर्क'],title:["Let’s talk software.",'सफ्टवेयरबारे कुरा गरौँ।'],copy:['For software, product, prototype, or collaboration enquiries.','सफ्टवेयर, प्रोडक्ट, प्रारम्भिक नमुना वा सहकार्यका लागि सम्पर्क गर्नुहोस्।']},
    projects:{
      team:{
        index:['01 / Team coordination','०१ / टोली समन्वय'],status:['Working web app','चलिरहेको वेब अनुप्रयोग'],
        desc:['A browser-based workflow product for live team status, task flow and a clear operations view. The public portfolio version uses sample data only.','टोलीको प्रत्यक्ष अवस्था, कामको प्रवाह र स्पष्ट सञ्चालन दृश्यका लागि बनाइएको ब्राउजरमा चल्ने प्रणाली। सार्वजनिक पोर्टफोलियो संस्करणमा नमुना डाटा मात्र प्रयोग हुन्छ।'],
        bullets:[['Start/end session flow with clear active status.','सत्र सुरु र अन्त्य गर्दा स्पष्ट सक्रिय अवस्था।'],['Task assignment, acknowledgement, completion and skip states.','काम तोक्ने, स्वीकार गर्ने, पूरा गर्ने र छोड्ने अवस्थाहरू।'],['Operations view with map-based context and live workflow status.','नक्सासहितको सञ्चालन दृश्य र प्रत्यक्ष कामको अवस्था।'],['Designed to stay understandable on both phone and desktop.','फोन र कम्प्युटर दुवैमा सजिलै बुझिने गरी बनाइएको।']],
        links:[['Open web app ↗','वेब अनुप्रयोग खोल्नुहोस् ↗'],['About the build','निर्माणबारे']],
        privacy:['Public interactive build · sample data only · no private operational records.','सार्वजनिक अन्तरक्रियात्मक संस्करण · नमुना डाटा मात्र · कुनै निजी सञ्चालन अभिलेख छैन।'],
        ticket:['Live team status, task flow and an operations view built around a simpler daily workflow.','दैनिक कामलाई सरल बनाउन टोलीको प्रत्यक्ष अवस्था, कामको प्रवाह र सञ्चालन दृश्य।']
      },
      fix:{
        index:['02 / Diagnostics','०२ / जडान परीक्षण'],status:['In development','विकासमा'],
        desc:['A no-login connectivity diagnostic utility that turns network signals into a clear next step instead of a wall of technical information.','लगइन बिना चल्ने जडान परीक्षण उपकरण, जसले नेटवर्कका संकेतहरूलाई जटिल प्राविधिक विवरणको सट्टा बुझ्न सजिलो अर्को कदममा बदल्छ।'],
        bullets:[['No forced account wall for the core check.','मुख्य परीक्षणका लागि खाता खोल्न बाध्य पारिँदैन।'],['Uses browser-available network signals instead of pretending to see everything.','ब्राउजरबाट उपलब्ध नेटवर्क संकेत मात्र प्रयोग गर्छ; नदेखेको कुरा देखेजस्तो गर्दैन।'],['Explains likely causes in plain language.','सम्भावित कारण सरल भाषामा बुझाउँछ।'],['Ends with a practical next step instead of raw technical output.','कच्चा प्राविधिक नतिजाको सट्टा उपयोगी अर्को कदम दिन्छ।']],
        links:[['Open web app ↗','वेब अनुप्रयोग खोल्नुहोस् ↗']],
        ticket:['A no-login diagnostic utility that turns network signals into an understandable next step.','लगइन बिना चल्ने जडान परीक्षण उपकरण, जसले नेटवर्क संकेतलाई बुझ्न सजिलो अर्को कदममा बदल्छ।']
      },
      date:{
        index:['03 / Expiry tracking','०३ / म्याद ट्र्याकिङ'],status:['Active development','सक्रिय विकास'],
        desc:['An expiry-date reminder app for capturing important dates and receiving useful reminders before items expire.','महत्त्वपूर्ण म्याद राख्ने र समय सकिनुअघि उपयोगी सम्झना दिने मिति-स्मरण अनुप्रयोग।'],
        bullets:[['Smart scan flow for adding items and reading expiry information.','सामान थप्न र म्याद पढ्न स्मार्ट स्क्यान प्रक्रिया।'],['Clear “expiring soon”, “this week” and “fresh” summaries.','“छिट्टै म्याद सकिने”, “यो हप्ता” र “ताजा” अवस्थाको स्पष्ट सारांश।'],['Reminder-first design so dates turn into useful action.','मितिलाई उपयोगी काममा बदल्ने सम्झना-केन्द्रित डिजाइन।'],['Archive/history with restore and delete controls for used items.','प्रयोग भइसकेका सामानका लागि फिर्ता ल्याउने र मेटाउने सुविधासहित अभिलेख।']],
        links:[['View screenshots ↓','तस्बिरहरू हेर्नुहोस् ↓']],
        ticket:['Smart expiry tracking with scanning, reminders, item history and a simple everyday interface.','स्क्यान, सम्झना, पुरानो अभिलेख र सरल दैनिक प्रयोगसहित म्याद ट्र्याकिङ।']
      },
      flood:{
        index:['04 / Public safety','०४ / सार्वजनिक सुरक्षा'],status:['Active development','सक्रिय विकास'],
        desc:['A Nepal-focused flood and river awareness platform built around local context, map-first information and frequently refreshed official river data.','नेपाल केन्द्रित बाढी तथा नदी सचेतना प्रणाली, स्थानीय सन्दर्भ, नक्सा-केन्द्रित जानकारी र बारम्बार ताजा हुने आधिकारिक नदी डाटामा आधारित।'],
        bullets:[['Nepal-focused river map with official station context.','आधिकारिक स्टेशन जानकारीसहित नेपाल केन्द्रित नदी नक्सा।'],['Official river observations, latest readings and warning states where available.','उपलब्ध ठाउँमा आधिकारिक नदी मापन, पछिल्लो रिडिङ र चेतावनी अवस्था।'],['Local weather/rain view, visible update timing and location-aware messaging.','स्थानीय मौसम तथा वर्षा दृश्य, अपडेट समय र स्थानअनुसार सन्देश।'],['Human-impact figures, alerts and Nepal news in the same safety experience.','मानवीय प्रभावका तथ्याङ्क, सतर्कता र नेपाल समाचार एउटै सुरक्षा अनुभवमा।']],
        links:[['Open latest web app ↗','नवीनतम वेब अनुप्रयोग खोल्नुहोस् ↗'],['View screenshots ↓','तस्बिरहरू हेर्नुहोस् ↓']],
        ticket:['Nepal-first map and river awareness with local relevance, update timing and clearer alerts.','नेपाल केन्द्रित नक्सा, नदी जानकारी, स्थानीय सान्दर्भिकता, अपडेट समय र स्पष्ट सतर्कता।']
      },
      sathi:{
        index:['05 / FloodSafe companion prototype','०५ / FloodSafe सहायक नमुना'],
        status:['Early prototype · FloodSafe companion','प्रारम्भिक नमुना · FloodSafe सहायक'],
        desc:['SATHI AI is currently a limited companion prototype inside the FloodSafe Nepal experience. When the companion is installed or enabled, it is designed to request the permissions it needs and run alongside FloodSafe in the background. The current work is focused on helping users interact with FloodSafe-related river, flood and weather information more naturally, without changing the working FloodSafe core.','SATHI AI अहिले FloodSafe Nepal भित्र परीक्षण भइरहेको सीमित सहायक नमुना हो। यसलाई जडान वा सक्रिय गर्दा आवश्यक अनुमति माग्ने र अनुमति पाएपछि FloodSafe सँगै पृष्ठभूमिमा चल्ने गरी विकास भइरहेको छ। अहिलेको काम FloodSafe को मुख्य प्रणाली नबिगारी नदी, बाढी र मौसमसम्बन्धी जानकारी प्रयोगकर्ताले सहज रूपमा सोध्न र बुझ्न सक्ने बनाउनेमा केन्द्रित छ।'],
        bullets:[['Current scope: FloodSafe Nepal companion prototype.','हालको काम: FloodSafe Nepal का लागि सहायक नमुना।'],['Permission-based setup when the companion is installed or enabled.','जडान वा सक्रिय गर्दा आवश्यक अनुमतिमा आधारित सेटअप।'],['Designed to run in the background alongside FloodSafe Nepal.','FloodSafe Nepal सँगै पृष्ठभूमिमा चल्ने गरी विकास।'],['Uses FloodSafe river and flood context for more natural assistance.','FloodSafe को नदी तथा बाढी जानकारी प्रयोग गरी सहज सहायता दिने।'],['Uses available weather context to explain rain timing more clearly.','उपलब्ध मौसम जानकारीबाट वर्षाको समय अझ स्पष्ट बुझाउन सहयोग गर्ने।'],['Presented only as the limited capability currently being built and tested.','हाल निर्माण र परीक्षण भइरहेको सीमित क्षमता मात्र सार्वजनिक रूपमा देखाइएको छ।']],
        links:[['Project contact ↗','प्रोजेक्टबारे सम्पर्क ↗']],
        ticket:['FloodSafe Nepal companion prototype with permission-based background operation and flood/weather context.','अनुमतिमा आधारित पृष्ठभूमि सञ्चालन तथा बाढी/मौसम जानकारीका लागि FloodSafe Nepal सहायक नमुना।'],
        preview:{head:['SATHI / FLOODSAFE COMPANION','SATHI / FLOODSAFE सहायक'],state:['PROTOTYPE','परीक्षण'],keys:[['scope','क्षेत्र'],['permission','अनुमति'],['background','पृष्ठभूमि'],['river','नदी'],['weather','मौसम'],['status','स्थिति']],values:[['FloodSafe companion prototype','FloodSafe सहायक नमुना'],['user-granted setup','प्रयोगकर्ताको अनुमति'],['runs alongside FloodSafe','FloodSafe सँगै चल्ने'],['FloodSafe river context','नदी तथा बाढी जानकारी'],['rain timing context','वर्षाको समयसम्बन्धी जानकारी'],['limited prototype','सीमित प्रारम्भिक नमुना']]}
      }
    }
  };

  function removeFalseProjects(){
    q('#new-projects')?.remove();q('#sathi')?.remove();qa('.auto-project').forEach(el=>el.remove());
    qa('.project').forEach(el=>{const title=(q('.project-side h3',el)?.textContent||'').trim().toLowerCase();const index=(q('.project-index',el)?.textContent||'').trim().toLowerCase();const bogus=['site','ios app','windows app','android app','web app'];if(index.includes('auto-detected project')||bogus.includes(title))el.remove()});
    qa('.ticket').forEach(el=>{const title=(q('h3',el)?.textContent||'').trim().toLowerCase();if(['site','ios app','windows app','android app','web app'].includes(title))el.remove()});
    qa('.navlinks a').forEach(a=>{const href=a.getAttribute('href')||'';if(href==='#sathi'||/site|ios-app|windows-app|android-app/i.test(href))a.remove()});
  }

  function ensureSwitch(){
    if(q('.lang-switch'))return;const host=q('.navin');if(!host)return;
    const box=document.createElement('div');box.className='lang-switch';box.setAttribute('aria-label','Language');box.innerHTML='<button type="button" data-lang="en">EN</button><button type="button" data-lang="np">नेपाली</button>';
    const note=q('.open-note',host);if(note)host.insertBefore(box,note);else host.appendChild(box);
    box.addEventListener('click',e=>{const b=e.target.closest('button[data-lang]');if(!b)return;lang=b.dataset.lang===NP?NP:EN;localStorage.setItem('pc-portfolio-lang',lang);apply()});
  }

  function ensureSathi(){
    const nav=q('.navlinks');if(nav&&!q('a[href="#sathi-ai"]',nav)){const a=document.createElement('a');a.href='#sathi-ai';a.textContent='SATHI AI';const about=q('a[href="#about"]',nav);if(about)nav.insertBefore(a,about);else nav.appendChild(a)}
    const aside=q('.hero-aside');if(aside&&!q('[data-product="sathi-ai"]',aside)){const card=document.createElement('div');card.className='ticket';card.dataset.product='sathi-ai';card.style.background='#eef3ff';card.style.transform='rotate(-.25deg)';card.innerHTML='<div class="ticket-head"><h3>SATHI AI</h3><span class="tag">EARLY PROTOTYPE</span></div><p>FloodSafe Nepal companion prototype with permission-based background operation and flood/weather context.</p><a href="#sathi-ai">View build notes →</a>';aside.appendChild(card)}
    if(!q('#sathi-ai')){const after=q('#datemate')||q('#floodsafe');if(after){const article=document.createElement('article');article.className='project';article.id='sathi-ai';article.innerHTML=`<div class="project-side"><div><div class="project-index">05 / FloodSafe companion prototype</div><h3>SATHI AI</h3><div class="project-status"><span class="dot"></span> Early prototype</div></div><div class="side-links"><a href="#contact">Project contact ↗</a></div></div><div class="project-main"><div class="project-copy"><p></p><div class="bullets"><div class="bullet"><i>01</i><span></span></div><div class="bullet"><i>02</i><span></span></div><div class="bullet"><i>03</i><span></span></div><div class="bullet"><i>04</i><span></span></div><div class="bullet"><i>05</i><span></span></div><div class="bullet"><i>06</i><span></span></div></div></div><div class="sathi-preview"><div class="sp-head"><span>SATHI / FLOODSAFE COMPANION</span><span class="sp-status"><span class="sp-pulse"></span>PROTOTYPE</span></div><div class="sp-lines"><div class="sp-line"><b class="sp-key">scope</b><span class="sp-value">FloodSafe companion prototype</span></div><div class="sp-line"><b class="sp-key">permission</b><span class="sp-value">user-granted setup</span></div><div class="sp-line"><b class="sp-key">background</b><span class="sp-value">runs alongside FloodSafe</span></div><div class="sp-line"><b class="sp-key">river</b><span class="sp-value">FloodSafe river context</span></div><div class="sp-line"><b class="sp-key">weather</b><span class="sp-value">rain timing context</span></div><div class="sp-line"><b class="sp-key">status</b><span class="sp-value">limited prototype</span></div></div></div></div>`;after.insertAdjacentElement('afterend',article)}}
    const contactNumber=q('#contact .section-number');if(contactNumber)contactNumber.textContent='06';const foot=q('.footlinks');if(foot&&!q('a[href="#sathi-ai"]',foot)){const a=document.createElement('a');a.href='#sathi-ai';a.textContent='SATHI AI';foot.appendChild(a)}
  }

  function setStatus(project,pair){const el=q('.project-status',project);if(!el)return;const dot=q('.dot',el)?.cloneNode(true);el.textContent='';if(dot)el.appendChild(dot);el.append(document.createTextNode(' '+pick(pair)))}
  function translateProject(selector,data){const p=q(selector);if(!p)return;set(q('.project-index',p),data.index);setStatus(p,data.status);set(q('.project-copy > p',p),data.desc);if(data.bullets)qa('.bullet span',p).forEach((el,i)=>{if(data.bullets[i])set(el,data.bullets[i])});if(data.links)qa('.side-links a',p).forEach((el,i)=>{if(data.links[i])set(el,data.links[i])})}
  function translateTicket(name,data){qa('.hero-aside .ticket').forEach(card=>{if((q('h3',card)?.textContent||'').trim()!==name)return;set(q('.tag',card),data.status);set(q('p',card),data.ticket||data.desc);const a=q('a',card);if(a)a.textContent=lang===NP?'विवरण हेर्नुहोस् →':'View build notes →'})}

  function translateSathiPreview(){
    const p=q('#sathi-ai'),d=T.projects.sathi.preview;if(!p||!d)return;const head=qa('.sp-head > span',p);if(head[0])set(head[0],d.head);
    const st=q('.sp-status',p);if(st){const pulse=q('.sp-pulse',st)?.cloneNode(true);st.textContent='';if(pulse)st.appendChild(pulse);st.append(document.createTextNode(pick(d.state)))}
    qa('.sp-key',p).forEach((el,i)=>{if(d.keys[i])set(el,d.keys[i])});qa('.sp-value',p).forEach((el,i)=>{if(d.values[i])set(el,d.values[i])});
  }

  function translateStaticUI(){
    set(q('.open-note'),T.hero.open);qa('.hero-actions .btn').forEach((el,i)=>{if(T.hero.actions[i])set(el,T.hero.actions[i])});
    const rules=qa('.rule-item');const ruleText=[['<strong>Problem first</strong>Start with what is actually annoying or unclear.','<strong>समस्या पहिले</strong>वास्तवमै के झन्झटिलो वा अस्पष्ट छ, त्यहीँबाट सुरु।'],['<strong>Working versions</strong>Visitors can open the web products and see real app screens.','<strong>चल्ने संस्करण</strong>प्रयोगकर्ताले वेब उत्पादन खोल्न र वास्तविक अनुप्रयोगका स्क्रिन हेर्न सक्छन्।'],['<strong>Simple on purpose</strong>Good software should not need a manual for basic use.','<strong>जानाजानी सरल</strong>आधारभूत प्रयोगका लागि राम्रो सफ्टवेयरलाई पुस्तिका चाहिनु हुँदैन।'],['<strong>Iterate hard</strong>Build, test, break, fix, repeat.','<strong>निरन्तर सुधार</strong>बनाउने, परीक्षण गर्ने, कमजोरी भेट्ने, सुधार्ने र फेरि दोहोर्‍याउने।']];rules.forEach((el,i)=>{if(ruleText[i])html(el,ruleText[i])});

    const team=q('#teamtracker');if(team){set(q('.windowbar > span:last-child',team),['Operations view','सञ्चालन दृश्य']);const boxes=qa('.ui-box',team);if(boxes[0]){set(q('h4',boxes[0]),['Live activity','प्रत्यक्ष गतिविधि']);const r=qa('.row',boxes[0]);if(r[0]){set(q('span',r[0]),['Team member A','टोली सदस्य A']);set(q('b',r[0]),['Active','सक्रिय'])}if(r[1]){set(q('span',r[1]),['Team member B','टोली सदस्य B']);set(q('b',r[1]),['On task','काममा'])}}if(boxes[1]){set(q('h4',boxes[1]),['Task board','काम सूची']);const r=qa('.row',boxes[1]);const vals=[[['Area check','क्षेत्र जाँच'],['Assigned','तोकिएको']],[['Support request','सहयोग अनुरोध'],['Ack','स्वीकार']],[['Routine task','नियमित काम'],['Done','पूरा']]];r.forEach((x,i)=>{if(vals[i]){set(q('span',x),vals[i][0]);set(q('b',x),vals[i][1])}})}}

    const fix=q('#fixcheck');if(fix){set(q('.windowbar > span:last-child',fix),['Quick diagnosis','छिटो जाँच']);set(q('.tag',fix),['QUICK TEST','छिटो परीक्षण']);set(q('.phone-title',fix),['What is not working?','के चलिरहेको छैन?']);set(q('.phone-copy',fix),['Run the useful checks first. Keep the result simple.','पहिले उपयोगी जाँच चलाउनुहोस्। नतिजा सरल राख्नुहोस्।']);const r=qa('.row',fix),vals=[[['Device','उपकरण'],['Ready','तयार']],[['Network','नेटवर्क'],['Online','अनलाइन']],[['DNS','DNS'],['Responding','जवाफ दिँदै']],[['Target service','लक्षित सेवा'],['Checking','जाँच हुँदै']]];r.forEach((x,i)=>{if(vals[i]){set(q('span',x),vals[i][0]);set(q('b',x),vals[i][1])}});set(q('.big-action',fix),['RUN CHECK','जाँच चलाउनुहोस्'])}

    const date=q('#datemate');if(date){set(q('.windowbar > span:last-child',date),['DateMate mobile flow','DateMate मोबाइल प्रक्रिया']);set(q('.tag',date),['SMART EXPIRY','स्मार्ट म्याद']);set(q('.phone-title',date),['Never waste food again','खाना खेर जान नदिनुहोस्']);set(q('.phone-copy',date),['Scan. Track. Get reminded before it is too late.','स्क्यान गर्नुहोस्, ट्र्याक गर्नुहोस् र ढिलो हुनुअघि सम्झना पाउनुहोस्।']);const r=qa('.row',date),vals=[[['Expiring soon','छिट्टै म्याद सकिने'],['2 days','२ दिन']],[['This week','यो हप्ता'],['3–7 days','३–७ दिन']],[['Fresh','ताजा'],['7+ days','७+ दिन']]];r.forEach((x,i)=>{if(vals[i]){set(q('span',x),vals[i][0]);set(q('b',x),vals[i][1])}});set(q('.big-action',date),['SMART SCAN ITEM','सामान स्मार्ट स्क्यान']);const sh=q('.screens-head',date);if(sh){set(q('h4',sh),['Screenshots','तस्बिरहरू']);set(q('span',sh),['2 DateMate app screens','DateMate का २ स्क्रिन'])}const caps=qa('figcaption',date);const cp=[['Home dashboard and Smart Scan entry point.','मुख्य ड्यासबोर्ड र स्मार्ट स्क्यान सुरु गर्ने ठाउँ।'],['Archive / History with restore and delete actions.','फिर्ता ल्याउने र मेटाउने सुविधासहित अभिलेख / इतिहास।']];caps.forEach((x,i)=>{if(cp[i])set(x,cp[i])})}

    const flood=q('#floodsafe');if(flood){set(q('.windowbar > span:last-child',flood),['Flood awareness','बाढी सचेतना']);set(q('.ui-box h4',flood),['Nepal river view','नेपाल नदी दृश्य']);const r=qa('.row',flood),vals=[[['Nearby stations','नजिकका स्टेशन'],['Refreshing','ताजा हुँदै']],[['Local risk','स्थानीय जोखिम'],['Area based','क्षेत्रअनुसार']],[['Data freshness','डाटा ताजापन'],['Visible','देखिने']]];r.forEach((x,i)=>{if(vals[i]){set(q('span',x),vals[i][0]);set(q('b',x),vals[i][1])}});const sh=q('.screens-head',flood);if(sh){set(q('h4',sh),['Screenshots','तस्बिरहरू']);set(q('span',sh),['6 FloodSafe Nepal screens','FloodSafe Nepal का ६ स्क्रिन'])}const caps=qa('figcaption',flood);const cp=[['Official live river map and station coverage.','आधिकारिक प्रत्यक्ष नदी नक्सा र स्टेशन क्षेत्र।'],['Station detail card with latest official reading and status.','पछिल्लो आधिकारिक रिडिङ र अवस्थासहित स्टेशन विवरण।'],['Local weather and rainfall forecast view.','स्थानीय मौसम र वर्षा पूर्वानुमान दृश्य।'],['Human impact figures and latest Nepal news sources.','मानवीय प्रभावका तथ्याङ्क र पछिल्ला नेपाल समाचार स्रोत।'],['Location-aware weather, warning and alert state.','स्थानअनुसार मौसम, चेतावनी र सतर्कता अवस्था।'],['FloodSafe Nepal project showcase poster.','FloodSafe Nepal प्रोजेक्ट प्रदर्शन पोस्टर।']];caps.forEach((x,i)=>{if(cp[i])set(x,cp[i])})}

    const notes=q('.note-grid');if(notes){set(q('.note-big small',notes),['How I work','म कसरी काम गर्छु']);set(q('.note-big p',notes),['Make the confusing thing obvious. Make the slow thing faster. Make the useful thing easier to reach.','अलमलिएको कुरा स्पष्ट बनाउने। ढिलो कुरा छिटो बनाउने। उपयोगी कुरा सजिलै पहुँचमा ल्याउने।']);const sm=qa('.note-small',notes);if(sm[0]){set(q('b',sm[0]),['Build notes','निर्माण नोट']);set(q('span',sm[0]),['I keep the products grounded in actual use instead of adding features just to make the page look busy.','पृष्ठ भरिभराउ देखाउन मात्र सुविधा थप्ने होइन; वास्तविक प्रयोगमा काम लाग्ने कुरा प्राथमिकता दिन्छु।'])}if(sm[1]){set(q('b',sm[1]),['What matters most','सबैभन्दा महत्त्वपूर्ण']);set(q('span',sm[1]),['Clear workflows, useful feedback, reliable updates and fewer unnecessary steps.','स्पष्ट कामको प्रवाह, उपयोगी प्रतिक्रिया, भरपर्दो अपडेट र कम अनावश्यक चरण।'])}}

    const about=q('#about');if(about){set(q('.section-title small',about),T.about.small);set(q('.section-title h2',about),T.about.title);set(q('.about-card span',about),['Software products · Web applications · Practical prototypes','सफ्टवेयर उत्पादन · वेब अनुप्रयोग · व्यवहारिक प्रारम्भिक नमुना']);set(q('.about-copy > p',about),['I like software that solves ordinary problems without making the user feel stupid.','म त्यस्तो सफ्टवेयर बनाउन चाहन्छु जसले सामान्य समस्या समाधान गरोस् र प्रयोगकर्तालाई अनावश्यक रूपमा अलमल्याओस् होइन।']);set(q('.about-copy .small',about),['The work here is hands-on: deciding the product direction, shaping the interface, testing flows, finding what breaks and refining it until it feels clearer. The portfolio is deliberately straightforward about what is working now and what is still being improved.','यहाँको काम प्रत्यक्ष रूपमा गरिएको छ: उत्पादनको दिशा तय गर्ने, प्रयोगकर्ता अनुभव बनाउने, कामको प्रवाह परीक्षण गर्ने, कमजोरी पत्ता लगाउने र स्पष्ट नहुन्जेल सुधार गर्ने। पोर्टफोलियोमा अहिले के चलिरहेको छ र के सुधार हुँदैछ भन्ने कुरा स्पष्ट रूपमा देखाइएको छ।'])}

    const contact=q('#contact');if(contact){set(q('.about-card strong',contact),['Email','इमेल']);set(q('.about-copy > p',contact),['Building practical software, testing it properly, and improving it through real use.','व्यवहारिक सफ्टवेयर बनाउने, राम्रोसँग परीक्षण गर्ने र वास्तविक प्रयोगबाट सुधार गर्दै लैजाने।']);set(q('.about-copy .small',contact),['Based in the United Kingdom · Software products & working prototypes','युनाइटेड किंगडममा आधारित · सफ्टवेयर उत्पादन र चल्ने प्रारम्भिक नमुना'])}

    const foot=q('footer');if(foot){set(q('.foot > span',foot),['© 2026 Pujan Chapagain · Software Portfolio','© २०२६ Pujan Chapagain · सफ्टवेयर पोर्टफोलियो']);const top=q('.footlinks a[href="#top"]',foot);if(top)set(top,['Top','माथि'])}
  }

  function apply(){
    removeFalseProjects();ensureSathi();ensureSwitch();document.documentElement.lang=lang===NP?'ne':'en';qa('.lang-switch button').forEach(b=>b.classList.toggle('active',b.dataset.lang===lang));
    html(q('.hero .kicker'),T.hero.kicker);html(q('.hero h1'),T.hero.title);set(q('.hero-copy'),T.hero.copy);set(q('.board-title b'),T.hero.board);set(q('.board-title span'),T.hero.builds);
    const navMap={'#work':T.nav.work,'#teamtracker':T.nav.team,'#team-tracker':T.nav.team,'#fixcheck':T.nav.fix,'#datemate':T.nav.date,'#floodsafe':T.nav.flood,'#sathi-ai':T.nav.sathi,'#about':T.nav.about,'#contact':T.nav.contact};qa('.navlinks a').forEach(a=>{const p=navMap[a.getAttribute('href')];if(p)set(a,p)});
    const work=q('#work .section-title');if(work){set(q('small',work),T.work.small);set(q('h2',work),T.work.title);set(q('p',work),T.work.copy)}const num=q('#work .section-number');if(num)num.textContent='05';
    const contact=q('#contact .section-title');if(contact){set(q('small',contact),T.contact.small);set(q('h2',contact),T.contact.title);set(q('p',contact),T.contact.copy)}
    translateProject('#teamtracker',T.projects.team);translateProject('#fixcheck',T.projects.fix);translateProject('#datemate',T.projects.date);translateProject('#floodsafe',T.projects.flood);translateProject('#sathi-ai',T.projects.sathi);
    translateTicket('Team Tracker',T.projects.team);translateTicket('FixCheck',T.projects.fix);translateTicket('DateMate',T.projects.date);translateTicket('FloodSafe Nepal',T.projects.flood);translateTicket('SATHI AI',T.projects.sathi);
    const team=q('#teamtracker');if(team){let note=q('.portfolio-privacy-note',team);if(!note){note=document.createElement('p');note.className='portfolio-privacy-note';q('.project-copy',team)?.appendChild(note)}set(note,T.projects.team.privacy)}
    translateSathiPreview();translateStaticUI();document.dispatchEvent(new CustomEvent('portfolio:language',{detail:{lang}}));
  }

  function boot(){removeFalseProjects();ensureSathi();ensureSwitch();apply();setTimeout(apply,250);setTimeout(apply,1200)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();