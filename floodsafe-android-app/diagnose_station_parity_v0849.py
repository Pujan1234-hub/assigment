import json, re, urllib.request, urllib.parse, html

BIPAD='https://bipadportal.gov.np/api/v1/'
TARGETS=['Balkhu Khola at Balambu','Dhobi Khola at Chabahil','Manohara Khola at Balkumari','Nagmati River at Sundarijal','Bagmati River at Gaurighat','Bagmati River at Sundarijal Bridge','Bishnumati Khola at Gongabu Buspark','Dhobi Khola at Kapan','Salinadi Sankhu Telemetry']

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'FloodSafeNepal-parity/0.8.49','Accept':'application/json,text/html'})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read().decode('utf-8','replace')

def rows(obj):
    if isinstance(obj,list): return obj
    if not isinstance(obj,dict): return []
    for k in ('results','data','items','features'):
        v=obj.get(k)
        if isinstance(v,list): return v
        if isinstance(v,dict):
            for kk in ('results','data','items'):
                if isinstance(v.get(kk),list): return v[kk]
    return []

def fetch_json(path):
    text=get(BIPAD+path)
    obj=json.loads(text)
    return obj, rows(obj)

def deep(d,key):
    if not isinstance(d,dict): return None
    if key in d:return d.get(key)
    for v in d.values():
        if isinstance(v,dict):
            x=deep(v,key)
            if x is not None:return x
    return None

def pick(d,keys):
    for k in keys:
        x=deep(d,k)
        if x not in (None,''):return x
    return None

def name(d):
    return str(pick(d,['river_name','riverName','station_name','stationName','title','name']) or '').strip()

def index(d):
    return str(pick(d,['stationIndex','station_index','stationSeriesId','station_series_id','stationId','station_id']) or '').strip()

def key(s): return re.sub(r'[^a-z0-9]+','',s.lower())

catalog_obj,catalog=fetch_json('river-stations/?limit=2000')
latest_obj,latest=fetch_json('river-stations/?latest=true&limit=2000')

# Exact current candidates from the BIPAD latest endpoint. Presence alone is not enough;
# report the actual measurement-looking fields and timestamps so app parsing can match source truth.
MEASURE=['_lastWaterLevel','waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level']
TIME=['_measurementTime','measurementTime','measurement_time','observedAt','observed_at','updatedOn','updated_on','modifiedOn','modified_on','createdOn','created_on']
STATUS=['_officialStatus','status','statusName','status_name','riverStatus','river_status']

latest_by_name={key(name(r)):r for r in latest if isinstance(r,dict) and name(r)}
latest_by_index={index(r):r for r in latest if isinstance(r,dict) and index(r)}

# DHM table
try:
    dhm_html=get('https://dhm.gov.np/hydrology/realtime-stream')
except Exception as e:
    dhm_html=''
    print('DHM_FETCH_ERROR',repr(e))

def text_cell(s):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'(?is)<[^>]+>',' ',s))).strip()

dhm=[]
for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>',dhm_html):
    cells=[text_cell(x) for x in re.findall(r'(?is)<t[dh][^>]*>(.*?)</t[dh]>',tr)]
    if len(cells)>=6 and cells[0].isdigit():
        dhm.append({'sn':cells[0],'index':cells[2].strip(),'name':cells[3].strip(),'district':cells[4].strip(),'level':cells[5].strip(),'discharge':cells[6].strip() if len(cells)>6 else ''})
dhm_by_name={key(r['name']):r for r in dhm}
dhm_by_index={r['index']:r for r in dhm if r['index']}

catalog_names={key(name(r)):r for r in catalog if isinstance(r,dict) and name(r)}

print('PARITY_COUNTS '+json.dumps({
    'bipad_catalog_rows':len(catalog),
    'bipad_catalog_count_field':catalog_obj.get('count') if isinstance(catalog_obj,dict) else None,
    'bipad_latest_rows':len(latest),
    'bipad_latest_count_field':latest_obj.get('count') if isinstance(latest_obj,dict) else None,
    'dhm_realtime_rows':len(dhm),
    'union_live_identity_count':len(set([('i:'+index(r)) if index(r) else ('n:'+key(name(r))) for r in latest if name(r)] + [('i:'+r['index']) if r['index'] else ('n:'+key(r['name'])) for r in dhm if r['name']]))
},ensure_ascii=False,sort_keys=True))

for target in TARGETS:
    ck=key(target); c=catalog_names.get(ck)
    # fuzzy token match if exact source spelling differs
    if c is None:
        toks=[t for t in re.split(r'[^a-z0-9]+',target.lower()) if len(t)>3]
        for r in catalog:
            nm=name(r).lower()
            if toks and sum(t in nm for t in toks)>=max(1,len(toks)-1): c=r;break
    ix=index(c) if c else ''
    b=(latest_by_index.get(ix) if ix else None) or latest_by_name.get(ck)
    d=(dhm_by_index.get(ix) if ix else None) or dhm_by_name.get(ck)
    out={'target':target,'catalog':bool(c),'station_index':ix,'bipad_latest':bool(b),'dhm_live':bool(d)}
    if b:
        out.update({'bipad_name':name(b),'measurement':pick(b,MEASURE),'time':pick(b,TIME),'status':pick(b,STATUS),'generic_level':pick(b,['level']),'elevation':pick(b,['elevation','altitude'])})
    if d:out['dhm']=d
    if c:
        out['catalog_name']=name(c);out['catalog_generic_level']=pick(c,['level']);out['catalog_elevation']=pick(c,['elevation','altitude'])
    print('STATION_CHECK '+json.dumps(out,ensure_ascii=False,sort_keys=True,default=str))
