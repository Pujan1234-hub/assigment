import { copyFileSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(here, '..');
const manifest = resolve(appRoot, 'android', 'app', 'src', 'main', 'AndroidManifest.xml');
const drawable = resolve(appRoot, 'android', 'app', 'src', 'main', 'res', 'drawable');
mkdirSync(drawable, { recursive: true });
copyFileSync(resolve(appRoot, 'resources', 'icon.png'), resolve(drawable, 'fixcheck_icon.png'));
let xml = readFileSync(manifest, 'utf8');
xml = xml.replace(/android:icon="[^"]+"/g, 'android:icon="@drawable/fixcheck_icon"');
xml = xml.replace(/android:roundIcon="[^"]+"/g, 'android:roundIcon="@drawable/fixcheck_icon"');
writeFileSync(manifest, xml);
console.log('Applied FixCheck icon to Android manifest.');
