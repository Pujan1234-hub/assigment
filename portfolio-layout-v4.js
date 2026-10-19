/* PJBUILTS Portfolio V4 — layout restructure only.
   Existing project, gallery, links, contact form and scripts are retained. */
(()=>{
  if(window.__pjPortfolioEditorialV4) return;
  window.__pjPortfolioEditorialV4=true;

  function el(tag,className,text){
    const item=document.createElement(tag);
    if(className)item.className=className;
    if(text!==undefined)item.textContent=text;
    return item;
  }

  function relayout(){
    const hero=document.querySelector('#home.hero');
    const work=document.querySelector('#work > .wrap');
    if(!hero||!work||document.documentElement.dataset.pjLayout==='editorial-v4')return;
    const grid=hero.querySelector('.hero-grid');
    const headline=grid?.querySelector('h1');
    const visual=grid?.querySelector('.hero-visual');
    const head=work.querySelector(':scope > .section-head');
    const projects=work.querySelector(':scope > .project-list');
    if(!grid||!headline||!visual||!head||!projects)return;

    // Preserve the original first-name span, subtitle span and text contents.
    const first=headline.querySelector('.grad');
    const subtitle=headline.querySelector('.thin');
    if(first&&subtitle&&!headline.querySelector('.pj-last-name')){
      const middle=el('span','pj-last-name','Chapagain');
      headline.replaceChildren(first,middle,subtitle);
    }

    // A new studio navigation panel replaces the old code demonstration hero.
    const showcase=el('aside','pj-hero-showcase');
    showcase.setAttribute('aria-label','Featured PJBUILTS work');
    showcase.innerHTML=`
      <div class="pj-showcase-top"><span class="pj-showcase-identity">P<span>J</span></span><span class="pj-showcase-edition">INDEPENDENT PRODUCT STUDIO<br>2026 / PORTFOLIO</span></div>
      <div class="pj-showcase-title">Digital products.<br><em>Real-world purpose.</em></div>
      <div class="pj-showcase-links">
        <a href="#floodsafe"><span>01 / PUBLIC SAFETY</span><strong>FloodSafe Nepal</strong><span aria-hidden="true">↗</span></a>
        <a href="#netsathi"><span>02 / ISP SUPPORT</span><strong>NetSathi</strong><span aria-hidden="true">↗</span></a>
        <a href="#datemate"><span>03 / ANDROID</span><strong>DateMate</strong><span aria-hidden="true">↗</span></a>
      </div>
      <div class="pj-showcase-footer"><span>DESIGNED · BUILT · TESTED</span><span aria-hidden="true">↗</span></div>`;
    grid.appendChild(showcase);

    // Do not destroy the original decorative code illustration. Keep it
    // available as an expandable technical snapshot rather than the hero.
    const archive=el('details','pj-technical-snapshot');
    const summary=el('summary','','Technical snapshot — original developer illustration');
    archive.appendChild(summary);
    archive.appendChild(visual);
    hero.insertAdjacentElement('afterend',archive);

    const intro=el('div','pj-work-intro');
    projects.insertAdjacentElement('beforebegin',intro);
    intro.appendChild(head);
    const stage=el('div','pj-work-stage');
    intro.insertAdjacentElement('afterend',stage);
    const rail=el('aside','pj-project-rail');
    const kicker=el('span','pj-rail-kicker','WORK / INDEX');
    const list=el('nav','pj-project-index');
    list.setAttribute('aria-label','Jump to projects');
    rail.append(kicker,list);
    stage.append(rail,projects);

    const counter=document.querySelector('.hero-stats .stat strong');
    function syncIndex(){
      const articles=[...projects.querySelectorAll(':scope > article.project[id]')];
      const signature=articles.map(a=>a.id+':'+(a.querySelector('h3')?.textContent||'')).join('|');
      if(list.dataset.signature===signature)return;
      list.dataset.signature=signature;
      list.replaceChildren(...articles.map((card,i)=>{
        const link=el('a','pj-project-index-link');
        link.href='#'+card.id;
        const num=el('span','pj-project-index-num',String(i+1).padStart(2,'0'));
        const label=el('span','pj-project-index-name',card.querySelector('h3')?.textContent?.trim()||card.id);
        link.append(num,label);
        return link;
      }));
      // Project count is updated by the existing runtime; the new panel
      // derives navigation from actual project cards, never assumes a count.
    }
    syncIndex();
    new MutationObserver(syncIndex).observe(projects,{childList:true});

    document.documentElement.dataset.pjLayout='editorial-v4';
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',relayout,{once:true});
  }else{
    relayout();
  }
  // Other PJBUILTS scripts create additional cards asynchronously. Reattempt
  // only initialization, never modify cards, galleries or form elements.
  let retry=0;
  const timer=setInterval(()=>{
    if(document.documentElement.dataset.pjLayout==='editorial-v4'||retry++>30)clearInterval(timer);
    else relayout();
  },150);
})();
