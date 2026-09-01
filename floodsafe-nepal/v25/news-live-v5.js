(()=>{'use strict';
if(window.__fsNewsV7)return;window.__fsNewsV7=true;
const MAX=10*60*1000,FUTURE=5*60*1000,POLL_FRESH=10000,POLL_STALE=3000,POLL_HIDDEN=60000;
const LIVE='https://camkoacuokffryyrygda.supabase.co/functions/v1/news-live-three';
const SNAP=['https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/data/floodsafe-news.json','../../data/floodsafe-news.json'];
const ALLOWED=new Set(['RONB Post','Radio Nepal','News24 Nepal']);
let live=[],fallback=[],sourceState={},lastOk=0,busy=false,timer=0,expiryTimer=0,lastHtml='';
const $=id=>document.getElementById(id),lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne',tr=(ne,en)=>lang()==='en'?en:ne,ts=t=>+new Date(t||0)||0;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]||c));
function age(t){const m=Math.max(0,Math.floor((Date.now()-ts(t))/60000));if(m<1)return tr('अहिले','Now');return tr(`${m} मिनेट अघि`,`${m} min ago`)}
function valid(x){const t=ts(x?.published_at),d=Date.now()-t;return ALLOWED.has(x?.source)&&!!x?.title&&!!x?.url&&t&&d>=-FUTURE&&d<=MAX}
function merged(){const out=[],seenUrl=new Set(),seenTitle=new Set();for(const x of[...live,...fallback].filter(valid).sort((a,b)=>ts(b.published_at)-ts(a.published_at))){const u=String(x.url||'').split('#')[0],k=String(x.title||'').toLowerCase().replace(/\W+/g,' ').trim();if(!k||seenUrl.has(u)||seenTitle.has(k))continue;seenUrl.add(u);seenTitle.add(k);out.push(x)}return out}
function card(x){return `<article class="newsItem"><h4>${esc(x.title)}</h4><div class="meta">${esc(x.source)} • ${esc(age(x.published_at))} • <b class="liveDot">NEW</b></div><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${tr('खोल्नुहोस्','Open')} ↗</a></article>`}
function waiting(){return `<div class="newsFreshBox"><div class="newsBoxTitle"><strong>${tr('🔄 पछिल्लो १० मिनेटमा नयाँ समाचार छैन','🔄 No new story in the last 10 minutes')}</strong></div><article class="newsItem"><h4>${tr('नयाँ verified update जाँच भइरहेको छ। पुरानो समाचार यहाँ देखाइँदैन।','Checking for a new verified update. Older stories are not shown here.')}</h4><div class="meta">${tr('Auto refresh जारी','Auto refresh active')}</div></article></div>`}
function armExpiry(items){clearTimeout(expiryTimer);let wait=Infinity;for(const x of items){const left=ts(x.published_at)+MAX-Date.now();if(left>0&&left<wait)wait=left}if(Number.isFinite(wait))expiryTimer=setTimeout(()=>{render();schedule(0)},Math.max(80,wait+40))}
function render(){const host=$('liveNews');if(!host)return;if($('newsSub'))$('newsSub').textContent='RONB Post • Radio Nepal • News24 Nepal';const all=merged(),html=all.length?`<div class="newsFreshBox"><div class="newsBoxTitle"><strong>${tr('पछिल्लो १० मिनेटका नयाँ समाचार','New stories from the last 10 minutes')}</strong></div>${all.map(card).join('')}</div>`:waiting();if(html!==lastHtml){lastHtml=html;host.innerHTML=html}window.__fsNewsLiveState={connected:!!lastOk,lastSuccess:lastOk?new Date(lastOk).toISOString():null,count:all.length,freshWindowMinutes:10,sources:sourceState,mode:'smooth-adaptive-live'};armExpiry(all)}
async function get(url){const r=await fetch(url+(url.includes('?')?'&':'?')+'_fsnews='+Date.now(),{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error(String(r.status));return r.json()}
async function fetchLive(){try{const j=await get(LIVE);if(j?.status==='error')throw Error(j.error||'news live error');live=Array.isArray(j?.items)?j.items.filter(x=>ALLOWED.has(x.source)):[];sourceState=j?.sources||{};lastOk=Date.now();return true}catch(e){console.warn('FloodSafe live news',e);return false}}
async function snapshot(){for(const u of SNAP)try{const j=await get(u);if(Array.isArray(j?.items)){fallback=j.items.filter(x=>ALLOWED.has(x.source));return true}}catch{}return false}
function nextDelay(){if(document.hidden)return POLL_HIDDEN;return merged().length?POLL_FRESH:POLL_STALE}
function schedule(ms=nextDelay()){clearTimeout(timer);timer=setTimeout(sync,Math.max(250,ms))}
function kick(ms=0){clearTimeout(timer);if(!busy)schedule(ms)}
async function sync(){if(busy)return;busy=true;try{const ok=await fetchLive();if(!ok||!live.length)await snapshot();render()}finally{busy=false;schedule()}}
function boot(){render();kick(0);window.addEventListener('online',()=>kick(0));window.addEventListener('focus',()=>kick(0));window.addEventListener('fslanguage',()=>{lastHtml='';render()});document.addEventListener('visibilitychange',()=>{if(!document.hidden)kick(0);else schedule(POLL_HIDDEN)});window.FloodSafeNews={refresh:()=>kick(0),get items(){return merged()},get state(){return window.__fsNewsLiveState||null},FRESH_WINDOW_MS:MAX,STALE_POLL_MS:POLL_STALE}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();