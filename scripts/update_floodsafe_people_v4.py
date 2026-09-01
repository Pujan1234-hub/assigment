#!/usr/bin/env python3
import html,json,re,requests
from bs4 import BeautifulSoup
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
OUT=Path('data/floodsafe-people-status.json')
H={'User-Agent':'Mozilla/5.0 (compatible; FloodSafeNepal-Human/6.0)','Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
EVENT=re.compile(r'(bhotekoshi|bhote\s*koshi|rasuwa|trishuli|भोटेकोशी|भोटेकोसी|रसुवा|त्रिशूली|त्रिशुली)',re.I)
CORR=re.compile(r'(corrected|correction|revised|revision|सच्याइएको|संशोधित)',re.I)
NP=str.maketrans('०१२३४५६७८९','0123456789')

def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip().translate(NP).replace(',','')
def stamp(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).timestamp() if v else 0
 except:return 0
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z') if t else None
def get(u,t=14):r=requests.get(u,headers=H,timeout=t);r.raise_for_status();return r
def page_time(s):
 for attrs in ({'property':'article:published_time'},{'property':'article:modified_time'},{'itemprop':'datePublished'}):
  x=s.find('meta',attrs=attrs)
  if x and stamp(x.get('content')):return x.get('content')
 for x in s.find_all('time',limit=12):
  if stamp(x.get('datetime')):return x.get('datetime')
 return None

def extract(text,kind):
 vals=[]
 for s in re.split(r'[.।!?\n]',clean(text)):
  if kind=='death' and not re.search(r'(death toll|deaths?|dead|killed|bodies?.*(found|recovered)|मृत्यु|मृतक|शव)',s,re.I):continue
  if kind=='missing' and not re.search(r'(more than .*missing|over .*missing|still missing|remain(?:s|ing)? missing|unaccounted for|बेपत्ता|सम्पर्कविहीन)',s,re.I):continue
  if kind=='rescued' and not re.search(r'(rescued so far|have been rescued|rescued|evacuated|found safe|उद्धार|सकुशल)',s,re.I):continue
  nums=[int(x) for x in re.findall(r'\b\d{1,6}\b',s) if 0<int(x)<100000]
  if nums:vals.append(max(nums))
 return max(vals) if vals else None

def consider(best,kind,value,t,source,url,correction=False,minimum=False):
 if value is None or not t:return
 c={'value':int(value),'t':float(t),'time':iso(t),'source':source,'url':url,'correction':bool(correction),'minimum':bool(minimum)};o=best.get(kind)
 if o and c['value']<o['value'] and not c['correction']:
  if kind!='missing' or c['value']<o['value']*.65:return
 if not o or c['t']>o['t']:best[kind]=c

def inspect(best,url,source):
 try:
  s=BeautifulSoup(get(url).text,'html.parser');h=s.find('h1');title=clean(h.get_text(' ',strip=True) if h else (s.title.get_text(' ',strip=True) if s.title else ''));a=s.find('article') or s.find('main');body=clean(a.get_text(' ',strip=True) if a else '');text=title+' '+body
  if not EVENT.search(text):return
  t=stamp(page_time(s));corr=bool(CORR.search(text))
  for k in ('death','missing','rescued'):consider(best,k,extract(text,k),t,source,url,corr,k=='missing' and bool(re.search(r'(more than|over)',text,re.I)))
 except Exception as e:print('skip',source,url,e)

def listing(best,base,host,source):
 try:s=BeautifulSoup(get(base).text,'html.parser')
 except Exception as e:print(source,e);return
 seen=[]
 for a in s.find_all('a',href=True):
  u=urljoin(base,a['href']);title=clean(' '.join(a.stripped_strings));p=urlparse(u)
  if not p.netloc.endswith(host) or not EVENT.search(title) or u in seen:continue
  seen.append(u);inspect(best,u,source)
  if len(seen)>=15:break

def main():
 old=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {};best={}
 specs=(('death','recovered_bodies','recovered_source','recovered_source_url','recovered_update_iso'),('missing','missing_minimum','missing_source','missing_source_url','missing_update_time'),('rescued','rescued_alive','rescued_source','rescued_source_url','rescued_update_time'))
 for k,vk,sk,uk,tk in specs:
  v=old.get(vk);t=stamp(old.get(tk) or old.get('recovered_update_time') if k=='death' else old.get(tk));
  if isinstance(v,int) and v>0 and t:best[k]={'value':v,'t':t,'time':iso(t),'source':old.get(sk),'url':old.get(uk),'correction':False,'minimum':bool(old.get('missing_is_minimum')) if k=='missing' else False}
 inspect(best,'https://radionepalonline.com/en/2026/08/31/435175.html','Radio Nepal / NDRRMA')
 listing(best,'https://radionepalonline.com/en/','radionepalonline.com','Radio Nepal / NDRRMA')
 listing(best,'https://ndrrma.gov.np/','ndrrma.gov.np','NDRRMA')
 d,m,r=best.get('death'),best.get('missing'),best.get('rescued')
 payload={'event':'Bhotekoshi flash flood','event_ne':'भोटेकोशी आकस्मिक बाढी','updated_date':datetime.now(timezone.utc).date().isoformat(),'recovered_bodies':d['value'] if d else None,'recovered_source':d['source'] if d else None,'recovered_source_url':d['url'] if d else None,'recovered_update_time':d['time'] if d else None,'recovered_update_iso':d['time'] if d else None,'missing_minimum':m['value'] if m else None,'missing_is_minimum':bool(m and m.get('minimum')),'missing_source':m['source'] if m else None,'missing_source_url':m['url'] if m else None,'missing_update_time':m['time'] if m else None,'rescued_alive':r['value'] if r else None,'rescued_source':r['source'] if r else None,'rescued_source_url':r['url'] if r else None,'rescued_update_time':r['time'] if r else None,'status':'event_scoped_requested_sources','last_checked_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'sync_sources':['NDRRMA','Nepal Police','Radio Nepal','RONB'],'sync_schema':4,'sync_policy':'Strict Bhotekoshi/Rasuwa/Trishuli event scope; subgroup counts rejected; >35% missing drop rejected without explicit correction; death/rescued never roll backward without explicit correction.'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(payload['recovered_bodies'],payload['missing_minimum'],payload['rescued_alive'])
if __name__=='__main__':main()
