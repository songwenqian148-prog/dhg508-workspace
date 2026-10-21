"""Try to get a *textured* mesh out of a Hunyuan3D Space that will answer an
anonymous call.

`tencent/Hunyuan3D-2` gives a good untextured shape via /shape_generation, but
its /generation_all endpoint raises a bare NameError, and 2.1 refuses anonymous
calls ("requested GPU duration 270s is larger than the maximum allowed"). This
script walks the public forks of the 2.0 Space, reads each one's real endpoint
signature, and calls /generation_all with exactly the arguments it declares.

Usage: python code/hunyuan_texture_probe.py
"""

from __future__ import annotations

import pathlib
import time

from gradio_client import Client, handle_file

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMAGE = ROOT / "artifacts" / "hunyuan" / "input.png"
OUT = ROOT / "artifacts" / "hunyuan"

SPACES = [
    "dawood/Hunyuan3D-2",
    "MMD-Coder/Hunyuan3D-2.0",
    "aimpowerment/Hunyuan3D-2",
    "shixiangbupt/Hunyuan3D-2",
    "Dhdb/Hunyuan3D-2",
]

VALUES = {
    "image": None,  # filled per call
    "caption": None,
    "mv_image_front": None,
    "mv_image_back": None,
    "mv_image_left": None,
    "mv_image_right": None,
    "steps": 30,
    "guidance_scale": 5.0,
    "seed": 1234,
    "octree_resolution": 256,
    "check_box_rembg": True,
    "num_chunks": 8000,
    "randomize_seed": False,
}


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


def main() -> int:
    for space in SPACES:
        print("=" * 70)
        print(space)
        try:
            client = Client(space, verbose=False)
            api = client.view_api(return_format="dict", print_info=False)
            endpoint = api.get("named_endpoints", {}).get("/generation_all")
            if not endpoint:
                print("  no /generation_all endpoint")
                continue
            names = [p.get("parameter_name") for p in endpoint.get("parameters", [])]
            kwargs = {name: VALUES[name] for name in names if name in VALUES}
            kwargs["image"] = handle_file(str(IMAGE))
            print(f"  calling with: {sorted(kwargs)}")
            started = time.time()
            result = client.predict(**kwargs, api_name="/generation_all")
            elapsed = time.time() - started
            print(f"  OK after {elapsed:.0f}s: {str(result)[:200]}")
            saved = []
            for i, value in enumerate(result):
                raw = normalise(value)
                if raw and str(raw).endswith(".glb"):
                    src = pathlib.Path(raw)
                    if src.exists():
                        dest = OUT / f"ak47_hunyuan3d_alt_{space.split('/')[0]}_{i}.glb"
                        dest.write_bytes(src.read_bytes())
                        saved.append((str(dest.relative_to(ROOT)), dest.stat().st_size))
            print(f"  saved: {saved}")
            if saved:
                return 0
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {type(exc).__name__}: {str(exc)[:240]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
