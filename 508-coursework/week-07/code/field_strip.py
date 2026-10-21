"""Field-strip animation: the AK-47 Type 2 comes apart into labelled groups and
goes back together.

This is a separate Blender script rather than another flag on
`build_ak47_type2.py`, because it only borrows the geometry: it loads that file
with runpy (its own main() stays unrun), builds the same scene, and then adds the
exploded-view staging, the camera move and the text labels here.

Run headless:
    blender -b --python code/field_strip.py -- --poster
    blender -b --python code/field_strip.py -- --frames --samples 24 --gpu

Frames land in artifacts/frames_strip/; encode them with code/encode_strip.py.
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

_model = runpy.run_path(str(BUILD), run_name="field_strip_module")
build_scene = _model["build_scene"]
add_studio = _model["add_studio"]
setup_render = _model["setup_render"]
frame_camera = _model["frame_camera"]
render_still = _model["render_still"]
PARTS = _model["PARTS"]

# ---------------------------------------------------------------- timing
# Each entry: group, offset in metres, first frame, duration.
# Order = the order the parts come off in a field strip (magazine, dust cover,
# recoil spring, bolt carrier, bolt), then the furniture, which is separated here
# to show what the receiver carries.
STRIP_MOVES = [
    ("mag", Vector((0.02, 0, -0.30)), 12, 18),
    ("cover", Vector((-0.02, 0, 0.19)), 20, 18),
    ("bolt", Vector((0.00, 0, 0.24)), 28, 18),
    ("handguard", Vector((0.20, 0, 0.04)), 36, 18),
    ("stock", Vector((-0.17, 0, 0.02)), 44, 18),
    ("grip", Vector((0.00, 0, -0.13)), 50, 18),
    ("barrel", Vector((0.13, 0, 0.00)), 56, 18),
]

# Extra single-object moves: the bolt leaves its carrier, the spring its tunnel,
# and the two handguards stop reading as one block.
STRIP_EXTRA = {
    "Bolt": Vector((0.05, 0, 0.07)),
    "Recoil_spring": Vector((-0.10, 0, 0.02)),
    "Recoil_spring_guide": Vector((-0.11, 0, 0.02)),
    "Upper_handguard": Vector((0.02, 0, 0.05)),
    "Lower_handguard": Vector((0.02, 0, -0.05)),
}

HOLD = 112          # exploded pose held until here
TOTAL = 168         # rifle back together by here
LABEL_ON = 84       # labels appear once the parts have settled
LABEL_OFF = 110

LABELS = [
    ("dust cover", Vector((0.030, 0, 0.330)), 0.026),
    ("recoil spring", Vector((-0.130, 0, 0.185)), 0.024),
    ("bolt carrier", Vector((0.245, 0, 0.375)), 0.024),
    ("bolt", Vector((0.430, 0, 0.480)), 0.024),
    ("magazine", Vector((0.120, 0, -0.605)), 0.026),
    ("upper handguard", Vector((0.610, 0, 0.230)), 0.024),
    ("lower handguard", Vector((0.610, 0, -0.150)), 0.024),
    ("buttstock", Vector((-0.455, 0, 0.145)), 0.026),
    ("pistol grip", Vector((-0.030, 0, -0.300)), 0.024),
    ("barrel", Vector((0.865, 0, 0.100)), 0.026),
]


def emission_material(name, colour, strength):
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


LABEL_MAT = None
DIM_MAT = None


def text_object(name, body, location, size, material, align="CENTER"):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.size = size
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    obj.data.materials.append(material)
    return obj


def face_camera(obj, camera):
    obj.rotation_euler = (camera.location - obj.location).to_track_quat("Z", "Y").to_euler()


def animate(camera):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL

    objects = {obj.name: obj for group in PARTS.values() for obj in group}
    rest = {name: obj.location.copy() for name, obj in objects.items()}
    group_offset = {group: offset for group, offset, _s, _d in STRIP_MOVES}
    timing = {obj.name: (start, duration)
              for group, _o, start, duration in STRIP_MOVES
              for obj in PARTS[group]}

    def key(obj_name, offset, start, duration):
        obj = objects[obj_name]
        base = rest[obj_name]
        obj.location = base
        obj.keyframe_insert("location", frame=max(1, start - 1))
        obj.location = base + offset
        obj.keyframe_insert("location", frame=start + duration)
        obj.keyframe_insert("location", frame=HOLD)
        obj.location = base
        obj.keyframe_insert("location", frame=HOLD + duration)
        obj.keyframe_insert("location", frame=TOTAL)

    for group, offset, start, duration in STRIP_MOVES:
        for obj in PARTS[group]:
            if obj.name in STRIP_EXTRA:
                continue
            key(obj.name, offset, start, duration)

    # objects that separate further than their group, on their group's schedule
    for name, extra in STRIP_EXTRA.items():
        if name not in timing:
            continue
        start, duration = timing[name]
        key(name, group_offset_of(name, extra), start, duration)

    for obj in objects.values():
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"

    title = text_object("Title", "AK-47 Type 2 - field strip",
                        Vector((-0.66, 0, 0.475)), 0.050, LABEL_MAT, align="LEFT")
    subtitle = text_object("Subtitle", "seven groups, separated along the axes they come apart in",
                           Vector((-0.66, 0, 0.425)), 0.022, DIM_MAT, align="LEFT")
    for text in (title, subtitle):
        face_camera(text, camera)

    for body, position, size in LABELS:
        label = text_object(f"Label {body}", body, position, size, LABEL_MAT)
        face_camera(label, camera)
        label.scale = (0.001, 0.001, 0.001)
        label.keyframe_insert("scale", frame=LABEL_ON - 4)
        label.scale = (1, 1, 1)
        label.keyframe_insert("scale", frame=LABEL_ON)
        label.keyframe_insert("scale", frame=LABEL_OFF)
        label.scale = (0.001, 0.001, 0.001)
        label.keyframe_insert("scale", frame=LABEL_OFF + 4)


def group_offset_of(name, extra):
    for group, offset, _s, _d in STRIP_MOVES:
        if any(obj.name == name for obj in PARTS[group]):
            return offset + extra
    return extra


def main():
    global LABEL_MAT, DIM_MAT
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--poster", action="store_true")
    ap.add_argument("--frames", action="store_true")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    args = ap.parse_args(argv)

    build_scene()
    add_studio()
    LABEL_MAT = emission_material("Label", (1.0, 0.93, 0.80), 2.4)
    DIM_MAT = emission_material("Label dim", (0.72, 0.72, 0.70), 1.5)

    setup_render(args.samples, (args.width, args.height), gpu=args.gpu)
    bpy.context.scene.view_settings.exposure = 0.55
    camera = frame_camera(-40, 16, 3.75, 50, target=(0.18, 0, -0.13))
    # a dropped magazine ends near z = -0.56, so the floor goes down instead of
    # the rifle going up (the labels live in world space)
    bpy.data.objects["Backdrop"].location.z -= 0.62
    animate(camera)

    if args.poster:
        bpy.context.scene.frame_set(LABEL_ON + 8)
        bpy.context.scene.render.resolution_x = 1800
        bpy.context.scene.render.resolution_y = 1200
        render_still(RENDERS / "07_field_strip_exploded.png")

    if args.frames:
        out_dir = ART / "frames_strip"
        out_dir.mkdir(parents=True, exist_ok=True)
        scene = bpy.context.scene
        scene.render.resolution_x = args.width
        scene.render.resolution_y = args.height
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.compression = 15
        last = args.end or TOTAL
        for frame in range(args.start, last + 1):
            scene.frame_set(frame)
            scene.render.filepath = str(out_dir / f"strip_{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"STRIP {frame}/{last}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
