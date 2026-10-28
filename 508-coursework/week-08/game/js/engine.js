/*
 * 图穷 - world + dialogue.
 *
 * The canvas owns the place: tiles, sprites, torch light, walking.
 * The DOM owns the conversation: one large portrait, the spoken line, a running
 * transcript, the decisions, and a box where the player writes anything at all.
 *
 * The world still decides everything. The model answers in character and reports
 * which of the listed intents it recognised; it can never move the story except
 * through an intent or option id that this file already knows.
 */

import { Battle } from './battle.js';

export const TS = 16;
export const VW = 480;
export const VH = 270;

const SOLID = new Set([
  'water', 'tree', 'pillar', 'wood_wall', 'palace_wall', 'roof', 'table',
  'lattice', 'curtain', 'banner_yan', 'banner_qin', 'torch', 'void',
]);
const WALK_SPEED = 66;

export const NAMES = {
  narrator: '旁白', jingke: '荆轲', gaojianli: '高渐离', goutu: '狗屠', tianguang: '田光',
  taizidan: '太子丹', fanyuqi: '樊於期', qinwuyang: '秦舞阳', qinwang: '秦王',
  xiawuju: '夏无且', guard: '秦郎中', mengjia: '蒙嘉', guest: '客',
};

export class Engine {
  constructor(canvas, { images, tiles, maps, story, ai }) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    // the backing store is 2x the logical 480x270, so vector shapes and the
    // title art stay smooth instead of blocky
    this.ctx.setTransform(2, 0, 0, 2, 0, 0);
    this.ctx.imageSmoothingEnabled = true;
    this.images = images;
    this.tiles = tiles;
    this.maps = maps;
    this.story = story;
    this.ai = ai;

    this.el = {
      stage: document.getElementById('stage'),
      portrait: document.getElementById('portrait'),
      who: document.getElementById('who'),
      tag: document.getElementById('tag'),
      line: document.getElementById('line'),
      transcript: document.getElementById('transcript'),
      opts: document.getElementById('opts'),
      sayform: document.getElementById('sayform'),
      sayinput: document.getElementById('sayinput'),
      saybtn: document.getElementById('saybtn'),
      hint: document.getElementById('hint'),
      meter: document.getElementById('meter'),
      act: document.getElementById('act'),
      endcard: document.getElementById('endcard'),
      endtag: document.getElementById('endtag'),
      endtitle: document.getElementById('endtitle'),
      endbody: document.getElementById('endbody'),
      endchron: document.getElementById('endchron'),
      endnext: document.getElementById('endnext'),
      title: document.getElementById('titlescreen'),
      startbtn: document.getElementById('startbtn'),
      modelstate: document.getElementById('modelstate'),
      routescreen: document.getElementById('routescreen'),
      explore: document.getElementById('explore'),
      cast: document.getElementById('cast'),
      placename: document.getElementById('placename'),
    };

    this.keys = new Set();
    this.t = 0;
    this.mode = 'title';
    this.fade = 0;
    this.fadeDir = 0;
    this.cost = 0;
    this.history = [];

    this.player = { x: 0, y: 0, dir: 'down', moving: false, anim: 0 };
    this.npcs = [];
    this.triggers = [];
    this.map = null;
    this.camera = { x: 0, y: 0 };

    this.reset();

