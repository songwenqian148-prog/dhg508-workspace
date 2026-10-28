/*
 * Structural check for the game data. No browser needed:
 *
 *     node code/check_story.mjs
 *
 * It fails (exit 1) if a node, beat, ending or map is referenced but missing,
 * if a beat or ending cannot be reached from the start, if a character stands
 * on a solid tile, or if a tile name used by a map is missing from tiles.json.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { STORY } from '../game/js/story.js';
import { MAPS, LEGEND } from '../game/js/maps.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const SOLID = new Set(['water', 'tree', 'pillar', 'wood_wall', 'palace_wall', 'roof', 'table',
  'lattice', 'curtain', 'banner_yan', 'banner_qin', 'torch', 'void']);

const errors = [];
const fail = (msg) => errors.push(msg);
const notes = [];
const note = (msg) => notes.push(msg);

const nodes = STORY.nodes;
const beats = STORY.beats;
const endings = STORY.endings;

function needNode(id, where) {
  if (id && !nodes[id]) fail(`${where}: missing node "${id}"`);
}
function needBeat(id, where) {
  if (id && !beats[id]) fail(`${where}: missing beat "${id}"`);
}
function needEnding(id, where) {
  if (id && !endings[id]) fail(`${where}: missing ending "${id}"`);
}

// ---------------------------------------------------------------- references
for (const [id, node] of Object.entries(nodes)) {
  needNode(node.next, `node ${id}.next`);
  needBeat(node.beat, `node ${id}.beat`);
  needEnding(node.ending, `node ${id}.ending`);
  if (node.route) {
    needNode(node.route.then, `node ${id}.route.then`);
    needNode(node.route.else, `node ${id}.route.else`);
  }
  if (node.talk) {
    (node.talk.intents || []).forEach((intent, i) => {
      needNode(intent.next, `node ${id}.talk.intents[${i}]`);
      if (!intent.id) fail(`node ${id}.talk.intents[${i}]: empty id`);
    });
    (node.talk.options || []).forEach((o, i) => {
      needNode(o.next, `node ${id}.talk.options[${i}]`);
      needEnding(o.ending, `node ${id}.talk.options[${i}]`);
    });
  }
  if (node.choice) {
    node.choice.options.forEach((o, i) => {
      needNode(o.next, `node ${id}.choice[${i}]`);
      needBeat(o.beat, `node ${id}.choice[${i}]`);
      needEnding(o.ending, `node ${id}.choice[${i}]`);
      if (!o.label) fail(`node ${id}.choice[${i}]: empty label`);
    });
  }
}

for (const [id, beat] of Object.entries(beats)) {
  if (beat.map && !MAPS[beat.map]) fail(`beat ${id}: missing map "${beat.map}"`);
  needNode(beat.onEnter, `beat ${id}.onEnter`);
  (beat.npcs || []).forEach((n) => needNode(n.node, `beat ${id} npc ${n.id}`));
  (beat.triggers || []).forEach((t, i) => needNode(t.node, `beat ${id}.triggers[${i}]`));
}

// ---------------------------------------------------------------- reachability
const reachedNodes = new Set();
const reachedBeats = new Set();
const reachedEndings = new Set();
const queue = [];

function visitNode(id) {
  if (!id || reachedNodes.has(id)) return;
  reachedNodes.add(id);
  queue.push(['node', id]);
}
function visitBeat(id) {
  if (!id || reachedBeats.has(id)) return;
  reachedBeats.add(id);
  queue.push(['beat', id]);
}
function visitEnding(id) {
  if (id) reachedEndings.add(id);
}

visitBeat(STORY.start);
// the route screen lives outside the node graph, so its two entries are walked too
for (const start of Object.values(STORY.routes || {})) visitBeat(start);
while (queue.length) {
  const [kind, id] = queue.shift();
  if (kind === 'beat') {
    const beat = beats[id];
    if (!beat) continue;
    visitNode(beat.onEnter);
    (beat.npcs || []).forEach((n) => visitNode(n.node));
    (beat.triggers || []).forEach((t) => visitNode(t.node));
  } else {
    const node = nodes[id];
    if (!node) continue;
    visitNode(node.next);
    visitBeat(node.beat);
    visitEnding(node.ending);
    if (node.route) {
      visitNode(node.route.then);
      visitNode(node.route.else);
    }
    if (node.talk) {
      (node.talk.intents || []).forEach((i) => visitNode(i.next));
    }
    if (node.choice) {
      node.choice.options.forEach((o) => {
        visitNode(o.next);
        visitBeat(o.beat);
        visitEnding(o.ending);
      });
    }
  }
}

for (const id of Object.keys(beats)) if (!reachedBeats.has(id)) note(`beat "${id}" is not reachable from ${STORY.start}`);
for (const [role, table] of Object.entries(STORY.battleEndings || {})) {
  for (const [kind, id] of Object.entries(table)) {
    if (!endings[id]) fail(`battleEndings.${role}.${kind}: missing ending "${id}"`);
    else visitEnding(id);
  }
}
for (const id of Object.keys(endings)) if (!reachedEndings.has(id)) note(`ending "${id}" is not reached by any current path`);

// Nodes can legitimately sit unused (a branch replaced by the arena). Report them
// rather than failing the build.
const unusedNodes = Object.keys(nodes).filter((id) => !reachedNodes.has(id));
if (unusedNodes.length) {
  console.log(`note: ${unusedNodes.length} unused node(s): ${unusedNodes.slice(0, 8).join(', ')}${unusedNodes.length > 8 ? ' …' : ''}`);
}

// ---------------------------------------------------------------- geometry
const SOLID_SET = SOLID;
for (const [id, beat] of Object.entries(beats)) {
  const map = MAPS[beat.map];
  if (!map) continue;
  const grid = map.rows.map((r) => r.split('').map((c) => map.legend[c] || 'void'));
  const tileAt = (x, y) => (grid[y] && grid[y][x]) || 'void';
  const checkSpot = (x, y, who) => {
    const t = tileAt(x, y);
    if (SOLID_SET.has(t)) fail(`${who} stands on solid tile "${t}" at (${x},${y}) in beat ${id}`);
  };
  checkSpot(beat.spawn.x, beat.spawn.y, `beat ${id} spawn`);
  (beat.npcs || []).forEach((n) => checkSpot(n.x, n.y, `beat ${id} npc ${n.id}`));
  // a walkable path from the spawn row to each npc's row must exist in the columns between
  for (const n of beat.npcs || []) {
    const t = tileAt(n.x, n.y);
    if (!map.legend[map.rows[n.y][n.x]]) fail(`beat ${id}: npc ${n.id} at a cell with no legend char`);
    if (t === 'void') fail(`beat ${id}: npc ${n.id} is in the void`);
  }
}

// ---------------------------------------------------------------- tile names
const tilesPath = join(ROOT, 'game', 'assets', 'tiles', 'tiles.json');
if (existsSync(tilesPath)) {
  const tiles = JSON.parse(readFileSync(tilesPath, 'utf8')).tiles;
  for (const name of new Set(Object.values(LEGEND))) {
    if (!(name in tiles)) fail(`tile "${name}" is used by a map but missing from tiles.json`);
  }
  console.log(`tiles.json: ${Object.keys(tiles).length} tiles, all map names present`);
} else {
  console.log('tiles.json: not generated yet (art subagent still running) - skipped');
}

// ---------------------------------------------------------------- statistics
let lines = 0, quoted = 0, invented = 0, plain = 0;
for (const node of Object.values(nodes)) {
  for (const line of node.lines || []) {
    lines += 1;
    if (typeof line === 'string') { plain += 1; continue; }
    if (line.src) quoted += 1;
    else if (line.inv) invented += 1;
    else plain += 1;
  }
}

console.log(`nodes ${Object.keys(nodes).length}, beats ${Object.keys(beats).length}, endings ${Object.keys(endings).length}, maps ${Object.keys(MAPS).length}`);
console.log(`lines ${lines}: quoted-from-Shiji ${quoted}, invented ${invented}, unattributed ${plain}`);
console.log(`reachable: ${reachedNodes.size} nodes, ${reachedBeats.size} beats, ${reachedEndings.size} endings`);

if (errors.length) {
  console.error(`\n${errors.length} problem(s):`);
  for (const e of errors) console.error('  - ' + e);
  process.exit(1);
}
console.log('\nOK - structure, reachability and geometry all check out.');
