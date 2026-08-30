#!/usr/bin/env python3
import json
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('data/floodsafe-core.json')
UA = 'FloodSafe-Nepal/1.0 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/)'
ALERTS_URL = 'https://bipadportal.gov.np/api/v1/alert/?limit=300&ordering=-createdOn'
ROADS_URL = 'https://bipadportal.gov.np/api/v1/highway/?limit=500'
RIVER_META_URL = 'https://bipadportal.gov.np/api/v1/river-stations/?limit=2000'
RIVER_URLS = [
    ('river-trimed', 'https://bipadportal.gov.np/api/v1/river-trimed/?limit=2000'),
    ('river-newest', 'https://bipadportal.gov.np/api/v1/river/?limit=2000&ordering=-waterLevelOn'),
    ('river', 'https://bipadportal.gov.np/api/v1/river/?limit=2000'),
]


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ('results', 'data', 'objects', 'features'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict) and isinstance(value.get('results'), list):
                return value['results']
    raise ValueError('JSON response does not contain a list')


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': UA,
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache',
        },
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f'HTTP {response.status}')
        return json.loads(response.read().decode('utf-8-sig'))


def load_old():
    try:
        return json.loads(OUT.read_text(encoding='utf-8'))
    except Exception:
        return {'sources': {}, 'alerts': [], 'rivers': [], 'roads': []}


def first(obj, keys):
    if not isinstance(obj, dict):
        return None
    for key in keys:
        value = obj.get(key)
        if value not in (None, ''):
            return value
    return None


def flatten(row):
    if not isinstance(row, dict):
        return row
    out = dict(row)
    fields = row.get('fields')
    if isinstance(fields, dict):
        out = {**fields, **out}
    return out


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        return None


def stamp(row):
    return first(row, (
        'waterLevelOn', 'water_level_on', 'measuredOn', 'measured_on',
        'updatedOn', 'updated_on', 'modifiedOn', 'modified_on',
        'updated_at', 'updatedAt', 'createdOn', 'created_on', 'date', 'timestamp',
    ))


def measured(row):
    return first(row, (
        'waterLevel', 'water_level', 'currentWaterLevel', 'current_water_level',
        'currentLevel', 'current_level', 'level', 'status', 'status_name',
    )) is not None


def coords(row):
    point = row.get('point') if isinstance(row, dict) else None
    if isinstance(point, dict):
        c = point.get('coordinates')
        if isinstance(c, list) and len(c) >= 2:
            return c
    return None


def station_key(row):
    sid = first(row, ('stationSeriesId', 'station_series_id', 'stationId', 'station_id'))
    if sid is not None:
        return f'id:{sid}'
    title = str(first(row, ('title', 'river_name', 'riverName', 'station_name', 'stationName', 'name')) or '').lower().strip()
    c = coords(row)
    if title:
        return 'name:' + ' '.join(title.split())
    if c:
        return f'xy:{c[0]}|{c[1]}'
    return 'row:' + str(row.get('id', 'unknown'))


def newer(a, b):
    ta, tb = parse_dt(stamp(a)), parse_dt(stamp(b))
    if tb and (not ta or tb > ta):
        return b
    if ta and (not tb or ta > tb):
        return a
    if measured(b) and not measured(a):
        return b
    return a


def merge_latest(groups):
    out = {}
    for group in groups:
        for raw in group:
            row = flatten(raw)
            if not isinstance(row, dict):
                continue
            key = station_key(row)
            out[key] = newer(out[key], row) if key in out else row
    return list(out.values())


def extract_alert_rivers(alerts):
    out = []
    for alert in alerts:
        if not isinstance(alert, dict) or alert.get('referenceType') != 'river':
            continue
        raw = alert.get('referenceData')
        try:
            ref = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            ref = None
        if not isinstance(ref, dict):
            continue
        fields = ref.get('fields') if isinstance(ref.get('fields'), dict) else ref
        row = dict(fields)
        if alert.get('point') and not row.get('point'):
            row['point'] = alert['point']
        row['_alert_created_on'] = alert.get('createdOn')
        out.append(row)
    return out


