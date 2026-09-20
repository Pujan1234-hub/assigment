(()=>{'use strict';
if(window.__fsAndroidCorsFetchFixV2)return;window.__fsAndroidCorsFetchFixV2=true;
const originalFetch=window.fetch.bind(window);
const isOfficialRealtimeRequest=url=>/^https:\/\/(?:camkoacuokffryyrygda\.supabase\.co\/functions\/v1\/sync-bipad-rivers|bipadportal\.gov\.np\/api\/v1\/(?:river-stations|river|rain-stations|rain|lake-stations|lake|reservoir-stations|reservoir|streamflow)\/)/i.test(String(url||''));
window.fetch=function(input,init){
  const url=typeof input==='string'?input:(input&&input.url)||'';
  if(!isOfficialRealtimeRequest(url))return originalFetch(input,init);
  try{
    const next={...(init||{})};
    if(next.headers){
      const headers=new Headers(next.headers);
      headers.delete('Cache-Control');
      headers.delete('Pragma');
      next.headers=headers;
    }
    if(!('cache' in next))next.cache='no-store';
    return originalFetch(input,next);
  }catch(_){
    return originalFetch(input,init);
  }
};
})();
