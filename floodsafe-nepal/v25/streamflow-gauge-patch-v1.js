(()=>{'use strict';if(window.__fsStreamflowGaugePatchV1)return;window.__fsStreamflowGaugePatchV1=true;
const rank={unknown:0,normal:1,watch:2,warning:3,danger:4};
function sfStage(s){s=String(s||'').toLowerCase();if(/danger|red|extreme|above\s*danger/.test(s))return'danger';if(/warning|orange|high|above\s*warning/.test(s))return'warning';if(/watch|yellow|moderate|rising|alert/.test(s))return'watch';if(/normal|below|steady|low/.test(s))return'normal';return'unknown'}
function enrich(g){if(!g)return g;const o=g.o||{},ss=o._officialStreamflowStatus??'',sv=o._officialStreamflow??null,st=o._officialStreamflowTime??null,s=sfStage(ss),base=g.status||'unknown';return{...g,status:(rank[s]||0)>(rank[base]||0)?s:base,streamflow:sv,streamflowStatus:ss,streamflowTime:st}}
function patch(){const g=window.FloodSafeGauge;if(!g||g.__streamflowPatch)return false;g.__streamflowPatch=true;for(const k of['forWaterway','forWaterwayCatalog']){const f=g[k];if(typeof f==='function')g[k]=(...a)=>enrich(f(...a))}return true}
let n=0,t=setInterval(()=>{if(patch()||++n>100)clearInterval(t)},100);for(const e of['fstrustedriverupdate','fsriverupdate'])window.addEventListener(e,patch);
})();
