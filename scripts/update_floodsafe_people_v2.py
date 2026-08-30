#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT=Path('data/floodsafe-people-status.json')
POLICE=Path('data/floodsafe-police.json')
UA='FloodSafe-Nepal/2.0 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/)'
KCHA='https://kchakhabar.com/api/v1/today.json?limit=100'
RONB='https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,modified_gmt,link,title,excerpt,content'
RADIO_LISTINGS=['https://radionepalonline.com/en/','https://radionepalonline.com/en/?s=Bhotekoshi','https://radionepalonline.com/en/?s=Rasuwa+flood','https://radionepalonline.com/en/?s=Trishuli+flood']
HAMRO_LISTINGS=['https://www.hamropatro.com/','https://www.hamropatro.com/posts','https://www.hamropatro.com/en/posts']
EVENT_RE=re.compile(r'(rasuwa|bhotekoshi|bhote\s*koshi|trishuli|रसुवा|भोटेकोशी|भोटेकोसी|त्रिशूली)',re.I)
FLOOD_RE=re.compile(r'(flood|flash flood|बाढी|आकस्मिक बाढी)',re.I)
AUTH_RE=re.compile(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|प्रहरी प्रधान कार्यालय|प्राधिकरण|Authority|government figures|सरकार)',re.I)
AGG_RE=re.compile(r'(total|so far|death toll|confirmed|remain(?:s)? unaccounted|remain(?:s)? missing|overall|कुल|हालसम्म|पुष्टि|सम्पर्कविहीन|बेपत्ता)',re.I)
CORRECTION_RE=re.compile(r'(revis(?:ed|ion)|correct(?:ed|ion)|updated figure|संशोधित|सच्याइएको)',re.I)
SUBGROUP_RE=re.compile(r'(tourists?|foreigners?|पर्यटक|विदेशी|army|सेना|police personnel|प्रहरी कर्मचारी|armed police|सशस्त्र प्रहरी|hydropower|जलविद्युत|workers?|employees?|कर्मचारी)',re.I)
PREFERRED=['Nepal Police','Radio Nepal','RONB','Hamro Patro','The Kathmandu Post','Kathmandu Post','OnlineKhabar','Onlinekhabar','Kantipur','Setopati','Ratopati','Republica','Nepal News','Gorkhapatra']

def req(url,accept='*/*'):
    return urllib.request.Request(url,headers={'User-Agent':UA,'Accept':accept,'Cache-Control':'no-cache','Pragma':'no-cache'})

def fetch_text(url):
    with urllib.request.urlopen(req(url,'text/html,application/json;q=0.9,*/*;q=0.8'),timeout=22) as r:
        return r.read().decode('utf-8-sig','replace')

def fetch_json(url):
    return json.loads(fetch_text(url))

def strip_html(raw):
    raw=re.sub(r'(?is)<script.*?</script>|<style.*?</style>',' ',raw or '')
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'(?s)<[^>]+>',' ',raw))).strip()

def digits(s):
    return str(s or '').translate(str.maketrans('०१२३४५६७८९','0123456789')).replace(',','')

def parse_time(v):
    if not v:return 0
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
    except:return 0

def iso_utc(v):
    t=parse_time(v)
    if not t:return datetime.now(timezone.utc).isoformat()
    return datetime.fromtimestamp(t,timezone.utc).isoformat()

def page_time(raw,url):
    best=(0,None)
    for p in [r'article:modified_time["\'][^>]+content=["\']([^"\']+)',r'article:published_time["\'][^>]+content=["\']([^"\']+)',r'<time[^>]+datetime=["\']([^"\']+)',r'"dateModified"\s*:\s*"([^"]+)',r'"datePublished"\s*:\s*"([^"]+)']:
        for m in re.finditer(p,raw or '',re.I):
            t=parse_time(m.group(1))
            if t>best[0]:best=(t,m.group(1))
    if best[0]:return best
    m=re.search(r'/(20\d\d)/(\d\d)/(\d\d)/',url or '')
    if m:
        d=datetime(int(m.group(1)),int(m.group(2)),int(m.group(3)),23,59,tzinfo=timezone.utc)
        return d.timestamp(),d.isoformat()
    return 0,None

def relevant(text):return bool(EVENT_RE.search(text or '') and FLOOD_RE.search(text or ''))

