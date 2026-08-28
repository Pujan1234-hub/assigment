#!/usr/bin/env python3
import json
import os
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('data/floodsafe-core.json')
ENDPOINTS = {
    'alerts': 'https://bipadportal.gov.np/api/v1/alert/?limit=200&ordering=-createdOn',
    'rivers': 'https://bipadportal.gov.np/api/v1/river/?limit=650',
    'roads': 'https://bipadportal.gov.np/api/v1/highway/?limit=500',
}
UA = 'FloodSafe-Nepal/1.0 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/)'


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
    with urllib.request.urlopen(req, timeout=25, context=ctx) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f'HTTP {response.status}')
        raw = response.read()
    return json.loads(raw.decode('utf-8-sig'))


def load_old():
    try:
        return json.loads(OUT.read_text(encoding='utf-8'))
    except Exception:
        return {'sources': {}, 'alerts': [], 'rivers': [], 'roads': []}


def main():
    old = load_old()
    stamp = now_iso()
    result = {
        'schema_version': 1,
        'generated_at': stamp,
        'sources': {},
        'alerts': old.get('alerts', []),
        'rivers': old.get('rivers', []),
        'roads': old.get('roads', []),
    }
    success = 0
    for name, url in ENDPOINTS.items():
        try:
            payload = fetch_json(url)
            items = rows(payload)
            result[name] = items
            result['sources'][name] = {
                'ok': True,
                'updated_at': stamp,
                'count': len(items),
                'endpoint': url,
                'error': None,
            }
            success += 1
            print(f'{name}: OK ({len(items)} rows)')
        except Exception as exc:
            previous = old.get('sources', {}).get(name, {})
            previous_items = old.get(name, []) if isinstance(old.get(name), list) else []
            result[name] = previous_items
            result['sources'][name] = {
                'ok': bool(previous.get('ok') and previous_items),
                'updated_at': previous.get('updated_at'),
                'count': len(previous_items),
                'endpoint': url,
                'error': f'{type(exc).__name__}: {exc}',
                'last_attempt_at': stamp,
            }
            print(f'{name}: FAILED ({exc})', file=sys.stderr)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(OUT)
    print(f'Wrote {OUT}; successful sources: {success}/{len(ENDPOINTS)}')
    return 0 if success else 2


if __name__ == '__main__':
    raise SystemExit(main())
