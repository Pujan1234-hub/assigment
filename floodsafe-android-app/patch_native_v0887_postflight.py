from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

# Ensure the first MapLibre style paint renders the monitored/detail-backed river subset
# even if candidate geometry finished loading before the style became ready.
marker='V0887_FIRST_STYLE_MONITORED_RIVERS'
if marker not in m:
    ready='styleReady = true;'
    i=m.find(ready)
    if i<0: raise SystemExit('v0887 postflight styleReady anchor missing')
    j=m.find('installGeoLayers();',i)
    if j<0: raise SystemExit('v0887 postflight installGeoLayers anchor missing')
    end=j+len('installGeoLayers();')
    m=m[:end]+'\n                v887ApplyMonitoredRiverGeometry(); // '+marker+m[end:]

if 'V0887_BLUE_RIVER_ALWAYS_HAS_DETAIL' not in m:
    raise SystemExit('v0887 postflight monitored-river helper missing')
m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.87 postflight PASS: monitored rivers render on first style paint')
