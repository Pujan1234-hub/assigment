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

def method_span(text,name):
    # Patch-chain output has changed modifiers/spacing many times; locate by method name
    # and balance braces instead of depending on a fragile Java declaration regex.
    mm=re.search(r'\b'+re.escape(name)+r'\s*\(',text)
    if not mm:return None
    start=text.rfind('\n',0,mm.start())+1
    op=text.find('{',mm.end())
    if op<0:return None
    depth=0;quote=None;esc=False;i=op
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
                if depth==0:return start,i+1
        i+=1
    return None

def replace_method(text,name,new_block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('v0882 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# v0.8.82 fixes the v0.8.81 semantic bug: station presence is NOT the same thing as
# a <=20 minute reading. BIPAD River Watch membership controls which stations/rivers
# are displayed; freshness remains only reading/safety metadata.
sp=method_span(a,'loadTrustedRiverStationsV862')
if not sp:raise SystemExit('v0882 station loader missing')
loader=a[sp[0]:sp[1]]

anchor='        java.util.LinkedHashMap<String,JSONObject> newest=new java.util.LinkedHashMap<>();\n        java.util.LinkedHashMap<String,JSONObject> metadataMatch=new java.util.LinkedHashMap<>();\n'
if anchor not in loader:raise SystemExit('v0882 active-set anchor missing')
loader=loader.replace(anchor,anchor+'        java.util.LinkedHashSet<String> v882RiverWatchKeys=new java.util.LinkedHashSet<>();\n        java.util.LinkedHashSet<String> v882TrimedKeys=new java.util.LinkedHashSet<>(); // V0882_BIPAD_ACTIVE_SETS\n',1)

key_anchor='                    String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;\n'
if key_anchor not in loader:raise SystemExit('v0882 key anchor missing')
key_insert=key_anchor+'                    if(path.startsWith("river/?"))v882RiverWatchKeys.add(key);else if(path.startsWith("river-trimed/?"))v882TrimedKeys.add(key); // V0882_ACTIVE_BIPAD_MEMBERSHIP\n'
loader=loader.replace(key_anchor,key_insert,1)

union_end='        }\n\n        String[] dhmUrls='
if union_end not in loader:raise SystemExit('v0882 union end anchor missing')
loader=loader.replace(union_end,'        }\n\n        final java.util.LinkedHashSet<String> v882ActiveKeys=!v882RiverWatchKeys.isEmpty()?v882RiverWatchKeys:v882TrimedKeys;\n        if(v882ActiveKeys.isEmpty())throw new IllegalStateException("BIPAD River Watch returned no active station rows"); // V0882_NO_ZERO_WIPE\n\n        String[] dhmUrls=',1)

loop_anchor='            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));JSONObject row=newest.get(key);\n'
if loop_anchor not in loader:raise SystemExit('v0882 final-loop anchor missing')
loader=loader.replace(loop_anchor,'            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));\n            if(!v882ActiveKeys.contains(key))continue; // V0882_ONLY_BIPAD_RIVER_WATCH_ROWS\n            JSONObject row=newest.get(key);\n',1)

count_old='        v877FreshObservationCount=freshCount;v877LatestObservationCount=latestCount;v877NoObservationCount=Math.max(0,catalog.length()-latestCount);\n        v849LatestCount=latestCount;v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);\n'
if count_old not in loader:raise SystemExit('v0882 count anchor missing')
loader=loader.replace(count_old,'        v849CatalogCount=v882ActiveKeys.size(); // V0882_RIVER_WATCH_COUNT_IS_TRUTH\n        v877FreshObservationCount=freshCount;v877LatestObservationCount=latestCount;v877NoObservationCount=Math.max(0,v849CatalogCount-latestCount);\n        v849LatestCount=latestCount;v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);\n',1)
loader=loader.replace('} // V0878_RESILIENT_STATION_REFRESH','} // V0882_BIPAD_RIVER_WATCH_DISPLAY_TRUTH',1)
a=a[:sp[0]]+loader+a[sp[1]:]

hint=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 BIPAD River Watch "+v849CatalogCount+" • map मा "+mapRiverTotal+" • recent reading "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount,
                          "🌊 BIPAD River Watch "+v849CatalogCount+" • mapped "+mapRiverTotal+" • recent reading "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount));
    } // V0882_RIVER_WATCH_HEADER
'''
a=replace_method(a,'updateMapHintCounts',hint)

spm=method_span(m,'v881RiverHasLiveStation')
if not spm:raise SystemExit('v0882 river matcher missing')
matcher=m[spm[0]:spm[1]]
if 's==null||!s.fresh||!Double.isFinite(s.lat)||!Double.isFinite(s.lon)' not in matcher:
    raise SystemExit('v0882 expected v0.8.81 fresh gate missing')
matcher=matcher.replace('s==null||!s.fresh||!Double.isFinite(s.lat)||!Double.isFinite(s.lon)','s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon)',1)
matcher=matcher.replace('} // V0881_LIVE_STATION_MATCH','} // V0882_ACTIVE_STATION_RIVER_MATCH',1)
m=m[:spm[0]]+matcher+m[spm[1]:]

check=method_span(m,'v881RiverHasLiveStation')
if not check or '!s.fresh' in m[check[0]:check[1]]:raise SystemExit('v0882 river visibility still depends on freshness')

g=re.sub(r'versionCode\s+101\b','versionCode 102',g,count=1)
g=g.replace("versionName '0.8.81'","versionName '0.8.82'",1)
if 'versionCode 102' not in g or "versionName '0.8.82'" not in g:raise SystemExit('v0882 version bump failed')

for x in ['V0882_BIPAD_ACTIVE_SETS','V0882_ACTIVE_BIPAD_MEMBERSHIP','V0882_NO_ZERO_WIPE','V0882_ONLY_BIPAD_RIVER_WATCH_ROWS','V0882_RIVER_WATCH_COUNT_IS_TRUTH','V0882_BIPAD_RIVER_WATCH_DISPLAY_TRUTH','V0882_RIVER_WATCH_HEADER']:
    if x not in a:raise SystemExit('missing '+x)
if 'V0882_ACTIVE_STATION_RIVER_MATCH' not in m:raise SystemExit('missing river matcher contract')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.82 BIPAD River Watch station-presence truth + station-river visibility fix applied')
