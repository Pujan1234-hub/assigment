#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('data/floodsafe-people-status.json')
NEWS = Path('data/national-news.json')
RADIO = 'https://radionepalonline.com/en/'
RADIO_SEARCHES = [
    'https://radionepalonline.com/en/?s=Bhotekoshi',
    'https://radionepalonline.com/en/?s=Rasuwa+flood',
    'https://radionepalonline.com/en/?s=Trishuli+flood',
]
KCHA = 'https://kchakhabar.com/api/v1/today.json?limit=150'
UA = 'FloodSafe-Nepal/1.3 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/)'

EVENT_RE = re.compile(r'(rasuwa|bhotekoshi|bhote\s*koshi|trishuli|रसुवा|भोटेकोशी|त्रिशूली)', re.I)
FLOOD_RE = re.compile(r'(flood|flash flood|बाढी|आकस्मिक बाढी)', re.I)
AUTH_RE = re.compile(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|प्राधिकरण|Authority|security agencies|सरकार)', re.I)
AGG_RE = re.compile(r'(total|so far|death toll|confirmed|remain(?:s)? unaccounted|remain(?:s)? missing|overall|कुल|हालसम्म|पुष्टि|सम्पर्कविहीन)', re.I)
CORRECTION_RE = re.compile(r'(revis(?:ed|ion)|correct(?:ed|ion)|updated figure|संशोधित|सच्याइएको)', re.I)
TRUSTED_PUBLISHERS = re.compile(r'(Radio Nepal|Public Service Broadcasting|RSS|Rastriya Samachar Samiti|The Rising Nepal|Kathmandu Post|Onlinekhabar|Setopati|Ratopati)', re.I)


def fetch_text(url):
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': UA,
            'Accept': 'text/html,application/json;q=0.9,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8-sig', 'replace')


def fetch_json(url):
    return json.loads(fetch_text(url))


def strip_html(raw):
    raw = re.sub(r'(?is)<script.*?</script>|<style.*?</style>', ' ', raw)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', raw))).strip()


def digits(s):
    return str(s or '').translate(str.maketrans('०१२३४५६७८९', '0123456789')).replace(',', '')


def parse_time(v):
    if not v:
        return 0
    try:
        return datetime.fromisoformat(str(v).replace('Z', '+00:00')).timestamp()
    except Exception:
        return 0


def url_date_stamp(url):
    m = re.search(r'/(20\d\d)/(\d\d)/(\d\d)/', url or '')
    if not m:
        return 0
    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 23, 59, tzinfo=timezone.utc).timestamp()


def page_time(raw, url):
    patterns = [
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
    ]
    for p in patterns:
        m = re.search(p, raw, re.I)
        if m and parse_time(m.group(1)):
            return parse_time(m.group(1)), m.group(1)
    stamp = url_date_stamp(url)
    iso = datetime.fromtimestamp(stamp, timezone.utc).isoformat() if stamp else None
    return stamp, iso


def relevant(text):
    return bool(EVENT_RE.search(text or '') and FLOOD_RE.search(text or ''))


def aggregate_context(text):
    return bool(AGG_RE.search(text or ''))


def metrics(text):
    t = digits(text)
    out = {}
    pats = {
        'death': [
            r'(?:death toll|deaths?|confirmed dead|मृत्यु|मृतक)[^0-9]{0,55}(\d{1,6})',
            r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,45}(?:confirmed dead|dead|died|मृत्यु|मृतक)',
            r'(?:total|कुल|हालसम्म)[^0-9]{0,30}(\d{1,6})[^.।]{0,30}(?:dead|deaths?|मृत्यु|मृतक)',
        ],
        'missing': [
            r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,65}(?:remain\s+)?(?:unaccounted for|missing|सम्पर्कविहीन|बेपत्ता)',
            r'(?:missing|unaccounted|सम्पर्कविहीन|बेपत्ता)[^0-9]{0,55}(\d{1,6})',
            r'(?:total|कुल|हालसम्म)[^0-9]{0,30}(\d{1,6})[^.।]{0,35}(?:missing|unaccounted|सम्पर्कविहीन|बेपत्ता)',
        ],
        'rescued': [
            r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,65}(?:have\s+)?(?:so\s+far\s+)?(?:been\s+)?rescued',
            r'(?:rescued|उद्धार)[^0-9]{0,55}(\d{1,6})',
            r'(?:total|कुल|हालसम्म)[^0-9]{0,30}(\d{1,6})[^.।]{0,35}(?:rescued|उद्धार)',
        ],
    }
    for k, pp in pats.items():
        for p in pp:
            m = re.search(p, t, re.I)
            if m:
                v = int(m.group(1))
                if v > 0:
                    out[k] = v
                    break
    return out


