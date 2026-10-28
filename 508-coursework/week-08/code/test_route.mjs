/* Click the two route cards and check where each one lands.
 *   node code/test_route.mjs
 */
import { spawn } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const CHROME = process.env.CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9346;
const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--no-proxy-server', '--window-size=1440,900',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-route')}`,
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

await send('Page.enable');
await send('Runtime.enable');
await send('Page.navigate', { url: 'http://127.0.0.1:8765/' });
await sleep(3000);

// the title screen only offers 开始
await evaluate(`document.getElementById('startbtn').click()`);
await sleep(600);
const routesVisible = await evaluate(`!document.getElementById('routescreen').hidden`);
console.log('route screen shown:', routesVisible);

for (const role of ['jingke', 'qinwang', 'palace']) {
  if (!(await evaluate(`!document.getElementById('routescreen').hidden`))) {
    await evaluate(`document.getElementById('startbtn').click()`);
    await sleep(400);
  }
  await evaluate(`document.querySelector('#routescreen .route[data-route="${role}"]').click()`);
  await sleep(900);
  const state = await evaluate(`(() => ({ mode: engine.mode, beat: engine.beat && engine.beat.act, map: !!engine.map, npcs: engine.npcs.length }))()`);
  console.log(role, '->', JSON.stringify(state));
  if (state.mode === 'title' || !state.map) {
    console.error('route did not open a place');
    process.exit(1);
  }
  await evaluate(`engine.showRoutes()`);
  await sleep(300);
}
ws.close();
chrome.kill();
console.log('OK - both cards open their place.');
