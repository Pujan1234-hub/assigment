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

  function apply(){
    document.querySelectorAll('#netsathi img,#netsathi-showcase img').forEach(hydrate);
  }

  apply();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});
  setTimeout(apply,100);
  setTimeout(apply,500);
  setTimeout(apply,1200);
  setTimeout(apply,3000);
  const mo=new MutationObserver(apply);
  mo.observe(document.documentElement,{childList:true,subtree:true});
})();
