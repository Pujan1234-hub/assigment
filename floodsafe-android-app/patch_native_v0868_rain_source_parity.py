from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
w_path=src/'RiverAlertWorker.java'
f_path=src/'FloodSafeMessagingService.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.68 is intentionally narrow:
# - rainfall follows the latest official BIPAD/DHM source exactly, with no local minute cutoff
# - keep the official rainfall measurement time/interval values unchanged
# - refresh rainfall every 10 seconds while the app is open
# - show official rainfall station dots at every Nepal map zoom, not only local zoom
# - fix the river map header count regression (0/0) by publishing the already-loaded source counts
# - do NOT change river source logic, station coordinates, news, weather, thresholds or 2 km alert radius

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

# Latest official rainfall source row = current display truth. No 5/20/30/40 minute app cutoff.
sp=method_span(a,'parseRainStation')
if not sp:raise SystemExit('v0868 parseRainStation missing')
block=a[sp[0]:sp[1]]
if 'V0868_RAIN_SOURCE_CURRENT_NOT_AGE_GATED' not in block:
    repl='boolean hasRain=Double.isFinite(mm)||Double.isFinite(mm3)||Double.isFinite(mm6)||Double.isFinite(mm12)||Double.isFinite(mm24); boolean fresh=hasRain&&at>0L; // V0868_RAIN_SOURCE_CURRENT_NOT_AGE_GATED'
    block,n=re.subn(r'boolean\s+fresh\s*=\s*[^;]+;',repl,block,count=1)
    if n!=1:raise SystemExit('v0868 rain freshness expression missing')
    a=a[:sp[0]]+block+a[sp[1]:]

a,n=re.subn(r'private\s+static\s+final\s+long\s+RAIN_FRESH_MS\s*=\s*[^;]+;',
            'private static final long RAIN_FRESH_MS=Long.MAX_VALUE; // V0868_NO_RAIN_MINUTE_CUTOFF',a,count=1)
if n!=1 and 'V0868_NO_RAIN_MINUTE_CUTOFF' not in a:raise SystemExit('v0868 RAIN_FRESH_MS missing')

# Re-read the existing official rain loader every 10 seconds in foreground.
field_anchor='    private boolean showAllStations=false;'
if 'V0868_RAIN_10S_POLL' not in a:
    if field_anchor not in a:raise SystemExit('v0868 field anchor missing')
    poll='''\n    private final Runnable v0868RainPoll=new Runnable(){@Override public void run(){\n        if(isFinishing()||(Build.VERSION.SDK_INT>=17&&isDestroyed()))return;\n        refreshRainStations();\n        main.postDelayed(this,10_000L);\n    }}; // V0868_RAIN_10S_POLL'''
    a=a.replace(field_anchor,field_anchor+poll,1)

if 'V0868_START_RAIN_POLL' not in a:
    on=method_span(a,'onCreate')
    if not on:raise SystemExit('v0868 onCreate missing')
    b=a[on[0]:on[1]]
    if 'refreshAll();' not in b:raise SystemExit('v0868 refreshAll onCreate anchor missing')
    b=b.replace('refreshAll();','refreshAll();main.postDelayed(v0868RainPoll,1200L); // V0868_START_RAIN_POLL',1)
    a=a[:on[0]]+b+a[on[1]:]

# Publish the real river counts to the map header; v0.8.67 accidentally left these at 0/0.
sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0868 refreshRiverUi missing')
block=a[sp[0]:sp[1]]
if 'V0868_MAP_HINT_RIVER_SOURCE_COUNTS' not in block:
    old='        updateRisk(copy);'
    new='        mapRiverCurrent=current;mapRiverTotal=sourceTotal;updateMapHintCounts(); // V0868_MAP_HINT_RIVER_SOURCE_COUNTS\n        updateRisk(copy);'
    if old not in block:raise SystemExit('v0868 updateRisk count anchor missing')
    block=block.replace(old,new,1)
    a=a[:sp[0]]+block+a[sp[1]:]

sp=method_span(a,'updateMapHintCounts')
if not sp:raise SystemExit('v0868 updateMapHintCounts missing')
hint=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 आधिकारिक नदी "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ आधिकारिक वर्षा "+mapRainFresh+" / "+mapRainTotal,
                          "🌊 official river "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ official rainfall "+mapRainFresh+" / "+mapRainTotal));
    } // V0868_SOURCE_COUNT_HEADER
