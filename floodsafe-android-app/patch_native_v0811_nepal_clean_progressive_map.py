from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
map_path=src/'FloodSafeNativeMapView.java'
gradle_path=root/'app/build.gradle'
helper=map_path.read_text(encoding='utf-8')
gradle=gradle_path.read_text(encoding='utf-8')

# Final native map cleanup: render only Nepal-clipped river geometry and reveal
# more detail as the user zooms. Keep heavy tile/geometry work off the UI thread.
start=helper.find('    private void refreshVisibleRiverTiles() {')
end=helper.find('    private List<RiverWay> readRiverTile',start)
if start<0 or end<0:
    raise SystemExit('refreshVisibleRiverTiles block missing')

new_block=r'''    private void refreshVisibleRiverTiles() {
        if (!styleReady || style == null || map == null || overviewRivers.isEmpty()) return;
        CameraPosition cp = map.getCameraPosition();
        final double zoom = cp.zoom;
        LatLng center = cp.target;
        final String zoomBand = nativeZoomBand(zoom);
        applyNativeZoomStyle(zoom);

        if (zoom < 7.8) {
            String key = "overview:" + zoomBand;
            if (key.equals(lastRiverTileKey)) return;
            lastRiverTileKey = key;
            final int generation = ++riverTileGeneration;
            io.execute(() -> {
                try {
                    JSONObject districts = districtGeoJson == null ? null : new JSONObject(districtGeoJson);
                    List<RiverWay> render = nativeCleanForZoom(overviewRivers, zoom, districts);
                    String geo = makeRiversGeoJson(render);
                    String labels = makeRiverLabelsGeoJson(render);
                    main.post(() -> {
                        if (generation != riverTileGeneration) return;
                        rivers.clear(); rivers.addAll(render);
                        riversGeoJson = geo; riverLabelsGeoJson = labels;
                        setGeo("fs-rivers", geo);
                        setGeo("fs-river-labels", labels);
                        refreshRiverStatusSources();
                        applyNativeZoomStyle(zoom);
                    });
                } catch (Exception ignored) {}
            });
            return;
        }

        int cx = Math.max(0, Math.min(11, (int)Math.floor((center.getLongitude()-80.0)/0.7)));
        int cy = Math.max(0, Math.min(7, (int)Math.floor((center.getLatitude()-26.2)/0.6)));
        int radius = zoom < 8.8 ? 1 : 0;
        String key = cx+":"+cy+":"+radius+":"+zoomBand;
        if (key.equals(lastRiverTileKey)) return;
        lastRiverTileKey = key;
        final int generation = ++riverTileGeneration;
        final double z = zoom;
        io.execute(() -> {
            try {
                JSONObject districts = districtGeoJson == null ? null : new JSONObject(districtGeoJson);
                List<RiverWay> merged = new ArrayList<>();
                java.util.HashSet<String> seen = new java.util.HashSet<>();
                int baseCount = Math.min(overviewRivers.size(), z < 8.8 ? 700 : (z < 9.4 ? 420 : 220));
                for (int i=0;i<baseCount;i++) {
                    RiverWay r=overviewRivers.get(i); String k=riverKey(r);
                    if(seen.add(k)) merged.add(r);
                }
                for (int x=Math.max(0,cx-radius); x<=Math.min(11,cx+radius); x++) {
                    for (int y=Math.max(0,cy-radius); y<=Math.min(7,cy+radius); y++) {
                        List<RiverWay> tile = readRiverTile(x,y,districts);
                        for (RiverWay r:tile) if(seen.add(riverKey(r))) merged.add(r);
                    }
                }
                List<RiverWay> render = nativeCleanForZoom(merged, z, districts);
                String geo = makeRiversGeoJson(render);
                String labels = makeRiverLabelsGeoJson(render);
                main.post(() -> {
                    if (generation != riverTileGeneration) return;
                    rivers.clear(); rivers.addAll(render);
                    riversGeoJson = geo; riverLabelsGeoJson = labels;
                    setGeo("fs-rivers", geo);
                    setGeo("fs-river-labels", labels);
                    refreshRiverStatusSources();
                    applyNativeZoomStyle(z);
                });
            } catch (Exception ignored) {}
        });
    }

    private static String nativeZoomBand(double z) {
        if (z < 6.4) return "major";
        if (z < 7.2) return "named-river";
        if (z < 8.2) return "named";
        if (z < 9.4) return "river";
        return "full";
    }

    private boolean nativeKeepRiver(RiverWay r,double z) {
        if (r == null || r.points.size() < 2) return false;
        String type = r.type == null ? "" : r.type.toLowerCase(Locale.ROOT);
        String name = r.name == null ? "" : r.name.trim();
        boolean named = !name.isEmpty() && !"नदी / खोला".equals(name) && !"river / stream".equalsIgnoreCase(name);
        boolean river = "river".equals(type);
        if (z < 6.4) {
            if (river && named) return true;
            try {
                StationDot g=routeGaugeFor(r);
                if(g!=null&&g.fresh){String s=normalizeStage(g.stage);return "danger".equals(s)||"warning".equals(s)||"alert".equals(s);}
            } catch(Exception ignored) {}
            return false;
        }
        if (z < 7.2) return river && named;
        if (z < 8.2) return named;
        if (z < 9.4) return river || named;
        return true;
    }

    private List<RiverWay> nativeCleanForZoom(List<RiverWay> input,double z,JSONObject districts) {
        List<RiverWay> sorted = new ArrayList<>(input == null ? Collections.emptyList() : input);
        sorted.sort(Comparator.comparingInt(FloodSafeNativeMapView::riverScore).reversed());
        int limit = z < 6.4 ? 80 : (z < 7.2 ? 180 : (z < 8.2 ? 420 : (z < 9.4 ? 900 : 1800)));
        List<RiverWay> out = new ArrayList<>();
        for (RiverWay r:sorted) {
            if (!nativeKeepRiver(r,z)) continue;
            RiverWay c = nativeCopyRiver(r);
            if (districts != null) nativeClipRiverToNepal(c,districts); else trimRiverToNepalBBox(c);
            if (c.points.size() < 2) continue;
            out.add(c);
            if (out.size() >= limit) break;
        }
        return out;
    }

    private static RiverWay nativeCopyRiver(RiverWay r) {
        RiverWay c = new RiverWay();
        c.name = r.name; c.type = r.type;
        for (double[] p:r.points) if (p != null && p.length >= 2) c.points.add(new double[]{p[0],p[1]});
        return c;
    }

    private static void nativeClipRiverToNepal(RiverWay r,JSONObject districts) {
        if (r == null || r.points.size() < 2 || districts == null) return;
        List<double[]> best = new ArrayList<>(), run = new ArrayList<>();
        for (double[] p:r.points) {
            boolean inside = p != null && p.length >= 2 && insideDistricts(p[0],p[1],districts);
            if (inside) run.add(p);
            else {
                if (run.size() > best.size()) best = new ArrayList<>(run);
                run.clear();
            }
        }
        if (run.size() > best.size()) best = new ArrayList<>(run);
        r.points.clear();
        if (best.size() >= 2) r.points.addAll(best);
    }

    private void applyNativeZoomStyle(double z) {
        if (style == null) return;
        float core = z < 6.4 ? 0.72f : (z < 7.2 ? 0.88f : (z < 8.2 ? 1.02f : (z < 9.4 ? 1.18f : 1.45f)));
        float trace = Math.max(0.24f, core * 0.42f);
        float glowWidth = Math.max(1.1f, core * 1.55f);
        float glowOpacity = z < 8.4 ? 0.0f : 0.12f;
        try { LineLayer l=style.getLayerAs("fs-rivers-layer"); if(l!=null)l.setProperties(lineColor("#168BFF"),lineWidth(core),lineOpacity(0.86f)); } catch(Exception ignored) {}
        try { LineLayer l=style.getLayerAs("fs-river-flow-trace"); if(l!=null)l.setProperties(lineWidth(trace),lineOpacity(z<6.4?0.34f:0.52f)); } catch(Exception ignored) {}
        try { LineLayer l=style.getLayerAs("fs-river-glow"); if(l!=null)l.setProperties(lineWidth(glowWidth),lineOpacity(glowOpacity)); } catch(Exception ignored) {}
    }

'''
helper=helper[:start]+new_block+helper[end:]

