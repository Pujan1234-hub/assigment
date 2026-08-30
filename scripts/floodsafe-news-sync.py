#!/usr/bin/env python3
import json,re,urllib.request,urllib.parse,html
from datetime import datetime,timezone,timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

OUT=Path('data/floodsafe-news.json')
UA='FloodSafe-Nepal-News/2.0'
SOURCES=[
 ('Onlinekhabar','https://english.onlinekhabar.com/feed'),
 ('eKantipur','https://ekantipur.com/rss'),
 ('Hamro Patro','https://www.hamropatro.com/news'),
 ('RONB Post','https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=40&_fields=date_gmt,modified_gmt,link,title'),
 ('Nepal Government','https://mofa.gov.np/'),
]
ALLOWED=('onlinekhabar.com','ekantipur.com','hamropatro.com','ronbpost.com','.gov.np')

def get(url):
 r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA,'Cache-Control':'no-cache'}),timeout=20);return r.read().decode('utf-8','replace')
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def stamp(s):
 if not s:return 0
 try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).timestamp()
 except: pass
 try:return parsedate_to_datetime(s).timestamp()
 except:return 0
def allowed(u):return any(x in urllib.parse.urlparse(u).netloc.lower() for x in ALLOWED)
def add(out,title,url,t,source):
 title=clean(title)
 if title and url and allowed(url) and stamp(t):out.append({'title':title,'url':url,'published_at':datetime.fromtimestamp(stamp(t),timezone.utc).isoformat().replace('+00:00','Z'),'source':source})
def rss(raw,source):
 out=[]
 try:
  root=ET.fromstring(raw)
  for x in root.findall('.//item')[:60]:add(out,x.findtext('title'),x.findtext('link'),x.findtext('pubDate') or x.findtext('{http://purl.org/dc/elements/1.1/}date'),source)
 except:pass
 return out
def html_links(raw,base,source):
 out=[]
 # Conservative fallback: only dated article URLs and page time metadata.
 page_date=re.search(r'(20\d\d[-/]\d\d[-/]\d\d[T ][0-9:]+)',raw)
 for href,label in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',raw):
  u=urllib.parse.urljoin(base,href); title=clean(label)
  m=re.search(r'/(20\d\d)/(\d\d)/(\d\d)/',u)
  if m and len(title)>18:
   t=f'{m.group(1)}-{m.group(2)}-{m.group(3)}T12:00:00+05:45';add(out,title,u,t,source)
 return out

def main():
 old={}
 if OUT.exists():
  try:old=json.loads(OUT.read_text())
  except:pass
 items=[];status={}
 for source,url in SOURCES:
  try:
   raw=get(url);status[source]='ok'
   if source=='RONB Post':
    for x in json.loads(raw):add(items,(x.get('title') or {}).get('rendered'),x.get('link'),(x.get('date_gmt') or x.get('modified_gmt') or '')+'Z',source)
   elif raw.lstrip().startswith('<?xml') or '<rss' in raw[:500].lower():items+=rss(raw,source)
   else:items+=html_links(raw,url,source)
  except Exception as e:status[source]='error:'+type(e).__name__
 # Preserve recent last-good items if a source temporarily fails.
 now=datetime.now(timezone.utc);cut=(now-timedelta(hours=6)).timestamp()
 for x in old.get('items',[]):
  if status.get(x.get('source'),'').startswith('error') and stamp(x.get('published_at'))>=cut:items.append(x)
 seen=set();ded=[]
 for x in sorted(items,key=lambda z:stamp(z['published_at']),reverse=True):
  k=re.sub(r'\W+',' ',x['title'].lower()).strip()
  if k in seen:continue
  seen.add(k);ded.append(x)
 OUT.parent.mkdir(exist_ok=True)
 OUT.write_text(json.dumps({'generated_at':now.isoformat().replace('+00:00','Z'),'refresh_minutes':10,'sources':status,'items':ded[:120]},ensure_ascii=False,indent=2)+'\n')
 print(status,'items',len(ded))
if __name__=='__main__':main()
