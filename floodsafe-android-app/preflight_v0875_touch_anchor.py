from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')

# Normalize any existing one-line @Override method declaration first. Older generated
# patch layers can produce "@Override public boolean dispatchTouchEvent(...)" on one
# line, while the generic method-span parser intentionally starts at a visibility token.
s=re.sub(
    r'(?m)^(\s*)@Override\s+(public\s+boolean\s+dispatchTouchEvent\s*\()',
    lambda m: m.group(1)+'@Override\n'+m.group(1)+m.group(2),
    s,
    count=1,
)

# The v0.8.74 generated MapView may have no dispatchTouchEvent override. Add a neutral,
# compiler-safe anchor so the v0.8.75 performance patch can replace it with the
# touch-priority implementation. No runtime behavior changes in this preflight.
if 'dispatchTouchEvent(' not in s:
    if 'import android.view.MotionEvent;' not in s:
        anchor='import android.view.'
        pos=s.find(anchor)
        if pos>=0:
            line_end=s.find('\n',pos)
            s=s[:line_end+1]+'import android.view.MotionEvent;\n'+s[line_end+1:]
        else:
            pkg_end=s.find('\n',s.find('package '))
            if pkg_end<0: raise SystemExit('v0875 preflight package/import anchor missing')
            s=s[:pkg_end+1]+'\nimport android.view.MotionEvent;\n'+s[pkg_end+1:]
    anchor='    private void v847UpdateMovingGlow('
    i=s.find(anchor)
    if i<0: raise SystemExit('v0875 preflight moving-glow anchor missing')
    neutral='''    @Override\n    public boolean dispatchTouchEvent(MotionEvent ev){\n        return super.dispatchTouchEvent(ev);\n    } // V0875_TOUCH_ANCHOR_PREFLIGHT\n\n'''
    s=s[:i]+neutral+s[i:]

if 'dispatchTouchEvent(' not in s:
    raise SystemExit('v0875 preflight touch anchor insert failed')
p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.75 preflight PASS: touch override anchor ready')
