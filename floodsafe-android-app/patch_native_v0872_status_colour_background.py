from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
s_path=src/'FloodMonitorService.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
s=s_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.72 is intentionally narrow:
# - keep v0.8.71 exact BIPAD/DHM values + 1s foreground detail refresh
# - make WARNING/DANGER river geometry visibly follow the matched official gauge status
# - keep a user-enabled foreground service polling the same official river source every 1s
#   while the app is backgrounded, with immediate 2 km warning/danger checks
# - show source numeric precision and computed safety status in the gauge detail
# - do not touch rainfall-only marker policy, 2-hour rain/event digest, news, SATHI,
#   77-district inventory, GPS, source timestamps, or river geometry assets.

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

# 1) Start/stop the dedicated one-second official-source poller from the existing
# user-enabled foreground safety service. Existing location behavior is untouched.
field='    private boolean updatesStarted;'
if 'V0872_BACKGROUND_SOURCE_MONITOR_FIELD' not in s:
    if field not in s:raise SystemExit('v0872 service field anchor missing')
    s=s.replace(field,field+'\n    private FloodLiveGaugeMonitor v872LiveGaugeMonitor; // V0872_BACKGROUND_SOURCE_MONITOR_FIELD',1)

start='        startLocationUpdates();\n        return START_STICKY;'
if 'V0872_START_1S_BACKGROUND_SOURCE' not in s:
    if start not in s:raise SystemExit('v0872 service start anchor missing')
    s=s.replace(start,'        startLocationUpdates();\n        if(v872LiveGaugeMonitor==null)v872LiveGaugeMonitor=new FloodLiveGaugeMonitor(getApplicationContext());\n        v872LiveGaugeMonitor.start(); // V0872_START_1S_BACKGROUND_SOURCE\n        return START_STICKY;',1)

sp=method_span(s,'onDestroy')
if not sp:raise SystemExit('v0872 service destroy missing')
block=s[sp[0]:sp[1]]
if 'V0872_STOP_BACKGROUND_SOURCE' not in block:
    anchor='        updatesStarted = false;'
    if anchor not in block:raise SystemExit('v0872 destroy anchor missing')
    block=block.replace(anchor,'        if(v872LiveGaugeMonitor!=null){v872LiveGaugeMonitor.stop();v872LiveGaugeMonitor=null;} // V0872_STOP_BACKGROUND_SOURCE\n'+anchor,1)
    s=s[:sp[0]]+block+s[sp[1]:]

# 2) Gauge popup: exact source precision, and safety status derived from source
# thresholds/status. Raw status remains visible separately when supplied.
helper='''    private static String v872ExactNumber(double x){\n        if(!Double.isFinite(x))return "—";\n        return java.math.BigDecimal.valueOf(x).stripTrailingZeros().toPlainString();\n    } // V0872_SOURCE_NUMBER_PRECISION\n\n'''
if 'V0872_SOURCE_NUMBER_PRECISION' not in a:
    anchor='    private String v871GaugeDetailText(RiverStation s){'
    if anchor not in a:raise SystemExit('v0872 gauge detail anchor missing')
    a=a.replace(anchor,helper+anchor,1)

# Replace only the v0.8.71 detail formatting, not other screens.
a=a.replace('b.append(String.format(Locale.US,"\\n\\n%s%.2f m",t("पानीको सतह: ","Water level: "),s.level));',
            'b.append("\\n\\n").append(t("पानीको सतह: ","Water level: ")).append(v872ExactNumber(s.level)).append(" m"); // V0872_EXACT_LEVEL_DETAIL',1)
a=a.replace('if(Double.isFinite(discharge))b.append(String.format(Locale.US,"\\n%s%.2f",t("Discharge: ","Discharge: "),discharge));',
            'if(Double.isFinite(discharge))b.append("\\n").append(t("Discharge: ","Discharge: ")).append(v872ExactNumber(discharge)).append(" m³/s");',1)
