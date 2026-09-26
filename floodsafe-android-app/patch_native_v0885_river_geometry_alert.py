from pathlib import Path
import re
root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
w_path=src/'RiverAlertWorker.java'; g_path=root/'app/build.gradle'
w=w_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

# Pass app Context into hazard() so the worker can measure distance to bundled river geometry.
w=w.replace('Hazard hazard = hazard(row, homeLat, homeLon, now);','Hazard hazard = hazard(row, homeLat, homeLon, now, app);',1)
w=w.replace('private static Hazard hazard(JSONObject row, double homeLat, double homeLon, long now) {','private static Hazard hazard(JSONObject row, double homeLat, double homeLon, long now, Context app) {',1)
if 'hazard(row, homeLat, homeLon, now, app)' not in w: raise SystemExit('hazard call patch failed')

# Replace station-point-only radius check with affected-river geometry distance first, station fallback only when no matching river geometry exists.
old='''        double distance = haversineKm(homeLat, homeLon, lat, lon);\n        if (!Double.isFinite(distance) || distance > RADIUS_KM) return null;'''
new='''        String riverForDistance = firstString(row, "river_name", "riverName", "station_name", "stationName", "title", "name");\n        double riverDistance = distanceToBundledRiverKm(app, homeLat, homeLon, riverForDistance);\n        double stationDistance = haversineKm(homeLat, homeLon, lat, lon);\n        double distance = Double.isFinite(riverDistance) ? riverDistance : stationDistance;\n        if (!Double.isFinite(distance) || distance > RADIUS_KM) return null; // V0885_AFFECTED_RIVER_2KM_GEOMETRY'''
if old not in w: raise SystemExit('station distance anchor missing')
w=w.replace(old,new,1)

# Add geometry helpers before insideNepal(). The overview asset is lightweight and Nepal-clipped.
anchor='    private static boolean insideNepal(double lat, double lon) {'
if anchor not in w: raise SystemExit('insideNepal anchor missing')
helpers=r'''    private static double distanceToBundledRiverKm(Context app, double lat, double lon, String stationName) {
        String target = riverKey(stationName);
        if (target.isEmpty()) return Double.NaN;
        try (java.io.InputStream in = app.getAssets().open("data/nepal-waterways-tiles/overview.json");
             java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder(); String line;
            while ((line = br.readLine()) != null) sb.append(line);
            JSONObject root = new JSONObject(sb.toString()); JSONArray ways = root.optJSONArray("waterways");
            if (ways == null) return Double.NaN;
            double best = Double.POSITIVE_INFINITY; boolean matched = false;
            for (int i=0;i<ways.length();i++) {
                JSONObject way=ways.optJSONObject(i); if(way==null)continue;
                String wn=firstNonBlank(way.optString("name"),way.optString("name_en"),way.optString("name_ne"));
                String wk=riverKey(wn); if(wk.isEmpty() || !(wk.contains(target)||target.contains(wk)))continue;
                JSONArray pts=way.optJSONArray("pts"); if(pts==null||pts.length()<2)continue; matched=true;
                for(int j=1;j<pts.length();j++){
                    JSONArray a=pts.optJSONArray(j-1),b=pts.optJSONArray(j);if(a==null||b==null||a.length()<2||b.length()<2)continue;
                    double d=segmentKm(lat,lon,a.optDouble(1),a.optDouble(0),b.optDouble(1),b.optDouble(0));if(d<best)best=d;
                }
            }
            return matched && Double.isFinite(best) ? best : Double.NaN;
        } catch (Exception ignored) { return Double.NaN; }
    } // V0885_RIVER_GEOMETRY_DISTANCE

    private static String riverKey(String s){
        if(s==null)return "";String q=s.toLowerCase(Locale.ROOT).trim();
        int at=q.indexOf(" at ");if(at>0)q=q.substring(0,at);
        q=q.replace("river","").replace("khola","").replace("nadi","").replace("नदी","").replace("खोला","");
        return q.replaceAll("[^\\p{L}\\p{N}]","");
    }
    private static String firstNonBlank(String... v){for(String s:v)if(s!=null&&!s.trim().isEmpty())return s.trim();return "";}
    private static double segmentKm(double lat,double lon,double aLat,double aLon,double bLat,double bLon){
        if(!Double.isFinite(aLat)||!Double.isFinite(aLon)||!Double.isFinite(bLat)||!Double.isFinite(bLon))return Double.NaN;
        double cos=Math.cos(Math.toRadians(lat));double ax=(aLon-lon)*111.320*cos,ay=(aLat-lat)*110.574,bx=(bLon-lon)*111.320*cos,by=(bLat-lat)*110.574;
        double dx=bx-ax,dy=by-ay,den=dx*dx+dy*dy,t=den>0?-(ax*dx+ay*dy)/den:0;t=Math.max(0,Math.min(1,t));double x=ax+t*dx,y=ay+t*dy;return Math.sqrt(x*x+y*y);
    }

'''
w=w.replace(anchor,helpers+anchor,1)

g=re.sub(r'versionCode\s+104\b','versionCode 105',g,count=1); g=g.replace("versionName '0.8.84'","versionName '0.8.85'",1)
for x in ['V0885_AFFECTED_RIVER_2KM_GEOMETRY','V0885_RIVER_GEOMETRY_DISTANCE']:
    if x not in w: raise SystemExit('missing '+x)
if "versionName '0.8.85'" not in g or 'versionCode 105' not in g: raise SystemExit('version bump failed')
w_path.write_text(w,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.85 PASS: 2km warning/danger uses matched affected-river geometry, with station fallback only when geometry unavailable')
