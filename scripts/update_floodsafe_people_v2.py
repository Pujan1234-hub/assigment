#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('data/floodsafe-people-status.json')
POLICE = Path('data/floodsafe-police.json')
UA = 'FloodSafe-Nepal/2.1 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/)'
RONB = 'https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,modified_gmt,link,title,excerpt,content'
KCHA = 'https://kchakhabar.com/api/v1/today.json?limit=100'
RADIO_LISTINGS = ['https://radionepalonline.com/en/','https://radionepalonline.com/en/?s=Bhotekoshi','https://radionepalonline.com/en/?s=Rasuwa+flood','https://radionepalonline.com/en/?s=Trishuli+flood']
HAMRO_LISTINGS = ['https://www.hamropatro.com/','https://www.hamropatro.com/posts','https://www.hamropatro.com/en/posts']
EVENT_RE = re.compile(r'(rasuwa|bhotekoshi|bhote\s*koshi|trishuli|रसुवा|भोटेकोशी|भोटेकोसी|त्रिशूली)', re.I)
FLOOD_RE = re.compile(r'(flood|flash flood|बाढी|आकस्मिक बाढी)', re.I)
AUTH_RE = re.compile(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|प्रहरी प्रधान कार्यालय|प्राधिकरण|Authority|government figures|सरकार)', re.I)
AGG_RE = re.compile(r'(total|so far|death toll|confirmed|remain(?:s)? unaccounted|remain(?:s)? missing|overall|कुल|हालसम्म|पुष्टि|सम्पर्कविहीन|बेपत्ता)', re.I)
CORRECTION_RE = re.compile(r'(revis(?:ed|ion)|correct(?:ed|ion)|updated figure|संशोधित|सच्याइएको)', re.I)
SUBGROUP_RE = re.compile(r'(tourists?|foreigners?|पर्यटक|विदेशी|army|सेना|police personnel|प्रहरी कर्मचारी|armed police|सशस्त्र प्रहरी|hydropower|जलविद्युत|workers?|employees?|कर्मचारी)', re.I)
PREFERRED = ['Nepal Police','Radio Nepal','RONB','Hamro Patro','The Kathmandu Post','Kathmandu Post','OnlineKhabar','Onlinekhabar','Kantipur','Setopati','Ratopati','Republica','Nepal News','Gorkhapatra']

def request(url, accept='*/*'):
    return urllib.request.Request(url, headers={'User-Agent':UA,'Accept':accept,'Cache-Control':'no-cache','Pragma':'no-cache'})

def fetch_text(url):
    with urllib.request.urlopen(request(url,'text/html,application/json;q=0.9,*/*;q=0.8'), timeout=22) as r:
        return r.read().decode('utf-8-sig','replace')

def fetch_json(url): return json.loads(fetch_text(url))

def strip_html(raw):
    raw = re.sub(r'(?is)<script.*?</script>|<style.*?</style>', ' ', raw or '')
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', raw))).strip()

def digits(s): return str(s or '').translate(str.maketrans('०१२३४५६७८९','0123456789')).replace(',','')

def parse_time(v):
    if not v: return 0
    try: return datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
    except Exception: return 0

def as_iso(v):
    t=parse_time(v)
    return datetime.fromtimestamp(t,timezone.utc).isoformat() if t else None

def page_time(raw,url):
    best=(0,None)
    for p in [r'article:modified_time["\'][^>]+content=["\']([^"\']+)',r'article:published_time["\'][^>]+content=["\']([^"\']+)',r'<time[^>]+datetime=["\']([^"\']+)',r'"dateModified"\s*:\s*"([^"]+)',r'"datePublished"\s*:\s*"([^"]+)']:
        for m in re.finditer(p,raw or '',re.I):
            t=parse_time(m.group(1))
            if t>best[0]: best=(t,m.group(1))
    return best

def relevant(text): return bool(EVENT_RE.search(text or '') and FLOOD_RE.search(text or ''))

def aggregate_ok(title,text):
    joined=(title or '')+' '+(text or '')
    if not relevant(joined) or not AGG_RE.search(joined): return False
    if SUBGROUP_RE.search(title or '') and not re.search(r'(overall|total|so far|कुल|हालसम्म|सरकार|NDRRMA)',joined,re.I): return False
    return True

