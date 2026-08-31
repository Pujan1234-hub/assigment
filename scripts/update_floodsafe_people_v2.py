#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT = Path('data/floodsafe-people-status.json')
POLICE = Path('data/floodsafe-police.json')
UA = 'FloodSafe-Nepal/3.0 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/)'
NPT = timezone(timedelta(hours=5, minutes=45))

RONB = 'https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,modified_gmt,link,title,excerpt,content'
ONLINEKHABAR = 'https://english.onlinekhabar.com/wp-json/wp/v2/posts?per_page=80&_fields=date,date_gmt,modified,modified_gmt,link,title,excerpt,content'
KCHA = 'https://kchakhabar.com/api/v1/today.json?limit=100'
RADIO_LISTINGS = [
    'https://radionepalonline.com/en/',
    'https://radionepalonline.com/en/?s=Bhotekoshi',
    'https://radionepalonline.com/en/?s=Rasuwa+flood',
    'https://radionepalonline.com/en/?s=Trishuli+flood',
]
HAMRO_LISTINGS = [
    'https://www.hamropatro.com/',
    'https://www.hamropatro.com/posts',
    'https://www.hamropatro.com/en/posts',
]

EVENT_RE = re.compile(r'(rasuwa|bhotekoshi|bhote\s*koshi|trishuli|रसुवा|भोटेकोशी|भोटेकोसी|त्रिशूली)', re.I)
FLOOD_RE = re.compile(r'(flood|flash flood|बाढी|आकस्मिक बाढी)', re.I)
AUTH_RE = re.compile(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|प्रहरी प्रधान कार्यालय|प्राधिकरण|Authority|government|सरकार)', re.I)
DEATH_RE = re.compile(r'(death toll|deaths?|dead|killed|bodies?|body|मृत्यु|मृतक|शव|लाश)', re.I)
MISSING_RE = re.compile(r'(missing|unaccounted|out of contact|contactless|सम्पर्कविहीन|बेपत्ता)', re.I)
RESCUE_RE = re.compile(r'(rescued?|evacuated|उद्धार)', re.I)
CORRECTION_RE = re.compile(r'(revis(?:ed|ion)|correct(?:ed|ion)|updated figure|संशोधित|सच्याइएको)', re.I)

def request(url, accept='*/*'):
    return urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': accept,
        'Cache-Control': 'no-cache, no-store, max-age=0',
        'Pragma': 'no-cache',
    })

def fetch_text(url):
    with urllib.request.urlopen(request(url, 'text/html,application/json;q=0.9,*/*;q=0.8'), timeout=22) as r:
        return r.read().decode('utf-8-sig', 'replace')

def fetch_json(url):
    return json.loads(fetch_text(url))

def strip_html(raw):
    raw = re.sub(r'(?is)<script.*?</script>|<style.*?</style>', ' ', raw or '')
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

def as_iso(v):
    t = parse_time(v)
    return datetime.fromtimestamp(t, timezone.utc).isoformat() if t else None

def page_time(raw):
    best = (0, None)
    pats = [
        r'article:modified_time["\'][^>]+content=["\']([^"\']+)',
        r'article:published_time["\'][^>]+content=["\']([^"\']+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
        r'"dateModified"\s*:\s*"([^"]+)',
        r'"datePublished"\s*:\s*"([^"]+)',
    ]
    for p in pats:
        for m in re.finditer(p, raw or '', re.I):
            t = parse_time(m.group(1))
            if t > best[0]:
                best = (t, m.group(1))
    return best

def html_title(raw):
    for p in [
        r'property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
        r'<h1[^>]*>(.*?)</h1>',
        r'<title[^>]*>(.*?)</title>',
    ]:
        m = re.search(p, raw or '', re.I | re.S)
        if m:
            return strip_html(m.group(1))
    return ''

def article_body(raw):
    m = re.search(r'(?is)<article\b[^>]*>(.*?)</article>', raw or '')
    if m:
        return strip_html(m.group(1))
    m = re.search(r'(?is)<main\b[^>]*>(.*?)</main>', raw or '')
    if m:
        return strip_html(m.group(1))
    return ''

def relevant_title(title):
    return bool(EVENT_RE.search(title or '') and FLOOD_RE.search(title or ''))

def focus_kinds(title):
    kinds = set()
    if DEATH_RE.search(title or ''):
        kinds.add('death')
        kinds.add('missing')
    if MISSING_RE.search(title or ''):
        kinds.add('missing')
    if RESCUE_RE.search(title or ''):
        kinds.add('rescued')
    return kinds

