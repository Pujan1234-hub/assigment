(()=>{
'use strict';
const DEV='०१२३४५६७८९';
const toAscii=s=>String(s??'').replace(/[०-९]/g,d=>String(DEV.indexOf(d)));
const countOf=id=>{
  const el=document.getElementById(id);if(!el)return null;
  const m=toAscii(el.textContent).match(/-?\d+(?:\.\d+)?/);return m?Number(m[0]):null;
};
function toggleCard(card,n){if(!card)return false;const show=Number.isFinite(n)&&n>0;card.style.display=show?'':'none';card.setAttribute('aria-hidden',show?'false':'true');return show}
function apply(){
  const section=document.getElementById('fs23hazards');if(!section)return;
  const land=countOf('fs23landN'),flood=countOf('fs23floodN'),light=countOf('fs23lightN'),fire=countOf('fs23fireN'),acc=countOf('fs23accidentN');
  const shown=[];
  shown.push(toggleCard(section.querySelector('[data-h="landslide"]'),land));
  shown.push(toggleCard(section.querySelector('[data-h="flood"]'),flood));
  shown.push(toggleCard(section.querySelector('[data-h="lightning"]'),light));
  shown.push(toggleCard(section.querySelector('[data-h="fire"]'),fire));
  shown.push(toggleCard(document.getElementById('fs23accidentCard'),acc));
  const ticker=document.getElementById('fs23landTicker');if(ticker?.parentElement)ticker.parentElement.style.display=(Number.isFinite(land)&&land>0)?'':'none';
  section.style.display=shown.some(Boolean)?'':'none';
}
function init(){apply();const obs=new MutationObserver(()=>requestAnimationFrame(apply));obs.observe(document.body,{childList:true,subtree:true,characterData:true});setInterval(apply,1000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,700));else setTimeout(init,700);
})();
