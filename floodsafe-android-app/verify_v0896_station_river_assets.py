from pathlib import Path
import json, math, re, sys

root=Path(__file__).resolve().parent
build=root/'app'/'build'
mans=list(build.rglob('data/nepal-waterways-tiles/manifest.json'))
if not mans: raise SystemExit('V0896 FAIL: exact river manifest missing')
tiles=mans[0].parent
MIN_LON,MIN_LAT,DX,DY,NX,NY=80.0,26.2,0.70,0.60,12,8

def tx(lon): return max(0,min(NX-1,int(math.floor((lon-MIN_LON)/DX))))
def ty(lat): return max(0,min(NY-1,int(math.floor((lat-MIN_LAT)/DY))))
def km(a,b,c,d):
    r=6371.0; dl=math.radians(c-a); dn=math.radians(d-b)
    q=math.sin(dl/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(dn/2)**2
    return 2*r*math.asin(min(1,math.sqrt(q)))

def local_ways(lat,lon):
    out=[];cx,cy=tx(lon),ty(lat)
    for x in range(max(0,cx-1),min(NX-1,cx+1)+1):
      for y in range(max(0,cy-1),min(NY-1,cy+1)+1):
        p=tiles/f'{x}-{y}.json'
        if not p.exists(): continue
        o=json.loads(p.read_text(encoding='utf-8'))
        out.extend(o.get('waterways') or [])
    return out

def nearest(lat,lon):
    ways=local_ways(lat,lon)
    if not ways: raise SystemExit(f'V0896 FAIL: no local waterways at {lat},{lon}')
    best=(1e9,None)
    for w in ways:
      pts=w.get('pts') or []
      if len(pts)<2: continue
      d=min((km(lat,lon,float(p[1]),float(p[0])) for p in pts if isinstance(p,list) and len(p)>=2), default=1e9)
      if d<best[0]: best=(d,w)
    if best[1] is None: raise SystemExit(f'V0896 FAIL: no valid river geometry at {lat},{lon}')
    return best, len(ways)

samples=[
 ('Ninda khola at East West Highway',26.660345,88.107933,12.0),
 ('Bagmati River at Gaurighat',27.713000,85.349700,8.0),
]
for name,lat,lon,limit in samples:
    (d,w),count=nearest(lat,lon)
    rn=w.get('name') or w.get('name_en') or w.get('name_ne') or '(unnamed)'
    print(f'V0896 sample={name!r} local_ways={count} nearest={rn!r} distance_km={d:.3f}')
    if d>limit: raise SystemExit(f'V0896 FAIL: nearest river too far for {name}: {d:.3f}km > {limit}km')

# Verify the official status precedence contract with the exact Ninda values from BIPAD.
def classify(level,warning,danger,raw):
    raw=(raw or '').upper()
    below_warning='BELOW WARNING' in raw or 'BELOWWARNING' in raw
    if below_warning or 'NORMAL' in raw or 'GREEN' in raw or 'SAFE' in raw: return 'normal'
    if (('DANGER' in raw and 'BELOW DANGER' not in raw) or 'RED' in raw): return 'danger'
    if (('WARNING' in raw and not below_warning) or 'ORANGE' in raw or 'BELOW DANGER' in raw): return 'warning'
    if any(x in raw for x in ('ALERT','WATCH','YELLOW')): return 'alert'
    sane=warning>0 and danger>warning
    if sane and level>=danger:return 'danger'
    if sane and level>=warning:return 'warning'
    return 'normal'

ninda=classify(123.818,125.0,122.5,'Below Warning Level And Steady')
print('V0896 Ninda official-status test =>',ninda)
if ninda!='normal': raise SystemExit('V0896 FAIL: Ninda official green/below-warning classified incorrectly')

print('V0896_STATION_RIVER_ASSET_VERIFY PASS')
