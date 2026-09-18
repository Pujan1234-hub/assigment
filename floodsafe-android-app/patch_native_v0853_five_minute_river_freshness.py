from pathlib import Path
import re

root = Path(__file__).resolve().parent
app = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
web = root.parent / 'floodsafe-nepal' / 'v25'

def replace_once(path, old, new, label):
    text = path.read_text(encoding='utf-8')
    if old in text:
        text = text.replace(old, new, 1)
        path.write_text(text, encoding='utf-8')
        return
    if new in text:
        return
    raise SystemExit(f'{label} anchor missing in {path}')

# Native dashboard: never treat an official river reading older than 5 minutes as current.
replace_once(
    app / 'NativeFullActivity.java',
    'RIVER_FRESH_MS=10L*60L*1000L',
    'RIVER_FRESH_MS=5L*60L*1000L',
    'native river freshness'
)

# Closed-app WorkManager warning/danger filter: keep 2 km logic untouched, tighten age only.
replace_once(
    app / 'RiverAlertWorker.java',
    'MAX_AGE_MS = 10L * 60L * 1000L',
    'MAX_AGE_MS = 5L * 60L * 1000L',
    'background river alert freshness'
)

# FCM warning/danger filter: keep 2 km logic untouched, tighten age only.
replace_once(
    app / 'FloodSafeMessagingService.java',
    'MAX_RIVER_AGE_MS = 10L * 60L * 1000L',
    'MAX_RIVER_AGE_MS = 5L * 60L * 1000L',
    'FCM river freshness'
)

# Compatibility river runtime bundled in the APK: strict observation age, not "same Nepal day".
trusted_path = web / 'trusted-river-runtime-v3.js'
trusted = trusted_path.read_text(encoding='utf-8')
trusted = trusted.replace('const FRESH_MS=10*60*1000,', 'const FRESH_MS=5*60*1000,', 1)
trusted, n = re.subn(
    r"function isCurrentTime\(t\)\{const a=ageMs\(t\);return Number\.isFinite\(a\)&&a>=-FUTURE_MS&&Math\.floor\(\(Date\.parse\(t\)\+20700000\)/86400000\)===Math\.floor\(\(Date\.now\(\)\+20700000\)/86400000\)\}",
    "function isCurrentTime(t){const a=ageMs(t);return Number.isFinite(a)&&a>=-FUTURE_MS&&a<=FRESH_MS}",
    trusted,
    count=1,
)
if n == 0 and 'a<=FRESH_MS' not in trusted:
    raise SystemExit('trusted river isCurrentTime anchor missing')

trusted, n = re.subn(
    r"function armExpiry\(input\)\{clearTimeout\(expiryTimer\);let wait=Infinity;for\(const o of input\|\|\[\]\)\{if\(!rawHasObservation\(o\)\)continue;const t=\+new Date\(measureTime\(o\)\|\|0\);if\(!t\)continue;const left=\(Math\.floor\(\(Date\.now\(\)\+20700000\)/86400000\)\+1\)\*86400000-20700000-Date\.now\(\);if\(left>0&&left<wait\)wait=left\}if\(Number\.isFinite\(wait\)\)expiryTimer=setTimeout\(\(\)=>\{if\(lastRaw\.length\)\{publish\(lastRaw,lastSource,true\);kick\(0\)\}\},Math\.max\(80,wait\+40\)\)\}",
    "function armExpiry(input){clearTimeout(expiryTimer);let wait=Infinity;for(const o of input||[]){if(!rawHasObservation(o))continue;const t=+new Date(measureTime(o)||0);if(!t)continue;const left=FRESH_MS-(Date.now()-t);if(left>0&&left<wait)wait=left}if(Number.isFinite(wait))expiryTimer=setTimeout(()=>{if(lastRaw.length){publish(lastRaw,lastSource,true);kick(0)}},Math.max(80,wait+40))}",
    trusted,
    count=1,
)
if n == 0 and 'const left=FRESH_MS-(Date.now()-t)' not in trusted:
    raise SystemExit('trusted river expiry anchor missing')
trusted = trusted.replace('if(a>8*60*1000)return POLL_NEAR_STALE', 'if(a>4*60*1000)return POLL_NEAR_STALE', 1)
trusted_path.write_text(trusted, encoding='utf-8')

