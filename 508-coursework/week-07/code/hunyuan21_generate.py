"""Image-to-3D with Tencent Hunyuan3D 2.1 (shape + texture) on the official
Hugging Face Space, anonymous, no key.

2.1's endpoint has no `caption` argument, which is what made 2.0's
`/generation_all` return a bare NameError; this is the call that works.

Usage: python code/hunyuan21_generate.py [--seed 1234] [--steps 30] [--octree 256]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import time

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "hunyuan"
SOURCE = ROOT / "sources" / "raw" / "AK-47_type_II_noBG.png.webp"
SPACE = "tencent/Hunyuan3D-2.1"


def normalise(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("value", "path", "name"):
            if isinstance(value.get(key), str):
                return value[key]
    if isinstance(value, (list, tuple)) and value:
        return normalise(value[0])
    return None


def copy_out(value, label: str) -> dict | None:
    raw = normalise(value)
    if not raw:
        print(f"WARN {label}: no path in {str(value)[:120]}", file=sys.stderr)
        return None
    src = pathlib.Path(raw)
    if not src.exists():
        print(f"WARN {label}: {src} does not exist", file=sys.stderr)
        return None
    dest = OUT / f"ak47_hunyuan21_{label}{src.suffix or '.glb'}"
    shutil.copyfile(src, dest)
    print(f"saved {dest.relative_to(ROOT)} ({dest.stat().st_size:,} bytes)")
    return {"file": dest.relative_to(ROOT).as_posix(), "bytes": dest.stat().st_size}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--octree", type=int, default=256)
    args = ap.parse_args()

    from gradio_client import Client, handle_file

    OUT.mkdir(parents=True, exist_ok=True)
    image = OUT / "input.png"
    if not image.exists():
        with Image.open(SOURCE) as im:
            im = im.convert("RGBA")
            canvas = Image.new("RGB", im.size, (255, 255, 255))
            canvas.paste(im, mask=im.split()[3])
            canvas.save(image, "PNG")

    client = Client(SPACE, verbose=False)
    started = time.time()
    print(f"{SPACE} /generation_all: steps={args.steps} octree={args.octree} seed={args.seed}", flush=True)
    result = client.predict(
        image=handle_file(str(image)),
        mv_image_front=None,
        mv_image_back=None,
        mv_image_left=None,
        mv_image_right=None,
        steps=args.steps,
        guidance_scale=5.0,
        seed=args.seed,
        octree_resolution=args.octree,
        check_box_rembg=True,
        num_chunks=8000,
        randomize_seed=False,
        api_name="/generation_all",
    )
    elapsed = time.time() - started
    print(f"returned after {elapsed:.0f}s")

    shape_file, textured_file, _html, stats, seed = result
    outputs = {
        "shape": copy_out(shape_file, "shape"),
        "textured": copy_out(textured_file, "textured"),
    }
    outputs = {k: v for k, v in outputs.items() if v}

    meta = {
        "tool": "Tencent Hunyuan3D 2.1 (open weights, official Hugging Face Space)",
        "space": SPACE,
        "endpoint": "/generation_all (shape + texture)",
        "cost_usd": 0.0,
        "key_used": "none (anonymous Space call)",
        "input": image.relative_to(ROOT).as_posix(),
        "input_source": SOURCE.relative_to(ROOT).as_posix(),
        "settings": {"steps": args.steps, "guidance_scale": 5.0, "seed": args.seed,
                     "octree_resolution": args.octree, "remove_background": True},
        "elapsed_seconds": round(elapsed, 1),
        "mesh_stats": stats if isinstance(stats, dict) else str(stats),
        "outputs": outputs,
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "hunyuan21_run.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved:", list(outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
