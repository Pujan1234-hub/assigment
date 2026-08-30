(()=>{'use strict';try{if('serviceWorker'in navigator)navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>{if((r.scope||'').includes('/floodsafe-nepal/'))r.unregister()}));if('caches'in window)caches.keys().then(ks=>ks.filter(k=>/floodsafe|v25|shell/i.test(k)).forEach(k=>caches.delete(k)));}catch{}

// National map guard: the first view must read as Nepal, not as a tilted Himalayan strip.
let tries=0;const timer=setInterval(()=>{tries++;try{const api=window.FloodSafeMap,m=api?.map;if(!m){if(tries>80)clearInterval(timer);return}api.set3D?.(false);if(!m.isStyleLoaded?.()||!m.getLayer?.('district-fill')){if(tries>80)clearInterval(timer);return}

// The old district-hole mask is topologically fragile. Hide it and make Nepal itself the visual focus.
if(m.getLayer('nepal-mask'))m.setLayoutProperty('nepal-mask','visibility','none');
if(m.getLayer('satellite')){m.setPaintProperty('satellite','raster-opacity',0.64);m.setPaintProperty('satellite','raster-saturation',-0.12);m.setPaintProperty('satellite','raster-contrast',0.08);m.setPaintProperty('satellite','raster-brightness-max',0.88)}
if(m.getLayer('hillshade'))m.setPaintProperty('hillshade','hillshade-exaggeration',0.16);
if(m.getLayer('district-fill')){m.setPaintProperty('district-fill','fill-color','#b9ffe0');m.setPaintProperty('district-fill','fill-opacity',['interpolate',['linear'],['zoom'],4.5,0.24,7,0.16,10,0.07])}
if(m.getLayer('district-lines-shadow'))m.setPaintProperty('district-lines-shadow','line-opacity',0.34);
if(m.getLayer('district-lines')){m.setPaintProperty('district-lines','line-color','#f7fffb');m.setPaintProperty('district-lines','line-opacity',0.82);m.setPaintProperty('district-lines','line-width',['interpolate',['linear'],['zoom'],5,0.65,11,1.3])}
if(m.getLayer('nepal-border-shadow')){m.setPaintProperty('nepal-border-shadow','line-color','#041a19');m.setPaintProperty('nepal-border-shadow','line-opacity',0.95)}
if(m.getLayer('nepal-border')){m.setPaintProperty('nepal-border','line-color','#39f2c2');m.setPaintProperty('nepal-border','line-opacity',1);m.setPaintProperty('nepal-border','line-width',['interpolate',['linear'],['zoom'],5,3.2,11,5])}

m.stop?.();m.setPitch?.(0);m.setBearing?.(0);m.fitBounds([[80.0,26.2],[88.35,30.5]],{padding:window.innerWidth<620?18:28,pitch:0,bearing:0,duration:0});
const hint=document.getElementById('mapHint');if(hint)hint.textContent=(window.FloodSafe?.state?.lang==='en')?'🇳🇵 Nepal overview • 77 districts • tap Nepal for local river detail':'🇳🇵 नेपालको स्पष्ट नक्सा • ७७ जिल्ला • स्थानीय नदी विवरणका लागि नेपालभित्र थिच्नुहोस्';
clearInterval(timer);
}catch(e){console.warn('Nepal map framing guard',e);if(tries>80)clearInterval(timer)}},250);
})();