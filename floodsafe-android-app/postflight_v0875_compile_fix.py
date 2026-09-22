from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')

# The v0.8.75 touch replacement can leave the normalized preflight @Override line
# immediately above its own inline @Override. Collapse only that duplicate annotation;
# runtime behavior and all realtime/safety/map contracts stay unchanged.
pattern=r'(?m)^(\s*)@Override\s*\n\1@Override\s+((?:public|protected|private)\s+boolean\s+dispatchTouchEvent\s*\()'
s,n=re.subn(pattern,lambda m:m.group(1)+'@Override\n'+m.group(1)+m.group(2),s,count=1)
if n==0:
    # Be idempotent if a later patch already emits the compiler-safe single annotation.
    if len(re.findall(r'\bboolean\s+dispatchTouchEvent\s*\(',s))!=1:
        raise SystemExit('v0875 compile fix: dispatchTouchEvent method count is not exactly one')
    before=s[:s.find('boolean dispatchTouchEvent')]
    tail=before[-120:]
    if tail.count('@Override')!=1:
        raise SystemExit('v0875 compile fix: expected one @Override before dispatchTouchEvent')

if re.search(r'(?m)^\s*@Override\s*\n\s*@Override\s+.*dispatchTouchEvent',s):
    raise SystemExit('v0875 compile fix: duplicate @Override remained')
if len(re.findall(r'\bboolean\s+dispatchTouchEvent\s*\(',s))!=1:
    raise SystemExit('v0875 compile fix: duplicate dispatchTouchEvent remained')
if 'V0875_TOUCH_PRIORITY' not in s:
    raise SystemExit('v0875 compile fix: touch priority contract missing')

p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.75 compile repair PASS: duplicate dispatchTouchEvent @Override removed')
