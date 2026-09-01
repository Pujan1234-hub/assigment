(()=>{'use strict';
if(window.__fsRiverNameAliasV1)return;window.__fsRiverNameAliasV1=true;
const fix=s=>{const x=String(s||'').trim();if(/^(?:bish?numati|bisnumati)(?:\s+(?:river|khola|nadi))?$/i.test(x)||/^(?:विष्णुमती|बिष्णुमती)(?:\s*(?:नदी|खोला))?$/.test(x))return'Bishnumati';return x};
function patch(){const g=window.FloodSafeGauge;if(!g||g.__bishnumatiAlias)return false;g.__bishnumatiAlias=true;for(const k of['forWaterway','forWaterwayCatalog']){const orig=g[k];if(typeof orig!=='function')continue;g[k]=(w,...rest)=>{const x={...(w||{})};for(const p of['name','name_en','name_ne','name_raw'])if(x[p])x[p]=fix(x[p]);const raw=[w?.name,w?.name_en,w?.name_ne,w?.name_raw].map(fix).find(v=>v==='Bishnumati');if(raw){x.name='Bishnumati';x.name_en='Bishnumati';x.name_raw='Bishnumati'}return orig(x,...rest)}}return true}
let n=0,t=setInterval(()=>{if(patch()||++n>100)clearInterval(t)},100);for(const e of['fsriverupdate','fstrustedriverupdate'])window.addEventListener(e,patch);
})();
