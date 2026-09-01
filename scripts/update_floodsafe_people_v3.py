#!/usr/bin/env python3
import html,json,re,requests
from bs4 import BeautifulSoup
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
OUT=Path('data/floodsafe-people-status.json')
UA='Mozilla/5.0 (compatible; FloodSafeNepal-Human/5.0)'
H={'User-Agent':UA,'Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
ALLOWED=('RONB','Radio Nepal','Nepal Police','NDRRMA','Government of Nepal')
EVENT=re.compile(r'(bhotekoshi|bhote\s*koshi|rasuwa|trishuli|flood|flash flood|भोटेकोशी|भोटेकोसी|रसुवा|त्रिशूली|बाढी)',re.I)
CORR=re.compile(r'(corrected|revised|correction|सच्याइएको|संशोधित)',re.I)
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip()
def digits(s):return str(s or '').translate(str.maketrans('०१२३४५६७८९','0123456789')).replace(',','')
def stamp(s):
 if not s:return 0
 try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).timestamp()
 except:return 0
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z') if t else None
def get(u,timeout=18):r=requests.get(u,headers=H,timeout=timeout);r.raise_for_status();return r
def source_allowed(s):return any(x.lower() in str(s or '').lower() for x in ALLOWED)
def page_time(soup):
 for attrs in ({'property':'article:published_time'},{'property':'article:modified_time'},{'itemprop':'datePublished'}):
  x=soup.find('meta',attrs=attrs)
  if x and stamp(x.get('content')):return x.get('content')
 for t in soup.find_all('time',limit=15):
  if stamp(t.get('datetime')):return t.get('datetime')
 for sc in soup.find_all('script',type='application/ld+json',limit=15):
  m=re.search(r'"datePublished"\s*:\s*"([^"]+)',sc.string or sc.get_text(' ',strip=True))
  if m and stamp(m.group(1)):return m.group(1)
 return None
def metric(text,kind):
 s=digits(text);pats={'death':[r'(?:death toll|deaths?|dead|killed|मृत्यु|मृतक|शव)[^0-9]{0,45}(\d{1,6})',r'(\d{1,6})\s*(?:people|persons|जना)?[^.।]{0,35}(?:dead|killed|मृत्यु|मृतक)'],'missing':[r'(?:missing|unaccounted|सम्पर्कविहीन|बेपत्ता)[^0-9]{0,45}(\d{1,6})',r'(\d{1,6})\s*(?:people|persons|जना)?[^.।]{0,40}(?:missing|unaccounted|सम्पर्कविहीन|बेपत्ता)'],'rescued':[r'(?:rescued|evacuated|found safe|उद्धार|सकुशल|सुरक्षित भेट)[^0-9]{0,45}(\d{1,6})',r'(\d{1,6})\s*(?:people|persons|जना)?[^.।]{0,45}(?:rescued|evacuated|found safe|उद्धार|सकुशल|सुरक्षित)']}
 for p in pats[kind]:
  m=re.search(p,s,re.I)
  if m:
   v=int(m.group(1))
   if 0<v<100000:return v
 return None
def add(best,kind,value,t,source,url,correction=False):
 if value is None or not t or not source_allowed(source):return
 c={'value':int(value),'t':float(t),'time':iso(t),'source':source,'url':url,'correction':bool(correction)};old=best.get(kind)
 if not old or c['t']>old['t']:best[kind]=c
def story(best,title,body,t,source,url):
 text=clean(title+' '+body)
 if not EVENT.search(text):return
 for kind in ('death','missing','rescued'):add(best,kind,metric(text,kind),t,source,url,bool(CORR.search(text)))
