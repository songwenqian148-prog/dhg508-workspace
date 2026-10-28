/*
 * Maps are built in code rather than typed by hand, so every row is exactly as
 * wide as the map and a walkable tile can be placed by coordinate.
 *
 * Legend: . dirt  , dirt_alt  s stone  g grass  w water  r reed  t tree
 *         # wood_wall  ~ roof  = wood_floor  | lattice  B banner_yan
 *         P palace_floor  W palace_wall  I pillar  C curtain  Q banner_qin
 *         H torch  T table  m mat  j wineskin  z zhu  S scroll  x blood
 */

function sheet(cols, rows, fill) {
  const g = Array.from({ length: rows }, () => Array(cols).fill(fill));
  const api = {
    rect(x0, y0, x1, y1, ch) {
      for (let y = y0; y <= y1; y++) {
        for (let x = x0; x <= x1; x++) if (g[y] && g[y][x] !== undefined) g[y][x] = ch;
      }
      return api;
    },
    put(x, y, ch) {
      if (g[y] && g[y][x] !== undefined) g[y][x] = ch;
      return api;
    },
    scatter(points, ch) {
      for (const [x, y] of points) api.put(x, y, ch);
      return api;
    },
    paint(rows) {
      return { legend: LEGEND, rows: g.map((r) => r.join('')) };
    },
    raw: g,
  };
  return api;
}

export const LEGEND = {
  '.': 'dirt', ',': 'dirt_alt', s: 'stone', g: 'grass', w: 'water', r: 'reed',
  t: 'tree', '#': 'wood_wall', '~': 'roof', '=': 'wood_floor', '|': 'lattice',
  B: 'banner_yan', P: 'palace_floor', W: 'palace_wall', I: 'pillar',
  C: 'curtain', Q: 'banner_qin', H: 'torch', T: 'table', m: 'mat',
  j: 'wineskin', z: 'zhu', S: 'scroll', x: 'blood', o: 'void', d: 'doorway',
  n: 'sand', b: 'water_bank', v: 'snow', k: 'stairs',
};

// ------------------------------------------------------------------ 燕市
// A market street in Ji, the Yan capital: roofs and shopfronts to the north,
// the river with reeds to the south. Jing Ke drinks here with the butcher and
// with Gao Jianli.
const yanMarket = sheet(32, 18, '.')
  .rect(0, 0, 31, 1, 'o')
  .rect(1, 1, 30, 1, '~')
  .rect(1, 2, 30, 3, '#')
  .scatter([[3, 2], [3, 3], [9, 2], [9, 3], [16, 2], [16, 3], [23, 2], [23, 3], [29, 2], [29, 3]], '|')
  .rect(1, 4, 30, 4, 's')
  .rect(0, 5, 31, 13, '.')
  .rect(2, 9, 5, 10, '=')           // the wine shop's open floor
  .put(2, 8, 'j').put(5, 8, 'j')
  .put(6, 6, 'T').put(7, 6, 'T')     // the butcher's trestle
  .put(12, 7, 'z')                   // Gao Jianli's zhu
  .put(3, 11, 'm')
  .scatter([[8, 6], [9, 7], [10, 5], [14, 6], [15, 9], [18, 7]], ',')
  .rect(0, 14, 31, 14, 'g')
  .scatter([[0, 14], [4, 14], [8, 14], [12, 14], [17, 14], [21, 14], [25, 14], [30, 14]], 'r')
  .rect(0, 15, 31, 15, 'b')
  .rect(0, 16, 31, 17, 'w')
  .scatter([[1, 12], [30, 12], [1, 6], [30, 6]], 't')
  .put(29, 8, 'B');

// ------------------------------------------------------------------ 太子宫
// Crown Prince Dan's hall: mats on the floor, a curtain behind the seat, the
// four pillars of a Warring-States hall.
const taiziGong = sheet(26, 15, 'P')
  .rect(0, 0, 25, 0, 'W')
  .rect(0, 14, 25, 14, 'W')
  .rect(0, 0, 0, 14, 'W')
  .rect(25, 0, 25, 14, 'W')
  .rect(2, 1, 23, 1, 'C')
  .scatter([[4, 5], [12, 5], [20, 5]], 'I')
  .scatter([[4, 9], [20, 9]], 'H')
  .rect(10, 2, 15, 2, 'm')
  .rect(11, 3, 14, 3, 'm')
  .put(12, 1, 'T')
  .rect(12, 4, 13, 13, 's')            // aisle from the door up to the prince's mat
  .rect(9, 10, 16, 12, 'm')
  .put(1, 7, 'B').put(24, 7, 'Q');

// ------------------------------------------------------------------ 舍人馆
// The house where the Qin general Fan Yuqi is kept after he flees to Yan.
const fanyuqiRoom = sheet(20, 13, '=')
  .rect(0, 0, 19, 0, '#')
  .rect(0, 12, 19, 12, '#')
  .rect(0, 0, 0, 12, '#')
  .rect(19, 0, 19, 12, '#')
  .rect(1, 1, 18, 1, '|')
  .put(2, 3, 'H')
  .rect(4, 3, 6, 5, 'm')
  .put(13, 4, 'T')
  .put(14, 4, 'S')
  .scatter([[8, 7], [9, 8], [10, 7]], ',');

// ------------------------------------------------------------------ 易水
// The Yi river: a road along the north bank, reeds, cold water to the south.
const yiRiver = sheet(34, 16, 'n')
  .rect(0, 0, 33, 1, 'g')
  .rect(0, 2, 33, 4, 'n')
  .rect(0, 5, 33, 7, 'g')
  .scatter([[2, 5], [6, 7], [11, 5], [15, 7], [20, 5], [24, 7], [28, 5], [32, 7]], 'r')
  .scatter([[1, 2], [7, 2], [30, 2]], 't')
  .rect(0, 8, 33, 8, 'b')
  .rect(0, 9, 33, 15, 'w')
  .put(4, 4, 'T')                    // the chariot, standing in
  .put(5, 4, 'T');

// ------------------------------------------------------------------ 咸阳宫
// The Qin palace hall: black lacquer, red pillars, the long sword, the map.
const xianyangHall = sheet(30, 18, 'P')
  .rect(0, 0, 29, 0, 'W')
  .rect(0, 17, 29, 17, 'W')
  .rect(0, 0, 0, 17, 'W')
  .rect(29, 0, 29, 17, 'W')
  .rect(1, 1, 28, 1, 'C')
  .scatter([[3, 3], [3, 9], [10, 3], [10, 9], [18, 3], [18, 9], [25, 3], [25, 9]], 'I')
  .scatter([[6, 2], [14, 2], [22, 2]], 'H')
  .rect(12, 2, 17, 3, 'm')
  .put(13, 1, 'T')
  .rect(13, 4, 15, 16, 's')            // the stone aisle from the door to the dais
  .scatter([[1, 8], [28, 8]], 'Q')
  .scatter([[7, 12], [21, 12]], 'H')
  .rect(1, 15, 28, 15, 's');

export const MAPS = {
  yan_market: yanMarket.paint(),
  taizi_gong: taiziGong.paint(),
  fanyuqi_room: fanyuqiRoom.paint(),
  yi_river: yiRiver.paint(),
  xianyang_hall: xianyangHall.paint(),
};
