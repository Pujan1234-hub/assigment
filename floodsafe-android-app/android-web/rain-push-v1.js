// Android local background weather bridge. The phone keeps the latest FloodSafe
// monitoring point in native storage and checks the 15-minute forecast in the
// background. With SATHI foreground mode active, additional checks are requested
// about every five minutes.
export function setupRainAlerts({getLanguage,getPoint}) {
  let status,button,onStatus,enabled=false,locationTimer=0;
  const tr=(ne,en)=>getLanguage()==='en'?en:ne;
  const message=()=>enabled
    ?tr('वर्षा सूचना सक्रिय छ • हालको/छानिएको क्षेत्रमा १५-मिनेट forecast जाँच हुन्छ र सम्भव भएसम्म १५–३० मिनेटअघि सूचना आउँछ।',
        'Rain alerts are active • 15-minute forecasts are checked for the current/selected area, normally warning about 15–30 minutes ahead.')
    :tr('वर्षा सूचना बन्द छ। स्थान छानेर सूचना सक्रिय गर्नुहोस्।',
        'Rain alerts are off. Choose a location and turn notifications on.');

  function render(){
    if(button){
      button.setAttribute('aria-pressed',String(enabled));
      button.textContent=enabled
        ?tr('🔕 वर्षा सूचना बन्द गर्नुहोस्','🔕 Turn off rain alerts')
        :tr('🔔 वर्षा सूचना सक्रिय गर्नुहोस्','🔔 Turn on rain alerts');
    }
    if(status)status.textContent=message();
  }

  function syncNativePoint(point){
    if(!point)return;
    const lat=Number(point.lat),lon=Number(point.lon);
    if(!Number.isFinite(lat)||!Number.isFinite(lon))return;
    window.SathiNative?.updateMonitoringPoint?.(lat,lon,point.kind==='gps');
  }

  function enable(){
    const point=getPoint?.();
    if(!point){
      status.textContent=tr('पहिले “मेरो हालको स्थान” थिच्नुहोस् वा नेपालमा निगरानी क्षेत्र छान्नुहोस्।',
        'Choose your current location or a Nepal monitoring area first.');
      return;
    }
    syncNativePoint(point);
    window.FloodSafeNative?.setBackgroundRainAlerts?.(point.lat,point.lon);
  }

  return {
    mount(after){
      const row=document.createElement('div');
      row.style.cssText='margin-top:10px;display:flex;flex-wrap:wrap;gap:8px';
      button=document.createElement('button');
      button.type='button';
      button.id='rainAlertBtn';
      button.className='pillBtn';
      button.style.fontSize='.8rem';
      button.addEventListener('click',()=>enabled?window.FloodSafeNative?.disableBackgroundRainAlerts?.():enable());
      row.appendChild(button);
      status=document.createElement('div');
      status.id='rainAlertStatus';
      status.setAttribute('role','status');
      status.style.cssText='font-size:.75rem;line-height:1.5;margin-top:6px';
      after.after(row);
      row.after(status);
      render();
      onStatus=event=>{
        enabled=Boolean(event?.detail?.enabled);
        if(enabled)syncNativePoint(getPoint?.());
        render();
      };
      window.addEventListener('floodsafe-alerts-status',onStatus);
      window.FloodSafeNative?.syncBackgroundRainAlerts?.();
    },
    render,
    locationChanged(){
      const point=getPoint?.();
      syncNativePoint(point);
      if(!enabled||!point)return;
      clearTimeout(locationTimer);
      locationTimer=setTimeout(()=>{
        const latest=getPoint?.();
        if(!latest)return;
        syncNativePoint(latest);
        window.FloodSafeNative?.setBackgroundRainAlerts?.(latest.lat,latest.lon);
      },700);
    },
    async check(){}
  };
}
