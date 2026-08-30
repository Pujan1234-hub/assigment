#!/usr/bin/env python3
import json
import re
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path

OUT = Path('data/floodsafe-core.json')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36 FloodSafe-Nepal/1.0'
ALERTS_URL = 'https://bipadportal.gov.np/api/v1/alert/?limit=300&ordering=-createdOn'
ROADS_URL = 'https://bipadportal.gov.np/api/v1/highway/?limit=500'
RIVER_META_URL = 'https://bipadportal.gov.np/api/v1/river-stations/?limit=2000'
RIVER_URLS = [
    ('river-newest', 'https://bipadportal.gov.np/api/v1/river/?limit=2000&ordering=-waterLevelOn'),
    ('river-trimed', 'https://bipadportal.gov.np/api/v1/river-trimed/?limit=2000'),
    ('river', 'https://bipadportal.gov.np/api/v1/river/?limit=2000'),
]
DHM_PAGE_URLS = [
    ('dhm-realtime-stream', 'https://www.dhm.gov.np/hydrology/realtime-stream'),
    ('dhm-flood-monitoring', 'https://www.dhm.gov.np/bhasa/hydrology_floodMonitoring/np'),
    ('dhm-river-watch', 'https://www.dhm.gov.np/hydrology/river-watch'),
]
DHM_HOME_URLS = [
    'https://www.dhm.gov.np/',
    'https://www.dhm.gov.np/?locale=en',
    'https://www.dhm.gov.np/index.php?p=hydro',
]
NPT = timezone(timedelta(hours=5, minutes=45))
LIVE_WINDOW = timedelta(minutes=60)


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
    return urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': accept,
        'Cache-Control': 'no-cache, no-store, max-age=0',
        'Pragma': 'no-cache',
    })


def fetch_json(url):
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(request(url, 'application/json, text/plain, */*'), timeout=30, context=ctx) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f'HTTP {response.status}')
        return json.loads(response.read().decode('utf-8-sig'))


def fetch_text(url):
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(request(url, 'text/html,application/xhtml+xml,*/*;q=0.8'), timeout=30, context=ctx) as response:
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
            self.row.append(' '.join(' '.join(self.cell).split()))
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


def html_text(html):
    p = TableParser()
    p.feed(html)
    return p, ' '.join(p.all_text)


def to_float(value):
    if value in (None, '', '-', '—', 'NA', 'N/A'):
        return None
    m = re.search(r'-?\d+(?:\.\d+)?', str(value).replace(',', ''))
    return float(m.group(0)) if m else None


def parse_dt(value):
    if not value:
        return None
    try:
        d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=NPT)
    except Exception:
        return None


