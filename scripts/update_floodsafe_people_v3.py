#!/usr/bin/env python3
import json,re,html
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

OUT=Path('data/floodsafe-people-status.json')
NEWS=Path('data/floodsafe-news.json')
UA='Mozilla/5.0 (compatible; FloodSafeNepal-Human/3.0; +https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/)'
H={'User-Agent':UA,'Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'ne,en;q=0.8'}
EVENT=re.compile(r'(bhotekoshi|bhote\s*koshi|rasuwa|trishuli|भोटेकोशी|भोटेकोसी|रसुवा|त्रिशूली|त्रिशुली)',re.I)
FLOOD=re.compile(r'(flood|flash\s*flood|बाढी|आकस्मिक\s*बाढी)',re.I)
AUTH=re.compile(r'(nepal\s*police|ndrrma|national\s*disaster\s*risk\s*reduction|नेपाल\s*प्रहरी|विपद्\s*जोखिम|प्राधिकरण|government\s*(?:figure|update)|authority)',re.I)
CORR=re.compile(r'(corrected|correction|revised|revision|संशोधित|सच्याइएको)',re.I)
NP=str.maketrans('०१२३४५६७८९','0123456789')

WP=[
 ('OnlineKhabar','https://english.onlinekhabar.com/wp-json/wp/v2/posts?per_page=100&_fields=date,date_gmt,modified,modified_gmt,link,title,excerpt,content'),
 ('RONB','https://www.ronbpost.com/wp-json/wp/v2/posts?per_page=80&_fields=date,date_gmt,modified,modified_gmt,link,title,excerpt,content'),
]
LISTINGS=[
 ('Nepal News','https://english.nepalnews.com/'),
 ('Radio Nepal','https://radionepalonline.com/en/'),
 ('Hamro Patro','https://www.hamropatro.com/news'),
]
KCHA='https://kchakhabar.com/api/v1/today.json?limit=100'

def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(s or '')))).strip()
def relevant_title(t):return bool(EVENT.search(t or '') and FLOOD.search(t or ''))
def numtext(s):return str(s or '').translate(NP).replace(',','')
def iso(v):
 if not v:return None
 try:
  s=str(v).strip();d=datetime.fromisoformat(s.replace('Z','+00:00'))
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  return d.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
 except:return None
def stamp(v):
 x=iso(v)
 return datetime.fromisoformat(x.replace('Z','+00:00')).timestamp() if x else 0

def metrics(text):
 t=numtext(text);out={}
 pats={
  'death':[
   r'(?:death\s*toll|confirmed\s*deaths?|bodies\s*(?:recovered|found)|मृत्यु|मृतक|शव)[^0-9]{0,70}(\d{1,6})',
   r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,70}(?:dead|died|deaths?|bodies\s*recovered|शव\s*फेला|मृत्यु)',
  ],
  'missing':[
   r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,90}(?:remain(?:s)?\s+)?(?:missing|unaccounted\s*for|सम्पर्कविहीन|बेपत्ता)',
   r'(?:missing|unaccounted\s*for|सम्पर्कविहीन|बेपत्ता)[^0-9]{0,70}(\d{1,6})',
  ],
  'rescued':[
   r'(\d{1,6})\s+(?:people|persons|जना)?[^.।]{0,90}(?:have\s+)?(?:so\s+far\s+)?(?:been\s+)?rescued',
   r'(?:rescued|उद्धार)[^0-9]{0,70}(\d{1,6})',
  ]
 }
 for k,pp in pats.items():
  for p in pp:
   m=re.search(p,t,re.I)
   if m:
    v=int(m.group(1))
    if 0<v<100000:out[k]=v;break
 return out

def get(url,timeout=14):
 r=requests.get(url,headers=H,timeout=timeout);r.raise_for_status();return r

def soup_article(raw):
 s=BeautifulSoup(raw,'html.parser')
 h=s.find('h1');title=clean(h.get_text(' ',strip=True)) if h else clean((s.find('title') or {}).get_text(' ',strip=True) if s.find('title') else '')
 body=s.find('article') or s.find(attrs={'itemprop':'articleBody'}) or s.find('main')
 text=clean(body.get_text(' ',strip=True) if body else '')
 if not text:text=clean(s.get_text(' ',strip=True))[:12000]
 when=None
 for attrs in ({'property':'article:modified_time'},{'property':'article:published_time'},{'name':'datePublished'},{'itemprop':'datePublished'}):
  x=s.find('meta',attrs=attrs)
  if x and iso(x.get('content')):when=iso(x.get('content'));break
 if not when:
  tm=s.find('time');when=iso(tm.get('datetime') if tm else None)
 return title,text,when

def add(best,kind,value,when,source,url,authority,correction=False):
 st=stamp(when)
 if not st or not value:return
 c={'value':int(value),'stamp':st,'iso':iso(when),'source':source,'url':url,'authority':authority,'correction':correction}
 old=best.get(kind)
 key=(st,1 if authority else 0,1 if correction else 0,int(value))
 oldkey=(-1,0,0,0) if not old else (old['stamp'],1 if old['authority'] else 0,1 if old['correction'] else 0,old['value'])
 if key>oldkey:best[kind]=c

