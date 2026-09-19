from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

# Narrow v0.8.68 compile repair only: restore the GeoJSON serializer used by the
# already-existing rainfall layers. No river, alert-radius, UI, source, or freshness
# behaviour is changed here.
if 'V0868_RAIN_GEO_COMPILE_FIX' not in m:
    anchor='    private static JSONObject pointFeature(double lo, double la, String name) throws Exception {'
    if anchor not in m:
        raise SystemExit('v0868 rainGeo insert anchor missing')
    helper=r'''    private static String rainGeo(List<RainDot> list, String group) {
        try {
            JSONArray features=new JSONArray();
            if(list!=null)for(RainDot r:list){
                if(r==null||!Double.isFinite(r.lat)||!Double.isFinite(r.lon))continue;
                String g=r.fresh?(r.band==null?"normal":r.band.toLowerCase(Locale.ROOT)):"stale";
                if(!group.equals(g))continue;
                features.put(pointFeature(r.lon,r.lat,r.name==null?"Official rain station":r.name));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",features).toString();
        }catch(Exception e){return emptyFeatureCollection();}
    } // V0868_RAIN_GEO_COMPILE_FIX

'''
    m=m.replace(anchor,helper+anchor,1)

if 'private static String rainGeo(List<RainDot>' not in m:
    raise SystemExit('v0868 rainGeo helper missing after repair')
if 'V0868_RAIN_GEO_COMPILE_FIX' not in m:
    raise SystemExit('v0868 rainGeo repair marker missing')

m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.68 rain GeoJSON compile-only repair PASS')
