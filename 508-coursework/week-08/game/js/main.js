import { Engine } from './engine.js';
import { MAPS, LEGEND } from './maps.js';
import { STORY } from './story.js';
import { AI } from './ai.js';

const SPRITES = ['jingke', 'gaojianli', 'goutu', 'tianguang', 'taizidan',
  'fanyuqi', 'qinwuyang', 'qinwang', 'xiawuju', 'guard'];
const ART = ['yan_market', 'yi_river'];

function loadImage(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

function fallbackTiles() {
  const names = [...new Set(Object.values(LEGEND))];
  const tiles = {};
  names.forEach((n, i) => { tiles[n] = i; });
  return { tileSize: 16, columns: 8, rows: 5, tiles };
}

async function boot() {
  const canvas = document.getElementById('screen');

  const images = {};
  // the walkable world: tile sheet, its index file, and one sheet per character
  const [tilesInfo, tilesImg] = await Promise.all([
    fetch('assets/tiles/tiles.json').then((r) => r.json()).catch(() => fallbackTiles()),
    loadImage('assets/tiles/tiles.png'),
  ]);
  if (tilesImg) images.tiles = tilesImg;
  await Promise.all(SPRITES.map((s) =>
    loadImage(`assets/sprites/${s}.png`).then((i) => { images['sprite_' + s] = i; })));
  await Promise.all(ART.map((a) =>
    loadImage(`assets/pixel/scenes/${a}.png`).then((i) => { images['art_' + a] = i; })));

  const ai = new AI();
  await ai.ping();

  const engine = new Engine(canvas, {
    images, tiles: tilesInfo, maps: MAPS, story: STORY, ai,
  });
  window.engine = engine;

  // Chapter jump for the class demo: ?beat=a5_yi or ?beat=a6_palace&node=a6_open
  const q = new URLSearchParams(location.search);
  if (q.has('beat')) {
    engine.startAt(q.get('beat'), q.get('node'));
    if (q.has('walk')) engine.pending = null;
  } else if (q.has('node')) {
    engine.startAt(engine.story.start, q.get('node'));
  } else if (q.has('start')) {
    engine.startGame();
  }

  let last = performance.now();
  const hint = document.getElementById('hint');
  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    try {
      engine.step(dt);
      engine.draw();
    } catch (err) {
      console.error(err);
      if (hint) {
        hint.textContent = 'ERROR: ' + (err && err.message ? err.message : String(err));
        hint.style.color = '#a8352a';
      }
      return;
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  if (ai.standalone && engine.el && engine.el.modelstate) {
    engine.el.modelstate.textContent = '单文件版：无需服务器；AI 不可用，人物改用剧本台词';
  }
  if (hint) {
    hint.textContent = ai.available
      ? (ai.dry ? '离线占位模式（未配置 key）' : '模型在线：可以直接打字与人物对话')
      : '模型未连接：对话走剧本备用文本';
  }
}

boot();
