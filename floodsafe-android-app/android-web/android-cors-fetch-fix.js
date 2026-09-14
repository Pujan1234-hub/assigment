(()=>{'use strict';
if(window.__fsAndroidCorsFetchFix)return;window.__fsAndroidCorsFetchFix=true;
const originalFetch=window.fetch.bind(window);
const isOfficialRiverRequest=url=>/^https:\/\/(?:camkoacuokffryyrygda\.supabase\.co\/functions\/v1\/sync-bipad-rivers|bipadportal\.gov\.np\/api\/v1\/(?:river-stations|river)\/)/i.test(String(url||''));
window.fetch=function(input,init){
  const url=typeof input==='string'?input:(input&&input.url)||'';
  if(!isOfficialRiverRequest(url))return originalFetch(input,init);
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