def metric_values(text):
    t = digits(text)
    out = {}
    pats = {
        'death': [
            r'(?:death toll|confirmed dead|deaths?|killed|मृत्यु|मृतक)[^0-9]{0,60}(\d{1,6})',
            r'(\d{1,6})\s+(?:bodies|people|persons|जना)?[^.।]{0,55}(?:recovered|dead|killed|मृत्यु|मृतक|शव\s+फेला)',
        ],
        'missing': [
            r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,70}(?:remain\s+)?(?:unaccounted for|missing|out of contact|contactless|सम्पर्कविहीन|बेपत्ता)',
            r'(?:missing|unaccounted|out of contact|contactless|सम्पर्कविहीन|बेपत्ता)[^0-9]{0,60}(\d{1,6})',
        ],
        'rescued': [
            r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,70}(?:have\s+)?(?:so\s+far\s+)?(?:been\s+)?(?:rescued|evacuated)',
            r'(?:rescued|evacuated|उद्धार)[^0-9]{0,60}(\d{1,6})',
        ],
    }
    for kind, pp in pats.items():
        for p in pp:
            m = re.search(p, t, re.I)
            if m:
                v = int(m.group(1))
                if 0 < v < 100000:
                    out[kind] = v
                    break
    return out

def explicit_observation_time(text, published_iso):
    pub_t = parse_time(published_iso)
    if not pub_t:
        return 0, None, False
    pub = datetime.fromtimestamp(pub_t, timezone.utc).astimezone(NPT)
    patterns = [
        r'\bas of\s+(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b',
        r'\b(?:data|figures|information)\s+(?:collected\s+)?as of\s+(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b',
    ]
    for p in patterns:
        m = re.search(p, text or '', re.I)
        if not m:
            continue
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        ap = m.group(3).lower().replace('.', '')
        if ap == 'pm' and hour < 12:
            hour += 12
        if ap == 'am' and hour == 12:
            hour = 0
        try:
            dt = pub.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return dt.timestamp(), dt.isoformat(), True
        except Exception:
            pass
    return pub_t, datetime.fromtimestamp(pub_t, timezone.utc).isoformat(), False

def add(best, kind, value, stamp, iso, source, url, authority, correction=False, explicit=False):
    if not value or not stamp or not iso or not authority:
        return
    c = {
        'value': int(value), 'stamp': stamp, 'iso': iso, 'source': source, 'url': url,
        'authority': True, 'correction': bool(correction), 'explicit_observation': bool(explicit),
    }
    old = best.get(kind)
    key = (1 if c['explicit_observation'] else 0, c['stamp'])
    oldkey = (-1, -1) if not old else (1 if old.get('explicit_observation') else 0, old['stamp'])
    if key > oldkey:
        best[kind] = c

def merge_into(dst, src):
    for kind, c in (src or {}).items():
        add(dst, kind, c['value'], c['stamp'], c['iso'], c['source'], c['url'],
            c.get('authority'), c.get('correction'), c.get('explicit_observation'))
    return dst

def candidates_from_story(title, body, published_iso, source, url):
    best = {}
    if not relevant_title(title):
        return best
    kinds = focus_kinds(title)
    if not kinds:
        return best
    text = (title + ' ' + body[:5000]).strip()
    authority = bool(AUTH_RE.search(text))
    if not authority:
        return best
    values = metric_values(text)
    stamp, iso, explicit = explicit_observation_time(text, published_iso)
    correction = bool(CORRECTION_RE.search(text))
    for kind in kinds:
        if kind not in values:
            continue
        if kind in ('death', 'missing') and not explicit:
            continue
        add(best, kind, values[kind], stamp, iso, source, url, True, correction, explicit)
    return best

def police_loader():
    best = {}
    if not POLICE.exists():
        return best
    try:
        j = json.loads(POLICE.read_text(encoding='utf-8'))
    except Exception:
        return best
    t = parse_time(j.get('official_update_iso'))
    v = j.get('total_deaths')
    if isinstance(v, int) and v > 0 and t:
        add(best, 'death', v, t, j.get('official_update_iso'), 'Nepal Police',
            j.get('source_url') or 'https://www.nepalpolice.gov.np/', True, False, True)
    return best

def wordpress_loader(endpoint, source_name):
    best = {}
    try:
        posts = fetch_json(endpoint)
    except Exception as e:
        print(source_name, 'wordpress failed', repr(e))
        return best
    for p in posts if isinstance(posts, list) else []:
        title = strip_html((p.get('title') or {}).get('rendered', ''))
        body = strip_html((p.get('content') or {}).get('rendered', '') + ' ' + (p.get('excerpt') or {}).get('rendered', ''))
        modified = p.get('modified_gmt') or p.get('date_gmt')
        pub_iso = as_iso(str(modified) + '+00:00') if modified else None
        if not pub_iso:
            pub_iso = as_iso(p.get('modified') or p.get('date'))
        if not pub_iso:
            continue
        merge_into(best, candidates_from_story(title, body, pub_iso, source_name, p.get('link') or endpoint))
    return best

