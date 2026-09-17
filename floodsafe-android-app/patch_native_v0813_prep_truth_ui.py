from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s=p.read_text(encoding='utf-8')
marker='Grey rivers = geometry only • colour/glow = current official gauge status'
if marker not in s:
    pat=r'mapSub\.setText\(t\("[^"]*","[^"]*"\)\);'
    repl='mapSub.setText(t("Grey नदी = geometry मात्र • रङ/Glow = आजको official gauge status","Grey rivers = geometry only • colour/glow = current official gauge status"));'
    s,n=re.subn(pat,repl,s,count=1)
    if n!=1: raise SystemExit('mapSub truth-label anchor missing')
p.write_text(s,encoding='utf-8')
if marker not in p.read_text(encoding='utf-8'): raise SystemExit('truth map label not applied')
print('FloodSafe v0.8.13 truth-map UI prep PASS')
