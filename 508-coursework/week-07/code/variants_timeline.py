"""Four stages of the AK-47 receiver, side by side on a timeline.

The modelling tied back to the history: the same rifle at 1949 (Type 1, stamped),
1951 (Type 2, milled), 1955 (Type 3, lightened milled) and 1959 (AKM, stamped
again). The Type 2 geometry is borrowed from `build_ak47_type2.py` with runpy and
copied; each copy then gets only the changes the sources name for that date.

The four rows stand at the same height on purpose: stacked vertically, the top
row sat closer to the key light and read as a different material.

Run headless:
    blender -b --python code/variants_timeline.py -- --poster
    blender -b --python code/variants_timeline.py -- --frames --samples 22 --gpu
"""

from __future__ import annotations

import argparse
import math
import pathlib
import runpy
import sys

import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "code" / "build_ak47_type2.py"
ART = ROOT / "artifacts"
RENDERS = ART / "renders"

_model = runpy.run_path(str(BUILD), run_name="variants_module")
build_scene = _model["build_scene"]
add_studio = _model["add_studio"]
setup_render = _model["setup_render"]
frame_camera = _model["frame_camera"]
render_still = _model["render_still"]
PARTS = _model["PARTS"]
MATS = _model["MATS"]
box = _model["box"]
cylinder = _model["cylinder"]

# year, name, receiver, weight, key, x offset
STAGES = [
    ("1949", "Type 1", "stamped receiver", "4.3 kg", "t1", -1.575),
    ("1951", "Type 2", "milled receiver", "4.3 kg*", "t2", -0.525),
    ("1955", "Type 3", "milled, lightened", "3.47 kg", "t3", 0.525),
    ("1959", "AKM", "stamped again", "3.1 kg", "akm", 1.575),
]

TOTAL = 180
APPEAR = {"t1": 14, "t2": 44, "t3": 74, "akm": 104}


def clone_assembly(suffix: str, x_offset: float) -> dict[str, bpy.types.Object]:
    root = bpy.data.objects["AK47_Root"]
    clones: dict[str, bpy.types.Object] = {}
    for group in PARTS.values():
        for obj in group:
            if obj.type != "MESH":
                continue
            clone = obj.copy()
            clone.data = obj.data.copy()
            bpy.context.collection.objects.link(clone)
            clone.name = f"{obj.name}_{suffix}"
            clone.parent = None
            world = root.location + obj.location
            clone.location = (world.x + x_offset, world.y, world.z)
            clones[obj.name] = clone
    return clones


def drop(clones: dict, *names: str) -> None:
    for name in names:
        obj = clones.pop(name, None)
        if obj:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data.users == 0:
                bpy.data.meshes.remove(data)


def add_rivets(suffix: str, x_offset: float) -> None:
    for side, y in (("L", 0.0160), ("R", -0.0160)):
        for row, z in enumerate((-0.020, 0.014)):
            for i in range(6):
                cylinder(f"Rivet_{suffix}_{side}_{row}_{i}", 0.0032, 0.0032,
                         (0.035 + i * 0.041 + x_offset, y, z), "steel_dark",
                         rot=(math.pi / 2, 0, 0), verts=10)


def add_weld(suffix: str, x_offset: float) -> None:
    for side, y in (("L", 0.0162), ("R", -0.0162)):
        cylinder(f"Weld_{suffix}_{side}", 0.0018, 0.255, (0.145 + x_offset, y, -0.030),
                 "steel_dark", rot=(0, math.pi / 2, 0), verts=8)


def make_stamped(suffix: str, clones: dict, x_offset: float) -> None:
    drop(clones, "Lightening_cut_L", "Lightening_cut_R",
         "Stock_socket", "Stock_socket_pin_0", "Stock_socket_pin_1")
    add_rivets(suffix, x_offset)
    add_weld(suffix, x_offset)


