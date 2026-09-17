from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.45 source-parity lock:
# - UI/map/list use ONLY rows actually available from BIPAD/DHM latest=true.
# - catalog-only stations are hidden instead of being shown as stale/offline.
# - latest endpoint is re-read on the foreground live poll; source changes propagate quickly.
# - visible rivers remain progressive, but tap target is screen-scale rather than too-small km math.
# - official source status/value/time remain authoritative; no app-invented flood stage.


def replace_between(text,start,end,replacement,label):
    i=text.find(start)
    if i<0: raise SystemExit(label+' start anchor missing')
    j=text.find(end,i)
    if j<0: raise SystemExit(label+' end anchor missing')
    return text[:i]+replacement+text[j:]

# -----------------------------------------------------------------------------
# BIPAD/DHM parity: latest=true is the display truth. Do NOT merge catalog-only rows.
# This fixes cases such as a catalog station being displayed as OFFLINE while it is not
# present in the live/latest source panel. If the source starts publishing it later,
# the next foreground poll adds it automatically.
# -----------------------------------------------------------------------------
latest_only=r'''    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{
        List<RiverStation> out=new ArrayList<>();
        JSONArray latest=new JSONArray();
        try{latest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000",now);}catch(Exception ignored){}

        for(int i=0;i<latest.length();i++){
            JSONObject r=latest.optJSONObject(i);if(r==null)continue;
            try{r.put("_floodsafeLatestEndpoint",true);}catch(Exception ignored){}
            RiverStation s=parseStation(r,now);
            if(s!=null&&s.fresh)out.add(s); // V0845_LATEST_ONLY_DISPLAY
        }

        // Network/CORS fallback only. The proxy is accepted only for rows that parse as
        // current official observations; stale/catalog rows are never reintroduced.
        if(out.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now));
                for(int i=0;i<rr.length();i++){
                    JSONObject r=rr.optJSONObject(i);if(r==null)continue;
                    try{r.put("_floodsafeLatestEndpoint",true);}catch(Exception ignored){}
                    RiverStation s=parseStation(r,now);
                    if(s!=null&&s.fresh)out.add(s);
                }
            }catch(Exception ignored){}
        }
        return out;
    }

'''
a=replace_between(a,'    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{','    private JSONArray trustedPages(',latest_only,'v0.8.45 latest-only station loader')

# Summary must describe what is actually displayed now: only current source rows.
old='feedFresh.setText(t("Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale,"Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale));'
new='feedFresh.setText(t("BIPAD/DHM अहिले उपलब्ध: "+copy.size()+" • 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • source status अज्ञात "+stale,"BIPAD/DHM available now: "+copy.size()+" • 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • source status unknown "+stale)); // V0845_SOURCE_PARITY_SUMMARY'
if old in a:
    a=a.replace(old,new,1)
elif 'V0845_SOURCE_PARITY_SUMMARY' not in a:
    raise SystemExit('v0.8.45 refreshRiverUi summary anchor missing')

# Keep the existing web-match 10 second foreground cadence. If an older chain somehow
# restored 60 seconds, tighten it back to 10 seconds. This is near-real-time polling of
# the official source, not synthetic data.
a=a.replace('main.postDelayed(this,60_000L);','main.postDelayed(this,10_000L);')
a=a.replace('main.postDelayed(livePoll,60_000L);','main.postDelayed(livePoll,10_000L);')
if 'main.postDelayed(this,10_000L)' not in a:
    raise SystemExit('v0.8.45 10-second source poll marker missing')

# -----------------------------------------------------------------------------
# River taps: v0.8.44 fixed exact line-segment distance and visible==touchable lists.
# v0.8.43 still used a geographic threshold that becomes much smaller than a finger at
# high zoom. Compute a ~16 px target from Web-Mercator scale, with safe caps.
# -----------------------------------------------------------------------------
click_start=m.find('    private boolean onMapClick(LatLng p) {')
click_end=m.find('    private static boolean isSevereStage',click_start)
if click_start<0 or click_end<0:
    raise SystemExit('v0.8.45 onMapClick anchors missing')
click_block=m[click_start:click_end]
pat=r'RiverWay rw=nearestRiver\(p\.getLatitude\(\),p\.getLongitude\(\),[^;]+;'
repl='double riverTapKm=v845RiverTapRadiusKm(p.getLatitude(),zoom); RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),riverTapKm); // V0845_SCREEN_SCALE_RIVER_TAP'
click_block,n=re.subn(pat,repl,click_block,count=1)
if n!=1:
    raise SystemExit('v0.8.45 river click threshold anchor missing')
m=m[:click_start]+click_block+m[click_end:]

helper=r'''    private static double v845RiverTapRadiusKm(double lat,double zoom){
        // Web-Mercator ground resolution (km/pixel) × ~16 finger pixels.
        double kmPerPixel=156.54303392*Math.max(0.35,Math.cos(Math.toRadians(lat)))/Math.pow(2.0,zoom);
        return Math.max(0.16,Math.min(18.0,kmPerPixel*16.0));
    }

'''
anchor='    private RiverWay nearestRiver(double la,double lo,double thresholdKm) {'
if anchor not in m:
    raise SystemExit('v0.8.45 nearestRiver anchor missing')
if 'private static double v845RiverTapRadiusKm' not in m:
    m=m.replace(anchor,helper+anchor,1)

# Version bump.
g=g.replace('versionCode 64','versionCode 65',1).replace("versionName '0.8.44'","versionName '0.8.45'",1)
if 'versionCode 65' not in g or "versionName '0.8.45'" not in g:
    raise SystemExit('v0.8.45 version bump failed')

joined=a+'\n'+m
for marker in [
    'V0845_LATEST_ONLY_DISPLAY','V0845_SOURCE_PARITY_SUMMARY','V0845_SCREEN_SCALE_RIVER_TAP',
    'v845RiverTapRadiusKm','V0844_VISIBLE_EQUALS_TOUCHABLE','v844PointSegmentKm',
    'raw==null||raw.trim().isEmpty()',
    'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))']:
    if marker not in joined:
        raise SystemExit('v0.8.45 marker missing: '+marker)

# Hard guard: display loader must not merge catalog and latest anymore.
loader=a[a.find('    private List<RiverStation> loadTrustedRiverStations'):a.find('    private JSONArray trustedPages(')]
if 'mergeTrustedRiverRows' in loader or 'river-stations/?limit=2000' in loader:
    raise SystemExit('v0.8.45 catalog rows still used by display loader')

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.45 BIPAD latest-only source parity + screen-scale river taps PASS')
