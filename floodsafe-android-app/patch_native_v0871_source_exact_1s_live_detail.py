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

# v0.8.71 is deliberately narrow:
# - official source values are displayed exactly; no datum/elevation normalization
# - foreground river source recheck is requested every 1 second
# - open gauge detail refreshes in place whenever official source data changes
# - river-line tap delegates to the same matched official gauge detail
# - rainfall-only map dots, 2 km warning/danger radius, 2h weather/event behavior,
#   news, GPS, river geometry and the full official gauge inventory remain untouched


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

# 1) Source-exact values. Never transform the official water/threshold numbers.
sp=method_span(a,'parseStation')
if not sp:raise SystemExit('v0871 parseStation missing')
block=a[sp[0]:sp[1]]
block,n=re.subn(r'\n\s*boolean datum=.*?\n\s*if\(datum\)\{.*?\}\n',
                '\n        // V0871_SOURCE_VALUES_EXACT: keep official level/warning/danger exactly as supplied.\n',
                block,count=1,flags=re.S)
if n!=1:raise SystemExit('v0871 datum-normalization block missing')
a=a[:sp[0]]+block+a[sp[1]:]

# 2) Foreground source recheck cadence: one second. In-flight guard still prevents overlap.
if 'main.postDelayed(this,10_000L);' not in a:raise SystemExit('v0871 old 10s poll anchor missing')
a=a.replace('main.postDelayed(this,10_000L);','main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK',1)

# 3) Keep the merged official source row so the map detail can show the same metadata.
field_anchor='    private volatile boolean v862FinalRefreshInFlight=false; private volatile String v862FinalLastFingerprint=""; // V0862_FINAL_REFRESH_FIELDS'
fields=r'''    private final java.util.concurrent.ConcurrentHashMap<String,JSONObject> v871SourceRowsByName=new java.util.concurrent.ConcurrentHashMap<>();
    private AlertDialog v871GaugeDialog=null; private String v871OpenGaugeName=""; // V0871_LIVE_DETAIL_FIELDS
'''
if 'V0871_LIVE_DETAIL_FIELDS' not in a:
    if field_anchor not in a:raise SystemExit('v0871 field anchor missing')
    a=a.replace(field_anchor,field_anchor+'\n'+fields,1)

ret='        return out; // V0862_FINAL_TRUE_REALTIME_BIPAD_DHM'
if ret not in a:raise SystemExit('v0871 trusted-loader return anchor missing')
cache=r'''        java.util.concurrent.ConcurrentHashMap<String,JSONObject> nextSourceRows=new java.util.concurrent.ConcurrentHashMap<>();
        try{
            for(JSONObject row:current.values()){
                String nm=v846StationName(row);if(nm!=null&&!nm.trim().isEmpty())nextSourceRows.put(v846Key(nm),new JSONObject(row.toString()));
            }
            for(int i=0;i<catalog.length();i++){
                JSONObject row=catalog.optJSONObject(i);if(row==null)continue;String nm=v846StationName(row);
                if(nm!=null&&!nm.trim().isEmpty())nextSourceRows.putIfAbsent(v846Key(nm),new JSONObject(row.toString()));
            }
        }catch(Exception ignored){}
        v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextSourceRows); // V0871_SOURCE_ROW_CACHE
'''
a=a.replace(ret,cache+ret,1)

# Fingerprint every value that can change the visible source detail, not only level/time.
sp=method_span(a,'v862FinalFingerprint')
if not sp:raise SystemExit('v0871 fingerprint missing')
finger=r'''    private static String v862FinalFingerprint(List<RiverStation> rows){
        StringBuilder b=new StringBuilder();for(RiverStation s:rows){
            b.append(s.name).append('|').append(s.online).append('|').append(s.at).append('|').append(s.stage).append('|').append(s.raw).append('|');
            if(Double.isFinite(s.level))b.append(String.format(Locale.US,"%.6f",s.level));b.append('|');
            if(Double.isFinite(s.warning))b.append(String.format(Locale.US,"%.6f",s.warning));b.append('|');
            if(Double.isFinite(s.danger))b.append(String.format(Locale.US,"%.6f",s.danger));b.append(';');
        }return b.toString();
    } // V0871_FULL_DETAIL_FINGERPRINT
'''
a=a[:sp[0]]+finger+a[sp[1]:]

