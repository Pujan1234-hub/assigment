from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app'
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'; m_path=src/'FloodSafeNativeMapView.java'; g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8'); m=m_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

def span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start()); d=0; quote=None; esc=False
    for i in range(op,len(text)):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':d+=1
            elif ch=='}':
                d-=1
                if d==0:return q.start(),i+1
    return None

def replace_method(text,name,block):
    s=span(text,name)
    if not s:raise SystemExit('v0892 method missing: '+name)
    return text[:s[0]]+block+text[s[1]:]

# Clear readable Nepal base map.
if 'World_Imagery/MapServer/tile' not in m:raise SystemExit('v0892 imagery URL anchor missing')
m=m.replace('World_Imagery/MapServer/tile','World_Topo_Map/MapServer/tile')
if 'V0892_CLEAR_TOPO_BASE' not in m:m='// V0892_CLEAR_TOPO_BASE: readable ESRI topo base\n'+m

# Thin the normal blue rivers and shrink station symbols.
s=span(m,'installGeoLayers')
if not s:raise SystemExit('v0892 installGeoLayers missing')
b=m[s[0]:s[1]]
def tune(layer,w,o):
    global b
    p=r'(new LineLayer\("'+re.escape(layer)+r'"[\s\S]*?\.withProperties\()([\s\S]*?)(\)\);)'
    z=re.search(p,b)
    if not z:raise SystemExit('v0892 line layer missing: '+layer)
    props=z.group(2)
    props=re.sub(r'lineWidth\([^\)]*\)',f'lineWidth({w}f)',props,count=1)
    props=re.sub(r'lineOpacity\([^\)]*\)',f'lineOpacity({o}f)',props,count=1)
    b=b[:z.start(2)]+props+b[z.end(2):]
tune('fs-river-glow','2.10','0.22'); tune('fs-rivers-layer','1.08','0.96')
points={
'fs-flow-particles':('fs-flow-particles-layer','#d6fbff','1.10','0.58'),
'fs-stale':('fs-stale-layer','#8e99a5','2.05','0.84'),
'fs-normal':('fs-normal-layer','#22c55e','2.25','0.92'),
'fs-alert':('fs-alert-layer','#facc15','2.65','0.98'),
'fs-warning':('fs-warning-layer','#f59e0b','2.95','1.0'),
'fs-danger':('fs-danger-layer','#ef4444','3.25','1.0')}
for source,(layer,color,radius,opacity) in points.items():
    p=r'ensurePointSource\("'+re.escape(source)+r'"\s*,\s*"'+re.escape(layer)+r'"\s*,\s*"[^"]+"\s*,\s*[^,]+\s*,\s*[^\)]+\);'
    repl=f'ensurePointSource("{source}", "{layer}", "{color}", {radius}f, {opacity}f);'
    b,n=re.subn(p,repl,b,count=1)
    if n!=1:raise SystemExit('v0892 point layer missing: '+source)
b=b[:b.find('{')+1]+'\n        // V0892_SMALL_STATION_DOTS V0892_THIN_BLUE_RIVERS'+b[b.find('{')+1:]
m=m[:s[0]]+b+m[s[1]:]

s=span(m,'ensurePointSource')
if not s:raise SystemExit('v0892 point helper missing')
b=m[s[0]:s[1]]
b=re.sub(r'circleStrokeWidth\([^\)]*\)','circleStrokeWidth(0.65f)',b,count=1)
b=b[:b.find('{')+1]+'\n        // V0892_POINT_STROKE_LIGHT'+b[b.find('{')+1:]
m=m[:s[0]]+b+m[s[1]:]

# Subtle, low-cost blue flow. Risk rivers stay more visible than normal rivers.
pulse=r'''    private void v847UpdateMovingGlow(long now){
        if(!styleReady||style==null||v875TouchActive)return;
        try{
            double wave=0.5+0.5*Math.sin(now/900.0);
            LineLayer glow=style.getLayerAs("fs-river-glow");if(glow!=null)glow.setProperties(lineOpacity((float)(0.18+0.08*wave)),lineWidth((float)(1.95+0.28*wave)));
            LineLayer core=style.getLayerAs("fs-rivers-layer");if(core!=null)core.setProperties(lineOpacity((float)(0.90+0.08*wave)),lineWidth((float)(1.00+0.14*wave)));
            String[] ids={"fs-river-alert-risk-layer","fs-river-warning-risk-layer","fs-river-danger-risk-layer"};float[] widths={2.3f,2.7f,3.15f};
            for(int i=0;i<ids.length;i++){LineLayer c=style.getLayerAs(ids[i]);if(c!=null)c.setProperties(lineOpacity(0.98f),lineWidth(widths[i]+(float)(0.16*wave)));LineLayer h=style.getLayerAs(ids[i]+"-glow");if(h!=null)h.setProperties(lineOpacity((float)(0.14+0.10*wave)),lineWidth(widths[i]+1.8f+(float)(0.35*wave)));}
            LineLayer h=style.getLayerAs("fs-river-flow-anim-halo");if(h!=null)h.setProperties(lineOpacity(0.0f));LineLayer c=style.getLayerAs("fs-river-flow-anim-core");if(c!=null)c.setProperties(lineOpacity(0.0f));
        }catch(Exception ignored){}
    } // V0892_SUBTLE_RIVER_FLOW V0892_THIN_BLUE_RIVERS V0892_LIGHT_FLOW_PARTICLES
'''
m=replace_method(m,'v847UpdateMovingGlow',pulse)
m=m.replace('int n = Math.min(36, rivers.size());','int n = Math.min(16, rivers.size()); // V0892_LIGHT_FLOW_PARTICLES')
m=m.replace('main.postDelayed(this, 160L);','main.postDelayed(this, 320L); // V0892_LIGHT_FLOW_PARTICLES')

