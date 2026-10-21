"""Build an AK-47 Type 2 (1951-1955, machined receiver) in Blender from the
numbers and details in research/sources.md, then render and export it.

Run headless (Windows):
    blender -b --python code/build_ak47_type2.py -- --quick --gpu
    blender -b --python code/build_ak47_type2.py -- --hero --gpu
    blender -b --python code/build_ak47_type2.py -- --export
    blender -b --python code/build_ak47_type2.py -- --turntable --gpu
    blender -b --python code/build_ak47_type2.py -- --explode --gpu

Proportions were measured off sources/raw/15_ak47_type2_right_side_view.jpg
(Commons, AK-47 type II, DM-ST-89-01131) and pinned to the published figures:

  overall length 0.870 m, barrel 0.415 m          Modern Firearms, pattern 1949
  receiver rear to muzzle 0.629 m, stock 0.241 m   measured on the reference
  machined receiver, no stamped rivet rows         Modern Firearms, Type 2
  separate pinned stock socket, one-piece grip     Modern Firearms, Type 2
  forward sling loop on the lower handguard        Modern Firearms, Type 3 note
  no bayonet provision on the early rifles         Modern Firearms, Type 1

Axes: +X towards the muzzle, +Z up, origin at the rear of the receiver.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
RENDER_DIR = ART / "renders"
VIDEO_DIR = ART / "video"
MODEL_DIR = ART / "model"

MATS: dict[str, bpy.types.Material] = {}
PARTS: dict[str, list[bpy.types.Object]] = {}


# ---------------------------------------------------------------- materials
def material(name, base, metallic, roughness, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    return mat


def metal_material(name, base, roughness, bump=0.0):
    """Blued steel: metallic, with a little roughness variation and a cast surface."""
    mat = material(name, base, 1.0, roughness)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 55.0
    tex.inputs["Detail"].default_value = 6.0
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], tex.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.40
    ramp.color_ramp.elements[0].color = (roughness - 0.03, roughness - 0.03, roughness - 0.03, 1)
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = (roughness + 0.04, roughness + 0.04, roughness + 0.04, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    if bump > 0:
        bmp = nt.nodes.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = bump
        bmp.inputs["Distance"].default_value = 0.0002
        nt.links.new(tex.outputs["Fac"], bmp.inputs["Height"])
        nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def wood_material(name, light, dark, roughness):
    """Varnished birch: banded grain along the length plus a coat layer."""
    mat = material(name, light, 0.0, roughness, coat=0.5)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 12.0, 12.0)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 45.0
    wave.inputs["Distortion"].default_value = 2.5
    wave.inputs["Detail"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 60.0
    noise.inputs["Detail"].default_value = 4.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(wave.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(noise.outputs["Color"], mix.inputs["Color2"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.40
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = 0.60
    ramp.color_ramp.elements[1].color = (*light, 1)
    nt.links.new(mix.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.05
    bmp.inputs["Distance"].default_value = 0.0003
    nt.links.new(wave.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def build_materials():
    MATS["steel"] = metal_material("Blued steel", (0.040, 0.043, 0.050), 0.34, bump=0.020)
    MATS["steel_dark"] = metal_material("Blued steel, dark", (0.024, 0.026, 0.030), 0.42, bump=0.018)
    MATS["mag"] = metal_material("Magazine steel", (0.034, 0.036, 0.040), 0.48, bump=0.030)
    MATS["gunmetal"] = metal_material("Gunmetal", (0.028, 0.030, 0.034), 0.52, bump=0.012)
    MATS["wood"] = wood_material("Varnished birch", (0.075, 0.028, 0.010), (0.022, 0.008, 0.003), 0.34)
    MATS["wood_dark"] = wood_material("Varnished birch, worn", (0.052, 0.020, 0.008), (0.016, 0.006, 0.002), 0.42)
    MATS["bore"] = material("Bore black", (0.003, 0.003, 0.003), 0.0, 0.9)
    MATS["backdrop"] = material("Backdrop", (0.020, 0.020, 0.022), 0.0, 0.80)


# ---------------------------------------------------------------- primitives
def box(name, size, loc, mat, bevel=0.0015, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(MATS[mat])
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return obj


def cylinder(name, radius, depth, loc, mat, rot=(0, math.pi / 2, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(MATS[mat])
    return obj


def prism(name, outline, thickness, mat, bevel=0.0015, loc=(0, 0, 0)):
    verts = [(x, -thickness / 2, z) for x, z in outline]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [list(range(len(outline)))])
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.data.materials.append(MATS[mat])
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, thickness, 0)})
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    return obj


def sweep(name, path, half_width, half_thick, mat, up_hint=Vector((0, 0, 1))):
    rings = []
    for i, p in enumerate(path):
        if i == 0:
            tangent = (path[1] - path[0]).normalized()
        elif i == len(path) - 1:
            tangent = (path[-1] - path[-2]).normalized()
        else:
            tangent = (path[i + 1] - path[i - 1]).normalized()
        normal = tangent.cross(Vector((0, 1, 0))).normalized()
        if normal.dot(up_hint) < 0:
            normal = -normal
        rings.append([
            p + normal * half_thick + Vector((0, half_width, 0)),
            p + normal * half_thick - Vector((0, half_width, 0)),
            p - normal * half_thick - Vector((0, half_width, 0)),
            p - normal * half_thick + Vector((0, half_width, 0)),
        ])
    verts = [tuple(v) for ring in rings for v in ring]
    faces = []
    for i in range(len(rings) - 1):
        a, b = i * 4, (i + 1) * 4
        for k in range(4):
            faces.append([a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k])
    faces.append([3, 2, 1, 0])
    last = (len(rings) - 1) * 4
    faces.append([last, last + 1, last + 2, last + 3])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(MATS[mat])
    return obj


def add(group, obj):
    PARTS.setdefault(group, []).append(obj)
    return obj


# ---------------------------------------------------------------- geometry
RECEIVER_FRONT = 0.291
MUZZLE = 0.629
STOCK_REAR = -0.241
BORE_Z = 0.0


def build_receiver():
    h = 0.060
    add("body", box("Receiver", (RECEIVER_FRONT, 0.031, h), (RECEIVER_FRONT / 2, 0, -0.005), "steel", bevel=0.0022))
    # shallow milled lightening pocket on both sides, above the magazine.
    # Kept on the Type 2; the Type 3 deepens and lengthens it.
    for side, y in (("L", 0.0146), ("R", -0.0146)):
        add("body", box(f"Lightening_cut_{side}", (0.132, 0.0022, 0.019), (0.150, y, -0.002),
                        "steel_dark", bevel=0.0045))
    # dust cover: stamped, sits on the receiver, two pressed ribs
    add("cover", box("Dust_cover", (0.276, 0.0305, 0.011), (RECEIVER_FRONT / 2, 0, 0.0305), "steel_dark", bevel=0.0032))
    for i, x in enumerate((0.055, 0.235)):
        add("cover", box(f"Dust_cover_rib_{i}", (0.011, 0.0310, 0.0055), (x, 0, 0.0365), "steel_dark", bevel=0.0012))
    # ejection port and charging-handle slot on the right side
    add("body", box("Ejection_port", (0.052, 0.0018, 0.019), (0.238, -0.0159, 0.006), "bore", bevel=0.0006))
    add("body", box("Charge_slot", (0.068, 0.0018, 0.007), (0.180, -0.0159, 0.002), "bore", bevel=0.0004))
    add("bolt", cylinder("Charging_handle", 0.0052, 0.026, (0.205, -0.030, 0.002), "steel", rot=(0, 0, 0), verts=16))
    # selector / safety lever: long stamped lever on the right side
    add("body", box("Selector_lever", (0.150, 0.0028, 0.017), (0.195, -0.0178, 0.014), "steel_dark",
                    bevel=0.0010, rot=(0, math.radians(-2), 0)))
    add("body", box("Selector_tab", (0.026, 0.012, 0.022), (0.268, -0.023, 0.000), "steel_dark", bevel=0.0016))
    # rear sight: block at the front of the receiver, tangent leaf, notch
    add("body", box("Rear_sight_block", (0.038, 0.028, 0.015), (0.272, 0, 0.0435), "gunmetal", bevel=0.0016))
    add("body", box("Rear_sight_leaf", (0.040, 0.024, 0.0032), (0.278, 0, 0.0520), "steel_dark",
                    bevel=0.0008, rot=(0, math.radians(-5), 0)))
    add("body", box("Rear_sight_notch", (0.008, 0.008, 0.0035), (0.296, 0, 0.0545), "bore", bevel=0.0003))
    # front trunnion visible at the handguard break
    add("body", box("Front_trunnion", (0.018, 0.030, 0.040), (0.288, 0, -0.002), "gunmetal", bevel=0.0018))
    # magazine well, catch and release paddle
    add("body", box("Mag_well", (0.080, 0.030, 0.016), (0.215, 0, -0.032), "steel", bevel=0.0016))
    add("body", box("Mag_release", (0.026, 0.018, 0.009), (0.172, 0, -0.042), "steel_dark", bevel=0.0010))
    # trigger guard: a rectangular loop behind the magazine
    add("body", box("Trigger_guard_front", (0.008, 0.018, 0.050), (0.120, 0, -0.050), "steel", bevel=0.0022))
    add("body", box("Trigger_guard_bottom", (0.070, 0.018, 0.008), (0.153, 0, -0.077), "steel", bevel=0.0022))
    add("body", box("Trigger_guard_rear", (0.008, 0.018, 0.050), (0.186, 0, -0.050), "steel", bevel=0.0022))
    add("body", box("Trigger", (0.007, 0.008, 0.026), (0.147, 0, -0.058), "steel_dark", bevel=0.0010,
                    rot=(0, math.radians(10), 0)))
    # steel stock socket pinned to the rear of the receiver (Type 2 feature)
    add("body", box("Stock_socket", (0.028, 0.034, 0.052), (0.002, 0, -0.003), "steel_dark", bevel=0.0024))
    for i, z in enumerate((-0.018, 0.012)):
        add("body", cylinder(f"Stock_socket_pin_{i}", 0.0030, 0.037, (0.002, 0, z), "steel",
                             rot=(math.pi / 2, 0, 0), verts=12))


def build_stock():
    # Straight-comb buttstock: buttplate 0.10 m tall, wrist meets the socket.
    outline = [(STOCK_REAR, 0.012), (STOCK_REAR, -0.100), (-0.160, -0.074), (-0.095, -0.058),
               (-0.020, -0.048), (0.000, -0.030), (0.000, 0.020), (-0.060, 0.024),
               (-0.140, 0.020), (-0.200, 0.016)]
    add("stock", prism("Buttstock", outline, 0.038, "wood", bevel=0.0050))
    add("stock", box("Buttplate", (0.007, 0.040, 0.116), (STOCK_REAR - 0.003, 0, -0.044), "steel_dark", bevel=0.0020))
    add("stock", box("Stock_sling_slot", (0.026, 0.042, 0.007), (-0.196, 0, -0.062), "bore", bevel=0.0005))
    # sling swivel on the left side of the wrist
    add("stock", cylinder("Stock_swivel", 0.008, 0.006, (-0.070, 0.021, -0.020), "steel_dark",
                          rot=(math.pi / 2, 0, 0), verts=16))


def build_pistol_grip():
    # One-piece wooden grip, single vertical bolt under the receiver (Type 2).
    outline = [(0.050, -0.030), (0.110, -0.030), (0.126, -0.148), (0.086, -0.164), (0.044, -0.044)]
    add("grip", prism("Pistol_grip", outline, 0.031, "wood", bevel=0.0055))
    add("grip", cylinder("Grip_bolt", 0.0042, 0.036, (0.082, 0, -0.032), "steel", rot=(math.pi / 2, 0, 0), verts=12))
    add("grip", box("Grip_base", (0.060, 0.033, 0.007), (0.081, 0, -0.036), "steel", bevel=0.0013))


def build_barrel_and_gas():
    add("barrel", cylinder("Barrel", 0.0110, 0.400, (0.4200, 0, BORE_Z), "gunmetal", verts=40))
    add("barrel", cylinder("Barrel_bore", 0.0046, 0.003, (MUZZLE - 0.001, 0, BORE_Z), "bore", verts=24))
    add("barrel", cylinder("Cleaning_rod", 0.0026, 0.230, (0.455, 0, -0.0165), "gunmetal", verts=14))
    # muzzle nut
    add("barrel", cylinder("Muzzle_nut", 0.0112, 0.026, (MUZZLE - 0.013, 0, BORE_Z), "gunmetal", verts=32))
    # gas block, angled, carrying the gas tube
    add("barrel", box("Gas_block", (0.030, 0.026, 0.042), (0.508, 0, 0.022), "gunmetal", bevel=0.0028,
                      rot=(0, math.radians(-10), 0)))
    add("barrel", cylinder("Gas_tube", 0.0115, 0.090, (0.4780, 0, 0.0360), "gunmetal", verts=28))
    add("barrel", box("Gas_tube_rear", (0.026, 0.024, 0.028), (0.297, 0, 0.0375), "gunmetal", bevel=0.002))
    # front sight: tall block, hooded post, near the muzzle
    add("barrel", box("Front_sight_base", (0.030, 0.026, 0.050), (MUZZLE - 0.052, 0, 0.030), "gunmetal", bevel=0.0024))
    add("barrel", cylinder("Front_sight_post", 0.0021, 0.024, (MUZZLE - 0.052, 0, 0.064), "steel_dark", verts=12,
                           rot=(0, 0, 0)))
    for side, y in (("L", 0.0115), ("R", -0.0115)):
        add("barrel", box(f"Front_sight_hood_{side}", (0.014, 0.0035, 0.026), (MUZZLE - 0.052, y, 0.070),
                          "steel_dark", bevel=0.0008))
    add("barrel", box("Front_sight_hood_top", (0.014, 0.026, 0.0035), (MUZZLE - 0.052, 0, 0.082),
                      "steel_dark", bevel=0.0008))


def build_handguards():
    # Lower handguard with finger grooves, forward sling loop at its front end
    add("handguard", box("Lower_handguard", (0.155, 0.038, 0.054), (0.373, 0, -0.017), "wood", bevel=0.0065))
    add("handguard", box("Upper_handguard", (0.155, 0.038, 0.046), (0.373, 0, 0.028), "wood", bevel=0.0075))
    add("handguard", box("Handguard_retainer", (0.009, 0.041, 0.052), (0.296, 0, 0.001), "steel_dark", bevel=0.0022))
    add("handguard", box("Sling_loop_front", (0.020, 0.007, 0.028), (0.446, 0.020, -0.030), "steel_dark", bevel=0.0020))
    add("handguard", box("Lower_band", (0.007, 0.042, 0.048), (0.447, 0, -0.002), "gunmetal", bevel=0.0016))


def build_magazine():
    # 30-round slab-sided magazine: curved, 3 ribs, floor plate.
    radius, cx, cz = 0.45, 0.196, -0.028
    path = []
    for i in range(13):
        t = math.radians(i * 2.6)
        path.append(Vector((cx + radius * (1 - math.cos(t)), 0, cz - radius * math.sin(t))))
    add("mag", sweep("Magazine", path, 0.0142, 0.038, "mag"))
    end = path[-1]
    tangent = (path[-1] - path[-2]).normalized()
    add("mag", box("Mag_floor", (0.078, 0.030, 0.006), (end + tangent * 0.004), "steel_dark", bevel=0.0012))
    for i, idx in enumerate((5, 7, 9)):
        p = path[idx]
        nxt = path[idx + 1] - path[idx - 1]
        ang = math.atan2(nxt.z, nxt.x)
        add("mag", box(f"Mag_rib_{i}", (0.007, 0.031, 0.070), (p.x, 0, p.z), "steel_dark",
                       bevel=0.0010, rot=(0, -ang, 0)))


def build_bolt_group():
    add("bolt", box("Bolt_carrier", (0.175, 0.026, 0.024), (0.185, 0, 0.006), "steel_dark", bevel=0.0018))
    add("bolt", cylinder("Gas_piston", 0.0072, 0.150, (0.355, 0, 0.024), "steel", verts=20))
    add("bolt", cylinder("Recoil_spring", 0.0058, 0.150, (0.075, 0, 0.033), "steel_dark", verts=16))
    add("bolt", cylinder("Recoil_spring_guide", 0.0040, 0.040, (0.000, 0, 0.033), "steel", verts=16))
    add("bolt", box("Bolt", (0.046, 0.022, 0.021), (0.235, 0, 0.006), "steel", bevel=0.0022))


def build_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            if item.users == 0:
                block.remove(item)

    build_materials()
    build_receiver()
    build_stock()
    build_pistol_grip()
    build_barrel_and_gas()
    build_handguards()
    build_magazine()
    build_bolt_group()

    root = bpy.data.objects.new("AK47_Root", None)
    bpy.context.collection.objects.link(root)
    # the rifle spans x = -0.241 .. 0.629, so its centre is at x = 0.194;
    # put the empty there and shift every child back, so a rotation of the empty
    # spins the rifle in place instead of orbiting it about the butt
    centre = Vector((0.194, 0, -0.020))
    for group in PARTS.values():
        for obj in group:
            obj.parent = root
            obj.matrix_parent_inverse = root.matrix_world.inverted()
            obj.location = obj.location - centre
    root.location = centre
    return root


# ---------------------------------------------------------------- studio
def add_studio():
    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.19, 0, -0.252))
    floor = bpy.context.object
    floor.name = "Backdrop"
    floor.data.materials.append(MATS["backdrop"])
    # vertical seamless behind the rifle (camera looks along +Y)
    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.19, 2.2, 1.4), rotation=(math.pi / 2, 0, 0))
    wall = bpy.context.object
    wall.name = "Backdrop_wall"
    wall.data.materials.append(MATS["backdrop"])

    def area(name, loc, energy, size, color=(1.0, 0.96, 0.92)):
        light = bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.size = size
        light.color = color
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        track = obj.constraints.new("TRACK_TO")
        track.target = bpy.data.objects["AK47_Root"]
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

    area("Key", (0.85, -0.95, 0.85), 220.0, 1.4)
    area("Fill", (0.10, 1.10, 0.45), 55.0, 1.8, color=(0.82, 0.88, 1.0))
    area("Rim", (-0.75, 0.35, 0.65), 130.0, 0.9, color=(1.0, 0.92, 0.84))
    area("Top", (0.25, 0.0, 1.20), 45.0, 1.2)


def frame_camera(azimuth_deg, elevation_deg, distance, lens, target=(0.19, 0, -0.02)):
    scn = bpy.context.scene
    cam = scn.camera
    if cam is None:
        cam_data = bpy.data.cameras.new("Camera")
        cam = bpy.data.objects.new("Camera", cam_data)
        bpy.context.collection.objects.link(cam)
        scn.camera = cam
    cam.data.lens = lens
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    cam.location = (
        target[0] + distance * math.cos(el) * math.sin(az),
        target[1] - distance * math.cos(el) * math.cos(az),
        target[2] + distance * math.sin(el),
    )
    if "CamTarget" not in bpy.data.objects:
        empty = bpy.data.objects.new("CamTarget", None)
        bpy.context.collection.objects.link(empty)
    target_obj = bpy.data.objects["CamTarget"]
    target_obj.location = target
    for con in list(cam.constraints):
        cam.constraints.remove(con)
    track = cam.constraints.new("TRACK_TO")
    track.target = target_obj
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    return cam


def enable_gpu():
    """Cycles needs the device switched on in the preferences, not just in the scene."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = backend
            prefs.refresh_devices()
            if any(d.type not in {"CPU", "NONE"} for d in prefs.devices):
                for device in prefs.devices:
                    device.use = device.type != "CPU"
                print(f"GPU backend: {backend}")
                return True
        except TypeError:
            continue
    print("No GPU backend available, staying on CPU")
    return False


