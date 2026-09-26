from pathlib import Path
import re

root = Path(__file__).resolve().parent
p = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s = p.read_text(encoding='utf-8')

if 'V0901_FAST_STATION_MAPPING' in s:
    print('v0.9.01 fast station mapping already applied')
    raise SystemExit(0)

if 'V0900_BUILD_MAPPING_ONCE' not in s:
    raise SystemExit('v0.9.00 station mapping must be applied before v0.9.01')

def method_span(text, name):
    q = re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b' + re.escape(name) + r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{', text)
    if not q:
        return None
    op = text.find('{', q.start())
    depth = 0
    quote = None
    esc = False
    for i in range(op, len(text)):
        ch = text[i]
        if quote:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                quote = None
        else:
            if ch in ('"', "'"):
                quote = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return q.start(), i + 1
    return None

def replace_method(text, name, block):
    sp = method_span(text, name)
    if not sp:
        raise SystemExit('Missing method: ' + name)
    return text[:sp[0]] + block + text[sp[1]:]

rebuild = r'''    private void rebuildMonitoredRiverMapping(String requestedInventory) {
        if (requestedInventory == null || requestedInventory.isEmpty()) return;
        if (requestedInventory.equals(mappedInventoryFingerprint) && monitoredSourceFeatureCount > 0) return;
        final long started = android.os.SystemClock.elapsedRealtime();
        List<StationDot> ss;
        List<RiverWay> candidates;
        synchronized (stations) { ss = new ArrayList<>(stations); }
        synchronized (rivers) { candidates = new ArrayList<>(rivers); }
        if (ss.isEmpty() || candidates.isEmpty()) {
            android.util.Log.i("FloodSafeRiver", "mapping_wait stations=" + ss.size() + " candidates=" + candidates.size());
            return;
        }

        java.util.Map<String,List<RiverWay>> byKey = new java.util.HashMap<>();
        java.util.IdentityHashMap<RiverWay,double[]> bounds = new java.util.IdentityHashMap<>();
        for (RiverWay r : candidates) {
            String k = riverKey(r.name);
            if (!k.isEmpty()) byKey.computeIfAbsent(k, ignored -> new ArrayList<>()).add(r);
            bounds.put(r, riverBounds(r));
        }
        android.util.Log.i("FloodSafeRiver", "mapping_start stations=" + ss.size() + " candidates=" + candidates.size() + " river_keys=" + byKey.size());

        java.util.LinkedHashSet<RiverWay> visible = new java.util.LinkedHashSet<>();
        java.util.Map<String,List<RiverWay>> byStation = new java.util.HashMap<>();
        int exact = 0, fallback = 0, unmatched = 0;
        String sample = "";
        for (StationDot st : ss) {
            String wanted = riverKey(!empty(st.riverName) ? st.riverName : riverFromStationTitle(st.name));
            List<RiverWay> family = candidateFamily(wanted, byKey);
            RiverWay seed = seedRiverForStation(st, family, bounds, candidates);
            if (seed == null) { unmatched++; continue; }
            boolean named = !family.isEmpty() && family.contains(seed) && !wanted.isEmpty()
                    && sameRiverKey(wanted, riverKey(seed.name));
            if (named) exact++; else fallback++;
            List<RiverWay> local = localConnectedRiverSegments(st, seed, family, named);
            if (local.isEmpty()) local = Collections.singletonList(seed);
            visible.addAll(local);
            byStation.put(stationKey(st), new ArrayList<>(local));
            String probe = ((st.name == null ? "" : st.name) + " " + (st.riverName == null ? "" : st.riverName)).toLowerCase(Locale.ROOT);
            if (sample.isEmpty() && (probe.contains("bagmati") || probe.contains("gaurighat"))) {
                sample = st.name + " -> " + seed.name + " segments=" + local.size();
            }
        }
        if (!requestedInventory.equals(stationInventoryFingerprint)) return;
        List<RiverWay> next = new ArrayList<>(visible);
        String geo = makeRiversGeoJsonSafe(next);
        synchronized (monitoredRivers) {
            monitoredRivers.clear();
            monitoredRivers.addAll(next);
        }
        synchronized (monitoredByStation) {
            monitoredByStation.clear();
            monitoredByStation.putAll(byStation);
        }
        riversGeoJson = geo;
        monitoredSourceFeatureCount = next.size();
        mappedInventoryFingerprint = requestedInventory;
        long elapsed = android.os.SystemClock.elapsedRealtime() - started;
        android.util.Log.i("FloodSafeRiver", "station_linked_features=" + next.size() + " stations=" + ss.size()
                + " exact=" + exact + " coordinate_fallback=" + fallback + " unmatched=" + unmatched
                + " mapping_ms=" + elapsed + (sample.isEmpty() ? "" : " sample=" + sample));
        main.post(() -> {
            if (styleReady && style != null) {
                if (style.getSource("fs-rivers") == null) installGeoLayers();
                setGeo("fs-rivers", riversGeoJson);
                refreshRiskRiverSources();
            }
        });
    } // V0901_FAST_STATION_MAPPING
'''
s = replace_method(s, 'rebuildMonitoredRiverMapping', rebuild)

