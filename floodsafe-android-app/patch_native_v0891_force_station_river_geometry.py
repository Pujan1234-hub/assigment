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
            // V0891: every official station MUST seed an actual river geometry. Prefer same-name river;
            // otherwise use nearest real river from the loaded verified river tile, with no arbitrary cutoff.
            RiverWay seed=bestName!=null?bestName:bestNear;
            if(seed!=null){
                selected.add(seed);
                String k=v881Norm(seed.name);if(!k.isEmpty())selectedNames.add(k);
            }
        }

        // Expand each station seed to same-name segments so a real network/river reach is visible.
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
    } // V0891_EVERY_STATION_FORCES_NEAREST_REAL_RIVER
'''
m=repl(m,'v881OnlyLiveStationRivers',station_only)

# Make flow/glow unmistakably visible above satellite imagery on the station-filtered source.
# Replace the v0.8.86 force layers if present.
m=re.sub(r'lineColor\("#00bfe8"\),lineWidth\([0-9.]+f\),lineOpacity\([0-9.]+f\)',
         'lineColor("#00c8ff"),lineWidth(9.0f),lineOpacity(0.50f)',m,count=1)
m=re.sub(r'lineColor\("#46e8ff"\),lineWidth\([0-9.]+f\),lineOpacity\([0-9.]+f\)',
         'lineColor("#68efff"),lineWidth(3.8f),lineOpacity(1.0f)',m,count=1)

# Ensure station update re-runs river geometry and force-visible layers on the new source.
set_sp=span(m,'setStations')
if not set_sp: raise SystemExit('setStations missing')
set_body=m[set_sp[0]:set_sp[1]]
if 'v879RefreshRiverGeometryForCamera();' in set_body and 'v886EnsureRiverVisibility();' not in set_body:
    set_body=set_body.replace('v879RefreshRiverGeometryForCamera();','v879RefreshRiverGeometryForCamera();\n        main.postDelayed(this::v886EnsureRiverVisibility, 250L); // V0891_FORCE_LAYER_AFTER_STATION_REFRESH',1)
    m=m[:set_sp[0]]+set_body+m[set_sp[1]:]

# Version bump only; no data/Supabase/alert/UI logic changes.
g=re.sub(r'versionCode\s+110\b','versionCode 111',g,count=1)
g=g.replace("versionName '0.8.90'","versionName '0.8.91'",1)

for token in ['V0891_EVERY_STATION_FORCES_NEAREST_REAL_RIVER','V0891_FORCE_LAYER_AFTER_STATION_REFRESH']:
    if token not in m: raise SystemExit('missing '+token)
if 'lineWidth(9.0f),lineOpacity(0.50f)' not in m or 'lineWidth(3.8f),lineOpacity(1.0f)' not in m:
    raise SystemExit('force flow/glow layer styling missing')
if "versionName '0.8.91'" not in g or 'versionCode 111' not in g: raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.91 PASS: every station forces nearest actual river geometry + visible cyan flow/glow')
