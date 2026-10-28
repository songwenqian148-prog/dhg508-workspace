/*
 * The last minute of the attempt, played rather than described.
 *
 * One arena, two roles. Play 荆轲 and you have to reach the king and land three
 * strikes before the clock runs out; play 秦王 and you have to get to the door, or
 * stay alive until the guards reach the hall. Nothing is scripted: the ending is
 * whatever happens on the floor. There is no "you die because the record says so".
 */

export const BATTLE_W = 480;
export const BATTLE_H = 270;

const BATTLE_SOLID = [
  // pillars split top and bottom, so there is a walkable band at mid height
  { x: 96, y: 30, w: 18, h: 70 },
  { x: 96, y: 200, w: 18, h: 40 },
  { x: 240, y: 30, w: 18, h: 70 },
  { x: 240, y: 200, w: 18, h: 40 },
  { x: 372, y: 30, w: 18, h: 70 },
  { x: 372, y: 200, w: 18, h: 40 },
];

const DOOR = { x: 452, y: 100, w: 22, h: 70 };

export class Battle {
  constructor(canvas, { role, onEnd }) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.role = role;                  // 'jingke' | 'qinwang'
    this.onEnd = onEnd;
    // the arena uses the same pixel sprites as the map: 16x24 frames, drawn
    // with nearest-neighbour scaling so the blocks stay square
    this.sprites = {};
    for (const slug of ['jingke', 'qinwang', 'guard']) {
      const img = new Image();
      img.src = `assets/sprites/${slug}.png`;
      this.sprites[slug] = img;
    }
    this.floor = new Image();
    this.floor.src = 'assets/pixel/scenes/xianyang_hall.png';
    this.t = 0;
    this.timeLeft = role === 'jingke' ? 55 : 60;
    this.hits = 0;                     // hits landed on the king / on the king by 荆轲
    this.over = false;
    this.keys = new Set();
    this.shake = 0;

    this.player = role === 'jingke'
      ? { x: 60, y: 135, vx: 0, vy: 0, face: 1, cool: 0, role: 'jingke' }
      : { x: 300, y: 135, vx: 0, vy: 0, face: -1, cool: 0, role: 'qinwang' };
    this.king = role === 'jingke'
      ? { x: 300, y: 135, vx: 0, vy: 0, face: -1, role: 'qinwang', panic: 0 }
      : { x: 180, y: 135, vx: 0, vy: 0, face: 1, role: 'jingke', cool: 0 };
    this.guards = [
      { x: 300, y: 70, vx: 0, vy: 0 },
      { x: 300, y: 210, vx: 0, vy: 0 },
    ];

