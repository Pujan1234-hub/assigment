(()=>{'use strict';
// Human Status / human-impact reporting is intentionally disabled in FloodSafe Nepal.
// Keep this tiny compatibility file because v25/index.html still references the filename.
// It performs no network requests and removes any legacy Human Status card if old markup
// or cached HTML attempts to render it.
if(window.__fsHumanStatusRemovedV1)return;
window.__fsHumanStatusRemovedV1=true;
function removeHumanStatus(){
  document.getElementById('impact')?.remove();
  document.getElementById('humanStatus')?.remove();
  document.querySelectorAll('[data-human-status],.human-status,.humanStatus').forEach(el=>el.remove());
}
function boot(){
  removeHumanStatus();
  const root=document.body;
  if(!root)return;
  const observer=new MutationObserver(removeHumanStatus);
  observer.observe(root,{childList:true,subtree:true});
  window.addEventListener('pageshow',removeHumanStatus);
  window.addEventListener('fslanguage',removeHumanStatus);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
