"""Probe several ways of calling the Hunyuan3D spaces, to find one that works
without a Hugging Face token. Prints the error of each attempt instead of
stopping, so the failure modes end up in the record.

Usage: python code/hunyuan3d_probe.py
"""

from __future__ import annotations

import pathlib
import time

from gradio_client import Client, handle_file

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMAGE = ROOT / "artifacts" / "hunyuan" / "input.png"

ATTEMPTS = [
    ("tencent/Hunyuan3D-2", "/shape_generation", dict(
        caption=None, image=None, mv_image_front=None, mv_image_back=None,
        mv_image_left=None, mv_image_right=None, steps=30, guidance_scale=5.0,
        seed=1234, octree_resolution=256, check_box_rembg=True, num_chunks=8000,
        randomize_seed=False)),
    ("tencent/Hunyuan3D-2", "/generation_all", dict(
        caption=None, image=None, mv_image_front=None, mv_image_back=None,
        mv_image_left=None, mv_image_right=None, steps=20, guidance_scale=5.0,
        seed=1234, octree_resolution=192, check_box_rembg=True, num_chunks=8000,
        randomize_seed=False)),
    ("tencent/Hunyuan3D-2mini-Turbo", "/shape_generation", dict(
        caption=None, image=None, mv_image_front=None, mv_image_back=None,
        mv_image_left=None, mv_image_right=None, steps=8, guidance_scale=5.0,
        seed=1234, octree_resolution=192, check_box_rembg=True, num_chunks=8000,
        randomize_seed=False)),
]


def main() -> int:
    for space, endpoint, params in ATTEMPTS:
        print("=" * 70)
        print(f"{space} {endpoint}")
        started = time.time()
        try:
            client = Client(space, verbose=False)
            kwargs = dict(params)
            kwargs["image"] = handle_file(str(IMAGE))
            result = client.predict(api_name=endpoint, **kwargs)
            print(f"OK after {time.time() - started:.0f}s: {str(result)[:500]}")
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED after {time.time() - started:.0f}s: {type(exc).__name__}: {str(exc)[:400]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