def make_type1(clones: dict, x_offset: float) -> None:
    make_stamped("t1", clones, x_offset)
    drop(clones, "Muzzle_nut")
    cylinder("Brake_t1", 0.0130, 0.034, (0.600 + x_offset, 0, 0.0), "gunmetal", verts=24)
    for i, x in enumerate((0.592, 0.600, 0.608)):
        box(f"Brake_slot_t1_{i}", (0.0035, 0.027, 0.010), (x + x_offset, 0, 0.006), "bore", bevel=0.0004)
    for side, y in (("L", 0.0160), ("R", -0.0160)):
        box(f"Grip_seam_t1_{side}", (0.060, 0.0015, 0.0022), (0.088 + x_offset, y, -0.085),
            "steel_dark", bevel=0.0003)


def make_type3(clones: dict, x_offset: float) -> None:
    for side in ("L", "R"):
        cut = clones.get(f"Lightening_cut_{side}")
        if cut:
            cut.scale = (1.28, cut.scale.y, 1.15)
            cut.location = (cut.location.x + 0.020, cut.location.y, cut.location.z)
    drop(clones, "Sling_loop_front")
    box("Sling_loop_t3", (0.018, 0.007, 0.024), (0.508 + x_offset, 0.020, -0.010), "steel_dark", bevel=0.0016)
    box("Bayonet_lug_t3", (0.030, 0.016, 0.026), (0.566 + x_offset, 0, -0.028), "gunmetal", bevel=0.0018)
    barrel = clones.get("Barrel")
    if barrel:
        barrel.scale = (1.0, barrel.scale.y * 0.90, barrel.scale.z * 0.90)


def make_akm(clones: dict, x_offset: float) -> None:
    make_stamped("akm", clones, x_offset)
    drop(clones, "Muzzle_nut", "Sling_loop_front")
    cylinder("Brake_akm", 0.0122, 0.032, (0.604 + x_offset, 0, 0.0), "gunmetal", verts=24)
    box("Brake_slant_akm", (0.026, 0.024, 0.022), (0.612 + x_offset, 0, 0.004), "gunmetal",
        bevel=0.0012, rot=(0, math.radians(20), 0))
    box("Sling_loop_akm", (0.018, 0.007, 0.024), (0.508 + x_offset, 0.020, -0.010), "steel_dark", bevel=0.0016)
    box("Bayonet_lug_akm", (0.030, 0.016, 0.026), (0.566 + x_offset, 0, -0.028), "gunmetal", bevel=0.0018)


def label(name, body, location, size, material, camera, align="CENTER"):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.size = size
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    obj.data.materials.append(material)
    obj.rotation_euler = (camera.location - obj.location).to_track_quat("Z", "Y").to_euler()
    return obj


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


