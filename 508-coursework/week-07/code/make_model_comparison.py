"""Side-by-side figure of the two 3D routes: the script-built model and the
Hunyuan3D image-to-3D mesh.

Panels appear only when their render exists, so the figure can be rebuilt at any
point while a service result is still missing.

Usage: python code/make_model_comparison.py
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
RENDERS = ROOT / "artifacts" / "renders"
OUT = ROOT / "generated" / "model_route_comparison.png"

BG = (22, 23, 26)
INK = (238, 238, 234)
DIM = (162, 164, 167)
ACCENT = (198, 129, 66)

PANELS = [
    ("A. BUILT BY SCRIPT IN BLENDER",
     "code/build_ak47_type2.py, 870 mm from the sources",
     RENDERS / "01_right_side.png",
     "parts modelled one by one; the Type 2 features are explicit, the surface is synthetic"),
    ("B. HUNYUAN3D 2, IMAGE-TO-3D",
     "one photograph in, an untextured shell out, 57 s",
     RENDERS / "hunyuan_side.png",
     "right silhouette from the photo, one fused surface, no parts, no texture"),
]

FOOTER = [
    "A is assembled from primitives, so the parts and their seams are the argument; B is recovered from a single photograph,",
    "so it carries the silhouette and invents the far side. B has no inside: no bore, no magazine body, no springs.",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in (r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
                 r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"):
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
    panels = [p for p in PANELS if p[2].exists()]
    if not panels:
        print("no renders found")
        return 1
    print(f"panels: {[p[0] for p in panels]}")

    margin, pad = 52, 30
    cols = len(panels)
    cell_w = 900 if cols < 3 else 640
    cell_h = 620 if cols < 3 else 470
    width = margin * 2 + cell_w * cols + pad * (cols - 1)
    height = 206 + cell_h + 120 + 96

    sheet = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(sheet)
    title, sub, label, small = font(44, True), font(24), font(25, True), font(19)

    draw.text((margin, 34), "Step 3 - two routes to the same object", font=title, fill=INK)
    draw.text((margin, 90), "Same studio, same camera angle; the only difference is how the geometry was made.",
              font=sub, fill=DIM)

    x = margin
    for heading, caption, path, note in panels:
        draw.text((x, 132), heading, font=label, fill=ACCENT)
        draw.text((x, 166), caption, font=small, fill=DIM)
        img = Image.open(path).convert("RGB")
        img.thumbnail((cell_w, cell_h), Image.LANCZOS)
        sheet.paste(img, (x + (cell_w - img.width) // 2, 200))
        y = 200 + cell_h + 10
        for line in wrap(draw, note, small, cell_w):
            draw.text((x, y), line, font=small, fill=DIM)
            y += 24
        x += cell_w + pad

    y = height - 84
    for line in FOOTER:
        draw.text((margin, y), line, font=small, fill=DIM)
        y += 26

    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT, "PNG")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