seed_and_helpers = r'''    private static List<RiverWay> candidateFamily(String wanted, java.util.Map<String,List<RiverWay>> byKey) {
        if (wanted == null || wanted.isEmpty() || byKey == null || byKey.isEmpty()) return Collections.emptyList();
        List<RiverWay> exact = byKey.get(wanted);
        if (exact != null && !exact.isEmpty()) return new ArrayList<>(exact);
        java.util.LinkedHashSet<RiverWay> out = new java.util.LinkedHashSet<>();
        for (java.util.Map.Entry<String,List<RiverWay>> e : byKey.entrySet()) {
            if (sameRiverKey(wanted, e.getKey())) out.addAll(e.getValue());
        }
        return new ArrayList<>(out);
    }

    private static double[] riverBounds(RiverWay r) {
        double minLat = Double.POSITIVE_INFINITY, maxLat = Double.NEGATIVE_INFINITY;
        double minLon = Double.POSITIVE_INFINITY, maxLon = Double.NEGATIVE_INFINITY;
        if (r != null) for (double[] p : r.points) {
            if (p == null || p.length < 2) continue;
            minLon = Math.min(minLon, p[0]); maxLon = Math.max(maxLon, p[0]);
            minLat = Math.min(minLat, p[1]); maxLat = Math.max(maxLat, p[1]);
        }
        return new double[]{minLat, maxLat, minLon, maxLon};
    }

    private static boolean boundsNear(double lat, double lon, double[] b, double padKm) {
        if (b == null || b.length < 4 || !Double.isFinite(b[0])) return false;
        double latPad = padKm / 110.574;
        double cos = Math.max(0.25, Math.cos(Math.toRadians(lat)));
        double lonPad = padKm / (111.320 * cos);
        return lat >= b[0] - latPad && lat <= b[1] + latPad
                && lon >= b[2] - lonPad && lon <= b[3] + lonPad;
    }

    private RiverWay seedRiverForStation(StationDot st, List<RiverWay> family,
                                          java.util.IdentityHashMap<RiverWay,double[]> bounds,
                                          List<RiverWay> candidates) {
        if (st == null) return null;
        RiverWay best = null;
        double bestD = Double.POSITIVE_INFINITY;
        if (family != null) {
            for (RiverWay r : family) {
                double d = distanceToRiverKm(st.lat, st.lon, r);
                if (Double.isFinite(d) && d < bestD) { bestD = d; best = r; }
            }
            if (best != null && bestD <= 10.0) return best;
        }
        // Strict coordinate fallback. Cheap bounds reject avoids millions of segment calculations.
        best = null; bestD = Double.POSITIVE_INFINITY;
        if (candidates != null) for (RiverWay r : candidates) {
            if (!boundsNear(st.lat, st.lon, bounds.get(r), 1.15)) continue;
            double d = distanceToRiverKm(st.lat, st.lon, r);
            if (Double.isFinite(d) && d < bestD) { bestD = d; best = r; }
        }
        return bestD <= 0.85 ? best : null;
    } // V0901_NAME_INDEX_BOUNDS_FALLBACK
'''
s = replace_method(s, 'seedRiverForStation', seed_and_helpers)

local = r'''    private List<RiverWay> localConnectedRiverSegments(StationDot st, RiverWay seed, List<RiverWay> family, boolean namedMatch) {
        java.util.LinkedHashSet<RiverWay> out = new java.util.LinkedHashSet<>();
        out.add(seed);
        if (!namedMatch || family == null || family.isEmpty()) return new ArrayList<>(out);
        java.util.IdentityHashMap<RiverWay,Double> stationDistance = new java.util.IdentityHashMap<>();
        for (RiverWay r : family) stationDistance.put(r, distanceToRiverKm(st.lat, st.lon, r));
        for (int round = 0; round < 5; round++) {
            boolean changed = false;
            List<RiverWay> current = new ArrayList<>(out);
            for (RiverWay r : family) {
                if (out.contains(r)) continue;
                Double stationD = stationDistance.get(r);
                if (stationD == null || !Double.isFinite(stationD) || stationD > 35.0) continue;
                boolean connected = stationD <= 2.0;
                if (!connected) {
                    for (RiverWay have : current) {
                        if (riverGapKm(have, r) <= 1.25) { connected = true; break; }
                    }
                }
                if (connected) { out.add(r); changed = true; }
            }
            if (!changed) break;
        }
        return new ArrayList<>(out);
    } // V0901_LOCAL_FAMILY_ONLY
'''
s = replace_method(s, 'localConnectedRiverSegments', local)

p.write_text(s, encoding='utf-8')
print('FloodSafe v0.9.01 PASS: station mapping indexed by river name with bounded coordinate fallback')
