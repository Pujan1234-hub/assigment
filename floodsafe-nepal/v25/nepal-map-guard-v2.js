(()=>{'use strict';
const BOUNDS=[[80.0,26.2],[88.35,30.5]];
let armed=false,tries=0,stabilize=null;
const $=id=>document.getElementById(id);
function lang(){return window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne'}
function hint(){const e=$('mapHint');if(e)e.textContent=lang()==='en'?'🇳🇵 Nepal overview • 77 districts • tap a district for local river detail':'🇳🇵 नेपालको स्पष्ट नक्सा • ७७ जिल्ला • स्थानीय नदी विवरणका लागि जिल्लाभित्र थिच्नुहोस्'}
function tune(m){
  try{m.setTerrain(null)}catch{}
  try{m.stop();m.setPitch(0);m.setBearing(0);m.fitBounds(BOUNDS,{padding:window.innerWidth<620?12:24,pitch:0,bearing:0,duration:0})}catch{}
  try{if(m.getLayer('nepal-mask'))m.setLayoutProperty('nepal-mask','visibility','none')}catch{}
  const z=m.getZoom?.()||5.5;
  const sat=z<7?0.22:z<9?0.45:0.78;
  try{if(m.getLayer('satellite')){m.setPaintProperty('satellite','raster-opacity',sat);m.setPaintProperty('satellite','raster-saturation',-0.12);m.setPaintProperty('satellite','raster-contrast',0.06)}}catch{}
  try{if(m.getLayer('hillshade'))m.setPaintProperty('hillshade','hillshade-exaggeration',0.10)}catch{}
  for(const id of ['guard-nepal-fill','guard-district-lines','guard-district-labels']){try{if(m.getLayer(id))m.moveLayer(id)}catch{}}
  const b=$('map3D');if(b){b.classList.remove('active');b.textContent=lang()==='en'?'◈ 3D Terrain':'◈ ३D भू-आकृति'}
  hint();
}
async function install(){
  const api=window.FloodSafeMap,m=api?.map;
  if(!m||!m.isStyleLoaded?.())return false;
  try{api.set3D?.(false)}catch{}
  let geo=null;
  try{const r=await fetch('../v24/nepal-districts.geojson?nepal_guard=20260830b',{cache:'no-store'});if(r.ok)geo=await r.json()}catch(e){console.warn('Nepal guard districts',e)}
  if(!geo?.features?.length)return false;
  try{
    if(!m.getSource('guard-districts'))m.addSource('guard-districts',{type:'geojson',data:geo});
    if(!m.getLayer('guard-nepal-fill'))m.addLayer({id:'guard-nepal-fill',type:'fill',source:'guard-districts',paint:{'fill-color':'#65d99f','fill-opacity':['interpolate',['linear'],['zoom'],5,0.52,7,0.34,10,0.10]}});
    if(!m.getLayer('guard-district-lines'))m.addLayer({id:'guard-district-lines',type:'line',source:'guard-districts',paint:{'line-color':'#f5fff9','line-width':['interpolate',['linear'],['zoom'],5,0.9,8,1.4,12,2.0],'line-opacity':0.94}});
    if(!m.getLayer('guard-district-labels'))m.addLayer({id:'guard-district-labels',type:'symbol',source:'guard-districts',minzoom:6.15,layout:{'text-field':['get','nameEn'],'text-size':['interpolate',['linear'],['zoom'],6.15,9,9,12,12,14],'text-font':['Open Sans Regular','Arial Unicode MS Regular'],'text-allow-overlap':false,'text-ignore-placement':false},paint:{'text-color':'#ffffff','text-halo-color':'#123b31','text-halo-width':1.4,'text-halo-blur':0.4}});
  }catch(e){console.warn('Nepal guard layer',e)}
  tune(m);
  if(!armed){armed=true;m.on('zoomend',()=>tune(m));m.on('styledata',()=>setTimeout(()=>tune(m),0));}
  clearInterval(stabilize);let n=0;stabilize=setInterval(()=>{n++;tune(m);if(n>24)clearInterval(stabilize)},500);
  return true;
}
const timer=setInterval(async()=>{tries++;if(await install())clearInterval(timer);else if(tries>100)clearInterval(timer)},200);
})();