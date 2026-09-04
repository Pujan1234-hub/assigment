#!/usr/bin/env python3
import html,json,re,requests
from bs4 import BeautifulSoup
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
OUT=Path('data/floodsafe-people-status.json')
H={'User-Agent':'Mozilla/5.0 (compatible; FloodSafeNepal-Human/6.0)','Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
EVENT=re.compile(r'(bhotekoshi|bhote\s*koshi|rasuwa|trishuli|भोटेकोशी|भोटेकोसी|रसुवा|त्रिशूली|त्रिशुली)',re.I)
CORR=re.compile(r'(corrected|correction|revised|revision|सच्याइएको|संशोधित)',re.I)
AUTHORITY=re.compile(r'(NDRRMA|National Disaster Risk Reduction|राष्ट्रिय विपद् जोखिम न्यूनीकरण|नेपाल प्रहरी|सशस्त्र प्रहरी|प्राधिकरण)',re.I)
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
 text=clean(s.get_text(' ',strip=True))
 m=re.search(r'2083\s+भदौ\s+(\d{1,2})\s+गते\s+(\d{1,2}):(\d{2})',text)
 if m:
  day,hour,minute=map(int,m.groups())
  if 1<=day<=32 and hour<24 and minute<60:
   return (datetime(2026,8,16+day,hour,minute,tzinfo=timezone.utc)-timedelta(hours=5,minutes=45)).isoformat()
 return None

def numberize(text):
 s=clean(text)
 def lakh(m):return str(int(m.group(1))*100000+int(m.group(2) or 0)*1000+int(m.group(3) or 0))
 def thousand(m):return str(int(m.group(1))*1000+int(m.group(2) or 0))
 s=re.sub(r'(\d{1,3})\s*(?:लाख|lakh)\s*(?:(\d{1,3})\s*(?:हजार|thousand))?\s*(\d{1,3})?',lakh,s,flags=re.I)
 return re.sub(r'(\d{1,3})\s*(?:हजार|thousand)\s*(\d{1,3})?',thousand,s,flags=re.I)

def extract(text,kind):
 s=numberize(text)
 patterns={
  'death':(r'death toll\s+(?:(?:(?:has|had)\s+)?(?:risen|increased|climbed)\s+to|(?:(?:has|had)\s+)?reached|stands?\s+at|is|of)\s+(\d+)\b',r'bodies\s+of\s+(\d+)\s+(?:people|persons)\s+who\s+died',r'total\s+of\s+(\d+)\s+(?:people|persons)\s+(?:have\s+died|were\s+killed)',r'(?:मृत्यु\s+हुनेको\s+संख्या|मृतक\s+संख्या)\s*(\d+)\b',r'(\d+)\s*जनाको\s+(?:शव\s+(?:फेला|भेटि)|मृत्यु)'),
  'missing':(r'(?:more than|over|total of)\s+(\d+)\s+(?:people|persons)\b[^.!?।]{0,220}?\b(?:still\s+|remain\s+|are\s+)?missing',r'(\d+)\s+(?:people\s+)?(?:still\s+)?(?:remain|are)\s+(?:unaccounted(?:\s+for)?|missing)',r'(\d+)\s+(?:people|persons)\s+(?:are\s+)?(?:still|remain)\s+missing',r'(?:अझै|हालसम्म)?\s*(\d+)\s*जना\s+(?:अझै\s+)?(?:सम्पर्कविहीन|बेपत्ता)'),
  'rescued':(r'(\d+)\s+(?:people|persons)\b[^.!?।]{0,100}?\bhad\s+been\s+rescued',r'(?:total of)\s+(\d+)\b[^.!?।]{0,100}?\brescued',r'(?:हालसम्म[^.!?।]{0,120}?)?(\d+)\s*जनाको\s+उद्धार',r'(\d+)\s*(?:को|जनालाई)\s+उद्धार')
 }
 vals={int(m.group(1)) for p in patterns.get(kind,()) for m in re.finditer(p,s,re.I)}
 return next(iter(vals)) if len(vals)==1 else None

def consider(best,kind,value,t,source,url,correction=False,minimum=False):
 if value is None or not t:return
 c={'value':int(value),'t':float(t),'time':iso(t),'source':source,'url':url,'correction':bool(correction),'minimum':bool(minimum)};o=best.get(kind)
 if o and c['value']<o['value'] and not c['correction']:
  if kind!='missing' or c['value']<o['value']*.65:return
 if not o or c['t']>o['t']:best[kind]=c

def inspect(best,url,source,require_authority=False):
 try:
  s=BeautifulSoup(get(url).text,'html.parser');h=s.find('h1');title=clean(h.get_text(' ',strip=True) if h else (s.title.get_text(' ',strip=True) if s.title else ''));a=s.find('article') or s.find('main');body=clean(a.get_text(' ',strip=True) if a else '');text=title+' '+body
  if not EVENT.search(text) or require_authority and not AUTHORITY.search(text):return
  t=stamp(page_time(s));corr=bool(CORR.search(text))
  for k in ('death','missing','rescued'):consider(best,k,extract(text,k),t,source,url,corr,k=='missing' and bool(re.search(r'(more than|over|भन्दा बढी)',text,re.I)))
 except Exception as e:print('skip',source,url,e)

def listing(best,base,host,source,require_authority=False):
 try:s=BeautifulSoup(get(base).text,'html.parser')
 except Exception as e:print(source,e);return
 seen=[]
 for a in s.find_all('a',href=True):
  u=urljoin(base,a['href']);title=clean(' '.join(a.stripped_strings));p=urlparse(u)
  if not p.netloc.endswith(host) or not EVENT.search(title) or u in seen:continue
  seen.append(u);inspect(best,u,source,require_authority)
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
 inspect(best,'https://www.onlinekhabar.com/2026/09/2009006/rasuwa-flood-death-toll-reaches-1114','NDRRMA via OnlineKhabar',True)
 listing(best,'https://www.onlinekhabar.com/trend/bhotekoshi-flood','onlinekhabar.com','NDRRMA via OnlineKhabar',True)
 # Independent Nepal newsrooms are used only when their report explicitly attributes
 # an event-wide total to NDRRMA/Nepal Police. This prevents a local subgroup count
 # becoming a national total.
 media=(
  ('https://myrepublica.nagariknetwork.com/news/bhotekoshi-flood-11993-rescued-4216-still-missing-96-15.html','NDRRMA via MyRepublica'),
  ('https://thehimalayantimes.com/ampArticle/1040101','NDRRMA via The Himalayan Times'),
  ('https://www.b360nepal.com/detail/29939/bhotekoshi-floods-11993-people-rescued-4216-reported-missing','NDRRMA via B360 Nepal'),
  ('https://english.nepalnews.com/s/nation/bhotekoshi-flood-4216-people-still-missing/','NDRRMA via Nepal News'),
 )
 for url,source in media:inspect(best,url,source,True)
 for base,host,source in (
  ('https://myrepublica.nagariknetwork.com/','myrepublica.nagariknetwork.com','NDRRMA via MyRepublica'),
  ('https://thehimalayantimes.com/','thehimalayantimes.com','NDRRMA via The Himalayan Times'),
  ('https://www.b360nepal.com/','b360nepal.com','NDRRMA via B360 Nepal'),
  ('https://english.nepalnews.com/','english.nepalnews.com','NDRRMA via Nepal News'),
 ):listing(best,base,host,source,True)
 d,m,r=best.get('death'),best.get('missing'),best.get('rescued')
 payload={'event':'Bhotekoshi flash flood','event_ne':'भोटेकोशी आकस्मिक बाढी','updated_date':datetime.now(timezone.utc).date().isoformat(),'recovered_bodies':d['value'] if d else None,'recovered_source':d['source'] if d else None,'recovered_source_url':d['url'] if d else None,'recovered_update_time':d['time'] if d else None,'recovered_update_iso':d['time'] if d else None,'missing_minimum':m['value'] if m else None,'missing_is_minimum':bool(m and m.get('minimum')),'missing_source':m['source'] if m else None,'missing_source_url':m['url'] if m else None,'missing_update_time':m['time'] if m else None,'rescued_alive':r['value'] if r else None,'rescued_source':r['source'] if r else None,'rescued_source_url':r['url'] if r else None,'rescued_update_time':r['time'] if r else None,'status':'event_scoped_requested_sources','last_checked_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'sync_sources':['NDRRMA','OnlineKhabar','Radio Nepal','RONB','MyRepublica','The Himalayan Times','B360 Nepal','Nepal News'],'sync_schema':4,'sync_policy':'Newest explicit event-wide authority-attributed total wins. Nepali thousand/lakh totals are parsed only when attached to deaths, missing or rescued outcomes; subgroup counts and BS years cannot become totals.'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(payload['recovered_bodies'],payload['missing_minimum'],payload['rescued_alive'])
if __name__=='__main__':main()
