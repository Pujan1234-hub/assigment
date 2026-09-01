#!/usr/bin/env python3
import html,json,re,requests
from bs4 import BeautifulSoup
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin
OUT=Path('data/floodsafe-news.json')
UA='Mozilla/5.0 (compatible; FloodSafeNepal-News/7.0)'
H={'User-Agent':UA,'Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
SOURCES=['RONB Post','Radio Nepal','News24 Nepal']
MAX_AGE=30*60
FUTURE=5*60

def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip()
def stamp(s):
 if not s:return 0
 try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).timestamp()
 except:return 0
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z')
def get(u,timeout=15):
 r=requests.get(u,headers=H,timeout=timeout);r.raise_for_status();return r
def add(out,title,url,t,source):
 t=stamp(t);title=clean(title);url=str(url or '').strip()
 if t and len(title)>=8 and url.startswith('http'):out.append({'title':title,'url':url,'published_at':iso(t),'source':source})

def wp(url,source):
 out=[];j=get(url).json()
 if not isinstance(j,list):raise RuntimeError('WordPress response is not a list')
 for x in j:
  t=x.get('date_gmt') or x.get('date') or x.get('modified_gmt') or x.get('modified') or ''
  if t and not re.search(r'(?:Z|[+-]\d\d:\d\d)$',t):t+='Z'
  tt=x.get('title') or {};add(out,tt.get('rendered') if isinstance(tt,dict) else tt,x.get('link'),t,source)
 return out

def ronb():return wp('https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,date,modified_gmt,modified,link,title','RONB Post')
def radio():return wp('https://radionepalonline.com/wp-json/wp/v2/posts?per_page=50&_fields=date_gmt,date,modified_gmt,modified,link,title','Radio Nepal')

def news24_time(raw):
 # News24 article images include the upload epoch, which matches the visible published time.
 vals=[int(x) for x in re.findall(r'(?:uploads/posts/[^\"\'<>\s]+-|\b)(1[7-9]\d{8})(?:\D|$)',raw)]
 for v in vals:
  if 1700000000 < v < 2000000000:return v
 soup=BeautifulSoup(raw,'html.parser')
 for attrs in ({'property':'article:published_time'},{'itemprop':'datePublished'}):
  x=soup.find('meta',attrs=attrs)
  if x and stamp(x.get('content')):return stamp(x.get('content'))
 for x in soup.find_all('time',limit=8):
  if stamp(x.get('datetime')):return stamp(x.get('datetime'))
 return 0

def news24():
 base='https://www.news24nepal.com/'
 raw=get(base).text
 links=[]
 for u in re.findall(r'href=["\'](https://www\.news24nepal\.com/detail/\d+/?)["\']',raw,re.I):
  u=u.rstrip('/')
  if u not in links:links.append(u)
  if len(links)>=8:break
 if not links:raise RuntimeError('News24 detail links not found')
 out=[]
 for u in links[:6]:
  try:
   page=get(u,8).text;t=news24_time(page)
   if not t:continue
   soup=BeautifulSoup(page,'html.parser')
   og=soup.find('meta',attrs={'property':'og:title'})
   title=og.get('content') if og else (soup.find('h1').get_text(' ',strip=True) if soup.find('h1') else soup.title.get_text(' ',strip=True))
   add(out,title,u,iso(t),'News24 Nepal')
  except Exception:pass
 return out

def main():
 now=datetime.now(timezone.utc).timestamp();cut=now-MAX_AGE;items=[];status={}
 for name,fn in [('RONB Post',ronb),('Radio Nepal',radio),('News24 Nepal',news24)]:
  try:
   got=fn();fresh=[x for x in got if cut<=stamp(x['published_at'])<=now+FUTURE];items+=fresh;status[name]={'ok':True,'items':len(fresh)}
  except Exception as e:status[name]={'ok':False,'items':0,'error':str(e)[:160]}
 seen=set();ded=[]
 for x in sorted(items,key=lambda z:stamp(z['published_at']),reverse=True):
  k=(x['url'].split('#')[0],re.sub(r'\W+',' ',x['title'].lower()).strip())
  if k in seen:continue
  seen.add(k);ded.append(x)
 payload={'generated_at':iso(now),'refresh_minutes':5,'latest_window_minutes':10,'archive_window_minutes':20,'max_age_minutes':30,'allowed_sources':SOURCES,'sources':status,'items':ded[:100]}
 OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('news',len(ded),status)
if __name__=='__main__':main()
