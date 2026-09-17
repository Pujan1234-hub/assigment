from pathlib import Path
import json, sys

try:
    from shapely.geometry import shape, LineString, MultiLineString, GeometryCollection
    from shapely.ops import unary_union
except Exception as e:
    raise SystemExit('shapely required: '+str(e))

ROOT=Path(__file__).resolve().parent
build=ROOT/'app/build'
# Locate the generated assets created by :app:bundleFloodSafe.
overviews=list(build.rglob('data/nepal-waterways-tiles/overview.json'))
if not overviews:
    raise SystemExit('generated overview.json not found under app/build')
overview=overviews[0]
assets_root=overview.parents[2]  # .../assets root containing data/ and floodsafe-nepal/

# Find the exact 77-district Nepal mask from the same generated asset tree.
district_candidates=list(assets_root.rglob('floodsafe-nepal/v24/nepal-districts.geojson'))
if not district_candidates:
    district_candidates=list(build.rglob('floodsafe-nepal/v24/nepal-districts.geojson'))
if not district_candidates:
    raise SystemExit('generated Nepal district GeoJSON not found')
district_path=district_candidates[0]

district_fc=json.loads(district_path.read_text(encoding='utf-8'))
polys=[shape(f['geometry']) for f in district_fc.get('features',[]) if f.get('geometry')]
if len(polys)<70:
    raise SystemExit(f'expected Nepal district polygons, found {len(polys)}')
nepal=unary_union(polys)
if not nepal.is_valid:
    nepal=nepal.buffer(0)

water_dir=overview.parent
files=sorted(water_dir.glob('*.json'))
if len(files)<2:
    raise SystemExit('waterway tile set missing')

def lines_from(g):
    if g.is_empty:
        return []
    if g.geom_type=='LineString':
        return [g]
    if g.geom_type=='MultiLineString':
        return list(g.geoms)
    if g.geom_type=='GeometryCollection':
        out=[]
        for x in g.geoms:
            out.extend(lines_from(x))
        return out
    return []

total_in=total_out=0
for p in files:
    try:
        obj=json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    ways=obj.get('waterways')
    if not isinstance(ways,list):
        continue
    clipped=[]
    for w in ways:
        pts=w.get('pts') or []
        if len(pts)<2:
            continue
        total_in+=1
        try:
            line=LineString([(float(q[0]),float(q[1])) for q in pts if len(q)>=2])
            inter=line.intersection(nepal)
        except Exception:
            continue
        for part in lines_from(inter):
            coords=list(part.coords)
            if len(coords)<2:
                continue
            nw=dict(w)
            # Keep enough precision for river tap / smooth native drawing.
            nw['pts']=[[round(x,6),round(y,6)] for x,y in coords]
            # New unique id for split cross-border segments.
            if 'id' in nw:
                nw['id']=str(nw['id'])+'-np-'+str(len(clipped))
            clipped.append(nw)
            total_out+=1
    obj['waterways']=clipped
    obj['count']=len(clipped)
    obj['source_note']='Build-time strict Nepal district-union clip; no runtime cross-border waterways.'
    p.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

print(f'PRECLIP_NEPAL_WATERWAYS PASS files={len(files)} input={total_in} output={total_out} mask={district_path}')
