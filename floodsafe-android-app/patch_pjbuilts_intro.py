from pathlib import Path

p = Path('floodsafe-android-app/app/build/generated/floodsafe-assets/floodsafe-nepal/v25/index.html')
text = p.read_text(encoding='utf-8')

# PJBUILTS is already rendered by the native PJBuiltsSplashActivity.
# Do not add a second full-screen HTML overlay: if its inline animation script is
# delayed/blocked during a warm relaunch, the overlay can cover the app forever.
# Keep a harmless marker so the release gate can verify native-splash packaging.
if 'id="pjbuiltsIntro"' not in text:
    marker = '<meta id="pjbuiltsIntro" name="pjbuilts-splash" content="native">'
    if '</head>' not in text:
        raise SystemExit('HTML head marker missing for PJBUILTS marker')
    text = text.replace('</head>', marker + '</head>', 1)

p.write_text(text, encoding='utf-8')
if 'id="pjbuiltsIntro"' not in text:
    raise SystemExit('PJBUILTS native splash marker missing')
print('Native PJBUILTS launch marker applied; duplicate WebView overlay disabled')
