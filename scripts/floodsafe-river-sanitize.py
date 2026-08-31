#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

PATH = Path('data/floodsafe-core.json')
MEASURE_KEYS = ('waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime')


def parse_dt(v):
    if not v:
        return None
    try:
        d = datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def first(row, keys):
    for k in keys:
        v = row.get(k)
        if v not in (None, ''):
            return v
    return None


def measurement_time(row):
    return first(row, MEASURE_KEYS)


def level(row):
    return first(row, ('waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level'))


def threshold(row, keys):
    v = first(row, keys)
    try:
        return float(v) if v not in (None,'') else None
    except Exception:
        return None


def classify(row):
    raw = str(first(row, ('status','status_name','alertStatus','alert_status','riskLevel','risk_level')) or '').upper()
    if raw:
        if ('ABOVE DANGER' in raw or 'DANGER LEVEL' in raw or raw == 'RED') and 'BELOW DANGER' not in raw:
            return 'DANGER'
        if ('ABOVE WARNING' in raw or 'WARNING LEVEL' in raw or raw == 'ORANGE') and 'BELOW WARNING' not in raw:
            return 'WARNING'
        if any(x in raw for x in ('WATCH','RISING','INCREASING','YELLOW')):
            return 'WATCH'
    try:
        wl = float(level(row))
    except Exception:
        wl = None
    warning = threshold(row, ('warningLevel','warning_level','warningThreshold','warning_threshold'))
    danger = threshold(row, ('dangerLevel','danger_level','dangerThreshold','danger_threshold'))
    if wl is not None and danger is not None and danger > 0 and wl >= danger:
        return 'DANGER'
    if wl is not None and warning is not None and warning > 0 and wl >= warning:
        return 'WARNING'
    return 'NORMAL' if wl is not None or raw else 'UNKNOWN'


def main():
    data = json.loads(PATH.read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc)
    current = 0
    trusted = 0
    newest = None
    live_page_rows = 0

    for row in data.get('rivers', []):
        if not isinstance(row, dict):
            continue
        dt = parse_dt(measurement_time(row))
        if dt:
            trusted += 1
            u = dt.astimezone(timezone.utc)
            if newest is None or u > newest:
                newest = u
            row['_measurementTime'] = u.isoformat().replace('+00:00','Z')
            row['_measurementTimeTrusted'] = True
        else:
            row['_measurementTime'] = None
            row['_measurementTimeTrusted'] = False

        has_value = level(row) is not None
        row['_currentOfficial'] = bool(has_value)
        row['_current5m'] = bool(has_value)
        row['_current20m'] = bool(has_value)
        row['_officialStatus'] = classify(row) if has_value else 'UNKNOWN'
        if row.get('_timeBasis') == 'official-live-page-retrieval':
            live_page_rows += 1
        if has_value:
            current += 1

    src = data.setdefault('sources', {}).setdefault('rivers', {})
    src['current_official_count'] = current
    src['current_5m_count'] = current
    src['current_20m_count'] = current
    src['trusted_measurement_timestamp_count'] = trusted
    src['official_live_page_row_count'] = live_page_rows
    src['newest_trusted_measurement'] = newest.isoformat().replace('+00:00','Z') if newest else None
    src['freshness_policy'] = 'latest-official-value'
    src['measurement_time_policy'] = 'Show an official observation time only when the source supplies one. Never invent a station observation time from retrieval time.'
    src['has_current_measurements'] = current > 0
    src['mirror_health'] = 'current' if current > 0 else 'degraded_no_official_values'
    src['sanitized_at'] = now.isoformat().replace('+00:00','Z')

    tmp = PATH.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(PATH)
    print(f'sanitized rivers: latest-official={current}, trusted-times={trusted}, live-page={live_page_rows}, newest={newest}')


if __name__ == '__main__':
    main()
