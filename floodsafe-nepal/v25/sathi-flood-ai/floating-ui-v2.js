(()=>{
'use strict';
if(window.__SATHI_FLOATING_UI_V2__) return;
window.__SATHI_FLOATING_UI_V2__=true;

function applyFloatingSathi(){
  const btn=document.getElementById('sathiFloodBtn');
  const panel=document.getElementById('sathiFloodPanel');
  if(!btn){setTimeout(applyFloatingSathi,120);return;}

  if(btn.parentElement!==document.body) document.body.appendChild(btn);
  btn.classList.add('sathiFloatingFab');

  if(!document.getElementById('sathiFloatingV2Style')){
    const style=document.createElement('style');
    style.id='sathiFloatingV2Style';
    style.textContent=`
#sathiFloodBtn.sathiFloatingFab{
  position:fixed!important;
  right:max(18px,env(safe-area-inset-right))!important;
  bottom:max(96px,calc(env(safe-area-inset-bottom) + 84px))!important;
  left:auto!important;
  top:auto!important;
  z-index:2147482998!important;
  margin:0!important;
  order:unset!important;
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  gap:8px!important;
  min-height:48px!important;
  padding:12px 16px!important;
  border:1px solid rgba(255,255,255,.42)!important;
  border-radius:999px!important;
  background:linear-gradient(135deg,#0b6ff4,#315cf4)!important;
  color:#fff!important;
  box-shadow:0 14px 34px rgba(11,70,170,.34),0 4px 10px rgba(0,0,0,.12)!important;
  backdrop-filter:blur(10px);
  -webkit-backdrop-filter:blur(10px);
  font:800 13px/1.1 system-ui,-apple-system,Segoe UI,sans-serif!important;
  white-space:nowrap!important;
  transform:translateZ(0);
  transition:transform .18s ease,box-shadow .18s ease,opacity .18s ease!important;
}
#sathiFloodBtn.sathiFloatingFab:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 18px 40px rgba(11,70,170,.4),0 5px 12px rgba(0,0,0,.14)!important}
#sathiFloodBtn.sathiFloatingFab:active{transform:scale(.97)}
#sathiFloodBtn.sathiFloatingFab>span:first-child{font-size:18px;line-height:1}
#sathiFloodBtn.sathiFloatingFab .sathiDot{width:8px!important;height:8px!important;flex:0 0 8px!important;background:#67e8a5!important;box-shadow:0 0 0 3px rgba(103,232,165,.22),0 0 12px rgba(103,232,165,.75)!important}
#sathiFloodPanel.open~#sathiFloodBtn.sathiFloatingFab{opacity:0;pointer-events:none}
@media(max-width:620px){
  #sathiFloodBtn.sathiFloatingFab{
    right:max(12px,env(safe-area-inset-right))!important;
    bottom:max(88px,calc(env(safe-area-inset-bottom) + 78px))!important;
    min-height:46px!important;
    padding:11px 14px!important;
    font-size:12px!important;
    max-width:calc(100vw - 24px)!important;
  }
}
@media(max-width:380px){
  #sathiFloodBtn.sathiFloatingFab{padding:11px 12px!important}
  #sathiFloodBtn.sathiFloatingFab>span:nth-child(2){max-width:118px;overflow:hidden;text-overflow:ellipsis}
}
`;
    document.head.appendChild(style);
  }

  // Keep the assistant above FloodSafe's fixed bottom navigation without changing any existing navigation code.
  const bottomNav=document.querySelector('nav.bottom,.bottom');
  const placeFab=()=>{
    if(!bottomNav)return;
    const r=bottomNav.getBoundingClientRect();
    if(r.height>0 && r.top<innerHeight){
      const gap=14;
      const lift=Math.max(84,Math.ceil(innerHeight-r.top)+gap);
      btn.style.setProperty('bottom',`max(${lift}px, calc(env(safe-area-inset-bottom) + ${lift-10}px))`,'important');
    }
  };
  placeFab();
  addEventListener('resize',placeFab,{passive:true});
  addEventListener('orientationchange',()=>setTimeout(placeFab,120),{passive:true});

  if(panel){
    const observer=new MutationObserver(()=>{
      btn.style.opacity=panel.classList.contains('open')?'0':'1';
      btn.style.pointerEvents=panel.classList.contains('open')?'none':'auto';
    });
    observer.observe(panel,{attributes:true,attributeFilter:['class']});
  }
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',applyFloatingSathi,{once:true});
else applyFloatingSathi();
})();
