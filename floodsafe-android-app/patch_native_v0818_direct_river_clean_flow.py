from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.18
# - Keep a Latin/English river name for official-gauge matching even when the displayed OSM name is Nepali.
# - River tap never borrows a different river's nearest gauge.
# - National view stays clean: districts + major rivers + severe gauges; normal/rain detail appears on zoom.
# - Flow animation is visual only; official gauge status controls blue/yellow/orange/red river overlays.

# Preserve separate display and matching names in both overview and local-tile readers.
m=m.replace('rw.name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"), "नदी / खोला");\n                        rw.type = w.optString("type", "stream");',
'''rw.name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"), "नदी / खोला");
                        rw.matchName = firstNonEmpty(w.optString("name_en"), w.optString("name"), w.optString("name_ne"), rw.name);
                        rw.type = w.optString("type", "stream");''',1)
m=m.replace('rw.name=firstNonEmpty(w.optString("name_ne"),w.optString("name"),w.optString("name_en"),"नदी / खोला");\n                rw.type=w.optString("type","stream");',
'''rw.name=firstNonEmpty(w.optString("name_ne"),w.optString("name"),w.optString("name_en"),"नदी / खोला");
                rw.matchName=firstNonEmpty(w.optString("name_en"),w.optString("name"),w.optString("name_ne"),rw.name);
                rw.type=w.optString("type","stream");''',1)
if m.count('rw.matchName=') + m.count('rw.matchName =') < 2:
    raise SystemExit('matchName population anchors missing')

# National = major rivers only; local = nearest 48. Exact Nepal polygon clipping is
# applied only to the small selected set, so it is accurate without bringing ANR back.
m=m.replace('int keep=Math.min(420,overviewRivers.size());','int keep=Math.min(180,overviewRivers.size());',1)
m=m.replace('for(int i=0;i<Math.min(180,overviewRivers.size());i++)','for(int i=0;i<Math.min(96,overviewRivers.size());i++)',1)
m=m.replace('int keep=Math.min(64,candidates.size());','int keep=Math.min(48,candidates.size());',1)
old_publish='''                String geo=makeRiversGeoJson(chosen),labels=makeRiverLabelsGeoJson(chosen);
                main.post(()->{if(generation!=riverTileGeneration)return;rivers.clear();rivers.addAll(chosen);riversGeoJson=geo;riverLabelsGeoJson=labels;setGeo("fs-rivers",geo);setGeo("fs-river-labels",labels);});'''
new_publish='''                if(districtGeoJson!=null){
                    try{JSONObject clipRoot=new JSONObject(districtGeoJson);List<RiverWay> clipped=new ArrayList<>();for(RiverWay rr:chosen){trimRiverToNepal(rr,clipRoot);if(rr.points.size()>=2)clipped.add(rr);}chosen=clipped;}catch(Exception ignored){}
                }
                String geo=makeRiversGeoJson(chosen),labels=zoom<7.0?emptyFeatureCollection():makeRiverLabelsGeoJson(chosen);
                final List<RiverWay> publish=new ArrayList<>(chosen);
                main.post(()->{if(generation!=riverTileGeneration)return;rivers.clear();rivers.addAll(publish);riversGeoJson=geo;riverLabelsGeoJson=labels;setGeo("fs-rivers",geo);setGeo("fs-river-labels",labels);refreshRiverStatusSources();});'''
if old_publish not in m: raise SystemExit('tile publish anchor missing')
m=m.replace(old_publish,new_publish,1)

# Thin geographic context. Strong colour belongs to official status overlays only.
m=m.replace('lineColor("#003a4b"), lineWidth(6.2f), lineOpacity(0.86f)',
            'lineColor("#0b4653"), lineWidth(3.2f), lineOpacity(0.26f)',1)
m=m.replace('lineColor("#6fe7f6"), lineWidth(1.25f), lineOpacity(0.74f)',
            'lineColor("#72dbe8"), lineWidth(1.05f), lineOpacity(0.58f)',1)
