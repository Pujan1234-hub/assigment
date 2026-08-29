(()=>{'use strict';
if(window.__fsNewsLiveV5)return;window.__fsNewsLiveV5=true;
const out=()=>document.getElementById('liveNews');
const KCHA='https://kchakhabar.com/api/v1/today.json?limit=100';
const RONB='https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=30&_fields=date_gmt,modified_gmt,link,title';
const MAJOR=/routine of nepal|ronb|onlinekhabar|ratopati|setopati|kantipur|kathmandu post|radio nepal|gorkhapatra|nepal news|republica|baahrakhari|himal khabar|annapurna|nepal press|ujyaalo|ekantipur|nagarik/i;
const FRESH=30*60*1000;
let ronbCache=[],mediaCache=[],lastRonb=0,lastMedia=0;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const strip=s=>String(s??'').replace(/<[^>]+>/g,' ').replace(/&nbsp;|&#8211;|&#8212;|&#8230;/g,' ').replace(/&amp;/g,'&').replace(/\s+/g,' ').trim();
const ts=v=>{const n=+new Date(v||0);return Number.isFinite(n)?n:0};
const gmt=v=>v?String(v).replace(/Z$/,'')+'Z':null;
async function get(u,ms=7000){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);try{const r=await fetch(u+(u.includes('?')?'&':'?')+'_live='+Date.now(),{cache:'no-store',credentials:'omit',signal:c.signal,headers:{accept:'application/json'}});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(t)}}
function fromKcha(j){const a=Array.isArray(j?.stories)?j.stories:Array.isArray(j?.items)?j.items:Array.isArray(j?.data)?j.data:[];return a.map(x=>{const s=x.sources?.[0]||{};return{title:x.topic_ne||x.title_ne||x.title||x.headline||x.topic_en||'',source:s.publisher||x.publisher||x.source||x.source_name||'Nepal media',url:s.url||x.url||x.link||'',time:x.updated_at||x.published_at||x.first_reported||x.date}}).filter(x=>MAJOR.test(x.source))}
function fromRonb(j){return(Array.isArray(j)?j:[]).map(x=>({title:strip(x?.title?.rendered||''),source:'RONB Post',url:x.link||'',time:gmt(x.date_gmt||x.modified_gmt)}))}
function npt(t){try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(t))+' NPT'}catch{return''}}
function age(t){const m=Math.max(0,Math.floor((Date.now()-ts(t))/60000));return m<1?'अहिले':`${m} मिनेट अघि`}
function render(){const el=out();if(!el)return;const now=Date.now(),seen=new Set();const list=[...ronbCache,...mediaCache].filter(x=>x.title&&ts(x.time)>0&&now-ts(x.time)>=-300000&&now-ts(x.time)<=FRESH).filter(x=>{const k=x.title.toLowerCase().replace(/\W+/g,' ').trim();if(!k||seen.has(k))return false;seen.add(k);return true}).sort((a,b)=>ts(b.time)-ts(a.time)).slice(0,30);el.innerHTML='';if(!list.length){el.innerHTML='<div class="empty"><strong>अहिले पछिल्लो ३० मिनेटमा नयाँ verified national news छैन।</strong><br>पुरानो समाचार देखाइएको छैन।</div>';return}for(const x of list){const a=document.createElement('article');a.className='newsItem'+(/ronb/i.test(x.source)?' ronbNews':'');a.innerHTML=`<h4>${esc(x.title)}</h4><div class="meta">${esc(x.source)} • ${esc(age(x.time))} • ${esc(npt(x.time))} <b class="liveDot">NEW</b></div>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">समाचार खोल्नुहोस् ↗</a>`:''}`;el.appendChild(a)}}
async function syncRonb(force=false){if(!force&&Date.now()-lastRonb<10000)return;lastRonb=Date.now();try{ronbCache=fromRonb(await get(RONB,6500))}catch{}render()}
async function syncMedia(force=false){if(!force&&Date.now()-lastMedia<60000)return;lastMedia=Date.now();try{mediaCache=fromKcha(await get(KCHA,8500))}catch{}render()}
function boot(){const m=document.querySelector('#bulletin .head .muted');if(m)m.textContent='RONB + verified राष्ट्रिय मिडिया • पछिल्लो ३० मिनेटका नयाँ पोस्ट मात्र';syncRonb(true);syncMedia(true);setInterval(()=>syncRonb(false),10000);setInterval(()=>syncMedia(false),60000);setInterval(render,10000);document.addEventListener('visibilitychange',()=>{if(!document.hidden){syncRonb(true);syncMedia(true)}});window.addEventListener('online',()=>{syncRonb(true);syncMedia(true)})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();