helpers=r'''    private String v871GaugeDetailText(RiverStation s){
        if(s==null)return "";JSONObject row=v871SourceRowsByName.get(v846Key(s.name));JSONObject f=row==null?null:row.optJSONObject("fields");
        String idx=strDeep(row,f,"stationIndex","station_index","stationSeriesId","station_series_id","stationId","station_id");
        String basin=strDeep(row,f,"basinName","basin_name","basin","riverBasin","river_basin");
        String trend=strDeep(row,f,"trend","waterLevelTrend","water_level_trend","levelTrend","level_trend");
        String desc=strDeep(row,f,"description","stationDescription","station_description");
        String source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source");
        double discharge=numDeep(row,f,"discharge","currentDischarge","current_discharge","flow","streamFlow","stream_flow");
        double elevation=numDeep(row,f,"elevation","stationElevation","station_elevation","altitude");
        boolean has=Double.isFinite(s.level)&&s.at>0L;
        StringBuilder b=new StringBuilder();
        b.append(v849AvailabilityDot(s)).append(" ").append(s.online?t("पछिल्लो आधिकारिक source मा उपलब्ध","Available in latest official source"):t("पछिल्लो आधिकारिक source मा उपलब्ध छैन","Not available in latest official source"));
        if(!idx.isEmpty())b.append("\n").append(t("Station no.: ","Station no.: ")).append(idx);
        if(!basin.isEmpty())b.append("\n").append(t("Basin: ","Basin: ")).append(basin);
        b.append("\n").append(t("जिल्ला: ","District: ")).append(s.district==null||s.district.isEmpty()?"—":s.district);
        b.append(String.format(Locale.US,"\n%s%.6f, %.6f",t("स्थान: ","Location: "),s.lat,s.lon));
        if(Double.isFinite(elevation))b.append(String.format(Locale.US,"\n%s%.2f m",t("Elevation: ","Elevation: "),elevation));
        if(!desc.isEmpty())b.append("\n").append(t("Description: ","Description: ")).append(desc);
        if(has){
            b.append(String.format(Locale.US,"\n\n%s%.2f m",t("पानीको सतह: ","Water level: "),s.level));
            if(Double.isFinite(discharge))b.append(String.format(Locale.US,"\n%s%.2f",t("Discharge: ","Discharge: "),discharge));
            if(Double.isFinite(s.warning))b.append(String.format(Locale.US,"\n%s%.2f m",t("चेतावनी तह: ","Warning level: "),s.warning));
            if(Double.isFinite(s.danger))b.append(String.format(Locale.US,"\n%s%.2f m",t("खतरा तह: ","Danger level: "),s.danger));
            if(!trend.isEmpty())b.append("\n").append(t("Trend: ","Trend: ")).append(trend);
            b.append("\n").append(t("अवस्था: ","Status: ")).append(s.raw==null||s.raw.trim().isEmpty()?stageName(s.stage):s.raw);
            b.append("\n").append(t("Official source time: ","Official source time: ")).append(v848Time(s.at));
        }else b.append("\n\n").append(t("हाल आधिकारिक source मा पानीको सतह/समय उपलब्ध छैन।","Water level/time is not currently available in the official source."));
        if(!source.isEmpty())b.append("\n").append(t("Data source: ","Data source: ")).append(source);
        v869AppendRain(b,s);
        b.append("\n\n").append(t("↻ यो detail १-१ सेकेन्डमा official source सँग recheck हुन्छ; source बदलिँदा यही popup update हुन्छ।","↻ This detail rechecks the official source every second and updates this popup when the source changes."));
        return b.toString();
    } // V0871_SOURCE_EXACT_DETAIL

    private void v871RefreshOpenGaugeDialog(List<RiverStation> rows){
        if(v871GaugeDialog==null||!v871GaugeDialog.isShowing()||v871OpenGaugeName==null||v871OpenGaugeName.isEmpty()||rows==null)return;
        for(RiverStation x:rows)if(x!=null&&v871OpenGaugeName.equalsIgnoreCase(x.name)){
            android.widget.TextView tv=v871GaugeDialog.findViewById(android.R.id.message);if(tv!=null)tv.setText(v871GaugeDetailText(x));return;
        }
    } // V0871_OPEN_POPUP_LIVE_UPDATE

'''
sp=method_span(a,'showStation')
if not sp:raise SystemExit('v0871 showStation anchor missing')
station=r'''    private void showStation(RiverStation s){
        if(s==null)return;
        if(v871GaugeDialog!=null&&v871GaugeDialog.isShowing())try{v871GaugeDialog.dismiss();}catch(Exception ignored){}
        v871OpenGaugeName=s.name==null?"":s.name;
        v871GaugeDialog=new AlertDialog.Builder(this).setTitle(s.name).setMessage(v871GaugeDetailText(s)).setPositiveButton(t("ठीक छ","OK"),null).create();
        v871GaugeDialog.setOnDismissListener(d->{v871GaugeDialog=null;v871OpenGaugeName="";});
        v871GaugeDialog.show();
    } // V0871_LIVE_SOURCE_DETAIL_DIALOG
'''
a=a[:sp[0]]+helpers+station+a[sp[1]:]

