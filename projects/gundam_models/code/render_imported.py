"""Render an imported GLB in the mecha studio, scaled to figure height.

Used to look at the image-to-3D meshes next to the script-built ones: the mesh is
measused, scaled so its height is `--height` metres, dropped onto z = 0 and lit
with the same rig.

Usage:
    blender -b --python code/render_imported.py -- --glb <path> --name sazabi_ai \
        --views three_quarter,front --samples 48
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mecha_kit import RENDERS, camera_view, clear, render, setup_render, studio


def import_glb(path: pathlib.Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [o for o in bpy.data.objects if o not in before]


def bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            lo = Vector((min(lo.x, world.x), min(lo.y, world.y), min(lo.z, world.z)))
            hi = Vector((max(hi.x, world.x), max(hi.y, world.y), max(hi.z, world.z)))
    return lo, hi


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--views", default="three_quarter")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--height", type=float, default=1.90)
    ap.add_argument("--res", default="1000x1300")
    args = ap.parse_args(argv)

    glb = pathlib.Path(args.glb)
    clear()
    objects = import_glb(glb)
    meshes = [o for o in objects if o.type == "MESH"]
    lo, hi = bounds(meshes)
    size = hi - lo
    scale = args.height / size.z if size.z else 1.0
    centre = (lo + hi) / 2

    for obj in objects:
        if obj.parent is None:
            obj.location = (obj.location - centre) * scale
            obj.scale = obj.scale * scale
            obj.location.z += args.height / 2

    print(f"imported {len(meshes)} meshes, bbox {size.x:.3f} x {size.y:.3f} x {size.z:.3f}, scale {scale:.4f}")

    studio()
    width, height = (int(v) for v in args.res.split("x"))
    setup_render(args.samples, (width, height))

    views = {
        "front": (0, 3, 4.9, 60),
        "three_quarter": (30, 7, 4.9, 60),
        "side": (78, 3, 4.9, 60),
        "back": (168, 7, 4.9, 60),
    }
    for name in args.views.split(","):
        az, el, dist, lens = views[name]
        camera_view(az, el, dist, lens, target=(0, 0, 0.98))
        render(RENDERS / f"{args.name}_{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
