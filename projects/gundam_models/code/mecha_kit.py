"""Shared kit for the mecha builds: primitives, materials, studio and camera.

Everything is in metres, Z up, and the model faces -Y (so the default camera at
-Y looks at its front). A build script imports this, assembles parts into a
`PARTS` dict, then calls `finish(...)` to render and export.

Design rule for this project: no traced polygons and no downloaded meshes. Each
part is a box, a tapered box, an extruded outline or a cylinder, sized from the
reference photographs by eye and by counting head-heights. What is being matched
is silhouette, proportion, colour separation and the presence of the right
equipment, not surface detail.
"""

from __future__ import annotations

import math
import os
import pathlib

import bmesh
import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
# The DSH sandbox lets Blender write only inside the session workspace, so renders
# and exports are written there and copied into this project afterwards by
# code/collect.ps1. Override MECHA_OUT if that ever changes.
OUT = pathlib.Path(os.environ.get(
    "MECHA_OUT",
    r"G:\workspeace\dhg508-workspace\508-coursework\week-07\artifacts\gundam"))
ART = OUT
RENDERS = OUT / "renders"
MODEL = OUT / "model"

PARTS: dict[str, list[bpy.types.Object]] = {}
MATS: dict[str, bpy.types.Material] = {}


# ---------------------------------------------------------------- materials
def material(name, base, metallic=0.0, roughness=0.4, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if coat and "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    return mat


def emission(name, colour, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*colour, 1.0)
    emit.inputs["Strength"].default_value = strength
    mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def make_materials(palette: dict[str, tuple]) -> None:
    for name, spec in palette.items():
        base, metallic, rough, coat = (list(spec) + [0.0, 0.4, 0.0])[:4]
        MATS[name] = material(name, base, metallic, rough, coat)
    MATS["eye"] = emission("Eye", (1.0, 0.30, 0.55), 12.0)


# ---------------------------------------------------------------- primitives
def _bevel(obj, width):
    if width > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = width
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return obj


def add(group: str, obj: bpy.types.Object) -> bpy.types.Object:
    PARTS.setdefault(group, []).append(obj)
    return obj


def armor(group, name, size, loc, mat, rot=(0, 0, 0), bevel=0.006,
          top_scale=(1.0, 1.0), top_shift=(0.0, 0.0)):
    """A box whose top face can be tapered and shifted - the workhorse for plate armour."""
    sx, sy, sz = (v / 2 for v in size)
    tx, ty = top_scale
    dx, dy = top_shift
    verts = [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx * tx + dx, -sy * ty + dy, sz), (sx * tx + dx, -sy * ty + dy, sz),
        (sx * tx + dx, sy * ty + dy, sz), (-sx * tx + dx, sy * ty + dy, sz),
    ]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.materials.append(MATS[mat])
    return add(group, _bevel(obj, bevel))


def prism(group, name, outline, thickness, loc, mat, rot=(0, 0, 0), bevel=0.004):
    """Extrude a 2D outline in the XZ plane along Y - skirts, shields, funnels."""
    verts = [(x, -thickness / 2, z) for x, z in outline]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [list(range(len(outline)))])
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    obj.data.materials.append(MATS[mat])
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, thickness, 0)})
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    return add(group, _bevel(obj, bevel))


def cyl(group, name, radius, depth, loc, mat, rot=(0, 0, 0), verts=24, bevel=0.002):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(MATS[mat])
    return add(group, _bevel(obj, bevel))