# GPS/current location: debounce duplicate provider callbacks. If an older chain still
# contains a national river refetch in this callback, remove it; normal source polling
# continues independently in the existing realtime pipeline.
s=span(a,'onLocationChanged')
if not s:raise SystemExit('v0892 onLocationChanged missing')
b=a[s[0]:s[1]]
b=re.sub(r'\s*fetchOfficialRiverData\(\);','\n        // national river polling is independent of GPS',b,count=1)
brace=b.find('{')+1
if brace<=0:raise SystemExit('v0892 location method brace missing')
guard='''\n        long v892Now=System.currentTimeMillis();
        if(v892Now-v892LastLocationWorkAt<3500L)return; // V0892_GPS_LOCATION_DEBOUNCE
        v892LastLocationWorkAt=v892Now;
'''
b=b[:brace]+guard+b[brace:]
a=a[:s[0]]+'    private long v892LastLocationWorkAt=0L; // V0892_GPS_NO_GLOBAL_RIVER_REFRESH\n'+b+a[s[1]:]

# Newest timestamp always wins across catalog, BIPAD live paths and DHM joins.
s=span(a,'loadTrustedRiverStationsV862')
if not s:raise SystemExit('v0892 official loader missing')
helper=r'''    private void v892PutNewest(java.util.Map<String,JSONObject> target,String key,JSONObject row){
        if(target==null||key==null||key.isEmpty()||row==null)return;
        JSONObject old=target.get(key);long nt=v877ObservationTime(row),ot=old==null?0L:v877ObservationTime(old);double nl=v877ObservationLevel(row),ol=old==null?Double.NaN:v877ObservationLevel(old);
        if(old==null||nt>ot||(nt==ot&&Double.isFinite(nl)&&!Double.isFinite(ol)))target.put(key,row);
    } // V0892_NEWEST_OFFICIAL_TIMESTAMP_WINS

'''
a=a[:s[0]]+helper+a[s[0]:]
a,n=re.subn(r'\bnewest\.put\(([^,;]+),\s*([^;]+)\);',r'v892PutNewest(newest,\1,\2);',a)
if n<2:raise SystemExit('v0892 newest writes missing: '+str(n))
s=span(a,'loadTrustedRiverStationsV862')
b=a[s[0]:s[1]]; p=b.find('{')+1
b=b[:p]+'\n        // V0892_RUNTIME_NOCACHE_SOURCE: all trustedPages BIPAD URLs carry current-millisecond _fs'+b[p:]
a=a[:s[0]]+b+a[s[1]:]

g=re.sub(r'versionCode\s+111\b','versionCode 112',g,count=1);g=g.replace("versionName '0.8.91'","versionName '0.8.92'",1)
for x in ['V0892_CLEAR_TOPO_BASE','V0892_SMALL_STATION_DOTS','V0892_THIN_BLUE_RIVERS','V0892_SUBTLE_RIVER_FLOW','V0891_FRESH_ONLY_RISK_LINE','V0890_NO_UNCHANGED_STATION_FLICKER']:
    if x not in m:raise SystemExit('v0892 map contract missing: '+x)
for x in ['V0892_GPS_NO_GLOBAL_RIVER_REFRESH','V0892_GPS_LOCATION_DEBOUNCE','V0892_NEWEST_OFFICIAL_TIMESTAMP_WINS','V0892_RUNTIME_NOCACHE_SOURCE','V0877_CLEAN_FULL_INVENTORY_TRUTH']:
    if x not in a:raise SystemExit('v0892 activity contract missing: '+x)
if 'World_Imagery/MapServer/tile' in m or 'World_Topo_Map/MapServer/tile' not in m:raise SystemExit('v0892 topo swap failed')
if 'versionCode 112' not in g or "versionName '0.8.92'" not in g:raise SystemExit('v0892 version bump failed')
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.92 PASS: clear topo + thin subtle flow + small stations + GPS debounce + newest timestamp wins')
