const assert=require('node:assert/strict');

// Browser-only intercepted fixtures. Never written to the live data services.
module.exports=async function verifyTransitions(browser,base){
  const page=await browser.newPage();await page.setViewport({width:412,height:915});
  page.on('pageerror',e=>console.log('TRANSITION PAGE ERROR',String(e)));
  page.on('console',m=>{if(m.type()==='error')console.log('TRANSITION CONSOLE',m.text())});
  let phase='old';const now=Date.now(),fresh=new Date(now-60000).toISOString(),old=new Date(now-86400000).toISOString();
  let tileRecoveryAllowed=false,tileFailures=0;
  const river=id=>({id,name:'TEST ONLY '+id,type:'stream',pts:id==='overview'?[[84.5,27.8],[85.5,28.2]]:id==='right'?[[85.01,28.02],[85.05,28.03]]:[[84.95,28.02],[84.99,28.03]]});
  await page.setRequestInterception(true);
  page.on('request',req=>{
    const url=req.url(),edge=url.includes('.supabase.co/functions/v1/');
    if(phase==='offline'&&(edge||url.includes('bipadportal.gov.np/api/')))return void req.abort();
    const time=phase==='old'?old:fresh;
    let payload;
    if(url.includes('/nepal-waterways-tiles/')){
      if(url.includes('manifest.json'))payload={minLon:80,minLat:26,stepLon:5,stepLat:5,nx:2,ny:1,tiles:{'0-0':{},'1-0':{}}};
      else if(url.includes('overview.json'))payload={waterways:[river('overview')]};
      else if(url.includes('/0-0.json')&&!tileRecoveryAllowed){tileFailures++;return void req.abort()}
      else payload={waterways:[river(url.includes('/0-0.json')?'left':'right')]};
      return void req.respond({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(payload)});
    }
    if(url.includes('/functions/v1/sync-bipad-rivers'))payload={fetched_at:new Date(now).toISOString(),results:[{stationSeriesId:987654,title:'TEST ONLY river',waterLevel:phase==='old'?2:6,waterLevelOn:time,warningLevel:5,dangerLevel:7,longitude:85,latitude:28}]};
    else if(url.includes('/functions/v1/news-live-three'))payload={items:[{title:'TEST ONLY timestamped flood report',source:'Radio Nepal',url:'https://radionepalonline.com/floodsafe-test-only',published_at:time}],sources:{'Radio Nepal':{ok:true,items:1,newest:time}}};
    else if(url.includes('/functions/v1/human-status-safe-live'))payload={event:'TEST ONLY flood',recovered_bodies:phase==='old'?12:13,recovered_source:'Radio Nepal',recovered_source_url:'https://radionepalonline.com/floodsafe-test-only',recovered_update_time:time};
    else if(/floodsafe-core\.json/.test(url))payload={river_stations:[],rivers:[]};
    else if(/floodsafe-(?:news|people-status)\.json/.test(url))payload={};
    if(payload!==undefined)return void req.respond({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(payload)});
    void req.continue();
  });
  try{
    await page.goto(base+'?fixture-transition='+now,{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForFunction(()=>window.__fsRiverRealtimeState?.connected&&window.__fsNewsLiveState?.lastSuccess&&window.__fsImpactLiveState?.lastSuccess,{timeout:45000});
    await page.evaluate(()=>{window.FloodSafe.state.lang='en';window.dispatchEvent(new Event('fslanguage'))});
    await page.waitForFunction(()=>document.getElementById('newsTip')&&document.getElementById('impactFresh').innerText.includes('Latest reported figures'));
    assert.equal(await page.$eval('#impactDeaths',e=>e.innerText),'12');
    assert.equal(await page.evaluate(()=>window.__fsRiverRealtimeState.currentCount),0);

    await page.waitForFunction(()=>window.FloodSafeMobileMap&&document.getElementById('fsOpenMapBtn'));
    assert.equal(await page.evaluate(()=>window.FloodSafeMobileMap.isOpen),false);
    await page.$eval('#fsOpenMapBtn',e=>e.scrollIntoView({block:'center',behavior:'instant'}));
    await page.locator('#fsOpenMapBtn').click();

    // The hydro source can exist before map initialisation's final Nepal fitBounds.
    // Wait for gauges/districts too so that initial fit cannot undo our test zoom.
    await page.waitForFunction(()=>window.FloodSafeHydroSmooth&&window.FloodSafeMap?.initialized&&window.FloodSafeMap?.map?.getSource('gauges')&&window.FloodSafeMap.map.getSource('hydro-complete'),{timeout:45000});
    await page.$eval('#riverMapGL',e=>e.scrollIntoView({block:'center',behavior:'instant'}));
    await page.evaluate(()=>{window.FloodSafeMap.map.on('error',e=>console.error('FIXTURE MAP ERROR',e.error?.message||String(e.error)));window.FloodSafeMap.map.resize();window.FloodSafeMap.map.jumpTo({center:[85,28],zoom:9})});
    try{await page.waitForFunction(()=>window.FloodSafeHydroSmooth.loadingState.failedVisibleTiles===1,{timeout:20000})}
    catch(e){console.log('RIVER TILE DIAGNOSTICS',JSON.stringify({tileFailures,state:await page.evaluate(()=>({loading:window.FloodSafeHydroSmooth?.loadingState,zoom:window.FloodSafeMap?.map?.getZoom(),manifest:window.FloodSafeHydroSmooth?.manifest,visible:!document.hidden}))}));throw e}
    try{await page.waitForFunction(()=>window.FloodSafeMap.map.querySourceFeatures('hydro-complete').some(f=>f.properties.id==='overview'),{timeout:10000})}
    catch(e){console.log('RIVER RENDER DIAGNOSTICS',JSON.stringify(await page.evaluate(()=>{const m=window.FloodSafeMap.map,c=m.style.sourceCaches['hydro-complete'];return{zoom:m.getZoom(),center:m.getCenter(),canvas:m.getCanvas().getBoundingClientRect().toJSON(),loading:window.FloodSafeHydroSmooth.loadingState,data:m.getStyle().sources['hydro-complete'].data,rendered:m.querySourceFeatures('hydro-complete'),sourceLoaded:m.isSourceLoaded('hydro-complete'),sourceUsed:c.used,tiles:Object.values(c._tiles).map(t=>({state:t.state,id:t.tileID})),layers:m.getStyle().layers.filter(l=>l.source==='hydro-complete')}})));throw e}
    assert.ok(tileFailures>=1);
    tileRecoveryAllowed=true; // No refresh or pan: the scheduled retry must recover it.
    await page.waitForFunction(()=>window.FloodSafeHydroSmooth.loadingState.loadedVisibleTiles===2&&window.FloodSafeHydroSmooth.loadingState.failedVisibleTiles===0,{timeout:65000});
    await page.waitForFunction(()=>['left','right'].every(id=>window.FloodSafeMap.map.querySourceFeatures('hydro-complete').some(f=>f.properties.id===id)),{timeout:15000});
    const streamStyle=await page.evaluate(()=>({
      color:window.FloodSafeMap.map.getPaintProperty('hydro-complete-lines','line-color'),
      opacity:window.FloodSafeMap.map.getPaintProperty('hydro-complete-lines','line-opacity'),
      states:window.FloodSafeMap.map.querySourceFeatures('hydro-complete').map(f=>f.properties.live_status)
    }));
    assert.equal(streamStyle.color.at(-1),'#cbd5e1');assert.equal(streamStyle.opacity.at(-1),.88);
    assert.ok(streamStyle.states.every(s=>s==='unknown'));
    await page.evaluate(()=>{const m=window.FloodSafeMap.map;m.jumpTo({center:[84.4,28.2],zoom:10});m.jumpTo({center:[85,28],zoom:6})});
    await page.waitForFunction(()=>window.FloodSafeHydroSmooth.loadingState.mode==='overview'&&window.FloodSafeMap.map.querySourceFeatures('hydro-complete').some(f=>f.properties.id==='overview'),{timeout:15000});
    console.log('PASS mobile river detail: failed tile retries without refresh, overview retained, recovered streams visible grey, pan/zoom still responds');

    await page.evaluate(()=>{window.FloodSafe.state.lat=28;window.FloodSafe.state.lon=85});
    const firstTip=await page.$eval('#newsTip',e=>e.dataset.tipIndex);
    assert.ok(firstTip!==undefined);
    phase='fresh';
    await page.evaluate(()=>{window.FloodSafeNews.refresh();window.FloodSafeRiverRealtime.refresh();void window.FloodSafeImpact.sync()});
    await page.waitForFunction(()=>window.__fsRiverRealtimeState?.currentCount===1&&window.__fsNewsLiveState?.freshCount===1&&document.getElementById('impactDeaths').innerText==='13',{timeout:30000});
    await page.waitForFunction(()=>document.getElementById('nearStations').innerText.includes('6 m')&&document.getElementById('nearCheck')?.innerText.includes('Auto-check active'),{timeout:10000});
    console.log('PASS nearby list receives new source reading without page reload');
    assert.equal(await page.evaluate(()=>window.FloodSafe.state.currentRiverStations[0]._derivedStatus),'warning');
    assert.equal(await page.$('#newsTip'),null);
    assert.ok(!(await page.$eval('#liveNews',e=>e.innerText)).includes('No fresh data'));

    // Advance the browser clock without changing source timestamps. A new
    // successful check must not make those now-expired observations fresh.
    await page.evaluate(()=>{const RealDate=Date;window.Date=class extends RealDate{constructor(...a){super(...(a.length?a:[RealDate.now()+11*60000]))}static now(){return RealDate.now()+11*60000}}});
    await page.evaluate(()=>{window.FloodSafeNews.refresh();window.FloodSafeRiverRealtime.refresh();void window.FloodSafeImpact.sync()});
    await page.waitForFunction(()=>window.__fsRiverRealtimeState?.currentCount===1&&window.__fsNewsLiveState?.freshCount===0&&window.__fsImpactLiveState?.reportedCount===1,{timeout:30000});
    assert.equal(await page.$eval('#impactDeaths',e=>e.innerText),'13');
    assert.match(await page.$eval('#liveNews',e=>e.innerText),/No fresh data/);
    assert.equal(await page.$eval('#impactDeaths',e=>e.textContent),'13');
    assert.equal(await page.evaluate(()=>window.FloodSafe.state.allRiverStations[0]._lastKnownObservation.level),6);

    phase='offline';
    await page.evaluate(()=>{window.FloodSafeNews.refresh();window.FloodSafeRiverRealtime.refresh();void window.FloodSafeImpact.sync()});
    await page.waitForFunction(()=>window.__fsRiverRealtimeState?.connected===false&&window.__fsNewsLiveState?.connected===false&&window.__fsImpactLiveState?.connected===false,{timeout:30000});
    assert.equal(await page.evaluate(()=>window.FloodSafe.state.allRiverStations[0]._lastKnownObservation.level),6);
    assert.equal(await page.$eval('#impactDeaths',e=>e.textContent),'13');
    console.log('PASS intercepted browser transitions: stale -> fresh -> expired -> offline; source times and last-good values preserved');
  }finally{await page.close()}
};