m=m.replace('lineColor("#bdfbff"), lineWidth(1.05f), lineOpacity(0.78f)',
            'lineColor("#d2fbff"), lineWidth(0.80f), lineOpacity(0.24f)',1)
m=m.replace('ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#f4feff", 4.0f, 1.0f);',
            'ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#e6fdff", 2.6f, 0.92f);',1)

# Current NORMAL river is visible blue but not glowing; higher stages keep source colours/glow.
m=m.replace('float coreWidth=normal?0.1f:(alert?2.55f:(warning?3.35f:4.0f));\n        float coreOpacity=normal?0.0f:1.0f;',
            'float coreWidth=normal?2.20f:(alert?2.55f:(warning?3.35f:4.0f));\n        float coreOpacity=normal?0.88f:1.0f;',1)

# Status overlay matching uses the English/Latin match-name rather than a Nepali display label.
m=m.replace('String rk=riverNameKey(r.name);if(rk.length()<3)continue;',
            'String rk=riverMatchKey(r);if(rk.length()<3)continue;',1)
m=m.replace('String key=riverNameKey(r.name);\n        if(key.length()<3)return null;',
            'String key=riverMatchKey(r);\n        if(key.length()<3)return null;',1)

# Replace river dialog and direct matcher. No different-river nearest reference is shown.
show_start=m.find('    private void showRiver(RiverWay r, double la, double lo) {')
show_end=m.find('    private static String formatOfficialTime(long at)',show_start)
if show_start<0 or show_end<0: raise SystemExit('showRiver/matcher anchors missing')
show_block=r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot direct = sameRiverGaugeFor(r, la, lo, true);
        StationDot sameAny = direct!=null?direct:sameRiverGaugeFor(r, la, lo, false);
        StringBuilder msg = new StringBuilder();
        if (direct != null) {
            double d=km(la,lo,direct.lat,direct.lon);
            msg.append("आजको direct official gauge: ").append(direct.name).append(String.format(Locale.US," • %.1f km",d));
            if(Double.isFinite(direct.level))msg.append(String.format(Locale.US,"\nपानीको सतह: %.2f m",direct.level));
            if(Double.isFinite(direct.warning))msg.append(String.format(Locale.US,"\nWarning सीमा: %.2f m",direct.warning));
            if(Double.isFinite(direct.danger))msg.append(String.format(Locale.US,"\nDanger सीमा: %.2f m",direct.danger));
            msg.append("\nSource status: ").append(direct.rawStatus!=null&&!direct.rawStatus.isEmpty()?direct.rawStatus:direct.stage.toUpperCase(Locale.ROOT));
            msg.append("\nOfficial time: ").append(formatOfficialTime(direct.at));
        } else if (sameAny != null) {
            msg.append("यसै नदी/खोलाको official gauge छ, तर current realtime reading उपलब्ध छैन।")
               .append("\nGauge: ").append(sameAny.name)
               .append("\nStatus: STALE / UNKNOWN");
        } else {
            msg.append("यो नदी/खोलामा direct official gauge छैन।")
               .append("\nRealtime status उपलब्ध छैन — अर्को नदीको gauge reference देखाइएको छैन।");
        }
        msg.append("\n\nनदीको line: OpenStreetMap / FloodSafe geometry • status: BIPAD/DHM official gauge");
        new AlertDialog.Builder(getContext()).setTitle(r.name).setMessage(msg.toString()).setPositiveButton("ठीक छ", null).show();
    }

    private StationDot sameRiverGaugeFor(RiverWay r,double la,double lo,boolean freshOnly){
        String key=riverMatchKey(r);if(key.length()<3)return null;StationDot best=null;double d=Double.MAX_VALUE;
        synchronized(stations){for(StationDot s:stations){if(s==null||(freshOnly&&!s.fresh))continue;String sk=riverNameKey(s.name);if(!sameRiverKey(key,sk))continue;double x=km(la,lo,s.lat,s.lon);if(x<d&&x<=45.0){d=x;best=s;}}}
        return best;
    }

    private StationDot directGaugeFor(RiverWay r,double la,double lo){return sameRiverGaugeFor(r,la,lo,true);}

    private static String riverMatchKey(RiverWay r){
        if(r==null)return "";String k=riverNameKey(r.matchName);return k.length()>=3?k:riverNameKey(r.name);
    }
    private static boolean sameRiverKey(String a,String b){
        if(a==null||b==null||a.length()<3||b.length()<3)return false;
        return a.equals(b);
    }
    private static String riverNameKey(String s){
        if(s==null)return "";
        String x=s.toLowerCase(Locale.ROOT)
                .replace('&',' ')
                .replaceAll("\\([^)]*\\)"," ")
                .replaceAll("\\b(at|near|beside|upstream|downstream)\\b.*$"," ")
                .replaceAll("\\b(river|khola|kholaa|nadi|nadhi|stream|station|gauge|hydrological|hydro|hs|bridge|highway|barrage)\\b"," ")
                .replaceAll("[^a-z0-9]"," ").replaceAll("\\s+"," ").trim();
        return x.replace(" ","");
    }