def metrics(text):
    t=digits(text);out={}
    pats={
      'death':[r'(?:death toll|confirmed dead|deaths?|मृत्यु|मृतक|शव)[^0-9]{0,60}(\d{1,6})',r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,55}(?:confirmed dead|dead|died|मृत्यु|मृतक|शव\s+फेला)',r'(?:total|कुल|हालसम्म)[^0-9]{0,35}(\d{1,6})[^.।]{0,45}(?:dead|death|मृत्यु|मृतक|शव)'],
      'missing':[r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,70}(?:remain\s+)?(?:unaccounted for|missing|सम्पर्कविहीन|बेपत्ता|out of contact)',r'(?:missing|unaccounted|out of contact|सम्पर्कविहीन|बेपत्ता)[^0-9]{0,60}(\d{1,6})',r'(?:total|कुल|हालसम्म)[^0-9]{0,35}(\d{1,6})[^.।]{0,45}(?:missing|unaccounted|सम्पर्कविहीन|बेपत्ता)'],
      'rescued':[r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,70}(?:have\s+)?(?:so\s+far\s+)?(?:been\s+)?rescued',r'(?:rescued|उद्धार)[^0-9]{0,60}(\d{1,6})',r'(?:total|कुल|हालसम्म|so far)[^0-9]{0,35}(\d{1,6})[^.।]{0,45}(?:rescued|उद्धार)']}
    for kind,pp in pats.items():
        for p in pp:
            m=re.search(p,t,re.I)
            if m:
                v=int(m.group(1))
                if 0<v<100000: out[kind]=v;break
    return out

def add(best,kind,value,stamp,iso,source,url,authority,correction=False):
    if not value or not stamp or not iso: return
    c={'value':int(value),'stamp':stamp,'iso':iso,'source':source,'url':url,'authority':bool(authority),'correction':bool(correction)}
    old=best.get(kind)
    key=(c['stamp'],1 if c['authority'] else 0,1 if c['correction'] else 0,c['value'])
    oldkey=(-1,0,0,0) if not old else (old['stamp'],1 if old.get('authority') else 0,1 if old.get('correction') else 0,old['value'])
    if key>oldkey: best[kind]=c

def police_loader():
    best={}
    if not POLICE.exists(): return best
    try: j=json.loads(POLICE.read_text(encoding='utf-8'))
    except Exception: return best
    t=parse_time(j.get('official_update_iso'));v=j.get('total_deaths')
    if isinstance(v,int) and v>0 and t: add(best,'death',v,t,j.get('official_update_iso'),'Nepal Police',j.get('source_url') or 'https://www.nepalpolice.gov.np/',True)
    return best

def discover_article_links(listings,domain,limit=70):
    links=[]
    for listing in listings:
        try: raw=fetch_text(listing)
        except Exception as e: print('listing failed',listing,repr(e));continue
        for href in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\']',raw):
            u=urllib.parse.urljoin(listing,href)
            if domain in u and u not in links: links.append(u)
    return links[:limit]

def article_loader(listings,domain,source_name,limit=70):
    best={}
    for u in discover_article_links(listings,domain,limit):
        try: raw=fetch_text(u)
        except Exception: continue
        text=strip_html(raw);title=text[:280]
        if not aggregate_ok(title,text): continue
        stamp,iso=page_time(raw,u)
        if not stamp: continue
        authority=bool(AUTH_RE.search(text));correction=bool(CORRECTION_RE.search(text))
        for kind,value in metrics(text).items(): add(best,kind,value,stamp,iso,source_name,u,authority,correction)
    return best

def radio_loader(): return article_loader(RADIO_LISTINGS,'radionepalonline.com','Radio Nepal',80)

def hamro_loader():
    # Watch Hamro Patro, but only accept a story if its own page exposes a stable timestamp.
    # Never use the current clock time as a substitute for article freshness.
    return article_loader(HAMRO_LISTINGS,'hamropatro.com','Hamro Patro',80)

