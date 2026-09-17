from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

helper=r'''    private static String makeNepalOutsideMask(String districtJson) {
        try {
            JSONObject root=new JSONObject(districtJson);JSONArray holes=new JSONArray();
            JSONArray outer=new JSONArray();
            outer.put(new JSONArray().put(79.1).put(25.3));
            outer.put(new JSONArray().put(89.25).put(25.3));
            outer.put(new JSONArray().put(89.25).put(31.25));
            outer.put(new JSONArray().put(79.1).put(31.25));
            outer.put(new JSONArray().put(79.1).put(25.3));
            holes.put(outer);
            JSONArray fs=root.optJSONArray("features");
            if(fs!=null)for(int i=0;i<fs.length();i++){
                JSONObject f=fs.optJSONObject(i),geom=f==null?null:f.optJSONObject("geometry");if(geom==null)continue;
                String type=geom.optString("type","");JSONArray c=geom.optJSONArray("coordinates");if(c==null)continue;
                if("Polygon".equals(type)){
                    JSONArray ring=c.optJSONArray(0);if(ring!=null&&ring.length()>=4)holes.put(ring);
                }else if("MultiPolygon".equals(type)){
                    for(int j=0;j<c.length();j++){JSONArray poly=c.optJSONArray(j),ring=poly==null?null:poly.optJSONArray(0);if(ring!=null&&ring.length()>=4)holes.put(ring);}
                }
            }
            JSONObject geom=new JSONObject().put("type","Polygon").put("coordinates",holes);
            JSONObject feat=new JSONObject().put("type","Feature").put("properties",new JSONObject()).put("geometry",geom);
            return new JSONObject().put("type","FeatureCollection").put("features",new JSONArray().put(feat)).toString();
        } catch(Exception ignored) { return emptyFeatureCollection(); }
    }

'''
helper_anchor='    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {'
if 'makeNepalOutsideMask(String districtJson)' not in m:
    if helper_anchor not in m: raise SystemExit('Nepal mask helper anchor missing')
    m=m.replace(helper_anchor,helper+helper_anchor,1)

flow_line='            ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#ffffff", 3.1f, 0.92f);'
mask_install=r'''            if (districtGeoJson != null && style.getSource("fs-nepal-outside-mask") == null) {
                String mask=makeNepalOutsideMask(districtGeoJson);
                style.addSource(new GeoJsonSource("fs-nepal-outside-mask", mask));
                style.addLayer(new FillLayer("fs-nepal-outside-mask-layer", "fs-nepal-outside-mask").withProperties(
                        fillColor("#071821"), fillOpacity(1.0f)));
            }
'''
if 'fs-nepal-outside-mask-layer' not in m:
    if flow_line not in m: raise SystemExit('flow layer mask insertion anchor missing')
    m=m.replace(flow_line,flow_line+'\n'+mask_install,1)

for marker in ['makeNepalOutsideMask(String districtJson)','fs-nepal-outside-mask-layer','fillOpacity(1.0f)']:
    if marker not in m: raise SystemExit('Nepal mask prep missing: '+marker)

m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.20 strict Nepal outside-mask prep PASS')
