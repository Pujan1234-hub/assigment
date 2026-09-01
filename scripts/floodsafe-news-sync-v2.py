#!/usr/bin/env python3
import html,json,re,requests,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin
OUT=Path('data/floodsafe-news.json')
UA='Mozilla/5.0 (compatible; FloodSafeNepal-News/5.0)'
H={'User-Agent':UA,'Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
SOURCES=['RONB Post','Radio Nepal','News24 Nepal']
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip()
def stamp(s):
 if not s:return 0
 try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).timestamp()
 except:pass
 try:return parsedate_to_datetime(str(s)).timestamp()
 except:return 0
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z')
def get(u,timeout=20):
 r=requests.get(u,headers=H,timeout=timeout);r.raise_for_status();return r
def add(out,title,url,t,source):
 t=stamp(t);title=clean(title);url=str(url or '').strip()
 if t and len(title)>=12 and url:out.append({'title':title,'url':url,'published_at':iso(t),'source':source})
def ronb():
 out=[]
 try:j=get('https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=60&_fields=date_gmt,modified_gmt,link,title').json()
 except Exception as e:return out,str(e)
 for x in j if isinstance(j,list) else []:
  t=x.get('date_gmt') or x.get('modified_gmt') or ''
  if t and not re.search(r'(?:Z|[+-]\d\d:\d\d)$',t):t+='Z'
  tt=x.get('title') or {};add(out,tt.get('rendered') if isinstance(tt,dict) else tt,x.get('link'),t,'RONB Post')
 return out,None
def article_time(soup):
 for attrs in ({'property':'article:published_time'},{'property':'og:published_time'},{'itemprop':'datePublished'}):
  x=soup.find('meta',attrs=attrs)
  if x and stamp(x.get('content')):return x.get('content')
 for x in soup.find_all('time',limit=10):
  if stamp(x.get('datetime')):return x.get('datetime')
 for x in soup.find_all('script',type='application/ld+json',limit=10):
  m=re.search(r'"datePublished"\s*:\s*"([^"]+)',x.string or x.get_text(' ',strip=True))
  if m and stamp(m.group(1)):return m.group(1)
 return None
def radio_nepal():
 out=[]
 try:
  base='https://radionepalonline.com/';s=BeautifulSoup(get(base).text,'html.parser');links=[]
  for a in s.find_all('a',href=True):
   u=urljoin(base,a['href']);title=clean(' '.join(a.stripped_strings))
   if 'radionepalonline.com/' not in u or len(title)<15 or u in [x[1] for x in links]:continue
   if re.search(r'/(category|tag|author|page|programs|audio)(?:/|$)',u):continue
   links.append((title,u))
   if len(links)>=80:break
  for title,u in links:
   try:
    page=BeautifulSoup(get(u,8).text,'html.parser');t=article_time(page)
    if not t:continue
    h1=page.find('h1');real=clean(h1.get_text(' ',strip=True)) if h1 else title;add(out,real,u,t,'Radio Nepal')
   except:pass
  return out,None
 except Exception as e:return out,str(e)
def news24():
 out=[]
 try:
  raw=get('https://www.youtube.com/@news24tvchannel/videos').text
  ids=re.findall(r'"channelId":"(UC[\w-]+)"',raw)
  if not ids:ids=re.findall(r'channel_id=(UC[\w-]+)',raw)
  if not ids:raise RuntimeError('News24 channel id not found')
  feed=get('https://www.youtube.com/feeds/videos.xml?channel_id='+ids[0]).text;root=ET.fromstring(feed)
  ns={'a':'http://www.w3.org/2005/Atom','yt':'http://www.youtube.com/xml/schemas/2015'}
  for e in root.findall('a:entry',ns):
   title=e.findtext('a:title',default='',namespaces=ns);vid=e.findtext('yt:videoId',default='',namespaces=ns);pub=e.findtext('a:published',default='',namespaces=ns)
   add(out,title,'https://www.youtube.com/watch?v='+vid,pub,'News24 Nepal')
  return out,None
 except Exception as e:return out,str(e)
def main():
 now=datetime.now(timezone.utc).timestamp();cut=now-30*60;items=[];status={}
 for name,fn in [('RONB Post',ronb),('Radio Nepal',radio_nepal),('News24 Nepal',news24)]:
  got,err=fn();fresh=[x for x in got if stamp(x['published_at'])>=cut and stamp(x['published_at'])<=now+300];items+=fresh;status[name]={'ok':err is None,'items':len(fresh)}
  if err:status[name]['error']=err[:160]
 seen=set();ded=[]
 for x in sorted(items,key=lambda z:stamp(z['published_at']),reverse=True):
  k=(x['url'].split('#')[0],re.sub(r'\W+',' ',x['title'].lower()).strip())
  if k in seen:continue
  seen.add(k);ded.append(x)
 payload={'generated_at':iso(now),'refresh_minutes':5,'latest_window_minutes':10,'archive_window_minutes':20,'max_age_minutes':30,'allowed_sources':SOURCES,'sources':status,'items':ded[:100]}
 OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('news',len(ded),status)
if __name__=='__main__':main()
