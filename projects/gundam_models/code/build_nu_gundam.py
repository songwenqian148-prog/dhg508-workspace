"""Nu Gundam (RX-93) as a display figure, built from primitives.

Reference: sources/raw/recovered_02.jpg (full body) and _03.jpg (close-up), both
Bandai product photographs, ©SOTSU·SUNRISE, used only as visual reference.

Run headless:
    blender -b --python code/build_nu_gundam.py -- --render --views three_quarter,front
    blender -b --python code/build_nu_gundam.py -- --render --views all --samples 96
    blender -b --python code/build_nu_gundam.py -- --export

Scale: 1 Blender unit = 1 m, figure about 1.95 m tall, facing -Y, feet on z = 0.
Asymmetric by design: fin funnels on the left of the backpack, beam rifle in the
right hand, shield on the left forearm.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

import bpy

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mecha_kit import (PARTS, RENDERS, armor, ball, camera_view, clear, cyl, export,
                       make_materials, mirror, prism, render, setup_render, studio, vent)

PALETTE = {
    "white": ((0.640, 0.640, 0.620), 0.10, 0.32, 0.35),
    "white_dark": ((0.420, 0.420, 0.410), 0.15, 0.36, 0.25),
    "navy": ((0.025, 0.035, 0.070), 0.30, 0.34, 0.30),
    "red": ((0.115, 0.010, 0.008), 0.20, 0.30, 0.40),
    "yellow": ((0.640, 0.380, 0.030), 0.55, 0.26, 0.30),
    "orange": ((0.300, 0.090, 0.010), 0.45, 0.30, 0.30),
    "frame": ((0.030, 0.030, 0.034), 0.70, 0.42, 0.00),
    "gun": ((0.055, 0.055, 0.062), 0.90, 0.32, 0.00),
    "gold": ((0.360, 0.230, 0.050), 1.00, 0.26, 0.00),
}

HEAD_Z = 1.760
CHEST_Z = 1.430
HIP_Z = 1.020
SHOULDER_X = 0.255
LEG_X = 0.120


def build_head() -> None:
    g = "head"
    armor(g, "helmet", (0.150, 0.160, 0.140), (0, 0.005, HEAD_Z), "white",
          top_scale=(0.86, 0.90), bevel=0.012)
    ball(g, "helmet_dome", 0.080, (0, 0.006, HEAD_Z + 0.072), "white",
         scale=(1.0, 1.04, 0.66))
    armor(g, "face", (0.098, 0.052, 0.088), (0, -0.078, HEAD_Z - 0.030), "white_dark",
          top_scale=(0.84, 1.0), bevel=0.007)
    armor(g, "eye_band", (0.118, 0.020, 0.026), (0, -0.086, HEAD_Z + 0.004), "frame", bevel=0.003)
    armor(g, "eyes", (0.070, 0.012, 0.014), (0, -0.096, HEAD_Z + 0.004), "eye", bevel=0.003)
    armor(g, "chin", (0.070, 0.040, 0.032), (0, -0.072, HEAD_Z - 0.086), "red", bevel=0.005)
    # V-fin: two blades from the forehead
    for side in (1, -1):
        prism(g, "v_fin",
              [(-0.011, 0.0), (0.011, 0.0), (0.014, 0.150), (0.002, 0.170), (-0.010, 0.150)],
              0.016, (side * 0.016, -0.060, HEAD_Z + 0.070), "yellow",
              rot=(0.16, side * 0.62, 0), bevel=0.002)
        armor(g, "cheek", (0.030, 0.068, 0.064), (side * 0.058, -0.030, HEAD_Z - 0.030), "white",
              bevel=0.006)
        cyl(g, "vulcan", 0.010, 0.034, (side * 0.048, -0.090, HEAD_Z + 0.050), "frame",
            rot=(math.pi / 2, 0, 0), verts=12)
    armor(g, "neck", (0.066, 0.066, 0.078), (0, 0, 1.660), "frame", bevel=0.007)


def build_torso() -> None:
    g = "torso"
    armor(g, "chest_white", (0.300, 0.200, 0.290), (0, 0, CHEST_Z), "white",
          top_scale=(1.05, 1.0), bevel=0.014)
    armor(g, "chest_navy", (0.290, 0.190, 0.130), (0, -0.010, CHEST_Z + 0.090), "navy",
          top_scale=(1.02, 1.0), bevel=0.010)
    armor(g, "chest_front", (0.210, 0.080, 0.180), (0, -0.120, CHEST_Z - 0.020), "white",
          top_scale=(0.86, 0.9), bevel=0.010)
    armor(g, "cockpit", (0.120, 0.045, 0.070), (0, -0.160, CHEST_Z - 0.030), "red", bevel=0.006)
    armor(g, "collar", (0.170, 0.140, 0.055), (0, -0.010, CHEST_Z + 0.155), "navy",
          top_scale=(0.80, 0.80), bevel=0.008)
    for side in (1, -1):
        vent(g, "chest_duct", (0.026, 0.080, 0.070), (side * 0.098, -0.150, CHEST_Z + 0.010),
              "orange", count=3, vertical=True)
        armor(g, "torso_side", (0.090, 0.180, 0.220), (side * 0.195, 0.005, CHEST_Z + 0.020),
              "white", top_scale=(0.92, 0.95), bevel=0.010)
        cyl(g, "shoulder_cover", 0.070, 0.060, (side * 0.235, 0, CHEST_Z + 0.090), "white_dark",
            rot=(0, math.pi / 2, 0), verts=20)
        armor(g, "chest_mark", (0.030, 0.110, 0.030), (side * 0.130, -0.110, CHEST_Z + 0.070),
              "red", bevel=0.003, rot=(0, 0, 0.5))
    armor(g, "abdomen", (0.200, 0.165, 0.115), (0, 0, CHEST_Z - 0.210), "white_dark", bevel=0.010)
    for i, z in enumerate((CHEST_Z - 0.170, CHEST_Z - 0.215, CHEST_Z - 0.260)):
        armor(g, f"ab_ring_{i}", (0.195 - i * 0.006, 0.160, 0.030), (0, 0, z), "white",
              bevel=0.005)
    armor(g, "back_plate", (0.270, 0.080, 0.240), (0, 0.125, CHEST_Z + 0.010), "white_dark",
          bevel=0.010)


def build_waist_and_skirt() -> None:
    g = "waist"
    armor(g, "pelvis", (0.270, 0.190, 0.130), (0, 0, HIP_Z), "white", top_scale=(0.94, 0.96),
          bevel=0.012)
    armor(g, "pelvis_front", (0.130, 0.060, 0.115), (0, -0.105, HIP_Z - 0.010), "red",
          top_scale=(0.86, 1.0), bevel=0.007)
    armor(g, "crotch", (0.085, 0.050, 0.085), (0, -0.108, HIP_Z - 0.085), "white_dark", bevel=0.007)
    prism(g, "skirt_front",
          [(-0.085, 0.0), (0.085, 0.0), (0.100, -0.150), (0.0, -0.190), (-0.100, -0.150)],
          0.045, (0, -0.105, HIP_Z - 0.005), "white", bevel=0.006)
    prism(g, "skirt_front_red",
          [(-0.045, 0.0), (0.045, 0.0), (0.052, -0.090), (0.0, -0.120), (-0.052, -0.090)],
          0.020, (0, -0.128, HIP_Z - 0.030), "red", bevel=0.003)
    for side in (1, -1):
        armor(g, "skirt_side", (0.045, 0.170, 0.200), (side * 0.170, -0.010, HIP_Z - 0.050),
              "white", top_scale=(1.0, 0.86), bevel=0.008, rot=(0, side * 0.16, 0))
        armor(g, "skirt_side_red", (0.020, 0.120, 0.026), (side * 0.192, -0.010, HIP_Z - 0.120),
              "red", bevel=0.003)
        ball(g, "hip_joint", 0.055, (side * LEG_X, 0, HIP_Z - 0.045), "frame")
        armor(g, "hip_cover", (0.105, 0.150, 0.080), (side * LEG_X, 0, HIP_Z - 0.028),
              "white_dark", bevel=0.007)
    prism(g, "skirt_rear",
          [(-0.120, 0.0), (0.120, 0.0), (0.135, -0.135), (0.0, -0.170), (-0.135, -0.135)],
          0.048, (0, 0.105, HIP_Z + 0.008), "white_dark", bevel=0.006)


def build_shoulders_and_arms() -> None:
    right = []
    g = "arm"
    armor(g, "pauldron", (0.185, 0.200, 0.170), (SHOULDER_X + 0.060, 0, CHEST_Z + 0.105),
          "white", top_scale=(0.80, 0.88), bevel=0.016)
    right.append(PARTS[g][-1])
    armor(g, "pauldron_lip", (0.200, 0.210, 0.040), (SHOULDER_X + 0.060, 0, CHEST_Z + 0.005),
          "white_dark", bevel=0.008)
    right.append(PARTS[g][-1])
    armor(g, "pauldron_mark", (0.070, 0.070, 0.014), (SHOULDER_X + 0.115, -0.070, CHEST_Z + 0.140),
          "red", bevel=0.002, rot=(0.2, 0, 0.5))
    right.append(PARTS[g][-1])

    cyl(g, "shoulder_ball", 0.058, 0.100, (SHOULDER_X, 0, CHEST_Z + 0.080), "frame",
        rot=(0, math.pi / 2, 0), verts=20)
    right.append(PARTS[g][-1])
    armor(g, "upper_arm", (0.105, 0.105, 0.235), (SHOULDER_X + 0.018, 0, CHEST_Z - 0.100),
          "white", bevel=0.009)
    right.append(PARTS[g][-1])
    ball(g, "elbow", 0.050, (SHOULDER_X + 0.018, 0, CHEST_Z - 0.225), "frame")
    right.append(PARTS[g][-1])
    armor(g, "forearm", (0.135, 0.145, 0.250), (SHOULDER_X + 0.028, 0, CHEST_Z - 0.370),
          "white", top_scale=(1.05, 1.05), bevel=0.012)
    right.append(PARTS[g][-1])
    armor(g, "forearm_cuff", (0.150, 0.160, 0.050), (SHOULDER_X + 0.028, 0, CHEST_Z - 0.258),
          "white_dark", bevel=0.008)
    right.append(PARTS[g][-1])
    armor(g, "wrist", (0.110, 0.115, 0.055), (SHOULDER_X + 0.028, 0, CHEST_Z - 0.510),
          "frame", bevel=0.007)
    right.append(PARTS[g][-1])
    armor(g, "hand", (0.082, 0.092, 0.085), (SHOULDER_X + 0.028, -0.010, CHEST_Z - 0.575),
          "frame", bevel=0.009)
    right.append(PARTS[g][-1])
    for i in range(4):
        armor(g, f"finger_{i}", (0.017, 0.024, 0.066),
              (SHOULDER_X + 0.000 + i * 0.021, -0.052, CHEST_Z - 0.618), "frame", bevel=0.004)
        right.append(PARTS[g][-1])
    armor(g, "thumb", (0.021, 0.025, 0.052), (SHOULDER_X - 0.028, -0.006, CHEST_Z - 0.606),
          "frame", bevel=0.004, rot=(0, 0.5, 0))
    right.append(PARTS[g][-1])
    mirror(g, right)


def build_legs() -> None:
    right = []
    g = "leg"
    armor(g, "thigh", (0.150, 0.175, 0.300), (LEG_X, 0, 0.870), "white",
          top_scale=(0.94, 0.94), bevel=0.012)
    right.append(PARTS[g][-1])
    armor(g, "thigh_side", (0.045, 0.140, 0.200), (LEG_X + 0.085, 0, 0.880), "white_dark",
          bevel=0.006)
    right.append(PARTS[g][-1])
    ball(g, "knee_joint", 0.052, (LEG_X, 0, 0.705), "frame")
    right.append(PARTS[g][-1])
    armor(g, "knee", (0.140, 0.115, 0.120), (LEG_X, -0.058, 0.690), "white",
          top_scale=(0.85, 0.82), bevel=0.010)
    right.append(PARTS[g][-1])
    armor(g, "knee_red", (0.075, 0.045, 0.070), (LEG_X, -0.108, 0.700), "red", bevel=0.005)
    right.append(PARTS[g][-1])
    armor(g, "calf", (0.160, 0.190, 0.400), (LEG_X, 0.010, 0.420), "white",
          top_scale=(1.0, 0.92), bevel=0.012)
    right.append(PARTS[g][-1])
    armor(g, "calf_rear", (0.130, 0.100, 0.280), (LEG_X, 0.115, 0.420), "white_dark",
          top_scale=(0.86, 0.9), bevel=0.008)
    right.append(PARTS[g][-1])
    armor(g, "shin", (0.115, 0.060, 0.260), (LEG_X, -0.095, 0.410), "white_dark", bevel=0.007)
    right.append(PARTS[g][-1])
    armor(g, "ankle", (0.100, 0.110, 0.100), (LEG_X, 0.010, 0.160), "navy", bevel=0.007)
    right.append(PARTS[g][-1])
    armor(g, "ankle_guard", (0.130, 0.130, 0.065), (LEG_X, 0.000, 0.200), "white", bevel=0.007)
    right.append(PARTS[g][-1])
    armor(g, "foot", (0.150, 0.310, 0.095), (LEG_X, -0.055, 0.050), "navy",
          top_scale=(0.90, 0.84), bevel=0.010)
    right.append(PARTS[g][-1])
    armor(g, "toe", (0.140, 0.110, 0.060), (LEG_X, -0.200, 0.040), "white",
          top_scale=(0.86, 0.8), bevel=0.007)
    right.append(PARTS[g][-1])
    armor(g, "heel", (0.120, 0.090, 0.070), (LEG_X, 0.110, 0.042), "white_dark", bevel=0.007)
    right.append(PARTS[g][-1])
    mirror(g, right)


def build_backpack_and_fin_funnels() -> None:
    g = "backpack"
    armor(g, "pack", (0.230, 0.110, 0.220), (0, 0.180, CHEST_Z + 0.020), "white_dark",
          bevel=0.010)
    # right side: propellant tank
    cyl(g, "tank", 0.075, 0.230, (0.150, 0.210, CHEST_Z + 0.010), "white",
        rot=(math.pi / 2, 0, 0), verts=24)
    cyl(g, "tank_cap", 0.078, 0.030, (0.150, 0.330, CHEST_Z + 0.010), "navy",
        rot=(math.pi / 2, 0, 0), verts=24)
    # left side: six fin funnels stacked as a wing
    for i in range(6):
        offset = i * 0.034
        prism(g, f"fin_funnel_{i}",
              [(-0.026, 0.0), (0.026, 0.0), (0.022, 0.300), (0.0, 0.340), (-0.022, 0.300)],
              0.026, (-0.115 - offset * 0.55, 0.235 + offset * 0.30, CHEST_Z + 0.070 + offset),
              "white", rot=(0.30, 0, 0.22), bevel=0.003)
        armor(g, f"funnel_tip_{i}", (0.026, 0.026, 0.036),
              (-0.115 - offset * 0.55, 0.330 + offset * 0.30, CHEST_Z + 0.390 + offset),
              "red", bevel=0.002)


def build_weapons() -> None:
    g = "weapon"
    x = SHOULDER_X + 0.028
    # beam rifle in the right hand
    armor(g, "rifle_body", (0.070, 0.560, 0.095), (x, -0.250, CHEST_Z - 0.560), "gun", bevel=0.006)
    armor(g, "rifle_barrel", (0.038, 0.330, 0.038), (x, -0.660, CHEST_Z - 0.545), "gun",
          bevel=0.004)
    cyl(g, "rifle_muzzle", 0.028, 0.060, (x, -0.850, CHEST_Z - 0.545), "frame",
        rot=(math.pi / 2, 0, 0), verts=16)
    armor(g, "rifle_scope", (0.048, 0.190, 0.048), (x, -0.245, CHEST_Z - 0.500), "gun",
          bevel=0.005)
    armor(g, "rifle_mag", (0.052, 0.090, 0.120), (x, -0.140, CHEST_Z - 0.640), "frame",
          bevel=0.005, rot=(0.20, 0, 0))
    armor(g, "rifle_grip", (0.040, 0.050, 0.080), (x, -0.040, CHEST_Z - 0.620), "frame",
          bevel=0.005, rot=(-0.20, 0, 0))
    # shield on the left forearm
    sx = -(SHOULDER_X + 0.028)
    armor(g, "shield_mount", (0.060, 0.110, 0.150), (sx - 0.050, -0.020, CHEST_Z - 0.380),
          "frame", bevel=0.006)
    prism(g, "shield_main",
          [(-0.135, 0.180), (0.135, 0.180), (0.160, -0.140), (0.055, -0.400),
           (-0.055, -0.400), (-0.160, -0.140)],
          0.065, (sx - 0.095, -0.020, CHEST_Z - 0.330), "white", bevel=0.008)
    prism(g, "shield_edge",
          [(-0.110, 0.140), (0.110, 0.140), (0.132, -0.126), (0.045, -0.335),
           (-0.045, -0.335), (-0.132, -0.126)],
          0.030, (sx - 0.140, -0.020, CHEST_Z - 0.320), "white_dark", bevel=0.006)
    # the red unicorn mark, simplified to a chevron
    prism(g, "shield_mark",
          [(-0.020, 0.070), (0.036, 0.050), (0.020, 0.010), (0.050, -0.010),
           (0.010, -0.080), (0.0, -0.030), (-0.030, -0.020)],
          0.016, (sx - 0.160, -0.020, CHEST_Z - 0.250), "red", bevel=0.002)


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
    build_backpack_and_fin_funnels()
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
            camera_view(az, el, dist, lens, target=(0, 0, 1.00))
            render(RENDERS / f"nu_gundam_{name}.png")

    if args.export:
        export("nu_gundam")

    print(f"parts: {sum(len(v) for v in PARTS.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
