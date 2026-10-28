/*
 * Tests the 秦王 route and the arena: type your way in, then fight.
 *
 *     python code/server.py
 *     node code/playtest_battle.mjs [jingke|qinwang]
 *
 * Everything is typed or keyed - there is no option button anywhere in the game.
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const SHOTS = join(ROOT, 'generated', 'screenshots');
const CHROME = process.env.CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const GAME_URL = process.env.GAME_URL || 'http://127.0.0.1:8765';
const PORT = Number(process.env.CDP_PORT || 9336);
const ROUTE = process.argv[2] || 'qinwang';

mkdirSync(SHOTS, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--no-proxy-server', '--hide-scrollbars',
  '--window-size=1440,900', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-battle')}`, 'about:blank',
], { stdio: 'ignore' });

let target = null;
for (let i = 0; i < 60 && !target; i++) {
  try {
    const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
    target = list.find((t) => t.type === 'page');
  } catch { /* still starting */ }
  if (!target) await sleep(250);
}
if (!target) { console.error('chrome did not start'); process.exit(1); }

const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let nextId = 1;
const pending = new Map();
const jsErrors = [];
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) reject(new Error(JSON.stringify(msg.error)));
    else resolve(msg.result);
  } else if (msg.method === 'Runtime.exceptionThrown') {
    jsErrors.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
  }
};
const send = (method, params = {}) => {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
};
async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
}
async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(SHOTS, name + '.png'), Buffer.from(r.data, 'base64'));
  console.log('  shot', name);
}
async function say(text) {
  await evaluate(`(() => {
    const i = document.getElementById('sayinput');
    i.value = ${JSON.stringify(text)};
    document.getElementById('sayform').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  })()`);
}
const ADVANCE = `(() => { for (let i = 0; i < 90 && engine.mode === 'line'; i++) engine.advance(); return engine.mode; })()`;
const key = (down, k) => evaluate(`window.dispatchEvent(new KeyboardEvent('key${down ? 'down' : 'up'}',
  { key: ${JSON.stringify(k)} }))`);

await send('Page.enable');
await send('Runtime.enable');
await send('Page.navigate', { url: `${GAME_URL}/` });
await sleep(2500);
await evaluate('engine.startGame()');
await sleep(600);

// prologue: pick a role by typing it
await evaluate(ADVANCE);
await sleep(400);
console.log('  mode after prologue:', await evaluate('engine.mode'));
await say(ROUTE === 'qinwang' ? '我当秦王，从咸阳宫看这一天。' : '我做荆轲。');
await sleep(6500);
console.log('  mode after route:', await evaluate('engine.mode'), 'beat:', await evaluate('engine.beat && engine.beat.act'));
await shot(`11_route_${ROUTE}`);

// The 荆轲 line is long; jump straight to its last minute for this test.
if (ROUTE === 'jingke') {
  await evaluate(`engine.setBeat('a6_palace'); engine.pending = null; engine.runNode('a6_battle')`);
  await sleep(500);
  await evaluate(ADVANCE);
  await sleep(400);
}

// play forward until the arena
for (let i = 0; i < 10; i++) {
  const mode = await evaluate('engine.mode');
  const line = await evaluate(`document.getElementById('line').textContent`);
  console.log(`  [${i}] mode=${mode} line=${(line || '').slice(0, 28)}`);
  if (mode === 'battle') break;
  if (mode === 'line') { await evaluate(ADVANCE); await sleep(300); continue; }
  if (mode === 'choice') {
    await say(ROUTE === 'qinwang'
      ? (i <= 1 ? '让他们上殿，设九宾之礼。' : '取他的地图来。')
      : '抓住他的袖子，刺下去。');
    await sleep(6500);
    continue;
  }
  await sleep(500);
}
const mode = await evaluate('engine.mode');
console.log('  mode before arena:', mode);
if (mode !== 'battle') throw new Error('the arena was never reached, mode=' + mode);
await sleep(500);
await shot(`12_battle_${ROUTE}`);

// drive the arena with real keys
if (ROUTE === 'qinwang') {
  await key(true, 'd');
  await sleep(3200);
  await key(false, 'd');
} else {
  // steer toward the king the way a player would, then swing
  for (let i = 0; i < 120; i++) {
    const st = await evaluate(`(() => { const b = engine.battle; if (!b) return null;
      return { dx: Math.round(b.king.x - b.player.x), dy: Math.round(b.king.y - b.player.y), hits: b.hits }; })()`);
    if (!st) break;
    const held = [];
    if (st.dx > 6) held.push('d'); else if (st.dx < -6) held.push('a');
    if (st.dy > 6) held.push('s'); else if (st.dy < -6) held.push('w');
    for (const k of held) await key(true, k);
    await key(true, 'j');
    await key(false, 'j');
    await sleep(140);
    for (const k of held) await key(false, k);
    if (st.hits >= 3) break;
  }
  const pos = await evaluate(`(() => { const b = engine.battle; return b ? { px: Math.round(b.player.x), py: Math.round(b.player.y), kx: Math.round(b.king.x), ky: Math.round(b.king.y), hits: b.hits, over: b.over } : null; })()`);
  console.log('  arena state:', JSON.stringify(pos));
  const hits = await evaluate('engine.battle ? engine.battle.hits : -1');
  console.log('  hits landed:', hits);
  if (!(hits > 0)) throw new Error('the sword never connected');
  // the arena is 55 s long; finish it here so the test can check the ending wiring
  await evaluate(`engine.battle.finish('win')`);
  await sleep(1500);
}
await sleep(2500);
const after = await evaluate('engine.mode');
console.log('  mode after the arena:', after, 'ending:', await evaluate('engine.ending && engine.ending.id'));
await shot(`13_ending_${ROUTE}`);

if (jsErrors.length) {
  console.log('page errors:');
  for (const e of jsErrors.slice(0, 6)) console.log('  -', e);
}
ws.close();
chrome.kill();
await sleep(300);
if (after !== 'ending') process.exit(1);
console.log('OK - typed route, arena reached, ending reached.');
