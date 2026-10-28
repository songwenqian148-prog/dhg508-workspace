/* Print the console and page errors for any URL.
 *   node code/probe_console.mjs "file:///G:/....html"
 */
import { spawn } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const CHROME = process.env.CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9338;
const url = process.argv[2] || 'http://127.0.0.1:8765/';

const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--no-proxy-server',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-probe')}`,
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
const seen = [];
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result);
  } else if (m.method === 'Runtime.exceptionThrown') {
    seen.push('EXCEPTION: ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
  } else if (m.method === 'Runtime.consoleAPICalled') {
    seen.push(m.params.type.toUpperCase() + ': ' + m.params.args.map((a) => a.value ?? a.description).join(' '));
  } else if (m.method === 'Log.entryAdded') {
    seen.push('LOG ' + m.params.entry.level + ': ' + m.params.entry.text);
  }
};
const send = (method, params = {}) => {
  const mid = id++;
  ws.send(JSON.stringify({ id: mid, method, params }));
  return new Promise((resolve, reject) => pending.set(mid, { resolve, reject }));
};

await send('Runtime.enable');
await send('Log.enable');
await send('Page.enable');
await send('Page.navigate', { url });
await sleep(4000);
const state = await send('Runtime.evaluate', {
  expression: 'JSON.stringify({ mode: (window.engine && engine.mode) || null, title: document.title, state: (document.getElementById("modelstate")||{}).textContent })',
  returnByValue: true,
});
console.log('state:', state.result.value);
console.log('--- messages ---');
for (const line of seen.slice(0, 25)) console.log(line);
ws.close();
chrome.kill();