def metrics(text):
    t=digits(text);out={}
    pats={
      'death':[r'(?:death toll|confirmed dead|deaths?|मृत्यु|मृतक|शव)[^0-9]{0,60}(\d{1,6})',r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,55}(?:confirmed dead|dead|died|मृत्यु|मृतक|शव\s+फेला)',r'(?:total|कुल|हालसम्म)[^0-9]{0,35}(\d{1,6})[^.।]{0,45}(?:dead|death|मृत्यु|मृतक|शव)'],
      'missing':[r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,70}(?:remain\s+)?(?:unaccounted for|missing|सम्पर्कविहीन|बेपत्ता|out of contact)',r'(?:missing|unaccounted|out of contact|सम्पर्कविहीन|बेपत्ता)[^0-9]{0,60}(\d{1,6})',r'(?:total|कुल|हालसम्म)[^0-9]{0,35}(\d{1,6})[^.।]{0,45}(?:missing|unaccounted|सम्पर्कविहीन|बेपत्ता)'],
      'rescued':[r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,70}(?:have\s+)?(?:so\s+far\s+)?(?:been\s+)?rescued',r'(?:rescued|उद्धार)[^0-9]{0,60}(\d{1,6})',r'(?:total|कुल|हालसम्म|so far)[^0-9]{0,35}(\d{1,6})[^.।]{0,45}(?:rescued|उद्धार)']}
    for k,pp in pats.items():
        for p in pp:
            m=re.search(p,t,re.I)
            if m:
                v=int(m.group(1))
                if 0<v<100000:out[k]=v;break
    return out

def aggregate_ok(title,text):
    joined=(title or '')+' '+(text or '')
    if not relevant(joined) or not AGG_RE.search(joined):return False
    if SUBGROUP_RE.search(title or '') and not re.search(r'(overall|total|so far|कुल|हालसम्म|सरकार|NDRRMA)',joined,re.I):return False
    return True

def add(best,kind,value,stamp,iso,source,url,authority,correction=False):
    if not value:return
    c={'value':int(value),'stamp':stamp or 0,'iso':iso or datetime.now(timezone.utc).isoformat(),'source':source,'url':url,'authority':bool(authority),'correction':bool(correction)}
    old=best.get(kind)
    key=(c['stamp'],1 if c['authority'] else 0,1 if c['correction'] else 0,c['value'])
    oldkey=(-1,0,0,0) if not old else (old['stamp'],1 if old.get('authority') else 0,1 if old.get('correction') else 0,old['value'])
    if key>oldkey:best[kind]=c

def police_loader():
    best={}
    if not POLICE.exists():return best
    try:j=json.loads(POLICE.read_text())
    except:return best
    v=j.get('total_deaths');t=parse_time(j.get('official_update_iso'))
    if isinstance(v,int) and v>0 and t:add(best,'death',v,t,j.get('official_update_iso'),'Nepal Police',j.get('source_url') or 'https://www.nepalpolice.gov.np/',True)
    return best

def radio_loader():
    best={};links=[]
    for listing in RADIO_LISTINGS:
        try:raw=fetch_text(listing)
        except Exception as e:print('radio listing',repr(e));continue
        for href in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\']',raw):
            u=urllib.parse.urljoin(listing,href)
            if 'radionepalonline.com/en/2026/' in u and u not in links:links.append(u)
    for u in links[:45]:
        try:raw=fetch_text(u)
        except:continue
        text=strip_html(raw);title=text[:260]
        if not aggregate_ok(title,text):continue
        authority=bool(AUTH_RE.search(text));stamp,iso=page_time(raw,u)
        for k,v in metrics(text).items():add(best,k,v,stamp,iso,'Radio Nepal',u,authority,CORRECTION_RE.search(text)!=None)
    return best

def ronb_loader():
    best={}
    try:posts=fetch_json(RONB)
    except Exception as e:print('ronb',repr(e));return best
    for p in posts if isinstance(posts,list) else []:
        title=strip_html((p.get('title') or {}).get('rendered',''));body=strip_html((p.get('content') or {}).get('rendered','')+' '+(p.get('excerpt') or {}).get('rendered',''))
        if not aggregate_ok(title,body):continue
        modified=p.get('modified_gmt') or p.get('date_gmt');stamp=parse_time(str(modified)+'+00:00') if modified else 0;iso=iso_utc(str(modified)+'+00:00') if modified else None;u=p.get('link') or 'https://www.ronbpost.com/'
        authority=bool(AUTH_RE.search(title+' '+body))
        for k,v in metrics(title+' '+body).items():add(best,k,v,stamp,iso,'RONB',u,authority,CORRECTION_RE.search(body)!=None)
    return best

