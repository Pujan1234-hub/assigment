from pathlib import Path
import json, sys

try:
    from shapely.geometry import shape, LineString
    from shapely.ops import unary_union
    try:
        from shapely import make_valid
    except Exception:
        make_valid = None
except Exception as e:
    raise SystemExit('shapely required: '+str(e))

ROOT=Path(__file__).resolve().parent
build=ROOT/'app/build'
# Locate the generated assets created by :app:bundleFloodSafe.
overviews=list(build.rglob('data/nepal-waterways-tiles/overview.json'))
if not overviews:
    raise SystemExit('generated overview.json not found under app/build')
overview=overviews[0]
assets_root=overview.parents[2]

# Find the exact 77-district Nepal mask from the same generated asset tree.
district_candidates=list(assets_root.rglob('floodsafe-nepal/v24/nepal-districts.geojson'))
if not district_candidates:
    district_candidates=list(build.rglob('floodsafe-nepal/v24/nepal-districts.geojson'))
if not district_candidates:
    raise SystemExit('generated Nepal district GeoJSON not found')
district_path=district_candidates[0]

district_fc=json.loads(district_path.read_text(encoding='utf-8'))
polys=[]
for f in district_fc.get('features',[]):
    if not f.get('geometry'):
        continue
    g=shape(f['geometry'])
    # Some district source rings contain tiny self-intersections. Repair every district
    # BEFORE union, otherwise GEOS can fail with a topology side-location conflict.
    try:
        if not g.is_valid:
            g=make_valid(g) if make_valid is not None else g.buffer(0)
        if not g.is_valid:
            g=g.buffer(0)
    except Exception:
        try:g=g.buffer(0)
        except Exception:continue
    if not g.is_empty:
        polys.append(g)
if len(polys)<70:
    raise SystemExit(f'expected Nepal district polygons, found {len(polys)}')
try:
    nepal=unary_union(polys)
except Exception:
    # Last-resort robust repair for any remaining topology edge case.
    nepal=unary_union([p.buffer(0) for p in polys if not p.is_empty])
if not nepal.is_valid:
    nepal=make_valid(nepal) if make_valid is not None else nepal.buffer(0)

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
            coords=[(float(q[0]),float(q[1])) for q in pts if len(q)>=2]
            if len(coords)<2:continue
            line=LineString(coords)
            inter=line.intersection(nepal)
        except Exception:
            continue
        for part in lines_from(inter):
            coords=list(part.coords)
            if len(coords)<2:
                continue
            nw=dict(w)
            nw['pts']=[[round(x,6),round(y,6)] for x,y in coords]
            if 'id' in nw:
                nw['id']=str(nw['id'])+'-np-'+str(len(clipped))
            clipped.append(nw)
            total_out+=1
    obj['waterways']=clipped
    obj['count']=len(clipped)
    obj['source_note']='Build-time strict Nepal district-union clip; no runtime cross-border waterways.'
    p.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

print(f'PRECLIP_NEPAL_WATERWAYS PASS files={len(files)} input={total_in} output={total_out} mask={district_path}')
