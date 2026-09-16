from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
manifest_path = root / 'app/src/main/AndroidManifest.xml'
gradle_path = root / 'app/build.gradle'

full = src / 'NativeFullActivity.java'
if not full.is_file():
    raise SystemExit('NativeFullActivity.java missing')
text = full.read_text(encoding='utf-8')
required = [
    'Full native Android implementation of the FloodSafe Nepal web dashboard. No WebView is used.',
    'class NativeFullActivity',
    'NativeRiverMap',
    'sync-bipad-rivers',
    'news-live-three',
    'WEATHER',
]
# WEATHER is intentionally validated through real endpoint marker below instead of literal.
for marker in required[:5]:
    if marker not in text:
        raise SystemExit('Native full dashboard marker missing: ' + marker)
if 'api.open-meteo.com/v1/forecast' not in text:
    raise SystemExit('Native weather endpoint missing')
if 'new WebView' in text or 'android.webkit.WebView' in text:
    raise SystemExit('NativeFullActivity must not use WebView')

# Register the full native activity.
manifest = manifest_path.read_text(encoding='utf-8')
activity = '''        <activity\n            android:name=".NativeFullActivity"\n            android:exported="false"\n            android:launchMode="singleTop"\n            android:configChanges="orientation|screenSize|screenLayout|keyboardHidden|smallestScreenSize" />\n\n'''
if 'android:name=".NativeFullActivity"' not in manifest:
    anchor = '        <activity\n            android:name=".NativeHomeActivity"'
    if anchor not in manifest:
        raise SystemExit('NativeHomeActivity manifest anchor missing')
    manifest = manifest.replace(anchor, activity + anchor, 1)
manifest_path.write_text(manifest, encoding='utf-8')

# After the legacy compatibility patches run, route every launcher open to the full native app.
splash_path = src / 'PJBuiltsSplashActivity.java'
splash = splash_path.read_text(encoding='utf-8')
splash = splash.replace('new Intent(this, VoiceMainActivity.class)', 'new Intent(this, NativeFullActivity.class)')
splash = splash.replace('new Intent(this, NativeHomeActivity.class)', 'new Intent(this, NativeFullActivity.class)')
if 'new Intent(this, NativeFullActivity.class)' not in splash:
    raise SystemExit('Unable to route splash to NativeFullActivity')
splash_path.write_text(splash, encoding='utf-8')

# Any legacy WebView/native fallback path should also land on the same full native activity.
main_path = src / 'MainActivity.java'
main = main_path.read_text(encoding='utf-8').replace(
    'new Intent(this, NativeHomeActivity.class)',
    'new Intent(this, NativeFullActivity.class)')
main_path.write_text(main, encoding='utf-8')

# "Ye Sathi" wake notifications and background commands must open the native SATHI UI.
wake_path = src / 'SathiWakeService.java'
wake = wake_path.read_text(encoding='utf-8').replace(
    'new Intent(this, VoiceMainActivity.class)',
    'new Intent(this, NativeFullActivity.class)')
if wake.count('new Intent(this, NativeFullActivity.class)') < 3:
    raise SystemExit('Not all SATHI wake launch routes were moved to NativeFullActivity')
wake_path.write_text(wake, encoding='utf-8')

# Distinct native generation version.
gradle = gradle_path.read_text(encoding='utf-8')
gradle = gradle.replace('versionCode 19', 'versionCode 20', 1)
gradle = gradle.replace("versionName '0.7.5'", "versionName '0.8.0'", 1)
if 'versionCode 20' not in gradle or "versionName '0.8.0'" not in gradle:
    raise SystemExit('v0.8.0 version bump failed; run v0.7.5 patches first')
gradle_path.write_text(gradle, encoding='utf-8')

# Keep the visible version aligned even though the web UI is no longer the launcher.
index_path = root.parent / 'floodsafe-nepal/v25/index.html'
index = index_path.read_text(encoding='utf-8')
index = index.replace('<span class="badge green">v0.7.5</span>', '<span class="badge green">v0.8.0</span>')
index = index.replace('<span class="badge green">v0.7.4</span>', '<span class="badge green">v0.8.0</span>')
index_path.write_text(index, encoding='utf-8')

print('FloodSafe v0.8.0 full native Android launcher patch PASS')
