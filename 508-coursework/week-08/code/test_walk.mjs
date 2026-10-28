/* Check that walking and "E" work in the tile world.
 *   node code/test_walk.mjs
 */
import { spawn } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { writeFileSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const CHROME = process.env.CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9344;

const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--no-proxy-server', '--window-size=1440,900',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-walk')}`,
  'about:blank',
], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let target = null;
for (let i = 0; i < 60 && !target; i++) {
  try {
    const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
    target = list.find((t) => t.type === 'page');
  } catch { /* starting */ }
  if (!target) await sleep(250);
}
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
const evaluate = async (expression) => {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};
const key = (down, k) => evaluate(`window.dispatchEvent(new KeyboardEvent('key${down ? 'down' : 'up'}', { key: ${JSON.stringify(k)} }))`);

await send('Page.enable');
await send('Runtime.enable');
await send('Page.navigate', { url: 'http://127.0.0.1:8765/?beat=a1_market&walk=1' });
await sleep(3000);

const before = await evaluate(`(() => ({ mode: engine.mode, x: Math.round(engine.player.x), y: Math.round(engine.player.y), map: !!engine.map, npcs: engine.npcs.length }))()`);
console.log('start:', JSON.stringify(before));

await key(true, 'd');
await sleep(700);
await key(false, 'd');
const after = await evaluate(`Math.round(engine.player.x)`);
console.log('after walking right:', after, after > before.x ? '(moved)' : '(did not move)');

// stand next to the nearest person and press E
await evaluate(`(() => {
  const n = engine.npcs[0];
  engine.player.x = n.px;
  engine.player.y = n.py + 14;
  return true;
})()`);
await sleep(200);
const near = await evaluate(`(() => { const n = engine.nearNpc(); return n ? n.id : null; })()`);
console.log('nearest npc:', near);
await key(true, 'e');
await key(false, 'e');
await sleep(1500);
const shot = await send('Page.captureScreenshot', { format: 'png' });
writeFileSync(join(ROOT, 'generated', 'screenshots', '15_talk_over_world.png'), Buffer.from(shot.data, 'base64'));
const mode = await evaluate('engine.mode');
console.log('mode after E:', mode);
ws.close();
chrome.kill();
if (!(after > before.x)) process.exit(1);
if (mode === 'explore') process.exit(1);
console.log('OK - walking and talking both work.');