def ball(group, name, radius, loc, mat, scale=(1, 1, 1), segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=segments,
                                         ring_count=max(8, segments // 2))
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(MATS[mat])
    return add(group, obj)


def vent(group, name, size, loc, mat, count=4, rot=(0, 0, 0), vertical=False):
    """A grille: `count` thin slats filling `size`."""
    sx, sy, sz = size
    step = (sy if not vertical else sz) / count
    for i in range(count):
        offset = -((sy if not vertical else sz) / 2) + step * (i + 0.5)
        pos = (loc[0], loc[1] + (0 if vertical else offset), loc[2] + (offset if vertical else 0))
        armor(group, f"{name}_{i}", (sx, step * 0.42 if not vertical else sy, sz * 0.86 if not vertical else step * 0.42),
              pos, mat, rot=rot, bevel=0.001)


def mirror(group: str, objects: list[bpy.types.Object], suffix: str = "_mirror") -> list[bpy.types.Object]:
    """Duplicate a list of objects across X = 0."""
    out = []
    for obj in objects:
        clone = obj.copy()
        clone.data = obj.data.copy()
        bpy.context.collection.objects.link(clone)
        clone.name = obj.name + suffix
        clone.location = (-obj.location.x, obj.location.y, obj.location.z)
        clone.rotation_euler = (obj.rotation_euler.x, -obj.rotation_euler.y, -obj.rotation_euler.z)
        clone.scale = (obj.scale.x, obj.scale.y, obj.scale.z)
        for mod in clone.modifiers:
            if mod.type == "BEVEL":
                mod.width = mod.width
        PARTS.setdefault(group, []).append(clone)
        out.append(clone)
    return out


# ---------------------------------------------------------------- scene
def clear() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def studio(floor_z: float = 0.0) -> None:
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, floor_z))
    floor = bpy.context.object
    floor.name = "Floor"
    floor.data.materials.append(material("Floor", (0.035, 0.036, 0.040), 0.0, 0.55))
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 6, 6), rotation=(math.pi / 2, 0, 0))
    wall = bpy.context.object
    wall.name = "Wall"
    wall.data.materials.append(material("Wall", (0.030, 0.031, 0.035), 0.0, 0.6))

    def area(name, loc, energy, size, colour=(1.0, 0.96, 0.92)):
        light = bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.size = size
        light.color = colour
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        target = bpy.data.objects.new(f"{name}_target", None)
        bpy.context.collection.objects.link(target)
        target.location = (0, 0, 1.0)
        track = obj.constraints.new("TRACK_TO")
        track.target = target
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

    area("Key", (-2.4, -3.0, 3.2), 1600.0, 3.0)
    area("Fill", (3.0, -2.2, 1.4), 420.0, 4.0, (0.80, 0.86, 1.0))
    area("Rim", (0.8, 3.2, 2.6), 900.0, 2.5, (1.0, 0.92, 0.84))
    area("Top", (0.0, 0.0, 4.2), 500.0, 3.0)

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.012, 0.013, 0.016, 1.0)
    bg.inputs["Strength"].default_value = 0.4


def setup_render(samples: int, res: tuple[int, int], gpu: bool = True) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    if gpu:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for backend in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = backend
                prefs.refresh_devices()
                if any(d.type not in {"CPU", "NONE"} for d in prefs.devices):
                    for device in prefs.devices:
                        device.use = device.type != "CPU"
                    scene.cycles.device = "GPU"
                    break
            except TypeError:
                continue
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.15


def camera_view(azimuth: float, elevation: float, distance: float, lens: float,
                target=(0.0, 0.0, 1.0)) -> bpy.types.Object:
    cam = bpy.data.objects.get("Camera")
    if cam is None:
        cam_data = bpy.data.cameras.new("Camera")
        cam = bpy.data.objects.new("Camera", cam_data)
        bpy.context.collection.objects.link(cam)
        bpy.context.scene.camera = cam
    cam.data.lens = lens
    az, el = math.radians(azimuth), math.radians(elevation)
    cam.location = (target[0] + distance * math.cos(el) * math.sin(az),
                    target[1] - distance * math.cos(el) * math.cos(az),
                    target[2] + distance * math.sin(el))
    empty = bpy.data.objects.get("CameraTarget")
    if empty is None:
        empty = bpy.data.objects.new("CameraTarget", None)
        bpy.context.collection.objects.link(empty)
    empty.location = target
    for constraint in list(cam.constraints):
        cam.constraints.remove(constraint)
    track = cam.constraints.new("TRACK_TO")
    track.target = empty
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    return cam


def render(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {path}")


def export(name: str) -> None:
    MODEL.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for group in PARTS.values():
        for obj in group:
            obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODEL / f"{name}.glb"), export_format="GLB",
                              use_selection=True, export_apply=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(MODEL / f"{name}.blend"))
    print(f"EXPORTED {MODEL / name}")