# Android display policy used by bundleFloodSafe. Always clear stale rows after 5 minutes.
display_path = web / 'latest-official-display-policy-v1.js'
display_path.write_text("""(()=>{'use strict';
if(window.__fsLatestOfficialDisplayPolicyV1)return;window.__fsLatestOfficialDisplayPolicyV1=true;
const FUTURE=5*60*1000,MAX_AGE=5*60*1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const num=v=>{if(v===null||v===undefined||v==='')return null;const n=Number(String(v).replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const time=o=>val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','observation_time','observedAt','observed_at','datetime','timestamp']);
const level=o=>num(val(o,['_lastWaterLevel','waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','value']));
const current=t=>{const x=Date.parse(t||'');if(!Number.isFinite(x))return false;const age=Date.now()-x;return age>=-FUTURE&&age<=MAX_AGE};
function restore(){const S=window.FloodSafe?.state;if(!S)return;const all=Array.isArray(S.allRiverStations)?S.allRiverStations:[];const latest=all.filter(o=>level(o)!==null&&current(time(o)));S.latestRiverStations=latest;S.currentRiverStations=latest;S.stations=latest;S.riverObservations=latest;S.lastRiverReadings=latest;const old=window.__fsRiverRealtimeState||{};window.__fsRiverRealtimeState={...old,latestCount:latest.length,currentCount:latest.length,withoutObservationCount:Math.max(0,all.length-latest.length),observationPolicy:'official reading <= 5 minutes',freshWindowMinutes:5,displayMode:'fresh-official-5m',checkedAt:new Date().toISOString()};window.dispatchEvent(new CustomEvent('fsriverupdate',{detail:window.__fsRiverRealtimeState}));}
for(const e of['fstrustedriverupdate','fsriverheartbeat','pageshow','online'])window.addEventListener(e,restore);
setInterval(()=>{if(!document.hidden)restore()},2000);
})();
""", encoding='utf-8')

# Keep the unused web stale-safety asset internally consistent too.
stale_path = web / 'official-stale-safety-v1.js'
stale = stale_path.read_text(encoding='utf-8')
stale = stale.replace('const CURRENT_MS=10*60*1000,', 'const CURRENT_MS=5*60*1000,', 1)
stale = stale.replace('windowMinutes:10', 'windowMinutes:5', 1)
stale_path.write_text(stale, encoding='utf-8')

# New installable build identity.
gradle_path = root / 'app/build.gradle'
gradle = gradle_path.read_text(encoding='utf-8')
if 'versionCode 72' in gradle:
    gradle = gradle.replace('versionCode 72', 'versionCode 73', 1)
elif 'versionCode 73' not in gradle:
    raise SystemExit('v0853 versionCode anchor missing')
if "versionName '0.8.52'" in gradle:
    gradle = gradle.replace("versionName '0.8.52'", "versionName '0.8.53'", 1)
elif "versionName '0.8.53'" not in gradle:
    raise SystemExit('v0853 versionName anchor missing')
gradle_path.write_text(gradle, encoding='utf-8')

# Fail build rather than silently shipping a 10-minute warning path.
checks = {
    app / 'NativeFullActivity.java': ['RIVER_FRESH_MS=5L*60L*1000L'],
    app / 'RiverAlertWorker.java': ['MAX_AGE_MS = 5L * 60L * 1000L', 'RADIUS_KM = 2d'],
    app / 'FloodSafeMessagingService.java': ['MAX_RIVER_AGE_MS = 5L * 60L * 1000L', 'DEFAULT_RIVER_RADIUS_KM = 2d'],
    trusted_path: ['FRESH_MS=5*60*1000', 'a<=FRESH_MS', 'const left=FRESH_MS-(Date.now()-t)'],
    display_path: ['MAX_AGE=5*60*1000', 'freshWindowMinutes:5', "displayMode:'fresh-official-5m'"],
    gradle_path: ['versionCode 73', "versionName '0.8.53'"],
}
for path, needles in checks.items():
    text = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v0853 verification failed: {needle} in {path}')

print('FloodSafe v0.8.53 FIVE-MINUTE river freshness + 2 km alert safety PASS')
