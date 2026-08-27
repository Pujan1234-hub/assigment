document.addEventListener('DOMContentLoaded',()=>{
  if(document.getElementById('floodsafe')) return;

  // Keep the public portfolio count current.
  document.querySelectorAll('.stat').forEach(el=>{
    if((el.textContent||'').includes('Active products')){
      const strong=el.querySelector('strong'); if(strong) strong.textContent='03';
    }
  });

  // Add navigation link.
  const nav=document.querySelector('.links');
  if(nav && !nav.querySelector('a[href="#floodsafe"]')){
    const platforms=nav.querySelector('a[href="#platforms"]');
    const a=document.createElement('a'); a.href='#floodsafe'; a.textContent='FloodSafe Nepal';
    if(platforms) nav.insertBefore(a,platforms); else nav.appendChild(a);
  }

  // Make 3 product cards fit cleanly.
  const style=document.createElement('style');
  style.textContent='.cards{grid-template-columns:repeat(3,1fr)}@media(max-width:850px){.cards{grid-template-columns:1fr}}';
  document.head.appendChild(style);

  // Add product card.
  const cards=document.querySelector('#products .cards');
  if(cards){
    const card=document.createElement('article');
    card.className='card';
    card.innerHTML=`
      <div class="cardhead"><div class="icon">🌊</div><span class="status amber">Active Development</span></div>
      <h3>FloodSafe Nepal</h3>
      <div class="sub">नेपालका लागि local flood & river alert platform</div>
      <p>A Nepal-focused safety app built around local-area flood awareness, live river-station updates and map-first risk context.</p>
      <ul class="features">
        <li>Nepal-only detailed map experience</li>
        <li>Local-area alerts for the place that matters to the user</li>
        <li>Official river-station and warning data with frequent refresh</li>
        <li>Current update time and visible data freshness</li>
        <li>Nepali-first interface and recognisable alert experience</li>
      </ul>
      <div class="miniui"><div class="mocktop"><span class="pill">FloodSafe Nepal</span><span class="ok">Latest live build</span></div>
      <div class="rows"><div class="row"><span>Nearby river stations</span><b class="ok">Refreshing</b></div><div class="row"><span>Local risk</span><b>Area based</b></div><div class="row"><span>Map</span><b>Nepal only</b></div></div></div>
      <div class="actions"><a class="btn primary" href="./floodsafe-nepal/">Open web app ↗</a><a class="btn" href="#floodsafe">Product details</a></div>`;
    cards.appendChild(card);
  }

  // Add full product detail before platform section.
  const platforms=document.getElementById('platforms');
  if(platforms){
    const sec=document.createElement('section');
    sec.id='floodsafe';
    sec.innerHTML=`<div class="wrap">
      <div class="productHead"><div><div class="k">Product 03 · Active Development</div><h2 class="productTitle">FloodSafe Nepal</h2>
      <p class="lead" style="font-size:17px">A Nepal-first flood and river-awareness platform designed to make nearby risk easier to understand through a detailed Nepal map, local-area alerts, live station updates and clear data freshness.</p>
      <div class="actions"><a class="btn primary" href="./floodsafe-nepal/">Launch latest web app ↗</a></div></div>
      <div class="summary"><div class="sitem"><strong>Product type</strong><span>Public safety / flood awareness web app and PWA direction</span></div><div class="sitem"><strong>Main focus</strong><span>Nearby river conditions, local-area warnings and map-based situational awareness</span></div><div class="sitem"><strong>Geographic focus</strong><span>Nepal only — detailed national map rather than a world map</span></div><div class="sitem"><strong>Current status</strong><span>Active development · working web build</span></div></div></div>
      <div class="three"><div class="box"><h3>The problem</h3><p>Broad national warnings can be less useful when someone mainly needs to know what is happening around their own home, route or current area.</p></div><div class="box"><h3>How it works</h3><p>The app combines a Nepal-focused map with frequently refreshed river/station information, local-area context and visible update timing.</p></div><div class="box"><h3>Product direction</h3><p>Keep the interface Nepali-first, make station refresh obvious and surface meaningful nearby risk without unrelated alert noise.</p></div></div>
      <div class="flow"><div class="step"><b>1. Choose or use an area</b><span>The user focuses the map on the place that matters to them.</span></div><div class="step"><b>2. See live context</b><span>Nearby stations and warning information refresh against the Nepal map.</span></div><div class="step"><b>3. Get a local alert</b><span>The app surfaces meaningful risk for that area instead of unrelated national noise.</span></div></div>
      <div class="note">FloodSafe Nepal is an active safety-oriented prototype. Public warnings should always be cross-checked with official emergency information.</div>
    </div>`;
    platforms.parentNode.insertBefore(sec,platforms);
  }

  const foot=document.querySelector('.footlinks');
  if(foot && !foot.querySelector('a[href="./floodsafe-nepal/"]')){
    const a=document.createElement('a'); a.href='./floodsafe-nepal/'; a.textContent='FloodSafe Nepal'; foot.appendChild(a);
  }
});