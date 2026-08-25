import { mkdirSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(here, '..');
const repoRoot = resolve(appRoot, '..');
const webSource = resolve(repoRoot, 'fixcheck');
const out = resolve(appRoot, 'www');
mkdirSync(out, { recursive: true });

let html = readFileSync(resolve(webSource, 'index.html'), 'utf8');
html = html.replace('</head>', '<style>#install{display:none!important}</style><script>window.FIXCHECK_NATIVE=true;</script></head>');
writeFileSync(resolve(out, 'index.html'), html);
for (const name of ['favicon.svg', 'manifest.webmanifest', 'ping.txt']) {
  try { copyFileSync(resolve(webSource, name), resolve(out, name)); } catch {}
}
console.log('Prepared FixCheck web assets for native/desktop packaging.');
