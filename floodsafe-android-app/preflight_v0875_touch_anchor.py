from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')

# Older generated patch layers sometimes emit "@Override public/protected ..." on
# one line. Normalize all such declarations so the v0.8.75 generic method parser can
# locate lifecycle and touch methods consistently. This is formatting-only.
s=re.sub(
    r'(?m)^(\s*)@Override\s+((?:public|protected|private)\s+)',
    lambda m: m.group(1)+'@Override\n'+m.group(1)+m.group(2),
    s,
)

# The generated MapView may have no dispatchTouchEvent override. Add a neutral,
# compiler-safe anchor so the v0.8.75 performance patch can replace it with the
# touch-priority implementation.
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

# Some generated baselines have no detach override at all. The smoothness patch needs
# a lifecycle anchor to close both executors. Add the same pre-existing IO shutdown
# semantics as a neutral detach anchor only when absent.
if 'onDetachedFromWindow(' not in s:
    i=s.rfind('\n}')
    if i<0: raise SystemExit('v0875 preflight class-close anchor missing')
    neutral='''\n    @Override\n    protected void onDetachedFromWindow(){\n        io.shutdownNow();\n        super.onDetachedFromWindow();\n    } // V0875_DETACH_ANCHOR_PREFLIGHT\n'''
    s=s[:i]+neutral+s[i:]

if 'dispatchTouchEvent(' not in s:
    raise SystemExit('v0875 preflight touch anchor insert failed')
if 'onDetachedFromWindow(' not in s:
    raise SystemExit('v0875 preflight detach anchor insert failed')
p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.75 preflight PASS: touch + detach method anchors ready')
