"""Sazabi (MSN-04) as a display figure, built from primitives.

Reference: sources/raw/recovered_01.jpg and _04.jpg (Bandai product photographs,
©SOTSU·SUNRISE, used only as visual reference for proportion and equipment).

Run headless:
    blender -b --python code/build_sazabi.py -- --render --views three_quarter,front
    blender -b --python code/build_sazabi.py -- --render --views all --samples 96
    blender -b --python code/build_sazabi.py -- --export

Scale: 1 Blender unit = 1 m, figure about 1.90 m tall, standing on z = 0,
facing -Y. Character's right hand is +X (rifle), left hand is -X (shield).

Proportion landmarks (metres):
    ground 0.00   foot 0.00-0.11   ankle 0.11-0.20   calf 0.20-0.62
    knee 0.58-0.72   thigh 0.70-1.02   hip 1.00   pelvis 0.98-1.12
    abdomen 1.12-1.24   chest 1.22-1.56   shoulder 1.38-1.58
    neck 1.56-1.62   head 1.62-1.80   crest to 1.90
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

import bpy

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mecha_kit import (MATS, PARTS, camera_view, clear, cyl, export, make_materials,
                       mirror, prism, render, RENDERS, setup_render, studio, armor,
                       ball, vent)

PALETTE = {
    "red": ((0.082, 0.008, 0.006), 0.22, 0.28, 0.45),
    "red_dark": ((0.040, 0.005, 0.004), 0.28, 0.32, 0.30),
    "red_deep": ((0.020, 0.003, 0.003), 0.32, 0.38, 0.20),
    "frame": ((0.019, 0.019, 0.023), 0.65, 0.42, 0.00),
    "gold": ((0.320, 0.200, 0.045), 1.00, 0.26, 0.00),
    "gun": ((0.042, 0.042, 0.048), 0.90, 0.32, 0.00),
    "grey": ((0.180, 0.180, 0.186), 0.55, 0.38, 0.00),
    "white": ((0.700, 0.690, 0.670), 0.15, 0.35, 0.00),
}

HEAD_Z = 1.710
CHEST_Z = 1.390
HIP_Z = 1.000
SHOULDER_X = 0.300
LEG_X = 0.135


def build_head() -> None:
    g = "head"
    # helmet: a dome sitting on a narrow face mask, with the mono-eye in a recess
    armor(g, "helmet", (0.190, 0.195, 0.150), (0, 0.006, HEAD_Z), "red",
          top_scale=(0.80, 0.84), bevel=0.014)
    ball(g, "helmet_dome", 0.098, (0, 0.010, HEAD_Z + 0.085), "red",
         scale=(1.0, 1.05, 0.62))
    armor(g, "face", (0.128, 0.060, 0.105), (0, -0.098, HEAD_Z - 0.030), "red_dark",
          top_scale=(0.82, 1.0), bevel=0.008)
    armor(g, "visor_band", (0.150, 0.026, 0.042), (0, -0.104, HEAD_Z + 0.012), "frame",
          bevel=0.004)
    armor(g, "eye", (0.088, 0.014, 0.020), (0, -0.118, HEAD_Z + 0.012), "eye", bevel=0.004)
    armor(g, "chin", (0.100, 0.048, 0.042), (0, -0.088, HEAD_Z - 0.098), "frame", bevel=0.006)
    # crest: one fin along the midline, sweeping back and up
    armor(g, "crest", (0.026, 0.190, 0.060), (0, 0.070, HEAD_Z + 0.115), "red",
          top_scale=(1.0, 0.30), bevel=0.004, rot=(-0.30, 0, 0))
    for side in (1, -1):
        armor(g, "cheek", (0.034, 0.082, 0.082), (side * 0.072, -0.040, HEAD_Z - 0.030), "red",
              bevel=0.006)
        armor(g, "ear_vent", (0.022, 0.032, 0.048), (side * 0.092, 0.008, HEAD_Z), "frame",
              bevel=0.003)
        cyl(g, "head_vulcan", 0.012, 0.040, (side * 0.058, -0.115, HEAD_Z + 0.060), "frame",
            rot=(math.pi / 2, 0, 0), verts=12)
    armor(g, "neck", (0.078, 0.078, 0.090), (0, 0, 1.585), "frame", bevel=0.008)


def build_torso() -> None:
    g = "torso"
    armor(g, "chest_core", (0.350, 0.235, 0.330), (0, 0, CHEST_Z), "red",
          top_scale=(1.03, 1.0), bevel=0.014)
    armor(g, "chest_front", (0.255, 0.095, 0.245), (0, -0.140, CHEST_Z - 0.020), "red",
          top_scale=(0.84, 0.92), bevel=0.012)
    armor(g, "cockpit_hatch", (0.125, 0.032, 0.140), (0, -0.192, CHEST_Z - 0.010), "red_dark",
          top_scale=(0.74, 1.0), bevel=0.008)
    armor(g, "hatch_trim", (0.075, 0.014, 0.028), (0, -0.206, CHEST_Z + 0.052), "gold", bevel=0.003)
    armor(g, "collar", (0.200, 0.160, 0.060), (0, -0.010, CHEST_Z + 0.168), "red_dark",
          top_scale=(0.78, 0.80), bevel=0.010)
    for side in (1, -1):
        armor(g, "shoulder_mount", (0.100, 0.140, 0.130), (side * 0.205, 0, CHEST_Z + 0.080),
              "red", bevel=0.010)
        vent(g, "chest_vent", (0.024, 0.075, 0.070), (side * 0.112, -0.150, CHEST_Z + 0.060),
              "gold", count=3, vertical=True)
        # chest side intakes
        armor(g, "chest_intake", (0.055, 0.100, 0.150), (side * 0.170, -0.070, CHEST_Z + 0.010),
              "red_dark", bevel=0.008)
    for side in (1, -1):
        # side fairing: fills the gap between the chest and the pauldron
        armor(g, "torso_side", (0.115, 0.200, 0.240), (side * 0.230, 0.005, CHEST_Z + 0.045),
              "red", top_scale=(0.9, 0.95), bevel=0.010)
        armor(g, "torso_side_lip", (0.125, 0.205, 0.045), (side * 0.230, 0.005, CHEST_Z - 0.080),
              "red_dark", bevel=0.008)
        # shoulder joint cover
        cyl(g, "shoulder_cover", 0.085, 0.070, (side * 0.268, 0, CHEST_Z + 0.075), "red_dark",
            rot=(0, math.pi / 2, 0), verts=20)

    # abdomen and the gold waist pipe
    armor(g, "abdomen", (0.235, 0.190, 0.120), (0, 0, CHEST_Z - 0.225), "frame", bevel=0.010)
    for i, z in enumerate((CHEST_Z - 0.185, CHEST_Z - 0.230, CHEST_Z - 0.275)):
        armor(g, f"ab_ring_{i}", (0.225 - i * 0.008, 0.185, 0.032), (0, 0, z), "red_dark",
              bevel=0.006)
    cyl(g, "waist_pipe", 0.017, 0.250, (0, -0.095, CHEST_Z - 0.315), "gold",
        rot=(0, math.pi / 2, 0), verts=16)
    for side in (1, -1):
        cyl(g, "waist_pipe_side", 0.017, 0.130, (side * 0.112, -0.030, CHEST_Z - 0.315),
            "gold", rot=(math.pi / 2, 0, 0), verts=16)
    armor(g, "back_pack", (0.300, 0.085, 0.270), (0, 0.140, CHEST_Z + 0.010), "red_dark",
          bevel=0.012)


def build_waist_and_skirt() -> None:
    g = "waist"
    armor(g, "pelvis", (0.300, 0.210, 0.140), (0, 0, HIP_Z), "red", top_scale=(0.92, 0.95),
          bevel=0.012)
    armor(g, "pelvis_front", (0.150, 0.065, 0.125), (0, -0.120, HIP_Z - 0.010), "red_dark",
          top_scale=(0.84, 1.0), bevel=0.008)
    armor(g, "crotch_guard", (0.095, 0.055, 0.095), (0, -0.120, HIP_Z - 0.090), "red_deep",
          bevel=0.008)
    prism(g, "skirt_front_center",
          [(-0.078, 0.0), (0.078, 0.0), (0.096, -0.140), (0.0, -0.180), (-0.096, -0.140)],
          0.048, (0, -0.120, HIP_Z - 0.005), "red", bevel=0.006)
    for side in (1, -1):
        prism(g, "skirt_front_side",
              [(-0.062, 0.0), (0.062, 0.0), (0.076, -0.120), (0.020, -0.152), (-0.062, -0.124)],
              0.042, (side * 0.135, -0.108, HIP_Z), "red_dark", bevel=0.006)
        armor(g, "skirt_side", (0.045, 0.195, 0.230), (side * 0.200, -0.010, HIP_Z - 0.060),
              "red", top_scale=(1.0, 0.82), bevel=0.008, rot=(0, side * 0.22, 0))
        armor(g, "skirt_side_trim", (0.022, 0.160, 0.032), (side * 0.222, -0.010, HIP_Z - 0.135),
              "gold", bevel=0.004)
        ball(g, "hip_joint", 0.064, (side * LEG_X, 0, HIP_Z - 0.050), "frame")
        armor(g, "hip_cover", (0.120, 0.170, 0.090), (side * LEG_X, 0, HIP_Z - 0.030), "red_dark",
              bevel=0.008)
    prism(g, "skirt_rear",
          [(-0.135, 0.0), (0.135, 0.0), (0.155, -0.145), (0.0, -0.180), (-0.155, -0.145)],
          0.052, (0, 0.120, HIP_Z + 0.010), "red_dark", bevel=0.006)


def build_shoulders_and_arms() -> None:
    right = []
    g = "arm"
    # pauldron: large rounded block, lower lip, side vent, swept fin
    armor(g, "pauldron", (0.240, 0.255, 0.225), (SHOULDER_X + 0.090, 0, CHEST_Z + 0.070),
          "red", top_scale=(0.78, 0.86), bevel=0.022)
    right.append(PARTS[g][-1])
    armor(g, "pauldron_lip", (0.258, 0.262, 0.052), (SHOULDER_X + 0.090, 0, CHEST_Z - 0.052),
          "red_dark", bevel=0.010)
    right.append(PARTS[g][-1])
    vent(g, "pauldron_vent", (0.028, 0.130, 0.080), (SHOULDER_X + 0.190, -0.030, CHEST_Z + 0.100),
          "frame", count=3, vertical=True)
    prism(g, "pauldron_fin",
          [(-0.065, 0.0), (0.065, 0.0), (0.080, 0.100), (-0.020, 0.076)],
          0.032, (SHOULDER_X + 0.080, 0.060, CHEST_Z + 0.200), "red",
          rot=(0.30, 0, 0), bevel=0.004)
    right.append(PARTS[g][-1])

    cyl(g, "shoulder_ball", 0.072, 0.120, (SHOULDER_X, 0, CHEST_Z + 0.070), "frame",
        rot=(0, math.pi / 2, 0), verts=20)
    right.append(PARTS[g][-1])
    armor(g, "upper_arm", (0.145, 0.145, 0.250), (SHOULDER_X + 0.028, 0, CHEST_Z - 0.140),
          "red_dark", bevel=0.010)
    right.append(PARTS[g][-1])
    ball(g, "elbow", 0.060, (SHOULDER_X + 0.028, 0, CHEST_Z - 0.275), "frame")
    right.append(PARTS[g][-1])

    # oversized forearm gauntlets
    armor(g, "forearm", (0.185, 0.200, 0.310), (SHOULDER_X + 0.032, 0, CHEST_Z - 0.450),
          "red", top_scale=(1.08, 1.08), bevel=0.016)
    right.append(PARTS[g][-1])
    armor(g, "forearm_cuff", (0.200, 0.215, 0.066), (SHOULDER_X + 0.032, 0, CHEST_Z - 0.310),
          "red_dark", bevel=0.010)
    right.append(PARTS[g][-1])
    armor(g, "forearm_wrist", (0.150, 0.160, 0.064), (SHOULDER_X + 0.032, 0, CHEST_Z - 0.610),
          "red_dark", bevel=0.008)
    right.append(PARTS[g][-1])
    vent(g, "forearm_vent", (0.024, 0.110, 0.070), (SHOULDER_X + 0.120, -0.035, CHEST_Z - 0.450),
          "frame", count=3, vertical=True)

    armor(g, "hand", (0.100, 0.110, 0.100), (SHOULDER_X + 0.032, -0.010, CHEST_Z - 0.690),
          "frame", bevel=0.010)
    right.append(PARTS[g][-1])
    for i in range(4):
        armor(g, f"finger_{i}", (0.019, 0.026, 0.075),
              (SHOULDER_X - 0.002 + i * 0.024, -0.060, CHEST_Z - 0.738), "frame", bevel=0.005)
        right.append(PARTS[g][-1])
    armor(g, "thumb", (0.024, 0.028, 0.060),
          (SHOULDER_X - 0.030, -0.008, CHEST_Z - 0.720), "frame", bevel=0.005, rot=(0, 0.5, 0))
    right.append(PARTS[g][-1])

    mirror(g, right)


def build_legs() -> None:
    right = []
    g = "leg"
    # thigh 0.70 - 1.02
    armor(g, "thigh", (0.170, 0.200, 0.320), (LEG_X, 0, 0.860), "red",
          top_scale=(0.94, 0.94), bevel=0.014)
    right.append(PARTS[g][-1])
    armor(g, "thigh_front", (0.135, 0.060, 0.250), (LEG_X, -0.110, 0.870), "red_dark",
          bevel=0.008)
    right.append(PARTS[g][-1])
    ball(g, "knee_joint", 0.062, (LEG_X, 0, 0.700), "frame")
    right.append(PARTS[g][-1])
    armor(g, "knee", (0.165, 0.130, 0.140), (LEG_X, -0.065, 0.680), "red",
          top_scale=(0.84, 0.80), bevel=0.012)
    right.append(PARTS[g][-1])
    prism(g, "knee_fin",
          [(-0.058, 0.0), (0.058, 0.0), (0.042, 0.075), (-0.032, 0.058)],
          0.032, (LEG_X, -0.128, 0.740), "red_dark", bevel=0.004)
    right.append(PARTS[g][-1])
    # calf 0.20 - 0.62
    armor(g, "calf", (0.185, 0.220, 0.420), (LEG_X, 0.012, 0.410), "red",
          top_scale=(1.0, 0.90), bevel=0.014)
    right.append(PARTS[g][-1])
    armor(g, "calf_rear", (0.155, 0.115, 0.300), (LEG_X, 0.135, 0.410), "red_dark",
          top_scale=(0.85, 0.9), bevel=0.010)
    right.append(PARTS[g][-1])
    vent(g, "calf_vent", (0.026, 0.085, 0.100), (LEG_X + 0.090, 0.065, 0.430),
          "frame", count=3, vertical=True)
    armor(g, "shin", (0.140, 0.070, 0.280), (LEG_X, -0.110, 0.400), "red_dark", bevel=0.008)
    right.append(PARTS[g][-1])
    # ankle and foot
    armor(g, "ankle", (0.115, 0.125, 0.110), (LEG_X, 0.010, 0.155), "frame", bevel=0.008)
    armor(g, "ankle_guard", (0.150, 0.150, 0.070), (LEG_X, 0.000, 0.195), "red_dark", bevel=0.008)
    right.append(PARTS[g][-1])
    armor(g, "foot", (0.180, 0.370, 0.110), (LEG_X, -0.060, 0.055), "red",
          top_scale=(0.90, 0.82), bevel=0.012)
    right.append(PARTS[g][-1])
    armor(g, "toe", (0.170, 0.135, 0.070), (LEG_X, -0.235, 0.042), "red_dark",
          top_scale=(0.84, 0.8), bevel=0.009)
    right.append(PARTS[g][-1])
    armor(g, "heel", (0.150, 0.110, 0.090), (LEG_X, 0.130, 0.048), "red_dark", bevel=0.009)
    right.append(PARTS[g][-1])
    mirror(g, right)


def build_backpack_and_funnels() -> None:
    g = "backpack"
    armor(g, "pack_body", (0.270, 0.115, 0.240), (0, 0.195, CHEST_Z + 0.020), "red_dark",
          bevel=0.010)
    for side in (1, -1):
        cyl(g, "thruster", 0.055, 0.140, (side * 0.090, 0.255, CHEST_Z - 0.050), "gun",
            rot=(math.pi / 2, 0, 0), verts=20)
        cyl(g, "thruster_inner", 0.040, 0.030, (side * 0.090, 0.320, CHEST_Z - 0.050), "frame",
            rot=(math.pi / 2, 0, 0), verts=20)
        # three funnels per side, lying back along the pack, fanned outward
        for i in range(3):
            prism(g, f"funnel_{side}_{i}",
                  [(-0.036, 0.0), (0.036, 0.0), (0.030, 0.390), (0.0, 0.430), (-0.030, 0.390)],
                  0.052, (side * (0.085 + i * 0.050), 0.235, CHEST_Z + 0.020), "red",
                  rot=(1.52, 0, side * (0.34 + i * 0.10)), bevel=0.004)


def build_weapons() -> None:
    g = "weapon"
    x = SHOULDER_X + 0.022
    # beam shot rifle in the right hand
    armor(g, "rifle_body", (0.085, 0.700, 0.115), (x, -0.280, CHEST_Z - 0.690), "gun",
          bevel=0.006)
    armor(g, "rifle_barrel", (0.048, 0.400, 0.048), (x, -0.800, CHEST_Z - 0.672), "gun",
          bevel=0.004)
    cyl(g, "rifle_muzzle", 0.036, 0.080, (x, -1.005, CHEST_Z - 0.672), "frame",
        rot=(math.pi / 2, 0, 0), verts=16)
    armor(g, "rifle_scope", (0.058, 0.220, 0.058), (x, -0.290, CHEST_Z - 0.690), "gun",
          bevel=0.005)
    armor(g, "rifle_mag", (0.062, 0.110, 0.160), (x, -0.150, CHEST_Z - 0.790), "frame",
          bevel=0.006, rot=(0.22, 0, 0))
    armor(g, "rifle_grip", (0.046, 0.060, 0.100), (x, -0.030, CHEST_Z - 0.760), "frame",
          bevel=0.005, rot=(-0.22, 0, 0))
    # shield on the left forearm
    sx = -(SHOULDER_X + 0.022)
    armor(g, "shield_mount", (0.070, 0.120, 0.160), (sx - 0.055, -0.020, CHEST_Z - 0.400), "frame",
          bevel=0.006)
    prism(g, "shield_main",
          [(-0.150, 0.190), (0.150, 0.190), (0.180, -0.130), (0.065, -0.390),
           (-0.065, -0.390), (-0.180, -0.130)],
          0.075, (sx - 0.110, -0.030, CHEST_Z - 0.420), "red", bevel=0.008)
    prism(g, "shield_face",
          [(-0.118, 0.140), (0.118, 0.140), (0.145, -0.118), (0.048, -0.320),
           (-0.048, -0.320), (-0.145, -0.118)],
          0.032, (sx - 0.162, -0.030, CHEST_Z - 0.410), "red_dark", bevel=0.006)
    prism(g, "shield_emblem",
          [(-0.032, 0.065), (0.032, 0.065), (0.045, -0.012), (0.0, -0.075), (-0.045, -0.012)],
          0.018, (sx - 0.188, -0.030, CHEST_Z - 0.330), "gold", bevel=0.003)


    # final placement tweaks: the rifle sits in the fist, the shield on the arm
    for obj in PARTS["weapon"]:
        if obj.name.startswith("rifle"):
            obj.location.z += 0.075
        if obj.name.startswith("shield"):
            obj.location.x += 0.015


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--views", default="three_quarter")
    ap.add_argument("--res", default="1000x1300")
    args = ap.parse_args(argv)

    clear()
    make_materials(PALETTE)
    build_head()
    build_torso()
    build_waist_and_skirt()
    build_shoulders_and_arms()
    build_legs()
    build_backpack_and_funnels()
    build_weapons()

    studio()
    width, height = (int(v) for v in args.res.split("x"))
    setup_render(args.samples, (width, height))

    if args.render:
        views = {
            "front": (0, 3, 4.9, 60),
            "three_quarter": (30, 7, 4.9, 60),
            "side": (78, 3, 4.9, 60),
            "back": (168, 7, 4.9, 60),
        }
        wanted = list(views) if args.views == "all" else args.views.split(",")
        for name in wanted:
            az, el, dist, lens = views[name]
            camera_view(az, el, dist, lens, target=(0, 0, 0.98))
            render(RENDERS / f"sazabi_{name}.png")

    if args.export:
        export("sazabi")

    print(f"parts: {sum(len(v) for v in PARTS.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
