from pathlib import Path
import json, re, hashlib
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parent
build = ROOT / 'app' / 'build'
manifest_files = list(build.rglob('data/nepal-waterways-tiles/manifest.json'))
if not manifest_files:
    raise SystemExit('v0.8.41 generated waterway manifest missing')
manifest_path = manifest_files[0]
water_dir = manifest_path.parent
out_path = water_dir.parent / 'nepal-waterways-national-v0841.geojson'

# Build one lightweight nationwide MultiLineString from every Nepal-clipped OSM
# river/stream segment. Unlike overview sampling, this cannot leave Far West/Far East
# blank. A single geometry also keeps MapLibre feature overhead low on Android.
TOL = 0.0015  # ~150 m; only used for national/regional display, dense local tiles remain exact.

def geom_key(coords):
    a = tuple((round(float(x), 6), round(float(y), 6)) for x, y in coords)
    b = tuple(reversed(a))
    return a if a <= b else b

seen = set()
lines = []
input_ways = 0
input_vertices = 0
output_vertices = 0
far_west = 0
far_east = 0

tile_files = sorted(
    [p for p in water_dir.glob('*.json') if re.fullmatch(r'\d+-\d+\.json', p.name)],
    key=lambda p: tuple(map(int, p.stem.split('-')))
)
if len(tile_files) < 90:
    raise SystemExit(f'v0.8.41 expected dense Nepal tiles, found {len(tile_files)}')

for p in tile_files:
    obj = json.loads(p.read_text(encoding='utf-8'))
    for w in obj.get('waterways') or []:
        pts = w.get('pts') or []
        if len(pts) < 2:
            continue
        input_ways += 1
        try:
            coords = [(float(q[0]), float(q[1])) for q in pts if isinstance(q, list) and len(q) >= 2]
        except Exception:
            continue
        if len(coords) < 2:
            continue
        input_vertices += len(coords)
        key = geom_key(coords)
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            simple = LineString(coords).simplify(TOL, preserve_topology=False)
            sc = list(simple.coords)
        except Exception:
            sc = coords
        if len(sc) < 2:
            continue
        rounded = [[round(float(x), 5), round(float(y), 5)] for x, y in sc]
        lines.append(rounded)
        output_vertices += len(rounded)
        if any(80.0 <= x <= 81.7 and 28.0 <= y <= 30.5 for x, y in sc):
            far_west += 1
        if any(87.0 <= x <= 88.4 and 26.2 <= y <= 28.3 for x, y in sc):
            far_east += 1

if len(lines) < 45000:
    raise SystemExit(f'v0.8.41 national network unexpectedly small: {len(lines)}')
if far_west < 500 or far_east < 400:
    raise SystemExit(f'v0.8.41 national edge coverage too small: west={far_west} east={far_east}')

fc = {
    'type': 'FeatureCollection',
    'features': [{
        'type': 'Feature',
        'properties': {
            'source': 'OpenStreetMap via Overpass',
            'license': 'ODbL',
            'display': 'FloodSafe v0.8.41 full Nepal river network'
        },
        'geometry': {'type': 'MultiLineString', 'coordinates': lines}
    }],
    'source_note': 'All unique build-time Nepal-clipped OSM waterways, simplified only for national Android display; no geographic sampling.',
    'line_count': len(lines),
    'input_ways': input_ways,
    'input_vertices': input_vertices,
    'display_vertices': output_vertices,
    'simplify_tolerance_degrees': TOL,
    'far_west_line_count': far_west,
    'far_east_line_count': far_east
}
out_path.write_text(json.dumps(fc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
size = out_path.stat().st_size
if size > 9_000_000:
    raise SystemExit(f'v0.8.41 national network too large: {size}')
print(f'V0841_NATIONAL_NETWORK PASS lines={len(lines)} vertices={output_vertices} west={far_west} east={far_east} bytes={size}')