# Tight camera target to Nepal and avoid showing unnecessary neighbouring-country area.
helper=helper.replace('map.setMinZoomPreference(4.8);','map.setMinZoomPreference(5.2);',1)
helper=helper.replace('.include(new LatLng(25.4, 79.2))\n                        .include(new LatLng(31.15, 89.15)).build();','.include(new LatLng(26.25, 80.02))\n                        .include(new LatLng(30.50, 88.25)).build();',1)
helper=helper.replace('Math.max(4.8, Math.min(19.0, current + delta))','Math.max(5.2, Math.min(19.0, current + delta))',1)

# Thin the static layer defaults; applyNativeZoomStyle adjusts them further by zoom.
old_glow='lineColor("#003a4b"), lineWidth(6.2f), lineOpacity(0.86f)'
new_glow='lineColor("#003a4b"), lineWidth(1.6f), lineOpacity(0.12f)'
if old_glow not in helper: raise SystemExit('native glow style anchor missing')
helper=helper.replace(old_glow,new_glow,1)
old_core='lineColor("#7f939c"), lineWidth(2.45f), lineOpacity(0.92f)'
new_core='lineColor("#168BFF"), lineWidth(0.95f), lineOpacity(0.86f)'
if old_core not in helper: raise SystemExit('native core style anchor missing')
helper=helper.replace(old_core,new_core,1)
old_trace='lineColor("#bdfbff"), lineWidth(1.05f), lineOpacity(0.78f)'
new_trace='lineColor("#bdfbff"), lineWidth(0.42f), lineOpacity(0.52f)'
if old_trace not in helper: raise SystemExit('native flow trace anchor missing')
helper=helper.replace(old_trace,new_trace,1)
old_particles='ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#f4feff", 4.0f, 1.0f);'
if old_particles not in helper: raise SystemExit('native particle style anchor missing')
helper=helper.replace(old_particles,'ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#f4feff", 2.0f, 0.82f);',1)
helper=helper.replace('Math.min(320, rivers.size())','Math.min(72, rivers.size())',1)
helper=helper.replace('lineWidth(1.05f+0.80f*glow)','lineWidth(0.28f+0.20f*glow)',1)
helper=helper.replace('main.postDelayed(this, 180L);','main.postDelayed(this, 260L);',1)

map_path.write_text(helper,encoding='utf-8')

if "versionName '0.8.11'" not in gradle:
    gradle=gradle.replace('versionCode 30','versionCode 31',1)
    gradle=gradle.replace("versionName '0.8.10'","versionName '0.8.11'",1)
if 'versionCode 31' not in gradle or "versionName '0.8.11'" not in gradle:
    raise SystemExit('v0.8.11 version bump failed')
gradle_path.write_text(gradle,encoding='utf-8')

h=map_path.read_text(encoding='utf-8')
for marker in ['nativeZoomBand','nativeCleanForZoom','nativeClipRiverToNepal','applyNativeZoomStyle','Math.min(72, rivers.size())','lineColor("#168BFF"), lineWidth(0.95f)','"#f4feff", 2.0f, 0.82f','new LatLng(26.25, 80.02)','new LatLng(30.50, 88.25)']:
    if marker not in h: raise SystemExit('v0.8.11 native clean-map marker missing: '+marker)
print('FloodSafe v0.8.11 Nepal-only progressive low-load native river map PASS')
