#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('data/floodsafe-people-status.json')
POLICE = Path('data/floodsafe-police.json')
RADIO = 'https://radionepalonline.com/en/'
RADIO_SEARCHES = [
    'https://radionepalonline.com/en/?s=Bhotekoshi',
    'https://radionepalonline.com/en/?s=Rasuwa+flood',
    'https://radionepalonline.com/en/?s=Trishuli+flood',
]
EKANTIPUR = 'https://ekantipur.com/'
EKANTIPUR_SEARCHES = [
    'https://ekantipur.com/search?q=%E0%A4%AD%E0%A5%8B%E0%A4%9F%E0%A5%87%E0%A4%95%E0%A5%8B%E0%A4%B6%E0%A5%80',
    'https://ekantipur.com/search?q=%E0%A4%B0%E0%A4%B8%E0%A5%81%E0%A4%B5%E0%A4%BE%20%E0%A4%AC%E0%A4%BE%E0%A4%A2%E0%A5%80',
    'https://ekantipur.com/search?q=Bhotekoshi%20flood',
]
UA = 'FloodSafe-Nepal/1.4 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/)'

EVENT_RE = re.compile(r'(rasuwa|bhotekoshi|bhote\s*koshi|trishuli|रसुवा|भोटेकोशी|त्रिशूली)', re.I)
FLOOD_RE = re.compile(r'(flood|flash flood|बाढी|आकस्मिक बाढी)', re.I)
AUTH_RE = re.compile(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|प्रहरी प्रधान कार्यालय|प्राधिकरण|Authority)', re.I)
AGG_RE = re.compile(r'(total|so far|death toll|confirmed|remain(?:s)? unaccounted|remain(?:s)? missing|overall|कुल|हालसम्म|पुष्टि|सम्पर्कविहीन)', re.I)
CORRECTION_RE = re.compile(r'(revis(?:ed|ion)|correct(?:ed|ion)|updated figure|संशोधित|सच्याइएको)', re.I)
SUBGROUP_RE = re.compile(r'(tourists?|foreigners?|विदेशी|पर्यटक|army|सेना|police personnel|प्रहरी कर्मचारी|armed police|सशस्त्र प्रहरी|customs|भन्सार|immigration|अध्यागमन)', re.I)


def fetch_text(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/json;q=0.9,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8-sig', 'replace')


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
        r'<meta[^>]+property=["\']article:modified_time["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
        r'"dateModified"\s*:\s*"([^"]+)"',
        r'"datePublished"\s*:\s*"([^"]+)"',
    ]
    best = (0, None)
    for p in patterns:
        for m in re.finditer(p, raw, re.I):
            stamp = parse_time(m.group(1))
            if stamp > best[0]:
                best = (stamp, m.group(1))
    if best[0]:
        return best
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
            r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,45}(?:confirmed dead|dead|died|मृत्यु|मृतक|शव\s+फेला)',
            r'(?:total|कुल|हालसम्म)[^0-9]{0,30}(\d{1,6})[^.।]{0,35}(?:dead|deaths?|मृत्यु|मृतक|शव)',
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


def add_candidate(best, kind, value, stamp, iso, source, url, authority=True, correction=False):
    if not value or value <= 0:
        return
    c = {
        'value': int(value),
        'stamp': stamp or 0,
        'iso': iso or datetime.now(timezone.utc).isoformat(),
        'source': source,
        'url': url,
        'authority': bool(authority),
        'correction': bool(correction),
    }
    cur = best.get(kind)
    if cur is None:
        best[kind] = c
        return
    # Fastest credible update wins. Authority status only breaks an exact timestamp tie.
    key = (c['stamp'], 1 if c['authority'] else 0, 1 if c['correction'] else 0, c['value'])
    oldkey = (cur['stamp'], 1 if cur.get('authority') else 0, 1 if cur.get('correction') else 0, cur['value'])
    if key > oldkey:
        best[kind] = c


def discover_links(listings, base, domain, max_links=80):
    links = []
    for listing in listings:
        try:
            raw = fetch_text(listing)
        except Exception as e:
            print('Listing failed:', listing, repr(e))
            continue
        for href, label in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw):
            title = strip_html(label)
            href = urllib.parse.urljoin(base, href)
            if domain not in href:
                continue
            if not relevant(title + ' ' + href):
                continue
            if href not in [x[0] for x in links]:
                links.append((href, title))
    return links[:max_links]


