#!/usr/bin/env python3
"""Build every pixel asset for the Week 8 *荆轲刺秦王* simulation.

Run from ``week-08``::

    python code/make_pixel_assets.py            # write the real assets
    python code/make_pixel_assets.py --check    # ...and 8x previews in artifacts/check/

Outputs (paths are fixed; the game engine reads them directly):

    game/assets/tiles/tiles.png       128x80  (8x5 grid of 16x16 tiles)
    game/assets/tiles/tiles.json      name -> tile index, 40 entries
    game/assets/sprites/<name>.png    128x24  (8 frames of 16x24, transparent)
    game/assets/portraits/<name>.png  48x48   (bust, transparent)
    game/assets/ui/pointer.png        8x8     (bone arrow, transparent)

Everything is drawn from code with Pillow only: no fonts, no text rendering,
no network, no source images, and no randomness.  Ground tiles are built from
value noise on a 16x16 torus and from features that wrap, so neighbouring
copies join without a seam.

The art direction is intentionally plain: one-pixel ink outlines, two or three
colours per garment, flat bands instead of dithering.  At 16x24 a figure is
about 10 px wide with a 7 px head; the silhouette carries the character and
the gear (crown, staff, halberd, zither) carries the identity.

Usage flags: ``--only tiles|sprites|portraits|ui`` and ``--no-verify``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import TRANSPARENT, colour, darken, lighten, mix  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TILES_PNG = ROOT / "game" / "assets" / "tiles" / "tiles.png"
TILES_JSON = ROOT / "game" / "assets" / "tiles" / "tiles.json"
SPRITE_DIR = ROOT / "game" / "assets" / "sprites"
PORTRAIT_DIR = ROOT / "game" / "assets" / "portraits"
UI_DIR = ROOT / "game" / "assets" / "ui"
CHECK_DIR = ROOT / "artifacts" / "check"

TILE = 16
COLS = 8
ROWS = 5


# ---------------------------------------------------------------------------
# A very small pixel canvas
# ---------------------------------------------------------------------------

RGBA = tuple[int, int, int, int]


class Canvas:
    """A tiny drawing surface with pixel-exact, bounds-checked primitives."""

    __slots__ = ("w", "h", "img", "px")

    def __init__(self, w: int, h: int, fill: str | RGBA | None = None) -> None:
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), TRANSPARENT if fill is None else colour(fill))
        self.px = self.img.load()

    # -- single pixels ----------------------------------------------------
    def set(self, x: int, y: int, c: str | RGBA, wrap: bool = False) -> None:
        """Paint one pixel.  ``wrap`` makes coordinates periodic (for tiling)."""
        if wrap:
            x %= self.w
            y %= self.h
        elif not (0 <= x < self.w and 0 <= y < self.h):
            return
        self.px[x, y] = colour(c)

    def get(self, x: int, y: int) -> RGBA:
        return self.px[x % self.w, y % self.h]

    def clear_px(self, x: int, y: int) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = TRANSPARENT

    # -- spans ------------------------------------------------------------
    def hline(self, x0: int, x1: int, y: int, c: str | RGBA, wrap: bool = False) -> None:
        if x1 < x0:
            x0, x1 = x1, x0
        for x in range(x0, x1 + 1):
            self.set(x, y, c, wrap)

    def vline(self, x: int, y0: int, y1: int, c: str | RGBA, wrap: bool = False) -> None:
        if y1 < y0:
            y0, y1 = y1, y0
        for y in range(y0, y1 + 1):
            self.set(x, y, c, wrap)

    def rect(
        self, x0: int, y0: int, x1: int, y1: int, c: str | RGBA, wrap: bool = False
    ) -> None:
        """Filled rectangle, inclusive on both corners."""
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c, wrap)

    def line(self, x0: int, y0: int, x1: int, y1: int, c: str | RGBA) -> None:
        """Bresenham line, 1 px wide."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            err2 = 2 * err
            if err2 >= dy:
                err += dy
                x0 += sx
            if err2 <= dx:
                err += dx
                y0 += sy

    # -- shape helpers ----------------------------------------------------
    def outline(self, c: str | RGBA, diagonal: bool = False) -> None:
        """Put a 1 px border just outside every opaque pixel (silhouette ink)."""
        pixels = self.img.load()
        opaque = [
            (x, y)
            for y in range(self.h)
            for x in range(self.w)
            if pixels[x, y][3] > 0
        ]
        neighbours = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if diagonal:
            neighbours += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        target = colour(c)
        for x, y in opaque:
            for dx, dy in neighbours:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h and pixels[nx, ny][3] == 0:
                    pixels[nx, ny] = target

    def flip_h(self) -> "Canvas":
        other = Canvas(self.w, self.h)
        other.img = self.img.transpose(Image.FLIP_LEFT_RIGHT)
        other.px = other.img.load()
        return other

    def paste(self, other: "Canvas", ox: int, oy: int) -> None:
        """Alpha-composite ``other`` onto this canvas at (ox, oy)."""
        self.img.alpha_composite(other.img, (ox, oy))
        self.px = self.img.load()

    def upscale(self, factor: int) -> Image.Image:
        return self.img.resize((self.w * factor, self.h * factor), Image.NEAREST)


# ---------------------------------------------------------------------------
# Deterministic noise on a 16x16 torus
# ---------------------------------------------------------------------------


