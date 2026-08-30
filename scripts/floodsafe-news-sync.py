#!/usr/bin/env python3
import html,json,re
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin,urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

OUT=Path('data/floodsafe-news.json')
UA='Mozilla/5.0 (compatible; FloodSafeNepal-News/3.3; +https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/)'
HEADERS={'User-Agent':UA,'Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
NP_DIGITS=str.maketrans('०१२३४५६७८९','0123456789')
SOURCES=(('RONB Post','ronb'),('eKantipur','ekantipur'),('Hamro Patro','hamropatro'),('Radio Nepal','radionepal'))
OLD_BY_URL={}

def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip()
def stamp(s):
 if not s:return 0
 try:return datetime.fromisoformat(str(s).strip().replace('Z','+00:00')).timestamp()
 except:pass
 try:return parsedate_to_datetime(str(s)).timestamp()
 except:return 0
def iso_from_ts(v):return datetime.fromtimestamp(v,timezone.utc).isoformat().replace('+00:00','Z')

def add(out,title,url,t,source,time_exact=True):
 title=clean(title);u=str(url or '').strip();ts=stamp(t)
 if len(title)<12 or not u or not ts:return
 p=urlparse(u)
 if p.scheme not in ('http','https'):return
 x={'title':title,'url':u,'published_at':iso_from_ts(ts),'source':source}
 if not time_exact:x['time_exact']=False
 out.append(x)

def get(url,timeout=16):
 r=requests.get(url,headers=HEADERS,timeout=timeout);r.raise_for_status();return r

def parse_rss(raw,source,base=''):
 out=[]
 try:root=ET.fromstring(raw)
 except:return out
 for x in root.findall('.//item')[:80]:
  add(out,x.findtext('title'),urljoin(base,x.findtext('link') or ''),x.findtext('pubDate') or x.findtext('{http://purl.org/dc/elements/1.1/}date'),source)
 return out

def published_from_html(raw):
 soup=BeautifulSoup(raw,'html.parser')
 for attrs in ({'property':'article:published_time'},{'name':'article:published_time'},{'property':'og:published_time'},{'name':'datePublished'},{'itemprop':'datePublished'},{'name':'pubdate'},{'name':'publish-date'},{'property':'datePublished'}):
  tag=soup.find('meta',attrs=attrs)
  if tag:
   v=tag.get('content') or tag.get('value')
   if stamp(v):return v
 for tm in soup.find_all('time',limit=12):
  v=tm.get('datetime') or tm.get('content') or clean(tm.get_text(' ',strip=True))
  if stamp(v):return v
 for sc in soup.find_all('script',type='application/ld+json',limit=16):
  rawj=sc.string or sc.get_text(' ',strip=True)
  if not rawj:continue
  m=re.search(r'"datePublished"\s*:\s*"([^"]+)"',rawj,re.I)
  if m and stamp(m.group(1)):return m.group(1)
 m=re.search(r'(?:datePublished|published_time)[^0-9]{0,60}(20\d{2}-\d{2}-\d{2}T[^"< ]+)',raw,re.I)
 return m.group(1) if m and stamp(m.group(1)) else None

def article_title(raw,fallback):
 soup=BeautifulSoup(raw,'html.parser');og=soup.find('meta',attrs={'property':'og:title'})
 if og and clean(og.get('content')):return clean(og.get('content'))
 h=soup.find('h1');return clean(h.get_text(' ',strip=True)) if h else clean(fallback)

def verify_page(source,title,url):
 try:
  r=get(url,10);pub=published_from_html(r.text)
  if not pub:return None
  out=[];add(out,article_title(r.text,title),url,pub,source);return out[0] if out else None
 except:return None

def site_candidates(listing_urls,host,max_links=30):
 seen=set();out=[]
 for listing in listing_urls:
  try:r=get(listing)
  except:continue
  soup=BeautifulSoup(r.text,'html.parser')
  for a in soup.find_all('a',href=True):
   title=clean(' '.join(a.stripped_strings));u=urljoin(listing,a.get('href')).split('#')[0];p=urlparse(u)
   if host not in p.netloc.replace('www.',''):continue
   if not re.search(r'/20\d{2}/\d{2}/\d{2}/',p.path):continue
   if len(title)<15 or len(title)>220 or u in seen:continue
   seen.add(u);out.append((title,u))
   if len(out)>=max_links:return out
  # Some publishers hydrate links in JSON/script instead of normal anchors.
  for raw_u in re.findall(r'(?:https?://(?:www\.)?'+re.escape(host)+r')?(/[^"\'<>\s]*/20\d{2}/\d{2}/\d{2}/[^"\'<>\s]+)',r.text,re.I):
   u=urljoin(listing,raw_u).replace('\\/','/').split('#')[0]
   if u in seen:continue
   seen.add(u);out.append(('Latest article',u))
   if len(out)>=max_links:return out
 return out

def verified_candidates(source,cand):
 out=[]
 with ThreadPoolExecutor(max_workers=10) as ex:
  fut=[ex.submit(verify_page,source,t,u) for t,u in cand]
  for f in as_completed(fut):
   x=f.result()
   if x:out.append(x)
 return out

def wp_posts(url,source):
 out=[]
 for x in get(url).json():
  t=x.get('date_gmt') or x.get('modified_gmt') or x.get('date') or x.get('modified') or ''
  if t and not re.search(r'(?:Z|[+-]\d\d:\d\d)$',t,re.I):t+='Z'
  title=x.get('title') or {}
  if isinstance(title,dict):title=title.get('rendered')
  add(out,title,x.get('link'),t,source)
 return out

def fetch_ronb():
 return wp_posts('https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,modified_gmt,link,title','RONB Post')

def first_seen_fallback(source,cand):
 now=datetime.now(timezone.utc);out=[]
 for i,(title,u) in enumerate(cand):
  old=OLD_BY_URL.get(u)
  if old and stamp(old.get('published_at')):
   x=dict(old);x['source']=source;x['time_exact']=False;out.append(x)
  elif title!='Latest article':add(out,title,u,(now-timedelta(seconds=i)).isoformat(),source,time_exact=False)
 return out

def fetch_ekantipur():
 try:
  items=parse_rss(get('https://ekantipur.com/rss').text,'eKantipur','https://ekantipur.com/')
  if items:return items
 except:pass
 cand=site_candidates(('https://ekantipur.com/headlines','https://ekantipur.com/breaking','https://ekantipur.com/news','https://ekantipur.com/'),'ekantipur.com',40)
 if not cand:return []
 exact=verified_candidates('eKantipur',cand)
 if exact:return exact
 return first_seen_fallback('eKantipur',cand)

def rel_minutes(text):
 s=str(text or '').translate(NP_DIGITS).lower()
 for pat,mul in ((r'(\d+)\s*मिनेट\s*अघि',1),(r'(\d+)\s*घण्टा\s*अघि',60),(r'(\d+)\s*(?:min|mins|minute|minutes)\s*ago',1),(r'(\d+)\s*(?:hr|hrs|hour|hours)\s*ago',60)):
  m=re.search(pat,s,re.I)
  if m:return int(m.group(1))*mul,m
 return None,None

def parse_hamropatro_listing(raw,base):
 out=[];now=datetime.now(timezone.utc);soup=BeautifulSoup(raw,'html.parser')
 for a in soup.find_all('a',href=True):
  text=' '.join(a.stripped_strings).strip();mins,_=rel_minutes(text)
  if mins is None or mins>180:continue
  normalized=text.translate(NP_DIGITS)
  mm=re.search(r'(?:\d+\s*मिनेट\s*अघि|\d+\s*घण्टा\s*अघि|\d+\s*(?:min|mins|minute|minutes|hr|hrs|hour|hours)\s*ago)',normalized,re.I)
  if not mm:continue
  title=clean(normalized[mm.end():].lstrip(' ·•|-:'))
  if len(title)<18:continue
  u=urljoin(base,a.get('href'));p=urlparse(u)
  if '/news/detail/' not in p.path:continue
  canonical='https://www.hamropatro.com'+p.path+('?' + p.query if p.query else '')
  add(out,title,canonical,(now-timedelta(minutes=mins)).isoformat(),'Hamro Patro')
 return out

def fetch_hamropatro():
 last=None
 for base in ('https://www.hamropatro.com/news','https://hamropatro.alpha.hamrostack.com/news'):
  try:
   items=parse_hamropatro_listing(get(base).text,base)
   if items:return items
  except Exception as e:last=e
 if last:raise last
 return []

def fetch_radionepal():
 # Radio Nepal is the official public broadcaster; use the official .gov.np site only.
 for url in ('https://radionepal.gov.np/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,modified_gmt,date,modified,link,title',
             'https://radionepal.gov.np/en/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,modified_gmt,date,modified,link,title'):
  try:
   items=wp_posts(url,'Radio Nepal')
   if items:return items
  except:pass
 try:
  items=parse_rss(get('https://radionepal.gov.np/feed/').text,'Radio Nepal','https://radionepal.gov.np/')
  if items:return items
 except:pass
 cand=site_candidates(('https://radionepal.gov.np/','https://radionepal.gov.np/en/'),'radionepal.gov.np',30)
 exact=verified_candidates('Radio Nepal',cand)
 if exact:return exact
 return first_seen_fallback('Radio Nepal',cand)

def main():
 global OLD_BY_URL
 old={}
 if OUT.exists():
  try:old=json.loads(OUT.read_text(encoding='utf-8'))
  except:old={}
 OLD_BY_URL={(x.get('url') or '').split('#')[0]:x for x in old.get('items',[]) if x.get('url')}
 items=[];status={};funcs={'ronb':fetch_ronb,'ekantipur':fetch_ekantipur,'hamropatro':fetch_hamropatro,'radionepal':fetch_radionepal}
 for label,key in SOURCES:
  try:
   got=funcs[key]();ok=bool(got);status[label]={'ok':ok,'items':len(got)}
   if not ok:status[label]['error']='no-verified-items'
   items.extend(got)
  except Exception as e:status[label]={'ok':False,'error':type(e).__name__}

 cut=(datetime.now(timezone.utc)-timedelta(hours=24)).timestamp()
 for x in old.get('items',[]):
  src=x.get('source')
  if isinstance(status.get(src),dict) and not status[src].get('ok') and stamp(x.get('published_at'))>=cut:items.append(x)

 seen_url=set();seen_title=set();ded=[]
 for x in sorted(items,key=lambda z:stamp(z.get('published_at')),reverse=True):
  u=(x.get('url') or '').split('#')[0];k=re.sub(r'\W+',' ',(x.get('title') or '').lower()).strip()
  if not k or u in seen_url or k in seen_title:continue
  seen_url.add(u);seen_title.add(k);ded.append(x)
  if len(ded)>=160:break

 now=datetime.now(timezone.utc);payload={'generated_at':now.isoformat().replace('+00:00','Z'),'refresh_minutes':5,'sources':status,'items':ded}
 old_sig=[(x.get('title'),x.get('url'),x.get('published_at'),x.get('source'),x.get('time_exact',True)) for x in old.get('items',[])];new_sig=[(x.get('title'),x.get('url'),x.get('published_at'),x.get('source'),x.get('time_exact',True)) for x in ded]
 if old_sig==new_sig and old.get('sources')==status and old.get('refresh_minutes')==5:
  print('No headline change');return
 OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Updated',len(ded),'items',status)

if __name__=='__main__':main()
