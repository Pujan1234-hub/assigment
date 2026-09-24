from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

bad='rivers.clear();rivers.addAll(monitored);riversGeoJson=makeRiversGeoJson(monitored);'
good='rivers.clear();rivers.addAll(monitored);try{riversGeoJson=makeRiversGeoJson(monitored);}catch(Exception e){riversGeoJson=emptyFeatureCollection();} // V0887_COMPILE_SAFE_RIVER_GEOJSON'
if bad in m:
    m=m.replace(bad,good,1)
elif 'V0887_COMPILE_SAFE_RIVER_GEOJSON' not in m:
    raise SystemExit('v0887 compile-fix monitored river GeoJSON anchor missing')

m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.87 compile fix PASS: monitored river GeoJSON exception handled')
