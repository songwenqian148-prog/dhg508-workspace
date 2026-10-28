/*
 * Playtest for the talking game: drives the real page in Chrome over the
 * DevTools protocol, types into the input box, and photographs each state.
 *
 *     python code/server.py        (in another window)
 *     node code/playtest.mjs
 *
 * It fails (exit 1) on a page error or on an expected state that never appears,
 * so it is a smoke test of the new dialogue layer as well as a screenshot run.
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
const PORT = Number(process.env.CDP_PORT || 9334);

mkdirSync(SHOTS, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--no-proxy-server', '--hide-scrollbars',
  '--window-size=1440,900', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-playtest')}`, 'about:blank',
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
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
}

async function shot(name) {
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(SHOTS, name + '.png'), Buffer.from(r.data, 'base64'));
  console.log('  shot', name);
}

/** type into the game's input box the way a player would */
async function say(text) {
  await evaluate(`(() => {
    const i = document.getElementById('sayinput');
    i.value = ${JSON.stringify(text)};
    document.getElementById('sayform').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
  })()`);
}

const ADVANCE = `(() => { for (let i = 0; i < 80 && engine.mode === 'line'; i++) engine.advance(); return engine.mode; })()`;

await send('Page.enable');
await send('Runtime.enable');

const steps = [
  ['01_title', async () => {
    await send('Page.navigate', { url: `${GAME_URL}/` });
    await sleep(3000);
    await evaluate('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
    const mode = await evaluate('engine.mode');
    if (mode !== 'title') throw new Error('expected the title screen, got ' + mode);
  }],

  ['02_talk_gaojianli', async () => {
    await evaluate(`engine.startGame(); engine.setBeat('a1_market'); engine.pending = null; engine.fade = 0;
      engine.runNode('a1_gao')`);
    await evaluate(ADVANCE);
    await sleep(600);
    const before = await evaluate(`document.getElementById('transcript').children.length`);
    await say('足下今日食何物？');
    await sleep(7000);
    const after = await evaluate(`document.getElementById('transcript').children.length`);
    const line = await evaluate(`document.getElementById('line').textContent`);
    if (!(after >= before + 2)) throw new Error(`no exchange recorded (${before} -> ${after})`);
    if (!line || line.length < 4) throw new Error('no reply rendered');
    console.log('    reply:', line.slice(0, 60));
  }],

  ['03_talk_offtopic', async () => {
    const mode = await evaluate('engine.mode');
    if (mode !== 'talk') {
      console.log('    (the first answer already moved the scene on:', mode + ')');
      return;
    }
    const before = await evaluate(`document.getElementById('transcript').children.length`);
    await say('燕市这酒，多少钱一斗？');
    await sleep(7000);
    const after = await evaluate(`document.getElementById('transcript').children.length`);
    const nowMode = await evaluate('engine.mode');
    if (after <= before && nowMode === 'talk') throw new Error('second exchange did not happen');
    console.log('    reply:', (await evaluate(`document.getElementById('line').textContent`)).slice(0, 60));
  }],

  ['04_choice_tianguang', async () => {
    await evaluate(`engine.runNode('a1_tianguang')`);
    await evaluate(ADVANCE);
    await sleep(500);
    const mode = await evaluate('engine.mode');
    if (mode !== 'choice') throw new Error('expected choice, got ' + mode);
  }],

  ['05_chaos_scene', async () => {
    await evaluate(`engine.setBeat('a7_chaos'); engine.pending = null; engine.fade = 0;
      engine.runNode('a7_open')`);
    await evaluate(ADVANCE);
    await sleep(600);
    const mode = await evaluate('engine.mode');
    if (mode !== 'choice') throw new Error('expected chaos choice, got ' + mode);
  }],

  ['06_talk_king', async () => {
    await evaluate(`engine.pickOption(engine.choiceCfg.options[3])`);
    await evaluate(ADVANCE);
    await sleep(600);
    await say('你为何要灭六国？');
    await sleep(7000);
    const who = await evaluate(`document.getElementById('who').textContent`);
    if (!who.includes('秦王')) throw new Error('the king is not speaking, got ' + who);
  }],

  ['07_ending', async () => {
    await evaluate(`engine.showEnding('end_cf_treaty')`);
    await sleep(600);
    const hidden = await evaluate(`document.getElementById('endcard').hidden`);
    if (hidden) throw new Error('ending card did not open');
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
    try { await shot('99_failure_' + name); } catch { /* ignore */ }
    break;
  }
}

console.log(`\nfinal mode: ${await evaluate('engine.mode').catch(() => '?')}`);
if (jsErrors.length) {
  console.log('page errors:');
  for (const e of jsErrors.slice(0, 8)) console.log('  -', e);
}
ws.close();
chrome.kill();
await sleep(300);
if (failed || jsErrors.length) process.exit(1);
console.log('OK - talking, choices and the chaos scene all work.');
