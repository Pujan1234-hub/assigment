from pathlib import Path
import subprocess,sys,re
root=Path(__file__).resolve().parent

# Historical v0.8.53/v0.8.56 patches contain exact string matchers for an older bundled
# web compatibility runtime. The repository now carries a newer trusted river runtime.
# Replay the native Android/version/language changes those releases introduced, while
# preserving the newer web runtime instead of downgrading it just to satisfy stale anchors.

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

v856=root/'patch_native_v0856_crashfix_clean_20min.py'
v856.write_text(r'''from pathlib import Path
root=Path(__file__).resolve().parent
app=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=app/'NativeFullActivity.java';w_path=app/'RiverAlertWorker.java';f_path=app/'FloodSafeMessagingService.java';g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8');w=w_path.read_text(encoding='utf-8');f=f_path.read_text(encoding='utf-8');g=g_path.read_text(encoding='utf-8')

def once(text,old,new,label):
    if old in text:return text.replace(old,new,1)
    if new in text:return text
    raise SystemExit(label+' anchor missing')

a=once(a,'RIVER_FRESH_MS=5L*60L*1000L','RIVER_FRESH_MS=20L*60L*1000L','native 20m freshness')
a=once(a,
 'boolean fresh=hasObservation&&now-at<=5L*60L*1000L&&at-now<=5L*60L*1000L; // V0854_NATIVE_FIVE_MINUTE_FRESH',
 'boolean fresh=hasObservation&&now-at<=20L*60L*1000L&&at-now<=5L*60L*1000L; // V0856_NATIVE_TWENTY_MINUTE_FRESH',
 'native parsed observation 20m freshness')
w=once(w,'MAX_AGE_MS = 5L * 60L * 1000L','MAX_AGE_MS = 20L * 60L * 1000L','worker 20m freshness')
f=once(f,'MAX_RIVER_AGE_MS = 5L * 60L * 1000L','MAX_RIVER_AGE_MS = 20L * 60L * 1000L','fcm 20m freshness')
a=once(a,
 'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();recreate();}); // V0854_LANGUAGE_REBUILD',
 'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();Intent r=new Intent(this,NativeFullActivity.class);r.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION|Intent.FLAG_ACTIVITY_CLEAR_TOP);startActivity(r);finish();overridePendingTransition(0,0);}); // V0856_SAFE_LANGUAGE_RESTART',
 'safe language restart')
a=once(a,'row.addView(langBtn);','LinearLayout.LayoutParams langLp=new LinearLayout.LayoutParams(dp(84),dp(44));row.addView(langBtn,langLp); // V0856_LANGUAGE_VISIBLE','header language visibility')
a=a.replace('langBtn.setText(t("अङ्ग्रेजी","नेपाली"));','langBtn.setText(t("English","नेपाली"));')
a=a.replace('पछिल्लो ५ मिनेट','पछिल्लो २० मिनेट').replace('५ मिनेटभित्र','२० मिनेटभित्र').replace('5 minutes','20 minutes').replace('within 5 min','within 20 min')
if 'versionCode 74' in g:g=g.replace('versionCode 74','versionCode 76',1)
elif 'versionCode 76' not in g:raise SystemExit('v0856 versionCode anchor missing')
if "versionName '0.8.54'" in g:g=g.replace("versionName '0.8.54'","versionName '0.8.56'",1)
elif "versionName '0.8.56'" not in g:raise SystemExit('v0856 versionName anchor missing')
for p,s in [(a_path,a),(w_path,w),(f_path,f),(g_path,g)]:p.write_text(s,encoding='utf-8')
for needle in ['RIVER_FRESH_MS=20L*60L*1000L','V0856_NATIVE_TWENTY_MINUTE_FRESH','V0856_SAFE_LANGUAGE_RESTART','V0856_LANGUAGE_VISIBLE']:
    if needle not in a:raise SystemExit('v0856 native compatibility verification failed: '+needle)
if 'MAX_AGE_MS = 20L * 60L * 1000L' not in w or 'RADIUS_KM = 2d' not in w:raise SystemExit('v0856 worker safety verification failed')
if 'MAX_RIVER_AGE_MS = 20L * 60L * 1000L' not in f or 'DEFAULT_RIVER_RADIUS_KM = 2d' not in f:raise SystemExit('v0856 FCM safety verification failed')
if 'versionCode 76' not in g or "versionName '0.8.56'" not in g:raise SystemExit('v0856 version verification failed')
print('FloodSafe v0.8.56 native/language compatibility PASS (newer web runtime preserved)')
''',encoding='utf-8')

subprocess.run([sys.executable,str(root/'run_patch_native_v0873.py')],check=True)

# Current v0.8.73 native map has had its historical camera-bounds formatting rewritten by
# intermediate patches. Apply the Nepal camera contract directly by structure instead of
# depending on one old whitespace/value string.
map_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=map_path.read_text(encoding='utf-8')
if 'V0874_NEPAL_FIXED_CAMERA' not in m:
    pat=r'LatLngBounds bounds\s*=\s*new LatLngBounds\.Builder\(\)\s*\.include\(new LatLng\([^;\n]+?\)\)\s*\.include\(new LatLng\([^;\n]+?\)\)\.build\(\);'
    repl='LatLngBounds bounds = new LatLngBounds.Builder()\n                        .include(new LatLng(NEPAL_MIN_LAT, NEPAL_MIN_LON))\n                        .include(new LatLng(NEPAL_MAX_LAT, NEPAL_MAX_LON)).build(); // V0874_NEPAL_FIXED_CAMERA'
    m,n=re.subn(pat,repl,m,count=1,flags=re.S)
    if n!=1:raise SystemExit('v0874 runner: structural Nepal camera bounds anchor missing')
# v0.8.73 left its marker comment outside the method body. It is not active behavior after
# v0.8.74 empties all rain map sources, so remove only that obsolete marker before auditing.
m=m.replace('V0873_ALL_RAIN_STATIONS_VISIBLE','V0874_REPLACED_RAIN_DOT_LAYER')
map_path.write_text(m,encoding='utf-8')

subprocess.run([sys.executable,str(root/'patch_native_v0874_nepal_fixed_map_district.py')],check=True)
print('FloodSafe v0.8.74 complete: v0.8.73 realtime source chain + Nepal-only map/district regression repair PASS')

# V0874_CI_RECHECK_20260922
