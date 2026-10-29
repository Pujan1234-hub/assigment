#!/usr/bin/env python3
"""Create a small, real Nepal-only river layer before Android compilation."""
import json, sys, math
from pathlib import Path
from shapely.geometry import shape,LineString
from shapely.ops import unary_union

def river_lines(g):
    if g.is_empty:return
    if g.geom_type=='LineString':yield g
    elif g.geom_type in ('MultiLineString','GeometryCollection'):
        for p in g.geoms:yield from river_lines(p)

def main(src,district_file,dest):
    districts=json.loads(Path(district_file).read_text())['features']
    if len(districts)<50:raise RuntimeError('Missing Nepal districts')
    country=unary_union([shape(f['geometry']) for f in districts if f.get('geometry')])
    source=json.loads(Path(src).read_text()).get('waterways',[])
    if len(source)<100:raise RuntimeError('Missing rivers')
    ranked=[]
    for r in source:
        points=r.get('pts',[])
        coords=[]
        for p in points:
            if not isinstance(p,list) or len(p)<2:continue
            try:x,y=float(p[0]),float(p[1])
            except (TypeError,ValueError):continue
            if 79<x<89.5 and 25<y<31.5 and (not coords or coords[-1]!=(x,y)):coords.append((x,y))
        if len(coords)<2:continue
        geom=LineString(coords)
        if not geom.intersects(country):continue
        named=bool(r.get('name') or r.get('name_ne') or r.get('name_en'))
        score=(1000 if r.get('type')=='river' else 0)+(600 if named else 0)+min(2000,geom.length*250)
        ranked.append((score,geom,r))
    ranked.sort(key=lambda x:x[0],reverse=True)
    final=[]
    for _,geom,r in ranked[:1800]:
        try: clipped=geom.intersection(country)
        except Exception:continue
        for part in river_lines(clipped):
            if part.length<.008:continue
            simplified=part.simplify(.0009,preserve_topology=True)
            for segment in river_lines(simplified):
                if not country.buffer(.00001).covers(segment):segment=part
                xy=[[round(x,6),round(y,6)] for x,y in segment.coords]
                if len(xy)<2:continue
                name=r.get('name_ne') or r.get('name') or r.get('name_en') or 'नदी / खोला'
                final.append(dict(name=name,name_ne=name,type=r.get('type','stream'),pts=xy))
        if len(final)>=1400:break
    if len(final)<75:raise RuntimeError('No usable clipped Nepal rivers: '+str(len(final)))
    out=Path(dest);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'waterways':final,'source':'Nepal boundary-clipped official geometry'},ensure_ascii=False,separators=(',',':')))
    print('NATIVE_NEPAL_RIVERS',len(final),'json_bytes',out.stat().st_size)

if __name__=='__main__':main(*sys.argv[1:4])
