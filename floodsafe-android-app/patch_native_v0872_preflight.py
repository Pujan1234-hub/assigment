from pathlib import Path

p=Path(__file__).resolve().parent/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodMonitorService.java'
s=p.read_text(encoding='utf-8')
old='    @Override public void onDestroy() {'
new='    @Override\n    public void onDestroy() {'
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('v0872 preflight onDestroy anchor missing')
p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.72 preflight PASS: service onDestroy made patch-addressable only; behavior unchanged')
