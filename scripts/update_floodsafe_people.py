#!/usr/bin/env python3
import json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path

OUT=Path('data/floodsafe-people-status.json')
KCHA='https://kchakhabar.com/api/v1/today.json?limit=100'
UA='FloodSafe-Nepal/1.0 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/)'

def fetch_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read().decode('utf-8-sig'))

def parse_time(v):
    if not v:return 0
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
    except:return 0

def digits(s):
    table=str.maketrans('०१२३४५६७८९','0123456789')
    return str(s or '').translate(table).replace(',','')

def metric(text,kind):
    t=digits(text)
    pats={
      'death':[r'(\d{1,6})\s+(?:bodies|body)\s+(?:have\s+been\s+)?(?:recovered|retrieved)',r'(?:death toll|deaths?|मृत्यु)[^0-9]{0,25}(\d{1,6})',r'(\d{1,6})\s*(?:people|persons|जना)?[^।.]{0,25}(?:dead|died|मृत्यु)'],
      'missing':[r'(\d{1,6})\s+(?:people[^.]{0,45})?(?:remain\s+)?(?:missing|unaccounted)',r'(?:missing|unaccounted)[^0-9]{0,25}(\d{1,6})',r'(\d{1,6})\s*(?:जना)?[^।.]{0,35}(?:सम्पर्कविहीन|बेपत्ता)'],
      'rescued':[r'(\d{1,6})\s+(?:people[^.]{0,35})?(?:have\s+)?(?:so\s+far\s+)?(?:been\s+)?rescued',r'(?:rescued|उद्धार)[^0-9]{0,25}(\d{1,6})',r'(\d{1,6})\s*(?:जना)?[^।.]{0,30}उद्धार']}
    for p in pats[kind]:
        m=re.search(p,t,re.I)
        if m:
            try:return int(m.group(1))
            except:pass
    return None

def main():
    old=json.loads(OUT.read_text(encoding='utf-8'))
    j=fetch_json(KCHA);stories=j.get('stories') or []
    best={'death':None,'missing':None,'rescued':None}
    for s in stories:
        text=' '.join(str(s.get(k) or '') for k in ('topic_ne','topic_en','summary_ne','summary_en'))
        if not re.search(r'(rasuwa|bhotekoshi|bhote\s*koshi|trishuli|रसुवा|भोटेकोशी|त्रिशूली)',text,re.I):continue
        if not re.search(r'(flood|बाढी)',text,re.I):continue
        src=(s.get('sources') or [{}])[0]
        publisher=src.get('publisher') or s.get('source') or 'Nepal media'
        authority=bool(re.search(r'(NDRRMA|National Disaster Risk Reduction|Nepal Police|नेपाल प्रहरी|विपद् जोखिम न्यूनीकरण|according to police|police said)',text+' '+publisher,re.I))
        if not authority:continue
        when=s.get('updated_at') or s.get('first_reported')
        stamp=parse_time(when)
        if not stamp:continue
        url=src.get('url') or s.get('url') or ''
        for k in best:
            v=metric(text,k)
            if v is None:continue
            if best[k] is None or stamp>best[k]['stamp']:
                best[k]={'value':v,'stamp':stamp,'iso':when,'source':f'Authority report via {publisher}','url':url}
    changed=False
    fields={
      'death':('recovered_bodies','recovered_update_iso','recovered_source','recovered_source_url'),
      'missing':('missing_minimum','missing_update_time','missing_source','missing_source_url'),
      'rescued':('rescued_alive','rescued_update_time','rescued_source','rescued_source_url')}
    for k,c in best.items():
        if not c:continue
        vf,tf,sf,uf=fields[k]
        if c['stamp']<=parse_time(old.get(tf)):continue
        old[vf]=c['value'];old[tf]=c['iso'];old[sf]=c['source'];old[uf]=c['url'];changed=True
        print(k,c['value'],c['iso'],c['source'])
    if changed:
        old['updated_date']=datetime.now(timezone.utc).date().isoformat()
        old['status']='verified_multi_source'
        OUT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Human Status updated')
    else:print('No newer Human Status metrics')

if __name__=='__main__':main()
