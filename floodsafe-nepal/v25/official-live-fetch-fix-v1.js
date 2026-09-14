(()=>{'use strict';
if(window.__fsOfficialLiveFetchFixV1)return;window.__fsOfficialLiveFetchFixV1=true;
const original=window.fetch.bind(window);
const OFFICIAL_HOSTS=new Set(['camkoacuokffryyrygda.supabase.co','bipadportal.gov.np','www.bipadportal.gov.np']);
function urlOf(input){try{return new URL(typeof input==='string'?input:input?.url,location.href)}catch{return null}}
function cleanHeaders(raw){const h=new Headers(raw||{});h.delete('Cache-Control');h.delete('cache-control');h.delete('Pragma');h.delete('pragma');return h}
window.fetch=function(input,init){
  const u=urlOf(input);
  if(!u||!OFFICIAL_HOSTS.has(u.hostname))return original(input,init);
  const next={...(init||{})};
  next.headers=cleanHeaders(next.headers);
  next.cache='no-store';
  if(!('credentials' in next))next.credentials='omit';
  return original(input,next);
};
window.__fsOfficialLiveFetchPolicy={hosts:[...OFFICIAL_HOSTS],cache:'no-store',corsSimpleHeadersOnly:true};
})();
