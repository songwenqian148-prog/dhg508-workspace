/* Print a few DOM facts about the running game.
 *   node code/inspect.mjs [url]
 */
import { spawn } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const CHROME = process.env.CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9342;
const url = process.argv[2] || 'http://127.0.0.1:8765/?start=1';

const chrome = spawn(CHROME, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--no-proxy-server', '--window-size=1440,900',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${join(ROOT, 'artifacts', 'chrome-inspect')}`,
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
const failed = [];
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result);
  } else if (m.method === 'Network.loadingFailed') {
    failed.push(m.params);
  }
};
const send = (method, params = {}) => {
  const mid = id++;
  ws.send(JSON.stringify({ id: mid, method, params }));
  return new Promise((resolve, reject) => pending.set(mid, { resolve, reject }));
};
await send('Page.enable');
await send('Network.enable');
await send('Runtime.enable');
await send('Page.navigate', { url });
await sleep(3500);

const r = await send('Runtime.evaluate', {
  returnByValue: true,
  expression: `(() => {
    const q = (s) => document.querySelector(s);
    const line = q('#line'), panel = q('.panel'), stage = q('#stage'), speak = q('.speaker');
    const cs = line ? getComputedStyle(line) : null;
    return {
      npcs: window.engine ? engine.npcs.map((n) => [n.id, Math.round(n.px), Math.round(n.py)]) : null,
      cam: window.engine ? engine.camera : null,
      names: window.engine ? engine.npcs.map((n) => n.id) : null,
      mode: window.engine ? engine.mode : null,
      nodeId: window.engine ? engine.nodeId : null,
      linesLen: window.engine && engine.lines ? engine.lines.length : null,
      firstLine: window.engine && engine.lines && engine.lines[0] ? JSON.stringify(engine.lines[0]).slice(0, 80) : null,
      lineIdx: window.engine ? engine.lineIndex : null,
      nodeLines: window.engine && engine.current && engine.current.lines ? engine.current.lines.length : null,
      elLine: window.engine ? engine.el.line.textContent.slice(0, 40) : null,
      stageHidden: stage ? stage.hidden : null,
      stageClass: stage ? stage.className : null,
      lineText: line ? line.textContent.slice(0, 60) : null,
      lineBox: line ? line.getBoundingClientRect().toJSON() : null,
      lineStyle: cs ? { color: cs.color, fontSize: cs.fontSize, display: cs.display } : null,
      panelBox: panel ? panel.getBoundingClientRect().toJSON() : null,
      speakerDisplay: speak ? getComputedStyle(speak).display : null,
      portraitW: q('#portrait') ? q('#portrait').getBoundingClientRect().width : null,
    };
  })()`,
});
console.log(JSON.stringify(r.result.value, null, 2));
if (failed.length) console.log('failed requests:', failed.length);
ws.close();
chrome.kill();
