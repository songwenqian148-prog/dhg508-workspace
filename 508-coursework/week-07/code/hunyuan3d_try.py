"""Image-to-3D with Tencent's Hunyuan3D 2, through the official Hugging Face
Space that runs the open weights (`tencent/Hunyuan3D-2`).

Why the Space and not Tencent Cloud: the Cloud API (hunyuan.tencentcloudapi.com)
needs a SecretId/SecretKey pair and none exists in this workspace. The Space is
the same weights, free, no key.

Two calls are tried, in this order:
  1. /generation_all - shape *and* texture in one go
  2. /shape_generation - shape only, no texture, if (1) fails

`caption` must be None, not "": passing an empty string makes the Space raise a
bare NameError. That cost one wasted run and is recorded in the log.

Usage:
    python code/hunyuan3d_try.py [--seed 1234] [--steps 30] [--octree 256]
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
SPACE = "tencent/Hunyuan3D-2"


def prepare_input() -> pathlib.Path:
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "input.png"
    if not dest.exists():
        with Image.open(SOURCE) as im:
            im = im.convert("RGBA")
            canvas = Image.new("RGB", im.size, (255, 255, 255))
            canvas.paste(im, mask=im.split()[3])
            canvas.save(dest, "PNG")
    print(f"input image: {dest.relative_to(ROOT)} ({dest.stat().st_size:,} bytes)")
    return dest


def normalise(value) -> str | None:
    """gradio_client returns either a path or a {'value': path, '__type__': ...} dict."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("value", "path", "name"):
            if isinstance(value.get(key), str):
                return value[key]
    if isinstance(value, (list, tuple)) and value:
        return normalise(value[0])
    return None


def copy_out(path, label: str, suffix: str = ".glb") -> dict | None:
    raw = normalise(path)
    if not raw:
        print(f"WARN {label}: no path in {str(path)[:120]}", file=sys.stderr)
        return None
    src = pathlib.Path(raw)
    if not src.exists():
        print(f"WARN {label}: {src} does not exist", file=sys.stderr)
        return None
    dest = OUT / f"ak47_hunyuan3d_{label}{suffix}"
    shutil.copyfile(src, dest)
    print(f"saved {dest.relative_to(ROOT)} ({dest.stat().st_size:,} bytes)")
    return {"file": dest.relative_to(ROOT).as_posix(), "bytes": dest.stat().st_size}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--octree", type=int, default=256)
    ap.add_argument("--shape-only", action="store_true", help="skip /generation_all, which errors on this Space")
    args = ap.parse_args()

    from gradio_client import Client, handle_file

    image = prepare_input()
    client = Client(SPACE, verbose=False)
    common = dict(
        caption=None,
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
    )

    outputs: dict[str, dict] = {}
    used = ""
    stats: dict | str | None = None
    started = time.time()

    print(f"/generation_all: steps={args.steps} octree={args.octree} seed={args.seed}", flush=True)
    tried_all = not args.shape_only
    if tried_all:
        try:
            result = client.predict(**common, api_name="/generation_all")
            shape_file, textured_file, _html, stats, seed = result
            outputs["shape"] = copy_out(shape_file, "shape")
            outputs["textured"] = copy_out(textured_file, "textured")
            used = "/generation_all"
        except Exception as exc:  # noqa: BLE001
            print(f"/generation_all failed: {type(exc).__name__}: {str(exc)[:300]}", file=sys.stderr)
    if "shape" not in outputs or not outputs.get("shape"):
        print("/shape_generation: shape only, no texture", flush=True)
        result = client.predict(**common, api_name="/shape_generation")
        shape_file, _html, stats, seed = result
        outputs["shape"] = copy_out(shape_file, "shape")
        used = "/shape_generation"
    elapsed = time.time() - started
    outputs = {k: v for k, v in outputs.items() if v}
    meta = {
        "tool": "Tencent Hunyuan3D 2 (open weights, official Hugging Face Space)",
        "space": SPACE,
        "endpoint_used": used,
        "cost_usd": 0.0,
        "key_used": "none (anonymous Space call)",
        "input": (OUT / "input.png").relative_to(ROOT).as_posix(),
        "input_source": SOURCE.relative_to(ROOT).as_posix(),
        "settings": {
            "steps": args.steps,
            "guidance_scale": 5.0,
            "seed": args.seed,
            "octree_resolution": args.octree,
            "remove_background": True,
            "num_chunks": 8000,
        },
        "elapsed_seconds": round(elapsed, 1),
        "mesh_stats": stats if isinstance(stats, dict) else str(stats),
        "outputs": outputs,
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT / "hunyuan3d_run.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {(OUT / 'hunyuan3d_run.json').relative_to(ROOT)}")
    print(f"saved outputs: {list(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
