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
UA='Mozilla/5.0 (compatible; FloodSafeNepal-News/4.0; +https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/)'
HEADERS={'User-Agent':UA,'Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
NP_DIGITS=str.maketrans('०१२३४५६७८९','0123456789')
SOURCES=(('RONB Post','ronb'),('Onlinekhabar','onlinekhabar'),('Hamro Patro','hamropatro'),('eKantipur','ekantipur'),('Nepal Government','gov'))
OLD_BY_URL={}

def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip()
def stamp(s):
 if not s:return 0
 try:return datetime.fromisoformat(str(s).strip().replace('Z','+00:00')).timestamp()
 except:pass
 try:return parsedate_to_datetime(str(s)).timestamp()
 except:return 0
def iso(v):return datetime.fromtimestamp(v,timezone.utc).isoformat().replace('+00:00','Z')
def add(out,title,url,t,source,time_exact=True):
 title=clean(title);u=str(url or '').strip();ts=stamp(t)
 if len(title)<12 or not u or not ts:return
 p=urlparse(u)
 if p.scheme not in ('http','https'):return
 x={'title':title,'url':u,'published_at':iso(ts),'source':source}
 if not time_exact:x['time_exact']=False
 out.append(x)
def get(url,timeout=16):
 r=requests.get(url,headers=HEADERS,timeout=timeout);r.raise_for_status();return r

def parse_rss(raw,source,base=''):
 out=[]
 try:root=ET.fromstring(raw)
 except:return out
 for x in root.findall('.//item')[:100]:
  add(out,x.findtext('title'),urljoin(base,x.findtext('link') or ''),x.findtext('pubDate') or x.findtext('{http://purl.org/dc/elements/1.1/}date'),source)
 return out

def published_from_html(raw):
 soup=BeautifulSoup(raw,'html.parser')
 for attrs in ({'property':'article:published_time'},{'name':'article:published_time'},{'property':'og:published_time'},{'itemprop':'datePublished'},{'name':'datePublished'},{'name':'pubdate'}):
  tag=soup.find('meta',attrs=attrs)
  if tag:
   v=tag.get('content') or tag.get('value')
   if stamp(v):return v
 for tm in soup.find_all('time',limit=20):
  v=tm.get('datetime') or tm.get('content')
  if stamp(v):return v
 for sc in soup.find_all('script',type='application/ld+json',limit=20):
  text=sc.string or sc.get_text(' ',strip=True)
  m=re.search(r'"datePublished"\s*:\s*"([^"]+)"',text or '',re.I)
  if m and stamp(m.group(1)):return m.group(1)
 return None

def verify_page(source,title,url,allowed_hosts=None):
 try:
  p=urlparse(url)
  if allowed_hosts and not any(p.netloc==h or p.netloc.endswith('.'+h) for h in allowed_hosts):return None
  r=get(url,10);pub=published_from_html(r.text)
  if not pub:return None
  soup=BeautifulSoup(r.text,'html.parser');og=soup.find('meta',attrs={'property':'og:title'});h=soup.find('h1');real=clean(og.get('content')) if og and og.get('content') else clean(h.get_text(' ',strip=True)) if h else title
  out=[];add(out,real,url,pub,source);return out[0] if out else None
 except:return None

def site_candidates(urls,allowed_hosts,max_links=60):
 seen=set();out=[]
 for listing in urls:
  try:r=get(listing)
  except:continue
  soup=BeautifulSoup(r.text.replace('\\/','/'),'html.parser')
  for a in soup.find_all('a',href=True):
   title=clean(' '.join(a.stripped_strings));u=urljoin(listing,a.get('href')).split('#')[0];p=urlparse(u)
   if not any(p.netloc==h or p.netloc.endswith('.'+h) for h in allowed_hosts):continue
   if len(title)<15 or len(title)>250 or u in seen:continue
   if re.search(r'/(tag|category|author|page|search|topic)/',p.path,re.I):continue
   seen.add(u);out.append((title,u))
   if len(out)>=max_links:return out
 return out

def verified_candidates(source,cand,hosts):
 out=[]
 with ThreadPoolExecutor(max_workers=10) as ex:
  fut=[ex.submit(verify_page,source,t,u,hosts) for t,u in cand]
  for f in as_completed(fut):
   x=f.result()
   if x:out.append(x)
 return out

def wp_posts(url,source):
 out=[]
 for x in get(url).json():
  t=x.get('date_gmt') or x.get('modified_gmt') or x.get('date') or x.get('modified') or ''
  if t and not re.search(r'(?:Z|[+-]\d\d:\d\d)$',t,re.I):t+='Z'
  title=x.get('title') or {};title=title.get('rendered') if isinstance(title,dict) else title
  add(out,title,x.get('link'),t,source)
 return out

def fetch_ronb():
 return wp_posts('https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=60&_fields=date_gmt,modified_gmt,link,title','RONB Post')

def fetch_onlinekhabar():
 for feed in ('https://www.onlinekhabar.com/feed','https://english.onlinekhabar.com/feed'):
  try:
   x=parse_rss(get(feed).text,'Onlinekhabar','https://www.onlinekhabar.com/')
   if x:return x
  except:pass
 hosts=('onlinekhabar.com',)
 cand=site_candidates(('https://www.onlinekhabar.com/','https://english.onlinekhabar.com/'),hosts,60)
 return verified_candidates('Onlinekhabar',cand,hosts)

def fetch_ekantipur():
 for feed in ('https://ekantipur.com/rss','https://ekantipur.com/feed'):
  try:
   x=parse_rss(get(feed).text,'eKantipur','https://ekantipur.com/')
   if x:return x
  except:pass
 hosts=('ekantipur.com',)
 cand=site_candidates(('https://ekantipur.com/','https://ekantipur.com/news','https://ekantipur.com/headlines'),hosts,60)
 return verified_candidates('eKantipur',cand,hosts)

def rel_minutes(text):
 s=str(text or '').translate(NP_DIGITS).lower()
 for pat,mul in ((r'(\d+)\s*मिनेट\s*अघि',1),(r'(\d+)\s*घण्टा\s*अघि',60),(r'(\d+)\s*(?:min|mins|minute|minutes)\s*ago',1),(r'(\d+)\s*(?:hr|hrs|hour|hours)\s*ago',60)):
  m=re.search(pat,s,re.I)
  if m:return int(m.group(1))*mul,m
 return None,None

def fetch_hamropatro():
 now=datetime.now(timezone.utc);out=[]
 for base in ('https://www.hamropatro.com/news','https://hamropatro.alpha.hamrostack.com/news'):
  try:soup=BeautifulSoup(get(base).text,'html.parser')
  except:continue
  for a in soup.find_all('a',href=True):
   text=' '.join(a.stripped_strings).strip();mins,m=rel_minutes(text)
   if mins is None or mins>240:continue
   title=clean(text[m.end():].lstrip(' ·•|-:'))
   u=urljoin(base,a.get('href'));p=urlparse(u)
   if '/news/detail/' not in p.path or len(title)<18:continue
   add(out,title,'https://www.hamropatro.com'+p.path,(now-timedelta(minutes=mins)).isoformat(),'Hamro Patro',False)
  if out:return out
 return out

def fetch_gov():
 hosts=('gov.np',)
 pages=('https://www.opmcm.gov.np/','https://moha.gov.np/','https://mofa.gov.np/','https://www.ndrrma.gov.np/','https://bipadportal.gov.np/')
 cand=site_candidates(pages,hosts,80)
 return verified_candidates('Nepal Government',cand,hosts)

def main():
 global OLD_BY_URL
 try:old=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
 except:old={}
 OLD_BY_URL={(x.get('url') or '').split('#')[0]:x for x in old.get('items',[]) if x.get('url')}
 funcs={'ronb':fetch_ronb,'onlinekhabar':fetch_onlinekhabar,'hamropatro':fetch_hamropatro,'ekantipur':fetch_ekantipur,'gov':fetch_gov}
 items=[];status={}
 with ThreadPoolExecutor(max_workers=len(SOURCES)) as ex:
  futs={ex.submit(funcs[key]):(label,key) for label,key in SOURCES}
  for f in as_completed(futs):
   label,_=futs[f]
   try:
    got=f.result();status[label]={'ok':bool(got),'items':len(got)}
    if not got:status[label]['error']='no-verified-items'
    items.extend(got)
   except Exception as e:status[label]={'ok':False,'items':0,'error':type(e).__name__}
 cut=(datetime.now(timezone.utc)-timedelta(hours=24)).timestamp()
 for x in old.get('items',[]):
  if x.get('source') in status and not status[x.get('source')].get('ok') and stamp(x.get('published_at'))>=cut:items.append(x)
 seen_u=set();seen_t=set();ded=[]
 for x in sorted(items,key=lambda z:stamp(z.get('published_at')),reverse=True):
  u=(x.get('url') or '').split('#')[0];k=re.sub(r'\W+',' ',(x.get('title') or '').lower()).strip()
  if not k or u in seen_u or k in seen_t:continue
  seen_u.add(u);seen_t.add(k);ded.append(x)
  if len(ded)>=200:break
 payload={'generated_at':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'refresh_minutes':5,'latest_window_minutes':10,'archive_window_minutes':30,'allowed_sources':[x[0] for x in SOURCES],'sources':status,'items':ded}
 OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Updated',len(ded),'items',status)
if __name__=='__main__':main()