# Refresh the already-open popup whenever a fresh source fingerprint is painted.
marker='    } // V0869_ALL_GAUGES_NOT_ONLY_CURRENT'
if marker not in a:raise SystemExit('v0871 refreshRiverUi marker missing')
a=a.replace(marker,'        v871RefreshOpenGaugeDialog(gauges);\n'+marker,1)

# 4) A river-line tap with a same-river gauge opens the exact same full source detail.
sp=method_span(m,'showRiver')
if not sp:raise SystemExit('v0871 map showRiver missing')
show=r'''    private void showRiver(RiverWay r,double la,double lo) {
        StationDot gauge=v863SameRiverGauge(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");
        if(gauge!=null&&stationTapListener!=null){stationTapListener.onStationTap(gauge.original);return;} // V0871_RIVER_TAP_FULL_SOURCE_DETAIL
        StringBuilder msg=new StringBuilder();
        if(named)msg.append(englishUi?"No matching official source reading is currently available for this river.":"यस नदीसँग मिल्ने आधिकारिक source reading अहिले उपलब्ध छैन।");
        else msg.append(englishUi?"This map segment has no usable river name in the source data, so FloodSafe will not attach an unrelated gauge.":"यो नक्सा खण्डको source मा प्रयोग गर्न मिल्ने नदीको नाम छैन, त्यसैले असम्बन्धित gauge जोडिँदैन।");
        msg.append("\n\n").append(englishUi?"No old or different-river station is shown as current.":"पुरानो वा अर्को नदीको station लाई current भनेर देखाइँदैन।");
        msg.append("\n\n").append(englishUi?"River geometry: OpenStreetMap / FloodSafe Nepal network":"नदी नक्सा: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(msg.toString()).setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0871_RIVER_LINE_SOURCE_PARITY
'''
m=m[:sp[0]]+show+m[sp[1]:]

# Version.
if 'versionCode 90' in g:g=g.replace('versionCode 90','versionCode 91',1)
elif 'versionCode 91' not in g:raise SystemExit('v0871 versionCode anchor missing')
if "versionName '0.8.70'" in g:g=g.replace("versionName '0.8.70'","versionName '0.8.71'",1)
elif "versionName '0.8.71'" not in g:raise SystemExit('v0871 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
for x in ['V0871_SOURCE_VALUES_EXACT','V0871_ONE_SECOND_SOURCE_RECHECK','V0871_SOURCE_ROW_CACHE','V0871_SOURCE_EXACT_DETAIL','V0871_OPEN_POPUP_LIVE_UPDATE','V0871_LIVE_SOURCE_DETAIL_DIALOG','V0871_FULL_DETAIL_FINGERPRINT']:
    if x not in a:raise SystemExit('v0871 activity marker missing: '+x)
for x in ['V0871_RIVER_TAP_FULL_SOURCE_DETAIL','V0871_RIVER_LINE_SOURCE_PARITY']:
    if x not in m:raise SystemExit('v0871 map marker missing: '+x)
for old in ['main.postDelayed(this,10_000L);','Only a matching official reading from the last 20 minutes is shown here.','पछिल्लो २० मिनेटभित्रको आधिकारिक मापन मात्र']:
    if old in a+'\n'+m:raise SystemExit('v0871 stale timing text/code remains: '+old)
for x in ['V0869_NO_RAIN_ONLY_MAP_STATIONS','V0869_ALL_77_DISTRICTS','V0869_GAUGE_WATER_AND_RAIN_DETAIL','V0869_IMMEDIATE_ALERT_CHECKS','V0870_BIPAD_POINT_COORDS']:
    if x not in a:raise SystemExit('v0871 prior contract missing: '+x)
if 'RADIUS_KM = 2d' not in (src/'RiverAlertWorker.java').read_text(encoding='utf-8'):raise SystemExit('v0871 2km river alert radius changed')
if 'versionCode 91' not in g or "versionName '0.8.71'" not in g:raise SystemExit('v0871 version failed')
print('FloodSafe v0.8.71 PASS: exact official values + 1s recheck + live full source popup; prior map/rain/alert contracts preserved')