#!/usr/bin/env python3
import html,json,re,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

OUT=Path('data/floodsafe-people-status.json')
SETU='https://setu.ndrrma.gov.np/admin/recordlist.php'
KCHA='https://kchakhabar.com/api/v1/today.json?limit=100'
UA='FloodSafe-Nepal/1.1 (+https://pujan1234-hub.github.io/assigment/floodsafe-nepal/)'

def fetch_text(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/json;q=0.9,*/*;q=0.8','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8-sig','replace')

def fetch_json(url): return json.loads(fetch_text(url))

def parse_time(v):
    if not v:return 0
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp()
    except:return 0

def digits(s):
    return str(s or '').translate(str.maketrans('०१२३४५६७८९','0123456789')).replace(',','')

def clean_html(raw):
    raw=re.sub(r'(?is)<script.*?</script>|<style.*?</style>',' ',raw)
    raw=re.sub(r'(?s)<[^>]+>','\n',raw)
    return html.unescape(raw)

def setu_counts():
    """Read NDRRMA SETU live Rasuwa records and count current statuses.
    Pages are discovered from links and also probed sequentially. Duplicate pages are ignored.
    """
    counts={'dead':0,'missing':0,'rescued':0,'safe':0,'injured':0}
    seen_pages=set(); seen_fingerprints=set(); max_hint=1
    page=1
    while page<=max(max_hint,1) or page<=40:
        url=SETU if page==1 else SETU+'?'+urllib.parse.urlencode({'page':page})
        try: raw=fetch_text(url)
        except Exception:
            if page==1: raise
            break
        # Stop when server starts repeating the final/first page.
        text=clean_html(raw)
        fingerprint='|'.join(re.findall(r'(?im)^\s*(?:Missing|Rescued|Found\s*-\s*(?:Safe|Dead|Injured))\s*$',text))+'#'+str(len(raw))
        if fingerprint in seen_fingerprints and page>1: break
        seen_fingerprints.add(fingerprint); seen_pages.add(page)
        hints=[int(x) for x in re.findall(r'[?&]page=(\d+)',raw,re.I)]
        if hints:max_hint=max(max_hint,max(hints))
        # Count only standalone status lines from rendered text.
        lines=[re.sub(r'\s+',' ',x).strip() for x in text.splitlines()]
        for line in lines:
            s=line.lower().replace('–','-').replace('—','-')
            if s=='missing':counts['missing']+=1
            elif s=='rescued':counts['rescued']+=1
            elif re.fullmatch(r'found\s*-\s*safe',s):counts['safe']+=1
            elif re.fullmatch(r'found\s*-\s*injured',s):counts['injured']+=1
            elif re.fullmatch(r'found\s*-\s*dead',s):counts['dead']+=1
        # Hard cap, but normally max_hint ends the loop much earlier.
        if page>=max_hint and page>=2:
            # Probe one extra page to catch pagination links hidden on first page.
            if page>=40:break
        page+=1
        if page>40:break
    total=sum(counts.values())
    if total<10: raise RuntimeError(f'SETU parse produced implausible total {total}')
    counts['resolved']=counts['rescued']+counts['safe']+counts['injured']
    counts['total']=total
    counts['pages']=len(seen_pages)
    return counts

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

def authority_media_update(old):
    """Fallback only: authority-attributed Nepal reporting if SETU is temporarily unavailable."""
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
        when=s.get('updated_at') or s.get('first_reported'); stamp=parse_time(when)
        if not stamp:continue
        url=src.get('url') or s.get('url') or ''
        for k in best:
            v=metric(text,k)
            if v is not None and (best[k] is None or stamp>best[k]['stamp']):
                best[k]={'value':v,'stamp':stamp,'iso':when,'source':f'Authority report via {publisher}','url':url}
    fields={'death':('recovered_bodies','recovered_update_iso','recovered_source','recovered_source_url'),'missing':('missing_minimum','missing_update_time','missing_source','missing_source_url'),'rescued':('rescued_alive','rescued_update_time','rescued_source','rescued_source_url')}
    changed=False
    for k,c in best.items():
        if not c:continue
        vf,tf,sf,uf=fields[k]
        if c['stamp']<=parse_time(old.get(tf)):continue
        old[vf]=c['value'];old[tf]=c['iso'];old[sf]=c['source'];old[uf]=c['url'];changed=True
    return changed

def main():
    old=json.loads(OUT.read_text(encoding='utf-8'))
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    changed=False
    try:
        c=setu_counts()
        # SETU is the Government of Nepal / NDRRMA live incident register, so it is primary.
        vals={'recovered_bodies':c['dead'],'missing_minimum':c['missing'],'rescued_alive':c['resolved']}
        for k,v in vals.items():
            if old.get(k)!=v: old[k]=v; changed=True
        old['recovered_source']='NDRRMA SETU live Rasuwa flood register'
        old['missing_source']='NDRRMA SETU live Rasuwa flood register'
        old['rescued_source']='NDRRMA SETU live Rasuwa flood register'
        old['recovered_source_url']=SETU;old['missing_source_url']=SETU;old['rescued_source_url']=SETU
        old['recovered_update_time']=now;old['recovered_update_iso']=now
        old['missing_update_time']=now;old['rescued_update_time']=now
        old['updated_date']=datetime.now(timezone.utc).date().isoformat()
        old['status']='live_official_ndrrma_setu'
        old['setu_breakdown']={'dead':c['dead'],'missing':c['missing'],'rescued':c['rescued'],'found_safe':c['safe'],'found_injured':c['injured'],'resolved_total':c['resolved'],'records_seen':c['total'],'pages_seen':c['pages']}
        changed=True
        print('SETU',c)
    except Exception as e:
        print('SETU unavailable:',repr(e))
        try: changed=authority_media_update(old) or changed
        except Exception as e2: print('Media fallback unavailable:',repr(e2))
    # Always write latest successful check time so the UI can show freshness.
    old['last_checked_utc']=now
    OUT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Human Status written', 'changed' if changed else 'no metric change')

if __name__=='__main__':main()
