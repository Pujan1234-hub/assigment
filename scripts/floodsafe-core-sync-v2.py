#!/usr/bin/env python3
"""FloodSafe river sync hardening wrapper.

Keeps the established multi-source collector but fixes one critical rule:
transport/retrieval timestamps must never outrank real hydrological
observation timestamps when river rows are merged.
"""
import importlib.util
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).with_name('floodsafe-core-sync.py')
spec = importlib.util.spec_from_file_location('floodsafe_core_sync_base', BASE)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

MEASURE_KEYS = (
    'waterLevelOn', 'water_level_on', 'measuredOn', 'measured_on',
    'measurementTime', 'observationTime'
)


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
        # Prefer an explicitly observed page row over a retrieval-only duplicate.
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
    # Retrieval-only rows may be retained as context but can never outrank a
    # row carrying a real observation timestamp.
    return 0


# Patch the established collector before main() executes.
core.stamp = measurement_stamp
core.source_priority = source_priority_v2
core.make_live_row = make_retrieval_row
core.parse_dhm_tables = parse_dhm_tables_v2

if __name__ == '__main__':
    raise SystemExit(core.main())
