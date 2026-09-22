/* NetSathi-only: keep the 18 real screenshots inside a compact, categorised viewer. */
(()=>{
  if(window.__netsathiCompactRealScreensV1)return;
  window.__netsathiCompactRealScreensV1=true;
  const style=document.createElement('style');
  style.id='netsathi-compact-real-screens-v1';
  style.textContent=`
    #netsathi-showcase .ns-screens-details{margin-top:28px;border:1px solid rgba(82,242,168,.27);border-radius:19px;background:rgba(7,19,27,.94);overflow:hidden;color:#f4f7fb}
    #netsathi-showcase .ns-screens-details>summary{list-style:none;cursor:pointer;padding:19px 21px;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:84px}
    #netsathi-showcase .ns-screens-details>summary::-webkit-details-marker{display:none}
    #netsathi-showcase .ns-screens-label{display:grid;gap:5px;min-width:0}
    #netsathi-showcase .ns-screens-label strong{font-size:1.06rem;color:#f8fffc}
    #netsathi-showcase .ns-screens-label small{color:#a6b8c4;font-size:.75rem;line-height:1.4}
    #netsathi-showcase .ns-screens-arrow{flex:none;color:#65ecc3;border:1px solid rgba(101,236,195,.35);border-radius:999px;padding:9px 12px;font-size:.73rem;font-weight:800}
    #netsathi-showcase .ns-screens-details[open] .ns-screens-arrow{background:rgba(82,242,168,.10)}
    #netsathi-showcase .ns-screens-content{border-top:1px solid rgba(255,255,255,.10);padding:17px}
    #netsathi-showcase .ns-screen-tabs{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:13px}
    #netsathi-showcase .ns-screen-tab,#netsathi-showcase .ns-screen-page-btn{appearance:none;background:#152833;border:1px solid rgba(255,255,255,.15);color:#ced9e3;border-radius:11px;padding:10px 12px;font:750 .76rem/1.25 inherit;cursor:pointer;min-height:41px}
    #netsathi-showcase .ns-screen-tab[aria-pressed="true"]{background:#52f2a8;border-color:#52f2a8;color:#071921}
    #netsathi-showcase .ns-screen-tab:focus-visible,#netsathi-showcase .ns-screen-page-btn:focus-visible,#netsathi-showcase .ns-screens-details>summary:focus-visible{outline:2px solid #52f2a8;outline-offset:3px}
    #netsathi-showcase .ns-gallery.ns-compact-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:12px!important;margin-top:0!important}
    #netsathi-showcase .ns-gallery.ns-compact-grid figure,#netsathi-showcase .ns-gallery.ns-compact-grid figure.ns-wide{grid-column:auto!important;min-width:0!important}
    #netsathi-showcase .ns-gallery.ns-compact-grid figure[hidden]{display:none!important}
    #netsathi-showcase .ns-gallery.ns-compact-grid img,#netsathi-showcase .ns-gallery.ns-compact-grid figure.ns-wide img{width:100%!important;height:165px!important;max-height:165px!important;object-fit:contain!important;object-position:center!important;background:#06101a!important;transform:none!important}
    #netsathi-showcase .ns-gallery.ns-compact-grid figcaption{padding:10px!important;font-size:.69rem!important;line-height:1.4!important}
    #netsathi-showcase .ns-gallery.ns-compact-grid figcaption b{font-size:.75rem!important}
    #netsathi-showcase .ns-screen-pages{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:14px;color:#b5c5d0;font-size:.76rem}
    #netsathi-showcase .ns-screen-page-btn:disabled{opacity:.35;cursor:not-allowed}
    #netsathi-showcase .ns-screen-help{color:#92a9b9;font-size:.73rem;margin:10px 1px 0}
    @media(max-width:700px){#netsathi-showcase .ns-screens-details{margin-top:21px}#netsathi-showcase .ns-screens-details>summary{padding:15px;min-height:76px}#netsathi-showcase .ns-screens-label strong{font-size:.96rem}#netsathi-showcase .ns-screens-arrow{font-size:.67rem;padding:8px}#netsathi-showcase .ns-screens-content{padding:12px}#netsathi-showcase .ns-screen-tab{flex:1 1 auto;padding:9px 8px;font-size:.69rem}#netsathi-showcase .ns-gallery.ns-compact-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:8px!important}#netsathi-showcase .ns-gallery.ns-compact-grid img,#netsathi-showcase .ns-gallery.ns-compact-grid figure.ns-wide img{height:135px!important;max-height:135px!important}#netsathi-showcase .ns-gallery.ns-compact-grid figcaption{padding:8px!important;font-size:.63rem!important}#netsathi-showcase .ns-gallery.ns-compact-grid figcaption b{font-size:.68rem!important}#netsathi-showcase .ns-screen-pages{font-size:.69rem}}
  `;
  document.head.appendChild(style);

  function install(){
    const section=document.getElementById('netsathi-showcase');
    if(!section)return false;
    if(section.querySelector('.ns-screens-details'))return true;
    const gallery=section.querySelector('.ns-gallery');
    const title=section.querySelector('.ns-gallery-title');
    if(!gallery||!title)return false;
    const details=document.createElement('details');
    details.className='ns-screens-details';
    details.id='netsathi-real-screens';
    const summary=document.createElement('summary');
    summary.innerHTML='<span class="ns-screens-label"><strong>📸 Real Screenshots</strong><small>18 actual NetSathi screens · organised by app</small></span><span class="ns-screens-arrow" aria-hidden="true">View screenshots ↓</span>';
    details.appendChild(summary);
    const body=document.createElement('div');
    body.className='ns-screens-content';
    const tabs=document.createElement('div');
    tabs.className='ns-screen-tabs';
    tabs.setAttribute('role','group');
    tabs.setAttribute('aria-label','Screenshot category');
    const categories=[['control-room','Control Room'],['customer','Customer App'],['technician','Technician App']];
    const buttons=categories.map(([key,label])=>{
      const b=document.createElement('button');
      b.type='button';b.className='ns-screen-tab';b.dataset.category=key;
      b.setAttribute('aria-pressed',key==='control-room'?'true':'false');
      b.textContent=label;
      tabs.appendChild(b);
      return b;
    });
    body.appendChild(tabs);
    gallery.classList.add('ns-compact-grid');
    body.appendChild(gallery);
    const pages=document.createElement('div');
    pages.className='ns-screen-pages';
    const prev=document.createElement('button');prev.type='button';prev.className='ns-screen-page-btn';prev.textContent='← Previous';
    const count=document.createElement('span');count.setAttribute('aria-live','polite');
    const next=document.createElement('button');next.type='button';next.className='ns-screen-page-btn';next.textContent='Next →';
    pages.append(prev,count,next);body.appendChild(pages);
    const help=document.createElement('p');help.className='ns-screen-help';help.textContent='Tap a screenshot to view it full size.';body.appendChild(help);
    details.appendChild(body);
    title.replaceWith(details);
    let category='control-room',page=0;
    const perPage=4;
    let ready=false;
    function render(){
      const figures=[...gallery.querySelectorAll('figure')];
      if(figures.length!==18||figures.some(f=>!(/\.webp(?:\?|$)/i.test(f.querySelector('img')?.getAttribute('src')||'')))){
        if(!ready)count.textContent='Loading screenshots…';
        return;
      }
      ready=true;
      const matched=figures.filter(f=>{
        const file=(f.querySelector('img').getAttribute('src')||'').split('/').pop().split('?')[0];
        return file.startsWith(category+'-');
      });
      const totalPages=Math.max(1,Math.ceil(matched.length/perPage));
      page=Math.max(0,Math.min(page,totalPages-1));
      const visible=new Set(matched.slice(page*perPage,(page+1)*perPage));
      figures.forEach(f=>{f.hidden=!visible.has(f);});
      buttons.forEach(b=>{
        const key=b.dataset.category;
        const n=figures.filter(f=>(f.querySelector('img').getAttribute('src')||'').split('/').pop().startsWith(key+'-')).length;
        b.textContent=categories.find(c=>c[0]===key)[1]+' ('+n+')';
        b.setAttribute('aria-pressed',String(category===key));
      });
      count.textContent='Page '+(page+1)+' of '+totalPages+' · '+matched.length+' screenshots';
      prev.disabled=page===0;next.disabled=page>=totalPages-1;
      pages.hidden=totalPages<2;
    }
    buttons.forEach(b=>b.addEventListener('click',()=>{category=b.dataset.category;page=0;render();}));
    prev.addEventListener('click',()=>{if(page>0){page--;render();}});
    next.addEventListener('click',()=>{page++;render();});
    const observer=new MutationObserver(()=>render());
    observer.observe(gallery,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
    render();
    const link=document.querySelector('#netsathi .project-links a[href="#netsathi-showcase"]');
    if(link){link.textContent='Real Screenshots (18) ↓';link.href='#netsathi-real-screens';link.addEventListener('click',()=>{details.open=true;setTimeout(()=>details.scrollIntoView({block:'start',behavior:'smooth'}),0);});}
    if(location.hash==='#netsathi-real-screens')details.open=true;
    details.addEventListener('toggle',()=>{const a=summary.querySelector('.ns-screens-arrow');if(a)a.textContent=details.open?'Hide screenshots ↑':'View screenshots ↓';});
    document.addEventListener('keydown',e=>{
      if(e.key!=='Escape')return;
      const overlay=section.querySelector('.ns-lightbox.open');
      if(overlay){overlay.classList.remove('open');overlay.setAttribute('aria-hidden','true');overlay.querySelector('img')?.removeAttribute('src');}
    });
    return true;
  }
  if(!install()){
    const observer=new MutationObserver(()=>{if(install())observer.disconnect();});
    observer.observe(document.documentElement,{childList:true,subtree:true});
    document.addEventListener('DOMContentLoaded',install,{once:true});
  }
})();
