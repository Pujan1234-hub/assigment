"""Copy the ZIP's UI/data into generated APK assets, retaining relative paths."""
import hashlib
import json
from pathlib import Path
import re
import shutil

project = Path(__file__).resolve().parent
repository = project.parent
destination = project / 'app/build/generated/floodsafe-assets'
if destination.exists():
    shutil.rmtree(destination)
destination.mkdir(parents=True)
for name in ('floodsafe-nepal', 'data'):
    shutil.copytree(repository / name, destination / name,
                    ignore=shutil.ignore_patterns('.*', 'node_modules', '*.map'))
for override in (project / 'android-web').iterdir():
    shutil.copy2(override, destination / 'floodsafe-nepal/v25' / override.name)

# Keep the existing foreground river alarm, with accurate permission/lifecycle copy.
flood = destination / 'floodsafe-nepal/v25/flood-only.js'
text = flood.read_text()
text = text.replace('🔔 चेतावनी सक्रिय', '🔔 app खुला हुँदा चेतावनी सक्रिय')
text = text.replace('🔔 Warning Alert ON', '🔔 Alerts ON while app is open')
flood.write_text(text)

# Check every local entry-point reference before Gradle can package a broken shell.
entry = destination / 'floodsafe-nepal/v25/index.html'
for reference in re.findall(r'(?:src|href)="([^"]+)"', entry.read_text()):
    if reference.startswith(('./', '../')):
        target = (entry.parent / reference.split('?')[0]).resolve()
        if not target.is_relative_to(destination) or not target.is_file():
            raise SystemExit(f'Missing local entry resource: {reference}')
manifest = {}
for path in sorted(destination.rglob('*')):
    if path.is_file():
        manifest[path.relative_to(destination).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
(destination / 'BUNDLE-SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Bundled {len(manifest)} files ({sum(p.stat().st_size for p in destination.rglob("*") if p.is_file()):,} bytes).')