a=a.replace('if(Double.isFinite(s.warning))b.append(String.format(Locale.US,"\\n%s%.2f m",t("चेतावनी तह: ","Warning level: "),s.warning));',
            'if(Double.isFinite(s.warning))b.append("\\n").append(t("चेतावनी तह: ","Warning level: ")).append(v872ExactNumber(s.warning)).append(" m");',1)
a=a.replace('if(Double.isFinite(s.danger))b.append(String.format(Locale.US,"\\n%s%.2f m",t("खतरा तह: ","Danger level: "),s.danger));',
            'if(Double.isFinite(s.danger))b.append("\\n").append(t("खतरा तह: ","Danger level: ")).append(v872ExactNumber(s.danger)).append(" m");',1)
old='b.append("\\n").append(t("अवस्था: ","Status: ")).append(rawStatus.isEmpty()?stageName(s.stage):rawStatus); // V0871_DISPLAY_RAW_SOURCE_STATUS'
new='b.append("\\n").append(t("अवस्था: ","Status: ")).append(stageName(s.stage)); if(!rawStatus.isEmpty())b.append(" • ").append(t("source: ","source: ")).append(rawStatus); // V0872_THRESHOLD_STATUS_VISIBLE'
if old in a:a=a.replace(old,new,1)
elif 'V0872_THRESHOLD_STATUS_VISIBLE' not in a:raise SystemExit('v0872 status detail anchor missing')

# 3) Add alert/warning/danger river overlays above the normal cyan river network.
layer_anchor='''                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(\n                        lineColor("#49dcff"), lineWidth(1.65f), lineOpacity(0.96f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));'''
layer_add='''\n                ensureRiskLineSource("fs-river-alert-risk","fs-river-alert-risk-layer","#ffc928",4.2f);\n                ensureRiskLineSource("fs-river-warning-risk","fs-river-warning-risk-layer","#ff8a1f",5.0f);\n                ensureRiskLineSource("fs-river-danger-risk","fs-river-danger-risk-layer","#f22f4b",5.8f); // V0872_RIVER_STATUS_COLOUR_LAYERS'''
if 'V0872_RIVER_STATUS_COLOUR_LAYERS' not in m:
    if layer_anchor not in m:raise SystemExit('v0872 river layer anchor missing')
    m=m.replace(layer_anchor,layer_anchor+layer_add,1)

risk_helpers=r'''    private void ensureRiskLineSource(String sourceId,String layerId,String color,float width){
        if(style.getSource(sourceId)==null)style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        if(style.getLayer(layerId)==null)style.addLayer(new LineLayer(layerId,sourceId).withProperties(
                lineColor(color),lineWidth(width),lineOpacity(0.96f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
    }

    private void refreshRiverRiskSources(){
        if(!styleReady||style==null)return;
        setGeo("fs-river-alert-risk",v872RiskRiverGeo("alert"));
        setGeo("fs-river-warning-risk",v872RiskRiverGeo("warning"));
        setGeo("fs-river-danger-risk",v872RiskRiverGeo("danger"));
    } // V0872_REFRESH_RIVER_STATUS_COLOURS

    private String v872RiskRiverGeo(String group){
        try{
            List<StationDot> ss;synchronized(stations){ss=new ArrayList<>(stations);}
            List<RiverWay> selected=new ArrayList<>();
            for(RiverWay r:rivers)if(v872RiskGaugeForRiver(r,ss,group)!=null)selected.add(r);
            return makeRiversGeoJson(selected);
        }catch(Exception e){return emptyFeatureCollection();}
    }

    private StationDot v872RiskGaugeForRiver(RiverWay r,List<StationDot> ss,String group){
        if(r==null||!v863UsefulRiverName(r.name))return null;String rk=v863RiverCore(r.name);if(rk.isEmpty())return null;
        StationDot best=null;double bestD=Double.POSITIVE_INFINITY;
        for(StationDot x:ss){
            if(x==null||!x.fresh||!group.equals(normalizeStage(x.stage))||x.name==null)continue;
            String sk=v863RiverCore(x.name);if(sk.isEmpty()||!v863RiverNamesMatch(rk,sk))continue;
            double d=v872GaugeToRiverKm(x,r);if(d<bestD){bestD=d;best=x;}
        }
        return bestD<=5.0?best:null; // tight geometry sanity gate: never colour an unrelated same-name river far away
    }

    private static double v872GaugeToRiverKm(StationDot s,RiverWay r){
        double best=Double.POSITIVE_INFINITY;int stride=Math.max(1,r.points.size()/220);
        for(int i=0;i<r.points.size();i+=stride){double[] p=r.points.get(i);best=Math.min(best,km(s.lat,s.lon,p[1],p[0]));}
        if(!r.points.isEmpty()){double[] p=r.points.get(r.points.size()-1);best=Math.min(best,km(s.lat,s.lon,p[1],p[0]));}
        return best;
    } // V0872_MATCHED_RIVER_GEOMETRY_ONLY

'''
if 'V0872_REFRESH_RIVER_STATUS_COLOURS' not in m:
    anchor='    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {'
    if anchor not in m:raise SystemExit('v0872 ensurePointSource anchor missing')
    m=m.replace(anchor,risk_helpers+anchor,1)

