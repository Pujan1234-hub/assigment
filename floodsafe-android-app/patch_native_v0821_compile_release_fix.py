from pathlib import Path

root=Path(__file__).resolve().parent
map_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
gradle_path=root/'app/build.gradle'

m=map_path.read_text(encoding='utf-8')
old='append(direct?(g.rawStatus==null||g.rawStatus.isEmpty()?g.stage.toUpperCase(Locale.ROOT):g.rawStatus):"STALE / NOT USED FOR LIVE COLOUR OR ALERT")'
new='append(direct!=null?(g.rawStatus==null||g.rawStatus.isEmpty()?g.stage.toUpperCase(Locale.ROOT):g.rawStatus):"STALE / NOT USED FOR LIVE COLOUR OR ALERT")'
if old in m:
    m=m.replace(old,new,1)
elif new not in m:
    raise SystemExit('v0.8.21 direct gauge status expression anchor missing')
map_path.write_text(m,encoding='utf-8')

g=gradle_path.read_text(encoding='utf-8')
# v0.8.2 deliberately introduced MapLibre's Vulkan+OpenGL SDK. The repository's
# older base dependency still adds the OpenGL-only SDK, which packages the same
# libmaplibre.so a second time. Keep the newer dual-backend SDK only.
g=g.replace("    implementation 'org.maplibre.gl:android-sdk-opengl:13.6.1'\n",'')
g=g.replace("    implementation 'org.maplibre.gl:android-sdk-opengl:13.6.1'\r\n",'')
if "org.maplibre.gl:android-sdk-vulkan-opengl:13.6.1" not in g:
    raise SystemExit('v0.8.21 expected MapLibre vulkan-opengl dependency missing')
if "org.maplibre.gl:android-sdk-opengl:13.6.1" in g:
    raise SystemExit('duplicate MapLibre opengl dependency remained')
if g.count("org.maplibre.gl:android-sdk-") != 1:
    raise SystemExit('expected exactly one MapLibre Android SDK dependency')
gradle_path.write_text(g,encoding='utf-8')

print('FloodSafe v0.8.21 Java + MapLibre release compile fix PASS')
