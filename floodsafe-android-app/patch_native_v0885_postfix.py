from pathlib import Path

root = Path(__file__).resolve().parent
map_p = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
full_p = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'

text = map_p.read_text(encoding='utf-8')
# Ensure the separator between generated Java statements is a real source newline,
# not a literal backslash+n token.
bad = 'append(r.type == null ? "stream" : r.type);\\n        msg.append("\\n\\nRiver geometry: OpenStreetMap / FloodSafe bundled network");'
good = 'append(r.type == null ? "stream" : r.type);\n        msg.append("\\n\\nRiver geometry: OpenStreetMap / FloodSafe bundled network");'
if bad in text:
    text = text.replace(bad, good, 1)
if 'River type:' not in text or 'V0885_SAME_RIVER_GAUGE_ONLY' not in text:
    raise SystemExit('v0885 generated native river detail contract missing')
if ');\\n        msg.append("\\n\\nRiver geometry:' in text:
    raise SystemExit('v0885 generated Java still contains literal statement newline token')
map_p.write_text(text, encoding='utf-8')

# NativeFullActivity is intentionally minified in several methods. A // marker
# inserted mid-line would comment out the rest of that Java method. Convert the
# generated contract markers to block comments so the original code remains live.
full = full_p.read_text(encoding='utf-8')
full = full.replace(')); // V0885_MAPLIBRE_NATIVE', ')); /* V0885_MAPLIBRE_NATIVE */', 1)
full = full.replace('; // V0885_SOURCE_LATEST_NO_APP_MINUTE_CUTOFF', '; /* V0885_SOURCE_LATEST_NO_APP_MINUTE_CUTOFF */', 1)
if '/* V0885_MAPLIBRE_NATIVE */' not in full:
    raise SystemExit('v0885 MapLibre holder block-comment postfix missing')
if '/* V0885_SOURCE_LATEST_NO_APP_MINUTE_CUTOFF */' not in full:
    raise SystemExit('v0885 latest-source block-comment postfix missing')
full_p.write_text(full, encoding='utf-8')

print('v0.8.85 generated Java postfix PASS')