'''
m=m[:show_start]+show_block+m[show_end:]

# National taps do not get stolen by markers that are visually hidden at that zoom.
click_start=m.find('    private boolean onMapClick(LatLng p) {')
click_end=m.find('    private StationDot nearestStation(',click_start)
if click_start<0 or click_end<0: raise SystemExit('onMapClick anchors missing')
click_block=r'''    private boolean onMapClick(LatLng p) {
        StationDot nearest = nearestStation(p.getLatitude(), p.getLongitude());
        RainDot nearestRain = nearestRain(p.getLatitude(), p.getLongitude());
        double zoom = map == null ? 6.0 : map.getCameraPosition().zoom;
        double stationThreshold = Math.max(0.45, 5.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        double rd=nearestRain==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearestRain.lat,nearestRain.lon);
        boolean stationShown=nearest!=null&&(zoom>=7.0||isSevereStage(nearest.stage));
        boolean rainShown=nearestRain!=null&&zoom>=8.0;
        if (rainShown && rd <= stationThreshold && rd < sd) { showRain(nearestRain); return true; }
        if (stationShown && sd <= stationThreshold) { if (stationTapListener != null) stationTapListener.onStationTap(nearest.original); return true; }
        if (rainShown && rd <= stationThreshold) { showRain(nearestRain); return true; }
        RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.25, 10.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))));
        if (rw != null) { showRiver(rw, p.getLatitude(), p.getLongitude()); return true; }
        return false;
    }

    private static boolean isSevereStage(String s){String x=normalizeStage(s);return "alert".equals(x)||"warning".equals(x)||"danger".equals(x);}

