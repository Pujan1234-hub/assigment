from pathlib import Path
import re

root = Path(__file__).resolve().parent
p = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s = p.read_text(encoding='utf-8')

start = s.find('private static final class StationDot')
if start < 0:
    raise SystemExit('StationDot class missing')
end = s.find('private static final class', start + 20)
if end < 0:
    end = len(s)
block = s[start:end]

if 'rawStatus' not in block:
    m = re.search(r'String\s+([^;]+);', block)
    if not m:
        raise SystemExit('StationDot String field declaration missing')
    old = m.group(0)
    names = m.group(1).strip()
    new = 'String ' + names + ', rawStatus;'
    block = block[:m.start()] + new + block[m.end():]
    s = s[:start] + block + s[end:]

if 's.rawStatus = getString(c, o, "rawStatus", s.stage);' not in s:
    raise SystemExit('rawStatus assignment missing')
if 'rawStatus' not in s[s.find('private static final class StationDot'):s.find('private static final class RiverWay')]:
    raise SystemExit('rawStatus field not added to StationDot')

p.write_text(s, encoding='utf-8')
print('FloodSafe v0.8.10 StationDot rawStatus compile fix PASS')
