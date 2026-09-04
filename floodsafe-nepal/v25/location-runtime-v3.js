(()=>{'use strict';
if(window.__fsLocationRuntimeV3)return;window.__fsLocationRuntimeV3=true;
const $=id=>document.getElementById(id),MAX_AGE=120000;
const inside=(la,lo)=>Number.isFinite(la)&&Number.isFinite(lo)&&la>=26.2&&la<=30.5&&lo>=80&&lo<=88.35;
let last=null,watch=null,requested=false,pendingCenter=false,busy=false,boundMap=null,lastError='';
const tr=(ne,en)=>(window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang'))==='en'?en:ne;
const fresh=()=>last&&!lastError&&Date.now()-last.at<=MAX_AGE;
function label(){
  if(!last||!$('place'))return;
  if(!inside(last.lat,last.lon)){$('place').textContent=tr('🌍 हालको GPS स्थान नेपाल बाहिर छ • मौसम यही स्थानको हो','🌍 Current GPS is outside Nepal • weather is for this location');return}
  const at=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(last.at);
  $('place').textContent=tr(`📍 ${fresh()?'मेरो हालको स्थान':'पछिल्लो GPS स्थान'} • ±${Math.round(last.accuracy)} m • ${at} NPT`,`📍 ${fresh()?'My current location':'Last GPS location'} • ±${Math.round(last.accuracy)} m • ${at} NPT`);
}
function marker(){
  if(!last)return;
  // The lightweight Nepal map must also show GPS when WebGL is unavailable.
  const svg=$('fsStaticMapFallback')?.querySelector?.('svg');
  if(svg){
    let group=svg.querySelector('[data-fs-gps]');
    if(!group){group=document.createElementNS('http://www.w3.org/2000/svg','g');group.setAttribute('data-fs-gps','1');const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('r','7');dot.setAttribute('stroke','#fff');dot.setAttribute('stroke-width','3');group.appendChild(dot);const label=document.createElementNS('http://www.w3.org/2000/svg','text');label.setAttribute('x','11');label.setAttribute('y','4');label.setAttribute('fill','#fff');label.setAttribute('font-size','13');label.setAttribute('font-weight','bold');label.textContent='GPS';group.appendChild(label);svg.appendChild(group)}
    group.style.display=inside(last.lat,last.lon)?'':'none';group.setAttribute('transform',`translate(${(last.lon-79.85)/8.6*1000},${(30.55-last.lat)/4.4*515})`);group.querySelector('circle').setAttribute('fill',fresh()?'#16a34a':'#64748b');svg.appendChild(group);
  }
  const map=window.FloodSafeMap?.map;if(!map)return;
  const valid=last&&inside(last.lat,last.lon),features=[];
  if(valid){
    const ring=[],radius=Math.min(last.accuracy,10000),cos=Math.cos(last.lat*Math.PI/180);
    for(let i=0;i<=48;i++){const a=i/48*2*Math.PI;ring.push([last.lon+Math.cos(a)*radius/(111320*cos),last.lat+Math.sin(a)*radius/111320])}
    features.push({type:'Feature',geometry:{type:'Polygon',coordinates:[ring]},properties:{kind:'accuracy'}},{type:'Feature',geometry:{type:'Point',coordinates:[last.lon,last.lat]},properties:{kind:'position',fresh:!!fresh(),accuracy:last.accuracy,observedAt:last.at}});
  }
  try{
    const data={type:'FeatureCollection',features};
    if(map.getSource('fs-user-location'))map.getSource('fs-user-location').setData(data);
    else map.addSource('fs-user-location',{type:'geojson',data});
    const layers=[
      {id:'fs-user-location-accuracy',type:'fill',source:'fs-user-location',filter:['==','kind','accuracy'],paint:{'fill-color':'#16a34a','fill-opacity':.12}},
      {id:'fs-user-location-halo',type:'circle',source:'fs-user-location',filter:['==','kind','position'],paint:{'circle-radius':14,'circle-color':'#fff','circle-opacity':.7}},
      {id:'fs-user-location-dot',type:'circle',source:'fs-user-location',filter:['==','kind','position'],paint:{'circle-radius':8,'circle-color':['case',['==',['get','fresh'],true],'#16a34a','#64748b'],'circle-stroke-color':'#fff','circle-stroke-width':3}}
    ];
    for(const layer of layers){if(!map.getLayer(layer.id))map.addLayer(layer);map.moveLayer?.(layer.id)}
    if(valid&&pendingCenter&&window.FloodSafeMobileMap?.isOpen){pendingCenter=false;map.flyTo?.({center:[last.lon,last.lat],zoom:12,duration:450})}
  }catch{/* A loading/replaced map style is retried on the next ready event. */}
}
function mapReady(){const map=window.FloodSafeMap?.map;if(map&&map!==boundMap){boundMap=map;map.on?.('style.load',marker)}marker()}
function accept(position){
  const c=position?.coords;if(typeof c?.latitude!=='number'||typeof c?.longitude!=='number'||!Number.isFinite(c.latitude)||!Number.isFinite(c.longitude)||Math.abs(c.latitude)>90||Math.abs(c.longitude)>180)return;
  const at=Number(position.timestamp)||Date.now();if(Date.now()-at>MAX_AGE||at>Date.now()+60000)return;
  if(last&&at<last.at)return;
  busy=false;lastError='';last={lat:c.latitude,lon:c.longitude,accuracy:Number.isFinite(c.accuracy)&&c.accuracy>0?c.accuracy:1000,at};
  if($('outsideNotice'))$('outsideNotice').hidden=inside(last.lat,last.lon);
  // Tracking follows the user until they deliberately select another monitoring point.
  if(inside(last.lat,last.lon)&&(pendingCenter||window.FloodSafe?.state?.kind==='gps'))void window.FloodSafe?.setFocus?.(last.lat,last.lon,'gps');
  marker();label();window.dispatchEvent(new CustomEvent('fscurrentlocation',{detail:{...last}}));
}
function fail(error){
  busy=false;lastError=String(error?.message||'Location unavailable');window.__fsLocationLastError=lastError;
  if(error?.code===1){requested=false;stopWatch()}
  if(!last&&$('outsideNotice'))$('outsideNotice').hidden=true;
  if(last)label();else if($('place'))$('place').textContent=tr('📍 Location अनुमति दिनुहोस् वा नेपाल नक्साबाट निगरानी स्थान छान्नुहोस्','📍 Allow location access or choose a monitoring point on the Nepal map');
  marker();window.dispatchEvent(new CustomEvent('fslocationerror',{detail:{message:lastError}}));
}
function stopWatch(){if(watch!==null)navigator.geolocation?.clearWatch(watch);watch=null;busy=false}
function startWatch(){
  if(watch!==null||document.hidden||!requested)return;
  if(!navigator.geolocation){fail({message:'GPS unavailable'});return}
  busy=true;
  watch=navigator.geolocation.watchPosition(accept,fail,{enableHighAccuracy:true,timeout:15000,maximumAge:5000});
}
function locate(){
  // Android WebView needs an explicit native request before geolocation starts.
  try{window.FloodSafeNative?.allowLocationPrompt?.()}catch{}
  requested=true;pendingCenter=true;lastError='';
  if($('place'))$('place').textContent=tr('📍 हालको स्थान खोजिँदैछ…','📍 Finding current location…');
  stopWatch();startWatch();
}
function boot(){
  $('locateBtn')?.addEventListener('click',locate);
  for(const event of ['fsmapready','fs281mapready','fsmapvisibility'])window.addEventListener(event,mapReady);
  window.addEventListener('fslanguage',label);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stopWatch();else{startWatch();label();marker()}});
  window.addEventListener('pagehide',stopWatch);window.addEventListener('pageshow',startWatch);
  setInterval(()=>{if(!document.hidden){label();marker()}},30000);
  window.FloodSafeCurrentLocation={locate,get last(){return last&&{...last}},get busy(){return busy},get tracking(){return watch!==null},get fresh(){return !!fresh()}};
  mapReady();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
