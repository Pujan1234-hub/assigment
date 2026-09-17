from pathlib import Path
import json, re, shutil

ROOT = Path(__file__).resolve().parent
build = ROOT / 'app' / 'build'
overviews = list(build.rglob('data/nepal-waterways-tiles/overview.json'))
if not overviews:
    raise SystemExit('v0.8.40 generated overview missing')
water_dir = overviews[0].parent
manifest_path = water_dir / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
min_lon = float(manifest.get('minLon', 80.0))
min_lat = float(manifest.get('minLat', 26.2))
step_lon = float(manifest.get('stepLon', 0.70))
step_lat = float(manifest.get('stepLat', 0.60))

# A separate, lightweight regional network solves the real-phone hole problem without
# making the phone parse the full 62k-way national dataset at regional zoom. Every source
# tile is sampled evenly across 6x6 subcells, then filled by real river/stream score.
# Runtime only opens the lightweight files intersecting the visible screen and caches them.
OUT = water_dir.parent / 'nepal-waterways-tiles-regional'
shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir(parents=True, exist_ok=True)
SUB = 6
PER_CELL = 5
QUOTA = 180

def score(w):
    pts = w.get('pts') or []
    typ = (w.get('type') or 'stream').lower()
    named = bool((w.get('name') or '').strip() or (w.get('name_ne') or '').strip() or (w.get('name_en') or '').strip())
    return (2200 if typ == 'river' else 0) + (650 if named else 0) + min(650, len(pts) * 5)

def key(w):
    raw = str(w.get('id') or '')
    if raw:
        return raw
    pts = w.get('pts') or []
    if not pts:
        return ''
    a, b = pts[0], pts[-1]
    return f"{w.get('type','stream')}|{round(float(a[0]),5)}:{round(float(a[1]),5)}|{round(float(b[0]),5)}:{round(float(b[1]),5)}"

def cells_for(w, tx, ty):
    west = min_lon + tx * step_lon
    south = min_lat + ty * step_lat
    out = set()
    for p in w.get('pts') or []:
        if not isinstance(p, list) or len(p) < 2:
            continue
        try:
            lo, la = float(p[0]), float(p[1])
        except Exception:
            continue
        if west - 1e-8 <= lo <= west + step_lon + 1e-8 and south - 1e-8 <= la <= south + step_lat + 1e-8:
            sx = max(0, min(SUB - 1, int(((lo - west) / step_lon) * SUB)))
            sy = max(0, min(SUB - 1, int(((la - south) / step_lat) * SUB)))
            out.add((sx, sy))
    return out

tiles = sorted([p for p in water_dir.glob('*.json') if re.fullmatch(r'\d+-\d+\.json', p.name)], key=lambda p: tuple(map(int, p.stem.split('-'))))
if len(tiles) < 80:
    raise SystemExit(f'v0.8.40 expected dense Nepal tiles, got {len(tiles)}')

all_selected = []
max_bytes = 0
for p in tiles:
    tx, ty = map(int, p.stem.split('-'))
    obj = json.loads(p.read_text(encoding='utf-8'))
    ways = [w for w in (obj.get('waterways') or []) if isinstance(w, dict) and len(w.get('pts') or []) >= 2]
    ranked = sorted(ways, key=score, reverse=True)
    buckets = {(x, y): [] for x in range(SUB) for y in range(SUB)}
    for w in ranked:
        for c in cells_for(w, tx, ty):
            buckets[c].append(w)
    chosen = {}
    for c in sorted(buckets):
        for w in buckets[c][:PER_CELL]:
            k = key(w)
            if k:
                chosen[k] = w
    for w in ranked:
        if len(chosen) >= QUOTA:
            break
        k = key(w)
        if k and k not in chosen:
            chosen[k] = w
    selected = list(chosen.values())
    out = {
        'count': len(selected),
        'source': obj.get('source', manifest.get('source')),
        'license': obj.get('license', manifest.get('license')),
        'source_note': 'v0.8.40 build-time strict Nepal clip; lightweight spatially balanced regional display tile.',
        'waterways': selected,
    }
    dest = OUT / p.name
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    max_bytes = max(max_bytes, dest.stat().st_size)
    all_selected.extend(selected)

# Real-phone screenshot target areas. These are the actual western/eastern boxes that were
# visually blank. Verify the new runtime asset set contains substantial real OSM geometry there.
def count_box(west, south, east, north):
    n = 0
    seen = set()
    for w in all_selected:
        k = key(w)
        if k in seen:
            continue
        for p in w.get('pts') or []:
            if len(p) >= 2 and west <= float(p[0]) <= east and south <= float(p[1]) <= north:
                seen.add(k); n += 1; break
    return n

west = count_box(80.0, 28.0, 81.7, 30.5)
east = count_box(87.0, 26.2, 88.35, 28.35)
if west < 120 or east < 120:
    raise SystemExit(f'v0.8.40 regional edge coverage insufficient west={west} east={east}')
if max_bytes > 950000:
    raise SystemExit(f'v0.8.40 regional tile too large: {max_bytes}')

index = {
    'strategy': 'v0.8.40 visible-screen regional tiles; 6x6 spatial cells; max 180 waterways per source tile',
    'tile_count': len(tiles),
    'far_west_count': west,
    'far_east_count': east,
    'max_tile_bytes': max_bytes,
}
(OUT / 'index.json').write_text(json.dumps(index, separators=(',', ':')), encoding='utf-8')
print(f'V0840_REGIONAL_TILES PASS tiles={len(tiles)} west={west} east={east} max_bytes={max_bytes}')
