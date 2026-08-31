(()=>{'use strict';
if(window.__fsMapRuntimeFixV1)return;window.__fsMapRuntimeFixV1=true;
const MAX=20*60*1000,FUTURE=5*60*1000;
let lastGps='',lastSig='';
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const num=v=>{const n=Number(String(v??'').replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const stamp=o=>val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime']);
const level=o=>num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level']));
const warn=o=>num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold']));
const danger=o=>num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold']));
function coords(o){const p=o?.point;const c=p?.coordinates;if(Array.isArray(c)&&c.length>=2&&Number.isFinite(+c[0])&&Number.isFinite(+c[1]))return[+c[0],+c[1]];const lo=num(val(o,['longitude','lon','lng','stationLongitude','station_longitude'])),la=num(val(o,['latitude','lat','stationLatitude','station_latitude']));return lo!==null&&la!==null?[lo,la]:null}
function current(o){if(!o||o._measurementTimeTrusted===false||o._current20m===false||level(o)===null)return false;const t=+new Date(stamp(o)||0),age=Date.now()-t;return !!t&&age>=-FUTURE&&age<=MAX}
function status(o){const l=level(o),w=warn(o),d=danger(o),raw=String(val(o,['_officialStatus','status','status_name','alertStatus','alert_status','riskLevel','risk_level'])||'').toUpperCase();if(l!==null&&d!==null&&d>0&&l>=d||/DANGER|RED/.test(raw)&&!/BELOW\s+DANGER/.test(raw))return'danger';if(l!==null&&w!==null&&w>0&&l>=w||/WARNING|ORANGE/.test(raw)&&!/BELOW\s+WARNING/.test(raw))return'warning';if(/WATCH|RISING|INCREASING|YELLOW/.test(raw))return'watch';return'normal'}
function name(o){return String(val(o,['river_name','riverName','station_name','stationName','title','name'])||'River station')}
function fc(){const out=[];for(const o of window.FloodSafe?.state?.stations||[]){if(!current(o))continue;const c=coords(o);if(!c||c[0]<79.5||c[0]>89||c[1]<26||c[1]>31)continue;out.push({type:'Feature',geometry:{type:'Point',coordinates:c},properties:{name:name(o),status:status(o),level:String(level(o)??''),time:String(stamp(o)||'')}})}return{type:'FeatureCollection',features:out}}
function repaint(){const map=window.FloodSafeMap?.map;if(!map?.getSource?.('gauges'))return;const data=fc(),sig=data.features.map(f=>`${f.properties.name}|${f.properties.status}|${f.properties.level}|${f.properties.time}`).sort().join('~');if(sig!==lastSig){lastSig=sig;map.getSource('gauges').setData(data)}try{map.setPaintProperty('gauges','circle-color',['match',['get','status'],'danger','#ff2d20','warning','#ff8a00','watch','#ffbd2e','#22a7ff']);map.setPaintProperty('river-base','line-color',['match',['get','live_status'],'danger','#ff2d20','warning','#ff8a00','watch','#ffbd2e','normal','#22a7ff','#22a7ff'])}catch{}const h=document.getElementById('mapHint');if(h){const n=data.features.length,matched=window.FloodSafeRiverLine?.indexedRiverCount||0;h.textContent=`🇳🇵 नेपाल • ७७ जिल्ला • ${n} ताजा official gauge ≤२० मिनेट • ${matched} नदी नाम match`}}
function gpsFollow(){const s=window.FloodSafe?.state,m=window.FloodSafeMap;if(!s||!m||s.kind!=='gps'||!Number.isFinite(s.lat)||!Number.isFinite(s.lon))return;const k=`${s.lat.toFixed(5)},${s.lon.toFixed(5)}`;if(k===lastGps)return;lastGps=k;m.select?.(s.lat,s.lon,true)}
function tick(){repaint();gpsFollow()}
window.addEventListener('fsriverupdate',tick);window.addEventListener('fstrustedriverupdate',tick);window.addEventListener('fsriverlinestatus',tick);setInterval(tick,1000);setTimeout(tick,500);
})();