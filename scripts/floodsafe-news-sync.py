#!/usr/bin/env python3
import html,json,re
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin,urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

OUT=Path('data/floodsafe-news.json')
UA='Mozilla/5.0 (compatible; FloodSafeNepal-News/3.0; +https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/)'
HEADERS={'User-Agent':UA,'Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
NPT=timezone(timedelta(hours=5,minutes=45))
NP_DIGITS=str.maketrans('०१२३४५६७८९','0123456789')

SOURCES=(
 ('RONB Post','ronb'),
 ('eKantipur','ekantipur'),
 ('Hamro Patro','hamropatro'),
 ('Radio Nepal','radionepal'),
)

def clean(s):
 return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip()

def stamp(s):
 if not s:return 0
 try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).timestamp()
 except:pass
 try:return parsedate_to_datetime(str(s)).timestamp()
 except:return 0

def iso_from_ts(v):
 return datetime.fromtimestamp(v,timezone.utc).isoformat().replace('+00:00','Z')

def add(out,title,url,t,source):
 title=clean(title);u=str(url or '').strip();ts=stamp(t)
 if len(title)<12 or not u or not ts:return
 p=urlparse(u)
 if p.scheme not in ('http','https'):return
 out.append({'title':title,'url':u,'published_at':iso_from_ts(ts),'source':source})

def get(url,timeout=18):
 r=requests.get(url,headers=HEADERS,timeout=timeout)
 r.raise_for_status()
 return r

def parse_rss(raw,source,base=''):
 out=[]
 try:root=ET.fromstring(raw)
 except:return out
 for x in root.findall('.//item')[:80]:
  title=x.findtext('title');link=x.findtext('link');date=x.findtext('pubDate') or x.findtext('{http://purl.org/dc/elements/1.1/}date')
  if link:add(out,title,urljoin(base,link),date,source)
 return out

def fetch_ronb():
 out=[]
 url='https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,modified_gmt,link,title'
 for x in get(url).json():
  t=(x.get('date_gmt') or x.get('modified_gmt') or '')
  if t and not t.endswith('Z'):t+='Z'
  add(out,(x.get('title') or {}).get('rendered'),x.get('link'),t,'RONB Post')
 return out

def fetch_ekantipur():
 r=get('https://ekantipur.com/rss')
 return parse_rss(r.text,'eKantipur','https://ekantipur.com/')

def rel_minutes(text):
 s=str(text or '').translate(NP_DIGITS).lower()
 pats=((r'(\d+)\s*मिनेट\s*अघि',1),(r'(\d+)\s*घण्टा\s*अघि',60),(r'(\d+)\s*(?:min|mins|minute|minutes)\s*ago',1),(r'(\d+)\s*(?:hr|hrs|hour|hours)\s*ago',60))
 for pat,mul in pats:
  m=re.search(pat,s,re.I)
  if m:return int(m.group(1))*mul,m
 return None,None

def fetch_hamropatro():
 out=[];now=datetime.now(timezone.utc)
 r=get('https://www.hamropatro.com/news')
 soup=BeautifulSoup(r.text,'html.parser')
 for a in soup.find_all('a',href=True):
  raw=' '.join(a.stripped_strings).strip();mins,m=rel_minutes(raw)
  if mins is None or mins>180:continue
  normalized=raw.translate(NP_DIGITS)
  # Remove the outlet/time prefix and keep the headline that follows it.
  mm=re.search(r'(?:\d+\s*मिनेट\s*अघि|\d+\s*घण्टा\s*अघि|\d+\s*(?:min|mins|minute|minutes|hr|hrs|hour|hours)\s*ago)',normalized,re.I)
  if not mm:continue
  title=clean(normalized[mm.end():].lstrip(' ·•|-:'))
  if len(title)<18:continue
  u=urljoin('https://www.hamropatro.com/news',a.get('href'))
  add(out,title,u,(now-timedelta(minutes=mins)).isoformat(),'Hamro Patro')
 return out

def fetch_radionepal():
 # Radio Nepal is WordPress; RSS gives exact publication timestamps when available.
 for url in ('https://radionepalonline.com/feed/','https://radionepalonline.com/en/feed/'):
  try:
   r=get(url)
   items=parse_rss(r.text,'Radio Nepal','https://radionepalonline.com/')
   if items:return items
  except:pass
 return []

def main():
 old={}
 if OUT.exists():
  try:old=json.loads(OUT.read_text(encoding='utf-8'))
  except:old={}
 items=[];status={}
 funcs={'ronb':fetch_ronb,'ekantipur':fetch_ekantipur,'hamropatro':fetch_hamropatro,'radionepal':fetch_radionepal}
 for label,key in SOURCES:
  try:
   got=funcs[key]();items.extend(got);status[label]={'ok':True,'items':len(got)}
  except Exception as e:
   status[label]={'ok':False,'error':type(e).__name__}

 # Preserve recent last-good items for a temporarily failing source.
 cut=(datetime.now(timezone.utc)-timedelta(hours=24)).timestamp()
 for x in old.get('items',[]):
  src=x.get('source')
  if isinstance(status.get(src),dict) and not status[src].get('ok') and stamp(x.get('published_at'))>=cut:
   items.append(x)

 seen_url=set();seen_title=set();ded=[]
 for x in sorted(items,key=lambda z:stamp(z.get('published_at')),reverse=True):
  u=(x.get('url') or '').split('#')[0]
  k=re.sub(r'\W+',' ',(x.get('title') or '').lower()).strip()
  if not k or u in seen_url or k in seen_title:continue
  seen_url.add(u);seen_title.add(k);ded.append(x)
  if len(ded)>=160:break

 now=datetime.now(timezone.utc)
 payload={'generated_at':now.isoformat().replace('+00:00','Z'),'refresh_minutes':5,'sources':status,'items':ded}
 old_sig=[(x.get('title'),x.get('url'),x.get('published_at'),x.get('source')) for x in old.get('items',[])]
 new_sig=[(x.get('title'),x.get('url'),x.get('published_at'),x.get('source')) for x in ded]
 if old_sig==new_sig and old.get('sources')==status and old.get('refresh_minutes')==5:
  print('No headline change')
  return
 OUT.parent.mkdir(exist_ok=True)
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Updated',len(ded),'items',status)

if __name__=='__main__':main()
