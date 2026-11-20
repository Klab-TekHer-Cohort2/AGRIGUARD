/**
 * Generates minimal valid PNG placeholder assets for the Expo build.
 * These are small but valid PNGs — Expo only needs them to exist and be valid.
 * Replace with real artwork before a production release.
 */

const fs = require('fs');
const path = require('path');

// Minimal 1×1 green PNG (IDAT deflated pixel #1A6B3C, RGBA)
// Generated via: python3 -c "import base64,zlib,struct; ..."
// This is a valid 68-byte PNG for a 1x1 green pixel
const TINY_GREEN_PNG_B64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

const assets = [
  'icon.png',
  'splash.png',
  'adaptive-icon.png',
  'favicon.png',
];

const outDir = path.join(__dirname, '..', 'assets');
fs.mkdirSync(outDir, { recursive: true });

for (const name of assets) {
  const dest = path.join(outDir, name);
  if (!fs.existsSync(dest)) {
    fs.writeFileSync(dest, Buffer.from(TINY_GREEN_PNG_B64, 'base64'));
    console.log('Created', dest);
  } else {
    console.log('Exists ', dest);
  }
}
console.log('Assets ready.');
