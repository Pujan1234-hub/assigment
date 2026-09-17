from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.28 MAP-ONLY FINISH.
# User contract:
# - every river line stays blue; warning/danger is shown by station dots/details, not by recolouring rivers
# - camera stays inside Nepal and cannot zoom out to a broad India/China view
# - station dots use the latest official BIPAD/DHM reading colour even when the reading is older than
#   the strict live/current window; the detail card clearly labels old readings as NOT CURRENT
# - alert/push/2 km safety logic is deliberately untouched

RIVER_BLUE='#168BFF'

# -----------------------------------------------------------------------------
# Native river visual: ALL river geometry/status overlays are blue.
# Station dots keep their own normal/alert/warning/danger palette.
# -----------------------------------------------------------------------------
for status in ('normal','alert','warning','danger'):
    pat=(r'ensureRiverStatusLayer\("fs-river-'+status+r'-status",\s*'
         r'"fs-river-'+status+r'-status-layer",\s*"#[0-9A-Fa-f]{6}"\);')
    repl='ensureRiverStatusLayer("fs-river-'+status+'-status","fs-river-'+status+'-status-layer","'+RIVER_BLUE+'");'
    m,n=re.subn(pat,repl,m,count=1)
    if n!=1:
        raise SystemExit('river status layer colour anchor missing: '+status)

# v0.8.27 core is cyan; make it the same clear FloodSafe blue requested for web + app.
m=m.replace('lineColor("#47d9ff")','lineColor("'+RIVER_BLUE+'")')
m=m.replace('lineColor("#58d9ef")','lineColor("'+RIVER_BLUE+'")')
m=m.replace('lineColor("#22e7ff")','lineColor("'+RIVER_BLUE+'")')

# Keep the camera tightly Nepal-focused. v0.8.24 already snaps an out-of-Nepal target back,
# and v0.8.27 already applies Nepal's bbox. This prevents zooming far enough out to leave Nepal.
m=m.replace('map.setMinZoomPreference(4.8);','map.setMinZoomPreference(5.35);',1)
m=m.replace('Math.max(4.8, Math.min(19.0, current + delta))','Math.max(5.35, Math.min(19.0, current + delta))',1)
if 'new LatLng(26.2, 80.0)' not in m or 'new LatLng(30.5, 88.35)' not in m:
    raise SystemExit('tight Nepal camera bbox missing after v0.8.27')
if 'cameraTargetInsideNepal' not in m:
    raise SystemExit('Nepal camera guard missing')

# -----------------------------------------------------------------------------
# MAP DISPLAY freshness != ALERT freshness.
# The previous native renderer put every reading outside its current window into fs-stale (grey),
# even when BIPAD/DHM still had a perfectly valid latest official water-level/status observation.
# For map display only, derive the colour from that latest observation. The original s.fresh flag
# stays unchanged and therefore cannot weaken risk, alert or notification safety.
# -----------------------------------------------------------------------------
station_geo_anchor='    private static String stationGeo(List<StationDot> list, String group) {'
if station_geo_anchor not in m:
    raise SystemExit('stationGeo anchor missing')

latest_stage=r'''    private static String latestMapStage(StationDot s) {
        if(s==null)return "stale";
        String declared=s.stage==null?"":s.stage.trim().toLowerCase(Locale.ROOT);
        if("danger".equals(declared)||"warning".equals(declared)||"alert".equals(declared)||"watch".equals(declared)||"normal".equals(declared))
            return "watch".equals(declared)?"alert":declared;
        String raw="";
        try{raw=getString(s.original.getClass(),s.original,"rawStatus","");}catch(Exception ignored){}
        raw=raw==null?"":raw.toUpperCase(Locale.ROOT);
        double level=s.level,warning=Double.NaN,danger=Double.NaN;
        try{warning=getDouble(s.original.getClass(),s.original,"warning");}catch(Exception ignored){}
        try{danger=getDouble(s.original.getClass(),s.original,"danger");}catch(Exception ignored){}
        if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED"))return "danger";
        if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE"))return "warning";
        if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning*.8)||raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW"))return "alert";
        if(Double.isFinite(level)||raw.contains("NORMAL")||raw.contains("BLUE")||raw.contains("BELOW WARNING"))return "normal";
        return "stale";
    }

'''
if 'private static String latestMapStage(StationDot s)' not in m:
    m=m.replace(station_geo_anchor,latest_stage+station_geo_anchor,1)

old_patterns=[
    r'String\s+g\s*=\s*s\.fresh\s*\?\s*normalizeStage\(s\.stage\)\s*:\s*"stale"\s*;',
    r'String\s+g=s\.fresh\?normalizeStage\(s\.stage\):"stale";'
]
changed=0
for pat in old_patterns:
    m,n=re.subn(pat,'String g=latestMapStage(s);',m,count=1)
    changed+=n
    if n: break
if changed!=1 and 'String g=latestMapStage(s);' not in m:
    raise SystemExit('strict-grey stationGeo classification anchor missing')

# If a later patch split stale/current classification into an equivalent conditional, fail loudly
# rather than silently shipping an all-grey station map again.
if 'private static String latestMapStage(StationDot s)' not in m or 'latestMapStage(s)' not in m:
    raise SystemExit('latest station display policy was not installed')

# -----------------------------------------------------------------------------
# Compact top-left live strip: distinguish latest observation from CURRENT observation.
# -----------------------------------------------------------------------------
us=a.find('    private void updateMapLiveOverlay(){')
ue=a.find('    private void refreshCompactRainCounts()',us)
if us<0 or ue<0:
    raise SystemExit('v0.8.27 compact overlay anchors missing')
