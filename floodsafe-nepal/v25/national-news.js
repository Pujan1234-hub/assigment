(()=>{
'use strict';
const PAGE=document.body.dataset.page||'home',$=id=>document.getElementById(id);
const KCHA='https://kchakhabar.com/api/v1/today.json?limit=100',LOCAL='../../data/national-news.json';
const ROTATE_SEC=30,FLASH_MS=60*60*1000,RECENT_MS=6*60*60*1000,FETCH_MS=30*1000;
let items=[],visible=[],sourceOk=false,nextRotate=ROTATE_SEC,lastFetch=0,busy=false,paused=false,pauseBtn=null,waitingNew=false;
const seen=new Set(),known=new Set();
const norm=s=>String(s||'').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const age=t=>{const x=+new Date(t||0);if(!x)return Infinity;return Math.max(0,Date.now()-x)};
const isFlash=x=>age(x?.published)<FLASH_MS;
const isRecent=x=>age(x?.published)<RECENT_MS;
function make(tag,cls,t){const e=document.createElement(tag);if(cls)e.className=cls;if(t!==undefined)e.textContent=t;return e}
function clear(e){if(e)while(e.firstChild)e.removeChild(e.firstChild)}
function fmt(t){try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',day:'numeric',month:'short'}).format(new Date(t))}catch{return''}}
function ago(t){const m=Math.max(0,Math.floor(age(t)/60000));if(m<1)return'भर्खर';if(m<60)return m+' मिनेट अघि';return Math.floor(m/60)+' घण्टा '+(m%60)+' मिनेट अघि'}
function keyOf(x){return norm(x.title)}
function nearDup(a,b){return a===b||((a.includes(b)||b.includes(a))&&Math.min(a.length,b.length)>24)}
function dedup(list){const out=[],keys=[];for(const x of list){const k=keyOf(x);if(!k||keys.some(s=>nearDup(k,s)))continue;keys.push(k);out.push(x)}return out}
function fromKcha(j){const raw=Array.isArray(j?.stories)?j.stories:[];return raw.map(s=>{const src=s.sources?.[0],published=s.first_reported||s.updated_at;return{id:String(s.id||''),title:s.topic_ne||s.topic_en||'',source:src?.publisher||'Nepal media',url:src?.url||s.url,published,updated:s.updated_at||published,score:+new Date(published||0)}}).filter(x=>x.title&&x.published&&isRecent(x))}
function fromLocal(j){if(!Array.isArray(j?.items))return[];return j.items.map((x,i)=>{const published=x.published_at||x.published||x.pub_date||x.date||null;return{id:'local-'+i,title:x.title||'',source:x.source||'Nepal media',url:x.url||'',published,updated:published,score:+new Date(published||0)}}).filter(x=>x.title&&x.published&&isRecent(x))}
function mergeFeeds(k,l){return dedup([...(k||[]),...(l||[])]).filter(isRecent).sort((a,b)=>(b.score||0)-(a.score||0)).slice(0,50)}
function storyCard(x){const box=make('article','item');box.dataset.newsKey=keyOf(x);box.dataset.newsKind=isFlash(x)?'flash':'latest';box.appendChild(make('span',isFlash(x)?'tag red':'tag',''+(isFlash(x)?'FLASH':'LATEST')));box.appendChild(make('h4','',x.title));box.appendChild(make('div','meta',x.source+' • '+ago(x.published)+(x.published?' • '+fmt(x.published):'')));if(x.url){const r=make('div','meta'),a=make('a','','समाचार खोल्नुहोस्');a.href=x.url;a.target='_blank';a.rel='noopener noreferrer';a.referrerPolicy='no-referrer';r.appendChild(a);box.appendChild(r)}return box}
function currentKind(){return visible.some(isFlash)?'flash':visible.length?'latest':'none'}
function statusText(){if(!sourceOk)return'समाचार स्रोत फेरि जाँच हुँदैछ…';if(paused)return'समाचार • पढ्नका लागि रोकिएको';if(waitingNew)return'उपलब्ध नयाँ समाचार देखाइयो • नयाँ समाचार पर्खिँदै…';const k=currentKind();if(k==='flash')return'Flash News • पछिल्लो १ घण्टा मात्र • अर्को '+nextRotate+' sec';if(k==='latest')return'पछिल्लो १ घण्टामा Flash छैन • पछिल्ला verified समाचार • अर्को '+nextRotate+' sec';return'नयाँ समाचार पर्खिँदै…'}
function updateStatus(){const s=statusText();if($('appStatus'))$('appStatus').textContent=s;if($('homeNewsFresh'))$('homeNewsFresh').textContent=s;if($('healthNews'))$('healthNews').textContent=sourceOk?'समाचार स्रोत जोडिएको':'समाचार स्रोत फेरि जाँच हुँदैछ';if(pauseBtn)pauseBtn.textContent=paused?'▶️ समाचार चलाउनुहोस्':'⏸ समाचार रोक्नुहोस्'}
function ensurePause(){const list=PAGE==='nationalnews'?$('newsList'):$('nationalHomeNews');if(!list||pauseBtn)return;pauseBtn=make('button','newsPause',paused?'▶️ समाचार चलाउनुहोस्':'⏸ समाचार रोक्नुहोस्');pauseBtn.type='button';pauseBtn.setAttribute('aria-pressed',String(paused));pauseBtn.style.cssText='margin:0 0 10px;padding:8px 12px;border-radius:999px;border:1px solid #6d4b3e;background:#1a1110;color:#fff;font-weight:850;font-size:12px;cursor:pointer';pauseBtn.addEventListener('click',()=>{paused=!paused;pauseBtn.setAttribute('aria-pressed',String(paused));if(!paused&&!waitingNew&&nextRotate<=0)nextRotate=ROTATE_SEC;updateStatus()});list.parentElement?.insertBefore(pauseBtn,list)}
function render(){const list=PAGE==='nationalnews'?$('newsList'):$('nationalHomeNews');if(!list)return;ensurePause();items=items.filter(isRecent);visible=visible.filter(isRecent);clear(list);if(!visible.length){list.appendChild(make('div','empty',sourceOk?'अहिले verified नयाँ समाचार भेटिएको छैन • स्रोत फेरि जाँच हुँदैछ…':'ताजा समाचार खोजिँदैछ…'));if($('newsCount'))$('newsCount').textContent=items.length||0;updateStatus();return}visible.forEach(x=>list.appendChild(storyCard(x)));if($('newsCount'))$('newsCount').textContent=items.length;updateStatus()}
function take(list){const count=PAGE==='nationalnews'?6:3;return list.slice(0,count)}
function showBatch(batch){batch=batch.filter(isRecent);if(!batch.length)return false;visible=batch;for(const x of batch)seen.add(keyOf(x));waitingNew=false;nextRotate=ROTATE_SEC;render();return true}
function unseen(list){return list.filter(x=>!seen.has(keyOf(x)))}
function pickNext(){items=items.filter(isRecent);const flash=unseen(items.filter(isFlash));if(showBatch(take(flash)))return;const latest=unseen(items.filter(x=>!isFlash(x)&&isRecent(x)));if(showBatch(take(latest)))return;visible=[];waitingNew=true;nextRotate=0;render()}
async function get(url,ms=7000){const c=new AbortController(),to=setTimeout(()=>c.abort(),ms);try{const r=await fetch(url,{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',signal:c.signal,headers:{accept:'application/json'}});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(to)}}
async function load(force=false){if(busy||(!force&&Date.now()-lastFetch<FETCH_MS))return;busy=true;lastFetch=Date.now();try{const [ka,lo]=await Promise.allSettled([get(KCHA,7000),get(LOCAL+'?t='+Date.now(),5000)]),k=ka.status==='fulfilled'?fromKcha(ka.value):[],l=lo.status==='fulfilled'?fromLocal(lo.value):[],next=mergeFeeds(k,l);sourceOk=ka.status==='fulfilled'||lo.status==='fulfilled';const brandNew=next.filter(x=>!known.has(keyOf(x)));items=next;for(const x of next)known.add(keyOf(x));visible=visible.filter(x=>isRecent(x)&&next.some(n=>keyOf(n)===keyOf(x)));
const freshNew=brandNew.filter(isFlash).filter(x=>!seen.has(keyOf(x)));if(freshNew.length){showBatch(take(freshNew));return}
if(!visible.length){pickNext();return}
render()}catch{sourceOk=false;render()}finally{busy=false}}
function tick(){const before=visible.map(x=>keyOf(x)+':' +(isFlash(x)?'f':'l')).join('|');items=items.filter(isRecent);visible=visible.filter(isRecent);const after=visible.map(x=>keyOf(x)+':' +(isFlash(x)?'f':'l')).join('|');if(before!==after){if(!visible.length)pickNext();else render()}if(!paused&&!waitingNew&&visible.length){nextRotate--;if(nextRotate<=0)pickNext()}updateStatus()}
async function boot(){await load(true);if(!visible.length)pickNext();render();setInterval(tick,1000);setInterval(()=>load(false),15000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)load(true)});window.addEventListener('online',()=>load(true))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();