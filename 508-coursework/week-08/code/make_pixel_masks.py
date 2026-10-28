"""Draw the eleven speakers as 48x48 pixel portraits, painted like 京剧脸谱.

    python code/make_pixel_masks.py

Opera convention is the guide, not a reproduction of a real role: a red face for
the wronged general, a white face with black eye-frames for the king, a small
white nose-patch for the clown roles, a child's cheeks for 秦舞阳. Everything is
drawn with flat primitives at the final 48x48 size, so the pixels are honest:
there is no downscaling anywhere.

The three faces the game never shows full-size (狗屠, 郎中, 蒙嘉) are drawn too,
because they are clickable on the stage.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

S = 48
OUT = Path(__file__).resolve().parent.parent / "game" / "assets" / "portraits"

# palette, kept small on purpose
BLACK = (24, 20, 20, 255)
WHITE = (244, 240, 230, 255)
RED = (176, 46, 40, 255)
DEEP_RED = (126, 30, 28, 255)
BLUE = (52, 84, 150, 255)
PALE_BLUE = (150, 178, 214, 255)
GREEN = (58, 104, 78, 255)
PALE_GREEN = (170, 196, 176, 255)
SKIN = (236, 198, 160, 255)
PALE = (244, 226, 206, 255)
GREY = (150, 146, 140, 255)
BROWN = (110, 78, 52, 255)
GOLD = (222, 176, 74, 255)
PINK = (222, 138, 128, 255)

# slug: (face, pattern, accent, headwear colour, beard, role marks)
FACES: dict[str, dict] = {
    "jingke":     dict(face=PALE_BLUE, pattern=BLACK, accent=BLUE, hat=BLACK, beard=None,
                       brows="flame", mark="crescent"),
    "gaojianli":  dict(face=PALE, pattern=BLACK, accent=GREEN, hat=GREEN, beard=None,
                       brows="thin", mark=None),
    "goutu":      dict(face=WHITE, pattern=BLACK, accent=BROWN, hat=BROWN, beard="stubble",
                       brows="thick", mark="nose"),
    "tianguang":  dict(face=PALE, pattern=BLACK, accent=GREY, hat=GREY, beard="long",
                       brows="white", mark=None),
    "taizidan":   dict(face=PALE, pattern=BLACK, accent=RED, hat=GOLD, beard=None,
                       brows="thin", mark="dot"),
    "fanyuqi":    dict(face=RED, pattern=BLACK, accent=DEEP_RED, hat=BLACK, beard="long_grey",
                       brows="flame", mark="scar"),
    "qinwuyang":  dict(face=PALE, pattern=BLACK, accent=RED, hat=BLACK, beard=None,
                       brows="child", mark="cheeks"),
    "qinwang":    dict(face=WHITE, pattern=BLACK, accent=RED, hat=BLACK, beard=None,
                       brows="slanted", mark="sovereign"),
    "xiawuju":    dict(face=PALE, pattern=BLACK, accent=GREY, hat=GREY, beard="goatee",
                       brows="thin", mark="nose"),
    "guard":      dict(face=PALE, pattern=BLACK, accent=BLUE, hat=BLACK, beard=None,
                       brows="thick", mark="helmet"),
    "mengjia":    dict(face=WHITE, pattern=BLACK, accent=BROWN, hat=BROWN, beard="goatee",
                       brows="slanted", mark="nose"),
}


def draw_face(spec: dict) -> Image.Image:
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    face, pattern, accent = spec["face"], spec["pattern"], spec["accent"]

    # shoulders / robe, so the head does not float
    d.rectangle([6, 38, 41, 47], fill=accent)
    d.rectangle([20, 38, 27, 47], fill=face)

    # head
    d.ellipse([9, 6, 38, 41], fill=face)

    # headwear: a band across the forehead, plus a crown for the king
    d.rectangle([9, 6, 38, 13], fill=spec["hat"])
    if spec["mark"] == "sovereign":
        d.rectangle([13, 1, 34, 7], fill=BLACK)
        d.rectangle([21, 0, 26, 3], fill=RED)
        d.rectangle([13, 1, 34, 2], fill=GOLD)
    elif spec["mark"] == "helmet":
        d.rectangle([8, 2, 39, 9], fill=BLACK)
        d.rectangle([22, 0, 25, 4], fill=RED)
    elif spec["mark"] == "dot":
        d.rectangle([23, 15, 24, 18], fill=RED)

    # eyebrows
    brow_y = 19
    if spec["brows"] == "flame":
        d.line([(14, brow_y + 2), (19, brow_y - 2), (23, brow_y + 1)], fill=pattern, width=2)
        d.line([(33, brow_y + 2), (28, brow_y - 2), (24, brow_y + 1)], fill=pattern, width=2)
    elif spec["brows"] == "thick":
        d.rectangle([13, brow_y - 1, 21, brow_y + 1], fill=pattern)
        d.rectangle([26, brow_y - 1, 34, brow_y + 1], fill=pattern)
    elif spec["brows"] == "thin":
        d.line([(14, brow_y), (21, brow_y - 1)], fill=pattern, width=1)
        d.line([(26, brow_y - 1), (33, brow_y)], fill=pattern, width=1)
    elif spec["brows"] == "white":
        d.rectangle([13, brow_y - 1, 21, brow_y], fill=WHITE)
        d.rectangle([26, brow_y - 1, 34, brow_y], fill=WHITE)
    elif spec["brows"] == "child":
        d.line([(15, brow_y), (20, brow_y)], fill=pattern, width=1)
        d.line([(27, brow_y), (32, brow_y)], fill=pattern, width=1)
    else:  # slanted, the schemer
        d.line([(13, brow_y + 2), (21, brow_y - 2)], fill=pattern, width=2)
        d.line([(34, brow_y + 2), (26, brow_y - 2)], fill=pattern, width=2)

    # painted eye-frames first (the loudest 脸谱 feature), then the eyes on top
    if face in (RED, WHITE, PALE_BLUE):
        d.rectangle([13, 21, 22, 28], fill=pattern)
        d.rectangle([26, 21, 35, 28], fill=pattern)
    d.rectangle([15, 23, 20, 26], fill=WHITE)
    d.rectangle([27, 23, 32, 26], fill=WHITE)
    d.rectangle([16, 23, 19, 26], fill=BLACK)
    d.rectangle([28, 23, 31, 26], fill=BLACK)
    d.rectangle([17, 24, 18, 25], fill=WHITE)
    d.rectangle([29, 24, 30, 25], fill=WHITE)

    # nose; the clown roles wear the little white patch right over it
    if spec["mark"] == "nose":
        d.rectangle([20, 26, 27, 31], fill=WHITE)
        d.rectangle([22, 27, 25, 29], fill=(252, 250, 244, 255))
    else:
        d.rectangle([23, 27, 24, 30], fill=SKIN)

    # mouth: a comic line for the clowns, a red one for everyone else
    if spec["mark"] == "nose":
        d.rectangle([21, 33, 26, 34], fill=BLACK)
    else:
        d.rectangle([21, 34, 26, 35], fill=RED if face != RED else BLACK)

    # cheeks
    if spec["mark"] == "cheeks":
        d.rectangle([12, 29, 15, 31], fill=PINK)
        d.rectangle([32, 29, 35, 31], fill=PINK)

    # marks
    if spec["mark"] == "crescent":
        d.rectangle([23, 14, 24, 16], fill=WHITE)
    if spec["mark"] == "scar":
        d.line([(12, 20), (17, 33)], fill=WHITE, width=1)

    # beard
    if spec["beard"] == "long":
        d.rectangle([18, 36, 29, 45], fill=GREY)
    elif spec["beard"] == "long_grey":
        d.rectangle([18, 37, 29, 44], fill=GREY)
    elif spec["beard"] == "goatee":
        d.rectangle([22, 36, 25, 41], fill=GREY)
    elif spec["beard"] == "stubble":
        d.rectangle([16, 36, 31, 38], fill=BLACK)

    return im


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, spec in FACES.items():
        draw_face(spec).save(OUT / f"{slug}.png")
        print("  ", slug)
    print(f"wrote {len(FACES)} pixel portraits to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
