(()=>{
'use strict';
if(window.__SATHI_NATIVE_EVENT_GUARD_V1__)return;
window.__SATHI_NATIVE_EVENT_GUARD_V1__=true;
const seen=new Map();
window.addEventListener('sathi-native-transcript',event=>{
  const id=String(event?.detail?.id||'').trim();
  if(!id)return;
  const now=Date.now(),last=seen.get(id)||0;
  if(last&&now-last<30000){event.stopImmediatePropagation();return}
  seen.set(id,now);
  if(seen.size>60){for(const [key,at] of seen){if(now-at>60000)seen.delete(key)}}
},true);
})();
