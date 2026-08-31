#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

PATH = Path('data/floodsafe-core.json')
MAX_AGE = timedelta(minutes=5)
FUTURE = timedelta(minutes=5)
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
    try:
        wl = float(level(row))
    except Exception:
        wl = None
    warning = threshold(row, ('warningLevel','warning_level','warningThreshold','warning_threshold'))
    danger = threshold(row, ('dangerLevel','danger_level','dangerThreshold','danger_threshold'))
    raw = str(first(row, ('status','status_name','alertStatus','alert_status','riskLevel','risk_level')) or '').upper()
    if wl is not None and danger is not None and danger > 0 and wl >= danger:
        return 'DANGER'
    if wl is not None and warning is not None and warning > 0 and wl >= warning:
        return 'WARNING'
    if ('ABOVE DANGER' in raw or 'DANGER LEVEL' in raw or raw == 'RED') and 'BELOW DANGER' not in raw:
        return 'DANGER'
    if ('ABOVE WARNING' in raw or 'WARNING LEVEL' in raw or raw == 'ORANGE') and 'BELOW WARNING' not in raw:
        return 'WARNING'
    if any(x in raw for x in ('WATCH','RISING','INCREASING','YELLOW')):
        return 'WATCH'
    if raw or wl is not None:
        return 'NORMAL'
    return 'UNKNOWN'


def main():
    data = json.loads(PATH.read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc)
    current = 0
    rejected_fake = 0
    trusted = 0
    newest = None

    for row in data.get('rivers', []):
        if not isinstance(row, dict):
            continue
        if row.get('_timeBasis') == 'official-live-page-retrieval':
            for k in MEASURE_KEYS:
                row.pop(k, None)
            row['_measurementTimeTrusted'] = False
            row['_current5m'] = False
            row['_current20m'] = False  # backwards-compatible fail-closed flag
            row['_officialStatus'] = 'UNKNOWN'
            rejected_fake += 1
            continue

        raw_time = measurement_time(row)
        dt = parse_dt(raw_time)
        ok = False
        if dt:
            age = now - dt.astimezone(timezone.utc)
            ok = -FUTURE <= age <= MAX_AGE
            trusted += 1
            if newest is None or dt.astimezone(timezone.utc) > newest:
                newest = dt.astimezone(timezone.utc)
        row['_measurementTimeTrusted'] = bool(dt)
        row['_measurementTime'] = dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z') if dt else None
        row['_current5m'] = bool(ok and level(row) is not None)
        # Older clients must never re-expand the window to 20 minutes.
        row['_current20m'] = row['_current5m']
        row['_officialStatus'] = classify(row) if row['_current5m'] else 'STALE'
        if row['_current5m']:
            current += 1

    src = data.setdefault('sources', {}).setdefault('rivers', {})
    src['freshness_policy_minutes'] = 5
    src['current_5m_count'] = current
    src['current_20m_count'] = current  # deprecated compatibility metric
    src['trusted_measurement_timestamp_count'] = trusted
    src['rejected_fetch_time_as_measurement_count'] = rejected_fake
    src['newest_trusted_measurement'] = newest.isoformat().replace('+00:00','Z') if newest else None
    src['measurement_time_policy'] = 'Only official hydrological observation timestamps count; retrieved/modified/alert timestamps never make a reading current. Current means observation age <=5 minutes.'
    src['has_current_measurements'] = current > 0
    src['mirror_health'] = 'current' if current > 0 else 'degraded_no_current_measurements'
    src['sanitized_at'] = now.isoformat().replace('+00:00','Z')

    tmp = PATH.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(PATH)
    print(f'sanitized rivers: current<=5m={current}, trusted timestamps={trusted}, rejected fake freshness={rejected_fake}, newest={newest}, health={src["mirror_health"]}')


if __name__ == '__main__':
    main()
