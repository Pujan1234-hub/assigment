import { mkdirSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(here, '..');
const repoRoot = resolve(appRoot, '..');
const webSource = resolve(repoRoot, 'fixcheck');
const out = resolve(appRoot, 'www');
const liveBaseline = 'https://pujan1234-hub.github.io/assigment/ping.txt';
mkdirSync(out, { recursive: true });

let html = readFileSync(resolve(webSource, 'index.html'), 'utf8');
// Native/desktop UI is bundled locally, but the comparison baseline must stay remote.
// The live GitHub Pages probe is cross-origin inside Electron/Capacitor, so native builds
// time it with no-cors mode rather than accidentally measuring a bundled local file.
html = html.replaceAll("probes('./ping.txt',6,false)", `probes('${liveBaseline}',6,true)`)
           .replaceAll('probes("./ping.txt",6,false)', `probes("${liveBaseline}",6,true)`)
           .replaceAll("'./ping.txt'", `'${liveBaseline}'`)
           .replaceAll('"./ping.txt"', `"${liveBaseline}"`);
html = html.replace('</head>', '<style>#install{display:none!important}</style><script>window.FIXCHECK_NATIVE=true;</script></head>');
writeFileSync(resolve(out, 'index.html'), html);
for (const name of ['favicon.svg', 'manifest.webmanifest']) {
  try { copyFileSync(resolve(webSource, name), resolve(out, name)); } catch {}
}
console.log('Prepared FixCheck assets. Native baseline:', liveBaseline);