def inspect_doc(best,title,text,when,source,url):
 title=clean(title);text=clean(text)
 # Critical guard: do not harvest a flood number from an unrelated page/sidebar.
 if not relevant_title(title):return
 joined=title+' '+text
 if not AUTH.search(joined):return
 mm=metrics(joined)
 for k,v in mm.items():add(best,k,v,when,source,url,True,bool(CORR.search(joined)))

def fetch_wp(best,source,url):
 try:j=get(url).json()
 except Exception as e:print(source,'WP failed',repr(e));return
 for p in j if isinstance(j,list) else []:
  title=clean((p.get('title') or {}).get('rendered',''))
  if not relevant_title(title):continue
  body=clean((p.get('content') or {}).get('rendered','')+' '+(p.get('excerpt') or {}).get('rendered',''))
  raw=p.get('modified_gmt') or p.get('date_gmt') or p.get('modified') or p.get('date')
  if raw and 'T' in str(raw) and not re.search(r'(?:Z|[+-]\d\d:\d\d)$',str(raw)):raw=str(raw)+'Z'
  inspect_doc(best,title,body,raw,source,p.get('link') or url)

def listing_links(base):
 try:r=get(base);s=BeautifulSoup(r.text,'html.parser')
 except Exception:return []
 host=urlparse(base).netloc.replace('www.','');out=[]
 for a in s.find_all('a',href=True):
  title=clean(' '.join(a.stripped_strings));u=urljoin(base,a.get('href')).split('#')[0]
  if host not in urlparse(u).netloc.replace('www.',''):continue
  if relevant_title(title) and u not in [x[1] for x in out]:out.append((title,u))
  if len(out)>=20:break
 return out

def fetch_listing(best,source,base):
 for _,u in listing_links(base):
  try:r=get(u,10);title,text,when=soup_article(r.text);inspect_doc(best,title,text,when,source,u)
  except Exception:continue

def fetch_news_snapshot(best):
 if not NEWS.exists():return
 try:j=json.loads(NEWS.read_text(encoding='utf-8'))
 except:return
 for x in j.get('items',[])[:100]:
  title=clean(x.get('title'))
  if not relevant_title(title):continue
  u=x.get('url');source=x.get('source') or 'Verified national media';when=x.get('published_at')
  if not u:continue
  try:r=get(u,10);pt,body,pwhen=soup_article(r.text);inspect_doc(best,pt or title,body,pwhen or when,source,u)
  except Exception:continue

def fetch_kcha(best):
 try:j=get(KCHA).json()
 except Exception as e:print('KCHA failed',repr(e));return
 stories=j.get('stories',[]) if isinstance(j,dict) else []
 for s in stories:
  title=clean((s.get('topic_en') or '')+' '+(s.get('topic_ne') or ''))
  if not relevant_title(title):continue
  sources=s.get('sources') or []
  for src in sources[:8]:
   u=src.get('url');name=src.get('publisher') or 'Verified national media'
   if not u:continue
   try:r=get(u,10);pt,body,when=soup_article(r.text);inspect_doc(best,pt or title,body,when or s.get('updated_at') or s.get('first_reported'),name,u)
   except Exception:continue

def main():
 old=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
 best={}
 for src,url in WP:fetch_wp(best,src,url)
 fetch_news_snapshot(best)
 fetch_kcha(best)
 for src,url in LISTINGS:fetch_listing(best,src,url)
 fields={
  'death':('recovered_bodies','recovered_update_time','recovered_source','recovered_source_url','recovered_update_iso'),
  'missing':('missing_minimum','missing_update_time','missing_source','missing_source_url',None),
  'rescued':('rescued_alive','rescued_update_time','rescued_source','rescued_source_url',None),
 }
 changed=False;winners={}
 for kind,c in best.items():
  vf,tf,sf,uf,extra=fields[kind];ov=int(old.get(vf) or 0);ot=stamp(old.get(tf))
  if c['stamp']<ot:continue
  if c['value']<ov and not c['correction']:continue
  if c['value']!=ov or c['stamp']>ot or old.get(sf)!=c['source'] or old.get(uf)!=c['url']:
   old[vf]=c['value'];old[tf]=c['iso'];old[sf]=c['source'];old[uf]=c['url'];changed=True
   if extra:old[extra]=c['iso']
  winners[kind]=c['source']
 if not changed:
  print('No newer verified Human Status metric');return
 old['event']='Bhotekoshi flash flood';old['event_ne']='भोटेकोशी आकस्मिक बाढी';old['updated_date']=datetime.now(timezone.utc).date().isoformat()
 old['status']='auto_multisource_strict_nepal_only';old['last_checked_utc']=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
 old['sync_policy']='Newest credible Nepal-side authority-attributed cumulative figure independently per metric. Reject unrelated-page/sidebar matches, subgroup-only counts and Nepal+China combined totals; never roll backward without an explicit correction.'
 old['sync_sources']=['Nepal Police','NDRRMA','Radio Nepal','RONB','Hamro Patro','OnlineKhabar','Nepal News','verified national media via K cha khabar']
 old['last_winning_sources']=winners
 OUT.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Updated Human Status',old.get('recovered_bodies'),old.get('missing_minimum'),old.get('rescued_alive'),winners)

if __name__=='__main__':main()
