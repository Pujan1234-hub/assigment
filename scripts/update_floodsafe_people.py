#!/usr/bin/env python3
import html,json,re,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

OUT=Path('data/floodsafe-people-status.json')
RADIO='https://radionepalonline.com/en/'
KCHA='https://kchakhabar.com/api/v1/today.json?limit=100'
SETU='https://setu.ndrrma.gov.np/admin/recordlist.php'
UA='FloodSafe-Nepal/1.2 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/)'

def fetch_text(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/json;q=0.9,*/*;q=0.8','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=20) as r:return r.read().decode('utf-8-sig','replace')

def fetch_json(url):return json.loads(fetch_text(url))
def strip_html(raw):return re.sub(r'\s+',' ',html.unescape(re.sub(r'(?s)<[^>]+>',' ',re.sub(r'(?is)<script.*?</script>|<style.*?</style>',' ',raw)))).strip()
def digits(s):return str(s or '').translate(str.maketrans('०१२३४५६७८९','0123456789')).replace(',','')
def parse_time(v):
    if not v:return 0
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
    except:return 0

def metrics(text):
    t=digits(text); out={}
    pats={
      'death':[r'(?:death toll|deaths?|confirmed dead|मृत्यु)[^0-9]{0,45}(\d{1,6})',r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,35}(?:confirmed dead|dead|died|मृत्यु)'],
      'missing':[r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,55}(?:remain\s+)?(?:unaccounted for|missing|सम्पर्कविहीन|बेपत्ता)',r'(?:missing|unaccounted|सम्पर्कविहीन|बेपत्ता)[^0-9]{0,45}(\d{1,6})'],
      'rescued':[r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,55}(?:have\s+)?(?:so\s+far\s+)?(?:been\s+)?rescued',r'(?:rescued|उद्धार)[^0-9]{0,45}(\d{1,6})']}
    for k,pp in pats.items():
        for p in pp:
            m=re.search(p,t,re.I)
            if m:
                v=int(m.group(1))
                if v>0:out[k]=v;break
    return out

def radio_candidates():
    raw=fetch_text(RADIO)
    links=[]
    for href,label in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',raw):
        title=strip_html(label)
        if not re.search(r'(bhotekoshi|rasuwa|trishuli|flood|भोटेकोशी|रसुवा|त्रिशूली|बाढी)',title,re.I):continue
        if href.startswith('/'):href=urllib.parse.urljoin(RADIO,href)
        if not href.startswith('https://radionepalonline.com/'):continue
        if href not in [x[0] for x in links]:links.append((href,title))
    return links[:35]

def latest_radio_metrics():
    best={}
    for url,title in radio_candidates():
        try: raw=fetch_text(url)
        except Exception:continue
        text=strip_html(raw)
        if not re.search(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|Authority|प्राधिकरण)',text,re.I):continue
        mm=metrics(title+' '+text)
        if not mm:continue
        # Article URLs contain publication date; use page metadata if available, else URL date.
        dm=re.search(r'/(20\d\d)/(\d\d)/(\d\d)/',url)
        stamp=datetime(int(dm.group(1)),int(dm.group(2)),int(dm.group(3)),23,59,tzinfo=timezone.utc).timestamp() if dm else 0
        iso=datetime.fromtimestamp(stamp,timezone.utc).isoformat() if stamp else datetime.now(timezone.utc).isoformat()
        for k,v in mm.items():
            # Same-day article order can be ambiguous, so prefer larger cumulative totals on equal date.
            cur=best.get(k)
            if cur is None or stamp>cur['stamp'] or (stamp==cur['stamp'] and v>cur['value']):
                best[k]={'value':v,'stamp':stamp,'iso':iso,'source':'NDRRMA / Nepal Police via Public Service Broadcasting Radio Nepal','url':url}
    return best

def kcha_metrics():
    best={}; j=fetch_json(KCHA)
    for s in j.get('stories') or []:
        text=' '.join(str(s.get(k) or '') for k in ('topic_ne','topic_en','summary_ne','summary_en'))
        if not re.search(r'(rasuwa|bhotekoshi|bhote\s*koshi|trishuli|रसुवा|भोटेकोशी|त्रिशूली)',text,re.I):continue
        if not re.search(r'(flood|बाढी)',text,re.I):continue
        src=(s.get('sources') or [{}])[0]; publisher=src.get('publisher') or s.get('source') or 'Nepal media'
        if not re.search(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|प्राधिकरण|police)',text+' '+publisher,re.I):continue
        when=s.get('updated_at') or s.get('first_reported'); stamp=parse_time(when)
        for k,v in metrics(text).items():
            cur=best.get(k)
            if cur is None or stamp>cur['stamp']:
                best[k]={'value':v,'stamp':stamp,'iso':when,'source':f'Authority report via {publisher}','url':src.get('url') or s.get('url') or ''}
    return best

def main():
    old=json.loads(OUT.read_text(encoding='utf-8'))
    combined={}
    for loader in (latest_radio_metrics,kcha_metrics):
        try:
            got=loader()
            for k,c in got.items():
                cur=combined.get(k)
                if cur is None or c['stamp']>cur['stamp'] or (c['stamp']==cur['stamp'] and c['value']>cur['value']):combined[k]=c
        except Exception as e:print(loader.__name__,'failed:',repr(e))
    fields={'death':('recovered_bodies','recovered_update_iso','recovered_update_time','recovered_source','recovered_source_url'),'missing':('missing_minimum','missing_update_time','missing_update_time','missing_source','missing_source_url'),'rescued':('rescued_alive','rescued_update_time','rescued_update_time','rescued_source','rescued_source_url')}
    changed=False
    for k,c in combined.items():
        vf,tf,tf2,sf,uf=fields[k]
        # Never replace a newer aggregate with an older article. Same-day cumulative totals may only rise here.
        oldstamp=parse_time(old.get(tf)); oldv=int(old.get(vf) or 0)
        if c['stamp']<oldstamp:continue
        if c['stamp']==oldstamp and c['value']<=oldv:continue
        old[vf]=c['value'];old[tf]=c['iso'];old[tf2]=c['iso'];old[sf]=c['source'];old[uf]=c['url'];changed=True
        print(k,c['value'],c['url'])
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    old['last_checked_utc']=now;old['updated_date']=datetime.now(timezone.utc).date().isoformat();old['status']='auto_authority_aggregate'
    old.pop('setu_breakdown',None)
    OUT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Human Status sync complete', 'metrics changed' if changed else 'no newer aggregate')

if __name__=='__main__':main()
