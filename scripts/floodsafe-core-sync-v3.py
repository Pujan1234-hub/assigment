#!/usr/bin/env python3
"""FloodSafe river sync v3.

Use the value currently shown by official DHM/BIPAD live pages as the preferred
observation. A page retrieval timestamp is never presented as an official
hydrological observation time; it is only transport metadata.
"""
import importlib.util
import re
from pathlib import Path

V2 = Path(__file__).with_name('floodsafe-core-sync-v2.py')
spec = importlib.util.spec_from_file_location('floodsafe_core_sync_v2', V2)
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)
core = v2.core


def priority(row):
    if row.get('_officialLive'):
        # The live DHM page is the strongest source for the value currently
        # displayed by government, even when that page omits per-row time.
        return 100
    ds = str(row.get('dataSource') or row.get('data_source') or '').lower()
    if 'dhm' in ds or 'hydrology.gov.np' in ds:
        return 80
    if v2.measurement_stamp(row):
        return 60
    return 10


def station_key(row):
    sid = core.first(row, (
        'stationSeriesId','station_series_id','stationId','station_id',
        'stationIndex','station_index'
    ))
    if sid not in (None, ''):
        return 'id:' + str(sid).strip()
    title = str(core.first(row, (
        'title','river_name','riverName','station_name','stationName','name'
    )) or '').lower().strip()
    title = re.sub(r'\s+(?:at|near)\s+.*$', '', title)
    title = re.sub(r'\b(river|khola|nadi|stream|station|gauge|bridge|rls|hs)\b', ' ', title)
    title = ' '.join(re.sub(r'[^a-z0-9]+', ' ', title).split())
    c = core.coords(row)
    if title:
        return 'name:' + title
    if c:
        return f'xy:{c[0]}|{c[1]}'
    return 'row:' + str(row.get('id', 'unknown'))


def newer(a, b):
    pa, pb = priority(a), priority(b)
    if pb != pa:
        return b if pb > pa else a
    ta, tb = core.parse_dt(v2.measurement_stamp(a)), core.parse_dt(v2.measurement_stamp(b))
    if tb and (not ta or tb > ta):
        return b
    if ta and (not tb or ta > tb):
        return a
    ra = core.parse_dt(a.get('retrievedAt'))
    rb = core.parse_dt(b.get('retrievedAt'))
    if rb and (not ra or rb > ra):
        return b
    return a


core.source_priority = priority
core.station_key = station_key
core.newer = newer

if __name__ == '__main__':
    rc = core.main()
    v2.append_catalogue_to_snapshot()
    raise SystemExit(rc)