def attach_meta(readings, meta):
    by_id, by_name = {}, {}
    for raw in meta:
        row = flatten(raw)
        sid = first(row, ('stationSeriesId', 'station_series_id', 'stationId', 'station_id', 'id'))
        if sid is not None:
            by_id[str(sid)] = row
        title = str(first(row, ('title', 'river_name', 'riverName', 'station_name', 'stationName', 'name')) or '').lower().strip()
        if title:
            by_name[' '.join(title.split())] = row
    joined = []
    for row in readings:
        sid = first(row, ('stationSeriesId', 'station_series_id', 'stationId', 'station_id'))
        title = str(first(row, ('title', 'river_name', 'riverName', 'station_name', 'stationName', 'name')) or '').lower().strip()
        m = by_id.get(str(sid)) if sid is not None else None
        if m is None and title:
            m = by_name.get(' '.join(title.split()))
        joined.append({**m, **row} if isinstance(m, dict) else row)
    return joined


def river_sync(alerts, old):
    groups = []
    sources = {}
    for label, url in RIVER_URLS:
        try:
            items = rows(fetch_json(url))
            groups.append(items)
            sources[label] = {'ok': True, 'count': len(items), 'endpoint': url, 'error': None}
            print(f'{label}: OK ({len(items)} rows)')
        except Exception as exc:
            sources[label] = {'ok': False, 'count': 0, 'endpoint': url, 'error': f'{type(exc).__name__}: {exc}'}
            print(f'{label}: FAILED ({exc})', file=sys.stderr)
    alert_rows = extract_alert_rivers(alerts)
    if alert_rows:
        groups.append(alert_rows)
        sources['alert-rivers'] = {'ok': True, 'count': len(alert_rows), 'endpoint': ALERTS_URL, 'error': None}
    try:
        meta = rows(fetch_json(RIVER_META_URL))
        sources['river-stations'] = {'ok': True, 'count': len(meta), 'endpoint': RIVER_META_URL, 'error': None}
    except Exception as exc:
        meta = []
        sources['river-stations'] = {'ok': False, 'count': 0, 'endpoint': RIVER_META_URL, 'error': f'{type(exc).__name__}: {exc}'}
    merged = merge_latest(groups)
    merged = attach_meta(merged, meta)
    if not merged:
        merged = old.get('rivers', []) if isinstance(old.get('rivers'), list) else []
    newest_time = None
    measured_count = 0
    for row in merged:
        if measured(row):
            measured_count += 1
        t = parse_dt(stamp(row))
        if t and (newest_time is None or t > newest_time):
            newest_time = t
    return merged, sources, measured_count, newest_time


def main():
    old = load_old()
    stamp_now = now_iso()
    result = {
        'schema_version': 2,
        'generated_at': stamp_now,
        'sources': {},
        'alerts': old.get('alerts', []),
        'rivers': old.get('rivers', []),
        'roads': old.get('roads', []),
    }

    try:
        result['alerts'] = rows(fetch_json(ALERTS_URL))
        result['sources']['alerts'] = {'ok': True, 'updated_at': stamp_now, 'count': len(result['alerts']), 'endpoint': ALERTS_URL, 'error': None}
        print(f"alerts: OK ({len(result['alerts'])} rows)")
    except Exception as exc:
        print(f'alerts: FAILED ({exc})', file=sys.stderr)
        result['sources']['alerts'] = {'ok': False, 'updated_at': old.get('sources', {}).get('alerts', {}).get('updated_at'), 'count': len(result['alerts']), 'endpoint': ALERTS_URL, 'error': f'{type(exc).__name__}: {exc}'}

    rivers, river_sources, measured_count, newest_time = river_sync(result['alerts'], old)
    result['rivers'] = rivers
    result['sources']['rivers'] = {
        'ok': bool(rivers),
        'updated_at': stamp_now,
        'count': len(rivers),
        'measured_count': measured_count,
        'newest_measurement': newest_time.isoformat() if newest_time else None,
        'endpoint': 'multi-source DHM/BIPAD river-trimed + river + alerts',
        'error': None if rivers else 'No river rows available',
        'feeds': river_sources,
    }

    try:
        result['roads'] = rows(fetch_json(ROADS_URL))
        result['sources']['roads'] = {'ok': True, 'updated_at': stamp_now, 'count': len(result['roads']), 'endpoint': ROADS_URL, 'error': None}
        print(f"roads: OK ({len(result['roads'])} rows)")
    except Exception as exc:
        print(f'roads: FAILED ({exc})', file=sys.stderr)
        result['sources']['roads'] = {'ok': False, 'updated_at': old.get('sources', {}).get('roads', {}).get('updated_at'), 'count': len(result['roads']), 'endpoint': ROADS_URL, 'error': f'{type(exc).__name__}: {exc}'}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(OUT)
    print(f"rivers: merged {len(rivers)} stations/readings; measured {measured_count}; newest {newest_time}")
    print(f'Wrote {OUT}')
    return 0 if result['sources']['rivers']['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
