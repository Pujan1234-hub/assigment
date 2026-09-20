from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent

# v0.8.73 MUST start from the accepted fully-native v0.8.72 baseline.
# v0.8.72 had one brittle exact whitespace/style anchor for the native river layer.
# Make only that patch matcher tolerant before applying v0.8.72; behavior is unchanged.
v872=root/'patch_native_v0872_status_colour_background.py'
q=v872.read_text(encoding='utf-8')
old="""if 'V0872_RIVER_STATUS_COLOUR_LAYERS' not in m:\n    if layer_anchor not in m:raise SystemExit('v0872 river layer anchor missing')\n    m=m.replace(layer_anchor,layer_anchor+layer_add,1)"""
new="""if 'V0872_RIVER_STATUS_COLOUR_LAYERS' not in m:\n    # v0.8.71 can restyle/reformat the same native layer, so match the layer ID rather than exact paint text.\n    pos=m.find('new LineLayer(\\\"fs-rivers-layer\\\"')\n    if pos<0:raise SystemExit('v0872 river layer anchor missing')\n    end=m.find(')));',pos)\n    if end<0:raise SystemExit('v0872 river layer close missing')\n    end+=4\n    m=m[:end]+layer_add+m[end:]"""
if old not in q:
    raise SystemExit('v0873 runner: v0872 brittle anchor block missing')
q=q.replace(old,new,1)
v872.write_text(q,encoding='utf-8')

subprocess.run([sys.executable,str(root/'run_patch_native_v0872.py')],check=True)

# v0.8.71 compile repair converts the one-line scheduler comment to a block comment.
# Normalize only the v0.8.73 patch's expected source anchors for the already-applied
# v0.8.72 baseline; these edits affect patch matching/version bump only, not app behavior.
p=root/'patch_native_v0873_source_parity_v2.py'
s=p.read_text(encoding='utf-8')
s=s.replace("poll='main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK'",
            "poll='main.postDelayed(this,1_000L); /* V0871_ONE_SECOND_SOURCE_RECHECK */'",1)
s=s.replace("if 'versionCode 91' in g:g=g.replace('versionCode 91','versionCode 93',1)",
            "if 'versionCode 92' in g:g=g.replace('versionCode 92','versionCode 93',1)",1)
s=s.replace("if \"versionName '0.8.71'\" in g:g=g.replace(\"versionName '0.8.71'\",\"versionName '0.8.73'\",1)",
            "if \"versionName '0.8.72'\" in g:g=g.replace(\"versionName '0.8.72'\",\"versionName '0.8.73'\",1)",1)
p.write_text(s,encoding='utf-8')

subprocess.run([sys.executable,str(p)],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0873_compile_fix.py')],check=True)
print('FloodSafe v0.8.73 complete: v0.8.72 native baseline + river/rain/hydrology-lake realtime parity + compile repair PASS')

# CI retrigger after compile-fix verification.