def ronb(best):
 try:j=get('https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=80&_fields=date_gmt,modified_gmt,link,title,excerpt,content').json()
 except Exception as e:print('RONB',e);return
 for x in j if isinstance(j,list) else []:
  raw=x.get('date_gmt') or x.get('modified_gmt') or ''
  if raw and not re.search(r'(?:Z|[+-]\d\d:\d\d)$',raw):raw+='Z'
  title=clean((x.get('title') or {}).get('rendered',''));body=clean((x.get('content') or {}).get('rendered','')+' '+(x.get('excerpt') or {}).get('rendered',''));story(best,title,body,stamp(raw),'RONB',x.get('link') or '')
def crawl(best,listing,host,source,limit=80):
 try:soup=BeautifulSoup(get(listing).text,'html.parser')
 except Exception as e:print(source,e);return
 links=[]
 for a in soup.find_all('a',href=True):
  u=urljoin(listing,a['href']);p=urlparse(u);title=clean(' '.join(a.stripped_strings))
  if not (p.netloc==host or p.netloc.endswith('.'+host)) or len(title)<12 or u in [z[1] for z in links]:continue
  if re.search(r'/(tag|category|author|page|search|programs|audio)(?:/|$)',p.path,re.I):continue
  links.append((title,u))
  if len(links)>=limit:break
 for title,u in links:
  try:
   s=BeautifulSoup(get(u,8).text,'html.parser');raw=s.find('article') or s.find('main');body=clean(raw.get_text(' ',strip=True) if raw else '');t=stamp(page_time(s));h=s.find('h1');story(best,clean(h.get_text(' ',strip=True)) if h else title,body,t,source,u)
  except:pass
def old_allowed(best):
 try:j=json.loads(OUT.read_text(encoding='utf-8'))
 except:return
 specs=[('death','recovered_bodies','recovered_source','recovered_source_url','recovered_update_iso','recovered_update_time'),('missing','missing_minimum','missing_source','missing_source_url','missing_update_time',None),('rescued','rescued_alive','rescued_source','rescued_source_url','rescued_update_time',None)]
 for kind,vk,sk,uk,tk,tk2 in specs:
  v=j.get(vk);s=j.get(sk);u=j.get(uk);tm=j.get(tk) or (j.get(tk2) if tk2 else None)
  if source_allowed(s) and isinstance(v,int) and v>0:add(best,kind,v,stamp(tm),s,u)
def main():
 best={};old_allowed(best);ronb(best);crawl(best,'https://radionepalonline.com/','radionepalonline.com','Radio Nepal',100);crawl(best,'https://www.nepalpolice.gov.np/news/','nepalpolice.gov.np','Nepal Police',80);crawl(best,'https://ndrrma.gov.np/','ndrrma.gov.np','NDRRMA',80)
 d,m,r=best.get('death'),best.get('missing'),best.get('rescued');payload={'event':'Current Nepal flood event','event_ne':'नेपालको हालको बाढी घटना','updated_date':datetime.now(timezone.utc).date().isoformat(),'recovered_bodies':d['value'] if d else None,'recovered_source':d['source'] if d else None,'recovered_source_url':d['url'] if d else None,'recovered_update_time':d['time'] if d else None,'recovered_update_iso':d['time'] if d else None,'missing_minimum':m['value'] if m else None,'missing_source':m['source'] if m else None,'missing_source_url':m['url'] if m else None,'missing_update_time':m['time'] if m else None,'rescued_alive':r['value'] if r else None,'rescued_source':r['source'] if r else None,'rescued_source_url':r['url'] if r else None,'rescued_update_time':r['time'] if r else None,'status':'requested_sources_only','last_checked_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'sync_sources':['RONB','Radio Nepal','Nepal Police','NDRRMA'],'last_winning_sources':{'death':d['source'] if d else None,'missing':m['source'] if m else None,'rescued':r['source'] if r else None},'sync_schema':3,'sync_policy':'Only RONB, Radio Nepal, Nepal Police and NDRRMA/Government official sources. Never substitute an unapproved source. Missing may decrease when a newer approved report changes the count; death/rescued can decrease only on an explicit correction.'}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(payload['last_winning_sources'])
if __name__=='__main__':main()
