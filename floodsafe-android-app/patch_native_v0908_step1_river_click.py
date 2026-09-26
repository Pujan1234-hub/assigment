from pathlib import Path
import re

MAP = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java")
s = MAP.read_text(encoding="utf-8")

pattern = r'''    private StationDot bestGaugeForRiver\(RiverWay r, double tapLat, double tapLon\) \{.*?    \} // V0899_NO_UNRELATED_NEAREST_GAUGE'''
replacement = r'''    private StationDot bestGaugeForRiver(RiverWay r, double tapLat, double tapLon) {
        if (r == null) return null;

        // First reuse the exact station↔river association that already drives the
        // visible river status colour. This prevents an orange/red river segment
        // from saying "no gauge" merely because the bundled geometry name differs
        // from the official BIPAD station/river spelling.
        StationDot mappedBest = null;
        double mappedScore = Double.POSITIVE_INFINITY;
        synchronized (stations) {
            for (StationDot s : stations) {
                boolean linkedToTappedGeometry = false;
                for (RiverWay linked : stationSegments(s)) {
                    if (linked == r) { linkedToTappedGeometry = true; break; }
                }
                if (!linkedToTappedGeometry) continue;
                double toTap = km(tapLat, tapLon, s.lat, s.lon);
                // Prefer a current official gauge when two mapped gauges share the segment,
                // while keeping the tap-distance ordering dominant.
                double score = toTap + (s.fresh ? 0.0 : 0.20);
                if (score < mappedScore) { mappedScore = score; mappedBest = s; }
            }
        }
        if (mappedBest != null) return mappedBest;

        // Conservative name-based fallback retained for a tapped named geometry that
        // was not part of the prebuilt station mapping.
        String rk = riverKey(r.name);
        if (rk.isEmpty()) return null;
        StationDot best = null;
        double bestScore = Double.POSITIVE_INFINITY;
        synchronized (stations) {
            for (StationDot s : stations) {
                String sk = riverKey(!empty(s.riverName) ? s.riverName : riverFromStationTitle(s.name));
                if (!sameRiverKey(rk, sk)) continue;
                double toRiver = distanceToRiverKm(s.lat, s.lon, r);
                if (!Double.isFinite(toRiver) || toRiver > 8.0) continue;
                double toTap = km(tapLat, tapLon, s.lat, s.lon);
                double score = toTap + toRiver * 2.0;
                if (score < bestScore) { bestScore = score; best = s; }
            }
        }
        return best;
    } // V0908_RIVER_TAP_REUSES_STATUS_MAPPING'''

s2, n = re.subn(pattern, lambda _m: replacement, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"bestGaugeForRiver patch expected 1 match, got {n}")
if "V0908_RIVER_TAP_REUSES_STATUS_MAPPING" not in s2:
    raise SystemExit("step1 marker missing")
# Guard critical map behaviour that must remain present.
for marker in [
    "V0900_TAP_ONLY_MONITORED_RIVERS",
    "V0900_STATUS_COLOURS_LINKED_SEGMENTS_ONLY",
    "V0901_FAST_STATION_MAPPING",
    "startParticles()",
    "fs-rivers-layer",
    "fs-river-warning-risk",
    "fs-river-danger-risk",
]:
    if marker not in s2:
        raise SystemExit("critical map marker missing: " + marker)
MAP.write_text(s2, encoding="utf-8")
print("V0908_STEP1_RIVER_CLICK_OK")
