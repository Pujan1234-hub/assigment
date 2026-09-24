from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app'
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.92 real-device cleanup:
# - clean readable topo base instead of muddy satellite overview
# - thin blue monitored rivers with subtle low-cost movement
# - smaller station dots so Nepal remains readable
# - current-location callback must not launch a full national hydrology refetch
# - every official-source merge is timestamp-arbitrated; an older row cannot overwrite newer

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

def replace_method(text,name,new_block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('v0892 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# -----------------------------------------------------------------------------
# A) Clear overview map. Keep MapLibre/native map, only swap the base tiles.
# -----------------------------------------------------------------------------
if 'World_Imagery/MapServer/tile' not in m:
    raise SystemExit('v0892 imagery URL anchor missing')
m=m.replace('World_Imagery/MapServer/tile','World_Topo_Map/MapServer/tile')
# Marker beside a stable field rather than inside the URL string.
field_anchor='    private boolean terrain = false;\n'
if 'V0892_CLEAR_TOPO_BASE' not in m:
    if field_anchor not in m:raise SystemExit('v0892 terrain field anchor missing')
    m=m.replace(field_anchor,field_anchor+'    // V0892_CLEAR_TOPO_BASE: readable ESRI topo base for Nepal overview\n',1)

# -----------------------------------------------------------------------------
# B) Smaller point symbols and thinner blue monitored river geometry.
# -----------------------------------------------------------------------------
sp=method_span(m,'installGeoLayers')
if not sp:raise SystemExit('v0892 installGeoLayers missing')
block=m[sp[0]:sp[1]]
# Normal river layer: thin but still easy to tap; risk overlays remain distinct.
def tune_line(block,layer,width,opacity):
    pat=r'(new LineLayer\("'+re.escape(layer)+r'"[\s\S]*?\.withProperties\()([\s\S]*?)(\)\);)'
    mm=re.search(pat,block)
    if not mm:return block,False
    props=mm.group(2)
    props=re.sub(r'lineWidth\([^\)]*\)',f'lineWidth({width}f)',props,count=1)
    props=re.sub(r'lineOpacity\([^\)]*\)',f'lineOpacity({opacity}f)',props,count=1)
    return block[:mm.start(2)]+props+block[mm.end(2):],True

block,ok1=tune_line(block,'fs-river-glow',2.10,0.22)
block,ok2=tune_line(block,'fs-rivers-layer',1.08,0.96)
if not ok1 or not ok2:raise SystemExit('v0892 base river layer anchors missing')

# Exact station point source calls. Keep severe stages a little larger than normal.
point_cfg={
 'fs-flow-particles':('fs-flow-particles-layer','#d6fbff','1.10','0.58'),
 'fs-stale':('fs-stale-layer','#8e99a5','2.05','0.84'),
 'fs-normal':('fs-normal-layer','#22c55e','2.25','0.92'),
 'fs-alert':('fs-alert-layer','#facc15','2.65','0.98'),
 'fs-warning':('fs-warning-layer','#f59e0b','2.95','1.0'),
 'fs-danger':('fs-danger-layer','#ef4444','3.25','1.0'),
}
for source,(layer,color,radius,opacity) in point_cfg.items():
    pat=r'ensurePointSource\("'+re.escape(source)+r'"\s*,\s*"'+re.escape(layer)+r'"\s*,\s*"[^"]+"\s*,\s*[^,]+\s*,\s*[^\)]+\);'
    repl=f'ensurePointSource("{source}", "{layer}", "{color}", {radius}f, {opacity}f);'
    block,n=re.subn(pat,repl,block,count=1)
    if n!=1:raise SystemExit('v0892 point layer anchor missing: '+source)
block=block[:block.find('{')+1]+'\n        // V0892_SMALL_STATION_DOTS V0892_THIN_BLUE_RIVERS'+block[block.find('{')+1:]
m=m[:sp[0]]+block+m[sp[1]:]

# Thin point outlines as well.
sp=method_span(m,'ensurePointSource')
if not sp:raise SystemExit('v0892 ensurePointSource missing')
ep=m[sp[0]:sp[1]]
ep=re.sub(r'circleStrokeWidth\([^\)]*\)', 'circleStrokeWidth(0.65f)', ep, count=1)
if 'V0892_POINT_STROKE_LIGHT' not in ep:
    p=ep.find('{')+1;ep=ep[:p]+'\n        // V0892_POINT_STROKE_LIGHT'+ep[p:]
m=m[:sp[0]]+ep+m[sp[1]:]

# -----------------------------------------------------------------------------
# C) Cheap subtle flow instead of heavy neon pulsing.
# -----------------------------------------------------------------------------
pulse=r'''    private void v847UpdateMovingGlow(long now){
        if(!styleReady||style==null||v875TouchActive)return;
        try{
            double wave=0.5+0.5*Math.sin(now/900.0);
            LineLayer baseGlow=style.getLayerAs("fs-river-glow");
            if(baseGlow!=null)baseGlow.setProperties(lineOpacity((float)(0.18+0.08*wave)),lineWidth((float)(1.95+0.28*wave)));
            LineLayer baseCore=style.getLayerAs("fs-rivers-layer");
            if(baseCore!=null)baseCore.setProperties(lineOpacity((float)(0.90+0.08*wave)),lineWidth((float)(1.00+0.14*wave)));
            String[] coreIds={"fs-river-alert-risk-layer","fs-river-warning-risk-layer","fs-river-danger-risk-layer"};
            float[] widths={2.3f,2.7f,3.15f};
            for(int i=0;i<coreIds.length;i++){
                LineLayer core=style.getLayerAs(coreIds[i]);
                if(core!=null)core.setProperties(lineOpacity(0.98f),lineWidth(widths[i]+(float)(0.16*wave)));
                LineLayer glow=style.getLayerAs(coreIds[i]+"-glow");
                if(glow!=null)glow.setProperties(lineOpacity((float)(0.14+0.10*wave)),lineWidth(widths[i]+1.8f+(float)(0.35*wave)));
            }
            LineLayer oldHalo=style.getLayerAs("fs-river-flow-anim-halo");if(oldHalo!=null)oldHalo.setProperties(lineOpacity(0.0f));
            LineLayer oldCore=style.getLayerAs("fs-river-flow-anim-core");if(oldCore!=null)oldCore.setProperties(lineOpacity(0.0f));
        }catch(Exception ignored){}
    } // V0892_SUBTLE_RIVER_FLOW V0892_THIN_BLUE_RIVERS
'''
m=replace_method(m,'v847UpdateMovingGlow',pulse)

# Reduce particle work while retaining visible direction/movement.
m=m.replace('int n = Math.min(36, rivers.size());','int n = Math.min(16, rivers.size()); // V0892_LIGHT_FLOW_PARTICLES')
m=m.replace('main.postDelayed(this, 160L);','main.postDelayed(this, 320L); // V0892_LIGHT_FLOW_PARTICLES')
if 'V0892_LIGHT_FLOW_PARTICLES' not in m:
    # Later chains may have already removed the old particle loop; the line pulse above is enough.
    m=m.replace('// V0892_SUBTLE_RIVER_FLOW V0892_THIN_BLUE_RIVERS','// V0892_SUBTLE_RIVER_FLOW V0892_THIN_BLUE_RIVERS V0892_LIGHT_FLOW_PARTICLES',1)

# -----------------------------------------------------------------------------
# D) Current-location tap: never trigger a whole national source/network refresh from GPS.
# The normal polling pipeline continues independently.
# -----------------------------------------------------------------------------
sp=method_span(a,'onLocationChanged')
if not sp:raise SystemExit('v0892 onLocationChanged missing')
loc=a[sp[0]:sp[1]]
loc,n=re.subn(r'\s*fetchOfficialRiverData\(\);', '\n        // V0892_GPS_NO_GLOBAL_RIVER_REFRESH: normal source poll continues independently', loc, count=1)
if n==0 and 'V0892_GPS_NO_GLOBAL_RIVER_REFRESH' not in loc:
    raise SystemExit('v0892 GPS global refresh anchor missing')
a=a[:sp[0]]+loc+a[sp[1]:]

# -----------------------------------------------------------------------------
# E) Newest official timestamp always wins across catalog/BIPAD/DHM merge paths.
# v0.8.85 pre-seeds catalog observations; this guard prevents an older row from later
# replacing a newer one and also resolves equal-time rows in favour of a real level.
# -----------------------------------------------------------------------------
if 'V0892_NEWEST_OFFICIAL_TIMESTAMP_WINS' not in a:
    sp=method_span(a,'loadTrustedRiverStationsV862')
    if not sp:raise SystemExit('v0892 official loader missing')
    helper=r'''    private void v892PutNewest(java.util.Map<String,JSONObject> target,String key,JSONObject row){
        if(target==null||key==null||key.isEmpty()||row==null)return;
        JSONObject old=target.get(key);
        long nt=v877ObservationTime(row),ot=old==null?0L:v877ObservationTime(old);
        double nl=v877ObservationLevel(row),ol=old==null?Double.NaN:v877ObservationLevel(old);
        if(old==null||nt>ot||(nt==ot&&Double.isFinite(nl)&&!Double.isFinite(ol)))target.put(key,row);
    } // V0892_NEWEST_OFFICIAL_TIMESTAMP_WINS

'''
    a=a[:sp[0]]+helper+a[sp[0]:]

# Only rewrite puts to the observation map named `newest`; metadata maps are untouched.
a,n=re.subn(r'\bnewest\.put\(([^,;]+),\s*([^;]+)\);',r'v892PutNewest(newest,\1,\2);',a)
if n<2:raise SystemExit('v0892 expected multiple newest observation writes, got '+str(n))

# Add no-cache uniqueness to every trusted BIPAD path already using &_fs=<now>.
# The loader already has `_fs`; keeping a millisecond timestamp ensures each poll is a fresh URL.
if 'V0892_RUNTIME_NOCACHE_SOURCE' not in a:
    sp=method_span(a,'loadTrustedRiverStationsV862')
    if not sp:raise SystemExit('v0892 loader span lost')
    loader=a[sp[0]:sp[1]]
    p=loader.find('{')+1
    loader=loader[:p]+'\n        // V0892_RUNTIME_NOCACHE_SOURCE: trustedPages URLs include current-millisecond _fs cache buster'+loader[p:]
    a=a[:sp[0]]+loader+a[sp[1]:]

# Version bump.
g=re.sub(r'versionCode\s+111\b','versionCode 112',g,count=1)
g=g.replace("versionName '0.8.91'","versionName '0.8.92'",1)

required_m=['V0892_CLEAR_TOPO_BASE','V0892_SMALL_STATION_DOTS','V0892_THIN_BLUE_RIVERS','V0892_SUBTLE_RIVER_FLOW','V0891_FRESH_ONLY_RISK_LINE','V0890_NO_UNCHANGED_STATION_FLICKER']
required_a=['V0892_GPS_NO_GLOBAL_RIVER_REFRESH','V0892_NEWEST_OFFICIAL_TIMESTAMP_WINS','V0892_RUNTIME_NOCACHE_SOURCE','V0877_CLEAN_FULL_INVENTORY_TRUTH']
for x in required_m:
    if x not in m:raise SystemExit('v0892 map contract missing: '+x)
for x in required_a:
    if x not in a:raise SystemExit('v0892 activity contract missing: '+x)
if 'World_Imagery/MapServer/tile' in m or 'World_Topo_Map/MapServer/tile' not in m:raise SystemExit('v0892 base map swap failed')
if 'versionCode 112' not in g or "versionName '0.8.92'" not in g:raise SystemExit('v0892 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.92 PASS: clear topo map + thin subtle river flow + small station dots + GPS no-stall + newest official timestamp wins')
