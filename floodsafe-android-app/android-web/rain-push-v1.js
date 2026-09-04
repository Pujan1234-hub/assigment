// Native Firebase push bridge. Android uses Firebase topic nepal-alerts.
// The visible control is intentionally the same weather-card area as the web app.
export function setupRainAlerts({getLanguage}) {
  let status,button,onStatus,enabled=false;
  const tr=(ne,en)=>getLanguage()==='en'?en:ne;
  const message=()=>enabled
    ?tr('आधिकारिक नेपाल वर्षा/बाढी सूचना सक्रिय छ।','Official Nepal rain and flood alerts are active.')
    :tr('सूचना बन्द छ। सूचना सक्रिय गर्नुहोस्।','Alerts are off. Turn notifications on.');
  function render(){
    if(button){button.setAttribute('aria-pressed',String(enabled));button.textContent=enabled
      ?tr('🔕 वर्षा सूचना बन्द गर्नुहोस्','🔕 Turn off rain alerts')
      :tr('🔔 वर्षा सूचना सक्रिय गर्नुहोस्','🔔 Turn on rain alerts');}
    if(status)status.textContent=message();
  }
  function set(enabledNext){
    if(window.FloodSafeNative?.setRainAlerts)window.FloodSafeNative.setRainAlerts(Boolean(enabledNext));
    else if(enabledNext&&window.FloodSafeNative?.enableRainAlerts)window.FloodSafeNative.enableRainAlerts();
  }
  return {
    mount(after){
      const row=document.createElement('div');row.style.cssText='margin-top:10px;display:flex;flex-wrap:wrap;gap:8px';
      button=document.createElement('button');button.type='button';button.id='rainAlertBtn';button.className='pillBtn';button.style.fontSize='.8rem';button.addEventListener('click',()=>set(!enabled));row.appendChild(button);
      status=document.createElement('div');status.id='rainAlertStatus';status.setAttribute('role','status');status.style.cssText='font-size:.75rem;line-height:1.5;margin-top:6px';
      after.after(row);row.after(status);render();
      onStatus=event=>{enabled=Boolean(event?.detail?.enabled);render()};
      window.addEventListener('floodsafe-alerts-status',onStatus);
      window.FloodSafeNative?.syncRainAlertsStatus?.();
    },
    render,
    locationChanged(){},
    async check(){}
  };
}
