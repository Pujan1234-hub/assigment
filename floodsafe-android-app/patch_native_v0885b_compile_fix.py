from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=a_path.read_text(encoding='utf-8')

bad='" • 🔴 "+d+" 🟠 "+w+" 🟡 "+a+" 🔵 "+n'
good='" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n'
count=a.count(bad)
if count<1:
    raise SystemExit('v0885b generated official-status summary anchor missing')
a=a.replace(bad,good)
if '+a+" 🔵 "+n' in a:
    raise SystemExit('v0885b undefined alert variable remained')
if 'V0885_OFFICIAL_LATEST_COUNTS' not in a:
    raise SystemExit('v0885b v0885 summary contract missing')
a_path.write_text(a,encoding='utf-8')
print('FloodSafe v0.8.85b PASS: official latest summary uses existing alert count variable al')