overlay=r'''    private void updateMapLiveOverlay(){
        if(mapLiveText==null)return;
        int total=0,latest=0,current=0;
        synchronized(stations){
            total=stations.size();
            for(RiverStation s:stations){
                if(s==null)continue;
                if(s.at>0&&Double.isFinite(s.level))latest++;
                if(s.fresh)current++;
            }
        }
        String rain=(mapRainLatest>=0&&mapRainTotal>=0)?(mapRainLatest+" / "+mapRainTotal):"— / —";
        mapLiveText.setText("🌊 official "+total+" • latest "+latest+" • current "+current+"   🌧️ rain "+rain);
    }

'''
a=a[:us]+overlay+a[ue:]

# -----------------------------------------------------------------------------
# Rich in-map station detail. This is presentation only: never mutates s.stage/s.fresh.
# -----------------------------------------------------------------------------
ss=a.find('    private void showStation(RiverStation s){')
se=a.find('    private void refreshHuman()',ss)
if ss<0 or se<0:
    raise SystemExit('showStation anchors missing')
detail=r'''    private String mapDisplayStage(RiverStation s){
        if(s==null)return "unknown";
        String declared=s.stage==null?"":s.stage.trim().toLowerCase(Locale.ROOT);
        if("danger".equals(declared)||"warning".equals(declared)||"alert".equals(declared)||"normal".equals(declared))return declared;
        String raw=s.rawStatus==null?"":s.rawStatus.toUpperCase(Locale.ROOT);
        if((Double.isFinite(s.level)&&Double.isFinite(s.danger)&&s.danger>0&&s.level>=s.danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED"))return "danger";
        if((Double.isFinite(s.level)&&Double.isFinite(s.warning)&&s.warning>0&&s.level>=s.warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE"))return "warning";
        if((Double.isFinite(s.level)&&Double.isFinite(s.warning)&&s.warning>0&&s.level>=s.warning*.8)||raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW"))return "alert";
        if(Double.isFinite(s.level)||raw.contains("NORMAL")||raw.contains("BLUE")||raw.contains("BELOW WARNING"))return "normal";
        return "unknown";
    }

    private String mapReadingAge(long at){
        if(at<=0)return t("समय उपलब्ध छैन","time unavailable");
        long mins=Math.max(0L,(System.currentTimeMillis()-at)/60000L);
        if(mins<60)return mins+" min";
        long h=mins/60,m=mins%60;
        if(h<48)return h+"h "+m+"m";
        return (h/24)+"d "+(h%24)+"h";
    }

    private void showStation(RiverStation s){
        if(s==null)return;
        String displayStage=mapDisplayStage(s);
        StringBuilder b=new StringBuilder();
        if(s.district!=null&&!s.district.trim().isEmpty())b.append(t("जिल्ला: ","District: ")).append(s.district.trim()).append("\n");
        b.append(t("Reading: ","Reading: ")).append(s.fresh?t("CURRENT official","CURRENT official"):t("LATEST official • अहिले current होइन","LATEST official • NOT CURRENT"));
        b.append("\n").append(t("अवस्था: ","Stage: ")).append(stageDot(displayStage)).append(" ").append(stageName(displayStage));
        String raw=s.rawStatus==null?"":s.rawStatus.trim();
        if(!raw.isEmpty())b.append("\n").append(t("Official status: ","Official status: ")).append(raw);
        b.append("\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.3f m",s.level):"—");
        if(Double.isFinite(s.warning))b.append("\nWarning level: ").append(String.format(Locale.US,"%.3f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\nDanger level: ").append(String.format(Locale.US,"%.3f m",s.danger));
        if(s.at>0){
            b.append("\n").append(t("Official time: ","Official time: ")).append(Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime());
            b.append("\n").append(t("Reading age: ","Reading age: ")).append(mapReadingAge(s.at));
        }
        b.append("\n").append(t("स्रोत: BIPAD / DHM official","Source: BIPAD / DHM official"));
        if(!s.fresh)b.append("\n⚪ ").append(t("यो latest official record हो; live/current खतरा होइन।","This is the latest official record; it is not a live/current threat."));
        showMapDetail(s.name,b.toString());
    }

'''
a=a[:ss]+detail+a[se:]

# Version bump only; no alert/notification source file is read or written by this patch.
g=g.replace('versionCode 47','versionCode 48',1).replace("versionName '0.8.27'","versionName '0.8.28'",1)
if 'versionCode 48' not in g or "versionName '0.8.28'" not in g:
    raise SystemExit('v0.8.28 version bump failed')

# Hard map-only gates.
for marker in ['#168BFF','latestMapStage(s)','cameraTargetInsideNepal','new LatLng(26.2, 80.0)','new LatLng(30.5, 88.35)']:
    if marker not in m: raise SystemExit('v0.8.28 map marker missing: '+marker)
for marker in ['LATEST official • NOT CURRENT','mapDisplayStage(RiverStation s)','official "+total+" • latest "+latest+" • current "+current']:
    if marker not in a: raise SystemExit('v0.8.28 detail marker missing: '+marker)
# Explicitly retain the app-side 2 km + fresh safety gate. This patch never weakens it.
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:
    raise SystemExit('native 2 km + fresh emergency gate changed unexpectedly')

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.28 blue Nepal-only map + latest official station colours/detail PASS')
