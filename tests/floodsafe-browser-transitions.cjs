const assert=require('node:assert/strict');

// Browser-only intercepted fixtures. Never written to the live data services.
module.exports=async function verifyTransitions(browser,base){
  const page=await browser.newPage();await page.setViewport({width:412,height:915});
  let phase='old';const now=Date.now(),fresh=new Date(now-60000).toISOString(),old=new Date(now-86400000).toISOString();
  await page.setRequestInterception(true);
  page.on('request',req=>{
    const url=req.url(),edge=url.includes('.supabase.co/functions/v1/');
    if(phase==='offline'&&(edge||url.includes('bipadportal.gov.np/api/')))return void req.abort();
    const time=phase==='old'?old:fresh;
    let payload;
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
    await page.waitForFunction(()=>document.getElementById('liveNews').innerText.includes('No fresh data')&&document.getElementById('impactFresh').innerText.includes('Latest reported figures'));
    assert.equal(await page.$eval('#impactDeaths',e=>e.innerText),'12');
    assert.equal(await page.evaluate(()=>window.__fsRiverRealtimeState.currentCount),0);

    await page.evaluate(()=>{window.FloodSafe.state.lat=28;window.FloodSafe.state.lon=85});
    phase='fresh';
    await page.evaluate(()=>{window.FloodSafeNews.refresh();window.FloodSafeRiverRealtime.refresh();void window.FloodSafeImpact.sync()});
    await page.waitForFunction(()=>window.__fsRiverRealtimeState?.currentCount===1&&window.__fsNewsLiveState?.freshCount===1&&document.getElementById('impactDeaths').innerText==='13',{timeout:30000});
    await page.waitForFunction(()=>document.getElementById('nearStations').innerText.includes('6 m')&&document.getElementById('nearCheck')?.innerText.includes('Auto-check active'),{timeout:10000});
    console.log('PASS nearby list receives new source reading without page reload');
    assert.equal(await page.evaluate(()=>window.FloodSafe.state.currentRiverStations[0]._derivedStatus),'warning');
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
