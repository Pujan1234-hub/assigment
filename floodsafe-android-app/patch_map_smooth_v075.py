from pathlib import Path

root = Path(__file__).resolve().parent
gradle_path = root / 'app/build.gradle'
gradle = gradle_path.read_text(encoding='utf-8')
gradle = gradle.replace('versionCode 18', 'versionCode 19', 1)
gradle = gradle.replace("versionName '0.7.4'", "versionName '0.7.5'", 1)
if 'versionCode 19' not in gradle or "versionName '0.7.5'" not in gradle:
    raise SystemExit('v0.7.5 version bump did not apply; run v0.7.4 patch first')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
index = index_path.read_text(encoding='utf-8')
index = index.replace('<span class="badge green">v0.7.4</span>', '<span class="badge green">v0.7.5</span>', 1)
index = index.replace('<span class="badge green">v0.7.3</span>', '<span class="badge green">v0.7.5</span>', 1)
index_path.write_text(index, encoding='utf-8')

print('FloodSafe v0.7.5 map smooth version patch applied')