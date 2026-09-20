from pathlib import Path
import json
from shapely.geometry import shape,mapping,GeometryCollection,LineString,MultiLineString
from shapely.ops import unary_union

root=Path(__file__).resolve().parent
build=root/'app'/'build'
districts=list(build.rglob('floodsafe-nepal/v24/nepal-districts.geojson'))
if not districts: raise SystemExit('v0874 district GeoJSON missing from generated assets')
d=json.loads(districts[0].read_text(encoding='utf-8'))
nepal=unary_union([shape(f['geometry']) for f in d.get('features',[]) if f.get('geometry')]).buffer(0)
if nepal.is_empty: raise SystemExit('v0874 Nepal union empty')

names=['nepal-waterways-major-v0842.geojson','nepal-waterways-medium-v0842.geojson','nepal-waterways-national-v0841.geojson']

def line_only(g):
    if g.is_empty:return None
    if isinstance(g,(LineString,MultiLineString)):return g
    if isinstance(g,GeometryCollection):
        lines=[]
        for x in g.geoms:
            if isinstance(x,LineString):lines.append(x)
            elif isinstance(x,MultiLineString):lines.extend(list(x.geoms))
        if not lines:return None
        return lines[0] if len(lines)==1 else MultiLineString(lines)
    return None

checked=0
for name in names:
    hits=list(build.rglob('data/'+name))
    if not hits: raise SystemExit('v0874 display asset missing: '+name)
    p=hits[0];obj=json.loads(p.read_text(encoding='utf-8'));out=[];before=0;after=0
    for f in obj.get('features',[]):
        if not f.get('geometry'):continue
        g=shape(f['geometry']);before+=1
        q=line_only(g.intersection(nepal))
        if q is None:continue
        nf=dict(f);nf['geometry']=mapping(q);out.append(nf);after+=1
    obj['features']=out
    obj['source_note']='FloodSafe v0.8.74 strict Nepal polygon post-clip; no displayed river geometry outside Nepal.'
    p.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    # Hard audit: every displayed geometry must be fully covered by Nepal after clip.
    bad=0;outside_len=0.0
    for f in out:
        g=shape(f['geometry']);outside=g.difference(nepal)
        if not outside.is_empty and outside.length>1e-9:
            bad+=1;outside_len+=outside.length
    if bad:raise SystemExit(f'v0874 outside-Nepal geometry remains in {name}: bad={bad} outside_len={outside_len}')
    print('V0874_STRICT_NEPAL_DISPLAY',name,'features',before,'->',after,'bytes',p.stat().st_size)
    checked+=1
if checked!=3:raise SystemExit('v0874 did not audit all display tiers')
print('V0874_STRICT_NEPAL_DISPLAY PASS')