def radio_metrics():
    best = {}
    links = discover_links([RADIO] + RADIO_SEARCHES, RADIO, 'radionepalonline.com')
    for url, title in links:
        try:
            raw = fetch_text(url)
        except Exception:
            continue
        text = strip_html(raw)
        joined = title + ' ' + text
        if not relevant(joined) or not aggregate_context(joined):
            continue
        authority = bool(AUTH_RE.search(joined))
        correction = bool(CORRECTION_RE.search(joined))
        stamp, iso = page_time(raw, url)
        for k, v in metrics(joined).items():
            add_candidate(best, k, v, stamp, iso, 'Radio Nepal', url, authority, correction)
    return best


def ekantipur_metrics():
    best = {}
    links = discover_links(EKANTIPUR_SEARCHES, EKANTIPUR, 'ekantipur.com', 100)
    for url, title in links:
        try:
            raw = fetch_text(url)
        except Exception:
            continue
        text = strip_html(raw)
        joined = title + ' ' + text
        if not relevant(joined) or not aggregate_context(joined):
            continue
        # Require an authority attribution for Human Status totals from eKantipur.
        authority = bool(AUTH_RE.search(joined))
        if not authority:
            continue
        # Reject obvious subgroup-only stories unless the same story also clearly says total/overall/so far.
        if SUBGROUP_RE.search(title) and not re.search(r'(कुल|हालसम्म|overall|total|so far)', joined, re.I):
            continue
        correction = bool(CORRECTION_RE.search(joined))
        stamp, iso = page_time(raw, url)
        for k, v in metrics(joined).items():
            add_candidate(best, k, v, stamp, iso, 'eKantipur', url, True, correction)
    return best


def nepal_police_metrics():
    best = {}
    if not POLICE.exists():
        return best
    try:
        j = json.loads(POLICE.read_text(encoding='utf-8'))
    except Exception:
        return best
    v = j.get('total_deaths')
    stamp = parse_time(j.get('official_update_iso'))
    iso = j.get('official_update_iso')
    url = j.get('source_url') or 'https://www.nepalpolice.gov.np/'
    if isinstance(v, int) and v > 0 and stamp:
        add_candidate(best, 'death', v, stamp, iso, 'Nepal Police', url, True, False)
    return best


def main():
    old = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    combined = {}
    for loader in (nepal_police_metrics, radio_metrics, ekantipur_metrics):
        try:
            got = loader()
            for k, c in got.items():
                cur = combined.get(k)
                if cur is None or (c['stamp'], 1 if c['authority'] else 0, c['value']) > (cur['stamp'], 1 if cur.get('authority') else 0, cur['value']):
                    combined[k] = c
        except Exception as e:
            print(loader.__name__, 'failed:', repr(e))

    fields = {
        'death': ('recovered_bodies', 'recovered_update_iso', 'recovered_update_time', 'recovered_source', 'recovered_source_url'),
        'missing': ('missing_minimum', 'missing_update_time', 'missing_update_time', 'missing_source', 'missing_source_url'),
        'rescued': ('rescued_alive', 'rescued_update_time', 'rescued_update_time', 'rescued_source', 'rescued_source_url'),
    }
    changed = False
    winners = {}
    for k, c in combined.items():
        vf, tf, tf2, sf, uf = fields[k]
        oldstamp = parse_time(old.get(tf))
        oldv = int(old.get(vf) or 0)
        if c['stamp'] < oldstamp:
            continue
        if c['value'] < oldv and not c.get('correction'):
            continue
        if c['stamp'] == oldstamp and c['value'] == oldv and old.get(sf) == c['source']:
            winners[k] = c['source']
            continue
        old[vf] = c['value']
        old[tf] = c['iso']
        old[tf2] = c['iso']
        old[sf] = c['source']
        old[uf] = c['url']
        winners[k] = c['source']
        changed = True
        print(k, c['value'], c['source'], c['url'])

    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    old.setdefault('event', 'Bhotekoshi flash flood')
    old.setdefault('event_ne', 'भोटेकोशी आकस्मिक बाढी')
    old['last_checked_utc'] = now
    old['updated_date'] = datetime.now(timezone.utc).date().isoformat()
    old['status'] = 'auto_3source_fastest_credible'
    old['sync_sources'] = ['Nepal Police', 'Radio Nepal', 'eKantipur']
    old['sync_policy'] = 'Among Nepal Police, Radio Nepal and eKantipur, use the newest credible cumulative authority-reported metric and display that publisher as the source. Reject subgroup-only counts.'
    old['last_winning_sources'] = winners
    old.pop('setu_breakdown', None)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Human Status 3-source sync complete', 'metrics changed' if changed else 'no newer credible aggregate')


if __name__ == '__main__':
    main()
