from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent
# v0.8.73 MUST start from the accepted fully-native v0.8.72 baseline.
# Apply v0.8.72 first, then only the requested official river/rain/hydrology-lake parity layer.
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
print('FloodSafe v0.8.73 complete: v0.8.72 native baseline + river/rain/hydrology-lake realtime parity patch PASS')
