from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')

# v0.8.8 normalized these values after v0.8.6. Restore the anchors expected by
# the v0.8.14 optimization patch, then that patch will reduce them for smooth UI.
old='int baseCount = Math.min(overviewRivers.size(), 1400);'
new='int baseCount = Math.min(overviewRivers.size(), z < 8.4 ? 3200 : 1400);'
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('v0.8.14 prep baseCount anchor missing')

old_labels='if(++count>=1400)break;'
new_labels='if(++count>=900)break;'
if old_labels in s:
    s=s.replace(old_labels,new_labels,1)
elif new_labels not in s:
    raise SystemExit('v0.8.14 prep label count anchor missing')

p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.14 runtime-count prep PASS')
