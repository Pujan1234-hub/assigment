(()=>{
  if(window.__pjNetSathiRealScreensV2)return;
  window.__pjNetSathiRealScreensV2=true;
  const dir='./assets/portfolio/netsathi-real/';
  const screens=[
    ['control-room-dashboard-map.webp','Control Room dashboard','Live dispatch map and technician availability',true],
    ['control-room-ticket-operations.webp','Ticket operations','Service requests, priority, assignment and ETA',true],
    ['customer-report-problem.webp','Customer: report a problem','Enter the issue, location and attach a photograph',false],
    ['technician-assigned.webp','Technician: assigned job','View the new job, customer photo and accept it',false],
    ['control-room-route.webp','Live dispatch route','Demo route displayed in the Control Room',true],
    ['customer-open-ticket.webp','Customer: request submitted','New ticket and issue photograph appear in My tickets',false],
    ['control-room-technician-operations.webp','Field technician operations','Workload, assignment and photo evidence',true],
    ['control-room-technician-status.webp','Technician status and photos','Field sync, availability and ticket overview',true],
    ['control-room-dispatch-status.webp','Active dispatch overview','Customer and demo-technician markers with route',true],
    ['control-room-recent-tickets.webp','Recent ticket overview','Status, ETA and technician assignment in the dashboard',true],
    ['control-room-overview.webp','Mobile Control Room dashboard','Responsive dashboard and satellite dispatch map',false],
    ['customer-accepted-notification.webp','Customer: accepted notification','Android notification for job acceptance',false],
    ['customer-on-way-notification.webp','Customer: on-way notification','Android notification after technician sets On Way',false],
    ['customer-on-way-gps.webp','Customer: technician location','Live field position and estimated arrival',false],
    ['technician-fixed-await-confirm.webp','Technician: fixed','Repair marked fixed and awaiting customer confirmation',false],
    ['customer-fixed-confirm.webp','Customer: confirm repair','Customer sees fixed status and confirmation action',false],
    ['customer-closed.webp','Customer: ticket closed','Confirmed repair and completed service request',false],
    ['technician-ready-closed.webp','Technician: completed jobs','Ready for dispatch after customer closes the ticket',false]
  ];
  let attempted=false;
  function apply(){
    const gallery=document.querySelector('#netsathi-showcase .ns-gallery');
    if(!gallery||attempted)return;
    attempted=true;
    const probe=new Image();
    probe.onload=()=>{
      const hero=document.querySelector('#netsathi .ns-visual-wrap img');
      if(hero){hero.src=dir+'control-room-dashboard-map.webp';hero.alt='Real NetSathi Control Room dashboard and live dispatch map';}
      const figures=[...gallery.querySelectorAll('figure')];
      const lightbox=document.querySelector('#netsathi-showcase .ns-lightbox');
      const lightboxImg=lightbox&&lightbox.querySelector('img');
      screens.forEach(([file,title,description,wide],i)=>{
        let figure=figures[i];
        if(!figure){
          figure=document.createElement('figure');
          if(wide)figure.classList.add('ns-wide');
          const image=document.createElement('img');
          image.loading='lazy';image.decoding='async';
          figure.appendChild(image);
          const caption=document.createElement('figcaption');
          figure.appendChild(caption);
          gallery.appendChild(figure);
          image.addEventListener('click',()=>{
            if(!lightbox||!lightboxImg)return;
            lightboxImg.src=image.src;
            lightbox.classList.add('open');
            lightbox.setAttribute('aria-hidden','false');
          });
        }
        const image=figure.querySelector('img');
        const oldSrc=image.getAttribute('src');
        if(wide)figure.classList.add('ns-wide');else figure.classList.remove('ns-wide');
        image.src=dir+file;
        image.alt=title+' — real NetSathi prototype screenshot';
        image.loading='lazy';image.decoding='async';
        image.onerror=()=>{if(i<figures.length&&oldSrc){image.onerror=null;image.src=oldSrc;}else figure.remove();};
        const caption=figure.querySelector('figcaption');
        if(caption){caption.textContent='';const bold=document.createElement('b');bold.textContent=title;caption.append(bold,document.createTextNode(description));}
      });
      const css=document.createElement('style');
      css.id='netsathi-real-screen-gallery-style';
      css.textContent='#netsathi-showcase .ns-gallery img{height:min(540px,60vw);object-fit:contain;object-position:center}#netsathi-showcase .ns-gallery figure.ns-wide img{height:min(600px,65vw)}@media(max-width:700px){#netsathi-showcase .ns-gallery img,#netsathi-showcase .ns-gallery figure.ns-wide img{height:440px}}';
      if(!document.getElementById(css.id))document.head.appendChild(css);
    };
    probe.onerror=()=>{attempted=false;};
    probe.src=dir+screens[0][0];
  }
  apply();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});
  setTimeout(apply,250);
  setTimeout(apply,1000);
  const observer=new MutationObserver(apply);
  observer.observe(document.documentElement,{childList:true,subtree:true});
})();

// Preserve the existing SVG image hydration until the screenshot assets are uploaded.
(()=>{
  if(window.__pjNetSathiPhotoFixV1)return;
  window.__pjNetSathiPhotoFixV1=true;
  const seen=new WeakSet();
  async function hydrate(img){
    if(!img||seen.has(img))return;
    const raw=img.getAttribute('src')||'';
    if(!/netsathi-[^/?]+\.svg/i.test(raw))return;
    seen.add(img);
    try{
      const clean=raw.split('?')[0];
      const url=new URL(clean,location.href);
      const r=await fetch(url.href+(url.search?'&':'?')+'photo='+Date.now(),{cache:'no-store'});
      if(!r.ok)throw new Error('HTTP '+r.status);
      const svg=await r.text();
      const m=svg.match(/(?:href|xlink:href)=["'](data:image\/(?:jpeg|jpg|png);base64,[^"']+)["']/i);
      if(!m)throw new Error('embedded photo not found');
      img.src=m[1];
      img.loading='eager';
      img.decoding='async';
      img.style.display='block';
      img.style.visibility='visible';
      img.style.opacity='1';
      img.style.minHeight='0';
      img.style.objectFit='contain';
      img.dataset.netsathiRealPhoto='1';
    }catch(err){
      seen.delete(img);
      console.warn('NetSathi photo hydrate failed',raw,err);
    }
  }
  function apply(){document.querySelectorAll('#netsathi img,#netsathi-showcase img').forEach(hydrate);}
  apply();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});
  setTimeout(apply,100);
  setTimeout(apply,500);
  setTimeout(apply,1200);
  setTimeout(apply,3000);
  const mo=new MutationObserver(apply);
  mo.observe(document.documentElement,{childList:true,subtree:true});
})();