def _hash01(x: int, y: int, seed: int) -> float:
    """Deterministic hash -> float in [0, 1).  No ``random`` module involved."""
    n = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
    n &= 0xFFFFFFFF
    n ^= n >> 13
    n = (n * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 65536.0


def _smoothstep(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def noise16(x: int, y: int, cells: int, seed: int) -> float:
    """Value noise on a ``cells x cells`` lattice that wraps every 16 px."""
    step = TILE / cells
    fx, fy = x / step, y / step
    x0, y0 = int(fx), int(fy)
    tx, ty = _smoothstep(fx - x0), _smoothstep(fy - y0)
    x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
    x0, y0 = x0 % cells, y0 % cells
    v00 = _hash01(x0, y0, seed)
    v10 = _hash01(x1, y0, seed)
    v01 = _hash01(x0, y1, seed)
    v11 = _hash01(x1, y1, seed)
    top = v00 + (v10 - v00) * tx
    bottom = v01 + (v11 - v01) * tx
    return top + (bottom - top) * ty


def field16(seed: int) -> list[list[float]]:
    """Two octaves of wrapping noise, one value per tile pixel."""
    out: list[list[float]] = []
    for y in range(TILE):
        row = []
        for x in range(TILE):
            v = 0.62 * noise16(x, y, 4, seed) + 0.38 * noise16(x, y, 8, seed + 101)
            row.append(v)
        out.append(row)
    return out


def pick(i: int, salt: int, seed: int, mod: int = TILE) -> int:
    """Deterministic coordinate helper (``i`` indexes the instance)."""
    return int(_hash01(i, salt, seed) * mod) % mod


def ground(
    c: Canvas,
    seed: int,
    dark: str | RGBA,
    base: str | RGBA,
    light: str | RGBA,
    lo: float = 0.42,
    hi: float = 0.68,
    speckle: bool = True,
) -> None:
    """Fill a tile with flat bands of wrapping noise: the shared ground recipe."""
    values = field16(seed)
    for y in range(TILE):
        row = values[y]
        for x in range(TILE):
            v = row[x]
            if v < lo:
                tone = dark
            elif v > hi:
                tone = light
            else:
                tone = base
            if speckle:
                h = _hash01(x, y, seed + 9001)
                if h > 0.972:
                    tone = light
                elif h < 0.028:
                    tone = dark
            c.set(x, y, tone)


def backdrop(c: Canvas, seed: int, base: str | RGBA = "ash") -> None:
    """Quiet dark ground used behind free-standing objects."""
    dark = darken(base, 0.38)
    ground(c, seed, dark, base, lighten(base, 0.10), lo=0.38, hi=0.72)


def wrap_blob(c: Canvas, cx: int, cy: int, rx: int, ry: int, col: str | RGBA) -> None:
    """Filled ellipse that wraps at the tile edges (so it stays seamless)."""
    for y in range(-ry, ry + 1):
        for x in range(-rx, rx + 1):
            if (x * x) / (rx * rx + 0.01) + (y * y) / (ry * ry + 0.01) <= 1.0:
                c.set(cx + x, cy + y, col, wrap=True)


# ---------------------------------------------------------------------------
# Tiles
#
# Ground tiles (dirt, grass, sand, water, ...) are seamless: their noise comes
# from the 16x16 torus above and every hand-placed mark wraps.  Object tiles
# (table, torch, banner, ...) sit on a quiet interior ground and only have to
# be opaque.
# ---------------------------------------------------------------------------


def grass_ground(c: Canvas, seed: int, base: str | RGBA | None = None) -> None:
    """The shared meadow ground, reused by grass, tree and grass_alt."""
    if base is None:
        base = mix("jade", "ink", 0.12)
    ground(c, seed, darken(base, 0.36), base, mix(base, "bone", 0.20), lo=0.40, hi=0.70)


def t_dirt(c: Canvas) -> None:
    base = "earth"
    ground(c, 1001, darken(base, 0.42), base, lighten(base, 0.22))
    for i in range(7):
        x, y = pick(i, 3, 1001), pick(i, 4, 1001)
        c.set(x, y, mix("earth", "bone", 0.32))
        if i % 2 == 0:
            c.set((x + 1) % 16, y, darken(base, 0.48))
        if i % 3 == 0:
            c.set(x, (y + 1) % 16, darken(base, 0.42))


def t_dirt_alt(c: Canvas) -> None:
    base = mix("earth", "clay", 0.45)
    ground(c, 1101, darken(base, 0.44), base, lighten(base, 0.18))
    # a dry cart rut and a scatter of small stones
    for y in range(16):
        c.set(6, y, darken(base, 0.30))
        if (y // 3) % 2 == 0:
            c.set(7, y, lighten(base, 0.16))
    for i in range(6):
        x, y = pick(i, 8, 1101), pick(i, 9, 1101)
        if x in (6, 7):
            continue
        c.set(x, y, mix("slate", "bone", 0.35))
        c.set(x, (y + 1) % 16, darken(base, 0.50))


def t_stone(c: Canvas) -> None:
    base = mix("slate", "ash", 0.28)
    grout = darken(base, 0.62)
    c.rect(0, 0, 15, 15, grout)
    for row in range(4):
        offset = 2 if row % 2 else 0
        for col in range(4):
            x0 = (col * 4 + offset) % 16
            tone = mix(base, "bone" if (col + 2 * row) % 3 == 0 else "ink", 0.12)
            if (col + row) % 2:
                tone = darken(tone, 0.12)
            for yy in range(row * 4 + 1, row * 4 + 4):
                for xx in range(x0, x0 + 3):
                    c.set(xx % 16, yy, tone)
            c.set(x0, row * 4 + 1, lighten(tone, 0.20))
            c.set((x0 + 1) % 16, row * 4 + 1, lighten(tone, 0.08))
            c.set((x0 + 2) % 16, row * 4 + 3, darken(tone, 0.22))


def t_grass(c: Canvas) -> None:
    base = mix("jade", "ink", 0.12)
    grass_ground(c, 1301, base)
    blades = (mix(base, "bone", 0.16), darken(base, 0.42), mix(base, "bone", 0.08))
    for i in range(10):
        x, y = pick(i, 7, 1301), pick(i, 8, 1301)
        height = 2 + pick(i, 9, 1301, 2)
        tone = blades[i % 3]
        for k in range(height):
            c.set(x, y - k, tone, wrap=True)


def t_sand(c: Canvas) -> None:
    base = mix("clay", "bone", 0.55)
    dark = mix(base, "earth", 0.32)
    light = mix(base, "silk", 0.45)
    ground(c, 1401, dark, base, light, lo=0.40, hi=0.70, speckle=False)
    # wind ripples: dashes on fixed rows, offset a little each row
    for row in range(4):
        y = row * 4
        offset = (row * 7) % 16
        length = 5 if row % 2 == 0 else 4
        for k in range(length):
            c.set(offset + k, y, light, wrap=True)
        for k in range(max(1, length - 2)):
            c.set(offset + k, y + 1, dark, wrap=True)


def t_water(c: Canvas) -> None:
    base: RGBA = colour("dark_water")
    ground(c, 1501, darken(base, 0.30), base, mix(base, "water", 0.75), lo=0.36, hi=0.58, speckle=False)
    crest = mix("water", "bone", 0.35)
    trough = darken(base, 0.35)
    waves = ((2, 3, 5), (10, 3, 4), (5, 8, 6), (0, 13, 4), (9, 13, 5), (13, 6, 2))
    for x0, y, n in waves:
        for k in range(n):
            c.set(x0 + k, y, crest, wrap=True)
        for k in range(max(1, n - 1)):
            c.set(x0 + 1 + k, y + 1, trough, wrap=True)


def t_water_bank(c: Canvas) -> None:
    base = mix("water", "clay", 0.34)
    sand = mix("clay", "bone", 0.48)
    ground(c, 1601, darken(base, 0.28), base, mix(base, "water", 0.6), lo=0.34, hi=0.58, speckle=False)
    patches = field16(1602)
    for y in range(16):
        for x in range(16):
            v = patches[y][x]
            if v > 0.64:
                c.set(x, y, sand if v > 0.73 else mix(sand, base, 0.40))
    for x0, y, n in ((2, 5, 4), (9, 9, 3), (7, 12, 4), (12, 2, 3)):
        for k in range(n):
            c.set(x0 + k, y, mix("water", "bone", 0.28), wrap=True)


def t_snow(c: Canvas) -> None:
    base = "snow"
    ground(c, 1701, mix(base, "water", 0.24), base, "silk", lo=0.40, hi=0.72, speckle=False)
    # wind-packed streaks and a few cold blue hollows
    for i in range(8):
        x, y = pick(i, 3, 1701), pick(i, 4, 1701)
        c.set(x, y, mix(base, "slate", 0.20))
        if i % 2:
            c.set(x + 1, y + 1, mix(base, "water", 0.22), wrap=True)
    for i in range(6):
        c.set(pick(i, 5, 1702), pick(i, 6, 1702), mix(base, "water", 0.32))


def t_wood_wall(c: Canvas) -> None:
    planks = (
        mix("earth", "clay", 0.30),
        mix("earth", "ink", 0.18),
        mix("earth", "clay", 0.05),
        mix("earth", "clay", 0.50),
    )
    for x in range(16):
        body = planks[x // 4]
        if x % 4 == 0:
            tone = darken(body, 0.58)
        elif x % 4 == 1:
            tone = lighten(body, 0.14)
        elif x % 4 == 3:
            tone = darken(body, 0.16)
        else:
            tone = body
        c.vline(x, 0, 15, tone)
    for i in range(16):
        x, y = pick(i, 21, 1801), pick(i, 22, 1801)
        if x % 4 == 0:
            continue
        body = planks[x // 4]
        c.set(x, y, darken(body, 0.30))
        if i % 3 == 0:
            c.set(x, y + 1, darken(body, 0.20), wrap=True)


def t_wood_floor(c: Canvas) -> None:
    planks = (
        mix("earth", "clay", 0.42),
        mix("earth", "clay", 0.62),
        mix("earth", "clay", 0.22),
        mix("earth", "ink", 0.10),
    )
    for y in range(16):
        body = planks[y // 4]
        if y % 4 == 0:
            tone = darken(body, 0.55)
        elif y % 4 == 1:
            tone = lighten(body, 0.13)
        elif y % 4 == 3:
            tone = darken(body, 0.14)
        else:
            tone = body
        c.hline(0, 15, y, tone)
    # staggered butt joints
    for p in range(4):
        joint = (p * 7 + 3) % 16
        for y in range(p * 4 + 1, p * 4 + 4):
            c.set(joint, y, darken(planks[p], 0.42))
    for i in range(10):
        x, y = pick(i, 31, 1901), pick(i, 32, 1901)
        if y % 4 == 0:
            continue
        c.set(x, y, darken(planks[y // 4], 0.26))


def t_roof(c: Canvas) -> None:
    """Rows of half-round roof tiles, seen from above."""
    base = mix("slate", "ash", 0.34)
    dark = darken(base, 0.52)
    light = mix(base, "bone", 0.26)
    c.rect(0, 0, 15, 15, base)
    for course in range(2):
        y0 = course * 8
        for rib in range(4):
            x0 = rib * 4
            body = base if (rib + course) % 2 == 0 else darken(base, 0.12)
            for yy in range(y0 + 2, y0 + 8):
                for xx in range(x0, x0 + 4):
                    c.set(xx % 16, yy % 16, body)
            # the round cap of each tile sits proud of the course below
            for yy in (y0, y0 + 1):
                for xx in (x0 + 1, x0 + 2):
                    c.set(xx % 16, yy % 16, lighten(body, 0.22))
            c.set(x0 % 16, y0 + 2, dark)
            c.set((x0 + 3) % 16, y0 + 2, dark)
            c.set(x0 % 16, y0 + 7, darken(body, 0.32))
            c.set((x0 + 3) % 16, y0 + 7, dark)
    for y in (2, 10):
        c.hline(0, 15, y, darken(base, 0.38))


def t_palace_floor(c: Canvas) -> None:
    """Black polished flags with faint red seams -- Qin court."""
    base = mix("ash", "slate", 0.30)
    grout = mix("ink", "cinnabar", 0.16)
    values = field16(2001)
    for y in range(16):
        for x in range(16):
            v = values[y][x]
            tone = darken(base, 0.22) if v < 0.40 else (lighten(base, 0.12) if v > 0.72 else base)
            c.set(x, y, tone)
    for i in (0, 8):
        c.vline(i, 0, 15, grout)
        c.hline(0, 15, i, grout)
    for sy in (0, 8):
        for sx in (0, 8):
            c.set((sx + 1) % 16, (sy + 1) % 16, lighten(base, 0.30))
            c.set((sx + 2) % 16, (sy + 1) % 16, lighten(base, 0.18))
            c.set((sx + 1) % 16, (sy + 2) % 16, lighten(base, 0.14))
            c.set((sx + 5) % 16, (sy + 4) % 16, darken(base, 0.30))


def t_palace_wall(c: Canvas) -> None:
    """Black plaster panels divided by cinnabar pilasters."""
    base = mix("ash", "ink", 0.42)
    ground(c, 2101, darken(base, 0.30), base, lighten(base, 0.10), lo=0.38, hi=0.74)
    stripe = mix("cinnabar", "ink", 0.40)
    c.vline(0, 0, 15, stripe)
    c.vline(1, 0, 15, mix("cinnabar", "ink", 0.20))
    c.vline(2, 0, 15, mix("ink", "cinnabar", 0.10))
    c.vline(3, 0, 15, darken(base, 0.35))
    c.vline(15, 0, 15, darken(stripe, 0.25))
    # a little wear at the foot of the wall
    for i in range(5):
        x = 4 + pick(i, 3, 2101, 11)
        c.set(x, 14 + pick(i, 4, 2101, 2), mix(base, "bone", 0.08))


def t_pillar(c: Canvas) -> None:
    """A lacquered red-brown column against dark interior shadow."""
    backdrop(c, 2201, mix("ash", "ink", 0.45))
    body = mix("blood", "earth", 0.38)
    light = mix(body, "bone", 0.26)
    dark = darken(body, 0.40)
    c.vline(3, 0, 15, darken(body, 0.62))
    c.vline(4, 0, 15, dark)
    for x in range(5, 11):
        c.vline(x, 0, 15, body)
    c.vline(6, 0, 15, light)
    c.vline(7, 0, 15, mix(body, "bone", 0.10))
    c.vline(10, 0, 15, dark)
    c.vline(11, 0, 15, darken(body, 0.58))
    for i in range(9):
        x = 5 + pick(i, 31, 2201, 6)
        y = pick(i, 32, 2201)
        c.set(x, y, darken(body, 0.30))
        if i % 2:
            c.set(x, y + 1, darken(body, 0.20), wrap=True)


def t_curtain(c: Canvas) -> None:
    """Hanging cloth; only vertical folds, so it tiles in both directions."""
    base: RGBA = colour("indigo")
    folds = (darken(base, 0.40), darken(base, 0.12), lighten(base, 0.12), darken(base, 0.26))
    for x in range(16):
        c.vline(x, 0, 15, folds[x % 4])
    for x in (2, 10):
        c.vline(x, 0, 15, mix("gold", base, 0.62))


def t_curtain_qin(c: Canvas) -> None:
    """Qin black cloth with cinnabar folds."""
    base = mix("ink", "ash", 0.55)
    folds = (darken(base, 0.45), base, mix(base, "cinnabar", 0.35), darken(base, 0.25))
    for x in range(16):
        c.vline(x, 0, 15, folds[x % 4])
    for x in (2, 10):
        c.vline(x, 0, 15, mix("cinnabar", "gold", 0.30))


def t_lattice(c: Canvas) -> None:
    """A dark lattice window: two-pixel frame, four panes."""
    c.rect(0, 0, 15, 15, mix("ink", "indigo", 0.35))
    wood = mix("clay", "bronze", 0.30)
    dark = darken(wood, 0.55)
    light = lighten(wood, 0.22)
    # outer frame
    c.rect(0, 0, 15, 1, wood)
    c.rect(0, 14, 15, 15, wood)
    c.rect(0, 0, 1, 15, wood)
    c.rect(14, 0, 15, 15, wood)
    # cross bars
    c.rect(7, 2, 8, 13, wood)
    c.rect(2, 7, 13, 8, wood)
    # lit edges and shadow lines around the bars
    for x0, y0, x1, y1 in ((0, 0, 15, 1), (0, 14, 15, 15), (0, 0, 1, 15), (14, 0, 15, 15),
                           (7, 2, 8, 13), (2, 7, 13, 8)):
        c.hline(x0, x1, y0, dark)
        c.vline(x0, y0, y1, dark)
        c.set(x1, y1, dark)
    c.hline(1, 14, 2, light)
    c.vline(2, 1, 14, light)
    c.hline(9, 13, 9, light)
    c.vline(9, 9, 13, light)


def t_banner_yan(c: Canvas) -> None:
    """Yan standard: muted blue-green cloth, pale border, swallow mark."""
    cloth = mix("jade", "slate", 0.45)
    trim = mix("bone", cloth, 0.30)
    dark = darken(cloth, 0.35)
    c.rect(0, 0, 15, 15, cloth)
    for x in (0, 1, 14, 15):
        c.vline(x, 0, 15, trim)
    c.vline(2, 0, 15, dark)
    c.vline(13, 0, 15, dark)
    for i in range(4):
        x = 4 + i * 2
        c.vline(x, 0, 15, darken(cloth, 0.14) if i % 2 else cloth)
    # swallow: wing tips, body, tail
    mark = mix("silk", cloth, 0.15)
    for x, y in ((5, 5), (10, 5), (6, 6), (9, 6), (7, 7), (8, 7), (7, 8), (8, 8), (7, 9), (8, 9)):
        c.set(x, y, mark)
    for x, y in ((4, 6), (11, 6), (6, 8), (9, 8)):
        c.set(x, y, dark)


def t_banner_qin(c: Canvas) -> None:
    """Qin standard: black cloth, cinnabar border and seal."""
    cloth = mix("ink", "ash", 0.40)
    trim = "cinnabar"
    c.rect(0, 0, 15, 15, cloth)
    for x in (0, 1, 14, 15):
        c.vline(x, 0, 15, trim)
    c.vline(2, 0, 15, darken(trim, 0.45))
    c.vline(13, 0, 15, darken(trim, 0.45))
    for x in (4, 6, 9, 11):
        c.vline(x, 0, 15, darken(cloth, 0.35))
    # a square seal mark, hollow centre
    seal = mix("cinnabar", "bone", 0.10)
    for x in range(5, 11):
        c.set(x, 5, seal)
        c.set(x, 10, seal)
    for y in range(5, 11):
        c.set(5, y, seal)
        c.set(10, y, seal)
    c.set(7, 7, seal)
    c.set(8, 7, seal)
    c.set(7, 8, seal)
    c.set(8, 8, seal)


def t_torch(c: Canvas) -> None:
    """Wall torch: bronze bracket, cinnabar flame, bone core."""
    backdrop(c, 2601, mix("ash", "ink", 0.40))
    bracket = mix("bronze", "earth", 0.35)
    c.rect(7, 9, 8, 14, bracket)
    c.rect(6, 9, 9, 10, lighten(bracket, 0.20))
    c.rect(6, 14, 9, 15, darken(bracket, 0.35))
    c.set(7, 13, darken(bracket, 0.25))
    # flame outline then core
    shape = (
        (1, 7, 8),
        (2, 7, 8),
        (3, 6, 9),
        (4, 6, 9),
        (5, 5, 10),
        (6, 5, 10),
        (7, 6, 9),
        (8, 6, 9),
    )
    for y, x0, x1 in shape:
        c.hline(x0, x1, y, "cinnabar")
    inner = (
        (2, 7, 8),
        (3, 7, 8),
        (4, 7, 8),
        (5, 6, 9),
        (6, 6, 9),
        (7, 7, 8),
    )
    for y, x0, x1 in inner:
        c.hline(x0, x1, y, "gold")
    for y, x0, x1 in ((1, 7, 8), (3, 7, 8), (4, 7, 8), (5, 7, 8)):
        c.hline(x0, x1, y, mix("silk", "gold", 0.35))
    # soot / glow flecks
    for x, y in ((4, 3), (11, 4), (3, 7), (12, 7), (5, 1), (10, 1)):
        c.set(x, y, mix("ink", "cinnabar", 0.30))


def t_tree(c: Canvas) -> None:
    """A bare-ish tree: dark canopy over meadow ground."""
    base = mix("jade", "ink", 0.16)
    grass_ground(c, 2701, base)
    canopy = mix("jade", "ink", 0.42)
    dark = mix("jade", "ink", 0.72)
    lit = mix("jade", "bone", 0.22)
    rows = (
        (0, 5, 10),
        (1, 3, 12),
        (2, 2, 13),
        (3, 2, 13),
        (4, 2, 13),
        (5, 2, 13),
        (6, 3, 12),
        (7, 4, 11),
        (8, 6, 9),
    )
    for y, x0, x1 in rows:
        c.hline(x0, x1, y, canopy)
    # ink silhouette, kept to the outside
    for y, x0, x1 in ((0, 5, 10), (1, 3, 12), (2, 2, 13), (7, 4, 11), (8, 6, 9)):
        c.hline(x0, x1, y, dark)
    for y in range(2, 8):
        c.set(2, y, dark)
        c.set(13, y, dark)
    for x, y in ((4, 2), (5, 2), (9, 2), (10, 2), (3, 3), (12, 3)):
        c.set(x, y, dark)
    # light clumps on the upper left
    for x, y in ((4, 3), (5, 3), (4, 4), (3, 4), (6, 2), (7, 2), (5, 5), (6, 5)):
        c.set(x, y, lit)
    # trunk and roots
    trunk = darken("earth", 0.30)
    c.rect(7, 8, 8, 14, trunk)
    c.set(7, 8, lighten(trunk, 0.18))
    c.set(6, 15, trunk)
    c.set(9, 15, trunk)
    c.set(5, 15, darken(trunk, 0.25))
    c.set(10, 15, darken(trunk, 0.25))
    c.set(8, 15, darken(trunk, 0.30))


def t_reed(c: Canvas) -> None:
    """Reeds at the water's edge, on shallow water."""
    base = mix("water", "jade", 0.30)
    ground(c, 2801, darken(base, 0.26), base, mix(base, "water", 0.55), lo=0.34, hi=0.58, speckle=False)
    for y in (6, 11):
        c.hline(0, 15, y, mix(base, "bone", 0.18))
    stalks = ((2, 3, "clay"), (5, 6, "jade"), (8, 2, "clay"), (11, 5, "jade"), (13, 8, "clay"))
    for x, top, tint in stalks:
        stem = mix(tint, "bone", 0.45)
        c.vline(x, top, 15, stem)
        head = mix(tint, "bronze", 0.35)
        for yy in range(top - 2, top + 1):
            c.set(x, yy, head)
            if yy > top - 2:
                c.set(x + 1 if x < 15 else 0, yy, darken(head, 0.20))
        c.set(x + 1 if x < 15 else 0, top + 3, stem)
    # water glints
    for x0, y, n in ((1, 9, 3), (6, 13, 4), (9, 4, 3)):
        for k in range(n):
            c.set(x0 + k, y, mix(base, "bone", 0.30), wrap=True)


def t_table(c: Canvas) -> None:
    """A low 案: the mat-level table of a Warring States room."""
    backdrop(c, 2901, mix("ash", "ink", 0.35))
    top = mix("earth", "clay", 0.55)
    dark = darken(top, 0.55)
    light = lighten(top, 0.24)
    c.rect(1, 6, 14, 9, top)
    c.hline(1, 14, 6, light)
    c.hline(1, 14, 7, lighten(top, 0.10))
    c.hline(1, 14, 9, dark)
    c.vline(1, 6, 9, dark)
    c.vline(14, 6, 9, dark)
    for x in (2, 3, 12, 13):
        c.rect(x, 10, x, 13, top if x in (3, 12) else darken(top, 0.25))
    c.hline(2, 13, 14, mix("ink", "ash", 0.35))
    c.set(5, 8, darken(top, 0.18))
    c.set(10, 8, darken(top, 0.18))


def t_mat(c: Canvas) -> None:
    """A woven sitting mat (席), edge to edge so mats lie side by side."""
    base = mix("clay", "bone", 0.30)
    light = mix(base, "silk", 0.30)
    dark = darken(base, 0.38)
    for y in range(16):
        for x in range(16):
            if (x // 2 + y // 2) % 2 == 0:
                c.set(x, y, light if (x % 2 == 0) else mix(light, base, 0.45))
            else:
                c.set(x, y, base if (x % 2 == 0) else mix(base, dark, 0.35))
    c.rect(0, 0, 15, 0, dark)
    c.rect(0, 15, 15, 15, dark)
    c.rect(0, 0, 0, 15, dark)
    c.rect(15, 0, 15, 15, dark)
    c.rect(1, 1, 14, 1, light)
    c.rect(1, 1, 1, 14, light)
    for x, y in ((1, 1), (14, 1), (1, 14), (14, 14)):
        c.set(x, y, mix("gold", base, 0.40))


def t_wineskin(c: Canvas) -> None:
    """A leather wine skin, tied at the neck."""
    backdrop(c, 3001, mix("ash", "ink", 0.40))
    body = mix("earth", "clay", 0.30)
    dark = darken(body, 0.55)
    light = lighten(body, 0.18)
    rows = (
        (3, 7, 8),
        (4, 6, 9),
        (5, 5, 10),
        (6, 4, 11),
        (7, 4, 11),
        (8, 4, 11),
        (9, 4, 11),
        (10, 4, 11),
        (11, 5, 10),
        (12, 5, 10),
        (13, 6, 9),
        (14, 6, 9),
    )
    for y, x0, x1 in rows:
        c.hline(x0, x1, y, body)
    for y, x0, x1 in (rows[0], rows[3], rows[-1]):
        c.set(x0, y, dark)
        c.set(x1, y, dark)
    c.vline(4, 6, 13, dark)
    c.vline(11, 6, 13, dark)
    c.vline(5, 5, 12, light)
    c.set(5, 7, light)
    # tie
    c.hline(6, 9, 4, "bone")
    c.set(7, 3, mix("bone", "clay", 0.30))
    c.set(8, 3, mix("bone", "clay", 0.30))
    c.set(9, 5, dark)
    # a stitched seam
    for y in range(7, 13):
        if y % 2 == 0:
            c.set(8, y, darken(body, 0.30))


def t_zhu(c: Canvas) -> None:
    """A 筑: the long struck zither Gao Jianli plays."""
    backdrop(c, 3101, mix("ash", "ink", 0.42))
    body = mix("earth", "gold", 0.20)
    dark = darken(body, 0.55)
    light = lighten(body, 0.22)
    c.rect(2, 7, 13, 11, body)
    c.hline(2, 13, 6, darken(body, 0.25))
    c.hline(2, 13, 7, light)
    c.hline(2, 13, 11, dark)
    c.vline(2, 7, 11, dark)
    c.vline(13, 7, 11, dark)
    c.rect(12, 5, 13, 7, lighten(body, 0.12))
    # strings along the soundboard
    for y in (8, 9, 10):
        c.hline(3, 12, y, mix("silk", body, 0.30))
    c.set(4, 9, dark)
    # bridge
    c.rect(9, 8, 9, 10, mix("bronze", "bone", 0.30))
    # striker stick lying across
    c.line(4, 3, 8, 5, mix("clay", "bone", 0.35))
    c.set(3, 3, darken("clay", 0.20))


def t_scroll(c: Canvas) -> None:
    """A bundle of bamboo slips (简), tied with cord."""
    backdrop(c, 3201, mix("ash", "ink", 0.42))
    slip = mix("clay", "bone", 0.25)
    for i in range(10):
        x = 3 + i
        tone = slip if i % 2 == 0 else mix(slip, "earth", 0.35)
        c.vline(x, 3, 14, tone)
    for x in (3, 12):
        c.vline(x, 3, 14, darken(slip, 0.50))
    c.hline(3, 12, 3, darken(slip, 0.45))
    c.hline(3, 12, 14, darken(slip, 0.45))
    for y in (6, 11):
        c.hline(3, 12, y, mix("bronze", "ink", 0.45))
        c.set(3, y, "bone")
        c.set(12, y, "bone")
    # a couple of characters scratched on the slips, abstract marks only
    for x, y in ((5, 5), (6, 5), (5, 6), (8, 5), (9, 5), (9, 6), (6, 9), (5, 10), (7, 10)):
        c.set(x, y, mix("ink", "clay", 0.30))


def t_blood(c: Canvas) -> None:
    """Blood on dark stone: an irregular pool with spatter."""
    base = mix("slate", "ash", 0.45)
    ground(c, 3301, darken(base, 0.35), base, lighten(base, 0.12), lo=0.38, hi=0.72)
    pool = (
        (5, 6, 9),
        (4, 7, 11),
        (4, 8, 11),
        (5, 9, 10),
        (6, 10, 9),
    )
    for y, x0, x1 in pool:
        c.hline(x0, x1, y, "blood")
    for y, x0, x1 in ((4, 7, 11), (5, 6, 9), (6, 10, 9)):
        c.hline(x0, x1, y, "blood")
    for y, x0, x1 in ((4, 8, 10), (5, 7, 8), (8, 6, 9)):
        c.hline(x0, x1, y, darken("blood", 0.35))
    c.set(6, 7, mix("cinnabar", "blood", 0.30))
    c.set(7, 7, mix("cinnabar", "blood", 0.30))
    c.set(5, 8, mix("cinnabar", "blood", 0.15))
    # spatter, wrapped so the tile stays seamless
    for x, y in ((2, 4), (12, 3), (13, 9), (2, 11), (8, 2), (3, 13), (14, 6), (10, 12)):
        c.set(x, y, "blood", wrap=True)
    c.set(2, 5, darken("blood", 0.30), wrap=True)


def t_stairs(c: Canvas) -> None:
    """Steps seen head-on: four treads, each with a shadowed riser."""
    base = mix("slate", "ash", 0.40)
    tread = mix(base, "bone", 0.22)
    riser = darken(base, 0.55)
    for i in range(4):
        y0 = i * 4
        c.hline(0, 15, y0, tread)
        c.hline(0, 15, y0 + 1, mix(tread, "bone", 0.12))
        c.hline(0, 15, y0 + 2, base)
        c.hline(0, 15, y0 + 3, riser)
    # worn hollows in the treads
    for i in range(4):
        y = i * 4
        for x in (3, 4, 11, 12):
            c.set(x, y + 1, lighten(tread, 0.10))


def t_doorway(c: Canvas) -> None:
    """A dark doorway in a Qin wall: bronze frame, black opening."""
    backdrop(c, 3401, mix("ash", "ink", 0.42))
    c.rect(3, 3, 12, 15, "ink")
    c.rect(4, 4, 11, 15, mix("ink", "indigo", 0.22))
    c.hline(4, 11, 4, mix("ink", "indigo", 0.10))
    frame = mix("bronze", "earth", 0.35)
    dark = darken(frame, 0.50)
    c.hline(2, 13, 2, lighten(frame, 0.20))
    c.hline(2, 13, 3, frame)
    c.vline(2, 3, 15, frame)
    c.vline(13, 3, 15, frame)
    c.vline(3, 4, 15, dark)
    c.vline(12, 4, 15, dark)
    c.hline(2, 13, 15, mix("ink", "bronze", 0.30))
    c.set(2, 3, dark)
    c.set(13, 3, dark)


def t_void(c: Canvas) -> None:
    """Nothing: near-black with a whisper of texture, so it is not dead flat."""
    ground(c, 3501, "ink", mix("ink", "ash", 0.45), "ash", lo=0.30, hi=0.86, speckle=False)


def t_dirt_road(c: Canvas) -> None:
    """Packed road: two cart ruts running through dirt."""
    base = mix("earth", "clay", 0.25)
    ground(c, 3601, darken(base, 0.40), base, lighten(base, 0.20))
    for x in (3, 4, 11, 12):
        for y in range(16):
            tone = darken(base, 0.35) if x in (4, 11) else lighten(base, 0.16)
            c.set(x, y, tone)
    for y in range(0, 16, 4):
        c.set(4, y, darken(base, 0.55))
        c.set(11, (y + 2) % 16, darken(base, 0.55))


def t_grass_alt(c: Canvas) -> None:
    """Meadow with pale flowers and a couple of stones."""
    base = mix("jade", "ink", 0.06)
    grass_ground(c, 3701, base)
    for i in range(5):
        x, y = pick(i, 3, 3701), pick(i, 4, 3701)
        c.set(x, y, mix("silk", "jade", 0.15))
        c.set(x, y + 1, mix(base, "bone", 0.30), wrap=True)
    for i in range(3):
        x, y = pick(i, 5, 3702), pick(i, 6, 3702)
        c.rect(x, y, (x + 1) % 16, (y + 1) % 16, mix("slate", "bone", 0.30), wrap=True)
        c.set(x, (y + 1) % 16, darken(base, 0.45), wrap=True)


def t_water_deep(c: Canvas) -> None:
    """Deep water: darker, slower, fewer crests."""
    base = "ink"
    ground(c, 3801, darken(base, 0.20), mix("ink", "dark_water", 0.55), mix("dark_water", "water", 0.45), lo=0.34, hi=0.62, speckle=False)
    crest = mix("water", "bone", 0.30)
    for x0, y, n in ((3, 6, 5), (11, 12, 4)):
        for k in range(n):
            c.set(x0 + k, y, crest, wrap=True)
        c.set((x0 + 1) % 16, y + 1, mix("dark_water", "water", 0.35), wrap=True)


def t_snow_path(c: Canvas) -> None:
    """Snow with a trodden path down the middle."""
    base = "snow"
    ground(c, 3901, mix(base, "water", 0.20), base, "silk", lo=0.40, hi=0.72, speckle=False)
    packed = mix(base, "clay", 0.28)
    for y in range(16):
        off = 1 if (y // 4) % 2 else 0
        c.set(6 + off, y, packed)
        c.set(7 + off, y, mix(packed, "bone", 0.22))
        c.set(8 + off, y, packed)
    for y in (2, 6, 10, 14):
        c.set(7, y, mix(base, "water", 0.28))
        c.set(8, (y + 2) % 16, mix(base, "water", 0.20))


def t_wall_stone(c: Canvas) -> None:
    """A coursed stone wall, larger blocks than the floor cobbles."""
    base = mix("slate", "ash", 0.20)
    mortar = darken(base, 0.58)
    c.rect(0, 0, 15, 15, mortar)
    for row in range(2):
        offset = 4 if row % 2 else 0
        for col in range(2):
            x0 = (col * 8 + offset) % 16
            tone = mix(base, "bone" if (col + row) % 2 == 0 else "ink", 0.10)
            for yy in range(row * 8 + 1, row * 8 + 8):
                for xx in range(x0, x0 + 7):
                    c.set(xx % 16, yy, tone)
            c.hline(x0, (x0 + 6) % 16, row * 8 + 1, lighten(tone, 0.16))
            c.hline(x0, (x0 + 6) % 16, row * 8 + 7, darken(tone, 0.24))
    for i in range(6):
        x = pick(i, 3, 4001)
        y = pick(i, 4, 4001)
        c.set(x, y, lighten(base, 0.24))
        c.set(x, (y + 1) % 16, darken(base, 0.30))


def t_roof_ridge(c: Canvas) -> None:
    """The ridge of a roof: a raised band of caps over dark tiles."""
    base = mix("slate", "ash", 0.30)
    c.rect(0, 0, 15, 15, darken(base, 0.10))
    for x in range(16):
        if x % 4 == 0:
            c.vline(x, 0, 15, darken(base, 0.40))
        elif x % 4 == 2:
            c.vline(x, 0, 15, lighten(base, 0.10))
    band = mix("slate", "bone", 0.18)
    c.rect(0, 3, 15, 9, band)
    c.hline(0, 15, 3, lighten(band, 0.22))
    c.hline(0, 15, 9, darken(band, 0.45))
    for x in range(0, 16, 4):
        c.rect(x, 4, x + 1, 8, lighten(band, 0.12))
        c.vline((x + 3) % 16, 4, 8, darken(band, 0.30))
    c.hline(0, 15, 6, mix("bronze", band, 0.45))
    c.hline(0, 15, 7, mix("bronze", band, 0.25))


def t_wood_beam(c: Canvas) -> None:
    """A horizontal beam with bronze studs, seen from the side."""
    backdrop(c, 4101, mix("ash", "ink", 0.40))
    body = mix("earth", "clay", 0.35)
    dark = darken(body, 0.55)
    light = lighten(body, 0.20)
    c.rect(0, 4, 15, 11, body)
    c.hline(0, 15, 4, light)
    c.hline(0, 15, 5, lighten(body, 0.10))
    c.hline(0, 15, 10, darken(body, 0.28))
    c.hline(0, 15, 11, dark)
    for x in range(16):
        if x % 8 == 3:
            c.set(x, 6, mix("bronze", "bone", 0.25))
            c.set(x, 9, mix("bronze", "bone", 0.20))
    for i in range(8):
        x = pick(i, 3, 4101)
        c.set(x, 7 + pick(i, 4, 4101, 3), darken(body, 0.24))
    c.rect(0, 12, 15, 13, mix("ink", "ash", 0.30))


def t_lacquer_red(c: Canvas) -> None:
    """Qin red lacquer floor: cinnabar panels with black seams."""
    base = mix("cinnabar", "ink", 0.30)
    values = field16(4201)
    for y in range(16):
        for x in range(16):
            v = values[y][x]
            c.set(x, y, darken(base, 0.16) if v < 0.42 else (lighten(base, 0.14) if v > 0.74 else base))
    for i in (0, 8):
        c.vline(i, 0, 15, "ink")
        c.hline(0, 15, i, "ink")
    for sy in (0, 8):
        for sx in (0, 8):
            c.set((sx + 1) % 16, (sy + 1) % 16, mix("bone", base, 0.35))
            c.set((sx + 1) % 16, (sy + 2) % 16, mix("bone", base, 0.20))


def t_gravel(c: Canvas) -> None:
    """Courtyard gravel: dense small stones."""
    base = mix("slate", "ash", 0.35)
    ground(c, 4301, darken(base, 0.30), base, lighten(base, 0.14), lo=0.34, hi=0.68, speckle=False)
    for i in range(46):
        x, y = pick(i, 3, 4301), pick(i, 4, 4301)
        tone = mix(base, "bone", 0.22) if i % 3 else mix(base, "ink", 0.35)
        c.set(x, y, tone)
        if i % 4 == 0:
            c.set(x + 1, y, mix(base, "bone", 0.12), wrap=True)
        if i % 5 == 0:
            c.set(x, y + 1, darken(base, 0.30), wrap=True)


#: Sheet order -- index = row * 8 + col.  The first thirty are the names the
#: engine asks for; the rest fill the sheet with useful variants.
TILES: list[tuple[str, object]] = [
    ("dirt", t_dirt),
    ("dirt_alt", t_dirt_alt),
    ("stone", t_stone),
    ("grass", t_grass),
    ("sand", t_sand),
    ("water", t_water),
    ("water_bank", t_water_bank),
    ("snow", t_snow),
    ("wood_wall", t_wood_wall),
    ("wood_floor", t_wood_floor),
    ("roof", t_roof),
    ("palace_floor", t_palace_floor),
    ("palace_wall", t_palace_wall),
    ("pillar", t_pillar),
    ("curtain", t_curtain),
    ("lattice", t_lattice),
    ("banner_yan", t_banner_yan),
    ("banner_qin", t_banner_qin),
    ("torch", t_torch),
    ("tree", t_tree),
    ("reed", t_reed),
    ("table", t_table),
    ("mat", t_mat),
    ("wineskin", t_wineskin),
    ("zhu", t_zhu),
    ("scroll", t_scroll),
    ("blood", t_blood),
    ("stairs", t_stairs),
    ("doorway", t_doorway),
    ("void", t_void),
    ("dirt_road", t_dirt_road),
    ("grass_alt", t_grass_alt),
    ("water_deep", t_water_deep),
    ("snow_path", t_snow_path),
    ("wall_stone", t_wall_stone),
    ("roof_ridge", t_roof_ridge),
    ("wood_beam", t_wood_beam),
    ("curtain_qin", t_curtain_qin),
    ("lacquer_red", t_lacquer_red),
    ("gravel", t_gravel),
]

#: Names the engine contract requires; the build fails if one is missing.
REQUIRED_TILES = (
    "dirt", "dirt_alt", "stone", "grass", "sand", "water", "water_bank", "snow",
    "wood_wall", "wood_floor", "roof", "palace_floor", "palace_wall", "pillar",
    "curtain", "lattice", "banner_yan", "banner_qin", "torch", "tree", "reed",
    "table", "mat", "wineskin", "zhu", "scroll", "blood", "stairs", "doorway",
    "void",
)

#: Ground tiles whose seams are measured by the verifier.
SEAMLESS_TILES = (
    "dirt", "dirt_alt", "stone", "grass", "sand", "water", "water_bank", "snow",
    "wood_wall", "wood_floor", "roof", "palace_floor", "palace_wall", "tree",
    "reed", "void", "dirt_road", "grass_alt", "water_deep", "snow_path",
    "wall_stone", "roof_ridge", "lacquer_red", "gravel",
)


def build_tiles() -> Canvas:
    """Draw all forty tiles into one 128x80 sheet."""
    sheet = Canvas(COLS * TILE, ROWS * TILE)
    for index, (_name, painter) in enumerate(TILES):
        tile = Canvas(TILE, TILE, "ink")
        painter(tile)  # type: ignore[operator]
        sheet.paste(tile, (index % COLS) * TILE, (index // COLS) * TILE)
    return sheet


def tiles_json() -> dict:
    return {
        "tileSize": TILE,
        "columns": COLS,
        "rows": ROWS,
        "tiles": {name: index for index, (name, _fn) in enumerate(TILES)},
    }


# ---------------------------------------------------------------------------
# Sprites and portraits (filled in below)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Sprites: ten people from 227 BC, eight frames each
#
# One 16x24 cell per frame: down_idle, down_step, left_idle, left_step,
# right_idle, right_step, up_idle, up_step.  Feet sit on the bottom row.  The
# idle and step frames of a direction share everything above the waist; only
# the legs and the sleeve cuffs move, so the engine can swap them as a bob.
# ---------------------------------------------------------------------------

GEO: dict[str, dict] = {
    # head 7 wide (5 px face) over an 8-wide body
    "adult": dict(hx0=5, hx1=11, fx0=6, fx1=10, head_top=3, head_bot=8, neck=9,
                  sy=10, tx0=5, tx1=10, sl=(3, 4), sr=(11, 12),
                  sash=15, hem=20, leg=21, foot=23),
    # same, but with shoulder pads and heavier arms
    "broad": dict(hx0=5, hx1=11, fx0=6, fx1=10, head_top=3, head_bot=8, neck=9,
                  sy=10, tx0=4, tx1=11, sl=(2, 3), sr=(12, 13),
                  sash=15, hem=20, leg=21, foot=23),
    # one row lower torso so the flat crown has room above the head
    "tall": dict(hx0=5, hx1=11, fx0=6, fx1=10, head_top=4, head_bot=9, neck=10,
                 sy=11, tx0=5, tx1=10, sl=(3, 4), sr=(11, 12),
                 sash=16, hem=20, leg=21, foot=23),
    # a boy: shorter body, chin on the shoulders, no neck row
    "small": dict(hx0=5, hx1=11, fx0=6, fx1=10, head_top=5, head_bot=10, neck=None,
                  sy=11, tx0=6, tx1=9, sl=(4, 5), sr=(10, 11),
                  sash=16, hem=20, leg=21, foot=23),
    # head sunk into the shoulders
    "hunched": dict(hx0=5, hx1=11, fx0=6, fx1=10, head_top=4, head_bot=9, neck=None,
                    sy=10, tx0=5, tx1=10, sl=(3, 4), sr=(11, 12),
                    sash=15, hem=20, leg=21, foot=23),
}

#: Profile x-ranges (the side frames are drawn facing left and mirrored).
SIDE_GEO: dict[str, dict] = {
    "adult": dict(hx0=4, hx1=10, face0=5, face1=9, torso=(6, 10), arm=(4, 6),
                  skirt=(5, 11), leg0=7, leg1=9, toe=4),
    "broad": dict(hx0=4, hx1=10, face0=5, face1=9, torso=(6, 10), arm=(3, 6),
                  skirt=(4, 11), leg0=7, leg1=10, toe=3),
    "tall": dict(hx0=4, hx1=10, face0=5, face1=9, torso=(6, 10), arm=(4, 6),
                 skirt=(5, 11), leg0=7, leg1=9, toe=4),
    "small": dict(hx0=5, hx1=10, face0=6, face1=9, torso=(7, 10), arm=(5, 7),
                  skirt=(6, 10), leg0=7, leg1=9, toe=5),
    "hunched": dict(hx0=3, hx1=9, face0=4, face1=8, torso=(6, 10), arm=(4, 6),
                    skirt=(5, 11), leg0=7, leg1=9, toe=4),
}

CHARACTERS = ("jingke", "gaojianli", "goutu", "tianguang", "taizidan",
              "fanyuqi", "qinwuyang", "qinwang", "xiawuju", "guard")

#: What each person wears and carries.  Muted colours, two or three per
#: garment, and one piece of gear that has to read at a glance.
SPRITE_SPECS: dict[str, dict] = {
    "jingke": dict(
        geo="adult",
        robe=mix("indigo", "ink", 0.16),
        robe_light=lighten("indigo", 0.12),
        robe_dark=darken("indigo", 0.45),
        trim=mix("bone", "indigo", 0.55),
        sash=mix("bone", "earth", 0.55),
        hair="hair",
        headgear="topknot",
        prop="sword",
    ),
    "gaojianli": dict(
        geo="adult",
        robe=mix("jade", "bone", 0.30),
        robe_light=lighten(mix("jade", "bone", 0.30), 0.16),
        robe_dark=darken(mix("jade", "bone", 0.30), 0.40),
        trim=mix("bone", "jade", 0.30),
        sash=mix("bronze", "bone", 0.50),
        hair=mix("hair", "hair_grey", 0.40),
        headgear="scholar_cap",
        prop="zither",
    ),
    "goutu": dict(
        geo="broad",
        robe=mix("earth", "clay", 0.28),
        robe_light=lighten(mix("earth", "clay", 0.28), 0.16),
        robe_dark=darken(mix("earth", "clay", 0.28), 0.42),
        trim=darken("earth", 0.25),
        sash="earth",
        hair="hair",
        headgear="band",
        apron=mix("ash", "bone", 0.22),
        prop="cleaver",
        short=True,
    ),
    "tianguang": dict(
        geo="hunched",
        robe=mix("bone", "ash", 0.42),
        robe_light=lighten(mix("bone", "ash", 0.42), 0.16),
        robe_dark=darken(mix("bone", "ash", 0.42), 0.38),
        trim=mix("bone", "ash", 0.22),
        sash=mix("clay", "ash", 0.30),
        hair=mix("snow", "bone", 0.15),
        headgear=None,
        beard="long_white",
        prop="staff",
    ),
    "taizidan": dict(
        geo="adult",
        robe=mix("blood", "earth", 0.45),
        robe_light=lighten(mix("blood", "earth", 0.45), 0.20),
        robe_dark=darken(mix("blood", "earth", 0.45), 0.45),
        trim="silk",
        sash="silk",
        hair="hair",
        headgear="cap_tall",
        prop="jade",
        hem_trim=True,
    ),
    "fanyuqi": dict(
        geo="broad",
        robe=darken("slate", 0.28),
        robe_light=mix("slate", "bone", 0.22),
        robe_dark=darken("slate", 0.55),
        trim=mix("bronze", "bone", 0.30),
        sash=darken("blood", 0.25),
        hair="hair",
        headgear="general_cap",
        beard="short_dark",
        armour="slate",
        cape=mix("blood", "earth", 0.30),
    ),
    "qinwuyang": dict(
        geo="small",
        robe=mix("clay", "earth", 0.35),
        robe_light=lighten(mix("clay", "earth", 0.35), 0.20),
        robe_dark=darken(mix("clay", "earth", 0.35), 0.40),
        trim=mix("bone", "clay", 0.45),
        sash="earth",
        hair="hair",
        headgear="boy_hair",
        prop="knife",
        short=True,
    ),
    "qinwang": dict(
        geo="tall",
        robe=mix("ash", "ink", 0.30),
        robe_light=mix("ash", "slate", 0.38),
        robe_dark="ink",
        trim="cinnabar",
        sash="cinnabar",
        hair="hair",
        headgear="crown_flat",
        prop="longsword",
        cuff="cinnabar",
    ),
    "xiawuju": dict(
        geo="adult",
        robe=mix("bone", "jade", 0.38),
        robe_light=lighten(mix("bone", "jade", 0.38), 0.14),
        robe_dark=darken(mix("bone", "jade", 0.38), 0.40),
        trim=mix("bone", "ash", 0.18),
        sash=mix("clay", "bone", 0.40),
        hair=mix("hair", "hair_grey", 0.55),
        headgear="cloth_cap",
        beard="short_grey",
        prop="bag",
    ),
    "guard": dict(
        geo="broad",
        robe=darken("slate", 0.45),
        robe_light=mix("slate", "bone", 0.16),
        robe_dark="ink",
        trim=mix("bronze", "ink", 0.35),
        sash="ink",
        hair="hair",
        headgear="helmet",
        armour=mix("slate", "ink", 0.25),
        prop="halberd",
    ),
}


def geometry(spec: dict) -> dict:
    g = dict(GEO[spec["geo"]])
    g["skirt_top"] = g["sash"] + 1
    if spec.get("short"):
        g["hem"] -= 2
    g["leg"] = min(g["leg"], g["hem"] + 1)
    return g


def pal(spec: dict) -> dict:
    """Resolve a spec's colours, filling in sensible default shades."""
    robe = colour(spec["robe"])
    trim = colour(spec["trim"]) if spec.get("trim") else darken(robe, 0.25)
    hair = colour(spec.get("hair", "hair"))
    p = {
        "robe": robe,
        "robe_light": colour(spec["robe_light"]) if spec.get("robe_light") else lighten(robe, 0.14),
        "robe_dark": colour(spec["robe_dark"]) if spec.get("robe_dark") else darken(robe, 0.40),
        "trim": trim,
        "sash": colour(spec["sash"]) if spec.get("sash") else darken(robe, 0.30),
        "cuff": colour(spec["cuff"]) if spec.get("cuff") else mix(trim, robe, 0.30),
        "hair": hair,
        "hair_light": lighten(hair, 0.24),
        "skin": colour(spec.get("skin", "skin")),
        "skin_shadow": colour("skin_shadow"),
        "eye": colour("ink"),
        "trouser": colour(spec.get("trouser")) if spec.get("trouser") else darken(robe, 0.45),
        "boot": colour(spec.get("boot")) if spec.get("boot") else darken("earth", 0.55),
        "tie": colour("bone"),
        "grip": mix("bone", "clay", 0.35),
        "guard": colour("bronze"),
        "sheath": darken("bronze", 0.35),
        "wood": darken("earth", 0.22),
        "wood_light": lighten("earth", 0.22),
        "cap": colour(spec.get("cap")) if spec.get("cap") else darken(robe, 0.30),
        "cap_band": colour(spec.get("cap_band", "bronze")),
        "stud": colour("gold"),
        "string": mix("silk", "bone", 0.35),
        "jade": colour("jade"),
        "jade_light": lighten("jade", 0.30),
        "apron": colour(spec["apron"]) if spec.get("apron") else None,
        "armour": None,
        "cape": None,
    }
    if spec.get("armour"):
        armour = colour(spec["armour"])
        p["armour"] = armour
        p["armour_dark"] = darken(armour, 0.45)
        p["armour_light"] = lighten(armour, 0.22)
    if spec.get("cape"):
        cape = colour(spec["cape"])
        p["cape"] = cape
        p["cape_dark"] = darken(cape, 0.40)
    return p


# -- front view -------------------------------------------------------------


def _cape_front(c: Canvas, g: dict, p: dict) -> None:
    cape, edge = p["cape"], p["cape_dark"]
    top = g["sy"] - 1
    bottom = g["sash"] + 4
    for y in range(top, bottom + 1):
        grow = 1 if y > g["sy"] + 2 else 0
        x0, x1 = g["tx0"] - 2 - grow, g["tx1"] + 2 + grow
        c.hline(x0, x1, y, cape)
        c.set(x0, y, edge)
        c.set(x1, y, edge)
    c.hline(g["tx0"] - 2, g["tx1"] + 2, top, edge)


def _legs_front(c: Canvas, g: dict, p: dict, phase: int) -> None:
    narrow = (g["tx1"] - g["tx0"]) <= 4
    lx = g["tx0"] if narrow else g["tx0"] + 1
    rx = g["tx1"] - 1
    top, foot = g["leg"], g["foot"]
    if phase == 0:
        c.rect(lx, top, lx + 1, foot - 1, p["trouser"])
        c.rect(rx, top, rx + 1, foot - 1, p["trouser"])
        c.rect(lx - 1, foot, lx + 1, foot, p["boot"])
        c.rect(rx, foot, rx + 2, foot, p["boot"])
    else:
        c.rect(lx - 1, top, lx, foot - 1, p["trouser"])
        c.rect(lx - 2, foot, lx, foot, p["boot"])
        c.rect(rx, top, rx + 1, foot - 2, p["trouser"])
        c.rect(rx + 1, foot - 1, rx + 2, foot - 1, p["boot"])


def _skirt_front(c: Canvas, g: dict, p: dict, spec: dict) -> None:
    top, hem = g["skirt_top"], g["hem"]

    def span(y: int) -> tuple[int, int]:
        grow = 1 if y >= hem - 2 else 0
        return g["tx0"] - 1 - grow, g["tx1"] + 1 + grow

    for y in range(top, hem + 1):
        x0, x1 = span(y)
        c.hline(x0, x1, y, p["robe"])
    for y in range(top, hem + 1):
        x0, x1 = span(y)
        c.set(x0, y, p["robe_dark"])
        c.set(x1, y, p["robe_dark"])
    for x in (g["tx0"] + 1, g["tx1"] - 1):
        c.vline(x, top + 1, hem - 1, p["robe_dark"])
    x0, x1 = span(hem)
    c.hline(x0, x1, hem, p["trim"] if spec.get("hem_trim") else p["robe_dark"])


def _torso_front(c: Canvas, g: dict, p: dict, phase: int) -> None:
    sy, sash = g["sy"], g["sash"]
    tx0, tx1 = g["tx0"], g["tx1"]
    c.hline(tx0 - 1, tx1 + 1, sy, p["robe"])
    for y in range(sy + 1, sash):
        c.hline(tx0, tx1, y, p["robe"])
    # a lit shoulder line keeps black robes readable on dark floors
    c.hline(tx0, tx1, sy, p["robe_light"])
    c.vline(tx0, sy + 1, sash - 1, p["robe_dark"])
    c.vline(tx1, sy + 1, sash - 1, p["robe_dark"])
    # sleeves: the cuff and hand shift outward by one pixel on the step frame
    dx = 1 if phase else 0
    slx0, slx1 = g["sl"]
    srx0, srx1 = g["sr"]
    for y in range(sy, sash - 1):
        c.hline(slx0 - dx, slx1, y, p["robe"])
        c.hline(srx0, srx1 + dx, y, p["robe"])
    c.hline(slx0 - dx, slx1, sy, p["robe_light"])
    c.hline(srx0, srx1 + dx, sy, p["robe_light"])
    c.vline(slx0 - dx, sy, sash - 2, p["robe_dark"])
    c.vline(srx1 + dx, sy, sash - 2, p["robe_dark"])
    c.vline(slx1, sy + 1, sash - 2, p["robe_light"])
    c.vline(srx0, sy + 1, sash - 2, p["robe_light"])
    c.hline(slx0 - dx, slx1, sash - 2, p["cuff"])
    c.hline(srx0, srx1 + dx, sash - 2, p["cuff"])
    c.hline(slx0 - dx, slx1 - dx, sash - 1, p["skin"])
    c.hline(srx0 + dx, srx1 + dx, sash - 1, p["skin"])


def _apron_front(c: Canvas, g: dict, p: dict) -> None:
    if not p["apron"]:
        return
    apron = p["apron"]
    top = g["sy"] + 4
    for y in range(top, g["hem"] - 1):
        c.hline(g["tx0"] + 1, g["tx1"] - 1, y, apron)
    c.hline(g["tx0"] + 1, g["tx1"] - 1, top, darken(apron, 0.32))
    c.vline(g["tx0"] + 1, top, g["hem"] - 2, darken(apron, 0.38))
    c.vline(g["tx1"] - 1, top, g["hem"] - 2, darken(apron, 0.38))
    c.set(g["tx0"] + 2, top + 2, mix(apron, "blood", 0.30))
    c.set(g["tx1"] - 2, top + 3, mix(apron, "blood", 0.22))


def _armour_front(c: Canvas, g: dict, p: dict) -> None:
    tx0, tx1 = g["tx0"], g["tx1"]
    sy, sash = g["sy"], g["sash"]
    for y in range(sy + 1, sash):
        band = (y - sy) % 3
        if band == 0:
            c.hline(tx0, tx1, y, p["armour_dark"])
        elif band == 1:
            c.hline(tx0, tx1, y, p["armour_light"])
        else:
            c.hline(tx0, tx1, y, p["armour"])
    for y in range(sy + 2, sash, 3):
        for x in (tx0 + 1, tx1 - 1):
            c.set(x, y, p["stud"])
    c.hline(tx0 - 1, tx1 + 1, sy, p["armour_light"])
    c.set(tx0 - 1, sy + 1, p["armour_dark"])
    c.set(tx1 + 1, sy + 1, p["armour_dark"])


def _collar_front(c: Canvas, g: dict, p: dict) -> None:
    sy = g["sy"]
    fx0, fx1 = g["fx0"], g["fx1"]
    trim = p["trim"]
    # V of the cross-collar
    c.set(fx0, sy, trim)
    c.set(fx0 + 1, sy + 1, trim)
    c.set(fx0 + 2, sy + 2, trim)
    c.set(fx1, sy, trim)
    c.set(fx1 - 1, sy + 1, trim)
    c.set(fx0 + 1, sy + 2, trim)
    # the wearer's left panel crosses over and runs to the hip
    c.set(fx0, sy + 3, trim)
    c.set(fx0 - 1, sy + 4, trim)


def _sash_front(c: Canvas, g: dict, p: dict) -> None:
    sash = g["sash"]
    tx0, tx1 = g["tx0"], g["tx1"]
    c.hline(tx0 - 1, tx1 + 1, sash, p["sash"])
    knot = (tx0 + tx1) // 2
    c.set(knot, sash, darken(p["sash"], 0.40))
    c.set(knot + 1, sash, darken(p["sash"], 0.40))
    c.vline(knot, sash + 1, sash + 2, darken(p["sash"], 0.25))


def _head_front(c: Canvas, g: dict, p: dict, spec: dict) -> None:
    top, bot = g["head_top"], g["head_bot"]
    hx0, hx1 = g["hx0"], g["hx1"]
    fx0, fx1 = g["fx0"], g["fx1"]
    hair, skin, shadow = p["hair"], p["skin"], p["skin_shadow"]
    c.hline(hx0 + 1, hx1 - 1, top, hair)
    c.hline(hx0, hx1, top + 1, hair)
    c.hline(hx0, hx1, top + 2, hair)
    for y in range(top + 2, bot + 1):
        c.hline(fx0, fx1, y, skin)
    for y in range(top + 2, bot):
        c.set(hx0, y, hair)
        c.set(hx1, y, hair)
    c.set(fx0, bot, shadow)
    c.set(fx1, bot, shadow)
    # ears
    c.set(hx0 - 1, top + 3, skin)
    c.set(hx1 + 1, top + 3, skin)
    # eyes, nose, mouth
    c.set(fx0 + 1, top + 3, p["eye"])
    c.set(fx1 - 1, top + 3, p["eye"])
    c.set(fx0 + 2, top + 4, shadow)
    c.set(fx0 + 2, bot, shadow)
    if g["neck"] is not None:
        c.hline(fx0 + 1, fx1 - 1, g["neck"], skin)
        c.set(fx1 - 1, g["neck"], shadow)


def _headgear_front(c: Canvas, g: dict, p: dict, spec: dict) -> None:
    kind = spec.get("headgear")
    top = g["head_top"]
    hx0, hx1 = g["hx0"], g["hx1"]
    mid = (hx0 + hx1) // 2
    if kind == "topknot":
        c.rect(mid - 1, top - 2, mid + 1, top - 1, p["hair"])
        c.set(mid, top - 2, p["hair_light"])
        c.hline(mid - 1, mid + 1, top - 1, p["tie"])
    elif kind == "scholar_cap":
        c.rect(hx0 + 1, top - 2, hx1 - 1, top - 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top - 1, p["cap_band"])
        c.hline(hx0 + 1, hx1 - 1, top - 2, darken(p["cap"], 0.35))
    elif kind == "cap_tall":
        c.rect(hx0 + 1, top - 3, hx1 - 1, top - 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top - 1, "bone")
        c.hline(hx0 + 2, hx1 - 2, top - 2, lighten(p["cap"], 0.20))
        c.hline(hx0 + 1, hx1 - 1, top - 3, darken(p["cap"], 0.40))
    elif kind == "crown_flat":
        board = "ink"
        c.hline(3, 13, top - 4, board)
        c.hline(4, 12, top - 3, "cinnabar")
        c.rect(mid - 1, top - 2, mid + 1, top - 1, board)
        c.hline(mid - 1, mid + 1, top - 1, "cinnabar")
        c.set(3, top - 3, "bone")
        c.set(13, top - 3, "bone")
        c.set(3, top - 2, "bone")
        c.set(13, top - 2, "bone")
    elif kind == "helmet":
        c.rect(hx0, top, hx1, top + 1, p["armour"] or p["robe_dark"])
        c.hline(hx0, hx1, top + 2, p["trim"])
        c.hline(hx0 + 1, hx1 - 1, top, lighten(p["armour"] or p["robe_dark"], 0.25))
        c.set(hx0, top + 3, p["armour"] or p["robe_dark"])
        c.set(hx1, top + 3, p["armour"] or p["robe_dark"])
    elif kind == "band":
        c.hline(hx0, hx1, top + 1, mix("bone", "clay", 0.40))
        c.set(hx1, top + 2, mix("bone", "clay", 0.25))
        c.set(hx1 + 1, top + 2, mix("clay", "earth", 0.40))
    elif kind == "cloth_cap":
        c.rect(hx0, top, hx1, top + 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top, lighten(p["cap"], 0.22))
        c.set(hx1, top + 1, darken(p["cap"], 0.35))
    elif kind == "boy_hair":
        c.rect(mid - 1, top - 2, mid, top - 1, p["hair"])
        c.hline(mid - 1, mid, top - 1, p["tie"])
        c.set(mid, top - 2, p["hair_light"])
        c.hline(hx0, hx1, top + 2, p["hair"])
    elif kind == "general_cap":
        c.rect(hx0 + 1, top - 1, hx1 - 1, top, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top, p["cap_band"])
        c.rect(mid, top - 3, mid + 1, top - 2, "cinnabar")
        c.set(mid, top - 3, mix("cinnabar", "bone", 0.35))


def _beard_front(c: Canvas, g: dict, p: dict, spec: dict) -> None:
    kind = spec.get("beard")
    if not kind:
        return
    bot = g["head_bot"]
    fx0, fx1 = g["fx0"], g["fx1"]
    if kind == "long_white":
        c.hline(fx0 + 1, fx1 - 1, bot + 1, p["hair"])
        c.hline(fx0 + 1, fx1 - 1, bot + 2, p["hair"])
        c.hline(fx0 + 2, fx1 - 2, bot + 3, p["hair"])
        c.set(fx0 + 1, bot + 1, p["hair_light"])
        c.set(fx0 + 2, bot + 2, p["hair_light"])
        c.set(fx1 - 1, bot + 1, darken(p["hair"], 0.25))
        c.set(fx1 - 2, bot + 3, darken(p["hair"], 0.25))
    else:
        tone = p["hair"]
        c.hline(fx0 + 1, fx1 - 1, bot + 1, tone)
        c.set(fx0 + 1, bot + 1, lighten(tone, 0.18))
        c.set(fx1 - 1, bot + 1, darken(tone, 0.20))


def _prop_front(c: Canvas, g: dict, p: dict, spec: dict) -> None:
    prop = spec.get("prop")
    if not prop:
        return
    hip = g["tx1"] + 1
    sash, hem, foot = g["sash"], g["hem"], g["foot"]
    if prop == "sword":
        c.set(hip, sash - 3, p["guard"])            # pommel
        c.vline(hip, sash - 2, sash - 1, p["grip"])  # wrapped grip
        c.set(hip, sash - 2, p["tie"])
        c.hline(hip - 1, hip + 1, sash - 1, p["guard"])
        c.line(hip, sash + 1, min(15, hip + 2), hem + 1, p["sheath"])
        c.line(hip + 1, sash + 1, min(15, hip + 3), hem + 1,
               mix(p["sheath"], "bone", 0.40))
        c.hline(min(15, hip + 2), min(15, hip + 3), hem + 1, p["guard"])
    elif prop == "longsword":
        c.set(hip - 1, sash - 5, p["guard"])
        c.vline(hip - 1, sash - 4, sash - 1, p["grip"])
        c.set(hip - 1, sash - 3, p["tie"])
        c.hline(hip - 2, hip, sash, p["guard"])
        c.line(hip, sash + 1, min(15, hip + 3), foot - 1, p["sheath"])
        c.line(hip + 1, sash + 1, min(15, hip + 4), foot - 1,
               mix(p["sheath"], "bone", 0.45))
        c.hline(min(15, hip + 3), min(15, hip + 4), foot, p["guard"])
    elif prop == "staff":
        x = g["tx1"] + 3
        c.vline(x, 3, foot, p["wood"])
        c.vline(x - 1, 3, foot - 1, p["wood_light"])
        c.rect(x - 1, 1, x, 2, p["wood"])
        c.set(x - 1, 1, p["wood_light"])
        c.hline(x - 2, x, sash - 1, p["skin"])
        c.set(x, sash - 1, p["wood"])
    elif prop == "zither":
        x = g["tx1"] + 2
        c.rect(x, g["sy"] + 1, x + 2, sash + 2, p["wood"])
        c.hline(x, x + 2, g["sy"] + 1, p["wood_light"])
        c.vline(x, g["sy"] + 1, sash + 2, p["wood_light"])
        c.vline(x + 2, g["sy"] + 1, sash + 2, p["sheath"])
        c.hline(x, x + 2, sash + 2, p["sheath"])
        for y in range(g["sy"] + 2, sash + 2, 2):
            c.set(x + 1, y, p["string"])
        c.set(x + 1, sash + 1, p["guard"])          # bridge
        c.hline(x - 1, x, sash - 1, p["skin"])
    elif prop == "cleaver":
        bx = g["tx1"] - 1
        c.rect(bx, sash - 1, bx + 2, sash + 1, mix("slate", "bone", 0.30))
        c.hline(bx, bx + 2, sash - 1, "bone")
        c.hline(bx, bx + 2, sash + 1, darken("slate", 0.35))
        c.set(bx + 3, sash - 1, p["wood"])
        c.set(bx + 3, sash, p["wood_light"])
    elif prop == "knife":
        c.hline(g["tx0"] + 1, g["tx1"], sash, mix("slate", "bone", 0.50))
        c.set(g["tx0"] + 1, sash, "bone")
        c.set(g["tx1"] + 1, sash, p["wood"])
        c.set(g["tx1"] + 1, sash + 1, p["wood_light"])
        c.set(g["tx1"], sash - 1, darken("slate", 0.35))
    elif prop == "bag":
        bx = g["fx0"]
        c.rect(bx, sash, bx + 2, sash + 3, "clay")
        c.hline(bx, bx + 2, sash, darken("clay", 0.35))
        c.hline(bx, bx + 2, sash + 1, "bone")
        c.vline(bx, sash, sash + 3, darken("clay", 0.45))
        c.vline(bx + 2, sash, sash + 3, darken("clay", 0.45))
        c.set(bx + 1, sash + 2, lighten("clay", 0.25))
        c.line(bx + 2, sash - 1, g["tx1"] - 1, g["sy"] + 1, darken("clay", 0.30))
    elif prop == "jade":
        cord = g["fx0"] + 2
        c.vline(cord, sash, sash + 2, p["tie"])
        c.rect(cord - 1, sash + 2, cord, sash + 3, p["jade"])
        c.set(cord - 1, sash + 2, p["jade_light"])
        c.set(cord, sash + 3, darken("jade", 0.35))
    elif prop == "halberd":
        x = g["tx0"] - 2
        blade = mix("slate", "bone", 0.35)
        light = mix("slate", "bone", 0.55)
        dark = darken("slate", 0.40)
        c.vline(x, 2, foot, p["wood"])
        c.vline(x + 1, 4, foot - 1, p["wood_light"])
        c.hline(x - 1, x + 1, 3, dark)
        c.hline(x - 1, x + 1, 4, blade)
        c.hline(x - 2, x + 1, 5, blade)
        c.hline(x - 2, x + 1, 6, blade)
        c.hline(x - 1, x + 1, 7, dark)
        c.set(x - 2, 5, light)
        c.set(x - 2, 6, light)
        c.set(x, 1, mix("slate", "bone", 0.50))
        c.set(x, 0, dark)
        c.hline(x, x + 1, sash - 1, p["skin"])


def _frame_front(spec: dict, phase: int) -> Canvas:
    c = Canvas(16, 24)
    g = geometry(spec)
    p = pal(spec)
    if p["cape"]:
        _cape_front(c, g, p)
    _legs_front(c, g, p, phase)
    _skirt_front(c, g, p, spec)
    _torso_front(c, g, p, phase)
    _apron_front(c, g, p)
    if p["armour"]:
        _armour_front(c, g, p)
    _collar_front(c, g, p)
    _sash_front(c, g, p)
    _head_front(c, g, p, spec)
    _headgear_front(c, g, p, spec)
    _beard_front(c, g, p, spec)
    _prop_front(c, g, p, spec)
    return c


# -- side view (drawn facing left; the right-facing frames are mirrored) -----


def _frame_side(spec: dict, phase: int) -> Canvas:
    c = Canvas(16, 24)
    g = geometry(spec)
    s = SIDE_GEO[spec["geo"]]
    p = pal(spec)
    top, bot = g["head_top"], g["head_bot"]
    sy, sash = g["sy"], g["sash"]
    hem, foot = g["hem"], g["foot"]
    hx0, hx1 = s["hx0"], s["hx1"]
    face0, face1 = s["face0"], s["face1"]
    t0, t1 = s["torso"]
    arm0, arm1 = s["arm"]
    k0, k1 = s["skirt"]
    if p["cape"]:
        cape, edge = p["cape"], p["cape_dark"]
        for y in range(sy - 1, sash + 4):
            grow = 1 if y > sy + 2 else 0
            c.hline(t1 - 1, k1 + 1 + grow, y, cape)
        c.vline(k1 + 1, sy - 1, sash + 4, edge)
        c.hline(t1 - 1, k1 + 1, sy - 1, edge)
    # legs: front leg strides forward, back leg lifts on the step frame
    lx0, lx1 = s["leg0"], s["leg1"]
    if phase == 0:
        c.rect(lx0, g["leg"], lx1, foot - 1, p["trouser"])
        c.rect(s["toe"], foot, lx1, foot, p["boot"])
        c.set(lx0 - 1, foot - 1, p["boot"])
    else:
        c.rect(lx0 - 1, g["leg"], lx0, foot - 1, p["trouser"])
        c.rect(s["toe"] - 1, foot, lx0, foot, p["boot"])
        c.rect(lx0 + 2, g["leg"], lx1, foot - 2, p["trouser"])
        c.rect(lx0 + 2, foot - 1, lx1, foot - 1, p["boot"])
    # skirt
    grow = 0
    for y in range(g["skirt_top"], hem + 1):
        grow = 1 if y >= hem - 2 else 0
        c.hline(k0 - grow, k1 + grow, y, p["robe"])
    c.vline(k0 - 1, g["skirt_top"], hem, p["robe_dark"])
    c.vline(k1 + 1, g["skirt_top"], hem, p["robe_dark"])
    c.hline(k0 - 1, k1 + 1, hem, p["trim"] if spec.get("hem_trim") else p["robe_dark"])
    c.vline((k0 + k1) // 2, g["skirt_top"] + 1, hem - 1, p["robe_dark"])
    # torso
    for y in range(sy, sash):
        c.hline(t0, t1, y, p["robe"])
    c.vline(t1, sy, sash - 1, p["robe_dark"])
    # near arm hangs in front of the body
    dx = 1 if phase else 0
    for y in range(sy + 1, sash - 1):
        c.hline(arm0 - dx, arm1, y, p["robe_light"] if p["armour"] is None else p["robe"])
    c.vline(arm0 - dx, sy + 1, sash - 2, p["robe_dark"])
    c.vline(arm1, sy + 1, sash - 2, p["robe_dark"])
    c.hline(arm0 - dx, arm1, sash - 2, p["cuff"])
    c.hline(arm0 - dx, arm1 - dx, sash - 1, p["skin"])
    if p["armour"]:
        for y in range(sy + 1, sash):
            band = (y - sy) % 3
            tone = p["armour_dark"] if band == 0 else (p["armour_light"] if band == 1 else p["armour"])
            c.hline(t0, t1, y, tone)
        c.set(t0 + 1, sy + 2, p["stud"])
    # collar and sash seen from the side
    c.set(face0, sy, p["trim"])
    c.set(face0, sy + 1, p["trim"])
    c.hline(t0, t1, sash, p["sash"])
    c.set(t0 + 1, sash, darken(p["sash"], 0.40))
    # head in profile
    hair, skin, shadow = p["hair"], p["skin"], p["skin_shadow"]
    c.hline(hx0 + 1, hx1, top, hair)
    c.hline(hx0, hx1, top + 1, hair)
    c.hline(hx0, hx1, top + 2, hair)
    for y in range(top + 2, bot + 1):
        c.hline(face0, face1, y, skin)
    for y in range(top + 2, bot + 1):
        c.set(hx1, y, hair)
        if y < bot - 1:
            c.set(hx1 - 1, y, hair)
    c.set(face0 - 1, top + 3, skin)          # nose
    c.set(face0 - 1, top + 4, shadow)
    c.set(face0 + 1, top + 3, p["eye"])
    c.set(face0, bot, shadow)
    c.set(face1, bot, shadow)
    if g["neck"] is not None:
        c.set(face0 + 1, g["neck"], skin)
        c.set(face0 + 2, g["neck"], skin)
    # headgear, in profile
    kind = spec.get("headgear")
    mid = (hx0 + hx1) // 2
    if kind == "topknot":
        c.rect(hx1 - 2, top - 2, hx1 - 1, top - 1, hair)
        c.hline(hx1 - 2, hx1 - 1, top - 1, p["tie"])
    elif kind == "scholar_cap":
        c.rect(hx0 + 1, top - 2, hx1 - 1, top - 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top - 1, p["cap_band"])
    elif kind == "cap_tall":
        c.rect(hx0 + 1, top - 3, hx1 - 1, top - 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top - 1, "bone")
    elif kind == "crown_flat":
        c.hline(3, 13, top - 4, "ink")
        c.hline(4, 12, top - 3, "cinnabar")
        c.rect(mid - 1, top - 2, mid + 1, top - 1, "ink")
        c.set(3, top - 3, "bone")
        c.set(3, top - 2, "bone")
    elif kind == "helmet":
        c.rect(hx0, top, hx1, top + 1, p["armour"] or p["robe_dark"])
        c.hline(hx0, hx1, top + 2, p["trim"])
        c.hline(hx0 + 1, hx1 - 1, top, lighten(p["armour"] or p["robe_dark"], 0.25))
    elif kind == "band":
        c.hline(hx0, hx1, top + 1, mix("clay", "bone", 0.35))
    elif kind == "cloth_cap":
        c.rect(hx0, top, hx1 - 1, top + 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top, lighten(p["cap"], 0.22))
    elif kind == "boy_hair":
        c.rect(mid, top - 1, mid + 1, top - 1, hair)
        c.hline(hx0, hx1, top + 2, hair)
    elif kind == "general_cap":
        c.rect(hx0 + 1, top - 1, hx1 - 1, top, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top, p["cap_band"])
        c.rect(hx1 - 2, top - 3, hx1 - 1, top - 2, "cinnabar")
    # beard
    if spec.get("beard") == "long_white":
        c.hline(face0, face1 - 1, bot + 1, hair)
        c.hline(face0, face1 - 2, bot + 2, hair)
        c.hline(face0 + 1, face1 - 2, bot + 3, hair)
        c.set(face0, bot + 1, lighten(hair, 0.20))
    elif spec.get("beard"):
        c.hline(face0, face1 - 1, bot + 1, hair)
    # props in profile
    prop = spec.get("prop")
    if prop == "sword":
        c.set(t1 + 1, sash - 2, p["grip"])
        c.set(t1 + 1, sash - 1, p["grip"])
        c.line(t1 + 1, sash + 1, min(15, t1 + 3), hem + 1, p["sheath"])
    elif prop == "longsword":
        c.vline(t1, sash - 3, sash - 1, p["grip"])
        c.set(t1, sash - 2, p["tie"])
        c.hline(t1 - 1, t1 + 1, sash, p["guard"])
        c.line(t1 + 1, sash + 1, min(15, t1 + 4), foot, p["sheath"])
        c.set(min(15, t1 + 4), foot, p["guard"])
    elif prop == "staff":
        x = t1 + 2
        c.vline(x, 2, foot, p["wood"])
        c.set(x, 1, p["wood"])
        c.set(x - 1, 2, p["wood_light"])
        c.hline(x - 1, x, sash - 1, p["skin"])
        c.set(x, sash, p["wood"])
    elif prop == "zither":
        x = t1 + 1
        c.rect(x, sy + 1, x + 1, sash + 2, p["wood"])
        c.vline(x, sy + 1, sash + 2, p["wood_light"])
        c.vline(x + 1, sy + 1, sash + 2, p["sheath"])
        for y in range(sy + 2, sash + 2, 2):
            c.set(x, y, p["string"])
        c.hline(x - 1, x, sash - 1, p["skin"])
    elif prop == "cleaver":
        c.rect(arm1, sash - 1, arm1 + 2, sash + 1, mix("slate", "bone", 0.30))
        c.hline(arm1, arm1 + 2, sash - 1, "bone")
        c.set(arm1 - 1, sash - 1, p["wood"])
    elif prop == "knife":
        c.set(face0 + 2, sash + 1, "bone")
        c.set(face0 + 1, sash + 1, mix("slate", "bone", 0.40))
        c.set(face0 + 3, sash + 1, p["wood"])
    elif prop == "bag":
        c.rect(face0, sash, face0 + 2, sash + 3, p["wood"])
        c.hline(face0, face0 + 2, sash + 1, "bone")
        c.vline(face0, sash, sash + 3, darken(p["wood"], 0.40))
        c.set(face0 + 1, sash + 2, lighten(p["wood"], 0.25))
    elif prop == "jade":
        c.vline(face0 + 2, sash, sash + 2, p["tie"])
        c.rect(face0 + 1, sash + 2, face0 + 2, sash + 3, p["jade"])
        c.set(face0 + 1, sash + 2, p["jade_light"])
    elif prop == "halberd":
        x = t1 + 2
        blade = mix("slate", "bone", 0.35)
        light = mix("slate", "bone", 0.55)
        dark = darken("slate", 0.40)
        c.vline(x, 2, foot, p["wood"])
        c.hline(x, x + 2, 3, dark)
        c.hline(x, x + 2, 4, blade)
        c.hline(x, x + 2, 5, blade)
        c.hline(x, x + 2, 6, blade)
        c.hline(x, x + 1, 7, dark)
        c.set(x + 2, 4, light)
        c.set(x + 2, 5, light)
        c.set(x, 1, light)
        c.set(x, 0, dark)
        c.hline(x - 1, x, sash - 1, p["skin"])
    return c


# -- back view --------------------------------------------------------------


def _frame_back(spec: dict, phase: int) -> Canvas:
    c = Canvas(16, 24)
    g = geometry(spec)
    p = pal(spec)
    sy, sash, hem, foot = g["sy"], g["sash"], g["hem"], g["foot"]
    top, bot = g["head_top"], g["head_bot"]
    hx0, hx1 = g["hx0"], g["hx1"]
    if p["cape"]:
        for y in range(sy - 1, sash + 4):
            grow = 1 if y > sy + 2 else 0
            c.hline(g["tx0"] - 2 - grow, g["tx1"] + 2 + grow, y, p["cape"])
        c.hline(g["tx0"] - 2, g["tx1"] + 2, sy - 1, p["cape_dark"])
    _legs_front(c, g, p, phase)
    # skirt (back pleat down the middle)
    for y in range(g["skirt_top"], hem + 1):
        grow = 1 if y >= hem - 2 else 0
        c.hline(g["tx0"] - 1 - grow, g["tx1"] + 1 + grow, y, p["robe"])
    for y in range(g["skirt_top"], hem + 1):
        grow = 1 if y >= hem - 2 else 0
        c.set(g["tx0"] - 1 - grow, y, p["robe_dark"])
        c.set(g["tx1"] + 1 + grow, y, p["robe_dark"])
    c.vline(g["tx0"] + 2, g["skirt_top"] + 1, hem - 1, p["robe_dark"])
    c.vline(g["tx1"] - 2, g["skirt_top"] + 1, hem - 1, p["robe_dark"])
    c.hline(g["tx0"] - 1, g["tx1"] + 1, hem, p["trim"] if spec.get("hem_trim") else p["robe_dark"])
    # torso and sleeves
    _torso_front(c, g, p, phase)
    if p["armour"]:
        _armour_front(c, g, p)
    # collar band at the nape and a sash knot
    c.hline(g["fx0"], g["fx1"], sy, p["trim"])
    _sash_front(c, g, p)
    # head: hair all round, no face
    hair = p["hair"]
    c.hline(hx0 + 1, hx1 - 1, top, hair)
    c.hline(hx0, hx1, top + 1, hair)
    for y in range(top + 2, bot + 1):
        c.hline(hx0, hx1, y, hair)
    c.hline(hx0 + 2, hx1 - 2, top + 1, p["hair_light"])
    c.set(hx0 + 1, top + 2, p["hair_light"])
    c.vline(hx0, top + 2, bot, darken(hair, 0.25))
    c.vline(hx1, top + 2, bot, darken(hair, 0.25))
    c.hline(hx0 + 1, hx1 - 1, bot, darken(hair, 0.15))
    if g["neck"] is not None:
        c.hline(g["fx0"] + 1, g["fx1"] - 1, g["neck"], p["skin"])
    kind = spec.get("headgear")
    mid = (hx0 + hx1) // 2
    if kind == "topknot":
        c.rect(mid - 1, top - 2, mid + 1, top - 1, hair)
        c.hline(mid - 1, mid + 1, top - 1, p["tie"])
        c.set(mid, top - 2, p["hair_light"])
    elif kind == "scholar_cap":
        c.rect(hx0 + 1, top - 2, hx1 - 1, top - 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top - 1, p["cap_band"])
    elif kind == "cap_tall":
        c.rect(hx0 + 1, top - 3, hx1 - 1, top - 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top - 1, "bone")
    elif kind == "crown_flat":
        c.hline(3, 13, top - 4, "ink")
        c.hline(4, 12, top - 3, "cinnabar")
        c.rect(mid - 1, top - 2, mid + 1, top - 1, "ink")
        c.set(13, top - 3, "bone")
        c.set(13, top - 2, "bone")
    elif kind == "helmet":
        c.rect(hx0, top, hx1, top + 1, p["armour"] or p["robe_dark"])
        c.hline(hx0, hx1, top + 2, p["trim"])
        c.hline(hx0 + 1, hx1 - 1, top, lighten(p["armour"] or p["robe_dark"], 0.25))
    elif kind == "band":
        c.hline(hx0, hx1, top + 1, mix("clay", "bone", 0.35))
    elif kind == "cloth_cap":
        c.rect(hx0, top, hx1, top + 1, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top, lighten(p["cap"], 0.22))
    elif kind == "boy_hair":
        c.rect(mid - 1, top - 1, mid, top - 1, hair)
    elif kind == "general_cap":
        c.rect(hx0 + 1, top - 1, hx1 - 1, top, p["cap"])
        c.hline(hx0 + 1, hx1 - 1, top, p["cap_band"])
        c.rect(mid, top - 3, mid + 1, top - 2, "cinnabar")
    # props visible from behind: those worn or carried on the left side
    prop = spec.get("prop")
    if prop == "sword":
        x = g["tx0"] - 1
        c.set(x, sash - 2, p["grip"])
        c.set(x, sash - 1, p["grip"])
        c.line(x, sash + 1, max(0, x - 2), hem + 1, p["sheath"])
        c.set(max(0, x - 2), hem + 1, p["guard"])
    elif prop == "longsword":
        x = g["tx0"] - 1
        c.vline(x, sash - 3, sash - 1, p["grip"])
        c.hline(x - 1, x + 1, sash, p["guard"])
        c.line(x, sash + 1, max(0, x - 2), foot, p["sheath"])
    elif prop in ("staff", "halberd"):
        x = 2 if prop == "staff" else 3
        if prop == "staff":
            c.vline(x, 2, foot, p["wood"])
            c.set(x, 1, p["wood"])
            c.hline(x, x + 1, sash - 1, p["skin"])
            c.set(x + 1, 2, p["wood_light"])
        else:
            blade = mix("slate", "bone", 0.35)
            light = mix("slate", "bone", 0.55)
            dark = darken("slate", 0.40)
            c.vline(x, 2, foot, p["wood"])
            c.hline(x - 2, x, 3, dark)
            c.hline(x - 2, x, 4, blade)
            c.hline(x - 2, x, 5, blade)
            c.hline(x - 2, x, 6, blade)
            c.hline(x - 1, x, 7, dark)
            c.set(x - 2, 4, light)
            c.set(x - 2, 5, light)
            c.set(x, 1, light)
            c.set(x, 0, dark)
            c.hline(x, x + 1, sash - 1, p["skin"])
    elif prop == "zither":
        x = 1
        c.rect(x, sy + 1, x + 1, sash + 2, p["wood"])
        c.vline(x + 1, sy + 1, sash + 2, p["sheath"])
        c.vline(x, sy + 1, sash + 2, p["wood_light"])
        for y in range(sy + 2, sash + 2, 2):
            c.set(x + 1, y, p["string"])
        c.hline(x, x + 1, sash - 1, p["skin"])
    elif prop == "jade":
        c.vline(g["tx0"] + 3, sash + 1, sash + 2, p["tie"])
    return c


def build_sprites() -> dict[str, Canvas]:
    """Render every character's eight-frame sheet."""
    out: dict[str, Canvas] = {}
    for name in CHARACTERS:
        spec = SPRITE_SPECS[name]
        sheet = Canvas(16 * 8, 24)
        frames = []
        for phase in (0, 1):
            frames.append(_frame_front(spec, phase))
        for phase in (0, 1):
            frames.append(_frame_side(spec, phase))
        for phase in (0, 1):
            frames.append(_frame_side(spec, phase).flip_h())
        for phase in (0, 1):
            frames.append(_frame_back(spec, phase))
        for index, frame in enumerate(frames):
            frame.outline("ink")
            sheet.paste(frame, index * 16, 0)
        out[name] = sheet
    return out


# ---------------------------------------------------------------------------
# Portraits: 48x48 busts for dialogue
#
# The same face geometry for everyone, with the identifying gear -- crown,
# tall cap, white beard, armour, zither -- drawn on top.  High contrast: an
# ink silhouette, a lit side and a shadow side, and eyes that stay legible at
# the 4x zoom the dialogue box uses.
# ---------------------------------------------------------------------------

PORTRAIT_HEAD_TOP = 6
PORTRAIT_HEAD_BOT = 28


def head_span(y: int) -> tuple[int, int]:
    """Rounded head outline: 19 px across at the temples, 5 px at the chin."""
    if y <= 6:
        return 20, 28
    if y == 7:
        return 18, 30
    if y == 8:
        return 17, 31
    if y == 9:
        return 16, 32
    if y <= 20:
        return 15, 33
    if y == 21:
        return 16, 32
    if y == 22:
        return 16, 32
    if y == 23:
        return 17, 31
    if y == 24:
        return 18, 30
    if y == 25:
        return 19, 29
    if y == 26:
        return 20, 28
    if y == 27:
        return 21, 27
    return 22, 26


PORTRAIT_SPECS: dict[str, dict] = {
    "jingke": dict(base="jingke", headgear="topknot", accessory="sword", stern=True),
    "gaojianli": dict(base="gaojianli", headgear="scholar_cap", accessory="zither"),
    "taizidan": dict(base="taizidan", headgear="cap_tall", accessory="jade",
                     beard="moustache"),
    "qinwuyang": dict(base="qinwuyang", headgear="boy_hair", young=True),
    "qinwang": dict(base="qinwang", headgear="crown_flat", accessory="sword",
                    beard="long_dark", stern=True),
    "xiawuju": dict(base="xiawuju", headgear="cloth_cap", beard="short_grey",
                    accessory="bag", old=True),
    "fanyuqi": dict(base="fanyuqi", headgear="general_cap", beard="short_dark",
                    armour=True, cape=True),
    "tianguang": dict(base="tianguang", headgear="topknot", beard="long_white",
                      old=True, accessory="staff"),
}

TORSO_ROWS = (
    (34, 15, 33), (35, 14, 34), (36, 13, 35), (37, 12, 36), (38, 11, 37),
    (39, 10, 38), (40, 9, 39), (41, 8, 40), (42, 7, 41), (43, 7, 41),
    (44, 6, 42), (45, 6, 42), (46, 6, 42), (47, 6, 42),
)


def _portrait_torso(c: Canvas, p: dict, spec: dict) -> None:
    robe = p["robe"]
    light = p["robe_light"]
    dark = p["robe_dark"]
    if spec.get("cape"):
        cape, edge = p["cape"], p["cape_dark"]
        for y in range(33, 48):
            grow = 0 if y < 38 else 1
            c.hline(4 - grow, 10, y, cape)
            c.hline(38, 44 + grow, y, cape)
        c.vline(4, 33, 47, edge)
        c.vline(44, 33, 47, edge)
        c.hline(5, 44, 33, edge)
    for y, x0, x1 in TORSO_ROWS:
        c.hline(x0, x1, y, robe)
        c.set(x0, y, dark)
        c.set(x1, y, dark)
    c.hline(16, 32, 34, light)               # lit shoulder line
    for y, x0, x1 in TORSO_ROWS:
        c.vline(x0 + 1, y, y, light)
        c.vline(x1 - 1, y, y, dark)
    # collar: a crossed V of trim, the left panel over the right
    c.line(17, 34, 23, 45, p["trim"])
    c.line(18, 34, 24, 45, p["trim"])
    c.line(31, 34, 25, 45, p["trim"])
    c.line(30, 34, 24, 45, p["trim"])
    c.line(19, 35, 24, 44, p["trim"])
    c.line(29, 35, 25, 44, p["trim"])
    c.line(20, 36, 24, 44, darken(p["trim"], 0.35))
    # inner robe between the lapels
    for y in range(36, 46):
        c.set(24, y, light)
        c.set(25, y, dark)
    if p["armour"]:
        for y in range(37, 48, 4):
            c.hline(10, 38, y, p["armour_dark"])
            for x in range(11, 38, 6):
                c.set(x, y - 1, p["stud"])
        c.hline(12, 36, 35, p["armour_light"])
        c.hline(12, 36, 36, p["armour"])
    if spec.get("accessory") == "bag":
        c.line(17, 35, 29, 47, "clay")
        c.line(18, 35, 30, 47, darken("clay", 0.30))
    if spec.get("accessory") == "jade":
        c.hline(22, 27, 42, p["tie"])
        c.rect(23, 43, 26, 46, p["jade"])
        c.hline(23, 26, 43, p["jade_light"])
        c.set(26, 46, darken("jade", 0.35))


def _portrait_neck(c: Canvas, p: dict) -> None:
    for y in range(26, 36):
        c.hline(20, 29, y, p["skin"])
    c.hline(20, 21, 27, p["skin_shadow"])
    c.hline(28, 29, 27, p["skin_shadow"])
    c.vline(20, 28, 34, p["skin_shadow"])
    c.vline(29, 28, 34, darken(p["skin_shadow"], 0.25))
    c.hline(21, 26, 34, p["skin_shadow"])


def _portrait_ears(c: Canvas, p: dict) -> None:
    for y in range(15, 22):
        c.set(13, y, p["skin"])
        c.set(14, y, p["skin"])
        c.set(34, y, p["skin"])
        c.set(35, y, p["skin"])
    c.set(13, 16, p["skin_shadow"])
    c.set(35, 16, p["skin_shadow"])
    c.vline(14, 17, 20, p["skin_shadow"])
    c.vline(34, 17, 20, p["skin_shadow"])


def _portrait_head(c: Canvas, p: dict, spec: dict) -> None:
    hair, skin, shadow = p["hair"], p["skin"], p["skin_shadow"]
    for y in range(PORTRAIT_HEAD_TOP, PORTRAIT_HEAD_BOT + 1):
        x0, x1 = head_span(y)
        c.hline(x0, x1, y, hair)
    # carve the face out of the hair; the boy keeps a rounder jaw
    jaw_inset = 1 if spec.get("young") else 2
    for y in range(10, PORTRAIT_HEAD_BOT + 1):
        x0, x1 = head_span(y)
        inset = 2 if y < 24 else jaw_inset
        c.hline(x0 + inset, x1 - inset, y, skin)
    # shadow side of the face
    for y in range(12, 26):
        x0, x1 = head_span(y)
        c.set(x1 - 2, y, shadow)
        if y > 14:
            c.set(x1 - 3, y, shadow)
    c.hline(19, 29, 10, skin)
    # fringe: parted, so the forehead shows
    c.hline(17, 21, 10, hair)
    c.hline(27, 31, 10, hair)
    c.hline(17, 19, 11, hair)
    c.hline(29, 31, 11, hair)
    c.hline(17, 18, 12, hair)
    c.hline(30, 31, 12, hair)
    c.set(18, 11, p["hair_light"])
    c.set(19, 10, p["hair_light"])
    c.hline(20, 28, 6, darken(hair, 0.25))
    c.set(21, 7, p["hair_light"])
    # ears sit inside the hair line
    for y in range(15, 22):
        c.set(15, y, skin)
        c.set(33, y, skin)
    # brows
    if spec.get("young"):
        c.hline(18, 22, 13, hair)
        c.hline(26, 30, 13, hair)
    elif spec.get("stern"):
        c.hline(18, 23, 13, hair)
        c.set(23, 14, hair)
        c.hline(25, 30, 13, hair)
        c.set(25, 14, hair)
    else:
        c.hline(19, 23, 13, hair)
        c.hline(25, 29, 13, hair)
    # eyes
    eye_w = 5 if spec.get("young") else 4
    for ex in (19, 26):
        c.hline(ex, ex + eye_w - 1, 15, hair)
        c.hline(ex, ex + eye_w - 1, 16, "silk")
        c.hline(ex + 1, ex + eye_w - 2, 16, "ink")
        c.set(ex + 1, 16, mix("silk", "ink", 0.15))
        c.hline(ex, ex + eye_w - 1, 17, shadow)
    # nose
    c.vline(24, 19, 22, shadow)
    c.set(23, 23, shadow)
    c.set(25, 23, shadow)
    c.hline(23, 25, 23, mix(skin, shadow, 0.5))
    c.set(24, 22, lighten(skin, 0.18))
    # mouth
    if spec.get("old"):
        c.hline(21, 27, 25, mix(shadow, "blood", 0.25))
        c.hline(21, 27, 26, lighten(skin, 0.10))
        c.set(20, 24, shadow)
        c.set(28, 24, shadow)
    elif spec.get("stern"):
        c.hline(21, 27, 25, mix(shadow, "blood", 0.30))
        c.set(21, 24, shadow)
        c.set(27, 24, shadow)
    else:
        c.hline(21, 27, 25, mix(shadow, "blood", 0.20))
        c.hline(22, 26, 26, lighten(skin, 0.12))
    c.hline(22, 26, 27, shadow)
    if spec.get("old"):
        for y in (11, 12):
            c.hline(19, 22, y, shadow)
            c.hline(27, 30, y, shadow)
        c.vline(20, 21, 24, shadow)
        c.vline(28, 21, 24, shadow)
        c.set(18, 17, shadow)
        c.set(31, 17, shadow)


def _portrait_headgear(c: Canvas, p: dict, spec: dict) -> None:
    kind = spec.get("headgear")
    if kind is None:
        return
    if kind == "topknot":
        c.rect(21, 1, 27, 5, p["hair"])
        c.hline(22, 26, 1, p["hair_light"])
        c.hline(21, 27, 5, p["tie"])
        c.hline(19, 29, 4, p["tie"])
        c.set(19, 3, p["tie"])
    elif kind == "boy_hair":
        c.rect(22, 2, 26, 5, p["hair"])
        c.hline(22, 26, 5, p["tie"])
        c.set(23, 2, p["hair_light"])
    elif kind == "scholar_cap":
        c.rect(16, 2, 32, 8, p["cap"])
        c.hline(16, 32, 8, p["cap_band"])
        c.hline(17, 31, 2, lighten(p["cap"], 0.22))
        c.hline(16, 32, 3, p["cap_band"])
    elif kind == "cap_tall":
        c.rect(19, 0, 29, 7, p["cap"])
        c.hline(19, 29, 7, "bone")
        c.hline(20, 28, 0, darken(p["cap"], 0.45))
        c.hline(20, 28, 1, lighten(p["cap"], 0.18))
        c.hline(19, 29, 6, darken(p["cap"], 0.25))
    elif kind == "crown_flat":
        c.hline(8, 40, 1, "ink")
        c.hline(8, 40, 2, "ink")
        c.hline(9, 39, 3, "ash")
        c.hline(9, 39, 4, "cinnabar")
        c.rect(20, 5, 28, 6, "ink")
        c.hline(21, 27, 5, "cinnabar")
        for x in (9, 10, 38, 39):
            for y in range(5, 12):
                c.set(x, y, "bone" if y % 2 == 0 else mix("bone", "ash", 0.45))
    elif kind == "cloth_cap":
        c.rect(16, 3, 32, 9, mix("ash", "bone", 0.35))
        c.hline(16, 32, 3, mix("ash", "bone", 0.55))
        c.hline(16, 32, 9, mix("ash", "bone", 0.12))
        c.hline(17, 31, 6, mix("ash", "bone", 0.28))
        c.set(32, 10, mix("ash", "bone", 0.20))
    elif kind == "general_cap":
        c.rect(18, 2, 30, 8, p["cap"])
        c.hline(18, 30, 8, p["cap_band"])
        c.hline(19, 29, 2, lighten(p["cap"], 0.22))
        c.hline(18, 30, 7, darken(p["cap"], 0.25))
        c.rect(23, 0, 24, 2, "cinnabar")
        c.set(23, 0, mix("cinnabar", "bone", 0.40))
        c.set(24, 1, darken("cinnabar", 0.30))


def _portrait_beard(c: Canvas, p: dict, spec: dict) -> None:
    kind = spec.get("beard")
    if not kind:
        return
    if kind == "moustache":
        c.hline(20, 23, 23, p["hair"])
        c.hline(25, 28, 23, p["hair"])
        c.set(20, 24, p["hair"])
        c.set(28, 24, p["hair"])
        c.hline(23, 25, 27, p["hair"])
        return
    if kind == "long_white":
        rows = ((28, 18, 30), (29, 17, 31), (30, 17, 31), (31, 17, 31),
                (32, 17, 31), (33, 18, 30), (34, 18, 30), (35, 19, 29),
                (36, 20, 28), (37, 21, 27), (38, 22, 26))
        tone = p["hair"]
        shade = mix(p["hair"], "hair_grey", 0.55)
    elif kind == "long_dark":
        rows = ((28, 21, 27), (29, 20, 28), (30, 20, 28), (31, 20, 28),
                (32, 21, 27), (33, 21, 27), (34, 22, 26), (35, 22, 26),
                (36, 23, 25))
        tone = p["hair"]
        shade = darken(p["hair"], 0.30)
    else:
        rows = ((28, 20, 28), (29, 20, 28), (30, 21, 27), (31, 21, 27),
                (32, 22, 26))
        tone = p["hair"]
        shade = darken(p["hair"], 0.25)
    for y, x0, x1 in rows:
        c.hline(x0, x1, y, tone)
        c.set(x1, y, shade)
    c.hline(rows[0][1] + 1, rows[0][2] - 1, rows[0][0], mix(tone, "bone", 0.25))
    c.hline(21, 27, 27, tone)              # join the moustache
    c.set(20, 27, tone)
    c.set(28, 27, tone)


def _portrait_accessory(c: Canvas, p: dict, spec: dict) -> None:
    kind = spec.get("accessory")
    if kind == "sword":
        c.line(35, 47, 29, 36, p["sheath"])
        c.line(36, 47, 30, 36, p["grip"])
        c.line(37, 47, 31, 36, p["grip"])
        c.line(29, 40, 33, 41, p["guard"])
        c.line(30, 41, 34, 42, p["guard"])
        c.set(30, 36, p["guard"])
        c.set(37, 47, mix(p["sheath"], "bone", 0.35))
    elif kind == "zither":
        c.line(12, 47, 7, 29, p["wood"])
        c.line(13, 47, 8, 29, p["wood_light"])
        c.line(14, 47, 9, 29, p["sheath"])
        for y in range(31, 47, 3):
            c.set(9, y, p["string"])
        c.set(8, 30, p["guard"])
        c.set(7, 30, p["wood_light"])
    elif kind == "staff":
        c.vline(42, 6, 47, p["wood"])
        c.vline(43, 6, 47, p["wood_light"])
        c.rect(41, 4, 43, 6, p["wood"])
        c.set(41, 4, p["wood_light"])
        c.hline(40, 41, 47, p["wood"])
    elif kind == "bag":
        c.rect(27, 44, 33, 47, "clay")
        c.hline(27, 33, 44, "bone")
        c.vline(27, 44, 47, darken("clay", 0.40))
        c.vline(33, 44, 47, darken("clay", 0.40))


def _portrait(name: str, pspec: dict) -> Canvas:
    base = SPRITE_SPECS[pspec["base"]]
    p = pal(base)
    c = Canvas(48, 48)
    _portrait_torso(c, p, pspec)
    _portrait_ears(c, p)
    _portrait_neck(c, p)
    _portrait_head(c, p, pspec)
    _portrait_headgear(c, p, pspec)
    _portrait_beard(c, p, pspec)
    _portrait_accessory(c, p, pspec)
    c.outline("ink")
    return c


def build_portraits() -> dict[str, Canvas]:
    """Render the eight dialogue busts."""
    return {name: _portrait(name, pspec) for name, pspec in PORTRAIT_SPECS.items()}

def build_pointer() -> Canvas:
    """An 8x8 bone arrow: a solid triangle pointing right, nothing else."""
    c = Canvas(8, 8)
    for y, width in ((1, 1), (2, 3), (3, 5), (4, 5), (5, 3), (6, 1)):
        c.hline(1, width, y, "bone")
    return c


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

SPRITE_FRAMES = ("down_idle", "down_step", "left_idle", "left_step",
                 "right_idle", "right_step", "up_idle", "up_step")

EXPECTED_SPRITES = ("jingke", "gaojianli", "goutu", "tianguang", "taizidan",
                    "fanyuqi", "qinwuyang", "qinwang", "xiawuju", "guard")

EXPECTED_PORTRAITS = ("jingke", "gaojianli", "taizidan", "qinwuyang", "qinwang",
                      "xiawuju", "fanyuqi", "tianguang")


def _distance(a: tuple, b: tuple) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def seam_score(img: Image.Image, vertical: bool) -> tuple[float, float]:
    """Return (edge difference, worst interior difference) for one axis.

    A tile copy joins its own first row/column, so the edge pair (15, 0) is
    exactly what a viewer sees at the join.  Comparing that against the worst
    ordinary neighbouring pair inside the tile says whether the join can be
    spotted.
    """
    w, h = img.size
    px = img.load()
    if vertical:
        edge = sum(_distance(px[15, y], px[0, y]) for y in range(h)) / h
        interior = max(
            sum(_distance(px[x, y], px[x + 1, y]) for y in range(h)) / h
            for x in range(0, 14)
        )
    else:
        edge = sum(_distance(px[x, 15], px[x, 0]) for x in range(w)) / w
        interior = max(
            sum(_distance(px[x, y], px[x, y + 1]) for x in range(w)) / w
            for y in range(0, 14)
        )
    return edge, interior


def verify_tiles(sheet: Canvas, data: dict) -> list[str]:
    problems: list[str] = []
    img = sheet.img
    if img.size != (COLS * TILE, ROWS * TILE):
        problems.append(f"tiles.png is {img.size}, expected {COLS * TILE}x{ROWS * TILE}")
    if img.mode != "RGBA":
        problems.append(f"tiles.png mode {img.mode}, expected RGBA")
    alpha = img.getchannel("A")
    if alpha.getextrema() != (255, 255):
        problems.append("tiles.png contains transparent pixels (must be fully opaque)")
    if data.get("tileSize") != TILE or data.get("columns") != COLS or data.get("rows") != ROWS:
        problems.append("tiles.json header is wrong")
    names = data.get("tiles", {})
    missing = [n for n in REQUIRED_TILES if n not in names]
    if missing:
        problems.append(f"tiles.json is missing required names: {missing}")
    if len(names) != len(TILES):
        problems.append(f"tiles.json has {len(names)} names, sheet has {len(TILES)} tiles")
    indices = list(names.values())
    if len(set(indices)) != len(indices):
        problems.append("tiles.json has duplicate indices")
    if any(not (0 <= i < COLS * ROWS) for i in indices):
        problems.append("tiles.json has an index outside 0..39")
    if set(indices) != set(range(COLS * ROWS)):
        problems.append("tiles.json does not map every slot")

    # seams
    tile_imgs = {}
    for index, (name, _fn) in enumerate(TILES):
        box = ((index % COLS) * TILE, (index // COLS) * TILE,
               (index % COLS) * TILE + TILE, (index // COLS) * TILE + TILE)
        tile_imgs[name] = img.crop(box)
    worst = []
    for name in SEAMLESS_TILES:
        edge_v, inner_v = seam_score(tile_imgs[name], vertical=True)
        edge_h, inner_h = seam_score(tile_imgs[name], vertical=False)
        worst.append((max(edge_v, edge_h), name, edge_v, inner_v, edge_h, inner_h))
        if edge_v > inner_v + 4 or edge_h > inner_h + 4:
            problems.append(f"tile {name}: seam {edge_v:.1f}/{edge_h:.1f} exceeds interior {inner_v:.1f}/{inner_h:.1f}")
    worst.sort(reverse=True)
    print("  seams (ground tiles): worst edge/interior difference")
    for edge, name, ev, iv, eh, ih in worst[:5]:
        print(f"    {name:<12} vertical {ev:5.1f} vs {iv:5.1f}   horizontal {eh:5.1f} vs {ih:5.1f}")

    # distinctness
    pal_names = [name for name, _fn in TILES]
    flat = {name: tile_imgs[name].tobytes() for name in pal_names}
    pairs = []
    for i, a in enumerate(pal_names):
        for b in pal_names[i + 1:]:
            data_a, data_b = flat[a], flat[b]
            diff = 0
            for k in range(0, len(data_a), 4):
                diff += (abs(data_a[k] - data_b[k])
                         + abs(data_a[k + 1] - data_b[k + 1])
                         + abs(data_a[k + 2] - data_b[k + 2]))
            mean = diff / (TILE * TILE)
            if mean < 40:
                pairs.append((mean, a, b))
    pairs.sort()
    if pairs and pairs[0][0] < 8:
        problems.append(f"tiles too similar: {pairs[0][1]} / {pairs[0][2]} mean {pairs[0][0]:.1f}")
    print("  most similar tile pairs (mean RGB distance, 0..765):")
    for mean, a, b in pairs[:4]:
        print(f"    {a:<12} {b:<12} {mean:6.1f}")
    return problems


def verify_sprites(sprites: dict[str, Canvas]) -> list[str]:
    problems: list[str] = []
    names = sorted(sprites)
    if tuple(names) != tuple(sorted(EXPECTED_SPRITES)):
        problems.append(f"sprite set is {names}, expected {list(EXPECTED_SPRITES)}")
    print(f"  {'sheet':<12} {'size':>9}  frames  head-identical  idle/step diff  transparent")
    for name in EXPECTED_SPRITES:
        if name not in sprites:
            continue
        img = sprites[name].img
        if img.size != (16 * 8, 24):
            problems.append(f"{name}.png is {img.size}, expected 128x24")
        head_ok, diffs = True, []
        for pair, start in (("down", 0), ("left", 2), ("right", 4), ("up", 6)):
            idle = img.crop((start * 16, 0, start * 16 + 16, 24))
            step = img.crop(((start + 1) * 16, 0, (start + 1) * 16 + 16, 24))
            a, b = idle.load(), step.load()
            for y in range(0, 9):
                for x in range(16):
                    if a[x, y] != b[x, y]:
                        head_ok = False
            diff = sum(1 for y in range(24) for x in range(16) if a[x, y] != b[x, y])
            diffs.append(diff)
            if diff == 0:
                problems.append(f"{name} {pair}: idle and step are identical")
            if diff > 90:
                problems.append(f"{name} {pair}: idle/step differ by {diff} px, too much for a bob")
            # feet must reach the bottom row
            if not any(b[x, 23][3] > 0 for x in range(16)):
                problems.append(f"{name} {pair}: no opaque pixel on the bottom row (feet)")
        if not head_ok:
            problems.append(f"{name}: head rows change between idle and step")
        if img.getchannel("A").getextrema()[0] != 0:
            problems.append(f"{name}.png has no transparent background")
        print(f"  {name:<12} {img.size[0]:>4d}x{img.size[1]:<4d}  {len(SPRITE_FRAMES):>5d}  "
              f"{str(head_ok):>14s}  {str(diffs):>15s}  {img.getchannel('A').getextrema()[0] == 0!s:>10s}")
    return problems


def verify_portraits(portraits: dict[str, Canvas]) -> list[str]:
    problems: list[str] = []
    print(f"  {'bust':<12} {'size':>9}  opaque%  luminance range")
    for name in EXPECTED_PORTRAITS:
        if name not in portraits:
            problems.append(f"portrait {name} missing")
            continue
        img = portraits[name].img
        if img.size != (48, 48):
            problems.append(f"portraits/{name}.png is {img.size}, expected 48x48")
        if img.getchannel("A").getextrema()[0] != 0:
            problems.append(f"portraits/{name}.png has no transparent background")
        pixels = [img.getpixel((x, y)) for y in range(48) for x in range(48)
                  if img.getpixel((x, y))[3] > 0]
        if not pixels:
            problems.append(f"portraits/{name}.png is empty")
            continue
        lum = [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in pixels]
        coverage = 100.0 * len(pixels) / (48 * 48)
        if not 25 <= coverage <= 85:
            problems.append(f"portraits/{name}.png covers {coverage:.0f}% of the cell")
        if max(lum) - min(lum) < 90:
            problems.append(f"portraits/{name}.png is low contrast ({max(lum) - min(lum):.0f})")
        print(f"  {name:<12} {img.size[0]:>4d}x{img.size[1]:<4d} {coverage:6.1f}   "
              f"{min(lum):3.0f}..{max(lum):3.0f}")
    return problems


def verify_pointer(pointer: Canvas) -> list[str]:
    problems: list[str] = []
    img = pointer.img
    if img.size != (8, 8):
        problems.append(f"pointer.png is {img.size}, expected 8x8")
    if img.getchannel("A").getextrema()[0] != 0:
        problems.append("pointer.png has no transparent background")
    data = img.tobytes()
    opaque = [tuple(data[k:k + 4]) for k in range(0, len(data), 4) if data[k + 3] > 0]
    colours = set(opaque)
    if colours != {colour("bone")}:
        problems.append(f"pointer.png should only use bone, found {colours}")
    print(f"  pointer.png  8x8, {len(colours)} colour, {len(opaque)} opaque px")
    return problems


# ---------------------------------------------------------------------------
# Preview sheets for eyeballing the art (written to artifacts/check/)
# ---------------------------------------------------------------------------


def checkerboard(w: int, h: int, cell: int = 8) -> Image.Image:
    img = Image.new("RGBA", (w, h), (58, 58, 62, 255))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if ((x // cell) + (y // cell)) % 2 == 0:
                px[x, y] = (74, 74, 78, 255)
    return img


def check_tile_sheet(sheet: Canvas) -> None:
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    sheet.upscale(8).save(CHECK_DIR / "tiles_x8.png")
    # 4x4 repeats of the ground tiles, so seams and tiling are obvious
    names = SEAMLESS_TILES
    scale, per_row, pad = 4, 6, 8
    block = TILE * 4 * scale
    cols = per_row
    rows = (len(names) + cols - 1) // cols
    canvas = Image.new("RGBA", (cols * (block + pad) + pad, rows * (block + pad) + pad),
                       (30, 30, 32, 255))
    tile_imgs = {}
    for index, (name, _fn) in enumerate(TILES):
        box = ((index % COLS) * TILE, (index // COLS) * TILE,
               (index % COLS) * TILE + TILE, (index // COLS) * TILE + TILE)
        tile_imgs[name] = sheet.img.crop(box)
    for i, name in enumerate(names):
        cx = pad + (i % cols) * (block + pad)
        cy = pad + (i // cols) * (block + pad)
        tile = tile_imgs[name]
        block_img = Image.new("RGBA", (TILE * 4, TILE * 4))
        for ty in range(4):
            for tx in range(4):
                block_img.alpha_composite(tile, (tx * TILE, ty * TILE))
        canvas.paste(block_img.resize((block, block), Image.NEAREST), (cx, cy))
    canvas.save(CHECK_DIR / "tiles_repeat_x4.png")


def check_sprites(sprites: dict[str, Canvas]) -> None:
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    scale, gap = 8, 8
    for part, names in (("a", CHARACTERS[:5]), ("b", CHARACTERS[5:])):
        width = 16 * 8 * scale + 2 * gap
        height = len(names) * (24 * scale + gap) + gap
        canvas = checkerboard(width, height, cell=16)
        for i, name in enumerate(names):
            big = sprites[name].upscale(scale)
            canvas.alpha_composite(big, (gap, gap + i * (24 * scale + gap)))
        canvas.save(CHECK_DIR / f"sprites_{part}_x8.png")


def check_portraits(portraits: dict[str, Canvas]) -> None:
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    scale, gap, cols = 4, 8, 4
    names = list(EXPECTED_PORTRAITS)
    rows = (len(names) + cols - 1) // cols
    cell = 48 * scale
    canvas = checkerboard(cols * (cell + gap) + gap, rows * (cell + gap) + gap, cell=12)
    for i, name in enumerate(names):
        big = portraits[name].upscale(scale)
        x = gap + (i % cols) * (cell + gap)
        y = gap + (i // cols) * (cell + gap)
        canvas.alpha_composite(big, (x, y))
    canvas.save(CHECK_DIR / "portraits_x4.png")


def check_pointer(pointer: Canvas) -> None:
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    big = checkerboard(8 * 16 + 16, 8 * 16 + 16, cell=8)
    big.alpha_composite(pointer.upscale(16), (8, 8))
    big.save(CHECK_DIR / "pointer_x16.png")


SCENE_KEY = {
    ".": "palace_floor", "l": "lacquer_red", "#": "palace_wall", "|": "pillar",
    "D": "doorway", "C": "curtain", "L": "lattice", "B": "banner_qin",
    "b": "banner_yan", "T": "torch", "t": "table", "m": "mat", "z": "zhu",
    "w": "wineskin", "s": "scroll", "S": "stairs", "r": "reed", "~": "water",
    "_": "water_bank", ",": "dirt", "g": "grass", "G": "grass_alt",
    "Y": "tree", "W": "wood_floor", "V": "wood_wall", "n": "snow_path",
    "N": "snow", "k": "wall_stone", "o": "dirt_road", "e": "gravel",
    "q": "curtain_qin", "R": "roof", "x": "blood", "v": "void", "c": "stone",
    "d": "sand", "h": "roof_ridge", "u": "wood_beam",
}

SCENE_PALACE = (
    "############",
    "#BDTBCTLBB##",
    "#..........#",
    "#.l..T...l.#",
    "#..........#",
    "#.m..t.z...#",
    "#..........#",
)

SCENE_RIVER = (
    "nnnnnnnnnnnn",
    "nYYYY,,,YYnn",
    "n,,gg,g,,,~n",
    "n,g,,,g,,,r~",
    "n,g,,,g,,,r~",
    "_,_,__,_~_r~",
    "~~~~~~~~~~~~",
)


def render_scene(rows: tuple[str, ...], cast: tuple[tuple[str, int, int], ...]) -> Image.Image:
    """Composite tiles and sprites into a 1x scene preview."""
    sheet_img = build_tiles().img
    index = {name: i for i, (name, _fn) in enumerate(TILES)}
    scene = Image.new("RGBA", (len(rows[0]) * TILE, len(rows) * TILE), (0, 0, 0, 255))
    for y, row in enumerate(rows):
        for x, key in enumerate(row):
            name = SCENE_KEY[key]
            i = index[name]
            box = ((i % COLS) * TILE, (i // COLS) * TILE,
                   (i % COLS) * TILE + TILE, (i // COLS) * TILE + TILE)
            scene.alpha_composite(sheet_img.crop(box), (x * TILE, y * TILE))
    sprites = build_sprites()
    for name, tx, ty in cast:
        sprite = sprites[name].img.crop((0, 0, 16, 24))
        scene.alpha_composite(sprite, (tx * TILE, (ty + 1) * TILE - 24))
    return scene


def check_scenes() -> None:
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    palace = render_scene(
        SCENE_PALACE,
        (("jingke", 2, 3), ("qinwang", 9, 3), ("xiawuju", 6, 5), ("guard", 10, 5)),
    )
    palace.resize((palace.width * 4, palace.height * 4), Image.NEAREST).save(
        CHECK_DIR / "scene_palace_x4.png"
    )
    river = render_scene(
        SCENE_RIVER,
        (("taizidan", 3, 2), ("jingke", 8, 3), ("gaojianli", 6, 4), ("tianguang", 10, 4)),
    )
    river.resize((river.width * 4, river.height * 4), Image.NEAREST).save(
        CHECK_DIR / "scene_river_x4.png"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def save(img: Image.Image, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")
    return path.stat().st_size


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Week 8 pixel art assets.")
    parser.add_argument("--only", choices=("tiles", "sprites", "portraits", "ui"),
                        help="build only one group (for iteration)")
    parser.add_argument("--check", action="store_true",
                        help="also write 4x/8x previews to artifacts/check/")
    parser.add_argument("--no-verify", action="store_true", help="skip checks")
    args = parser.parse_args(argv)

    print("Week 8 pixel assets -- Jing Ke and the King of Qin")
    problems: list[str] = []
    files: list[tuple[str, Path, tuple[int, int]]] = []
    sheet = sprites = portraits = pointer = None

    if args.only in (None, "tiles"):
        sheet = build_tiles()
        size = save(sheet.img, TILES_PNG)
        data = tiles_json()
        TILES_JSON.parent.mkdir(parents=True, exist_ok=True)
        with TILES_JSON.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        files.append(("tiles.png", TILES_PNG, sheet.img.size))
        files.append(("tiles.json", TILES_JSON, (0, 0)))
        if not args.no_verify:
            problems += verify_tiles(sheet, data)
        if args.check:
            check_tile_sheet(sheet)

    if args.only in (None, "sprites"):
        sprites = build_sprites()
        for name in EXPECTED_SPRITES:
            path = SPRITE_DIR / f"{name}.png"
            save(sprites[name].img, path)
            files.append((path.name, path, sprites[name].img.size))
        if not args.no_verify:
            problems += verify_sprites(sprites)
        if args.check:
            check_sprites(sprites)

    if args.only in (None, "portraits"):
        portraits = build_portraits()
        for name in EXPECTED_PORTRAITS:
            path = PORTRAIT_DIR / f"{name}.png"
            save(portraits[name].img, path)
            files.append((path.name, path, portraits[name].img.size))
        if not args.no_verify:
            problems += verify_portraits(portraits)
        if args.check:
            check_portraits(portraits)

    if args.only in (None, "ui"):
        pointer = build_pointer()
        path = UI_DIR / "pointer.png"
        save(pointer.img, path)
        files.append((path.name, path, pointer.img.size))
        if not args.no_verify:
            problems += verify_pointer(pointer)
        if args.check:
            check_pointer(pointer)

    print("\nfiles:")
    total = 0
    for name, path, size in files:
        if path.suffix == ".json":
            print(f"  {name:<18} {path.stat().st_size:>7d} B   {path.parent.relative_to(ROOT)}")
        else:
            total += path.stat().st_size
            print(f"  {name:<18} {size[0]:>3d}x{size[1]:<3d} {path.stat().st_size:>7d} B   "
                  f"{path.parent.relative_to(ROOT)}")
    print(f"  PNG bytes: {total} ({total / 1024:.1f} KiB)")

    if args.check:
        if sheet is not None and sprites is not None:
            check_scenes()
        print(f"  previews in {CHECK_DIR.relative_to(ROOT)}/")

    if problems:
        print("\nPROBLEMS:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    if not args.no_verify:
        print("\nall checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

