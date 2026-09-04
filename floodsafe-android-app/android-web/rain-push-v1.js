// Android local background weather bridge. The phone checks the last selected point
// every 15 minutes and notifies even after the app is closed (not force-stopped).
export function setupRainAlerts({getLanguage,getPoint}) {
  let status,button,onStatus,enabled=false;
  const tr=(ne,en)=>getLanguage()==='en'?en:ne;
  const message=()=>enabled
    ?tr('वर्षा सूचना सक्रिय छ • अन्तिम छानिएको क्षेत्रमा हरेक १५ मिनेटमा जाँच हुन्छ।','Rain alerts are active • the last selected area is checked every 15 minutes.')
    :tr('वर्षा सूचना बन्द छ। सूचना सक्रिय गर्नुहोस्।','Rain alerts are off. Turn notifications on.');
  function render(){
    if(button){button.setAttribute('aria-pressed',String(enabled));button.textContent=enabled
      ?tr('🔕 वर्षा सूचना बन्द गर्नुहोस्','🔕 Turn off rain alerts')
      :tr('🔔 वर्षा सूचना सक्रिय गर्नुहोस्','🔔 Turn on rain alerts');}
    if(status)status.textContent=message();
  }
  function enable(){
    const point=getPoint?.();
    if(!point){status.textContent=tr('पहिले मेरो हालको स्थान वा निगरानी क्षेत्र छान्नुहोस्।','Choose your current location or monitoring area first.');return}
    window.FloodSafeNative?.setBackgroundRainAlerts?.(point.lat,point.lon);
  }
  return {
    mount(after){
      const row=document.createElement('div');row.style.cssText='margin-top:10px;display:flex;flex-wrap:wrap;gap:8px';
      button=document.createElement('button');button.type='button';button.id='rainAlertBtn';button.className='pillBtn';button.style.fontSize='.8rem';button.addEventListener('click',()=>enabled?window.FloodSafeNative?.disableBackgroundRainAlerts?.():enable());row.appendChild(button);
      status=document.createElement('div');status.id='rainAlertStatus';status.setAttribute('role','status');status.style.cssText='font-size:.75rem;line-height:1.5;margin-top:6px';
      after.after(row);row.after(status);render();
      onStatus=event=>{enabled=Boolean(event?.detail?.enabled);render()};
      window.addEventListener('floodsafe-alerts-status',onStatus);
      window.FloodSafeNative?.syncBackgroundRainAlerts?.();
    },
    render,
    locationChanged(){},
    async check(){}
  };
}