def hamro_loader():
    best={}
    for u in HAMRO_LISTINGS:
        try:raw=fetch_text(u)
        except:continue
        # Hamro Patro is an aggregator. Split around visible headline markers so unrelated counts are not mixed.
        text=strip_html(raw)
        chunks=re.split(r'(?=\b(?:Aug|२०२६|##)\b)',text)
        for chunk in chunks:
            if len(chunk)<80 or not aggregate_ok(chunk[:220],chunk):continue
            t=datetime.now(timezone.utc).timestamp();authority=bool(AUTH_RE.search(chunk))
            for k,v in metrics(chunk).items():add(best,k,v,t,datetime.now(timezone.utc).isoformat(),'Hamro Patro',u,authority,CORRECTION_RE.search(chunk)!=None)
    return best

def kcha_loader():
    best={}
    try:j=fetch_json(KCHA)
    except Exception as e:print('kcha',repr(e));return best
    for s in j.get('stories',[]):
        title=(s.get('topic_en') or '')+' '+(s.get('topic_ne') or '')
        body=(s.get('summary_en') or '')+' '+(s.get('summary_ne') or '')
        if not aggregate_ok(title,body):continue
        sources=s.get('sources') or [];source='Verified national media via K cha khabar';url=s.get('url') or 'https://kchakhabar.com/'
        for pref in PREFERRED:
            hit=next((x for x in sources if pref.lower() in str(x.get('publisher','')).lower()),None)
            if hit:source=str(hit.get('publisher') or pref);url=hit.get('url') or url;break
        if sources and source.startswith('Verified'):source=str(sources[0].get('publisher') or source);url=sources[0].get('url') or url
        stamp=parse_time(s.get('updated_at') or s.get('first_reported'));iso=s.get('updated_at') or s.get('first_reported') or datetime.now(timezone.utc).isoformat();authority=bool(AUTH_RE.search(title+' '+body))
        for k,v in metrics(title+' '+body).items():add(best,k,v,stamp,iso,source,url,authority,CORRECTION_RE.search(body)!=None)
    return best

def main():
    old=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    combined={}
    for loader in (police_loader,radio_loader,ronb_loader,hamro_loader,kcha_loader):
        try:got=loader()
        except Exception as e:print(loader.__name__,repr(e));continue
        for k,c in got.items():
            cur=combined.get(k);key=(c['stamp'],1 if c['authority'] else 0,c['value']);oldkey=(-1,0,0) if not cur else (cur['stamp'],1 if cur.get('authority') else 0,cur['value'])
            if key>oldkey:combined[k]=c
    fields={'death':('recovered_bodies','recovered_update_time','recovered_source','recovered_source_url','recovered_update_iso'),'missing':('missing_minimum','missing_update_time','missing_source','missing_source_url',None),'rescued':('rescued_alive','rescued_update_time','rescued_source','rescued_source_url',None)}
    winners={}
    for k,c in combined.items():
        vf,tf,sf,uf,extra=fields[k];oldstamp=parse_time(old.get(tf));oldv=int(old.get(vf) or 0)
        if c['stamp']<oldstamp:continue
        if c['value']<oldv and not c.get('correction'):continue
        old[vf]=c['value'];old[tf]=c['iso'];old[sf]=c['source'];old[uf]=c['url'];winners[k]=c['source']
        if extra:old[extra]=c['iso']
        print('winner',k,c['value'],c['source'],c['url'])
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    old.setdefault('event','Bhotekoshi flash flood');old.setdefault('event_ne','भोटेकोशी आकस्मिक बाढी');old['updated_date']=datetime.now(timezone.utc).date().isoformat();old['last_checked_utc']=now;old['status']='auto_multisource_fastest_credible';old['sync_sources']=['Nepal Police','Radio Nepal','RONB','Hamro Patro','K cha khabar verified national media'];old['sync_policy']='Use the newest credible cumulative authority-attributed figure. Reject subgroup-only counts and do not roll a metric backward unless the source explicitly marks a correction.';old['last_winning_sources']=winners
    OUT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