    addEventListener('keydown', (e) => this.onKey(e, true));
    addEventListener('keyup', (e) => this.onKey(e, false));
    this.el.sayform.addEventListener('submit', (e) => {
      e.preventDefault();
      this.submitSay(this.el.sayinput.value);
    });
    this.el.endnext.addEventListener('click', () => {
      this.hideEnding();
      this.startGame();
    });
    this.el.startbtn.addEventListener('click', () => this.startGame());
    for (const card of document.querySelectorAll('#routescreen .route')) {
      card.addEventListener('click', () => this.chooseRoute(card.dataset.route));
    }
    document.getElementById('frame').addEventListener('click', () => {
      if (this.mode === 'line') this.advance();
    });
    this.el.modelstate.textContent = (ai && ai.available)
      ? (ai.dry ? '离线占位模式' : '模型在线')
      : '模型未连接：对话走备用文本';
    this.el.title.hidden = false;
    this.setPortrait(null);
    this.showStage(false);
  }

  // ------------------------------------------------------------------ state

  reset() {
    this.flags = {};
    this.stats = { sword: 0, composure: 0, trust: 0 };
    this.chronicle = [];
    this.history = [];
    this.beat = null;
    this.node = null;
    this.talkCfg = null;
    this.choiceCfg = null;
    this.busy = false;
    this.cost = 0;
  }

  image(key) { return this.images[key] || null; }

  sprite(name, dir, frame) {
    const sheet = this.image('sprite_' + name);
    if (!sheet) return null;
    const order = { down: 0, left: 2, right: 4, up: 6 };
    return { sheet, sx: ((order[dir] ?? 0) + (frame ? 1 : 0)) * 16, sy: 0, sw: 16, sh: 24 };
  }

  // ------------------------------------------------------------------ world

  setBeat(id) {
    const beat = this.story.beats[id];
    if (!beat) throw new Error('unknown beat ' + id);
    this.beat = beat;
    this.el.act.textContent = beat.act || '';
    this.buildCast(beat);
    this.buildWorld(beat);
    this.mode = 'explore';
    this.showStage(false);
    this.pending = beat.onEnter ? { node: beat.onEnter } : null;
  }

  // the walkable world for this beat: tiles, the player's start, the people
  buildWorld(beat) {
    const raw = beat.map && this.maps ? this.maps[beat.map] : null;
    if (!raw) { this.map = null; this.npcs = []; this.triggers = []; return; }
    const cols = raw.rows[0].length, rowsN = raw.rows.length;
    this.map = {
      cols, rowsN,
      w: cols * TS, h: rowsN * TS,
      grid: raw.rows.map((r) => r.split('').map((c) => raw.legend[c] || 'void')),
    };
    const spawn = beat.spawn || { x: Math.floor(cols / 2), y: Math.floor(rowsN / 2), dir: 'up' };
    this.player.x = (spawn.x + 0.5) * TS;
    this.player.y = (spawn.y + 1) * TS;
    this.player.dir = spawn.dir || 'up';
    this.player.moving = false;
    this.player.anim = 0;
    this.npcs = (beat.npcs || []).map((n) => ({
      id: n.id, sprite: n.sprite || n.id, node: n.node,
      px: (n.x + 0.5) * TS, py: (n.y + 1) * TS,
      dir: 'down', moving: false, anim: 0,
    }));
    this.triggers = (beat.triggers || []).map((t) => ({ ...t }));
    this.updateCamera();
  }

  buildCast(beat) {
    if (!this.el.cast) return;            // the stage no longer lists people as chips
    this.el.cast.innerHTML = '';
    (beat.npcs || []).forEach((npc) => {
      if (!npc.node) return;
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'chip';
      const img = document.createElement('img');
      img.src = `assets/portraits/${npc.sprite || npc.id}.png`;
      img.alt = NAMES[npc.id] || npc.id;
      const label = document.createElement('span');
      label.textContent = NAMES[npc.id] || npc.id;
      chip.appendChild(img);
      chip.appendChild(label);
      chip.addEventListener('click', () => this.runNode(npc.node));
      this.el.cast.appendChild(chip);
    });
  }

  step(dt) {
    this.t += dt;
    if (this.mode === 'battle' && this.battle) { this.battle.update(dt); return; }
    if (this.pending) {
      const node = this.pending.node;
      this.pending = null;
      this.runNode(node);
      return;
    }
    if (this.mode === 'explore' && this.map) {
      this.updateExplore(dt);
      this.updateCamera();
    }
  }

  updateExplore(dt) {
    const k = this.keys;
    let dx = 0, dy = 0;
    if (k.has('arrowleft') || k.has('a')) dx -= 1;
    if (k.has('arrowright') || k.has('d')) dx += 1;
    if (k.has('arrowup') || k.has('w')) dy -= 1;
    if (k.has('arrowdown') || k.has('s')) dy += 1;
    if (dx && dy) { dx *= 0.7071; dy *= 0.7071; }
    this.player.moving = !!(dx || dy);
    if (dx < 0) this.player.dir = 'left';
    else if (dx > 0) this.player.dir = 'right';
    else if (dy < 0) this.player.dir = 'up';
    else if (dy > 0) this.player.dir = 'down';

    if (this.player.moving) {
      this.player.anim += dt * 6;
      const nx = this.player.x + dx * WALK_SPEED * dt;
      const ny = this.player.y + dy * WALK_SPEED * dt;
      if (!this.blocked(nx, this.player.y)) this.player.x = nx;
      if (!this.blocked(this.player.x, ny)) this.player.y = ny;
      this.checkTriggers();
    }
  }

  updateCamera() {
    if (!this.map) return;
    const cx = this.map.w <= VW ? (this.map.w - VW) / 2 : clamp(this.player.x - VW / 2, 0, this.map.w - VW);
    const cy = this.map.h <= VH ? (this.map.h - VH) / 2 : clamp(this.player.y - VH / 2, 0, this.map.h - VH);
    this.camera = { x: cx, y: cy };
  }

  blocked(x, y) {
    const half = 6, foot = 4;
    for (const [px, py] of [[x - half, y], [x + half, y], [x - half, y - foot], [x + half, y - foot]]) {
      const col = Math.floor(px / TS), row = Math.floor(py / TS);
      if (row < 0 || col < 0 || row >= this.map.rowsN || col >= this.map.cols) return true;
      if (SOLID.has(this.map.grid[row][col])) return true;
    }
    for (const n of this.npcs) {
      if (Math.abs(n.px - x) < 13 && Math.abs(n.py - 6 - y) < 12) return true;
    }
    return false;
  }

  checkTriggers() {
    for (const t of this.triggers) {
      if (t.done) continue;
      const px = this.player.x, py = this.player.y;
      if (px > t.x * TS - 8 && px < (t.x + (t.w || 1)) * TS + 8 &&
          py > t.y * TS - 12 && py < (t.y + (t.h || 1)) * TS + 12) {
        t.done = true;
        this.runNode(t.node);
        return;
      }
    }
  }

  nearNpc() {
    let best = null, bestD = 30;
    for (const n of this.npcs) {
      if (!n.node) continue;
      const d = Math.hypot(n.px - this.player.x, n.py - 8 - this.player.y);
      if (d < bestD) { best = n; bestD = d; }
    }
    return best;
  }

  interact() {
    const n = this.nearNpc();
    if (!n) return;
    const dx = n.px - this.player.x, dy = n.py - this.player.y;
    this.player.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    n.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'left' : 'right') : (dy > 0 ? 'up' : 'down');
    this.runNode(n.node);
  }

  // ------------------------------------------------------------------- flow

  runNode(id) {
    const node = this.story.nodes[id];
    if (!node) { console.warn('missing node', id); this.mode = 'explore'; return; }
    this.node = node;
    this.nodeId = id;
    this.talkCfg = null;
    this.choiceCfg = null;
    this.lines = (node.lines || []).map((l) => (typeof l === 'string' ? { who: 'narrator', text: l } : l));
    this.lineIndex = 0;
    if (this.lines.length) {
      this.showStage(true);
      this.mode = 'line';
      this.renderLine(this.lines[0]);
    } else {
      this.onNodeDone(node);
    }
  }

  advance() {
    if (this.mode !== 'line') return;
    this.lineIndex += 1;
    if (this.lineIndex < this.lines.length) {
      this.renderLine(this.lines[this.lineIndex]);
      return;
    }
    if (this.pendingAfterChronicle) {
      const fn = this.pendingAfterChronicle;
      this.pendingAfterChronicle = null;
      return fn();
    }
    this.onNodeDone(this.node);
  }

  onNodeDone(node) {
    if (!node) { this.mode = 'explore'; this.showStage(true, true); return; }
    if (node.talk) return this.startTalk(node.talk);
    if (node.battle) return this.startBattle(node.battle);
    if (node.choice) return this.startChoice(node.choice);
    if (node.ending) return this.showEnding(node.ending);
    if (node.beat) return this.queueBeat(node.beat);
    if (node.route) return this.runNode(this.check(node.route) ? node.route.then : node.route.else);
    if (node.next) return this.runNode(node.next);
    this.mode = 'explore';
    this.showStage(true, true);
  }

  queueBeat(id) {
    this.mode = 'explore';
    this.setBeat(id);
  }

  check(cond) {
    if (!cond) return true;
    if (cond.flag) {
      const v = this.flags[cond.flag];
      return cond.value === undefined ? !!v : v === cond.value;
    }
    if (cond.stat) return (this.stats[cond.stat.name] || 0) >= cond.stat.gte;
    if (cond.all) return cond.all.every((c) => this.check(c));
    if (cond.any) return cond.any.some((c) => this.check(c));
    if (cond.not) return !this.check(cond.not);
    return true;
  }

  applyEffect(e = {}) {
    if (e.flags) Object.assign(this.flags, e.flags);
    if (e.stats) for (const [k, v] of Object.entries(e.stats)) this.stats[k] = (this.stats[k] || 0) + v;
  }

  // ------------------------------------------------------------- talk mode

  startTalk(cfg) {
    this.talkCfg = { ...cfg };
    this.mode = 'talk';
    this.showStage(true);
    this.el.stage.classList.remove('narrating');
    this.setPortrait(cfg.npc);
    this.el.tag.hidden = !cfg.counterfactual;
    this.el.opts.innerHTML = '';
    this.el.transcript.style.display = 'flex';
    this.el.transcript.innerHTML = '';
    this.history = [];
    this.el.sayform.hidden = false;
    this.el.sayinput.placeholder = '你要说什么？直接打字，随便说，敲回车说出口';
    if (cfg.opening) {
      this.el.line.className = '';
      this.el.line.textContent = cfg.opening;
      this.pushTranscript(cfg.npc, cfg.opening);
    }
    this.el.sayinput.value = '';
    this.enableInput();
    this.el.hint.textContent = '说什么都行：问事、闲聊、试探；AI 会按其人身份回答';
  }

  enableInput() {
    this.el.sayform.hidden = false;
    this.el.sayinput.disabled = false;
    this.el.saybtn.disabled = false;
    this.el.sayinput.focus();
  }

  async submitSay(text) {
    const said = (text || '').trim();
    if (!said || this.busy) return;
    const cfg = this.talkCfg;
    const choice = this.choiceCfg;
    const npc = cfg ? cfg.npc : (choice && (choice.npc || 'narrator'));
    if (!npc) return;

    this.busy = true;
    this.el.sayinput.value = '';
    this.el.sayinput.disabled = true;
    this.el.saybtn.disabled = true;

    this.el.line.className = 'player';
    this.el.line.textContent = said;
    this.pushTranscript('you', said);
    this.el.hint.textContent = '……';

    const reply = this.ai ? await this.ai.talk({
      npc,
      profile: cfg ? cfg.profile : choice.profile,
      scene: (cfg && cfg.scene) || (this.beat && this.beat.act) || '',
      perception: (cfg && cfg.perception) || (choice && choice.perception) || '',
      player_role: (cfg && cfg.player_role) || '荆轲，燕之上卿',
      text: said,
      intents: (cfg && cfg.intents) || [],
      options: (choice && choice.options) || [],
      history: this.history.slice(-8),
    }) : null;

    this.busy = false;
    const answer = (reply && reply.reply) ? reply.reply : (cfg ? (cfg.fallback || '……') : '……');
    this.el.stage.classList.remove('narrating');
    this.setPortrait(npc);
    this.el.line.className = '';
    this.el.line.textContent = answer;
    this.pushTranscript(npc, answer);
    if (reply && typeof reply.cost === 'number') {
      this.cost += reply.cost;
      this.el.meter.textContent = `本局模型花费 ¥${this.cost.toFixed(4)}`;
    }
    if (reply && reply.hint) {
      this.el.hint.textContent = '· ' + reply.hint;
    }

    if (choice) {
      const option = (choice.options || []).find((o) => o.id === (reply && reply.option));
      if (option) {
        this.choiceCfg = null;
        this.el.sayform.hidden = true;
        return setTimeout(() => this.pickOption(option), 700);
      }
      this.enableInput();
      this.el.hint.textContent = '再说得明白些也可以：你还没做出决定';
      return;
    }

    const matched = (cfg.intents || []).find((i) => i.id === (reply && reply.intent));
    if (matched && (matched.next || matched.beat || matched.ending)) {
      setTimeout(() => {
        this.talkCfg = null;
        this.el.sayform.hidden = true;
        if (matched.effect) this.applyEffect(matched.effect);
        if (matched.ending) return this.showEnding(matched.ending);
        if (matched.beat) return this.queueBeat(matched.beat);
        return this.runNode(matched.next);
      }, 900);
      return;
    }
    this.enableInput();
    this.el.hint.textContent = '继续说，或者换个话题';
  }

  // ----------------------------------------------------------- choice mode

  startChoice(choice) {
    // No option buttons any more: the player says what they want to do, and the
    // model maps that onto one of the options the world already knows.
    this.choiceCfg = choice;
    this.mode = 'choice';
    this.showStage(true);
    this.el.stage.classList.toggle('narrating', !choice.npc);
    this.setPortrait(choice.npc || null);
    this.el.tag.hidden = !choice.counterfactual;
    this.el.transcript.style.display = 'none';
    this.el.transcript.innerHTML = '';
    this.history = [];
    this.el.line.className = 'narration';
    this.el.line.textContent = choice.prompt || '';
    this.el.opts.innerHTML = '';
    this.el.sayform.hidden = false;
    this.el.sayinput.placeholder = '说出你的打算，例如「我把剑架在他颈上」';
    this.el.sayinput.value = '';
    this.enableInput();
    this.el.hint.textContent = choice.hint || '用自己的话说；拿不准，就先问眼前的人';
  }

  pickOption(opt) {
    if (!opt) return;
    this.choiceCfg = null;
    this.el.opts.innerHTML = '';
    this.el.sayform.hidden = true;
    if (opt.effect) this.applyEffect(opt.effect);
    this.resolveOption(opt);
  }

  resolveOption(opt) {
    if (opt.chronicle) return this.speakChronicle(opt.chronicle, opt);
    if (opt.ending) return this.showEnding(opt.ending);
    if (opt.beat) return this.queueBeat(opt.beat);
    if (opt.next) return this.runNode(opt.next);
    this.onNodeDone(this.node);
  }

  async speakChronicle(cfg, opt) {
    this.showStage(true);
    this.el.line.className = 'narration';
    this.el.line.textContent = '（正在推演这一条没有发生的历史……）';
    this.el.hint.textContent = '';
    const res = this.ai ? await this.ai.chronicle({
      divergence: cfg.divergence, context: cfg.context || '',
      outcome: cfg.outcome || '', flags: this.flags, stats: this.stats,
    }) : null;
    const body = (res && res.text) ? res.text : (cfg.fallback || '……');
    if (res && typeof res.cost === 'number') {
      this.cost += res.cost;
      this.el.meter.textContent = `本局模型花费 ¥${this.cost.toFixed(4)}`;
    }
    this.chronicle.push({ divergence: cfg.divergence, text: body });
    this.lines = [{ who: 'narrator', text: body, counterfactual: true }];
    this.lineIndex = 0;
    this.mode = 'line';
    this.pendingAfterChronicle = () => {
      if (opt.ending) return this.showEnding(opt.ending);
      if (opt.beat) return this.queueBeat(opt.beat);
      if (opt.next) return this.runNode(opt.next);
      this.onNodeDone(this.node);
    };
    this.renderLine(this.lines[0]);
  }

  // ---------------------------------------------------------------- render

  showStage(on, exploring = false) {
    this.el.stage.hidden = !on;
    this.el.stage.classList.toggle('exploring', !!exploring);
  }

  setPortrait(who) {
    const img = this.el.portrait;
    if (!who || who === 'narrator') {
      img.style.opacity = who === 'narrator' ? '0.22' : '0';
      this.el.who.textContent = '旁白';
      return;
    }
    const file = who === 'you' ? 'jingke' : who;
    img.onerror = () => {
      // cartoon portrait first, ink-wash fallback if that slug is missing
      if (!img.dataset.fellback) {
        img.dataset.fellback = '1';
        img.style.visibility = 'hidden';
      } else {
        img.style.visibility = 'hidden';
      }
    };
    img.onload = () => { img.style.visibility = 'visible'; img.dataset.fellback = ''; };
    img.style.opacity = '1';
    img.dataset.fellback = '';
    img.src = `assets/portraits/${file}.png`;
    img.alt = NAMES[file] || file;
    this.el.who.textContent = NAMES[file] || file;
  }

  renderLine(line) {
    const isNarr = line.who === 'narrator';
    this.setPortrait(line.who);
    this.el.stage.classList.toggle('narrating', isNarr);
    this.el.tag.hidden = !line.counterfactual;
    this.el.transcript.style.display = isNarr ? 'none' : 'flex';
    this.el.line.className = isNarr ? 'narration' : (line.who === 'you' ? 'player' : '');
    this.el.line.textContent = line.text || '';      // the line itself
    this.el.sayform.hidden = true;
    this.mode = 'line';
    this.el.hint.textContent = '空格 / 点击画面 继续';
  }

  pushTranscript(who, text) {
    const row = document.createElement('div');
    row.className = 't' + (who === 'you' ? ' me' : '');
    const b = document.createElement('b');
    b.textContent = who === 'you' ? '你' : (NAMES[who] || who);
    const s = document.createElement('span');
    s.textContent = text;
    row.appendChild(b);
    row.appendChild(s);
    this.el.transcript.appendChild(row);
    this.el.transcript.scrollTop = this.el.transcript.scrollHeight;
    this.history.push({ who: who === 'you' ? '荆轲' : (NAMES[who] || who), text });
  }

  // ---------------------------------------------------------------- battle

  startBattle(role) {
    this.showStage(false);
    this.el.title.hidden = true;
    this.mode = 'battle';
    this.battle = new Battle(this.canvas, {
      role,
      onEnd: (kind) => {
        this.battle && this.battle.destroy();
        this.battle = null;
        const table = (this.story.battleEndings && this.story.battleEndings[role]) || {};
        const id = table[kind] || 'end_history';
        this.role = role;
        this.showEnding(id);
      },
    });
  }

  // --------------------------------------------------------------- endings

  showEnding(id) {
    const e = this.story.endings[id];
    if (!e) return;
    this.ending = { ...e, id };
    this.mode = 'ending';
    this.showStage(false);
    this.el.endtag.textContent = e.tag || (e.history ? '史实' : '史外 · 推演');
    this.el.endtitle.textContent = e.title;
    this.el.endbody.innerHTML = '';
    for (const p of (e.paragraphs || [])) {
      const el = document.createElement('p');
      el.textContent = p;
      this.el.endbody.appendChild(el);
    }
    if (this.chronicle.length) {
      const wrap = document.createElement('div');
      const h = document.createElement('h2');
      h.textContent = '你所改变的历史';
      wrap.appendChild(h);
      for (const c of this.chronicle) {
        const d = document.createElement('div');
        d.className = 'c';
        const b = document.createElement('b');
        b.textContent = c.divergence;
        const s = document.createElement('span');
        s.textContent = c.text;
        d.appendChild(b);
        d.appendChild(s);
        wrap.appendChild(d);
      }
      this.el.endchron.innerHTML = '';
      this.el.endchron.appendChild(wrap);
      this.el.endchron.hidden = false;
    } else {
      this.el.endchron.hidden = true;
    }
    this.el.endcard.hidden = false;
    this.el.endnext.textContent = '回到开头';
    this.el.endnext.focus();
  }

  hideEnding() { this.el.endcard.hidden = true; }

  // jump straight to a beat, used by the ?beat= demo links
  startAt(beatId, nodeId) {
    this.hideEnding();
    this.el.title.hidden = true;
    this.el.routescreen.hidden = true;
    this.reset();
    this.setBeat(beatId);
    if (nodeId) { this.pending = null; this.runNode(nodeId); }
  }

  startGame() {
    this.hideEnding();
    this.el.title.hidden = true;
    this.reset();
    this.showRoutes();
  }

  // the route is picked by clicking a card, not by typing a sentence
  showRoutes() {
    this.mode = 'title';
    this.el.routescreen.hidden = false;
    const first = this.el.routescreen.querySelector('.route');
    if (first) first.focus();
  }

  chooseRoute(role) {
    this.el.routescreen.hidden = true;
    if (role === 'palace') {
      // short cut: straight to the audience hall
      this.route = 'jingke';
      this.flags = this.flags || {};
      this.flags.route = 'jingke';
      this.setBeat('a6_palace');
      return;
    }
    this.flags = this.flags || {};
    if (role === 'qinwang' || role === 'qin') {
      this.route = 'qin';
      this.flags.route = 'qin';
      this.setBeat((this.story.routes && this.story.routes.qinwang) || 'q1_court');
    } else {
      this.route = 'jingke';
      this.flags.route = 'jingke';
      this.setBeat((this.story.routes && this.story.routes.jingke) || 'a1_market');
    }
  }

  // ------------------------------------------------------------------ keys

  onKey(e, down) {
    const k = e.key.toLowerCase();
    if (this.mode === 'battle') return;            // the arena owns the keyboard
    if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(k) &&
        e.target && e.target.tagName === 'INPUT') {
      return;                                // let the text box own its keys
    }
    if (down) this.keys.add(k); else this.keys.delete(k);
    if (!down) return;
    if (this.mode === 'title') {
      if (k === 'enter' || k === ' ') this.startGame();
      return;
    }
    if (this.mode === 'ending') return;
    if (this.mode === 'line') {
      if (k === ' ' || k === 'enter') this.advance();
      return;
    }
    if (this.mode === 'explore') {
      if (k === 'e' || k === ' ') this.interact();
      return;
    }
    if (this.mode === 'choice') {
      const n = parseInt(k, 10);
      if (n >= 1 && this.choiceCfg && n <= this.choiceCfg.options.length) {
        this.pickOption(this.choiceCfg.options[n - 1]);
      }
    }
  }

  // ------------------------------------------------------------------ draw

  draw() {
    const c = this.ctx;
    c.imageSmoothingEnabled = true;
    c.fillStyle = '#0a0908';
    c.fillRect(0, 0, VW, VH);
    if (this.mode === 'battle' && this.battle) { this.battle.draw(); return; }
    if (this.mode === 'title') { this.drawTitle(); return; }
    if (this.map) this.drawWorld();
  }

  // the place: tiles, people, torch light, and the "E 交谈" prompt
  drawWorld() {
    const c = this.ctx;
    const cam = this.camera;
    const sheet = this.image('tiles');
    c.imageSmoothingEnabled = false;
    if (!this.map || !sheet || !this.tiles) return;
    const cols = this.tiles.columns;
    for (let r = 0; r < this.map.rowsN; r++) {
      for (let x = 0; x < this.map.cols; x++) {
        const name = this.map.grid[r][x];
        const idx = this.tiles.tiles[name];
        if (idx === undefined) continue;
        const dx = Math.round(x * TS - cam.x);
        const dy = Math.round(r * TS - cam.y);
        if (dx < -TS || dx > VW || dy < -TS || dy > VH) continue;
        c.drawImage(sheet, (idx % cols) * TS, Math.floor(idx / cols) * TS, TS, TS, dx, dy, TS, TS);
      }
    }
    this.drawLights(cam);

    const actors = this.npcs.map((n) => ({ ...n, kind: 'npc' }))
      .concat([{ ...this.player, px: this.player.x, py: this.player.y, kind: 'player' }])
      .sort((a, b) => a.py - b.py);
    for (const a of actors) {
      const frame = a.moving ? Math.floor(a.anim * 3) % 2 === 1 : false;
      this.drawActor(a.sprite || 'jingke', a.dir, a.px, a.py, frame);
      if (a.kind === 'npc' && a.id) {
        this.label(a.px - cam.x, a.py - 32 - cam.y, NAMES[a.id] || a.id);
      }
    }
    if (this.mode === 'explore') {
      const near = this.nearNpc();
      if (near) this.label(near.px - cam.x, near.py - 46 - cam.y, 'E 交谈');
    }
  }

  drawTitle() {
    // only the backdrop: the title itself is DOM text, so it stays sharp
    const c = this.ctx;
    const art = this.image('art_yan_market');
    if (art) {
      c.imageSmoothingEnabled = true;
      c.globalAlpha = 0.75;
      c.drawImage(art, 0, 0, VW, VH);
      c.globalAlpha = 1;
    }
    const g = c.createRadialGradient(VW / 2, VH / 2, 40, VW / 2, VH / 2, VW / 1.6);
    g.addColorStop(0, 'rgba(10,9,8,.15)');
    g.addColorStop(1, 'rgba(10,9,8,.85)');
    c.fillStyle = g;
    c.fillRect(0, 0, VW, VH);
  }

  drawLights(cam) {
    const c = this.ctx;
    const flicker = 0.86 + 0.14 * Math.sin(this.t * 6.1) * Math.sin(this.t * 2.3);
    c.save();
    c.globalCompositeOperation = 'lighter';
    for (let r = 0; r < this.map.rowsN; r++) {
      for (let cc = 0; cc < this.map.cols; cc++) {
        if (this.map.grid[r][cc] !== 'torch') continue;
        const x = cc * TS + TS / 2 - cam.x, y = r * TS + TS / 2 - cam.y;
        if (x < -60 || x > VW + 60 || y < -60 || y > VH + 60) continue;
        const g = c.createRadialGradient(x, y, 2, x, y, 46);
        g.addColorStop(0, `rgba(255,186,110,${0.16 * flicker})`);
        g.addColorStop(0.5, `rgba(214,132,64,${0.07 * flicker})`);
        g.addColorStop(1, 'rgba(0,0,0,0)');
        c.fillStyle = g;
        c.beginPath();
        c.arc(x, y, 46, 0, Math.PI * 2);
        c.fill();
      }
    }
    c.restore();
  }

  drawActor(spriteName, dir, x, y, frame) {
    const c = this.ctx;
    const cam = this.camera;
    const s = this.sprite(spriteName, dir, frame);
    const dx = Math.round(x - 8 - cam.x), dy = Math.round(y - 24 - cam.y);
    if (s) c.drawImage(s.sheet, s.sx, s.sy, s.sw, s.sh, dx, dy + 2, 16, 24);
    else { c.fillStyle = '#6b4f3a'; c.fillRect(dx + 3, dy + 4, 10, 18); }
    c.fillStyle = 'rgba(0,0,0,.28)';
    c.beginPath();
    c.ellipse(Math.round(x - cam.x), Math.round(y - 1 - cam.y), 7, 3, 0, 0, Math.PI * 2);
    c.fill();
  }

  label(x, y, text) {
    const c = this.ctx;
    if (!text) return;
    c.font = '10px "Microsoft YaHei",sans-serif';
    const w = c.measureText(text).width + 8;
    c.fillStyle = 'rgba(10,9,8,.82)';
    c.fillRect(Math.round(x - w / 2), Math.round(y - 10), w, 13);
    c.fillStyle = '#d9cfbd';
    c.textAlign = 'center';
    c.fillText(text, Math.round(x), Math.round(y));
    c.textAlign = 'left';
  }
}

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
