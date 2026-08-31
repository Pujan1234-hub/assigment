(()=>{'use strict';
if(window.__fsLatestOfficialSemanticsV1)return;window.__fsLatestOfficialSemanticsV1=true;
function apply(){const S=window.FloodSafe?.state;if(!S)return;const latest=Array.isArray(S.latestRiverStations)?S.latestRiverStations:(Array.isArray(S.stations)?S.stations:[]);S.currentRiverStations=latest;S.stations=latest;const R=window.__fsRiverRealtimeState;if(R){R.currentCount=latest.length;R.currentMode='latest-official';R.currentMeaning='latest official BIPAD/DHM reading, no arbitrary 5-minute cutoff';}
const f=document.getElementById('feedFresh');if(f){const all=Number(R?.catalogCount||S.allRiverStations?.length||0);f.textContent=`BIPAD/DHM LIVE • ${all} official station • ${latest.length} latest official reading`;}
}
['fstrustedriverupdate','fsriverupdate','fsriverheartbeat'].forEach(n=>window.addEventListener(n,apply));
setInterval(apply,5000);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
})();
