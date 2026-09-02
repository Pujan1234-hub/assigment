const ENDPOINT='https://camkoacuokffryyrygda.supabase.co/functions/v1/rain-alerts';
const KEY='fs-rain-push-v1';
export function setupRainAlerts({getPoint,getLanguage,refresh}){
  let saved=null,registration=null,busy=false,message='',lastSync=0,pendingKey='',button,status,testBtn;
  try{saved=JSON.parse(localStorage.getItem(KEY)||'null')}catch{}
  const tr=(ne,en)=>getLanguage()==='en'?en:ne;
  const supported=()=>window.isSecureContext&&'serviceWorker'in navigator&&'PushManager'in window&&'Notification'in window;
  const locationKey=()=>{const p=getPoint();return p?`${p.lat.toFixed(2)},${p.lon.toFixed(2)}`:null};
  function save(value){saved=value;if(value)localStorage.setItem(KEY,JSON.stringify(value));else localStorage.removeItem(KEY)}
  async function api(body){const c=new AbortController(),to=setTimeout(()=>c.abort(),15000);try{const r=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'omit',signal:c.signal});const j=await r.json();if(!r.ok)throw Error(j.error||'Rain notification service unavailable');return j}finally{clearTimeout(to)}}
  async function worker(){
    if(!registration)registration=await navigator.serviceWorker.register('./rain-alert-sw.js?v=1',{scope:'./',updateViaCache:'none'});
    if(!registration.active)await new Promise((resolve,reject)=>{const target=registration.installing||registration.waiting;if(!target){reject(Error('Notification worker not ready'));return}const timer=setTimeout(()=>{target.removeEventListener('statechange',changed);reject(Error('Notification worker not ready'))},12000);function changed(){if(target.state==='activated'||target.state==='redundant'){clearTimeout(timer);target.removeEventListener('statechange',changed);target.state==='activated'?resolve():reject(Error('Notification worker installation failed'))}}target.addEventListener('statechange',changed);changed()});
    return registration;
  }
  async function settings(enabled,key=locationKey()){const reg=await worker();return new Promise((resolve,reject)=>{const channel=new MessageChannel(),timer=setTimeout(()=>{channel.port1.close();reject(Error('Notification settings not saved'))},5000);channel.port1.onmessage=e=>{clearTimeout(timer);channel.port1.close();e.data?.ok?resolve():reject(Error('Notification settings not saved'))};reg.active.postMessage({type:'rain-settings',enabled,id:saved?.id,key,expiresAt:saved?.expiresAt||0},[channel.port2])})}
  function render(){
    if(!button)return;button.disabled=busy;button.setAttribute('aria-pressed',String(!!saved));
    button.textContent=busy?tr('जोडिँदैछ…','Connecting…'):saved?tr('🔕 वर्षा सूचना बन्द गर्नुहोस्','🔕 Turn off rain notifications'):tr('🔔 १५ मिनेटअघिको वर्षा सूचना','🔔 15-minute rain heads-up');
    if(testBtn){testBtn.disabled=busy||!saved;testBtn.textContent=tr('सूचना परीक्षण','Test notification')}
    status.textContent=message||(saved?tr('वर्षा push सक्रिय • अन्तिम छानिएको क्षेत्रका अनुमानित सूचना; समय र delivery निश्चित हुँदैन।','Rain push active • forecast alerts for the last selected area; timing and delivery are not guaranteed.'):tr('अनुमति दिएपछि मात्रै वर्षा सूचना सुरु हुन्छ।','Rain notifications start only after you opt in.'));
  }
  async function enable(){
    if(busy)return;if(!supported()){message=tr('यो browser मा push उपलब्ध छैन। Chrome/Firefox प्रयोग गर्नुहोस्; iPhone मा Home Screen मा थपेर खोल्नुहोस्।','Push is unavailable here. Use Chrome/Firefox; on iPhone add the app to your Home Screen.');render();return}
    const p=getPoint();if(!p){message=tr('पहिले हालको स्थान वा निगरानी क्षेत्र छान्नुहोस्।','Choose your current location or monitoring area first.');render();return}
    if(!window.confirm(tr('वर्षा सूचना सुरु गर्ने? अन्तिम छानिएको करिब १-किमि क्षेत्र र browser push subscription FloodSafe को server मा ७ दिनसम्म राखिन्छ; app खोल्दा अवधि नवीकरण हुन्छ। App बन्द हुँदा पनि त्यही क्षेत्रको अनुमानित सूचना आउन सक्छ। बन्द गरेपछि विवरण मेटिन्छ।','Enable rain notifications? FloodSafe will keep your last selected approximate 1-km area and browser push subscription for 7 days, renewed when you open the app. Forecast alerts can arrive while the app is closed, for that last area. Turning off removes these details.')))return;
    busy=true;message='';render();
    try{
      const permission=await Notification.requestPermission();if(permission!=='granted')throw Error(tr('Notification अनुमति दिइएको छैन। Browser settings बाट Allow गर्नुहोस्।','Notification permission was not granted. Allow it in browser settings.'));
      const reg=await worker(),config=await fetch(ENDPOINT+'?config=1',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Push service unavailable');return r.json()});
      let sub=await reg.pushManager.getSubscription();if(sub&&!saved){await sub.unsubscribe();sub=null}
      const bytes=Uint8Array.from(atob(config.publicKey.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
      sub=sub||await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:bytes});
      const token=saved?.token||crypto.randomUUID()+crypto.randomUUID(),key=locationKey(),[lat,lon]=key.split(',').map(Number);
      const result=await api({action:'subscribe',subscription:sub.toJSON(),token,lat,lon,lang:getLanguage()});
      save({id:result.id,token,key,expiresAt:result.expiresAt});lastSync=Date.now();await settings(true,locationKey());message='';
      void refresh();
    }catch(e){message=String(e.message||e);if(!saved){try{const sub=await registration?.pushManager.getSubscription();await sub?.unsubscribe()}catch{}}}
    finally{busy=false;render()}
  }
  async function disable(){
    if(busy||!saved)return;busy=true;render();
    try{
      await worker();await settings(false);const old=saved;
      // Unsubscribe locally even when the server is temporarily unreachable.
      await (await registration.pushManager.getSubscription())?.unsubscribe();
      try{await api({action:'unsubscribe',id:old.id,token:old.token});message=tr('वर्षा सूचना बन्द भयो; server विवरण हटाइयो।','Rain notifications off; server details removed.')}catch{message=tr('यस device मा सूचना बन्द भयो। Server विवरण बढीमा ७ दिनभित्र स्वतः हट्छ।','Notifications are off on this device. Server details expire within 7 days.')}
      save(null);
    }catch(e){message=String(e.message||e)}finally{busy=false;render()}
  }
  async function sync(){
    if(!saved||busy||!getPoint())return;const key=locationKey();
    if(key===saved.key&&Date.now()-lastSync<3600000)return;
    busy=true;pendingKey=key;
    try{
      const reg=await worker();await settings(true,key);const sub=await reg.pushManager.getSubscription();
      if(!sub||Notification.permission!=='granted'){await settings(false);save(null);message=tr('वर्षा सूचना पुनः सुरु गर्न अनुमति दिनुहोस्।','Enable rain notifications again.');return}
      const [lat,lon]=key.split(',').map(Number),result=await api({action:'subscribe',subscription:sub.toJSON(),token:saved.token,lat,lon,lang:getLanguage()});
      save({...saved,key,id:result.id,expiresAt:result.expiresAt});lastSync=Date.now();await settings(true,locationKey());message='';
    }catch{message=tr('वर्षा सूचना server सँग sync भएन • पुनः प्रयास हुँदैछ','Rain notification area not synced • retrying')}
    finally{busy=false;render();if(pendingKey!==locationKey())setTimeout(()=>void sync(),500)}
  }
  async function test(){
    if(!saved||busy)return;busy=true;render();
    try{await settings(true,saved.key);await api({action:'test',id:saved.id,token:saved.token});message=tr('परीक्षण सूचना push service लाई पठाइयो। Phone मा आएको जाँच्नुहोस्।','Test submitted to the push service. Check whether it arrives on your phone.')}catch(e){message=String(e.message||e)}finally{busy=false;render()}
  }
  return {mount(after){
    const row=document.createElement('div');row.style.cssText='margin-top:10px;display:flex;flex-wrap:wrap;gap:8px';
    button=document.createElement('button');button.type='button';button.id='rainAlertBtn';button.className='pillBtn';button.style.fontSize='.8rem';button.addEventListener('click',()=>saved?void disable():void enable());row.appendChild(button);
    testBtn=document.createElement('button');testBtn.type='button';testBtn.id='rainAlertTestBtn';testBtn.className='pillBtn';testBtn.style.fontSize='.8rem';testBtn.addEventListener('click',()=>void test());row.appendChild(testBtn);
    status=document.createElement('div');status.id='rainAlertStatus';status.setAttribute('role','status');status.style.cssText='font-size:.75rem;line-height:1.4;margin-top:6px';after.after(row);row.after(status);render();
    if(saved)void sync();setInterval(()=>void sync(),60000);
  },render,locationChanged(){if(saved){void settings(true).catch(()=>{});void sync()}},check:async()=>{if(saved)await sync()}};
}
