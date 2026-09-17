from pathlib import Path
import runpy

root = Path(__file__).resolve().parent
p = root / 'patch_native_v0850_official_parity_sathi_language.py'
s = p.read_text(encoding='utf-8')

old = '''old='                String g = s.fresh ? normalizeStage(s.stage) : "stale";'
new='                String g = s.online ? "normal" : "stale"; // V0850_MAP_AVAILABILITY_GROUP'
if old in m:m=m.replace(old,new,1)
elif 'V0850_MAP_AVAILABILITY_GROUP' not in m:raise SystemExit('v0850 stationGeo group anchor')'''
new = r'''if 'V0850_MAP_AVAILABILITY_GROUP' not in m:
    sg=m.find('    private static String stationGeo(')
    eg=m.find('    private static JSONObject pointFeature(',sg)
    if sg<0 or eg<0: raise SystemExit('v0850 stationGeo method anchors')
    station_geo=r'''    private static String stationGeo(List<StationDot> list, String group) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) {
                String g = s.online ? "normal" : "stale"; // V0850_MAP_AVAILABILITY_GROUP
                if (!group.equals(g)) continue;
                f.put(pointFeature(s.lon, s.lat, s.name));
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }

'''
    m=m[:sg]+station_geo+m[eg:]'''

if old not in s:
    raise SystemExit('v0850 runner could not find strict stationGeo block')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
runpy.run_path(str(p), run_name='__main__')