sp=method_span(m,'refreshStationSources')
if not sp:raise SystemExit('v0872 refreshStationSources missing')
block=m[sp[0]:sp[1]]
if 'refreshRiverRiskSources(); // V0872_STATION_UPDATE_REFRESHES_RIVER_COLOUR' not in block:
    pos=block.rfind('}')
    block=block[:pos]+'        refreshRiverRiskSources(); // V0872_STATION_UPDATE_REFRESHES_RIVER_COLOUR\n    '+block[pos:]
    m=m[:sp[0]]+block+m[sp[1]:]

# 4) Version only; all previous contracts must survive.
if 'versionCode 91' in g:g=g.replace('versionCode 91','versionCode 92',1)
elif 'versionCode 92' not in g:raise SystemExit('v0872 versionCode anchor missing')
if "versionName '0.8.71'" in g:g=g.replace("versionName '0.8.71'","versionName '0.8.72'",1)
elif "versionName '0.8.72'" not in g:raise SystemExit('v0872 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');s_path.write_text(s,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0872_SOURCE_NUMBER_PRECISION','V0872_EXACT_LEVEL_DETAIL','V0872_THRESHOLD_STATUS_VISIBLE','V0871_SOURCE_EXACT_DETAIL','V0871_OPEN_POPUP_LIVE_UPDATE','main.postDelayed(this,1_000L);']:
    if x not in a:raise SystemExit('v0872 activity contract missing: '+x)
for x in ['V0872_RIVER_STATUS_COLOUR_LAYERS','V0872_REFRESH_RIVER_STATUS_COLOURS','V0872_MATCHED_RIVER_GEOMETRY_ONLY','V0872_STATION_UPDATE_REFRESHES_RIVER_COLOUR','V0871_RIVER_TAP_FULL_SOURCE_DETAIL']:
    if x not in m:raise SystemExit('v0872 map contract missing: '+x)
for x in ['V0872_BACKGROUND_SOURCE_MONITOR_FIELD','V0872_START_1S_BACKGROUND_SOURCE','V0872_STOP_BACKGROUND_SOURCE']:
    if x not in s:raise SystemExit('v0872 service contract missing: '+x)
for x in ['V0869_NO_RAIN_ONLY_MAP_STATIONS','V0869_ALL_77_DISTRICTS','V0869_IMMEDIATE_ALERT_CHECKS']:
    if x not in a:raise SystemExit('v0872 previous behavior missing: '+x)
if 'RIVER_FRESH_MS=Long.MAX_VALUE' not in a:raise SystemExit('v0872 source no-age-gate changed')
if 'versionCode 92' not in g or "versionName '0.8.72'" not in g:raise SystemExit('v0872 version failed')
print('FloodSafe v0.8.72 PASS: exact source detail + matched river risk colours + one-second background source monitor; prior rain/news/77-district behavior untouched')