def add_candidate(best, kind, value, stamp, iso, source, url, confidence=2, correction=False):
    if not value or value <= 0:
        return
    c = {
        'value': int(value), 'stamp': stamp or 0, 'iso': iso or datetime.now(timezone.utc).isoformat(),
        'source': source, 'url': url, 'confidence': confidence, 'correction': correction,
    }
    cur = best.get(kind)
    if cur is None:
        best[kind] = c
        return
    # Newer publication wins. For same timestamp/date, prefer higher-confidence source,
    # then the larger cumulative total. Explicit corrections are allowed to replace totals.
    key = (c['stamp'], c['confidence'], 1 if c['correction'] else 0, c['value'])
    oldkey = (cur['stamp'], cur['confidence'], 1 if cur.get('correction') else 0, cur['value'])
    if key > oldkey:
        best[kind] = c


def discover_radio_links():
    links = []
    for listing in [RADIO] + RADIO_SEARCHES:
        try:
            raw = fetch_text(listing)
        except Exception as e:
            print('Radio listing failed:', listing, repr(e))
            continue
        for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw):
            title = strip_html(label)
            href = urllib.parse.urljoin(RADIO, href)
            if not href.startswith('https://radionepalonline.com/'):
                continue
            if not relevant(title + ' ' + href):
                continue
            if href not in [x[0] for x in links]:
                links.append((href, title))
    return links[:80]


def radio_metrics():
    best = {}
    for url, title in discover_radio_links():
        try:
            raw = fetch_text(url)
        except Exception:
            continue
        text = strip_html(raw)
        joined = title + ' ' + text
        if not relevant(joined):
            continue
        mm = metrics(joined)
        if not mm:
            continue
        # Public-service Radio Nepal/RSS is accepted when the item clearly presents cumulative totals.
        # If it also cites NDRRMA/Nepal Police, give it the highest confidence.
        authority = bool(AUTH_RE.search(joined))
        if not authority and not aggregate_context(joined):
            continue
        stamp, iso = page_time(raw, url)
        source = 'NDRRMA / Nepal Police via Public Service Broadcasting Radio Nepal' if authority else 'Public Service Broadcasting Radio Nepal / RSS'
        confidence = 4 if authority else 3
        correction = bool(CORRECTION_RE.search(joined))
        for k, v in mm.items():
            add_candidate(best, k, v, stamp, iso, source, url, confidence, correction)
    return best


def kcha_metrics():
    best = {}
    j = fetch_json(KCHA)
    for s in j.get('stories') or []:
        text = ' '.join(str(s.get(k) or '') for k in ('topic_ne', 'topic_en', 'summary_ne', 'summary_en'))
        if not relevant(text):
            continue
        src = (s.get('sources') or [{}])[0]
        publisher = src.get('publisher') or s.get('source') or 'Nepal media'
        authority = bool(AUTH_RE.search(text + ' ' + publisher))
        trusted = bool(TRUSTED_PUBLISHERS.search(publisher))
        # Do not turn subgroup updates (tourists, one district, one agency) into national totals.
        if not authority and not (trusted and aggregate_context(text)):
            continue
        when = s.get('updated_at') or s.get('first_reported')
        stamp = parse_time(when)
        confidence = 4 if authority else 2
        correction = bool(CORRECTION_RE.search(text))
        for k, v in metrics(text).items():
            add_candidate(best, k, v, stamp, when, ('Authority report via ' if authority else 'Latest aggregate via ') + publisher, src.get('url') or s.get('url') or '', confidence, correction)
    return best