def discover_article_links(listings, domain, limit=80):
    links = []
    for listing in listings:
        try:
            raw = fetch_text(listing)
        except Exception as e:
            print('listing failed', listing, repr(e))
            continue
        for href in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\']', raw):
            u = urllib.parse.urljoin(listing, href)
            if domain in u and u not in links:
                links.append(u)
    return links[:limit]

def article_loader(listings, domain, source_name, limit=80):
    best = {}
    for u in discover_article_links(listings, domain, limit):
        try:
            raw = fetch_text(u)
        except Exception:
            continue
        title = html_title(raw)
        body = article_body(raw)
        if not title or not body:
            continue
        _, pub_raw = page_time(raw)
        pub_iso = as_iso(pub_raw)
        if not pub_iso:
            continue
        merge_into(best, candidates_from_story(title, body, pub_iso, source_name, u))
    return best

def kcha_loader():
    best = {}
    try:
        j = fetch_json(KCHA)
    except Exception as e:
        print('kcha failed', repr(e))
        return best
    for s in j.get('stories', []) if isinstance(j, dict) else []:
        title = (s.get('topic_en') or '') + ' ' + (s.get('topic_ne') or '')
        body = (s.get('summary_en') or '') + ' ' + (s.get('summary_ne') or '')
        raw_time = s.get('updated_at') or s.get('first_reported')
        pub_iso = as_iso(raw_time)
        if not pub_iso:
            continue
        sources = s.get('sources') or []
        source = str(sources[0].get('publisher') if sources else 'Verified national media via K cha khabar')
        url = str((sources[0].get('url') if sources else None) or s.get('url') or 'https://kchakhabar.com/')
        merge_into(best, candidates_from_story(title, body, pub_iso, source, url))
    return best

def main():
    old = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    combined = {}
    loaders = [
        police_loader,
        lambda: wordpress_loader(ONLINEKHABAR, 'OnlineKhabar'),
        lambda: article_loader(RADIO_LISTINGS, 'radionepalonline.com', 'Radio Nepal', 90),
        lambda: wordpress_loader(RONB, 'RONB'),
        lambda: article_loader(HAMRO_LISTINGS, 'hamropatro.com', 'Hamro Patro', 80),
        kcha_loader,
    ]
    for loader in loaders:
        try:
            merge_into(combined, loader())
        except Exception as e:
            print('loader failed', getattr(loader, '__name__', 'loader'), repr(e))

    fields = {
        'death': ('recovered_bodies', 'recovered_update_time', 'recovered_source', 'recovered_source_url', 'recovered_update_iso'),
        'missing': ('missing_minimum', 'missing_update_time', 'missing_source', 'missing_source_url', None),
        'rescued': ('rescued_alive', 'rescued_update_time', 'rescued_source', 'rescued_source_url', None),
    }
    trusted_old = int(old.get('sync_schema') or 0) >= 2
    winners = {}
    for kind, c in combined.items():
        vf, tf, sf, uf, extra = fields[kind]
        oldstamp = parse_time(old.get(tf))
        oldv = int(old.get(vf) or 0)
        if trusted_old and c['stamp'] < oldstamp:
            continue
        if kind in ('death', 'rescued') and c['value'] < oldv and not c.get('correction'):
            continue
        old[vf] = c['value']
        old[tf] = c['iso']
        old[sf] = c['source']
        old[uf] = c['url']
        old[f'{kind}_time_basis'] = 'explicit_authority_observation' if c.get('explicit_observation') else 'trusted_source_publication'
        winners[kind] = c['source']
        if extra:
            old[extra] = c['iso']
        print('winner', kind, c['value'], c['source'], c['iso'], c['url'])

    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    old.setdefault('event', 'Bhotekoshi flash flood')
    old.setdefault('event_ne', 'भोटेकोशी आकस्मिक बाढी')
    old['updated_date'] = datetime.now(timezone.utc).date().isoformat()
    old['last_checked_utc'] = now
    old['status'] = 'event_scoped_authority_mirror'
    old['sync_schema'] = 2
    old['sync_sources'] = ['Nepal Police', 'OnlineKhabar direct', 'Radio Nepal', 'RONB', 'Hamro Patro', 'K cha khabar']
    old['sync_policy'] = (
        'Use event-scoped authority-attributed figures only. Parse article main content, not sidebars. '
        'Death and rescued cumulative totals do not decrease without an explicit correction; missing may '
        'decrease when a newer authoritative event bulletin reports fewer people unaccounted for. '
        'last_checked_utc never counts as a metric observation timestamp.'
    )
    old['last_winning_sources'] = winners
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
