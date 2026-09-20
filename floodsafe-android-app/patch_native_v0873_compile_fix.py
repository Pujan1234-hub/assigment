from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')

# v0.8.73 compile-only repair. Do not change the accepted UI, river geometry,
# alert radius, source values, thresholds, language, or notification behavior.
# The existing 1-second livePoll already calls refreshRainStations(); the v0.8.73
# parity patch accidentally added a second call to a method that does not exist.
bad='refreshRain(); // V0873_ONE_SECOND_RAIN_RECHECK'
if bad in a:
    a=a.replace(bad,'/* V0873_ONE_SECOND_RAIN_RECHECK: refreshRainStations() already runs on this same 1s livePoll */',1)
elif 'V0873_ONE_SECOND_RAIN_RECHECK' not in a:
    raise SystemExit('v0873 compile fix: rain recheck marker missing')
if 'refreshRainStations();' not in a:
    raise SystemExit('v0873 compile fix: real rain refresh method call missing')

# v0.8.72 may already carry a compatible rainGeo helper. Reuse it when present;
# only restore the tiny adapter if the fully-native baseline no longer has one.
if 'private static String rainGeo(' not in m:
    anchor='    private void refreshRainSources() {'
    if anchor not in m:
        raise SystemExit('v0873 compile fix: refreshRainSources anchor missing')
    helper=r'''    private static String rainGeo(List<RainDot> list,String group) {
        try {
            JSONArray features=new JSONArray();
            if(list!=null)for(RainDot r:list){
                if(r==null||!Double.isFinite(r.lat)||!Double.isFinite(r.lon))continue;
                String raw=r.band==null?"":r.band.toLowerCase(Locale.ROOT);
                String g=(!r.fresh||raw.contains("stale"))?"stale":normalizeStage(raw);
                if(!group.equals(g))continue;
                features.put(pointFeature(r.lon,r.lat,r.name==null?"Official rain station":r.name));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",features).toString();
        }catch(Exception e){return emptyFeatureCollection();}
    } // V0873_RAIN_GEO_COMPILE_FIX

'''
    m=m.replace(anchor,helper+anchor,1)

if 'refreshRain(); // V0873_ONE_SECOND_RAIN_RECHECK' in a:
    raise SystemExit('v0873 compile fix: nonexistent refreshRain call remains')
for x in ['V0873_ONE_SECOND_RAIN_RECHECK','refreshRainStations();']:
    if x not in a:raise SystemExit('v0873 compile fix activity verification failed: '+x)
if 'private static String rainGeo(' not in m:
    raise SystemExit('v0873 compile fix map verification failed: rainGeo helper missing')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.73 compile repair PASS: real 1s rain refresh retained + compatible native rain GeoJSON helper present')
