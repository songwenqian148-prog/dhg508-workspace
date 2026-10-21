"""Normalise an image-to-3D GLB into the repository and report what it contains.

The Hunyuan mesh arrives at an arbitrary scale (the 2.0 shape came out 1960 mm
long for a 870 mm rifle) and off-axis, so this script scales it to the published
overall length, centres it on the origin, drops it on z = 0, writes it to
model/, and prints the geometry facts that the write-up quotes: triangle count,
bounding box, whether the shell is closed, how many separate shells it has.

Usage:
    python code/prepare_hunyuan_asset.py artifacts/hunyuan/ak47_hunyuan3d_shape.glb ak47_hunyuan3d
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import trimesh

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = ROOT / "model"
OVERALL_LENGTH_M = 0.870


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("name", help="output stem, e.g. ak47_hunyuan3d")
    args = ap.parse_args()

    src = pathlib.Path(args.glb)
    if not src.is_absolute():
        src = ROOT / src
    scene = trimesh.load(src, force="scene")
    meshes = [g for g in scene.geometry.values() if isinstance(g, trimesh.Trimesh)]
    if not meshes:
        print("no triangle geometry in the file", file=sys.stderr)
        return 1

    mesh = trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]

    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    longest = float(max(size))
    scale = OVERALL_LENGTH_M / longest if longest else 1.0
    mesh.apply_scale(scale)

    # glTF is Y-up, so centre X and Z and drop the model onto y = 0; putting it
    # on z = 0 would leave half of it below the floor in a glTF viewer.
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)
    mesh.apply_translation((0, -mesh.bounds[0][1], 0))

    MODEL.mkdir(parents=True, exist_ok=True)
    dest = MODEL / f"{args.name}.glb"
    mesh.export(dest)
    print(f"wrote {dest.relative_to(ROOT)} ({dest.stat().st_size:,} bytes)")

    bodies = mesh.split(only_watertight=False)
    stats = {
        "source": src.relative_to(ROOT).as_posix(),
        "output": dest.relative_to(ROOT).as_posix(),
        "up_axis": "glTF Y-up; the mesh rests on y = 0",
        "vertices": int(len(mesh.vertices)),
        "triangles": int(len(mesh.faces)),
        "bbox_mm": [round(float(v) * 1000, 1) for v in mesh.extents],
        "scale_applied_to_reach_870mm": round(scale, 4),
        "watertight": bool(mesh.is_watertight),
        "shells": len(bodies),
        "volume_cm3": round(float(mesh.volume) * 1e6, 1) if mesh.is_watertight else None,
        "has_texture": bool(getattr(mesh.visual, "material", None) is not None and
                            getattr(mesh.visual.material, "baseColorTexture", None) is not None)
        if hasattr(mesh.visual, "material") else False,
    }
    (MODEL / f"{args.name}.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
