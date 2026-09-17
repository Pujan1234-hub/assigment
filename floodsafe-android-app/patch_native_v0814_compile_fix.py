from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')
old='private static JSONArray localRiverSegment(RiverWay r,double la,double lo){'
new='private static JSONArray localRiverSegment(RiverWay r,double la,double lo) throws Exception {'
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('v0.8.14 localRiverSegment signature missing')
p.write_text(s,encoding='utf-8')
if new not in p.read_text(encoding='utf-8'):
    raise SystemExit('v0.8.14 compile fix marker missing')
print('FloodSafe v0.8.14 JSONException compile fix PASS')
