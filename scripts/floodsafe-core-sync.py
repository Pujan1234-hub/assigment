#!/usr/bin/env python3
import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path

OUT = Path('data/floodsafe-core.json')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36 FloodSafe-Nepal/1.0'
ALERTS_URL = 'https://bipadportal.gov.np/api/v1/alert/?limit=300&ordering=-createdOn'
ROADS_URL = 'https://bipadportal.gov.np/api/v1/highway/?limit=500'
RIVER_META_URL = 'https://bipadportal.gov.np/api/v1/river-stations/?limit=2000'
DHM_REALTIME_URL = 'https://dhm.gov.np/hydrology/realtime-stream'
RIVER_URLS = [
    ('river-trimed', 'https://bipadportal.gov.np/api/v1/river-trimed/?limit=2000'),
    ('river-newest', 'https://bipadportal.gov.np/api/v1/river/?limit=2000&ordering=-waterLevelOn'),
    ('river', 'https://bipadportal.gov.np/api/v1/river/?limit=2000'),
]
NPT = timezone(timedelta(hours=5, minutes=45))


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


def request(url, accept):
    return urllib.request.Request(
        url,
        headers={
            'User-Agent': UA,
            'Accept': accept,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        },
    )


def fetch_json(url):
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(request(url, 'application/json, text/plain, */*'), timeout=35, context=ctx) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f'HTTP {response.status}')
        return json.loads(response.read().decode('utf-8-sig'))


def fetch_text(url):
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(request(url, 'text/html,application/xhtml+xml,*/*;q=0.8'), timeout=35, context=ctx) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f'HTTP {response.status}')
        return response.read().decode('utf-8', errors='replace')


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_cell = False
        self.in_row = False
        self.cell = []
        self.row = []
        self.rows = []
        self.all_text = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'tr':
            self.in_row = True
            self.row = []
        elif tag in ('td', 'th') and self.in_row:
            self.in_cell = True
            self.cell = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ('td', 'th') and self.in_cell:
            text = ' '.join(' '.join(self.cell).split())
            self.row.append(text)
            self.in_cell = False
            self.cell = []
        elif tag == 'tr' and self.in_row:
            if self.row:
                self.rows.append(self.row)
            self.in_row = False
            self.row = []

    def handle_data(self, data):
        text = str(data or '').strip()
        if text:
            self.all_text.append(text)
            if self.in_cell:
                self.cell.append(text)


def parse_dhm_updated(text):
    compact = ' '.join(text.split())
    m = re.search(
        r'Last\s+updated\s+on\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+'
        r'([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{4})\s+(\d{1,2}):(\d{2})(?:\s*([AP]M))?',
        compact,
        re.I,
    )
    if not m:
        return None
    month_name, day, year, hour, minute, ap = m.groups()
    months = {name.lower(): i for i, name in enumerate(
        ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'), 1
    )}
    mon = months.get(month_name[:3].lower())
    if not mon:
        return None
    h = int(hour)
    if ap and h <= 12:
        if ap.upper() == 'PM' and h < 12:
            h += 12
        elif ap.upper() == 'AM' and h == 12:
            h = 0
    if h > 23:
        return None
    return datetime(int(year), mon, int(day), h, int(minute), tzinfo=NPT)


def to_float(value):
    if value in (None, '', '-', '—', 'NA', 'N/A'):
        return None
    m = re.search(r'-?\d+(?:\.\d+)?', str(value).replace(',', ''))
    return float(m.group(0)) if m else None


def fetch_dhm_realtime():
    html = fetch_text(DHM_REALTIME_URL)
    parser = TableParser()
    parser.feed(html)
    updated = parse_dhm_updated(' '.join(parser.all_text))
    if updated is None:
        raise ValueError('DHM realtime page did not expose Last updated time')
    live = []
    for row in parser.rows:
        cells = [str(x).strip() for x in row]
        if len(cells) < 6:
            continue
        low = ' | '.join(cells).lower()
        if 'station name' in low or 'water level' in low and 'basin name' in low:
            continue
        # Official table: S.No | Basin | Station Index | Station Name | District | Water Level | Discharge
        if len(cells) >= 7:
            _, basin_name, station_index, station_name, district_name, level_text, discharge_text = cells[:7]
        else:
            basin_name, station_index, station_name, district_name, level_text, discharge_text = cells[:6]
        wl = to_float(level_text)
        if not station_name or wl is None:
            continue
        live.append({
            'title': station_name,
            'basin': basin_name,
            'stationIndex': station_index,
            'districtName': district_name,
            'waterLevel': wl,
            'discharge': to_float(discharge_text),
            'waterLevelOn': updated.isoformat(),
            'dataSource': 'dhm.gov.np',
            '_officialLive': True,
            '_officialLivePage': DHM_REALTIME_URL,
        })
    if len(live) < 100:
        raise ValueError(f'DHM realtime table too small: {len(live)} rows')
    return live, updated


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


def normalize_title(value):
    text = str(value or '').lower().strip()
    text = re.sub(r'\s+(?:at|near)\s+.*$', '', text)
    text = re.sub(r'\b(river|khola|nadi|stream|station|gauge|bridge|rls|hs)\b', ' ', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return ' '.join(text.split())


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
    by_id, by_name, by_base = {}, {}, {}
    for raw in meta:
        row = flatten(raw)
        sid = first(row, ('stationSeriesId', 'station_series_id', 'stationId', 'station_id', 'id'))
        if sid is not None:
            by_id[str(sid)] = row
        title = str(first(row, ('title', 'river_name', 'riverName', 'station_name', 'stationName', 'name')) or '').lower().strip()
        if title:
            key = ' '.join(title.split())
            by_name[key] = row
            base = normalize_title(title)
            if base:
                by_base.setdefault(base, []).append(row)
    joined = []
    for row in readings:
        sid = first(row, ('stationSeriesId', 'station_series_id', 'stationId', 'station_id'))
        title = str(first(row, ('title', 'river_name', 'riverName', 'station_name', 'stationName', 'name')) or '').lower().strip()
        m = by_id.get(str(sid)) if sid is not None else None
        if m is None and title:
            key = ' '.join(title.split())
            m = by_name.get(key)
            if m is None:
                base = normalize_title(title)
                hits = by_base.get(base, []) if base else []
                if len(hits) == 1:
                    m = hits[0]
        joined.append({**m, **row} if isinstance(m, dict) else row)
    return joined


def river_sync(alerts, old):
    groups = []
    sources = {}
    try:
        dhm_live, dhm_updated = fetch_dhm_realtime()
        groups.append(dhm_live)
        sources['dhm-realtime-stream'] = {
            'ok': True,
            'count': len(dhm_live),
            'updated_at': dhm_updated.isoformat(),
            'endpoint': DHM_REALTIME_URL,
            'error': None,
        }
        print(f'DHM realtime-stream: OK ({len(dhm_live)} rows), updated {dhm_updated.isoformat()}')
    except Exception as exc:
        sources['dhm-realtime-stream'] = {
            'ok': False,
            'count': 0,
            'endpoint': DHM_REALTIME_URL,
            'error': f'{type(exc).__name__}: {exc}',
        }
        print(f'DHM realtime-stream: FAILED ({exc})', file=sys.stderr)
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
        'schema_version': 3,
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
        'endpoint': 'DHM realtime-stream + BIPAD river feeds + alerts',
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
