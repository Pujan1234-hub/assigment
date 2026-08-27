(()=>{
'use strict';
const DATA='../../data/national-news.json';
const PAGE=document.body.dataset.page||'home';
const $=id=>document.getElementById(id);
const safeText=v=>String(v??'').trim();
const fmt=t=>{try{return new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kathmandu',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(t))+' NPT'}catch{return''}};
function clear(el){if(el)while(el.firstChild)el.removeChild(el.firstChild)}
function make(tag,cls,text){const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el}
function storyCard(item){
 const box=make('article','item');
 const badge=make('span','tag red',item.flash?'FLASH':'LATEST');box.appendChild(badge);
 box.appendChild(make('h4','',safeText(item.title)));
 const meta=make('div','meta',`${safeText(item.source)}${item.published_at?' • '+fmt(item.published_at):''}`);box.appendChild(meta);
 if(item.url){const row=make('div','meta');const a=make('a','', 'समाचार खोल्नुहोस्');a.href=item.url;a.target='_blank';a.rel='noopener noreferrer';a.referrerPolicy='no-referrer';row.appendChild(a);box.appendChild(row)}
 return box;
}
async function load(){
 let data;try{const r=await fetch(DATA+'?t='+Date.now(),{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error('HTTP '+r.status);data=await r.json()}catch(e){return}
 const items=Array.isArray(data?.items)?data.items:[];
 if(PAGE==='news'){
   const list=$('newsList');if(list){clear(list);items.slice(0,30).forEach(x=>list.appendChild(storyCard(x)));if(!items.length)list.appendChild(make('div','empty','अहिले नयाँ राष्ट्रिय समाचार उपलब्ध छैन।'))}
   if($('newsCount'))$('newsCount').textContent=items.length;
   if($('appStatus'))$('appStatus').textContent='राष्ट्रिय समाचार अपडेट • '+(data?.updated_at_npt||fmt(data?.generated_at));
 }
 if(PAGE==='home'){
   const list=$('homeHot');if(list){clear(list);items.slice(0,4).forEach(x=>list.appendChild(storyCard(x)));if(!items.length)list.appendChild(make('div','empty','अहिले नयाँ राष्ट्रिय समाचार उपलब्ध छैन।'))}
 }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{setTimeout(load,250)});else setTimeout(load,250);
setInterval(load,60000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
window.addEventListener('online',load);
})();