def setup_render(samples, res, engine="CYCLES", gpu=False):
    scene = bpy.context.scene
    scene.render.engine = engine
    if engine == "CYCLES":
        if gpu and not enable_gpu():
            gpu = False
        scene.cycles.device = "GPU" if gpu else "CPU"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 6
    scene.render.resolution_x = res[0]
    scene.render.resolution_y = res[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.010, 0.011, 0.013, 1.0)
    bg.inputs["Strength"].default_value = 0.35


def render_still(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {path}")


# ---------------------------------------------------------------- animation
def animate_turntable(frames=120):
    root = bpy.data.objects["AK47_Root"]
    root.rotation_mode = "XYZ"
    # start at -90 deg so frame 1 is already a side view instead of an end-on one
    root.rotation_euler = (0, 0, math.radians(-90))
    root.keyframe_insert("rotation_euler", frame=1)
    root.rotation_euler = (0, 0, math.radians(270))
    root.keyframe_insert("rotation_euler", frame=frames)
    for fc in root.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def animate_explode():
    """Field-strip in reverse: magazine, cover, spring, bolt carrier, bolt."""
    moves = {
        "mag": Vector((0, 0, -0.22)),
        "cover": Vector((0, 0, 0.10)),
    }
    objects = {obj.name: obj for group in PARTS.values() for obj in group}
    for group, delta in moves.items():
        for obj in PARTS[group]:
            obj["rest_loc"] = obj.location.copy()
            obj.location = obj.location
            obj.keyframe_insert("location", frame=1)
    # bolt carrier group and bolt move up after the cover
    for name in ("Bolt_carrier", "Gas_piston", "Charging_handle"):
        obj = objects[name]
        obj.keyframe_insert("location", frame=1)
        obj.location = obj.location + Vector((0, 0, 0.075))
        obj.keyframe_insert("location", frame=40)
    for group, delta in moves.items():
        for obj in PARTS[group]:
            loc = obj.location.copy()
            obj.keyframe_insert("location", frame=25)
            obj.location = loc + delta
            obj.keyframe_insert("location", frame=45)
    scene = bpy.context.scene
    scene.frame_end = 120
    for obj in objects.values():
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"


def render_animation(frames, out_path, res=(1280, 720)):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = frames
    scene.render.fps = 30
    scene.render.resolution_x = res[0]
    scene.render.resolution_y = res[1]
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(animation=True)
    print(f"RENDERED {out_path}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--hero", action="store_true")
    ap.add_argument("--turntable", action="store_true")
    ap.add_argument("--explode", action="store_true")
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--explode-still", action="store_true")
    ap.add_argument("--frames-png", action="store_true")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--save", default="")
    args = ap.parse_args(argv)

    build_scene()
    add_studio()
    setup_render(args.samples, (1280, 720) if args.quick else (1800, 1200), gpu=args.gpu)
    frame_camera(0, 4, 2.05, 65)

    if args.quick:
        render_still(RENDER_DIR / "quick_check.png")

    if args.hero:
        shots = {
            "01_right_side.png": (0, 3, 2.05, 65),
            "02_three_quarter_front.png": (32, 12, 2.00, 58),
            "03_three_quarter_rear.png": (-38, 14, 2.10, 60),
            "04_receiver_detail.png": (6, 7, 0.95, 85),
            "05_top_view.png": (0, 78, 1.95, 70),
        }
        for name, (az, el, dist, lens) in shots.items():
            frame_camera(az, el, dist, lens)
            render_still(RENDER_DIR / name)

    if args.explode_still:
        # lift the whole rifle first so dropped parts stay above the floor
        bpy.data.objects["AK47_Root"].location = (0, 0, 0.22)
        offsets = {
            "mag": (0.01, 0, -0.13),
            "cover": (-0.03, 0, 0.075),
        }
        for group, delta in offsets.items():
            for obj in PARTS[group]:
                obj.location = obj.location + Vector(delta)
        for obj in PARTS["bolt"]:
            obj.location = obj.location + Vector((-0.01, 0, 0.050))
        frame_camera(-14, 10, 1.95, 62, target=(0.19, 0, 0.09))
        render_still(RENDER_DIR / "06_exploded_view.png")

    if args.export:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        for group in PARTS.values():
            for obj in group:
                obj.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(MODEL_DIR / "ak47_type2.glb"), export_format="GLB",
                                  use_selection=True, export_apply=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(MODEL_DIR / "ak47_type2.blend"))
        print(f"EXPORTED {MODEL_DIR}")

    if args.frames_png:
        animate_turntable(args.frames)
        frame_camera(-90, 9, 2.20, 62)
        scene = bpy.context.scene
        scene.frame_start = 1
        scene.frame_end = args.frames
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.compression = 15
        frames_dir = ART / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        for frame in range(1, args.frames + 1):
            scene.frame_set(frame)
            scene.render.filepath = str(frames_dir / f"frame_{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"FRAME {frame}/{args.frames}", flush=True)

    if args.turntable:
        animate_turntable(args.frames)
        frame_camera(-90, 8, 2.15, 80)
        render_animation(args.frames, VIDEO_DIR / "turntable.mp4")

    if args.explode:
        animate_explode()
        frame_camera(-48, 12, 2.10, 62)
        render_animation(120, VIDEO_DIR / "field_strip_exploded.mp4")

    if args.save:
        bpy.ops.wm.save_as_mainfile(filepath=args.save)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
