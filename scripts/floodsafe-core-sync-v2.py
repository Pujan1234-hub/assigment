#!/usr/bin/env python3
"""FloodSafe river sync hardening wrapper.

Separates the official BIPAD station catalogue from hydrological observations,
keeps transport/retrieval timestamps from creating fake freshness, and emits a
complete station catalogue for the map while observations remain independently
freshness-gated.
"""
import importlib.util
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).with_name('floodsafe-core-sync.py')
spec = importlib.util.spec_from_file_location('floodsafe_core_sync_base', BASE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

MEASURE_KEYS = (
    'waterLevelOn', 'water_level_on', 'measuredOn', 'measured_on',
    'measurementTime', 'observationTime'
)
CAPTURED_STATION_META = []


def measurement_stamp(row):
    """Only hydrological observation timestamps participate in freshness merge."""
    return core.first(row, MEASURE_KEYS)


def make_retrieval_row(name, level, source_url, retrieved, basin='', station_index='',
                       district='', warning=None, danger=None, discharge=None):
    """A page-retrieved value without an explicit page observation time is not current."""
    row = {
        'title': name.strip(),
        'waterLevel': float(level),
        'retrievedAt': retrieved.isoformat(),
        'dataSource': 'dhm.gov.np',
        '_officialLive': True,
        '_timeBasis': 'official-live-page-retrieval',
        '_officialLivePage': source_url,
    }
    if basin:
        row['basin'] = basin.strip()
    if station_index:
        row['stationIndex'] = station_index.strip()
    if district:
        row['districtName'] = district.strip()
    if warning is not None:
        row['warningLevel'] = warning
    if danger is not None:
        row['dangerLevel'] = danger
    if discharge is not None:
        row['discharge'] = discharge
    return row


def make_observed_row(name, level, source_url, observed, retrieved, basin='',
                      station_index='', district='', warning=None, danger=None,
                      discharge=None):
    row = make_retrieval_row(
        name, level, source_url, retrieved, basin, station_index, district,
        warning, danger, discharge
    )
    row['waterLevelOn'] = observed.isoformat()
    row['_timeBasis'] = 'official-page-updated-at'
    row['_measurementTimeSource'] = 'DHM page Last updated timestamp'
    return row


def parse_dhm_tables_v2(html, source_url):
    parser, text = core.html_text(html)
    observed = core.parse_dhm_updated(text)
    retrieved = datetime.now(core.NPT).replace(microsecond=0)
    out = []

    for cells in parser.rows:
        cells = [str(x).strip() for x in cells if str(x).strip()]
        if len(cells) < 2:
            continue
        low = ' | '.join(cells).lower()
        if any(h in low for h in ('station name', 'station |', 'water lvl', 'water level')) and not any(ch.isdigit() for ch in low):
            continue

        def build(station_name, wl, basin='', station_index='', district='', discharge=None):
            maker = make_observed_row if observed else make_retrieval_row
            if observed:
                return maker(station_name, wl, source_url, observed, retrieved, basin,
                             station_index, district, discharge=discharge)
            return maker(station_name, wl, source_url, retrieved, basin,
                         station_index, district, discharge=discharge)

        if len(cells) >= 7 and core.to_float(cells[5]) is not None:
            _, basin, station_index, station_name, district, wl, discharge = cells[:7]
            if len(station_name) >= 3:
                out.append(build(
                    station_name, core.to_float(wl), basin, station_index, district,
                    core.to_float(discharge)
                ))
                continue

        for i in range(len(cells) - 1):
            wl = core.to_float(cells[i + 1])
            station = cells[i]
            if wl is None or len(station) < 3 or re.fullmatch(r'[\d.]+', station):
                continue
            if any(x in station.lower() for x in ('station', 'water', 'level', 'status', 'basin')):
                continue
            out.append(build(station, wl))
            break

    dedup = {}
    for row in out:
        key = re.sub(r'[^a-z0-9]+', ' ', row['title'].lower()).strip()
        if not key:
            continue
        prev = dedup.get(key)
        if prev is None or (row.get('waterLevelOn') and not prev.get('waterLevelOn')):
            dedup[key] = row
    return list(dedup.values()), observed or retrieved


def source_priority_v2(row):
    has_measurement_time = bool(measurement_stamp(row))
    if row.get('_officialLive') and row.get('_timeBasis') == 'official-page-updated-at' and has_measurement_time:
        return 5
    ds = str(row.get('dataSource') or row.get('data_source') or '').lower()
    if has_measurement_time and ('hydrology.gov.np' in ds or 'dhm' in ds):
        return 4
    if has_measurement_time:
        return 3
    return 0


def station_id(row):
    return core.first(row, (
        'stationSeriesId', 'station_series_id', 'stationId', 'station_id',
        'stationIndex', 'station_index', 'id'
    ))


def station_name(row):
    return str(core.first(row, (
        'title', 'river_name', 'riverName', 'station_name', 'stationName', 'name'
    )) or '').strip()


def point(row):
    if not isinstance(row, dict):
        return None
    for obj in (row.get('point'), row.get('location'), row.get('geometry')):
        if isinstance(obj, dict):
            c = obj.get('coordinates')
            if isinstance(c, list) and len(c) >= 2:
                try:
                    lon, lat = float(c[0]), float(c[1])
                    if 79.5 <= lon <= 89 and 26 <= lat <= 31:
                        return [lon, lat]
                except Exception:
                    pass
    lon = core.to_float(core.first(row, ('longitude','lon','lng','stationLongitude','station_longitude')))
    lat = core.to_float(core.first(row, ('latitude','lat','stationLatitude','station_latitude')))
    if lon is not None and lat is not None and 79.5 <= lon <= 89 and 26 <= lat <= 31:
        return [lon, lat]
    return None


def catalogue_key(row):
    sid = station_id(row)
    if sid not in (None, ''):
        return f'id:{sid}'
    n = re.sub(r'[^a-z0-9]+', ' ', station_name(row).lower()).strip()
    c = point(row)
    if n and c:
        return f'namexy:{n}:{c[0]:.5f}:{c[1]:.5f}'
    if n:
        return f'name:{n}'
    if c:
        return f'xy:{c[0]:.5f}:{c[1]:.5f}'
    return None


def station_catalogue(rows):
    out = {}
    for raw in rows or []:
        row = core.flatten(raw)
        if not isinstance(row, dict):
            continue
        key = catalogue_key(row)
        if not key:
            continue
        clean = dict(row)
        # Catalogue metadata never creates current river status. Remove fields
        # that could accidentally be interpreted as a fresh observation later.
        for k in ('_current20m','_current5m','_officialStatus','_measurementTime'):
            clean.pop(k, None)
        clean['_catalogueOnly'] = True
        clean['_catalogueSource'] = 'BIPAD river-stations / DHM station metadata'
        out[key] = {**out.get(key, {}), **clean}
    return list(out.values())


_original_fetch_bipad_bundle = core.fetch_bipad_bundle


def fetch_bipad_bundle_capture():
    result = _original_fetch_bipad_bundle()
    global CAPTURED_STATION_META
    CAPTURED_STATION_META = list(result.get('river-stations', ([], {}))[0] or [])
    return result


def append_catalogue_to_snapshot():
    path = core.OUT
    data = json.loads(path.read_text(encoding='utf-8'))
    catalog = station_catalogue(CAPTURED_STATION_META)
    # Do not erase a previously valid catalogue if the station metadata request
    # alone failed during this iteration.
    if not catalog:
        old = data.get('river_stations')
        if isinstance(old, list):
            catalog = old
    data['schema_version'] = max(int(data.get('schema_version') or 0), 5)
    data['river_stations'] = catalog
    src = data.setdefault('sources', {}).setdefault('rivers', {})
    src['station_catalog_count'] = len(catalog)
    src['station_catalog_with_coordinates'] = sum(1 for r in catalog if point(r))
    src['station_catalog_source'] = 'BIPAD /api/v1/river-stations/ (DHM station metadata)'
    src['observation_sources'] = 'BIPAD /river/ + /river-trimed/ + DHM official observation pages'
    src['freshness_policy_minutes'] = 5
    tmp = path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)
    print(f"station catalogue: {len(catalog)} official stations; {src['station_catalog_with_coordinates']} geolocated")


# Patch the established collector before main() executes.
core.stamp = measurement_stamp
core.source_priority = source_priority_v2
core.make_live_row = make_retrieval_row
core.parse_dhm_tables = parse_dhm_tables_v2
core.fetch_bipad_bundle = fetch_bipad_bundle_capture
core.LIVE_WINDOW = timedelta(minutes=5)

if __name__ == '__main__':
    rc = core.main()
    append_catalogue_to_snapshot()
    raise SystemExit(rc)
