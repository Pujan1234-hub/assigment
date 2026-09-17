from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path=src/'NativeFullActivity.java'
gradle_path=root/'app/build.gradle'
activity=activity_path.read_text(encoding='utf-8')
gradle=gradle_path.read_text(encoding='utf-8')

# v0.8.15: one official-source truth across map/cards/lists/risk/SATHI.
# Visual colour still maps the source status to the locked palette, but user-visible
# status text is the exact source status. Do not invent a stage when the source did
# not publish one.

# Remove threshold-derived fallback stage from v0.8.14 when official raw status is absent.
old='''            else if(Double.isFinite(danger)&&danger>0&&level>=danger){stage="danger";rank=0;}\n            else if(Double.isFinite(warning)&&warning>0&&level>=warning){stage="warning";rank=1;}\n            else{stage="normal";rank=3;}'''
new='''            else if(raw==null||raw.trim().isEmpty()){stage="unknown";rank=4;}\n            else{stage="unknown";rank=4;}'''
if old in activity:
    activity=activity.replace(old,new,1)
elif 'raw==null||raw.trim().isEmpty()' not in activity:
    raise SystemExit('v0.8.14 stage fallback anchor missing')

# Source-exact label helper used everywhere the app exposes a river status.
anchor='    private String stationLine(RiverStation s){'
helper=r'''    private String sourceStatusLabel(RiverStation s){
        if(s==null)return "UNKNOWN";
        String raw=s.rawStatus==null?"":s.rawStatus.trim();
        if(!s.fresh)return raw.isEmpty()||"NO_CURRENT_OFFICIAL_READING".equals(raw)?"STALE / UNKNOWN":raw;
        if(!raw.isEmpty()&&!"NO_CURRENT_OFFICIAL_READING".equals(raw))return raw;
        return "UNKNOWN";
    }

'''
if 'private String sourceStatusLabel(RiverStation s)' not in activity:
    if anchor not in activity: raise SystemExit('stationLine anchor missing')
    activity=activity.replace(anchor,helper+anchor,1)

# Near/national rows + risk text use exact source status and same official value/time.
station_pat=r'''    private String stationLine\(RiverStation s\)\{.*?\}\n'''
station_new=r'''    private String stationLine(RiverStation s){
        String age=s.at>0?Math.max(0,(System.currentTimeMillis()-s.at)/60000)+" min ago":"time unknown";
        String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"level —";
        double d=distanceKm(s.lat,s.lon);
        return sourceStatusLabel(s)+" • "+lev+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • %.1f km",d):"");
    }
'''
activity,n=re.subn(station_pat,station_new,activity,count=1,flags=re.S)
if n!=1: raise SystemExit('stationLine replacement failed')

activity=activity.replace('riskValue.setText(stageName(best.stage));riskBadge.setText(stageName(best.stage));',
                          'riskValue.setText(sourceStatusLabel(best));riskBadge.setText(sourceStatusLabel(best));',1)

# Station detail: first line and explicit Source status use source wording, not app wording.
activity=activity.replace('b.append(stageDot(s.stage)).append(" ").append(stageName(s.stage)).append("\\n\\n")',
                          'b.append(stageDot(s.stage)).append(" ").append(sourceStatusLabel(s)).append("\\n\\n")',1)
obs_anchor='b.append("\\n").append(t("Official observation: ","Official observation: ")).append(s.at>0?Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime():"—")'
if obs_anchor in activity:
    activity=activity.replace(obs_anchor,
        'b.append("\\n").append(t("Source status: ","Source status: ")).append(sourceStatusLabel(s)).append("\\n").append(t("Official observation: ","Official observation: ")).append(s.at>0?Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime():"—")',1)

# SATHI answers from the same RiverStation truth object and source status string.
activity=activity.replace('.append(stageName(s.stage));if(Double.isFinite(s.level))',
                          '.append(sourceStatusLabel(s));if(Double.isFinite(s.level))',1)
activity=activity.replace('.append(stageName(s.stage));if(shown>=3)break;',
                          '.append(sourceStatusLabel(s));if(shown>=3)break;',1)

# Make summary wording explicit that the colours are a visualization of the source status.
activity=activity.replace(
    'mapSub.setText(t("Grey=geometry • 🔵 Normal • 🟡 Alert • 🟠 Warning • 🔴 Danger — official source अनुसार","Grey=geometry • 🔵 Normal • 🟡 Alert • 🟠 Warning • 🔴 Danger — official source status"));',
    'mapSub.setText(t("Source status जस्तै: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER • Grey=stale/geometry","Source-exact status: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER • Grey=stale/geometry"));',1)

# Version bump.
if "versionName '0.8.15'" not in gradle:
    gradle=gradle.replace('versionCode 34','versionCode 35',1)
    gradle=gradle.replace("versionName '0.8.14'","versionName '0.8.15'",1)
if 'versionCode 35' not in gradle or "versionName '0.8.15'" not in gradle:
    raise SystemExit('v0.8.15 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

# Hard truth assertions.
a=activity_path.read_text(encoding='utf-8')
for marker in ['sourceStatusLabel(RiverStation s)','Source status: ','sourceStatusLabel(best)','Source-exact status','raw==null||raw.trim().isEmpty()']:
    if marker not in a: raise SystemExit('v0.8.15 truth marker missing: '+marker)
if 'riskValue.setText(stageName(best.stage))' in a: raise SystemExit('derived risk label remained')
print('FloodSafe v0.8.15 single official source truth across app PASS')