def build(scene_mats):
    year_mat, dim_mat = scene_mats
    timed = []

    def register(obj, key):
        timed.append((obj, APPEAR[key]))

    for year, name, receiver, weight, key, x in STAGES:
        before = set(bpy.data.objects)
        clones = clone_assembly(key, x)
        if key == "t1":
            make_type1(clones, x)
        elif key == "t3":
            make_type3(clones, x)
        elif key == "akm":
            make_akm(clones, x)
        for obj in [o for o in bpy.data.objects if o not in before]:
            register(obj, key)

    # horizontal timeline: a rule under the four rifles with a tick per stage
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.194, 0.0, -0.315))
    rule = bpy.context.object
    rule.name = "Timeline_rule"
    rule.scale = (3.95, 0.004, 0.004)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rule.data.materials.append(MATS["steel_dark"])
    for year, name, receiver, weight, key, x in STAGES:
        cylinder(f"Tick_{key}", 0.0085, 0.006, (x + 0.194, 0.0, -0.315), "steel_dark",
                 rot=(math.pi / 2, 0, 0), verts=12)

    camera = bpy.data.objects["Camera"]
    for year, name, receiver, weight, key, x in STAGES:
        head = label(f"Year_{key}", f"{year}   {name}", Vector((x + 0.194, 0, -0.395)), 0.055,
                     year_mat, camera)
        sub = label(f"Sub_{key}", f"{receiver}  ·  {weight}", Vector((x + 0.194, 0, -0.470)), 0.032,
                    dim_mat, camera)
        register(head, key)
        register(sub, key)

    label("Title", "AK-47 receiver, 1949 - 1959", Vector((-1.34, 0, 0.545)), 0.070, year_mat, camera)
    label("Subtitle", "one rifle, four production stages; only the parts the sources name as changed",
          Vector((-1.34, 0, 0.455)), 0.032, dim_mat, camera)

    summary = label("Summary", "stamped 1949  ->  milled 1951  ->  lightened 1955  ->  stamped 1959",
                    Vector((0.194, 0, -0.590)), 0.030, dim_mat, camera)
    summary.hide_render = True
    summary.hide_viewport = True
    summary.keyframe_insert("hide_render", frame=1)
    summary.keyframe_insert("hide_viewport", frame=1)
    summary.hide_render = False
    summary.hide_viewport = False
    summary.keyframe_insert("hide_render", frame=APPEAR["akm"] + 8)
    summary.keyframe_insert("hide_viewport", frame=APPEAR["akm"] + 8)

    for obj, start in timed:
        obj.hide_render = True
        obj.hide_viewport = True
        obj.keyframe_insert("hide_render", frame=1)
        obj.keyframe_insert("hide_viewport", frame=1)
        obj.hide_render = False
        obj.hide_viewport = False
        obj.keyframe_insert("hide_render", frame=start)
        obj.keyframe_insert("hide_viewport", frame=start)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--poster", action="store_true")
    ap.add_argument("--frames", action="store_true")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=800)
    args = ap.parse_args(argv)

    build_scene()
    add_studio()
    for name, (loc, energy, size) in {
        # broad soft sources centred on the row: a small light at one end made
        # the near row brighter than the far row, which read as different metal
        "Key": ((0.20, -3.00, 2.10), 2600.0, 5.0),
        "Fill": ((0.20, 3.60, 1.20), 600.0, 6.0),
        "Rim": ((0.20, 2.20, 1.90), 700.0, 3.5),
        "Top": ((0.20, 0.0, 2.60), 0.0, 1.4),
    }.items():
        light = bpy.data.objects.get(name)
        if light:
            light.location = loc
            light.data.energy = energy
            light.data.size = size

    setup_render(args.samples, (args.width, args.height), gpu=args.gpu)
    bpy.context.scene.view_settings.exposure = -1.05
    bpy.data.objects["Backdrop"].location.z = -1.10

    camera = frame_camera(-6, 7, 6.90, 55, target=(0.194, 0, -0.05))

    year_mat = emission("Year label", (1.0, 0.93, 0.80), 2.8)
    dim_mat = emission("Sub label", (0.72, 0.72, 0.70), 1.6)

    # hide the original rifle; only the four copies are shown
    for group in PARTS.values():
        for obj in group:
            obj.hide_render = True
            obj.hide_viewport = True

    build((year_mat, dim_mat))

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL
    scene.render.fps = 30

    if args.poster:
        scene.frame_set(TOTAL - 6)
        scene.render.resolution_x = 2200
        scene.render.resolution_y = 920
        render_still(RENDERS / "08_receiver_timeline.png")

    if args.frames:
        out_dir = ART / "frames_timeline"
        out_dir.mkdir(parents=True, exist_ok=True)
        scene.render.resolution_x = args.width
        scene.render.resolution_y = args.height
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.compression = 15
        for frame in range(1, TOTAL + 1):
            scene.frame_set(frame)
            scene.render.filepath = str(out_dir / f"timeline_{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"TIMELINE {frame}/{TOTAL}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