def national_news_metrics():
    best = {}
    if not NEWS.exists():
        return best
    try:
        j = json.loads(NEWS.read_text(encoding='utf-8'))
    except Exception:
        return best
    for item in j.get('items') or []:
        title = str(item.get('title') or '')
        url = str(item.get('url') or '')
        publisher = str(item.get('source') or 'Nepal media')
        if not relevant(title):
            continue
        try:
            raw = fetch_text(url)
        except Exception:
            continue
        text = strip_html(raw)
        joined = title + ' ' + text
        mm = metrics(joined)
        if not mm:
            continue
        authority = bool(AUTH_RE.search(joined))
        trusted = bool(TRUSTED_PUBLISHERS.search(publisher))
        if not authority and not (trusted and aggregate_context(joined)):
            continue
        stamp = parse_time(item.get('published_at')) or page_time(raw, url)[0]
        iso = item.get('published_at') or datetime.fromtimestamp(stamp, timezone.utc).isoformat()
        confidence = 4 if authority else 2
        correction = bool(CORRECTION_RE.search(joined))
        for k, v in mm.items():
            add_candidate(best, k, v, stamp, iso, ('Authority report via ' if authority else 'Latest aggregate via ') + publisher, url, confidence, correction)
    return best


def main():
    old = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    combined = {}
    loaders = (radio_metrics, kcha_metrics, national_news_metrics)
    for loader in loaders:
        try:
            got = loader()
            for k, c in got.items():
                cur = combined.get(k)
                if cur is None or (c['stamp'], c['confidence'], c['value']) > (cur['stamp'], cur['confidence'], cur['value']):
                    combined[k] = c
        except Exception as e:
            print(loader.__name__, 'failed:', repr(e))

    fields = {
        'death': ('recovered_bodies', 'recovered_update_iso', 'recovered_update_time', 'recovered_source', 'recovered_source_url'),
        'missing': ('missing_minimum', 'missing_update_time', 'missing_update_time', 'missing_source', 'missing_source_url'),
        'rescued': ('rescued_alive', 'rescued_update_time', 'rescued_update_time', 'rescued_source', 'rescued_source_url'),
    }
    changed = False
    for k, c in combined.items():
        vf, tf, tf2, sf, uf = fields[k]
        oldstamp = parse_time(old.get(tf))
        oldv = int(old.get(vf) or 0)
        # Ignore older reports. Cumulative totals normally cannot fall; a lower value is accepted only
        # when the newer source explicitly says the figure was revised/corrected.
        if c['stamp'] < oldstamp:
            continue
        if c['value'] < oldv and not c.get('correction'):
            continue
        if c['stamp'] == oldstamp and c['value'] == oldv:
            continue
        old[vf] = c['value']
        old[tf] = c['iso']
        old[tf2] = c['iso']
        old[sf] = c['source']
        old[uf] = c['url']
        changed = True
        print(k, c['value'], c['url'])

    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    old.setdefault('event', 'Bhotekoshi flash flood')
    old.setdefault('event_ne', 'भोटेकोशी आकस्मिक बाढी')
    old['last_checked_utc'] = now
    old['updated_date'] = datetime.now(timezone.utc).date().isoformat()
    old['status'] = 'auto_multi_source_aggregate'
    old['sync_policy'] = 'Latest credible cumulative aggregate; official/authority reports preferred; subgroup counts rejected.'
    old.pop('setu_breakdown', None)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Human Status sync complete', 'metrics changed' if changed else 'no newer credible aggregate')


if __name__ == '__main__':
    main()
