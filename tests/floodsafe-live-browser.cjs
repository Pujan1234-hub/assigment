const puppeteer=require('puppeteer-core');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await puppeteer.launch({executablePath:process.env.CHROME,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  try {
    const page=await browser.newPage();await page.setViewport({width:412,height:915});
    const errors=[];page.on('pageerror',e=>{errors.push(String(e));console.log('PAGE ERROR',String(e))});page.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text())});
    await page.goto((process.env.FLOODSAFE_URL||'https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/')+'?refresh-verification='+Date.now(),{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForFunction(()=>window.FloodSafeRiverRealtime&&window.FloodSafeImpact&&window.FloodSafeNews,{timeout:45000});
    await page.waitForFunction(()=>window.__fsRiverRealtimeState?.catalogCount>=100&&window.__fsImpactLiveState?.lastSuccess&&window.__fsNewsLiveState?.lastSuccess,{timeout:60000});
    await page.waitForFunction(()=>window.FloodSafeMap?.map?.isStyleLoaded?.()||window.__fsStaticMapFallback?.active,{timeout:60000});
    const read=()=>page.evaluate(()=>({
      river:window.__fsRiverRealtimeState,
      news:window.__fsNewsLiveState,
      impact:window.__fsImpactLiveState,
      mapVisible:document.querySelector('.mapCanvas').getBoundingClientRect().height>0,
      mapClosed:document.getElementById('map').classList.contains('fsMapClosed'),
      gauges:window.FloodSafeMap?.map?.querySourceFeatures?.('gauges')?.length||window.__fsStaticMapFallback?.stations||0,
      oldHumanScript:!!document.querySelector('script[src*="flood-freshness.js"]'),
      newsText:document.getElementById('liveNews').innerText.slice(0,400),
      checkText:document.getElementById('feedFresh').innerText
    }));
    console.log('MAP DIAGNOSTICS',await page.evaluate(()=>({render:window.__fsGaugeRenderState,style:window.FloodSafeMap?.map?.getStyle?.()?.sources,sourceFeatures:window.FloodSafeMap?.map?.querySourceFeatures?.('gauges')?.length})));
    // Style readiness precedes the first asynchronous station-source update.
    await page.waitForFunction(()=>((window.FloodSafeMap?.map?.querySourceFeatures?.('gauges')?.length||window.__fsStaticMapFallback?.stations||0)>=100),{timeout:15000});
    const before=await read();assert.equal(before.mapClosed,false);assert.equal(before.mapVisible,true);assert.equal(before.oldHumanScript,false);assert.ok(before.gauges>=100,JSON.stringify(before));
    const layout=await page.evaluate(()=>{const r=document.querySelector('.bottom').getBoundingClientRect();return {left:r.left,right:r.right,width:innerWidth,actions:getComputedStyle(document.querySelector('.actions')).position}});
    assert.ok(layout.left>=-1&&layout.right<=layout.width+1,JSON.stringify(layout));
    assert.equal(layout.actions,'static','mobile actions must not cover the content');
    const mapSafety=await page.evaluate(()=>({paint:window.FloodSafeMap?.map?.getPaintProperty('gauges-live-281','circle-color'),historical:(window.FloodSafe.state.allRiverStations||[]).filter(x=>x._catalogueOnly&&x._lastKnownObservation).length}));
    if(!await page.evaluate(()=>window.__fsStaticMapFallback?.active)){
      assert.ok(JSON.stringify(mapSafety.paint).includes('has_latest'),'paint must check observation presence');
      assert.ok(JSON.stringify(mapSafety.paint).includes('age_ms'),'paint must check observation age');
    }
    console.log('PASS mobile bounds and map safety',JSON.stringify({layout,mapSafety}));
    const historicalPanel=await page.evaluate(()=>{
      const o=window.FloodSafe.state.allRiverStations.find(x=>x._catalogueOnly&&x._lastKnownObservation);
      if(!o)return null;
      const api=window.FloodSafeRiverRealtime,c=api.coords(o);
      window.FloodSafeMapPanel.show(api.name(o),{station_id:api.ids(o)[0],has_latest:0},c?.[1]||28,c?.[0]||85);
      const p=document.getElementById('fsMapSidePanel');const archive=p.querySelector('details');if(archive&&!archive.open)throw Error('Last-known river reading must be visible without another click');
      const text=p.innerText;p.querySelector('.fsSideClose').click();
      return text;
    });
    if(historicalPanel){assert.match(historicalPanel,/पछिल्लो उपलब्ध मापन|Last known observation/);assert.match(historicalPanel,/NPT/);console.log('PASS last-known panel',historicalPanel);}
    await page.waitForFunction((first)=>window.__fsRiverRealtimeState?.checkedAt>first.river&&window.__fsImpactLiveState?.checkedAt>first.impact&&window.__fsNewsLiveState?.checkedAt>first.news,{timeout:60000},{river:before.river.checkedAt,impact:before.impact.checkedAt,news:before.news.checkedAt});
    await page.click('#langBtn');await page.waitForFunction(()=>window.FloodSafe.state.lang==='en',{timeout:10000});
    const archives=await page.evaluate(()=>['newsArchive','impactArchive'].map(id=>({id,exists:!!document.getElementById(id),open:document.getElementById(id)?.open})));
    for(const archive of archives)if(archive.exists)assert.equal(archive.open,true,archive.id+' must show dated reports by default');
    console.log('PASS dated older news and human reports visible by default',JSON.stringify(archives));
    await page.waitForFunction(()=>((window.FloodSafeMap?.map?.querySourceFeatures?.('gauges')?.length||window.__fsStaticMapFallback?.stations||0)>=100),{timeout:15000});
    const after=await read();assert.ok(after.gauges>=100);assert.equal(errors.length,0,errors.join('\n'));
    assert.equal(after.river.connected,true,'a failed poll is not a successful river refresh');
    assert.equal(after.news.connected,true);assert.equal(after.impact.connected,true);
    const freshnessUI=await page.evaluate(()=>({newsCount:window.__fsNewsLiveState.freshCount,news:document.getElementById('liveNews').innerText,humanCount:window.__fsImpactLiveState.freshCount,human:document.getElementById('impactFresh').innerText,deaths:document.getElementById('impactDeaths').innerText}));
    if(freshnessUI.newsCount===0)assert.match(freshnessUI.news,/No fresh data/);
    if(freshnessUI.humanCount===0){assert.match(freshnessUI.human,/No fresh data/);assert.equal(freshnessUI.deaths,'—');}
    console.log('PASS explicit no-fresh-data UI',JSON.stringify(freshnessUI));
    console.log('PASS mobile map, single human renderer, independent river/news/human refresh, language interaction',JSON.stringify({before,after}));
    await require('./floodsafe-browser-transitions.cjs')(browser,process.env.FLOODSAFE_URL||'https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
