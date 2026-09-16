from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
helper_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'
helper = helper_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')

# v0.8.8: restore the proven old web-map river architecture.
# National view uses the full snapshot ranked down to 1,400 major/named routes,
# matching map-gl-v4. Zoomed views still add local tile detail. Do NOT run the
# expensive 77-district polygon clip that caused the river source to disappear.
helper = helper.replace(
    'try { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }\n                catch (Exception e) { raw = readAsset("data/nepal-waterways-snapshot.json"); }',
    'try { raw = readAsset("data/nepal-waterways-snapshot.json"); }\n                catch (Exception e) { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }',
    1)

helper = helper.replace(
    'if (all.size() > 6400) all = new ArrayList<>(all.subList(0, 6400));',
    'if (all.size() > 1400) all = new ArrayList<>(all.subList(0, 1400));',
    1)

# Replace v0.8.7 sampled polygon rejection with a cheap continuous Nepal-bounds trim.
# This preserves whole visible river routes and avoids both the India-heavy spill and
# the prior point-by-point polygon cost.
helper = helper.replace(
    'if (nepalDistricts != null && rw.points.size() >= 2 && !riverTouchesNepalFast(rw, nepalDistricts)) rw.points.clear();',
    'if (rw.points.size() >= 2) trimRiverToNepalBBox(rw);',
    1)
helper = helper.replace(
    'if(districts!=null&&rw.points.size()>=2&&!riverTouchesNepalFast(rw,districts))rw.points.clear();',
    'if(rw.points.size()>=2)trimRiverToNepalBBox(rw);',
    1)

anchor = '    private static boolean riverTouchesNepalFast(RiverWay r, JSONObject districtRoot) {'
method = r'''    private static void trimRiverToNepalBBox(RiverWay r) {
        if (r == null || r.points.size() < 2) return;
        int first = -1, last = -1;
        for (int i = 0; i < r.points.size(); i++) {
            double[] p = r.points.get(i);
            if (p == null || p.length < 2) continue;
            double lo = p[0], la = p[1];
            // Small tolerance keeps border rivers continuous without drawing deep into India/Tibet.
            if (lo >= 79.92 && lo <= 88.43 && la >= 26.12 && la <= 30.58) {
                if (first < 0) first = i;
                last = i;
            }
        }
        if (first < 0 || last <= first) { r.points.clear(); return; }
        if (first == 0 && last == r.points.size() - 1) return;
        List<double[]> keep = new ArrayList<>(r.points.subList(first, last + 1));
        r.points.clear();
        r.points.addAll(keep);
    }

'''
if 'private static void trimRiverToNepalBBox' not in helper:
    if anchor not in helper:
        raise SystemExit('v0.8.7 river helper anchor missing')
    helper = helper.replace(anchor, method + anchor, 1)

# Match the web map visual language: dark cyan shadow + vivid cyan core + bright
# animated trace on EVERY rendered river. Station status remains independent/live.
helper = helper.replace(
    'lineColor("#00c9f4"), lineWidth(8.6f), lineOpacity(0.66f)',
    'lineColor("#003a4b"), lineWidth(6.2f), lineOpacity(0.86f)',
    1)
helper = helper.replace(
    'lineColor("#a5f6ff"), lineWidth(3.15f), lineOpacity(1.0f)',
    'lineColor("#22e7ff"), lineWidth(2.45f), lineOpacity(1.0f)',
    1)
helper = helper.replace(
    'lineColor("#e9fdff"), lineWidth(0.9f), lineOpacity(0.62f)',
    'lineColor("#bdfbff"), lineWidth(1.05f), lineOpacity(0.78f)',
    1)

# Keep the whole-river trace pulsing and spread moving dots over many routes without
# overloading weaker phones.
helper = helper.replace('int n = Math.min(220, rivers.size());', 'int n = Math.min(320, rivers.size());', 1)
helper = helper.replace('if(++count>=900)break;', 'if(++count>=1400)break;', 1)

# Make sure the national overview is restored immediately after geometry loads.
helper = helper.replace(
    'int baseCount = Math.min(overviewRivers.size(), z < 8.4 ? 3200 : 1400);',
    'int baseCount = Math.min(overviewRivers.size(), 1400);',
    1)

helper_path.write_text(helper, encoding='utf-8')

if "versionName '0.8.8'" not in gradle:
    gradle = gradle.replace('versionCode 27', 'versionCode 28', 1)
    gradle = gradle.replace("versionName '0.8.7'", "versionName '0.8.8'", 1)
if 'versionCode 28' not in gradle or "versionName '0.8.8'" not in gradle:
    raise SystemExit('v0.8.8 version bump failed')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
if index_path.is_file():
    index = index_path.read_text(encoding='utf-8').replace('<span class="badge green">v0.8.7</span>', '<span class="badge green">v0.8.8</span>')
    index_path.write_text(index, encoding='utf-8')

h = helper_path.read_text(encoding='utf-8')
for marker in [
    'data/nepal-waterways-snapshot.json',
    'all.size() > 1400',
    'trimRiverToNepalBBox(rw)',
    'lineColor("#003a4b"), lineWidth(6.2f)',
    'lineColor("#22e7ff"), lineWidth(2.45f)',
    'lineColor("#bdfbff"), lineWidth(1.05f)',
    'Math.min(320, rivers.size())',
    'refreshVisibleRiverTiles',
]:
    if marker not in h:
        raise SystemExit('v0.8.8 restore marker missing: ' + marker)
print('FloodSafe v0.8.8 web-style native river network + glow/flow restore PASS')
