"""Build the control check figure: the same request with and without the
researched clauses, at matched seeds.

Rows: the control prompt (words alone) at seed 11 and 23.
      the treatment prompt (control + three researched clauses) at seed 11 and 61.

Seed 11 appears in both rows, so the seed is held constant there; the only
variable is the added words.

Usage: python code/make_control_check.py
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "generated"
OUT = GEN / "control_check.png"

CELL_W, CELL_H = 640, 480
PAD = 26
BG = (22, 23, 26)
INK = (238, 238, 234)
DIM = (160, 162, 165)
ACCENT = (198, 129, 66)

ROWS = [
    ("CONTROL - words alone", "a photograph of an AK-47 rifle, side view, whole rifle, plain background", [
        (GEN / "final" / "baseline" / "seed11.jpg", "seed 11"),
        (GEN / "a_words_only" / "seed23.png", "seed 23"),
    ], INK),
    ("TREATMENT - same prompt + wooden furniture + no scope", "…with a wooden stock and wooden handguard, no scope, side view, whole rifle, plain background", [
        (GEN / "final" / "researched" / "seed11_short_prompt.jpg", "seed 11  (matched)"),
        (GEN / "final" / "researched" / "wooden_stock.jpg", "seed 61"),
    ], ACCENT),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in (r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
                 r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"):
        if pathlib.Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> int:
    margin = 54
    width = 2 * CELL_W + 3 * PAD + 2 * margin
    height = 150 + 2 * (CELL_H + 96) + 40
    sheet = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(sheet)
    title, sub = font(42, True), font(23)
    row_font, status = font(24, True), font(20)

    draw.text((margin, 34), "Step 2 control check - same request, matched seeds", font=title, fill=INK)
    draw.text((margin, 88), "Left column seed 11 appears in both rows: the seed is held constant, only the researched words change.",
              font=sub, fill=DIM)

    y = 150
    for label, prompt, cells, colour in ROWS:
        draw.text((margin, y), label, font=row_font, fill=colour)
        draw.text((margin, y + 32), prompt, font=status, fill=DIM)
        x = margin
        for path, seed in cells:
            img = Image.open(path).convert("RGB")
            img.thumbnail((CELL_W, CELL_H), Image.LANCZOS)
            top = y + 66
            sheet.paste(img, (x + (CELL_W - img.width) // 2, top))
            draw.text((x + 8, top + CELL_H + 6), seed, font=status, fill=DIM)
            x += CELL_W + PAD
        y += CELL_H + 96

    GEN.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT, "PNG")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
