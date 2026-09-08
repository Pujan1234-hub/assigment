(()=>{'use strict';
// FloodSafe: the extra disaster/news card is intentionally removed.
// National/general news remains only in the existing #bulletin section.
if(window.__floodsafeDisasterCardRemovedV1)return;
window.__floodsafeDisasterCardRemovedV1=true;
function removeExtraCard(){
  const card=document.getElementById('disasterStatus');
  if(card)card.remove();
  window.__floodsafeDisasterState={active:null,removed:true,checkedAt:new Date().toISOString()};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',removeExtraCard,{once:true});
else removeExtraCard();
})();
