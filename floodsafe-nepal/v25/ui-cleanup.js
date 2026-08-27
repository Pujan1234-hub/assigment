(()=>{
'use strict';
const $=id=>document.getElementById(id);
function setText(el,next){if(el&&el.textContent!==next)el.textContent=next}
function cleanNumber(id){const el=$(id);if(!el)return;const t=el.textContent.trim().replace(/^≥\s*/, '').replace(/^minimum\s*/i,'');if(t!==el.textContent.trim())setText(el,t)}
function cleanBreakdown(){
 const el=$('peopleBreakdown');if(!el)return;
 const t=el.textContent.trim();
 const m=t.match(/tourists\s+([^•]+)\s*•\s*security\s+([^()]+)\s*\(Army\s+([^,]+),\s*Nepal Police\s+([^,]+),\s*APF\s+([^)]+)\)\.\s*Rescued alive:\s*Nepali\s+([^•]+)\s*•\s*foreign\s+([^\.]+)/i);
 if(m){setText(el,`सम्पर्कविहीन: पर्यटक ${m[1].trim()} • सुरक्षाकर्मी ${m[2].trim()} (नेपाली सेना ${m[3].trim()} • नेपाल प्रहरी ${m[4].trim()} • सशस्त्र प्रहरी ${m[5].trim()}) • उद्धार: नेपाली ${m[6].trim()} • विदेशी ${m[7].trim()}`);return}
 if(/Verified breakdown|लोड हुँदैछ/i.test(t))setText(el,'विवरण लोड हुँदैछ…');
}
function replaceExact(selector,map){document.querySelectorAll(selector).forEach(el=>{const k=el.textContent.trim();if(map[k])setText(el,map[k])})}
function cleanStatus(){const el=$('appStatus');if(!el)return;let t=el.textContent;t=t.replace('Official summaries checked','अपडेट').replace('People sources checked','अपडेट').replace('High-priority sources checked','अपडेट').replace('Priority sources checked','अपडेट').replace('Data temporarily unavailable','डेटा उपलब्ध छैन');if(t!==el.textContent)setText(el,t)}
function cleanCards(){document.querySelectorAll('.item p').forEach(el=>{let t=el.textContent;t=t.replace(/^Count\/record:\s*/i,'संख्या: ').replace(/BIPAD people-loss record/gi,'BIPAD विवरण');if(t!==el.textContent)setText(el,t)})}
function cleanEmpty(){document.querySelectorAll('.empty').forEach(el=>{const t=el.textContent;if(/breaking\/high-priority|महत्वपूर्ण.*भेटिएन/i.test(t))setText(el,'नयाँ महत्वपूर्ण समाचार अहिले उपलब्ध छैन।');else if(/people-loss feed|parse हुन सकेन/i.test(t))setText(el,'नयाँ BIPAD मानव विवरण अहिले उपलब्ध छैन।');else if(/High-priority official alert|Feed unavailable/i.test(t))setText(el,'नयाँ चेतावनी अहिले उपलब्ध छैन।')})}
function clean(){
 cleanNumber('homeMissing');cleanNumber('peopleMissing');cleanBreakdown();cleanStatus();cleanCards();cleanEmpty();
 replaceExact('.tag',{'HIGH ATTENTION':'महत्वपूर्ण','HIGH PRIORITY':'महत्वपूर्ण','CROSS-BORDER WATCH':'सीमापार चेतावनी','ROAD':'सडक','DANGER':'खतरा','WARNING':'चेतावनी','RISING':'बढ्दो','Missing':'सम्पर्कविहीन','Death':'मृत्यु','Rescued':'उद्धार','Injured':'घाइते','People record':'मानव विवरण'});
}
let queued=false;const run=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;clean()})};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
new MutationObserver(run).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
})();