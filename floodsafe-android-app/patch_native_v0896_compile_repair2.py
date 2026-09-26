from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')
old='if(gen!=v896StationRiverGeneration||out.isEmpty())return;rivers.clear();rivers.addAll(out);riversGeoJson=makeRiversGeoJson(out);v879RiverGeometryKey="v896-station-rivers";'
new='if(gen!=v896StationRiverGeneration||out.isEmpty())return;rivers.clear();rivers.addAll(out);try{riversGeoJson=makeRiversGeoJson(out);}catch(Exception ex){return;}v879RiverGeometryKey="v896-station-rivers"; // V0896_GEOJSON_EXCEPTION_REPAIR'
if old not in s: raise SystemExit('repair2 builder anchor missing')
s=s.replace(old,new,1)
old2='private String v896RiverGeo(String stage){List<RiverWay> z=new ArrayList<>();for(RiverWay r:rivers)if(stage.equals(normalizeStage(r.stage)))z.add(r);return makeRiversGeoJson(z);}'
new2='private String v896RiverGeo(String stage){List<RiverWay> z=new ArrayList<>();for(RiverWay r:rivers)if(stage.equals(normalizeStage(r.stage)))z.add(r);try{return makeRiversGeoJson(z);}catch(Exception ex){return emptyFeatureCollection();}} // V0896_RISK_GEOJSON_EXCEPTION_REPAIR'
if old2 not in s: raise SystemExit('repair2 risk geo anchor missing')
s=s.replace(old2,new2,1)
for x in ('V0896_GEOJSON_EXCEPTION_REPAIR','V0896_RISK_GEOJSON_EXCEPTION_REPAIR'):
    if x not in s: raise SystemExit('missing '+x)
p.write_text(s,encoding='utf-8')
print('v0.8.96 GeoJSON exception compile repair applied')
