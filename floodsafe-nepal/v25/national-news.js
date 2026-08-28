(()=>{
'use strict';
const PAGE=document.body.dataset.page||'home',$=id=>document.getElementById(id),KCHA='https://kchakhabar.com/api/v1/today.json?limit=100';
const ROTATE_SEC=30,FRESH_MS=60*60*1000,FETCH_MS=60*1000;
let items=[],visible=[],sourceOk=false,nextRotate=ROTATE_SEC,lastFetch=0,busy=false,paused=false,pauseBtn=null;
const norm=s=>String(s||'').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const age=t=>{const x=+new Date(t||0);if(!x)return Infinity;return Math.max(0,Date.now()-x)};
const seenKey='fs25-flash-seen-'+PAGE;
function loadSeen(){try{const a=JSON.parse(sessionStorage.getItem(seenKey)||'[]');return new Set(Array.isArray(a)?a:[])}catch{return new Set()}}
const seen=loadSeen();
function saveSeen(){try{sessionStorage.setItem(seenKey,JSON.stringify([...seen].slice(-250)))}catch{}}
function make(tag,cls,t){const e=document.createElement(tag);if(cls)e.className=cls;if(t!==undefined)e.textContent=t;return e}
function clear(e){if(e)while(e.firstChild)e.removeChild(e.firstChild)}
function fmt(t){try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',day:'numeric',month:'short'}).format(new Date(t))}catch{return''}}
function ago(t){const m=Math.max(0,Math.floor(age(t)/60000));return m<1?'भर्खर':m+' मिनेट अघि'}
function keyOf(x){return String(x.id||norm(x.title))}
function dedup(list){const out=[],keys=[];for(const x of list){const k=norm(x.title);if(!k||keys.some(s=>(k.includes(s)||s.includes(k))&&Math.min(k.length,s.length)>24))continue;keys.push(k);out.push(x)}return out}
function fromKcha(j){const raw=Array.isArray(j?.stories)?j.stories:[];return dedup(raw.filter(s=>s.first_reported&&age(s.first_reported)<FRESH_MS).map(s=>{const src=s.sources?.[0];return{id:String(s.id||''),title:s.topic_ne||s.topic_en||'',source:src?.publisher||'Nepal media',url:src?.url||s.url,published:s.first_reported,updated:s.updated_at||s.first_reported,flash:true}})).sort((a,b)=>(+new Date(b.published||0))-(+new Date(a.published||0)))}
function storyCard(x){const box=make('article','item');box.dataset.newsKey=keyOf(x);box.appendChild(make('span','tag red','FLASH'));box.appendChild(make('h4','',x.title));box.appendChild(make('div','meta',x.source+' • '+ago(x.published)+(x.published?' • '+fmt(x.published):'')));if(x.url){const r=make('div','meta'),a=make('a','','समाचार खोल्नुहोस्');a.href=x.url;a.target='_blank';a.rel='noopener noreferrer';a.referrerPolicy='no-referrer';r.appendChild(a);box.appendChild(r)}return box}
function statusText(){if(!sourceOk)return'ताजा Flash News feed फेरि जाँच हुँदैछ…';if(paused)return'Flash News • पढ्नका लागि रोकिएको';return visible.length?'Flash News • १ घण्टाभित्रका समाचार • अर्को '+nextRotate+' sec':'नयाँ Flash News पर्खिँदै…'}
function updateStatus(){const s=statusText();if($('appStatus'))$('appStatus').textContent=s;if($('homeNewsFresh'))$('homeNewsFresh').textContent=s;if($('healthNews'))$('healthNews').textContent=sourceOk?'Flash feed ✓ • १ घण्टाभित्र':'Flash feed • फेरि जाँच हुँदैछ';if(pauseBtn)pauseBtn.textContent=paused?'▶️ समाचार चलाउनुहोस्':'⏸ समाचार रोक्नुहोस्'}
function ensurePause(){const list=PAGE==='nationalnews'?$('newsList'):$('nationalHomeNews');if(!list||pauseBtn)return;pauseBtn=make('button','newsPause',paused?'▶️ समाचार चलाउनुहोस्':'⏸ समाचार रोक्नुहोस्');pauseBtn.type='button';pauseBtn.setAttribute('aria-pressed',String(paused));pauseBtn.style.cssText='margin:0 0 10px;padding:8px 12px;border-radius:999px;border:1px solid #6d4b3e;background:#1a1110;color:#fff;font-weight:850;font-size:12px;cursor:pointer';pauseBtn.addEventListener('click',()=>{paused=!paused;pauseBtn.setAttribute('aria-pressed',String(paused));if(!paused&&nextRotate<=0)nextRotate=ROTATE_SEC;updateStatus()});list.parentElement?.insertBefore(pauseBtn,list)}
function render(){const list=PAGE==='nationalnews'?$('newsList'):$('nationalHomeNews');if(!list)return;ensurePause();clear(list);visible=visible.filter(x=>age(x.published)<FRESH_MS);if(!visible.length){list.appendChild(make('div','empty',sourceOk?'नयाँ ताजा Flash News पर्खिँदैछ…':'ताजा समाचार खोजिँदैछ…'));if($('newsCount'))$('newsCount').textContent='0';updateStatus();return}visible.forEach(x=>list.appendChild(storyCard(x)));if($('newsCount'))$('newsCount').textContent=items.length;updateStatus()}
function pickNext(){items=items.filter(x=>age(x.published)<FRESH_MS);const count=PAGE==='nationalnews'?6:3,candidates=items.filter(x=>!seen.has(keyOf(x)));visible=candidates.slice(0,count);for(const x of visible)seen.add(keyOf(x));saveSeen();nextRotate=ROTATE_SEC;render()}
async function get(url,ms=7000){const c=new AbortController(),to=setTimeout(()=>c.abort(),ms);try{const r=await fetch(url,{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',signal:c.signal,headers:{accept:'application/json'}});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(to)}}
async function load(force=false){if(busy||(!force&&Date.now()-lastFetch<FETCH_MS))return;busy=true;lastFetch=Date.now();try{const j=await get(KCHA),next=fromKcha(j);items=next;sourceOk=true;if(!visible.length)pickNext();else render()}catch{sourceOk=false;render()}finally{busy=false}}
function tick(){const before=visible.length;visible=visible.filter(x=>age(x.published)<FRESH_MS);if(before!==visible.length){if(!visible.length)pickNext();else render()}if(!paused&&visible.length){nextRotate--;if(nextRotate<=0)pickNext()}updateStatus()}
async function boot(){await load(true);if(!visible.length)pickNext();render();setInterval(tick,1000);setInterval(()=>load(false),1000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)load(true)});window.addEventListener('online',()=>load(true))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();