def parse_dhm_updated(text):
    compact = ' '.join(text.split())
    patterns = [
        r'Last\s+updated\s+on\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{4})\s+(\d{1,2}):(\d{2})(?:\s*([AP]M))?',
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})\s+(\d{1,2}):(\d{2})',
    ]
    m = re.search(patterns[0], compact, re.I)
    if m:
        month_name, day, year, hour, minute, ap = m.groups()
        months = {name.lower(): i for i, name in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'), 1)}
        mon = months.get(month_name[:3].lower())
        if mon:
            h = int(hour)
            if ap:
                if ap.upper() == 'PM' and h < 12: h += 12
                if ap.upper() == 'AM' and h == 12: h = 0
            return datetime(int(year), mon, int(day), h, int(minute), tzinfo=NPT)
    m = re.search(patterns[1], compact, re.I)
    if m:
        y, mo, d, h, mi = map(int, m.groups())
        try:
            return datetime(y, mo, d, h, mi, tzinfo=NPT)
        except Exception:
            pass
    return None


def make_live_row(name, level, source_url, retrieved, basin='', station_index='', district='', warning=None, danger=None, discharge=None):
    row = {
        'title': name.strip(),
        'waterLevel': float(level),
        'waterLevelOn': retrieved.isoformat(),
        'retrievedAt': retrieved.isoformat(),
        'dataSource': 'dhm.gov.np',
        '_officialLive': True,
        '_timeBasis': 'official-live-page-retrieval',
        '_officialLivePage': source_url,
    }
    if basin: row['basin'] = basin.strip()
    if station_index: row['stationIndex'] = station_index.strip()
    if district: row['districtName'] = district.strip()
    if warning is not None: row['warningLevel'] = warning
    if danger is not None: row['dangerLevel'] = danger
    if discharge is not None: row['discharge'] = discharge
    return row


def parse_dhm_tables(html, source_url):
    parser, text = html_text(html)
    observed = parse_dhm_updated(text)
    retrieved = observed or datetime.now(NPT).replace(microsecond=0)
    out = []
    for cells in parser.rows:
        cells = [str(x).strip() for x in cells if str(x).strip()]
        if len(cells) < 2:
            continue
        low = ' | '.join(cells).lower()
        if any(h in low for h in ('station name', 'station |', 'water lvl', 'water level')) and not any(char.isdigit() for char in low):
            continue
        if len(cells) >= 7 and to_float(cells[5]) is not None:
            _, basin, station_index, station_name, district, wl, discharge = cells[:7]
            if len(station_name) >= 3:
                out.append(make_live_row(station_name, to_float(wl), source_url, retrieved, basin, station_index, district, discharge=to_float(discharge)))
                continue
        for i in range(len(cells)-1):
            wl = to_float(cells[i+1])
            station = cells[i]
            if wl is None or len(station) < 3 or re.fullmatch(r'[\d.]+', station):
                continue
            if any(x in station.lower() for x in ('station', 'water', 'level', 'status', 'basin')):
                continue
            out.append(make_live_row(station, wl, source_url, retrieved))
            break
    dedup = {}
    for row in out:
        k = re.sub(r'[^a-z0-9]+', ' ', row['title'].lower()).strip()
        if k:
            dedup[k] = row
    return list(dedup.values()), retrieved


def parse_dhm_home(html, source_url):
    _, text = html_text(html)
    retrieved = datetime.now(NPT).replace(microsecond=0)
    pattern = re.compile(
        r'([A-Za-z][A-Za-z0-9() .\-/]+?\s+at\s+[A-Za-z][A-Za-z0-9() .\-/]+?)\s+WL:\s*(-?\d+(?:\.\d+)?)\s*m\s+WR:\s*(-?\d+(?:\.\d+)?)\s*m\s+DL:\s*(-?\d+(?:\.\d+)?)\s*m',
        re.I,
    )
    out = []
    for m in pattern.finditer(' '.join(text.split())):
        name, wl, wr, dl = m.groups()
        name = ' '.join(name.split())
        known = re.search(r'(Narayani\s+at\s+Devghat|Karnali\s+at\s+Chisapani|Kankai\s+River\s+at\s+Mainachuli|Babai\s+at\s+Chepang|Mahakali\s+at\s+Parigaon)$', name, re.I)
        if known:
            name = known.group(1)
        elif len(name) > 80:
            continue
        out.append(make_live_row(name, float(wl), source_url, retrieved, warning=float(wr), danger=float(dl)))
    return out, retrieved


def fetch_dhm_live_sources():
    feeds = {}
    rows_out = []
    targets = [(label, url, 'table') for label, url in DHM_PAGE_URLS] + [(f'dhm-home-{i+1}', url, 'home') for i, url in enumerate(DHM_HOME_URLS)]
    with ThreadPoolExecutor(max_workers=len(targets)) as ex:
        futs = {ex.submit(fetch_text, url):(label,url,kind) for label,url,kind in targets}
        for fut in as_completed(futs):
            label, url, kind = futs[fut]
            try:
                html = fut.result()
                parsed, updated = parse_dhm_tables(html, url) if kind == 'table' else parse_dhm_home(html, url)
                if not parsed:
                    raise ValueError('no current water-level rows parsed')
                rows_out.extend(parsed)
                feeds[label] = {'ok': True, 'count': len(parsed), 'updated_at': updated.isoformat(), 'endpoint': url, 'error': None}
                print(f'{label}: OK ({len(parsed)} live rows)')
            except Exception as exc:
                feeds[label] = {'ok': False, 'count': 0, 'endpoint': url, 'error': f'{type(exc).__name__}: {exc}'}
                print(f'{label}: FAILED ({exc})', file=sys.stderr)
    return rows_out, feeds


def load_old():
    try:
        return json.loads(OUT.read_text(encoding='utf-8'))
    except Exception:
        return {'sources': {}, 'alerts': [], 'rivers': [], 'roads': []}


def first(obj, keys):
    if not isinstance(obj, dict): return None
    for key in keys:
        value = obj.get(key)
        if value not in (None, ''): return value
    return None


def flatten(row):
    if not isinstance(row, dict): return row
    out = dict(row)
    fields = row.get('fields')
    if isinstance(fields, dict): out = {**fields, **out}
    return out


def stamp(row):
    return first(row, ('waterLevelOn','water_level_on','measuredOn','measured_on','updatedOn','updated_on','modifiedOn','modified_on','updated_at','updatedAt','createdOn','created_on','date','timestamp','retrievedAt'))


def measured(row):
    return first(row, ('waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','status','status_name')) is not None


def coords(row):
    point = row.get('point') if isinstance(row, dict) else None
    if isinstance(point, dict):
        c = point.get('coordinates')
        if isinstance(c, list) and len(c) >= 2: return c
    return None


def normalize_title(value):
    text = str(value or '').lower().strip()
    text = re.sub(r'\s+(?:at|near)\s+.*$', '', text)
    text = re.sub(r'\b(river|khola|nadi|stream|station|gauge|bridge|rls|hs)\b', ' ', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return ' '.join(text.split())


def station_key(row):
    sid = first(row, ('stationSeriesId','station_series_id','stationId','station_id'))
    if sid is not None: return f'id:{sid}'
    title = str(first(row, ('title','river_name','riverName','station_name','stationName','name')) or '').lower().strip()
    c = coords(row)
    if title: return 'name:' + ' '.join(title.split())
    if c: return f'xy:{c[0]}|{c[1]}'
    return 'row:' + str(row.get('id', 'unknown'))


def source_priority(row):
    if row.get('_officialLive'): return 3
    ds = str(row.get('dataSource') or row.get('data_source') or '').lower()
    if 'hydrology.gov.np' in ds or 'dhm' in ds: return 2
    return 1


def newer(a, b):
    ta, tb = parse_dt(stamp(a)), parse_dt(stamp(b))
    if tb and (not ta or tb > ta): return b
    if ta and (not tb or ta > tb): return a
    pa, pb = source_priority(a), source_priority(b)
    if pb > pa: return b
    if pa > pb: return a
    if measured(b) and not measured(a): return b
    return a


def merge_latest(groups):
    out = {}
    for group in groups:
        for raw in group:
            row = flatten(raw)
            if not isinstance(row, dict): continue
            key = station_key(row)
            out[key] = newer(out[key], row) if key in out else row
    return list(out.values())


def extract_alert_rivers(alerts):
    out = []
    for alert in alerts:
        if not isinstance(alert, dict) or alert.get('referenceType') != 'river': continue
        raw = alert.get('referenceData')
        try: ref = json.loads(raw) if isinstance(raw, str) else raw
        except Exception: ref = None
        if not isinstance(ref, dict): continue
        fields = ref.get('fields') if isinstance(ref.get('fields'), dict) else ref
        row = dict(fields)
        if alert.get('point') and not row.get('point'): row['point'] = alert['point']
        row['_alert_created_on'] = alert.get('createdOn')
        out.append(row)
    return out


def attach_meta(readings, meta):
    by_id, by_name, by_base = {}, {}, {}
    for raw in meta:
        row = flatten(raw)
        sid = first(row, ('stationSeriesId','station_series_id','stationId','station_id','id'))
        if sid is not None: by_id[str(sid)] = row
        title = str(first(row, ('title','river_name','riverName','station_name','stationName','name')) or '').lower().strip()
        if title:
            by_name[' '.join(title.split())] = row
            base = normalize_title(title)
            if base: by_base.setdefault(base, []).append(row)
    joined = []
    for row in readings:
        sid = first(row, ('stationSeriesId','station_series_id','stationId','station_id'))
        title = str(first(row, ('title','river_name','riverName','station_name','stationName','name')) or '').lower().strip()
        m = by_id.get(str(sid)) if sid is not None else None
        if m is None and title:
            m = by_name.get(' '.join(title.split()))
            if m is None:
                base = normalize_title(title)
                hits = by_base.get(base, []) if base else []
                if len(hits) == 1: m = hits[0]
        joined.append({**m, **row} if isinstance(m, dict) else row)
    return joined


def fetch_bipad_bundle():
    tasks = [('alerts', ALERTS_URL), ('roads', ROADS_URL), ('river-stations', RIVER_META_URL)] + RIVER_URLS
    result = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
        futs = {ex.submit(fetch_json, url):(label,url) for label,url in tasks}
        for fut in as_completed(futs):
            label, url = futs[fut]
            try:
                items = rows(fut.result())
                result[label] = (items, {'ok': True, 'count': len(items), 'endpoint': url, 'error': None})
                print(f'{label}: OK ({len(items)} rows)')
            except Exception as exc:
                result[label] = ([], {'ok': False, 'count': 0, 'endpoint': url, 'error': f'{type(exc).__name__}: {exc}'})
                print(f'{label}: FAILED ({exc})', file=sys.stderr)
    return result


def main():
    old = load_old()
    stamp_now = now_iso()
    result = {'schema_version': 4, 'generated_at': stamp_now, 'sources': {}, 'alerts': old.get('alerts', []), 'rivers': old.get('rivers', []), 'roads': old.get('roads', [])}

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_dhm = ex.submit(fetch_dhm_live_sources)
        f_bipad = ex.submit(fetch_bipad_bundle)
        dhm_rows, dhm_feeds = f_dhm.result()
        bipad = f_bipad.result()

    alerts, alerts_meta = bipad.get('alerts', ([], {}))
    roads, roads_meta = bipad.get('roads', ([], {}))
    meta, meta_meta = bipad.get('river-stations', ([], {}))
    if alerts: result['alerts'] = alerts
    if roads: result['roads'] = roads
    result['sources']['alerts'] = {**alerts_meta, 'updated_at': stamp_now}
    result['sources']['roads'] = {**roads_meta, 'updated_at': stamp_now}

    groups = []
    if dhm_rows: groups.append(dhm_rows)
    river_feeds = dict(dhm_feeds)
    for label, _ in RIVER_URLS:
        items, smeta = bipad.get(label, ([], {}))
        if items: groups.append(items)
        river_feeds[label] = smeta
    river_feeds['river-stations'] = meta_meta
    alert_rows = extract_alert_rivers(result['alerts'])
    if alert_rows:
        groups.append(alert_rows)
        river_feeds['alert-rivers'] = {'ok': True, 'count': len(alert_rows), 'endpoint': ALERTS_URL, 'error': None}

    merged = merge_latest(groups)
    merged = attach_meta(merged, meta)
    merged = merge_latest([merged])
    if not merged: merged = old.get('rivers', []) if isinstance(old.get('rivers'), list) else []

    now = datetime.now(timezone.utc)
    newest_time = None
    measured_count = 0
    live_count = 0
    dhm_live_count = 0
    for row in merged:
        if measured(row): measured_count += 1
        t = parse_dt(stamp(row))
        if t:
            tu = t.astimezone(timezone.utc)
            if newest_time is None or tu > newest_time: newest_time = tu
            if -timedelta(minutes=5) <= now - tu <= LIVE_WINDOW: live_count += 1
        if row.get('_officialLive'): dhm_live_count += 1

    result['rivers'] = merged
    result['sources']['rivers'] = {
        'ok': bool(merged),
        'updated_at': stamp_now,
        'count': len(merged),
        'measured_count': measured_count,
        'live_60m_count': live_count,
        'dhm_live_page_count': dhm_live_count,
        'newest_measurement': newest_time.isoformat() if newest_time else None,
        'freshness_policy_minutes': 60,
        'endpoint': 'DHM official live pages + BIPAD realtime river feeds + DHM alerts',
        'error': None if merged else 'No river rows available',
        'feeds': river_feeds,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(OUT)
    print(f"rivers: merged {len(merged)}; live<=60m {live_count}; DHM live-page {dhm_live_count}; newest {newest_time}")
    print(f'Wrote {OUT}')
    return 0 if result['sources']['rivers']['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
