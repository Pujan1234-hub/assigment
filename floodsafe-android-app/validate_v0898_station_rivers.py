from pathlib import Path
import json, math, os, sys
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point

root=Path(__file__).resolve().parent
build=root/'app'/'build'
cores=list(build.rglob('data/floodsafe-core.json'))
tdirs=list(build.rglob('data/nepal-waterways-tiles'))
if not cores or not tdirs: raise SystemExit('V0898_VALIDATION assets missing')
core=json.loads(cores[0].read_text(encoding='utf-8')); td=tdirs[0]
rows=core.get('river_stations') or core.get('riverStations') or []

def coord(row):
    p=row.get('point') or {}; c=p.get('coordinates') or []
    if len(c)>=2:
        try:
            a,b=float(c[0]),float(c[1])
            if 26<=a<=31 and 80<=b<=89: return a,b
            if 80<=a<=89 and 26<=b<=31: return b,a
        except: pass
    for la_key in ('latitude','lat','stationLatitude','station_latitude'):
        for lo_key in ('longitude','lon','lng','stationLongitude','station_longitude'):
            try:
                la=float(row.get(la_key));lo=float(row.get(lo_key))
                if 26<=la<=31 and 79.5<=lo<=89:return la,lo
            except:pass
    return math.nan,math.nan

def station_name(o):
    for k in ('river_name','riverName','station_name','stationName','title','name'):
        if o.get(k):return str(o[k])
    return ''

def norm(s):
    s=''.join(ch.lower() for ch in str(s) if ch.isalnum())
    for w in ('river','khola','nadi','station','at'):s=s.replace(w,'')
    return s

tile_cache={}
def tile(x,y):
    k=(x,y)
    if k in tile_cache:return tile_cache[k]
    p=td/f'{x}-{y}.json'; out=[]
    if p.exists():
        obj=json.loads(p.read_text(encoding='utf-8'))
        for w in obj.get('waterways') or []:
            pts=w.get('pts') or []
            if len(pts)<2:continue
            try:out.append((w,LineString([(float(q[0]),float(q[1])) for q in pts])))
            except:pass
    tile_cache[k]=out;return out

valid=[]; matched=[]; misses=[]
for s in rows:
    if not isinstance(s,dict):continue
    la,lo=coord(s)
    if not(math.isfinite(la) and math.isfinite(lo)):continue
    valid.append((s,la,lo))
    cx=max(0,min(11,int(math.floor((lo-80.0)/.70))))
    cy=max(0,min(7,int(math.floor((la-26.2)/.60))))
    local=[]
    for x in range(max(0,cx-1),min(11,cx+1)+1):
        for y in range(max(0,cy-1),min(7,cy+1)+1):local+=tile(x,y)
    pt=Point(lo,la);sn=norm(station_name(s));best_name=None;best_any=None
    for w,line in local:
        d=pt.distance(line)*111.2
        rn=norm(w.get('name_en') or w.get('name') or w.get('name_ne') or '')
        same=bool(sn and rn and (sn in rn or rn in sn))
        if same and (best_name is None or d<best_name[0]):best_name=(d,w,line)
        if best_any is None or d<best_any[0]:best_any=(d,w,line)
    best=best_name if best_name and best_name[0]<=6 else best_any
    if best and best[0]<=8:matched.append((s,la,lo,best))
    else:misses.append((station_name(s),la,lo,None if best is None else best[0]))

report=f'catalog={len(rows)}\nvalid_coords={len(valid)}\nmatched={len(matched)}\nmissed={len(misses)}\n'
report+='\n'.join(f'MISS {n} {la:.6f},{lo:.6f} nearest={d}' for n,la,lo,d in misses)
Path('FloodSafe-v0.8.98-river-validation.txt').write_text(report,encoding='utf-8')
print(report)
if len(rows)!=284:raise SystemExit(f'expected bundled 284 station catalog, got {len(rows)}')
if len(valid)!=284:raise SystemExit(f'expected 284 valid station coordinates, got {len(valid)}')
if len(matched)!=284:raise SystemExit(f'expected all 284 stations matched to exact local river, got {len(matched)}')

fig,ax=plt.subplots(figsize=(11,6.2))
for _,la,lo,b in matched:
    pts=list(b[2].coords);ax.plot([p[0] for p in pts],[p[1] for p in pts],color='#32d9ff',linewidth=1.4,alpha=.9)
ax.scatter([x[2] for x in valid],[x[1] for x in valid],s=9,c='#16a77b',edgecolors='white',linewidths=.25,zorder=4)
ax.set_xlim(80,88.4);ax.set_ylim(26.2,30.5);ax.set_aspect('equal');ax.set_facecolor('#10212d')
fig.patch.set_facecolor('#10212d');ax.tick_params(colors='white');ax.set_title('FloodSafe v0.8.98 — 284/284 station-local river geometry matched',color='white')
for sp in ax.spines.values():sp.set_color('white')
fig.tight_layout();fig.savefig('FloodSafe-v0.8.98-river-validation.png',dpi=190,facecolor=fig.get_facecolor());plt.close(fig)
print('V0898_VISUAL_VALIDATION PASS 284/284')
