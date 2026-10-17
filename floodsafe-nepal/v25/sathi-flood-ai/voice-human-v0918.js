(()=>{
'use strict';
if(window.__SATHI_VOICE_HUMAN_V0918__)return;
window.__SATHI_VOICE_HUMAN_V0918__=true;

let pending=null,lastSpoken='',lastUserCount=0;
const nepali=/[\u0900-\u097f]/;
const clean=s=>String(s||'')
  .replace(/[🔴🟠🟡🔵⚪🌧️☁️⚠️🚨🙂👍👀📍📰🤖]/gu,' ')
  .replace(/[•·]/g,'. ')
  .replace(/\s+/g,' ')
  .trim();

function chooseVoice(lang){
  if(!('speechSynthesis' in window))return null;
  const voices=window.speechSynthesis.getVoices?.()||[];
  const exact=voices.find(v=>String(v.lang||'').toLowerCase()===lang.toLowerCase());
  if(exact)return exact;
  const base=lang.split('-')[0].toLowerCase();
  return voices.find(v=>String(v.lang||'').toLowerCase().startsWith(base))||null;
}

function speak(text){
  const raw=clean(text);if(!raw||raw===lastSpoken)return;
  lastSpoken=raw;
  try{
    if(window.SathiNative&&typeof window.SathiNative.speak==='function'){
      window.SathiNative.speak(raw);return;
    }
  }catch{}
  if(!('speechSynthesis' in window)||typeof SpeechSynthesisUtterance==='undefined')return;
  try{
    window.speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(raw);
    const lang=nepali.test(raw)?'ne-NP':'en-GB';
    u.lang=lang;u.rate=.94;u.pitch=1.03;u.volume=1;
    const voice=chooseVoice(lang);if(voice)u.voice=voice;
    window.speechSynthesis.speak(u);
  }catch{}
}

function scheduleFromPanel(){
  const box=document.querySelector('#sathiFloodMsgs');if(!box)return;
  const users=box.querySelectorAll('.sathiMsg.user');
  if(!users.length||users.length<lastUserCount)return;
  lastUserCount=users.length;
  clearTimeout(pending);
  pending=setTimeout(()=>{
    const msgs=[...box.querySelectorAll('.sathiMsg.ai')];
    const last=msgs[msgs.length-1];
    if(last&&last.textContent?.trim())speak(last.textContent);
  },420);
}

const observer=new MutationObserver(mutations=>{
  let touched=false;
  for(const m of mutations){
    for(const n of m.addedNodes||[]){
      if(!(n instanceof Element))continue;
      if(n.matches?.('.sathiMsg.ai,.sathiMsg.user')||n.querySelector?.('.sathiMsg.ai,.sathiMsg.user'))touched=true;
    }
    if(m.type==='characterData'&&m.target?.parentElement?.closest?.('.sathiMsg.ai'))touched=true;
  }
  if(touched)scheduleFromPanel();
});

function boot(){
  observer.observe(document.body,{childList:true,subtree:true,characterData:true});
  const box=document.querySelector('#sathiFloodMsgs');
  if(box)lastUserCount=box.querySelectorAll('.sathiMsg.user').length;
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();

window.SathiVoiceV0918={speak,stop(){try{window.speechSynthesis?.cancel?.()}catch{}}};
})();