    this._onKeyDown = (e) => this.keyDown(e);
    this._onKeyUp = (e) => this.keys.delete(e.key.toLowerCase());
    addEventListener('keydown', this._onKeyDown);
    addEventListener('keyup', this._onKeyUp);
    this.banner = role === 'jingke' ? '追上秦王，连刺三下（W A S D 移动，J 出剑）'
      : '逃到殿门，或撑到郎中上殿（W A S D 移动）';
    this.bannerT = 4;
  }

  destroy() {
    removeEventListener('keydown', this._onKeyDown);
    removeEventListener('keyup', this._onKeyUp);
  }

  keyDown(e) {
    const k = e.key.toLowerCase();
    if ([' ', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) e.preventDefault();
    this.keys.add(k);
    if (k === 'j' && this.role === 'jingke') this.attack();
  }

  attack() {
    if (this.over || this.player.cool > 0) return;
    this.player.cool = 0.45;
    this.player.swing = 0.18;
    const reach = 30;
    if (this.role === 'jingke') {
      const dx = this.king.x - this.player.x, dy = this.king.y - this.player.y;
      if (Math.hypot(dx, dy) < reach) {
        this.hits += 1;
        this.king.panic = 2.2;
        this.king.stun = 0.9;
        this.king.x = Math.min(430, this.king.x + 26 * this.player.face);
        this.shake = 0.25;
        if (this.hits >= 3) this.finish('win');
      }
    }
  }

  finish(kind) {
    if (this.over) return;
    this.over = true;
    this.result = kind;
    setTimeout(() => this.onEnd(kind), 700);
  }

  update(dt) {
    if (this.over) return;
    this.t += dt;
    this.timeLeft -= dt;
    this.bannerT = Math.max(0, this.bannerT - dt);
    this.shake = Math.max(0, this.shake - dt);
    const p = this.player;
    p.cool = Math.max(0, p.cool - dt);
    if (p.swing) p.swing = Math.max(0, p.swing - dt);

    let dx = 0, dy = 0;
    const k = this.keys;
    if (k.has('a') || k.has('arrowleft')) dx -= 1;
    if (k.has('d') || k.has('arrowright')) dx += 1;
    if (k.has('w') || k.has('arrowup')) dy -= 1;
    if (k.has('s') || k.has('arrowdown')) dy += 1;
    if (dx && dy) { dx *= 0.71; dy *= 0.71; }
    if (dx) p.face = dx > 0 ? 1 : -1;
    const speed = this.role === 'jingke' ? 108 : 96;
    this.move(p, dx * speed * dt, dy * speed * dt);

    if (this.role === 'jingke') this.updateKing(dt); else this.updateChaser(dt);
    this.updateGuards(dt);

    if (this.role === 'qinwang' && this.reachedDoor(p)) { this.finish('escape'); return; }
    if (this.role === 'jingke' && this.reachedDoor(this.king)) { this.finish('escaped'); return; }
    if (this.timeLeft <= 0) {
      this.finish(this.role === 'jingke' ? 'timeout' : 'saved');
    }
  }

  move(e, dx, dy) {
    const tryX = e.x + dx, tryY = e.y + dy;
    if (!this.blocked(tryX, e.y)) e.x = tryX;
    if (!this.blocked(e.x, tryY)) e.y = tryY;
    e.x = Math.max(16, Math.min(BATTLE_W - 16, e.x));
    e.y = Math.max(24, Math.min(BATTLE_H - 20, e.y));
  }

  blocked(x, y) {
    for (const r of BATTLE_SOLID) {
      if (x > r.x - 10 && x < r.x + r.w + 10 && y > r.y - 10 && y < r.y + r.h + 10) return true;
    }
    return false;
  }

  // 荆轲 is playing: the king runs for the door, and if he gets there he is gone
  updateKing(dt) {
    const k = this.king;
    k.panic = Math.max(0, k.panic - dt);
    k.stun = Math.max(0, (k.stun || 0) - dt);
    if (k.stun > 0) return;
    const dx = k.x - this.player.x, dy = k.y - this.player.y;
    const away = Math.hypot(dx, dy) < 110;
    let vx = 0, vy = 0;
    if (away) {
      vx = Math.sign(dx) * 40;
      vy = Math.sign(dy) * 30;
    } else {
      vx = 16;                     // drift toward the door, slowly
      vy = Math.sin(this.t * 1.7) * 16;
    }
    k.face = vx >= 0 ? 1 : -1;
    this.move(k, vx * dt, vy * dt);
  }

  // 秦王 is playing: 荆轲 chases, and strikes when he is close
  updateChaser(dt) {
    const c = this.king;
    c.cool = Math.max(0, c.cool - dt);
    const dx = this.player.x - c.x, dy = this.player.y - c.y;
    const d = Math.hypot(dx, dy) || 1;
    c.face = dx >= 0 ? 1 : -1;
    this.move(c, (dx / d) * 74 * dt, (dy / d) * 74 * dt);
    if (d < 28 && c.cool <= 0) {
      c.cool = 1.4;
      this.hits += 1;
      this.shake = 0.25;
      this.player.x = Math.min(430, this.player.x + 28 * (dx > 0 ? 1 : -1));
      if (this.hits >= 3) this.finish('caught');
    }
  }

  updateGuards(dt) {
    const target = this.role === 'jingke' ? this.player : this.king;
    for (const g of this.guards) {
      const dx = target.x - g.x, dy = target.y - g.y;
      const d = Math.hypot(dx, dy) || 1;
      if (d > 18) this.move(g, (dx / d) * 52 * dt, (dy / d) * 52 * dt);
    }
  }

  reachedDoor(e) { return e.x > DOOR.x - 6 && e.y > DOOR.y && e.y < DOOR.y + DOOR.h; }

  draw() {
    const c = this.ctx;
    c.save();
    if (this.shake > 0) c.translate((Math.random() - 0.5) * 6, (Math.random() - 0.5) * 6);
    this.drawHall(c);
    for (const r of BATTLE_SOLID) this.drawPillar(c, r);
    this.drawDoor(c);
    for (const g of this.guards) this.chibi(c, g.x, g.y, '#2f3b4c', '#c9a227', 'guard', false);
    this.chibi(c, this.king.x, this.king.y, this.king.role === 'qinwang' ? '#1a1614' : '#2c4a86',
      this.king.role === 'qinwang' ? '#a8352a' : '#c9a227', this.king.role,
      this.king.role === 'jingke' && this.king.cool > 1.1);
    this.chibi(c, this.player.x, this.player.y,
      this.role === 'jingke' ? '#2c4a86' : '#1a1614',
      this.role === 'jingke' ? '#c9a227' : '#a8352a', this.role,
      this.role === 'jingke' && this.player.swing > 0);
    c.restore();
    this.drawHud(c);
    if (this.bannerT > 0) {
      c.fillStyle = 'rgba(10,9,8,.7)';
      c.fillRect(0, 8, BATTLE_W, 26);
      c.fillStyle = '#efe6d4';
      c.font = '12px "Microsoft YaHei", sans-serif';
      c.textAlign = 'center';
      c.fillText(this.banner, BATTLE_W / 2, 25);
      c.textAlign = 'left';
    }
  }

  drawHall(c) {
    c.fillStyle = '#16110e';
    c.fillRect(0, 0, BATTLE_W, BATTLE_H);
    if (this.floor && this.floor.complete && this.floor.naturalWidth) {
      c.save();
      c.imageSmoothingEnabled = false;
      c.globalAlpha = 0.5;
      c.drawImage(this.floor, 0, 0, BATTLE_W, BATTLE_H);
      c.globalAlpha = 1;
      c.restore();
    }
    c.fillStyle = '#241a14';
    for (let x = 0; x < BATTLE_W; x += 24) {
      for (let y = 0; y < BATTLE_H; y += 24) {
        c.fillRect(x + 1, y + 1, 22, 22);
      }
    }
    c.fillStyle = 'rgba(168,53,42,.16)';
    c.fillRect(0, 0, BATTLE_W, 16);
    c.fillRect(0, BATTLE_H - 14, BATTLE_W, 14);
  }

  drawPillar(c, r) {
    c.fillStyle = '#7d1f18';
    c.fillRect(r.x, r.y, r.w, r.h);
    c.fillStyle = 'rgba(0,0,0,.35)';
    c.fillRect(r.x + r.w - 5, r.y, 5, r.h);
  }

  drawDoor(c) {
    c.fillStyle = 'rgba(242,193,78,.25)';
    c.fillRect(DOOR.x, DOOR.y, DOOR.w, DOOR.h);
    c.strokeStyle = 'rgba(242,193,78,.7)';
    c.strokeRect(DOOR.x + 0.5, DOOR.y + 0.5, DOOR.w - 1, DOOR.h - 1);
  }

  // a pixel figure: the 16x24 walk sprite from the map, scaled up with
  // nearest-neighbour so the blocks stay square, plus a dagger when striking
  chibi(c, x, y, robe, trim, role, swinging) {
    const slug = role === 'qinwang' ? 'qinwang' : (role === 'jingke' ? 'jingke' : 'guard');
    const img = this.sprites[slug];
    const W = 16, H = 24, scale = 2.2;
    c.save();
    c.translate(x, y);
    c.fillStyle = 'rgba(0,0,0,.4)';
    c.beginPath();
    c.ellipse(0, 4, 11, 3.6, 0, 0, Math.PI * 2);
    c.fill();
    c.imageSmoothingEnabled = false;
    if (img && img.complete && img.naturalWidth) {
      // frame 0 of the sheet is the front-facing idle pose
      c.drawImage(img, 0, 0, W, H, -(W * scale) / 2, -H * scale + 4, W * scale, H * scale);
    } else {
      c.fillStyle = robe;
      c.fillRect(-7, -20, 14, 20);
      c.fillStyle = trim;
      c.fillRect(-7, -6, 14, 3);
    }
    c.imageSmoothingEnabled = true;
    if (role === 'jingke') {
      c.strokeStyle = swinging ? '#fff4e0' : '#cfd6df';
      c.lineWidth = swinging ? 3 : 2;
      c.beginPath();
      c.moveTo(8, -14);
      c.lineTo(swinging ? 30 : 22, swinging ? -26 : -17);
      c.stroke();
      if (swinging) {
        c.strokeStyle = 'rgba(255,244,224,.5)';
        c.lineWidth = 2;
        c.beginPath();
        c.arc(8, -14, 24, -1.2, 0.2);
        c.stroke();
      }
    }
    c.restore();
  }

  drawHud(c) {
    c.font = '12px "Microsoft YaHei", sans-serif';
    c.fillStyle = '#d9cfbd';
    c.fillText(this.role === 'jingke' ? '荆轲' : '秦王政', 12, 22);
    c.fillStyle = '#8a7a66';
    c.fillText(`时间 ${Math.max(0, this.timeLeft).toFixed(0)}s`, 12, 40);
    // three marks: the king's wounds (as 荆轲) or yours (as 秦王)
    for (let i = 0; i < 3; i++) {
      c.fillStyle = i < this.hits ? '#a8352a' : 'rgba(217,207,189,.25)';
      c.beginPath();
      c.arc(BATTLE_W - 26 - i * 16, 22, 5, 0, Math.PI * 2);
      c.fill();
    }
    c.fillStyle = '#6b6157';
    c.fillText(this.role === 'jingke' ? '命中' : '受伤', BATTLE_W - 84, 40);
  }
}
