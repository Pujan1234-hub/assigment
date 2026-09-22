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

# v0.8.76 separates two facts that must never be conflated:
# 1) the newest row the official source currently exposes for a gauge, and
# 2) whether that row is fresh enough to be treated as LIVE/current safety data.
# Old official readings remain inspectable with their exact source time/value, but they
# are grey/stale and never drive live colours, Warning/Danger risk or notifications.
# Official source recheck cadence remains one second; no values/timestamps are invented.

FRESH_EXPR='online&&hasObservation&&now-at<=RIVER_FRESH_MS&&at-now<=5L*60L*1000L'

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
            if ch in ('"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

# 1) LIVE/current means <=20 minutes old (with only a 5-minute future-clock tolerance).
# The row itself is NOT discarded when older: it remains the last official reading.
a,n=re.subn(r'RIVER_FRESH_MS\s*=\s*Long\.MAX_VALUE',
            'RIVER_FRESH_MS=20L*60L*1000L /* V0876_SOURCE_FRESHNESS_20M */',a,count=1)
if n!=1 and 'V0876_SOURCE_FRESHNESS_20M' not in a:
    raise SystemExit('v0876 unlimited river freshness anchor missing')

sp=method_span(a,'parseStation')
if not sp:raise SystemExit('v0876 parseStation missing')
block=a[sp[0]:sp[1]]
block,n=re.subn(r'boolean\s+fresh\s*=\s*online\s*&&\s*hasObservation\s*;[^\n]*',
                'boolean fresh='+FRESH_EXPR+'; // V0876_LATEST_ROW_RETAINED V0876_FRESH_TIMESTAMP_GATE',
                block,count=1)
if n!=1:
    # tolerate a historical 20m expression while still making this patch idempotent
    block,n2=re.subn(r'boolean\s+fresh\s*=\s*online\s*&&\s*hasObservation\s*&&[^;]+;[^\n]*',
                     'boolean fresh='+FRESH_EXPR+'; // V0876_LATEST_ROW_RETAINED V0876_FRESH_TIMESTAMP_GATE',
                     block,count=1)
    if n2!=1 and 'V0876_FRESH_TIMESTAMP_GATE' not in block:
        raise SystemExit('v0876 parseStation freshness anchor missing')
a=a[:sp[0]]+block+a[sp[1]:]

# 2) Availability/status dot: old source rows are explicitly grey, never green/current.
sp=method_span(a,'v849AvailabilityDot')
if not sp:raise SystemExit('v0876 availability dot missing')
dot=r'''    private static String v849AvailabilityDot(RiverStation s){
        if(s==null||!s.fresh)return "⚪"; // V0876_STALE_OFFICIAL_GREY
        if("danger".equals(s.stage))return "🔴";
        if("warning".equals(s.stage))return "🟠";
        if("alert".equals(s.stage))return "🟡";
        return "🔵";
    }
'''
a=a[:sp[0]]+dot+a[sp[1]:]

# 3) Fingerprint includes the freshness transition. This makes a reading turn stale on
# screen as soon as its 20-minute LIVE window expires, even when the source row is unchanged.
sp=method_span(a,'v862FinalFingerprint')
if not sp:raise SystemExit('v0876 fingerprint missing')
finger=r'''    private static String v862FinalFingerprint(List<RiverStation> rows){
        StringBuilder b=new StringBuilder();for(RiverStation s:rows){
            b.append(s.name).append('|').append(s.online).append('|').append(s.fresh).append('|').append(s.at).append('|').append(s.stage).append('|').append(s.raw).append('|');
            if(Double.isFinite(s.level))b.append(String.format(Locale.US,"%.6f",s.level));b.append('|');
            if(Double.isFinite(s.warning))b.append(String.format(Locale.US,"%.6f",s.warning));b.append('|');
            if(Double.isFinite(s.danger))b.append(String.format(Locale.US,"%.6f",s.danger));b.append(';');
        }return b.toString();
    } // V0876_FRESHNESS_IN_FINGERPRINT
'''
a=a[:sp[0]]+finger+a[sp[1]:]

# 4) Lists/counts call a reading current only when it is actually fresh. Keep stale rows
# in the inventory so exact last official value/time is still inspectable.
sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0876 refreshRiverUi missing')
ui=a[sp[0]:sp[1]]
ui=ui.replace('s.online&&Double.isFinite(s.level)&&s.at>0L','s.fresh&&Double.isFinite(s.level)&&s.at>0L')
ui=ui.replace('s.online && Double.isFinite(s.level) && s.at>0L','s.fresh && Double.isFinite(s.level) && s.at>0L')
if 'V0876_CURRENT_COUNT_FRESH_ONLY' not in ui:
    # marker in a harmless comment near the first counter declaration
    ui=ui.replace('int current=0', 'int current=0 /* V0876_CURRENT_COUNT_FRESH_ONLY */',1)
a=a[:sp[0]]+ui+a[sp[1]:]

# Compact station rows also distinguish LIVE from the last official stale reading.
sp=method_span(a,'stationLine')
if sp:
    line=r'''    private String stationLine(RiverStation s){
        if(s==null)return "";
        boolean has=Double.isFinite(s.level)&&s.at>0L;
        if(!has)return t("आधिकारिक मापन उपलब्ध छैन","Official measurement unavailable");
        String lev=String.format(Locale.US,"%.2f m",s.level);
        String age=v850Age(s.at);
        double km=distanceKm(s.lat,s.lon);String dist=Double.isFinite(km)?String.format(Locale.US," • %.1f km",km):"";
        if(!s.fresh)return t("अन्तिम आधिकारिक मापन: ","Last official reading: ")+lev+" • "+age+dist+" • "+t("LIVE होइन","NOT LIVE");
        return stageName(s.stage)+" • "+lev+" • "+age+dist;
    } // V0876_STALE_ROW_LABEL
'''
    a=a[:sp[0]]+line+a[sp[1]:]

# 5) Full popup: exact source values/time stay visible. Freshness is an app safety label,
# never a fabricated replacement timestamp. Rainfall is a separate official station/feed,
# so its timestamp is intentionally shown independently from the river gauge timestamp.
sp=method_span(a,'v871GaugeDetailText')
if not sp:raise SystemExit('v0876 exact gauge detail missing')
detail=r'''    private String v871GaugeDetailText(RiverStation s){
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
        if(s.fresh)b.append(v849AvailabilityDot(s)).append(" ").append(t("ताजा आधिकारिक मापन • LIVE/current","Fresh official measurement • LIVE/current"));
        else if(has)b.append("⚪ ").append(t("अन्तिम आधिकारिक मापन • पुरानो / LIVE होइन","Last official measurement • STALE / NOT LIVE"));
        else b.append("⚪ ").append(t("हाल मापन उपलब्ध छैन","No measurement currently available"));
        b.append("\n").append(t("Source inventory: ","Source inventory: ")).append(s.online?t("latest official source मा station उपलब्ध","station is present in latest official source"):t("latest official source मा station उपलब्ध छैन","station is not present in latest official source"));
        if(!idx.isEmpty())b.append("\n").append(t("Station no.: ","Station no.: ")).append(idx);
        if(!basin.isEmpty())b.append("\n").append(t("Basin: ","Basin: ")).append(basin);
        b.append("\n").append(t("जिल्ला: ","District: ")).append(s.district==null||s.district.isEmpty()?"—":s.district);
        b.append(String.format(Locale.US,"\n%s%.6f, %.6f",t("स्थान: ","Location: "),s.lat,s.lon));
        if(Double.isFinite(elevation))b.append(String.format(Locale.US,"\n%s%.2f m",t("Elevation: ","Elevation: "),elevation));
        if(!desc.isEmpty())b.append("\n").append(t("Description: ","Description: ")).append(desc);
        if(has){
            b.append(String.format(Locale.US,"\n\n%s%.6f m",t("पानीको सतह: ","Water level: "),s.level));
            if(Double.isFinite(discharge))b.append(String.format(Locale.US,"\n%s%.6f",t("Discharge / streamflow: ","Discharge / streamflow: "),discharge));
            if(Double.isFinite(s.warning))b.append(String.format(Locale.US,"\n%s%.6f m",t("चेतावनी तह: ","Warning level: "),s.warning));
            if(Double.isFinite(s.danger))b.append(String.format(Locale.US,"\n%s%.6f m",t("खतरा तह: ","Danger level: "),s.danger));
            if(!trend.isEmpty())b.append("\n").append(t("Trend: ","Trend: ")).append(trend);
            b.append("\n").append(t(s.fresh?"LIVE अवस्था: ":"अन्तिम source अवस्था: ",s.fresh?"LIVE status: ":"Last source status: ")).append(s.raw==null||s.raw.trim().isEmpty()?stageName(s.stage):s.raw);
            b.append("\n").append(t("Official river source time: ","Official river source time: ")).append(v848Time(s.at));
            b.append("\n").append(t("River reading age: ","River reading age: ")).append(v850Age(s.at));
            if(!s.fresh)b.append("\n\n").append(t("⚪ यो source ले दिएको अन्तिम आधिकारिक reading हो, तर २० मिनेटभन्दा पुरानो भएकाले LIVE risk/alert मा प्रयोग हुँदैन। नयाँ official measurement आएपछि १-सेकेन्ड recheck ले यही detail बदल्छ।","⚪ This is the last official reading exposed by the source, but it is older than 20 minutes, so it is not used for LIVE risk/alerts. A new official measurement will replace it on the one-second recheck."));
        }else b.append("\n\n").append(t("Official source मा water-level/time measurement उपलब्ध छैन। FloodSafe ले value वा time बनाउँदैन।","The official source does not provide a water-level/time measurement here. FloodSafe does not invent a value or timestamp."));
        if(!source.isEmpty())b.append("\n").append(t("Data source: ","Data source: ")).append(source);
        v869AppendRain(b,s);
        b.append("\n\n").append(t("↻ River, rain र अन्य official hydrology feeds १-१ सेकेन्डमा recheck हुन्छन्। प्रत्येक station/feed को official timestamp आफ्नै हुन्छ; source मा नयाँ data आएपछि app update हुन्छ।","↻ River, rain and other official hydrology feeds are rechecked every second. Each station/feed keeps its own official timestamp; the app updates when the source publishes new data."));
        return b.toString();
    } // V0876_STALE_OFFICIAL_DETAIL V0876_READING_AGE V0876_INDEPENDENT_SOURCE_TIMES
'''
a=a[:sp[0]]+detail+a[sp[1]:]

# 6) Risk geometry must stay fresh-only. The existing v0.8.72 matcher already enforces
# !x.fresh -> skip; assert it instead of changing trusted geometry logic.
if '!x.fresh' not in m or 'v872RiskGaugeForRiver' not in m:
    raise SystemExit('v0876 fresh-only river risk geometry guard missing')
# Marker used by CI to make this safety promise explicit without changing the matcher.
m=m.replace('private StationDot v872RiskGaugeForRiver', '/* V0876_STALE_NEVER_DRIVES_RISK */\n    private StationDot v872RiskGaugeForRiver',1)

# Release identity.
if 'versionCode 95' in g:g=g.replace('versionCode 95','versionCode 96',1)
elif 'versionCode 96' not in g:raise SystemExit('v0876 versionCode anchor missing')
if "versionName '0.8.75'" in g:g=g.replace("versionName '0.8.75'","versionName '0.8.76'",1)
elif "versionName '0.8.76'" not in g:raise SystemExit('v0876 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0876_SOURCE_FRESHNESS_20M','V0876_FRESH_TIMESTAMP_GATE','V0876_LATEST_ROW_RETAINED','V0876_STALE_OFFICIAL_GREY','V0876_FRESHNESS_IN_FINGERPRINT','V0876_CURRENT_COUNT_FRESH_ONLY','V0876_STALE_OFFICIAL_DETAIL','V0876_READING_AGE','V0876_INDEPENDENT_SOURCE_TIMES','V0871_ONE_SECOND_SOURCE_RECHECK']:
    if x not in a:raise SystemExit('v0876 activity contract missing: '+x)
for x in ['V0876_STALE_NEVER_DRIVES_RISK','V0875_TOUCH_PRIORITY','V0875_ASYNC_RISK_REBUILD']:
    if x not in m:raise SystemExit('v0876 map contract missing: '+x)
if 'RIVER_FRESH_MS=Long.MAX_VALUE' in a:raise SystemExit('v0876 unlimited freshness regression remains')
if 'RIVER_FRESH_MS=20L*60L*1000L' not in a:raise SystemExit('v0876 20m freshness constant missing')
if 'versionCode 96' not in g or "versionName '0.8.76'" not in g:raise SystemExit('v0876 version verification failed')
print('FloodSafe v0.8.76 PASS: exact latest official rows retained; only <=20m readings are LIVE; stale data grey/detail-only; 1s source recheck preserved')
