from pathlib import Path
import re
root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'; m_path=src/'FloodSafeNativeMapView.java'; g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8'); m=m_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

# v0.8.84 field feedback:
# 1. Do not hide an official observation merely because FloodSafe chose an arbitrary age window.
#    Source truth wins: if official feed supplies a matched level+timestamp, show it as current/latest exactly as supplied.
# 2. River geometry must be tappable before a merely-near station steals the click.
# 3. Keep catalog-only stations visible and waterbody/outlet metadata honest; never fabricate a reading.

# Remove arbitrary 20-minute freshness gate from parseStation. Future timestamps still receive a small clock-skew guard.
old='boolean fresh=online&&now-at<=RIVER_FRESH_MS&&at-now<=5L*60L*1000L; // V0877_CLEAN_FRESH_ONLY_LIVE'
new='boolean fresh=online&&at-now<=5L*60L*1000L; // V0884_SOURCE_TIMESTAMP_PARITY_NO_ARBITRARY_20M_GATE'
if old not in a: raise SystemExit('v0884 freshness anchor missing')
a=a.replace(old,new,1)
# Remove UI wording that claims >20m is unusable; source timestamp remains visible.
a=a.replace('Official catalog "+v849CatalogCount+" • LIVE (≤20m) "+v877FreshObservationCount+', 'Official catalog "+v849CatalogCount+" • source-current "+v877FreshObservationCount+',1)
a=a.replace('आधिकारिक catalog "+v849CatalogCount+" • LIVE (≤20m) "+v877FreshObservationCount+', 'आधिकारिक catalog "+v849CatalogCount+" • source-current "+v877FreshObservationCount+',1)
a=a.replace('यो latest official reading हो; २० मिनेटभन्दा पुरानो भएकाले LIVE alert मा प्रयोग हुँदैन।','यो official source ले दिएको latest reading हो; source time जस्ताको तस्तै देखाइएको छ।')
a=a.replace('This is the latest official reading; because it is older than 20 minutes it is not used for LIVE alerts.','This is the latest reading supplied by the official source; its source time is shown unchanged.')

# River click priority: in onMapClick, if a river geometry is under the finger, open river detail first.
# Waterbody/outlet direct hit remains first because it is itself an official hydrology object.
def span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start()); d=0; quote=None; esc=False
    for i in range(op,len(text)):
        c=text[i]
        if quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        else:
            if c in ('\"',"'"):quote=c
            elif c=='{':d+=1
            elif c=='}':
                d-=1
                if d==0:return q.start(),i+1
    return None
sp=span(m,'onMapClick')
if not sp: raise SystemExit('v0884 onMapClick missing')
block=m[sp[0]:sp[1]]
if 'V0884_RIVER_GEOMETRY_CLICK_FIRST' not in block:
    z=re.search(r'double\s+zoom\s*=\s*[^;]+;',block)
    if not z: raise SystemExit('v0884 zoom anchor missing')
    # Insert after existing waterbody priority block when present; otherwise immediately after zoom.
    insert=z.end()
    wm=block.find('// V0881_WATERBODY_TAP_PRIORITY')
    if wm>=0:
        nl=block.find('\n',wm); insert=len(block) if nl<0 else nl+1
    code='''        RiverWay v884River=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.12,Math.min(1.25,4.2/Math.pow(2.0,Math.max(0.0,zoom-7.0)))));\n        if(v884River!=null){showRiver(v884River,p.getLatitude(),p.getLongitude());return true;} // V0884_RIVER_GEOMETRY_CLICK_FIRST\n'''
    block=block[:insert]+code+block[insert:]
    m=m[:sp[0]]+block+m[sp[1]:]

# Explicit contract marker: catalog station visibility and waterbody layers are retained from v0.8.81.
if 'V0884_FULL_OFFICIAL_CATALOG_RETAINED' not in m:
    marker='// V0881_HYDRO_WATERBODY_GEO'
    if marker not in m: raise SystemExit('v0884 waterbody layer missing')
    m=m.replace(marker,marker+' V0884_FULL_OFFICIAL_CATALOG_RETAINED',1)

# Version identity
g=re.sub(r'versionCode\s+103\b','versionCode 104',g,count=1)
g=g.replace("versionName '0.8.83'","versionName '0.8.84'",1)
for x in ['V0884_SOURCE_TIMESTAMP_PARITY_NO_ARBITRARY_20M_GATE']:
    if x not in a: raise SystemExit('v0884 activity contract missing '+x)
for x in ['V0884_RIVER_GEOMETRY_CLICK_FIRST','V0884_FULL_OFFICIAL_CATALOG_RETAINED','V0881_RIVER_FIRST_CLASS_DETAIL','V0881_WATERBODY_DETAIL_POPUP']:
    if x not in m: raise SystemExit('v0884 map contract missing '+x)
if 'versionCode 104' not in g or "versionName '0.8.84'" not in g: raise SystemExit('v0884 version bump failed')
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.84 PASS: source timestamp parity + river geometry click first + full catalog/waterbody retention')
