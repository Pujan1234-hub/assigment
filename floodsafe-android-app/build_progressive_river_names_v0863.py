from pathlib import Path
import json, runpy
from shapely.geometry import LineString

root=Path(__file__).resolve().parent
ns=runpy.run_path(str(root/'build_progressive_river_tiers_v0842.py'),run_name='__v0863_base__')
water_dir=ns['water_dir']
major=ns['major']; medium=ns['medium']

# v0.8.42 intentionally packed each tier into one MultiLineString, which discarded
# each individual river's name. Re-write the same selected geometry as per-river
# features so a tap can identify the actual named river instead of every line being
# "नदी / खोला". Geometry coverage/selection is unchanged.
def build_named(selected,out_name,tol,tier_name):
    features=[];west=east=0;named=0
    for w in selected:
        pts=[]
        for p in w.get('pts') or []:
            if isinstance(p,list) and len(p)>=2:
                try:pts.append((float(p[0]),float(p[1])))
                except Exception:pass
        if len(pts)<2:continue
        try:pts=list(LineString(pts).simplify(tol,preserve_topology=False).coords)
        except Exception:pass
        if len(pts)<2:continue
        coords=[[round(x,5),round(y,5)] for x,y in pts]
        name_en=str(w.get('name_en') or '').strip()
        name=str(w.get('name') or '').strip()
        name_ne=str(w.get('name_ne') or '').strip()
        # Official BIPAD/DHM station names are mostly Latin-script, so prefer name_en
        # for reliable same-river matching, then fall back to the native OSM name.
        display=name_en or name or name_ne or 'नदी / खोला'
        if display!='नदी / खोला':named+=1
        props={'source':'OpenStreetMap via Overpass','license':'ODbL','display':tier_name,
               'name':display,'type':str(w.get('type') or 'stream')}
        if name:props['name_osm']=name
        if name_en:props['name_en']=name_en
        if name_ne:props['name_ne']=name_ne
        if w.get('id') is not None:props['osm_id']=str(w.get('id'))
        features.append({'type':'Feature','properties':props,
                         'geometry':{'type':'LineString','coordinates':coords}})
        if any(80.0<=x<=81.7 and 28.0<=y<=30.5 for x,y in pts):west+=1
        if any(87.0<=x<=88.4 and 26.2<=y<=28.35 for x,y in pts):east+=1
    obj={'type':'FeatureCollection','features':features,
         'source_note':'FloodSafe v0.8.63 named progressive Nepal river tier; same v0.8.42 selected geometry with per-river properties preserved.',
         'line_count':len(features),'named_line_count':named,'far_west_line_count':west,
         'far_east_line_count':east,'simplify_tolerance_degrees':tol}
    out=water_dir.parent/out_name
    out.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    return obj,out

ma,mp=build_named(major,'nepal-waterways-major-v0842.geojson',0.0030,'FloodSafe v0.8.63 named major Nepal rivers')
me,ep=build_named(medium,'nepal-waterways-medium-v0842.geojson',0.0018,'FloodSafe v0.8.63 named medium Nepal rivers')
if not (650<=ma['line_count']<=1100):raise SystemExit('v0863 major count '+str(ma['line_count']))
if not (3200<=me['line_count']<=4700):raise SystemExit('v0863 medium count '+str(me['line_count']))
if ma['far_west_line_count']<25 or ma['far_east_line_count']<25:raise SystemExit('v0863 major edge coverage')
if me['far_west_line_count']<100 or me['far_east_line_count']<100:raise SystemExit('v0863 medium edge coverage')
if ma['named_line_count']<50 or me['named_line_count']<150:raise SystemExit('v0863 too few named rivers')
if mp.stat().st_size>1800000 or ep.stat().st_size>7000000:raise SystemExit('v0863 named tier unexpectedly large')
print('V0863_NAMED_PROGRESSIVE_RIVERS PASS',ma['line_count'],ma['named_line_count'],mp.stat().st_size,me['line_count'],me['named_line_count'],ep.stat().st_size)
