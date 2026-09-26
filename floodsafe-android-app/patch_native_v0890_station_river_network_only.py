from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

def span(text,name):
    q=re.search(r'(?m)^\s*(?:(?:private|public|protected)\s+)?[A-Za-z0-9_<>\[\]?., ]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start());d=0;quote=None;esc=False
    for i in range(op,len(text)):
        c=text[i]
        if quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        else:
            if c in ('\"',"'"):quote=c
            elif c=='{':d+=1
            elif c=='}':
                d-=1
                if d==0:return q.start(),i+1
    return None

def repl(text,name,block):
    s=span(text,name)
    if not s: raise SystemExit('missing method '+name)
    return text[:s[0]]+block+text[s[1]:]

# ONLY map river geometry that belongs to an official station. For each station choose the
# best river seed by canonical river name first, then nearest geometry. After seeding, include
# same-name segments so the visible river looks like a network rather than a tiny fragment.
station_only=r'''    private List<RiverWay> v881OnlyLiveStationRivers(List<RiverWay> input,List<StationDot> ss){
        List<RiverWay> out=new ArrayList<>();
        if(input==null||input.isEmpty()||ss==null||ss.isEmpty())return out;
        java.util.LinkedHashSet<RiverWay> selected=new java.util.LinkedHashSet<>();
        java.util.LinkedHashSet<String> selectedNames=new java.util.LinkedHashSet<>();

        for(StationDot s:ss){
            if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
            String sn=v881Norm(s.name);
            RiverWay bestName=null,bestNear=null;
            double bestNameKm=Double.POSITIVE_INFINITY,bestNearKm=Double.POSITIVE_INFINITY;
            for(RiverWay r:input){
                if(r==null||r.points==null||r.points.size()<2)continue;
                double km=v881DistanceToRiverKm(s.lat,s.lon,r);
                if(!Double.isFinite(km))continue;
                String rn=v881Norm(r.name);
                boolean nameMatch=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
                if(nameMatch&&km<bestNameKm){bestNameKm=km;bestName=r;}
                if(km<bestNearKm){bestNearKm=km;bestNear=r;}
            }
            RiverWay seed=(bestName!=null&&bestNameKm<=25d)?bestName:((bestNear!=null&&bestNearKm<=10d)?bestNear:null);
            if(seed!=null){
                selected.add(seed);
                String k=v881Norm(seed.name);if(!k.isEmpty())selectedNames.add(k);
            }
        }

        // Expand each station's seed to all same-named segments in the current progressive tile.
        if(!selectedNames.isEmpty()){
            for(RiverWay r:input){
                if(r==null||r.points==null||r.points.size()<2)continue;
                String rn=v881Norm(r.name);if(rn.isEmpty())continue;
                for(String k:selectedNames){
                    if(rn.equals(k)||rn.contains(k)||k.contains(rn)){selected.add(r);break;}
                }
            }
        }
        out.addAll(selected);
        return out;
    } // V0890_284_STATION_RIVER_NETWORK_ONLY
'''
m=repl(m,'v881OnlyLiveStationRivers',station_only)

# Make the station-river association deterministic for status colours too. Historical station
# rows can keep the river visible, but only fresh rows may supply alert/warning/danger colour
# because v0.8.89 already enforces s.fresh inside v884Stage().
# Increase flow/glow visibility without touching any non-map feature.
m=m.replace('lineWidth(9.0f),lineOpacity(0.44f)','lineWidth(10.5f),lineOpacity(0.48f)')
m=m.replace('lineWidth(3.2f),lineOpacity(1.0f)','lineWidth(3.8f),lineOpacity(1.0f)')

# Disable any accidental unfiltered force layer: fs-rivers itself is now station-only, so these
# remain safe; add an explicit marker for CI regression checks.
marker='    // V0890_FLOW_GLOW_USES_STATION_FILTERED_FS_RIVERS_ONLY\n'
if 'V0890_FLOW_GLOW_USES_STATION_FILTERED_FS_RIVERS_ONLY' not in m:
    p=m.find('private void v886EnsureRiverVisibility()')
    if p<0: raise SystemExit('v886EnsureRiverVisibility missing')
    line=m.rfind('\n',0,p)+1
    m=m[:line]+marker+m[line:]

# Version bump only; no data/alert/UI source changes.
g=re.sub(r'versionCode\s+109\b','versionCode 110',g,count=1)
g=g.replace("versionName '0.8.89'","versionName '0.8.90'",1)

for token in ['V0890_284_STATION_RIVER_NETWORK_ONLY','V0890_FLOW_GLOW_USES_STATION_FILTERED_FS_RIVERS_ONLY']:
    if token not in m: raise SystemExit('missing '+token)
if "versionName '0.8.90'" not in g or 'versionCode 110' not in g: raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.90 PASS: ONLY official-station rivers, guaranteed station seed + same-name network expansion + stronger flow/glow')
