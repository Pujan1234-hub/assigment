from pathlib import Path

p = Path(__file__).resolve().parent / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
text = p.read_text(encoding='utf-8')
# patch_native_v0885_release intentionally embeds Java string escapes. Ensure the
# separator between two Java statements is a real source newline, not a literal \\n token.
bad = 'append(r.type == null ? "stream" : r.type);\\n        msg.append("\\n\\nRiver geometry: OpenStreetMap / FloodSafe bundled network");'
good = 'append(r.type == null ? "stream" : r.type);\n        msg.append("\\n\\nRiver geometry: OpenStreetMap / FloodSafe bundled network");'
if bad in text:
    text = text.replace(bad, good, 1)
if 'River type:' not in text or 'V0885_SAME_RIVER_GAUGE_ONLY' not in text:
    raise SystemExit('v0885 generated native river detail contract missing')
if ');\\n        msg.append("\\n\\nRiver geometry:' in text:
    raise SystemExit('v0885 generated Java still contains literal statement newline token')
p.write_text(text, encoding='utf-8')
print('v0.8.85 generated Java syntax postfix PASS')
