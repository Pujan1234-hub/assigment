from pathlib import Path
import json, math, re

ROOT = Path(__file__).resolve().parent
build = ROOT / 'app' / 'build'
overviews = list(build.rglob('data/nepal-waterways-tiles/overview.json'))
if not overviews:
    raise SystemExit('v0.8.39 generated overview.json not found under app/build')
overview_path = overviews[0]
water_dir = overview_path.parent
manifest_path = water_dir / 'manifest.json'
if not manifest_path.exists():
    raise SystemExit('v0.8.39 generated waterway manifest missing')

manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
old_overview = json.loads(overview_path.read_text(encoding='utf-8'))
min_lon = float(manifest.get('minLon', 80.0))
min_lat = float(manifest.get('minLat', 26.2))
step_lon = float(manifest.get('stepLon', 0.70))
step_lat = float(manifest.get('stepLat', 0.60))

# Keep national startup light, but make the overview spatially fair. The previous
# top-ranked-per-tile sample could cluster around one side of a tile and leave whole
# districts looking blank even though the dense OSM tile contained real rivers.
SUB = 4
PER_CELL = 6
QUOTA_PER_TILE = 100

def score(w):
    pts = w.get('pts') or []
    named = bool((w.get('name') or '').strip() or (w.get('name_ne') or '').strip() or (w.get('name_en') or '').strip())
    typ = (w.get('type') or 'stream').lower()
    return (1800 if typ == 'river' else 0) + (700 if named else 0) + min(700, len(pts) * 6)

def base_id(w):
    raw = str(w.get('id') or '')
    if raw:
        return re.sub(r'-np-\d+$', '', raw)
    pts = w.get('pts') or []
    if not pts:
        return ''
    a, b = pts[0], pts[-1]
    return f"{w.get('type','stream')}|{round(float(a[0]),5)}:{round(float(a[1]),5)}|{round(float(b[0]),5)}:{round(float(b[1]),5)}"

def touched_cells(w, tx, ty):
    west = min_lon + tx * step_lon
    south = min_lat + ty * step_lat
    cells = set()
    for p in (w.get('pts') or []):
        if not isinstance(p, list) or len(p) < 2:
            continue
        try:
            lo, la = float(p[0]), float(p[1])
        except Exception:
            continue
        if not (west - 1e-8 <= lo <= west + step_lon + 1e-8 and south - 1e-8 <= la <= south + step_lat + 1e-8):
            continue
        sx = max(0, min(SUB - 1, int(((lo - west) / step_lon) * SUB)))
        sy = max(0, min(SUB - 1, int(((la - south) / step_lat) * SUB)))
        cells.add((sx, sy))
    if cells:
        return cells
    # Defensive fallback for a line whose source vertices are just outside the tile.
    pts = w.get('pts') or []
    if pts:
        try:
            lo = sum(float(p[0]) for p in pts if len(p) >= 2) / len(pts)
            la = sum(float(p[1]) for p in pts if len(p) >= 2) / len(pts)
            sx = max(0, min(SUB - 1, int(((lo - west) / step_lon) * SUB)))
            sy = max(0, min(SUB - 1, int(((la - south) / step_lat) * SUB)))
            cells.add((sx, sy))
        except Exception:
            pass
    return cells

selected_global = {}
tile_files = sorted(
    [p for p in water_dir.glob('*.json') if re.fullmatch(r'\d+-\d+\.json', p.name)],
    key=lambda p: tuple(map(int, p.stem.split('-')))
)
if len(tile_files) < 50:
    raise SystemExit(f'v0.8.39 expected Nepal tile set, found {len(tile_files)} files')

for p in tile_files:
    tx, ty = map(int, p.stem.split('-'))
    obj = json.loads(p.read_text(encoding='utf-8'))
    ways = [w for w in (obj.get('waterways') or []) if isinstance(w, dict) and len(w.get('pts') or []) >= 2]
    if not ways:
        continue
    ranked = sorted(ways, key=score, reverse=True)
    buckets = {(x, y): [] for x in range(SUB) for y in range(SUB)}
    for w in ranked:
        for c in touched_cells(w, tx, ty):
            buckets[c].append(w)

    local = {}
    # First reserve representation for every part of this geographic tile.
    for c in sorted(buckets):
        for w in buckets[c][:PER_CELL]:
            k = base_id(w)
            if k:
                local[k] = w

    # Then fill remaining capacity with the strongest river/stream geometry in the tile.
    if len(local) < QUOTA_PER_TILE:
        for w in ranked:
            k = base_id(w)
            if not k or k in local:
                continue
            local[k] = w
            if len(local) >= QUOTA_PER_TILE:
                break

    for k, w in local.items():
        if k not in selected_global or score(w) > score(selected_global[k]):
            selected_global[k] = w

balanced = list(selected_global.values())
balanced.sort(key=score, reverse=True)
if len(balanced) < 1500:
    raise SystemExit(f'v0.8.39 balanced overview unexpectedly small: {len(balanced)}')

# Verify both edges that were visibly blank on the real phone screenshot now have
# representative OSM waterway geometry in the national/regional overview.
def point_count(west, south, east, north):
    n = 0
    for w in balanced:
        for p in (w.get('pts') or []):
            if len(p) >= 2:
                lo, la = float(p[0]), float(p[1])
                if west <= lo <= east and south <= la <= north:
                    n += 1
                    break
    return n

far_west = point_count(80.0, 28.0, 81.7, 30.5)
far_east = point_count(87.0, 26.2, 88.4, 28.3)
if far_west < 20 or far_east < 20:
    raise SystemExit(f'v0.8.39 edge coverage too sparse: west={far_west} east={far_east}')

out = dict(old_overview)
out['waterways'] = balanced
out['count'] = len(balanced)
out['source_note'] = 'Build-time strict Nepal district-union clip; spatially balanced national overview for complete regional coverage.'
overview_path.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
manifest['overview_count'] = len(balanced)
manifest['overview_strategy'] = 'v0.8.39 spatially balanced 4x4 subcells per source tile'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

print(f'V0839_BALANCED_OVERVIEW PASS waterways={len(balanced)} far_west={far_west} far_east={far_east} bytes={overview_path.stat().st_size}')
