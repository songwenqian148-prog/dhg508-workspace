"""Image-to-3D for the mecha references, through the Hunyuan3D 2 Space.

An alternative to hand-blocking the figures: send the product photograph to the
open Hunyuan3D model and get a mesh back. Compared with the script-built figures
it keeps the silhouette and surface detail much better, and gives up articulation
and part separation - the opposite trade from `build_sazabi.py`.

Usage:
    python code/image_to_3d.py --ref sources/raw/recovered_04.jpg --name sazabi
    python code/image_to_3d.py --ref sources/raw/recovered_02.jpg --name nu_gundam
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import time

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(os.environ.get(
    "MECHA_OUT",
    r"G:\workspeace\dhg508-workspace\508-coursework\week-07\artifacts\gundam")) / "image_to_3d"
SPACE = "tencent/Hunyuan3D-2"


def prepare(ref: pathlib.Path, name: str) -> pathlib.Path:
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{name}_input.png"
    with Image.open(ref) as im:
        im = im.convert("RGB")
        # the references sit on black; a light grey pad keeps the model from
        # treating the frame edge as part of the figure
        canvas = Image.new("RGB", im.size, (235, 235, 235))
        arr = np.asarray(im).astype(int).sum(axis=2)
        mask = Image.fromarray(((arr > 90) * 255).astype("uint8"))
        canvas.paste(im, mask=mask)
        canvas.save(dest, "PNG")
    print(f"input: {dest} ({dest.stat().st_size:,} bytes)")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--octree", type=int, default=256)
    ap.add_argument("--seed", type=int, default=1234)
    args = ap.parse_args()

    from gradio_client import Client, handle_file

    ref = ROOT / args.ref
    image = prepare(ref, args.name)

    client = Client(SPACE, verbose=False)
    started = time.time()
    print(f"/generation_all on {SPACE}", flush=True)
    try:
        result = client.predict(
            caption=None, image=handle_file(str(image)),
            mv_image_front=None, mv_image_back=None, mv_image_left=None, mv_image_right=None,
            steps=args.steps, guidance_scale=5.0, seed=args.seed,
            octree_resolution=args.octree, check_box_rembg=True, num_chunks=8000,
            randomize_seed=False, api_name="/generation_all",
        )
        shape_file, textured_file, _html, stats, seed = result
        print("generation_all ok")
    except Exception as exc:  # noqa: BLE001
        print(f"/generation_all failed ({type(exc).__name__}: {str(exc)[:160]}), trying shape only")
        result = client.predict(
            caption=None, image=handle_file(str(image)),
            mv_image_front=None, mv_image_back=None, mv_image_left=None, mv_image_right=None,
            steps=args.steps, guidance_scale=5.0, seed=args.seed,
            octree_resolution=args.octree, check_box_rembg=True, num_chunks=8000,
            randomize_seed=False, api_name="/shape_generation",
        )
        shape_file, _html, stats, seed = result
        textured_file = None

    elapsed = time.time() - started
    saved = {}
    for label, value in (("shape", shape_file), ("textured", textured_file)):
        raw = value.get("value") if isinstance(value, dict) else value
        if not raw:
            continue
        src = pathlib.Path(raw)
        if not src.exists():
            print(f"missing {label}: {src}")
            continue
        dest = OUT / f"{args.name}_{label}.glb"
        shutil.copyfile(src, dest)
        saved[label] = {"file": str(dest), "bytes": dest.stat().st_size}
        print(f"saved {dest} ({dest.stat().st_size:,} bytes)")

    record = {
        "space": SPACE,
        "reference": str(ref),
        "input": str(image),
        "cost_usd": 0.0,
        "elapsed_seconds": round(elapsed, 1),
        "settings": {"steps": args.steps, "octree": args.octree, "seed": args.seed},
        "mesh_stats": stats if isinstance(stats, dict) else str(stats),
        "outputs": saved,
    }
    (OUT / f"{args.name}_run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"wrote {OUT / (args.name + '_run.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
