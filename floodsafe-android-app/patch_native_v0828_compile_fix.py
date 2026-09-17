from pathlib import Path

root = Path(__file__).resolve().parent
p = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s = p.read_text(encoding='utf-8')

# v0.8.27 adds mapRainLatest for the compact live strip. An older map patch already
# owns mapRainTotal, so declaring it again makes javac reject the final generated class.
# Keep the existing shared mapRainTotal field and only add the new latest counter here.
old = '    private volatile int mapRainLatest=-1,mapRainTotal=-1;'
new = '    private volatile int mapRainLatest=-1;'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('v0.8.28 compact rain declaration anchor missing')

existing = 'mapRiverCurrent=0,mapRiverTotal=0,mapRainFresh=0,mapRainTotal=0;'
if existing not in s:
    raise SystemExit('existing mapRainTotal owner missing')
if s.count('mapRainLatest=-1') != 1:
    raise SystemExit('mapRainLatest declaration is not unique')

p.write_text(s, encoding='utf-8')
print('FloodSafe v0.8.28 compile fix PASS: unique mapRainTotal field')