'''
m=m[:click_start]+click_block+m[click_end:]

# Zoom-aware marker publishing: overview stays clean; zoom reveals current gauges and rain details.
station_start=m.find('    private void refreshStationSources() {')
rain_start=m.find('    private void refreshRainSources() {',station_start)
user_start=m.find('    private void refreshUserSource() {',rain_start)
if station_start<0 or rain_start<0 or user_start<0: raise SystemExit('refresh source anchors missing')
source_block=r'''    private void refreshStationSources() {
        if (!styleReady || style == null) return;
        List<StationDot> snapshot; synchronized (stations) { snapshot = new ArrayList<>(stations); }
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        boolean detail=zoom>=7.0;
        setGeo("fs-stale", detail?stationGeo(snapshot, "stale"):emptyFeatureCollection());
        setGeo("fs-normal", detail?stationGeo(snapshot, "normal"):emptyFeatureCollection());
        setGeo("fs-alert", stationGeo(snapshot, "alert"));
        setGeo("fs-warning", stationGeo(snapshot, "warning"));
        setGeo("fs-danger", stationGeo(snapshot, "danger"));
        refreshRiverStatusSources();
        setGeo("fs-station-labels", zoom>=8.0?stationGeoImportant(snapshot):emptyFeatureCollection());
    }

    private void refreshRainSources() {
        if (!styleReady || style == null) return;
        List<RainDot> snapshot; synchronized (rainStations) { snapshot = new ArrayList<>(rainStations); }
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        boolean showRainMarkers=zoom>=8.0;
        if(!showRainMarkers){
            setGeo("fs-rain-stale",emptyFeatureCollection());setGeo("fs-rain-normal",emptyFeatureCollection());setGeo("fs-rain-alert",emptyFeatureCollection());setGeo("fs-rain-warning",emptyFeatureCollection());setGeo("fs-rain-danger",emptyFeatureCollection());return;
        }
        setGeo("fs-rain-stale", zoom>=9.0?rainGeo(snapshot, "stale"):emptyFeatureCollection());
        setGeo("fs-rain-normal", rainGeo(snapshot, "normal"));
        setGeo("fs-rain-alert", rainGeo(snapshot, "alert"));
        setGeo("fs-rain-warning", rainGeo(snapshot, "warning"));
        setGeo("fs-rain-danger", rainGeo(snapshot, "danger"));
    }

'''
m=m[:station_start]+source_block+m[user_start:]

m=m.replace('map.addOnCameraIdleListener(this::refreshVisibleRiverTiles);',
            'map.addOnCameraIdleListener(()->{refreshVisibleRiverTiles();refreshStationSources();refreshRainSources();});',1)

# Continuous but lightweight web-style flow beads; no river/station matching occurs per animation frame.
m=m.replace('JSONArray features=new JSONArray();int n=Math.min(30,visibleSnapshot.size());',
            'JSONArray features=new JSONArray();int n=Math.min(24,visibleSnapshot.size());',1)
m=m.replace('main.postDelayed(this,180L);','main.postDelayed(this,220L);',1)

# RiverWay now keeps display and official-match names separately.
m=m.replace('String name, type; final List<double[]> points = new ArrayList<>();',
            'String name, matchName, type; final List<double[]> points = new ArrayList<>();',1)
if 'String name, matchName, type' not in m: raise SystemExit('RiverWay matchName field anchor missing')

# Explain the interaction truthfully.
a=a.replace('mapSub.setText(t("जिल्ला + नदी network • 🔵 official gauge • 🟡 Alert • 🟠 Warning • 🔴 Danger","District + river network • 🔵 official gauge • 🟡 Alert • 🟠 Warning • 🔴 Danger"));',
'''mapSub.setText(t("जिल्ला + मुख्य नदी • नदी थिच्दा त्यही नदीको official gauge • zoom गर्दा local/rain detail","District + major rivers • river tap uses same-river official gauge • zoom for local/rain detail"));''',1)

# Version bump.
g=g.replace('versionCode 37','versionCode 38',1).replace("versionName '0.8.17'","versionName '0.8.18'",1)
if 'versionCode 38' not in g or "versionName '0.8.18'" not in g: raise SystemExit('v0.8.18 version bump failed')

m_path.write_text(m,encoding='utf-8');a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for marker in ['String name, matchName, type','sameRiverGaugeFor','riverMatchKey','अर्को नदीको gauge reference देखाइएको छैन','Math.min(180,overviewRivers.size())','Math.min(48,candidates.size())','zoom<7.0?emptyFeatureCollection()','showRainMarkers=zoom>=8.0','coreOpacity=normal?0.88f','Math.min(24,visibleSnapshot.size())','main.postDelayed(this,220L)']:
    if marker not in m: raise SystemExit('v0.8.18 map marker missing: '+marker)
if 'नजिकको आजको official gauge reference' in m or 'StationDot near = nearestFreshStation' in m:
    raise SystemExit('different-river nearest reference remained')
print('FloodSafe v0.8.18 direct same-river realtime + clean web flow map PASS')