def ronb_loader():
    best={}
    try: posts=fetch_json(RONB)
    except Exception as e: print('ronb failed',repr(e));return best
    for p in posts if isinstance(posts,list) else []:
        title=strip_html((p.get('title') or {}).get('rendered',''));body=strip_html((p.get('content') or {}).get('rendered','')+' '+(p.get('excerpt') or {}).get('rendered',''))
        if not aggregate_ok(title,body): continue
        modified=p.get('modified_gmt') or p.get('date_gmt');iso=as_iso(str(modified)+'+00:00') if modified else None;stamp=parse_time(iso);authority=bool(AUTH_RE.search(title+' '+body));correction=bool(CORRECTION_RE.search(body));u=p.get('link') or 'https://www.ronbpost.com/'
        for kind,value in metrics(title+' '+body).items(): add(best,kind,value,stamp,iso,'RONB',u,authority,correction)
    return best

def kcha_loader():
    best={}
    try: j=fetch_json(KCHA)
    except Exception as e: print('kcha failed',repr(e));return best
    stories=j.get('stories',[]) if isinstance(j,dict) else []
    for s in stories:
        title=(s.get('topic_en') or '')+' '+(s.get('topic_ne') or '');body=(s.get('summary_en') or '')+' '+(s.get('summary_ne') or '')
        if not aggregate_ok(title,body): continue
        raw_time=s.get('updated_at') or s.get('first_reported');stamp=parse_time(raw_time);iso=as_iso(raw_time)
        if not stamp: continue
        sources=s.get('sources') or [];source='Verified national media via K cha khabar';url=s.get('url') or 'https://kchakhabar.com/'
        for pref in PREFERRED:
            hit=next((x for x in sources if pref.lower() in str(x.get('publisher','')).lower()),None)
            if hit: source=str(hit.get('publisher') or pref);url=hit.get('url') or url;break
        if sources and source.startswith('Verified'): source=str(sources[0].get('publisher') or source);url=sources[0].get('url') or url
        authority=bool(AUTH_RE.search(title+' '+body));correction=bool(CORRECTION_RE.search(body))
        for kind,value in metrics(title+' '+body).items(): add(best,kind,value,stamp,iso,source,url,authority,correction)
    return best

def main():
    old=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {};combined={}
    for loader in (police_loader,radio_loader,ronb_loader,hamro_loader,kcha_loader):
        try: got=loader()
        except Exception as e: print(loader.__name__,'failed',repr(e));continue
        for kind,c in got.items():
            cur=combined.get(kind);key=(c['stamp'],1 if c['authority'] else 0,c['value']);oldkey=(-1,0,0) if not cur else (cur['stamp'],1 if cur.get('authority') else 0,cur['value'])
            if key>oldkey: combined[kind]=c
    fields={'death':('recovered_bodies','recovered_update_time','recovered_source','recovered_source_url','recovered_update_iso'),'missing':('missing_minimum','missing_update_time','missing_source','missing_source_url',None),'rescued':('rescued_alive','rescued_update_time','rescued_source','rescued_source_url',None)};winners={}
    for kind,c in combined.items():
        vf,tf,sf,uf,extra=fields[kind];oldstamp=parse_time(old.get(tf));oldv=int(old.get(vf) or 0)
        if c['stamp']<oldstamp: continue
        if c['value']<oldv and not c.get('correction'): continue
        old[vf]=c['value'];old[tf]=c['iso'];old[sf]=c['source'];old[uf]=c['url'];winners[kind]=c['source']
        if extra: old[extra]=c['iso']
        print('winner',kind,c['value'],c['source'],c['url'])
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z');old.setdefault('event','Bhotekoshi flash flood');old.setdefault('event_ne','भोटेकोशी आकस्मिक बाढी');old['updated_date']=datetime.now(timezone.utc).date().isoformat();old['last_checked_utc']=now;old['status']='auto_multisource_fastest_credible';old['sync_sources']=['Nepal Police','Radio Nepal','RONB','Hamro Patro','K cha khabar verified national media'];old['sync_policy']='Use the newest credible cumulative authority-attributed figure. Reject subgroup-only counts, require a stable source timestamp, and do not roll a metric backward unless the source explicitly marks a correction.';old['last_winning_sources']=winners
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
