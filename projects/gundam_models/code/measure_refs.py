"""Measure the reference photographs: silhouette widths at heights.

The product shots are red/white figures on a black background, so a brightness
threshold gives the silhouette. The output is a table of widths as fractions of
the figure's height, which is what the build scripts are tuned against (head
unit, shoulder span, hip width, foot spread).

Usage: python code/measure_refs.py
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "sources" / "raw"
OUT = ROOT / "research" / "ref_measurements.json"

REFS = {
    "sazabi": "recovered_04.jpg",   # front view, full body
    "nu_gundam": "recovered_02.jpg",  # front view, full body
}


def measure(path: pathlib.Path) -> dict:
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((900, 900))
        arr = np.asarray(im).astype(int)

    # silhouette: anything clearly brighter than the black backdrop
    mask = arr.sum(axis=2) > 90
    # drop the watermark strip in the bottom-left corner
    mask[-40:, :120] = False
    ys, xs = np.where(mask)
    top, bottom = ys.min(), ys.max()
    left, right = xs.min(), xs.max()
    height = bottom - top + 1

    rows = []
    for frac in (0.02, 0.05, 0.10, 0.16, 0.24, 0.32, 0.40, 0.48, 0.56, 0.64, 0.72, 0.80, 0.88, 0.94, 0.98):
        y = int(top + frac * (height - 1))
        band = mask[max(0, y - 2):y + 3, :]
        cols = np.where(band.any(axis=0))[0]
        width = (cols.max() - cols.min() + 1) if len(cols) else 0
        rows.append({
            "from_top": round(frac, 2),
            "width_px": int(width),
            "width_over_height": round(width / height, 3),
        })

    return {
        "file": path.name,
        "px_height": int(height),
        "px_width": int(right - left + 1),
        "aspect": round((right - left + 1) / height, 3),
        "profile": rows,
    }


def main() -> int:
    results = {}
    for name, filename in REFS.items():
        path = RAW / filename
        if not path.exists():
            print(f"missing {path}")
            continue
        results[name] = measure(path)
        data = results[name]
        print(f"{name}: {data['file']}  h={data['px_height']}px  w/h={data['aspect']}")
        for row in data["profile"]:
            bar = "#" * int(row["width_over_height"] * 60)
            print(f"  {row['from_top']:.2f}  {row['width_over_height']:.3f}  {bar}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
