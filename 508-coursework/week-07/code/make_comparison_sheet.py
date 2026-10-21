"""Assemble the side-by-side comparison sheet required by step 2.

Left: the words-only baseline. Right: the image built from the sources.
Both are used exactly as the generator returned them (only converted to RGB for
the sheet). Labels, captions and the credit line are drawn here so the sheet can
be shown on its own in class.

Usage:
    python code/make_comparison_sheet.py
"""

from __future__ import annotations

import json
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "generated"
OUT = GEN / "comparison_sheet.png"

PAIR = {
    "left": {
        "file": GEN / "final" / "baseline" / "seed11.jpg",
        "label": "A. WORDS ALONE - no sources",
        "prompt": "a photograph of an AK-47 rifle, side view, whole rifle, plain background",
        "seed": 11,
    },
    "right": {
        "file": GEN / "final" / "researched" / "wooden_stock.jpg",
        "label": "B. FROM SOURCES - AK-47 Type 2, 1951-1955",
        "prompt": "a photograph of an AK-47 rifle with a wooden stock and wooden handguard, "
                  "no scope, side view, whole rifle, plain background",
        "seed": 61,
    },
}

WIDTH, HEIGHT = 2400, 1340
MARGIN = 60
GUTTER = 40
PANEL_W = (WIDTH - 2 * MARGIN - GUTTER) // 2
BG = (22, 23, 26)
INK = (236, 236, 232)
DIM = (166, 168, 170)
ACCENT = (198, 129, 66)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if pathlib.Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def main() -> int:
    sheet = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(sheet)

    title_font = font(58, bold=True)
    sub_font = font(30)
    label_font = font(30, bold=True)
    body_font = font(24)
    small_font = font(21)

    draw.text((MARGIN, 46), "Step 2 - the same request, with and without the sources",
              font=title_font, fill=INK)
    draw.text((MARGIN, 118),
              "Both images: Pollinations text-to-image, 1024x768 requested (returned 886x665), cost 0",
              font=sub_font, fill=DIM)

    panel_top = 190
    image_h = 620
    for i, side in enumerate(("left", "right")):
        entry = PAIR[side]
        x = MARGIN + i * (PANEL_W + GUTTER)
        draw.text((x, panel_top), entry["label"], font=label_font,
                  fill=ACCENT if side == "right" else INK)

        img = Image.open(entry["file"]).convert("RGB")
        scale = min(PANEL_W / img.width, image_h / img.height)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        img_x = x + (PANEL_W - img.width) // 2
        img_y = panel_top + 56
        sheet.paste(img, (img_x, img_y))
        draw.rectangle([img_x - 1, img_y - 1, img_x + img.width, img_y + img.height],
                       outline=(60, 61, 64), width=1)

        y = img_y + img.height + 24
        draw.text((x, y), "prompt (verbatim)", font=small_font, fill=DIM)
        y += 30
        for line in wrap(draw, entry["prompt"], body_font, PANEL_W):
            draw.text((x, y), line, font=body_font, fill=INK)
            y += 32
        y += 10
        draw.text((x, y), f"seed {entry['seed']}  -  file {entry['file'].relative_to(ROOT).as_posix()}",
                  font=small_font, fill=DIM)

    footer_y = HEIGHT - 250
    draw.line([(MARGIN, footer_y), (WIDTH - MARGIN, footer_y)], fill=(60, 61, 64), width=2)
    footer = [
        "Left: what the generator draws from the words 'AK-47' alone - black plastic furniture, an invented optic and",
        "mount, an invented case, the rifle cropped, no milled receiver, no 1950s feature anywhere.",
        "Right: the same request plus the two facts the sources establish (wooden furniture, no optic) - the wood and the",
        "absence of a scope are right, and the generator still invents a rail, an optic mount and a hand, and crops the muzzle.",
        "Item-by-item answer to step 2: research/comparison.md.",
    ]
    y = footer_y + 22
    for i, line in enumerate(footer):
        draw.text((MARGIN, y), line, font=small_font if i < 4 else body_font,
                  fill=DIM if i < 4 else INK)
        y += 34

    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT, "PNG")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
