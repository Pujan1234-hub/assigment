import sharp from 'sharp';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(here, '..');
const repoRoot = resolve(appRoot, '..');
const input = resolve(repoRoot, 'fixcheck', 'favicon.svg');
const resources = resolve(appRoot, 'resources');
mkdirSync(resources, { recursive: true });
await sharp(input).resize(512, 512).png().toFile(resolve(resources, 'icon.png'));
console.log('Generated FixCheck 512x512 app icon.');