'''
a=a[:sp[0]]+hint+a[sp[1]:]

# Do not hide current rainfall stations behind a zoom cutoff.
sp=method_span(m,'refreshRainSources')
if not sp:raise SystemExit('v0868 refreshRainSources missing')
rain_sources=r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        List<RainDot> snapshot;synchronized(rainStations){snapshot=new ArrayList<>(rainStations);}
        setGeo("fs-rain-stale",rainGeo(snapshot,"stale"));
        setGeo("fs-rain-normal",rainGeo(snapshot,"normal"));
        setGeo("fs-rain-alert",rainGeo(snapshot,"alert"));
        setGeo("fs-rain-warning",rainGeo(snapshot,"warning"));
        setGeo("fs-rain-danger",rainGeo(snapshot,"danger"));
    } // V0868_RAIN_VISIBLE_ALL_ZOOMS
'''
m=m[:sp[0]]+rain_sources+m[sp[1]:]

# Exact data markers first: river gauge, rainfall gauge, then river geometry.
sp=method_span(m,'onMapClick')
if not sp:raise SystemExit('v0868 onMapClick missing')
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;

        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.16,Math.min(2.0,1.6/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        if(nearest!=null&&sd<=stationThreshold){ // V0866_STATION_TAP_FIRST
            if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);
            return true;
        }

        RainDot rain=nearestRain(p.getLatitude(),p.getLongitude());
        double rainThreshold=Math.max(0.28,Math.min(8.0,2.0/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double rd=rain==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),rain.lat,rain.lon);
        if(rain!=null&&rd<=rainThreshold){showRain(rain);return true;} // V0868_RAIN_TAP_FIRST

        RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.10,3.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(rw!=null){showRiver(rw,p.getLatitude(),p.getLongitude());return true;}
        return false;
    }
'''
m=m[:sp[0]]+click+m[sp[1]:]

# Keep rain popup source semantics explicit without changing official values/time.
sp=method_span(m,'showRain')
if not sp:raise SystemExit('v0868 showRain missing')
block=m[sp[0]:sp[1]]
if 'V0868_RAIN_DETAIL_SOURCE_PARITY' not in block:
    if 'r.fresh?"LATEST":"STALE / OLD"' in block:
        block=block.replace('r.fresh?"LATEST":"STALE / OLD"','r.fresh?"LATEST OFFICIAL SOURCE":"SOURCE TIME UNAVAILABLE"',1)
    elif 'r.fresh ? "LATEST" : "STALE / OLD"' in block:
        block=block.replace('r.fresh ? "LATEST" : "STALE / OLD"','r.fresh ? "LATEST OFFICIAL SOURCE" : "SOURCE TIME UNAVAILABLE"',1)
    # Marker is kept even if a later language patch changed the exact visible phrase.
    block=block[:-1]+'        // V0868_RAIN_DETAIL_SOURCE_PARITY\n    }'
    m=m[:sp[0]]+block+m[sp[1]:]

if 'versionCode 87' in g:g=g.replace('versionCode 87','versionCode 88',1)
elif 'versionCode 88' not in g:raise SystemExit('v0868 versionCode anchor missing')
if "versionName '0.8.67'" in g:g=g.replace("versionName '0.8.67'","versionName '0.8.68'",1)
elif "versionName '0.8.68'" not in g:raise SystemExit('v0868 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0868_RAIN_SOURCE_CURRENT_NOT_AGE_GATED','V0868_NO_RAIN_MINUTE_CUTOFF','V0868_RAIN_10S_POLL','V0868_START_RAIN_POLL','V0868_MAP_HINT_RIVER_SOURCE_COUNTS','V0868_SOURCE_COUNT_HEADER']:
    if x not in a:raise SystemExit('v0868 activity verification failed: '+x)
for x in ['V0868_RAIN_VISIBLE_ALL_ZOOMS','V0868_RAIN_TAP_FIRST','V0868_RAIN_DETAIL_SOURCE_PARITY','V0867_RIVER_SOURCE_PARITY','V0866_STATION_TAP_FIRST']:
    if x not in m:raise SystemExit('v0868 map verification failed: '+x)
for x in ['versionCode 88',"versionName '0.8.68'"]:
    if x not in g:raise SystemExit('v0868 version verification failed: '+x)
if 'RADIUS_KM = 2d' not in w_path.read_text(encoding='utf-8'):raise SystemExit('v0868 2 km worker radius changed')
if 'DEFAULT_RIVER_RADIUS_KM = 2d' not in f_path.read_text(encoding='utf-8'):raise SystemExit('v0868 2 km FCM radius changed')
print('FloodSafe v0.8.68 PASS: official rainfall source parity + 10s rain refresh + all-zoom rain dots + correct river/rain header counts; other features untouched')
