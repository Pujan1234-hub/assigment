from pathlib import Path
p=Path(__file__).resolve().parent/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')
old='rw.name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"), "नदी / खोला");'
new='rw.name = firstNonEmpty(w.optString("name_en"), w.optString("name"), w.optString("name_ne"), "नदी / खोला"); // V0900_BIPAD_NAME_MATCH_PRIORITY'
if old in s:s=s.replace(old,new,1)
elif 'V0900_BIPAD_NAME_MATCH_PRIORITY' not in s:raise SystemExit('river name priority anchor missing')
p.write_text(s,encoding='utf-8')
print('v0.9.00 river alias priority PASS: BIPAD-compatible English name first, Nepali retained as fallback')
