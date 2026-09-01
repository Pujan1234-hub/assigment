const puppeteer=require('puppeteer-core');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await puppeteer.launch({executablePath:process.env.CHROME,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  try {
    const page=await browser.newPage();await page.setViewport({width:412,height:915});
    const errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto('https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/?refresh-verification='+Date.now(),{waitUntil:'domcontentloaded',timeout:60000});
    await page.waitForFunction(()=>window.FloodSafeRiverRealtime&&window.FloodSafeImpact&&window.FloodSafeNews,{timeout:45000});
    await page.waitForFunction(()=>window.__fsRiverRealtimeState?.catalogCount>=100&&window.__fsImpactLiveState?.lastSuccess&&window.__fsNewsLiveState?.lastSuccess,{timeout:60000});
    await page.waitForFunction(()=>window.FloodSafeMap?.map?.isStyleLoaded?.()||window.__fsStaticMapFallback?.active,{timeout:60000});
    const read=()=>page.evaluate(()=>({
      river:window.__fsRiverRealtimeState,
      news:window.__fsNewsLiveState,
      impact:window.__fsImpactLiveState,
      mapVisible:document.querySelector('.mapCanvas').getBoundingClientRect().height>0,
      mapClosed:document.getElementById('map').classList.contains('fsMapClosed'),
      gauges:window.FloodSafeMap?.map?.getSource?.('gauges')?._data?.features?.length||window.__fsStaticMapFallback?.stations||0,
      oldHumanScript:!!document.querySelector('script[src*="flood-freshness.js"]'),
      newsText:document.getElementById('liveNews').innerText.slice(0,400),
      checkText:document.getElementById('feedFresh').innerText
    }));
    // Style readiness precedes the first asynchronous station-source update.
    await page.waitForFunction(()=>((window.FloodSafeMap?.map?.getSource?.('gauges')?._data?.features?.length||window.__fsStaticMapFallback?.stations||0)>=100),{timeout:15000});
    const before=await read();assert.equal(before.mapClosed,false);assert.equal(before.mapVisible,true);assert.equal(before.oldHumanScript,false);assert.ok(before.gauges>=100,JSON.stringify(before));
    await page.waitForFunction((first)=>window.__fsRiverRealtimeState?.checkedAt>first.river&&window.__fsImpactLiveState?.checkedAt>first.impact&&window.__fsNewsLiveState?.checkedAt>first.news,{timeout:60000},{river:before.river.checkedAt,impact:before.impact.checkedAt,news:before.news.checkedAt});
    await page.click('#langBtn');await page.waitForFunction(()=>window.FloodSafe.state.lang==='en',{timeout:10000});
    await page.waitForFunction(()=>((window.FloodSafeMap?.map?.getSource?.('gauges')?._data?.features?.length||window.__fsStaticMapFallback?.stations||0)>=100),{timeout:15000});
    const after=await read();assert.ok(after.gauges>=100);assert.equal(errors.length,0,errors.join('\n'));
    console.log('PASS mobile map, single human renderer, independent river/news/human refresh, language interaction',JSON.stringify({before,after}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
