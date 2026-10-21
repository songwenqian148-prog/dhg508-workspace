"""Render an imported GLB in the same studio as the hand-built model, so the two
can be compared side by side without a change of lighting or camera.

Usage:
    blender -b --python code/render_glb.py -- --glb artifacts/hunyuan/ak47_hunyuan3d_textured.glb \
        --prefix hunyuan --samples 64

Writes artifacts/renders/<prefix>_side.png, <prefix>_three_quarter.png,
<prefix>_top.png, and prints the bounding box in millimetres.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
RENDERS = ROOT / "artifacts" / "renders"


def material(name, base, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def clear() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path: pathlib.Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before]


def bbox(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
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


def studio(centre: Vector, size: float) -> None:
    bpy.ops.mesh.primitive_plane_add(size=size * 6, location=(centre.x, centre.y, centre.z - size * 0.45))
    floor = bpy.context.object
    floor.data.materials.append(material("Backdrop", (0.020, 0.020, 0.022), 0.0, 0.80))
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(centre.x, centre.y + size * 1.6, centre.z + size),
                                     rotation=(math.pi / 2, 0, 0))
    wall = bpy.context.object
    wall.data.materials.append(material("Wall", (0.020, 0.020, 0.022), 0.0, 0.80))

    target = bpy.data.objects.new("Target", None)
    bpy.context.collection.objects.link(target)
    target.location = centre

    def area(name, offset, energy, area_size, colour=(1.0, 0.96, 0.92)):
        light = bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.size = area_size
        light.color = colour
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = centre + Vector(offset) * size
        track = obj.constraints.new("TRACK_TO")
        track.target = target
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

    area("Key", (0.8, -1.0, 0.9), 220.0, 1.4)
    area("Fill", (0.1, 1.1, 0.5), 60.0, 1.8, (0.82, 0.88, 1.0))
    area("Rim", (-0.8, 0.4, 0.7), 140.0, 0.9, (1.0, 0.92, 0.84))
    area("Top", (0.2, 0.0, 1.2), 50.0, 1.2)


def camera(centre: Vector, size: float, azimuth: float, elevation: float, lens: float = 65.0):
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.data.lens = lens
    distance = size * 1.9
    az, el = math.radians(azimuth), math.radians(elevation)
    cam.location = centre + Vector((distance * math.cos(el) * math.sin(az),
                                   -distance * math.cos(el) * math.cos(az),
                                   distance * math.sin(el)))
    target = bpy.data.objects["Target"]
    track = cam.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam


def setup(samples: int, resolution: tuple[int, int]) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.refresh_devices()
        for device in prefs.devices:
            device.use = device.type != "CPU"
        scene.cycles.device = "GPU"
    except Exception:  # noqa: BLE001
        scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.010, 0.011, 0.013, 1.0)
    bg.inputs["Strength"].default_value = 0.35


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", required=True)
    ap.add_argument("--prefix", default="imported")
    ap.add_argument("--samples", type=int, default=64)
    args = ap.parse_args(argv)

    glb = pathlib.Path(args.glb)
    if not glb.is_absolute():
        glb = ROOT / glb
    clear()
    objects = import_glb(glb)
    meshes = [o for o in objects if o.type == "MESH"]
    if not meshes:
        print("no meshes imported", file=sys.stderr)
        return 1

    lo, hi = bbox(meshes)
    size_vec = hi - lo
    centre = (lo + hi) / 2
    size = max(size_vec.x, size_vec.y, size_vec.z)
    print(f"imported {len(meshes)} meshes")
    print(f"bbox mm: x={size_vec.x*1000:.0f} y={size_vec.y*1000:.0f} z={size_vec.z*1000:.0f}")
    print(f"vertices={sum(len(o.data.vertices) for o in meshes):,} "
          f"triangles={sum(len(o.data.polygons) for o in meshes):,}")

    studio(centre, size)
    setup(args.samples, (1800, 1200))
    RENDERS.mkdir(parents=True, exist_ok=True)

    for name, (az, el, lens) in {
        f"{args.prefix}_side": (0, 3, 65),
        f"{args.prefix}_three_quarter": (34, 12, 58),
        f"{args.prefix}_top": (0, 78, 70),
    }.items():
        camera(centre, size, az, el, lens)
        bpy.context.scene.render.filepath = str(RENDERS / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
