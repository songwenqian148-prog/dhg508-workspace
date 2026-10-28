/* Render the five places as pixel scene images from the tile maps.
 *
 *   node code/render_pixel_scenes.mjs
 *
 * It opens the game page, uses the map data already loaded there (engine.maps),
 * draws each map into a canvas with the 16x16 tile sheet, and writes
 *   game/assets/pixel/scenes/<map>.png
 * so the stage can show a pixel background without the walkable world.
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const OUT = join(ROOT, 'game', 'assets', 'pixel', 'scenes');
const CHROME = process.env.CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const GAME_URL = process.env.GAME_URL || 'http://127.0.0.1:8765';
const PORT = Number(process.env.CDP_PORT || 9340);

mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--no-proxy-server',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-render')}`,
  'about:blank',
], { stdio: 'ignore' });

let target = null;
for (let i = 0; i < 60 && !target; i++) {
  try {
    const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
    target = list.find((t) => t.type === 'page');
  } catch { /* starting */ }
  if (!target) await sleep(250);
}
if (!target) { console.error('chrome did not start'); process.exit(1); }

const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let id = 1;
const pending = new Map();
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result);
  }
};
const send = (method, params = {}) => {
  const mid = id++;
  ws.send(JSON.stringify({ id: mid, method, params }));
  return new Promise((resolve, reject) => pending.set(mid, { resolve, reject }));
};

await send('Page.enable');
await send('Runtime.enable');
await send('Page.navigate', { url: `${GAME_URL}/?render=1` });
await sleep(3000);

const result = await send('Runtime.evaluate', {
  awaitPromise: true,
  returnByValue: true,
  expression: `(async () => {
    const maps = engine.maps;
    const info = await (await fetch('assets/tiles/tiles.json')).json();
    const sheet = await new Promise((res) => { const i = new Image(); i.onload = () => res(i); i.src = 'assets/tiles/tiles.png'; });
    const TS = 16, cols = info.columns;
    const out = {};
    for (const [name, map] of Object.entries(maps)) {
      const grid = map.rows.map((r) => r.split('').map((c) => map.legend[c] || 'void'));
      const cv = document.createElement('canvas');
      cv.width = grid[0].length * TS;
      cv.height = grid.length * TS;
      const c = cv.getContext('2d');
      c.imageSmoothingEnabled = false;
      for (let y = 0; y < grid.length; y++) {
        for (let x = 0; x < grid[y].length; x++) {
          const t = grid[y][x];
          if (t === 'void') continue;
          const idx = info.tiles[t];
          if (idx === undefined) continue;
          c.drawImage(sheet, (idx % cols) * TS, Math.floor(idx / cols) * TS, TS, TS, x * TS, y * TS, TS, TS);
        }
      }
      out[name] = cv.toDataURL('image/png');
    }
    return out;
  })()`,
});

if (result.exceptionDetails) {
  console.error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
  process.exit(1);
}
const maps = result.result.value;
for (const [name, dataUrl] of Object.entries(maps)) {
  const b64 = dataUrl.split(',')[1];
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(b64, 'base64'));
  console.log('  wrote', name + '.png');
}
console.log(`done: ${Object.keys(maps).length} pixel scenes`);
ws.close();
chrome.kill();
