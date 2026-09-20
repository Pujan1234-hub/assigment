from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent

# The current repository already carries the newer trusted-river web runtime. The historical
# v0.8.53 patch only fails because it expects an obsolete one-line JS implementation. Keep
# its native Android safety/version changes exactly, but do not downgrade/rewrite the newer
# compatibility web runtime just to satisfy that stale text anchor.
v853=root/'patch_native_v0853_five_minute_river_freshness.py'
v853.write_text(r'''from pathlib import Path
root=Path(__file__).resolve().parent
app=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'

def one(path,old,new,label):
    s=path.read_text(encoding='utf-8')
    if old in s:s=s.replace(old,new,1);path.write_text(s,encoding='utf-8')
    elif new not in s:raise SystemExit(label+' anchor missing')

one(app/'NativeFullActivity.java','RIVER_FRESH_MS=10L*60L*1000L','RIVER_FRESH_MS=5L*60L*1000L','native river freshness')
one(app/'RiverAlertWorker.java','MAX_AGE_MS = 10L * 60L * 1000L','MAX_AGE_MS = 5L * 60L * 1000L','background river freshness')
one(app/'FloodSafeMessagingService.java','MAX_RIVER_AGE_MS = 10L * 60L * 1000L','MAX_RIVER_AGE_MS = 5L * 60L * 1000L','FCM river freshness')
gp=root/'app/build.gradle';g=gp.read_text(encoding='utf-8')
if 'versionCode 72' in g:g=g.replace('versionCode 72','versionCode 73',1)
elif 'versionCode 73' not in g:raise SystemExit('v0853 versionCode anchor missing')
if "versionName '0.8.52'" in g:g=g.replace("versionName '0.8.52'","versionName '0.8.53'",1)
elif "versionName '0.8.53'" not in g:raise SystemExit('v0853 versionName anchor missing')
gp.write_text(g,encoding='utf-8')
for p,n in [(app/'NativeFullActivity.java','RIVER_FRESH_MS=5L*60L*1000L'),(app/'RiverAlertWorker.java','RADIUS_KM = 2d'),(app/'FloodSafeMessagingService.java','DEFAULT_RIVER_RADIUS_KM = 2d')]:
    if n not in p.read_text(encoding='utf-8'):raise SystemExit('v0853 native verification failed: '+n)
print('FloodSafe v0.8.53 native five-minute safety compatibility PASS (newer web runtime preserved)')
''',encoding='utf-8')

subprocess.run([sys.executable,str(root/'run_patch_native_v0873.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0874_nepal_fixed_map_district.py')],check=True)
print('FloodSafe v0.8.74 complete: v0.8.73 realtime source chain + Nepal-only map/district regression repair PASS')
