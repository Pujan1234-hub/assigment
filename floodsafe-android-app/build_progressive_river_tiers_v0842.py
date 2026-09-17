from pathlib import Path
import json, math, re
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parent
build = ROOT / 'app' / 'build'
manifests = list(build.rglob('data/nepal-waterways-tiles/manifest.json'))
if not manifests:
    raise SystemExit('v0.8.42 generated waterway manifest missing')
water_dir = manifests[0].parent
manifest = json.loads(manifests[0].read_text(encoding='utf-8'))
min_lon = float(manifest.get('minLon', 80.0))
min_lat = float(manifest.get('minLat', 26.2))
step_lon = float(manifest.get('stepLon', 0.70))
step_lat = float(manifest.get('stepLat', 0.60))

# User-facing goal: whole-Nepal view must stay readable. Start with only a balanced
# major network, add a medium network on the first zoom step, then let the existing
# visible regional tiles and exact local tiles take over. This preserves Far West/East
# coverage without painting all ~55k waterways at Nepal-wide zoom.

TILES_X = 12
TILES_Y = 8


def hav_km(a, b):
    lon1, lat1 = a; lon2, lat2 = b
    r = 6371.0
    p1 = math.radians(lat1); p2 = math.radians(lat2)
    dp = math.radians(lat2-lat1); dl = math.radians(lon2-lon1)
    q = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.atan2(math.sqrt(q), math.sqrt(max(1e-15,1-q)))


def length_km(pts):
    total = 0.0
    for a,b in zip(pts,pts[1:]):
        try: total += hav_km((float(a[0]),float(a[1])),(float(b[0]),float(b[1])))
        except Exception: pass
    return total


def key(w):
    raw = str(w.get('id') or '')
    if raw:
        return raw
    pts = w.get('pts') or []
    if len(pts) < 2:
        return ''
    a,b = pts[0],pts[-1]
    return f"{w.get('type','stream')}|{round(float(a[0]),5)}:{round(float(a[1]),5)}|{round(float(b[0]),5)}:{round(float(b[1]),5)}"


def score(w):
    pts = w.get('pts') or []
    typ = (w.get('type') or 'stream').lower()
    named = bool((w.get('name') or '').strip() or (w.get('name_ne') or '').strip() or (w.get('name_en') or '').strip())
    lk = length_km(pts)
    return (14000 if typ == 'river' else 0) + (3200 if named else 0) + min(9000, lk*65.0) + min(1800, len(pts)*9)


def bucket_for(w):
    pts = w.get('pts') or []
    if not pts:
        return (0,0)
    p = pts[len(pts)//2]
    lo,la = float(p[0]),float(p[1])
    x = max(0,min(TILES_X-1,int(math.floor((lo-min_lon)/step_lon))))
    y = max(0,min(TILES_Y-1,int(math.floor((la-min_lat)/step_lat))))
    return (x,y)


tile_files = sorted([p for p in water_dir.glob('*.json') if re.fullmatch(r'\d+-\d+\.json',p.name)], key=lambda p: tuple(map(int,p.stem.split('-'))))
if len(tile_files) < 90:
    raise SystemExit(f'v0.8.42 expected dense Nepal tiles, found {len(tile_files)}')

all_by_key = {}
for p in tile_files:
    obj = json.loads(p.read_text(encoding='utf-8'))
    for w in obj.get('waterways') or []:
        if not isinstance(w,dict) or len(w.get('pts') or []) < 2:
            continue
        k = key(w)
        if not k:
            continue
        old = all_by_key.get(k)
        if old is None or score(w) > score(old):
            all_by_key[k] = w

ways = list(all_by_key.values())
ranked = sorted(ways,key=score,reverse=True)
buckets = {(x,y):[] for x in range(TILES_X) for y in range(TILES_Y)}
for w in ranked:
    buckets[bucket_for(w)].append(w)


def choose(target, per_cell):
    chosen = {}
    for c in sorted(buckets):
        for w in buckets[c][:per_cell]:
            k=key(w)
            if k: chosen[k]=w
    for w in ranked:
        if len(chosen) >= target:
            break
        k=key(w)
        if k and k not in chosen:
            chosen[k]=w
    return list(chosen.values())


def make_asset(selected, out_name, tol, tier_name):
    lines=[]
    west=east=0
    for w in selected:
        pts=[]
        for p in w.get('pts') or []:
            if isinstance(p,list) and len(p)>=2:
                try: pts.append((float(p[0]),float(p[1])))
                except Exception: pass
        if len(pts)<2: continue
        try:
            simple=LineString(pts).simplify(tol,preserve_topology=False)
            pts=list(simple.coords)
        except Exception:
            pass
        if len(pts)<2: continue
        rounded=[[round(x,5),round(y,5)] for x,y in pts]
        lines.append(rounded)
        if any(80.0<=x<=81.7 and 28.0<=y<=30.5 for x,y in pts): west+=1
        if any(87.0<=x<=88.4 and 26.2<=y<=28.35 for x,y in pts): east+=1
    obj={
        'type':'FeatureCollection',
        'features':[{
            'type':'Feature',
            'properties':{'source':'OpenStreetMap via Overpass','license':'ODbL','display':tier_name},
            'geometry':{'type':'MultiLineString','coordinates':lines}
        }],
        'source_note':'Spatially balanced progressive FloodSafe display tier from build-time Nepal-clipped OSM waterways.',
        'line_count':len(lines),
        'far_west_line_count':west,
        'far_east_line_count':east,
        'simplify_tolerance_degrees':tol,
    }
    out=water_dir.parent/out_name
    out.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    return obj,out

major = choose(900, 5)
medium = choose(4200, 24)
major_obj,major_path = make_asset(major,'nepal-waterways-major-v0842.geojson',0.0030,'FloodSafe v0.8.42 major Nepal rivers')
medium_obj,medium_path = make_asset(medium,'nepal-waterways-medium-v0842.geojson',0.0018,'FloodSafe v0.8.42 medium Nepal rivers')

if not (650 <= major_obj['line_count'] <= 1100):
    raise SystemExit(f"v0.8.42 major tier unexpected size: {major_obj['line_count']}")
if not (3200 <= medium_obj['line_count'] <= 4700):
    raise SystemExit(f"v0.8.42 medium tier unexpected size: {medium_obj['line_count']}")
if major_obj['far_west_line_count'] < 25 or major_obj['far_east_line_count'] < 25:
    raise SystemExit(f"v0.8.42 major edge coverage weak west={major_obj['far_west_line_count']} east={major_obj['far_east_line_count']}")
if medium_obj['far_west_line_count'] < 100 or medium_obj['far_east_line_count'] < 100:
    raise SystemExit(f"v0.8.42 medium edge coverage weak west={medium_obj['far_west_line_count']} east={medium_obj['far_east_line_count']}")
if major_path.stat().st_size > 900000 or medium_path.stat().st_size > 3000000:
    raise SystemExit(f'v0.8.42 tier asset too large major={major_path.stat().st_size} medium={medium_path.stat().st_size}')

print('V0842_PROGRESSIVE_TIERS PASS',
      'major=',major_obj['line_count'],'major_west=',major_obj['far_west_line_count'],'major_east=',major_obj['far_east_line_count'],'major_bytes=',major_path.stat().st_size,
      'medium=',medium_obj['line_count'],'medium_west=',medium_obj['far_west_line_count'],'medium_east=',medium_obj['far_east_line_count'],'medium_bytes=',medium_path.stat().st_size)
