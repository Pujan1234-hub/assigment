from pathlib import Path

p = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java')
s = p.read_text(encoding='utf-8')

old = 'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyTtsLanguage();recreate();}); /* V0918_ATOMIC_LANGUAGE_SWITCH */'
new = 'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyTtsLanguage();v0909SkipMapUpdateOnce=true;applyLanguage();v0909TranslateStaticTree(root);refreshRiverUi();updateWeatherLayerUi();}); /* V0918_LANGUAGE_KEEP_MAP_VISIBLE */'

if old not in s:
    raise SystemExit('v0.9.18 language recreate anchor not found')
if 'V0909_LANGUAGE_PRESERVE_MAP' not in s or 'v0909TranslateStaticTree' not in s:
    raise SystemExit('required in-place language/map-preserve support missing')

s = s.replace(old, new, 1)

if 'V0918_LANGUAGE_KEEP_MAP_VISIBLE' not in s:
    raise SystemExit('language no-flicker marker missing')
if 'applyTtsLanguage();recreate();' in s:
    raise SystemExit('language switch still recreates activity')

p.write_text(s, encoding='utf-8')
print('V0918_LANGUAGE_NO_MAP_RELOAD_OK')
