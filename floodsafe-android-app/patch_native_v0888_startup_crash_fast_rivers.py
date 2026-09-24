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

# v0.8.88 real-device startup repair:
# 1) never do bootstrap parsing / map refresh inline in Activity.onCreate before first frame;
# 2) remove the O(rivers * stations * geometry) monitored-river filter from the UI thread;
# 3) every rendered monitored river name can still open a same-river official gauge detail,
#    but no unrelated nearest-station fallback is introduced.


def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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


def replace_method(text,name,new_block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('v0888 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# Defer bootstrap until Android has a chance to draw the first frame. The method already
# catches its own parsing/source errors, so this also prevents a cold-start black window/ANR.
old='v887LoadBootstrapOfficialStations(); // V0887_BOOTSTRAP_CALL'
new='main.postDelayed(() -> v887LoadBootstrapOfficialStations(), 180L); // V0887_BOOTSTRAP_CALL V0888_FIRST_FRAME_BEFORE_BOOTSTRAP'
if old not in a:
    if 'V0888_FIRST_FRAME_BEFORE_BOOTSTRAP' not in a: raise SystemExit('v0888 bootstrap call anchor missing')
else:
    a=a.replace(old,new,1)

# Fast monitored-river filter: build a tiny set of official river keys once per refresh,
# then filter geometry with O(rivers + stations) string lookups instead of thousands/millions
# of expensive point-to-polyline distance calculations on the main thread.
fast=r'''    private List<RiverWay> v887MonitoredRivers(List<RiverWay> input){
        List<RiverWay> out=new ArrayList<>();if(input==null||input.isEmpty())return out;
        java.util.HashSet<String> officialKeys=new java.util.HashSet<>();
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)continue;
            String k=v886RiverKey(s.riverName);if(!k.isEmpty())officialKeys.add(k);
            String tk=v886RiverKey(v886StationRiverFromTitle(s.name));if(!tk.isEmpty())officialKeys.add(tk);
        }}
        if(officialKeys.isEmpty())return out;
        for(RiverWay r:input){
            if(r==null||!v863UsefulRiverName(r.name))continue;
            String rk=v886RiverKey(r.name);
            if(!rk.isEmpty()&&officialKeys.contains(rk))out.add(r);
        }
        return out;
    } // V0888_FAST_MONITORED_RIVER_FILTER V0888_NO_MAINTHREAD_GEOMETRY_JOIN
'''
m=replace_method(m,'v887MonitoredRivers',fast)

# Detail matching remains strict on river identity, but a tap may use the nearest official
# station on that SAME named river even when the clicked segment is farther than the old 7.5 km
# geometry gate. This guarantees visible monitored river lines have useful official detail.
detail=r'''    private StationDot v884SameRiverGaugeForDetail(RiverWay r,double la,double lo){
        if(r==null||!v863UsefulRiverName(r.name))return null;
        StationDot bestObserved=null,bestAny=null;double obsScore=Double.POSITIVE_INFINITY,anyScore=Double.POSITIVE_INFINITY;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!v886SameOfficialRiver(r,s))continue; // same-river identity is mandatory
            double routeD=v872GaugeToRiverKm(s,r);if(!Double.isFinite(routeD))routeD=9999.0;
            double tapD=km(la,lo,s.lat,s.lon);if(!Double.isFinite(tapD))tapD=9999.0;
            double score=routeD*4.0+tapD;
            if(score<anyScore){anyScore=score;bestAny=s;}
            if((Double.isFinite(s.level)||s.v881At>0L)&&score<obsScore){obsScore=score;bestObserved=s;}
        }}
        return bestObserved!=null?bestObserved:bestAny;
    } // V0888_VISIBLE_MONITORED_RIVER_HAS_SAME_RIVER_DETAIL V0888_NO_UNRELATED_STATION_FALLBACK
'''
m=replace_method(m,'v884SameRiverGaugeForDetail',detail)

# Protect cold-start style paint from any unexpected runtime exception in the monitored-river
# refresh path. OutOfMemoryError is intentionally not swallowed.
sp=method_span(m,'v887ApplyMonitoredRiverGeometry')
if not sp:raise SystemExit('v0888 monitored apply missing')
block=m[sp[0]:sp[1]]
if 'V0888_STARTUP_MAP_GUARD' not in block:
    p=block.find('{')+1
    body=block[p:-1]
    block=block[:p]+'\n        try{ // V0888_STARTUP_MAP_GUARD\n'+body+'\n        }catch(Exception ignored){}\n    '
    m=m[:sp[0]]+block+m[sp[1]:]

g=re.sub(r'versionCode\s+107\b','versionCode 108',g,count=1)
g=g.replace("versionName '0.8.87'","versionName '0.8.88'",1)

for x in ['V0888_FIRST_FRAME_BEFORE_BOOTSTRAP']:
    if x not in a:raise SystemExit('v0888 activity contract missing: '+x)
for x in ['V0888_FAST_MONITORED_RIVER_FILTER','V0888_NO_MAINTHREAD_GEOMETRY_JOIN','V0888_VISIBLE_MONITORED_RIVER_HAS_SAME_RIVER_DETAIL','V0888_NO_UNRELATED_STATION_FALLBACK','V0888_STARTUP_MAP_GUARD','V0887_BLUE_RIVER_ALWAYS_HAS_DETAIL']:
    if x not in m:raise SystemExit('v0888 map contract missing: '+x)
if 'versionCode 108' not in g or "versionName '0.8.88'" not in g:raise SystemExit('v0888 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.88 PASS: cold-start first frame protected + fast monitored river filter + same-river detail')
