from pathlib import Path
p=Path('floodsafe-android-app/app/build.gradle')
s=p.read_text(encoding='utf-8')
if "versionName '0.9.11-sathi-live-all-data-alert-safe'" not in s: raise SystemExit('v0911 version name missing')
if 'versionCode 27' in s:s=s.replace('versionCode 27','versionCode 28',1)
elif 'versionCode 28' not in s: raise SystemExit('unexpected versionCode')
p.write_text(s,encoding='utf-8')
print('V0911_VERSION_CODE_28_OK')
