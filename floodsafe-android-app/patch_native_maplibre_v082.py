from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path = src / 'NativeFullActivity.java'
gradle_path = root / 'app/build.gradle'
helper_path = src / 'FloodSafeNativeMapView.java'

if not activity_path.is_file() or not helper_path.is_file():
    raise SystemExit('Native map source missing')

helper = helper_path.read_text(encoding='utf-8')
for marker in [
    '100% native Android river map using MapLibre Native. No WebView is used.',
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/',
    'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/',
    'data/nepal-waterways-snapshot.json',
    'floodsafe-nepal/v24/nepal-districts.geojson',
    'requestDisallowInterceptTouchEvent(true)',
    'fs-danger-layer', 'fs-warning-layer', 'fs-alert-layer', 'fs-normal-layer', 'fs-stale-layer',
]:
    if marker not in helper:
        raise SystemExit('Native MapLibre helper marker missing: ' + marker)
if 'android.webkit.WebView' in helper or 'new WebView' in helper:
    raise SystemExit('MapLibre helper must not use WebView')

text = activity_path.read_text(encoding='utf-8')
if 'private NativeRiverMap map;' not in text and 'private FloodSafeNativeMapView map;' not in text:
    raise SystemExit('NativeFullActivity map field anchor missing')
text = text.replace('private NativeRiverMap map;', 'private FloodSafeNativeMapView map;', 1)
old = 'map=new NativeRiverMap();holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));'
new = 'map=new FloodSafeNativeMapView(this,obj->{if(obj instanceof RiverStation)showStation((RiverStation)obj);});holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));'
if old in text:
    text = text.replace(old, new, 1)
elif 'map=new FloodSafeNativeMapView(this' not in text:
    raise SystemExit('Native map constructor anchor missing')
activity_path.write_text(text, encoding='utf-8')

gradle = gradle_path.read_text(encoding='utf-8')
dep = "    implementation 'org.maplibre.gl:android-sdk-vulkan-opengl:13.6.1'\n"
if 'org.maplibre.gl:android-sdk-vulkan-opengl:' not in gradle:
    anchor = "dependencies {\n"
    if anchor not in gradle:
        raise SystemExit('Gradle dependencies anchor missing')
    gradle = gradle.replace(anchor, anchor + dep, 1)
gradle = gradle.replace('versionCode 21', 'versionCode 22', 1)
gradle = gradle.replace("versionName '0.8.1'", "versionName '0.8.2'", 1)
if 'versionCode 22' not in gradle or "versionName '0.8.2'" not in gradle:
    raise SystemExit('v0.8.2 version bump failed; v0.8.1 patches must run first')
if 'android-sdk-vulkan-opengl:13.6.1' not in gradle:
    raise SystemExit('MapLibre native dependency missing')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
if index_path.is_file():
    index = index_path.read_text(encoding='utf-8')
    index = index.replace('<span class="badge green">v0.8.1</span>', '<span class="badge green">v0.8.2</span>')
    index_path.write_text(index, encoding='utf-8')

print('FloodSafe v0.8.2 native MapLibre web-match map patch PASS')
