import { mkdirSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(here, '..');
const repoRoot = resolve(appRoot, '..');
const webAssets = resolve(repoRoot, 'fixcheck');
const out = resolve(appRoot, 'www');
const liveBaseline = 'https://pujan1234-hub.github.io/assigment/fixcheck/ping.txt';
const appSource = 'https://raw.githubusercontent.com/Pujan1234-hub/assigment/0afecb6aab4da3775ba79b4eb4a8d6dfd697ea7f/fixcheck/index.html';
mkdirSync(out, { recursive: true });

// Keep the native app on the tested FixCheck v0.7 UI even if the public web folder
// is later reused by the portfolio site. A failed source fetch aborts the build rather
// than silently packaging the wrong page.
const sourceResponse = await fetch(appSource, { cache: 'no-store' });
if (!sourceResponse.ok) throw new Error(`Unable to load FixCheck v0.7 source: ${sourceResponse.status}`);
let html = await sourceResponse.text();

// Native/desktop UI is bundled locally, but the comparison baseline must stay remote.
// Match any probe count (v0.7 uses 7) and force no-cors for the cross-origin baseline.
html = html.replace(
  /probes\((['"])\.\/ping\.txt\1\s*,\s*(\d+)\s*,\s*false\)/g,
  (_m, _q, count) => `probes('${liveBaseline}',${count},true)`
);

html = html.replace('</head>', '<style>#install{display:none!important}</style><script>window.FIXCHECK_NATIVE=true;</script></head>');
writeFileSync(resolve(out, 'index.html'), html);
for (const name of ['favicon.svg', 'manifest.webmanifest']) {
  try { copyFileSync(resolve(webAssets, name), resolve(out, name)); } catch {}
}
console.log('Prepared pinned FixCheck v0.7 assets. Native baseline:', liveBaseline);
