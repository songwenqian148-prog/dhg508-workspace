/*
 * Headless playthrough: drives the real game in Chrome through the DevTools
 * protocol, presses the same buttons a player would, and saves screenshots.
 *
 *     python code/server.py          (in another window)
 *     node code/shoot.mjs
 *
 * It fails (exit 1) if the page throws, so it doubles as a smoke test of the
 * whole build: story data, engine, map, server, asset paths.
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
const PORT = Number(process.env.CDP_PORT || 9333);

mkdirSync(SHOTS, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ------------------------------------------------------------------ chrome
const chrome = spawn(CHROME, [
  '--headless=new',
  '--no-sandbox',
  '--disable-gpu',
  '--no-proxy-server',
  '--hide-scrollbars',
  '--window-size=1280,780',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-profile')}`,
  'about:blank',
], { stdio: 'ignore' });

async function getJson(path) {
  const res = await fetch(`http://127.0.0.1:${PORT}${path}`);
  return res.json();
}

let target = null;
for (let i = 0; i < 60 && !target; i++) {
  try {
    const list = await getJson('/json/list');
    target = list.find((t) => t.type === 'page');
  } catch { /* chrome still starting */ }
  if (!target) await sleep(250);
}
if (!target) { console.error('chrome did not start'); process.exit(1); }

// --------------------------------------------------------------------- cdp
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
    const d = msg.params.exceptionDetails;
    jsErrors.push(d.exception?.description || d.text);
  } else if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
    jsErrors.push(msg.params.args.map((a) => a.value ?? a.description).join(' '));
  }
};

function send(method, params = {}) {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) {
    throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  }
  return r.result.value;
}

async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(SHOTS, name + '.png'), Buffer.from(r.data, 'base64'));
  console.log('  shot', name);
}

async function navigate(url, wait = 2500) {
  await send('Page.navigate', { url });
  await sleep(wait);
  await evaluate('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
}

// Play the dialogue until the engine leaves dialogue mode (choice / panel / ...).
const ADVANCE = `(() => { for (let i = 0; i < 80 && engine.mode === 'dialogue'; i++) engine.advance(); return engine.mode; })()`;

// ------------------------------------------------------------------- script
await send('Page.enable');
await send('Runtime.enable');

const steps = [
  ['01_title', async () => {
    await navigate(`${GAME_URL}/?instant=1`);
    const mode = await evaluate('engine.mode');
    if (mode !== 'title') throw new Error('expected title, got ' + mode);
  }],

  ['02_dialogue', async () => {
    await evaluate(`engine.startGame(); engine.setBeat('a1_market'); engine.runNode('a1_open')`);
    await evaluate(`for (let i = 0; i < 2; i++) engine.advance()`);
    await sleep(500);
  }],

  ['03_choice', async () => {
    await evaluate(`engine.runNode('a1_memory')`);
    const mode = await evaluate(ADVANCE);
    if (mode !== 'choice') throw new Error('expected choice, got ' + mode);
    await sleep(400);
  }],

  ['04_agentic', async () => {
    await evaluate(`engine.runNode('a1_gao')`);
    await evaluate(ADVANCE);
    await evaluate(`engine.agentic.idx = 1; engine.runAgentic(1)`);
    await sleep(3000);
  }],

  ['05_chronicle', async () => {
    await evaluate(`engine.agentic = null`);
    await evaluate(`engine.runNode('a1_tianguang')`);
    await evaluate(ADVANCE);
    await evaluate(`engine.choices.idx = 1; engine.pickChoice()`);
    await sleep(5000);
    const mode = await evaluate('engine.mode');
    if (mode !== 'panel') throw new Error('expected chronicle panel, got ' + mode);
  }],

  ['06_yi_river', async () => {
    await evaluate(`engine.panel = null; engine.panelThen = null; engine.mode = 'explore'; engine.setBeat('a5_yi'); engine.runNode('a5_open')`);
    await evaluate(`for (let i = 0; i < 3; i++) engine.advance()`);
    await sleep(800);
  }],

  ['07_ending', async () => {
    await evaluate(`engine.showEnding('end_history')`);
    await sleep(500);
    const mode = await evaluate('engine.mode');
    if (mode !== 'ending') throw new Error('expected ending, got ' + mode);
  }],

  ['08_ending_chronicle', async () => {
    await evaluate(`engine.endingPage = 1`);
    await sleep(300);
    const page = await evaluate('engine.endingPage');
    if (page !== 1) throw new Error('expected chronicle page');
  }],

  // The one branch where earlier choices decide the outcome: wait for the man
  // who never came in the record, and the dagger arrives first.
  ['09_counterfactual_win', async () => {
    await evaluate(`engine.flags.waited = true; engine.stats.sword = 1;
      engine.chronicle = []; engine.lastChronicle = null; engine.mode = 'explore';
      engine.setBeat('a6_palace'); engine.pending = null; engine.fade = 0; engine.runNode('a6_sword')`);
    await sleep(300);
    await evaluate(ADVANCE);
    await sleep(6000);
    const before = await evaluate('engine.mode');
    if (before === 'panel') await evaluate(`engine.closePanel()`);
    await evaluate(ADVANCE);
    await sleep(800);
    const id = await evaluate('engine.ending && engine.ending.id');
    if (id !== 'end_counterfactual_win') throw new Error('expected end_counterfactual_win, got ' + id + ' (was ' + before + ')');
  }],

  // Real keyboard events, not engine methods: walking and talking must work.
  ['10_input', async () => {
    await evaluate(`engine.mode = 'explore'; engine.setBeat('a1_market'); engine.pending = null;
      engine.fade = 0; engine.dialog = null; engine.player.x = 4 * 16 + 8; engine.player.y = 11 * 16 + 14; 'ok'`);
    await sleep(200);
    const before = await evaluate('engine.player.x');
    await evaluate(`window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))`);
    await sleep(500);
    await evaluate(`window.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowRight' }))`);
    const after = await evaluate('engine.player.x');
    if (!(after > before)) throw new Error(`walking did not move the player (${before} -> ${after})`);

    // stand right in front of Gao Jianli and press E
    await evaluate(`engine.player.x = 13 * 16 + 4; engine.player.y = 8 * 16 + 14; 'ok'`);
    await sleep(150);
    const near = await evaluate('!!engine.nearNpc()');
    if (!near) throw new Error('no NPC in reach to talk to');
    await evaluate(`window.dispatchEvent(new KeyboardEvent('keydown', { key: 'e' }))`);
    await sleep(400);
    const mode = await evaluate('engine.mode');
    if (mode !== 'dialogue') throw new Error('E did not start a conversation, mode=' + mode);
  }],
];

let failed = null;
for (const [name, fn] of steps) {
  try {
    await fn();
    await shot(name);
  } catch (err) {
    failed = `${name}: ${err.message}`;
    console.error('FAILED at', failed);
    break;
  }
}

console.log(`\nfinal mode: ${await evaluate('engine.mode').catch(() => '?')}`);
if (jsErrors.length) {
  console.log('page errors:');
  for (const e of jsErrors.slice(0, 10)) console.log('  -', e);
}

ws.close();
chrome.kill();
await sleep(300);

if (failed || jsErrors.length) process.exit(1);
console.log('OK - playthrough finished with no page errors.');
