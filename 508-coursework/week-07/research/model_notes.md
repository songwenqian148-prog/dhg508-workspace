# The 3D model: what it is, what it is not

Two routes were actually run, because the brief allows "an agent building it in
Blender, an image-to-3D service, or both":

- **Route A, built by script in Blender** - the parts model the Type 2 features
  one by one. This is the model used for the renders and the turntable.
- **Route B, Tencent Hunyuan3D 2 (image-to-3D)** - one photograph in, one mesh
  out. It captures the silhouette better than the hand-built model and knows
  nothing about parts. Section "Route B" below has the numbers and the failures.

Comparison figure: [`generated/model_route_comparison.png`](../generated/model_route_comparison.png).

## Route A: the Blender model

**File:** [`model/ak47_type2.blend`](../model/ak47_type2.blend) (Blender scene,
1.0 MB) and [`model/ak47_type2.glb`](../model/ak47_type2.glb) (glTF binary with
embedded materials, 0.4 MB). The same two files are also written to
`artifacts/model/` when the script runs.
**Built by:** `code/build_ak47_type2.py`, run headless in Blender 4.5.14 LTS.
**Renders:** six stills, 1800×1200, Cycles, 96 samples. Web-size copies in
[`generated/renders/`](../generated/renders); full-resolution PNGs in the
git-ignored `artifacts/renders/`.
**Clip:** 60-frame turntable, 1280×720, 28 samples, one full rotation:
[`generated/turntable.mp4`](../generated/turntable.mp4).

## Dimensions and where each came from

| Dimension | Value used | Source |
| --- | --- | --- |
| Overall length | 870 mm | S2 specification table |
| Barrel length | 415 mm | S2 specification table |
| Empty weight (for reference, not modelled) | 4.3 kg | S2 specification table |
| Receiver length | 291 mm | measured on `15_ak47_type2_right_side_view.jpg` |
| Buttstock length | 241 mm | measured on the same photograph |
| Exposed barrel, receiver front to muzzle | 338 mm | measured on the same photograph |
| Butt plate height | ~112 mm | measured on the same photograph |
| Overall height, top of rear sight to magazine floor | ~330 mm | measured on the same photograph |

How the photograph was measured: the rifle occupies 1220 px in
`01_ak47_general_view.png`, and the real rifle is 870 mm, so 1 px = 0.713 mm.
The silhouette was thresholded and sampled in columns (`code/measure_reference.py`),
which gives the position of the wrist, the receiver front, the handguard front,
the gas block and the muzzle. Those landmarks set the part positions in the
script, and 241 + 291 + 338 = 870 mm, which is the check that they add up.

## Type 2 features the model deliberately carries

- **Receiver machined from one block**, modelled as a single solid slab with flat
  sides - no rivet rows, no separate trunnions, which is what separates it from
  the stamped Type 1 and the AKM (S2).
- **A shallow lightening pocket** on each side above the magazine. The Type 2
  keeps this pocket; the Type 3 deepens and lengthens it (S2).
- **Steel stock socket pinned to the rear of the receiver**, with two pin heads
  modelled (S2: "separate mounting socket … pinned to the rear end").
- **One-piece wooden pistol grip on a separate base, one vertical bolt** (S2).
- **Wooden buttstock, wooden upper and lower handguards** (S2, and visible in
  `15_ak47_type2_right_side_view.jpg`).
- **Forward sling loop at the front of the lower handguard**, not on the gas
  block: the move to the gas block is a Type 3 change (S2).
- **No bayonet lug.** The early rifles had "no provision for a bayonet"; the
  knife bayonet arrives with the Type 3 (S2).
- **Curved 30-round slab-sided steel magazine**, 30 mm thick, swept on a 0.45 m
  arc so that the floor plate sits about 60 mm forward of the top - the curve in
  the reference photograph.
- **Tall front sight base and hooded post near the muzzle**, tangent rear sight
  with a notch at the receiver front.

## What the model does not represent

- It is a **block-out**, not a manufacturing model. Springs, the bolt and the gas
  piston are single primitives; the receiver interior does not exist; there is no
  fire-control geometry inside the trigger guard.
- The **wood grain** is a procedural texture, not a scan; it is there so the
  material reads as varnished birch at render size.
- **No markings**: no serial numbers, no Izhmash stamp, no date. A 1953 receiver
  would carry them. I did not invent any, because inventing a serial number would
  be inventing evidence.
- **No sling**, no cleaning kit, no magazine pouch: all of those appear in the
  photographs, none of them are part of the object's Type 2 identity.

## Route B: Tencent Hunyuan3D 2, image-to-3D

**Service:** the official Hugging Face Space that runs Tencent's open weights,
`tencent/Hunyuan3D-2`, endpoint `/shape_generation`. Anonymous call, no key,
no card, cost 0. Tencent Cloud's `hunyuan.tencentcloudapi.com` also offers this
model but needs a SecretId/SecretKey pair, and there is none in this workspace.

**Input:** `sources/raw/AK-47_type_II_noBG.png.webp` - the transparent-background
Type 2 cut-out, composited onto white by `code/hunyuan3d_try.py` and written to
`artifacts/hunyuan/input.png` (960×372). The Space's own background removal was
left switched on.

**Settings:** steps 30, guidance scale 5.0, seed 1234, octree resolution 256,
remove background on. **Wall time: 57 s.**

**Output:** `artifacts/hunyuan/ak47_hunyuan3d_shape.glb` (948 KB, untextured),
normalised to real size by `code/prepare_hunyuan_asset.py` and published as
[`model/ak47_hunyuan3d.glb`](../model/ak47_hunyuan3d.glb), with the measurements
in [`model/ak47_hunyuan3d.json`](../model/ak47_hunyuan3d.json):

| Measurement | Value |
| --- | --- |
| Vertices / triangles | 21,444 / 57,480 |
| Bounding box | 870 × 258 × 61.5 mm |
| Scale applied to reach 870 mm | ×0.4438 (the service returns an arbitrary scale) |
| Watertight | no |
| Separate shells | 14,585 |
| Texture | none (see below) |

**What it does better than Route A:** the silhouette. The stock profile, the
stepped receiver top, the handguard break, the trigger guard, the curve of the
magazine and the height of the front sight are all where the photograph puts
them, because they were read off the photograph rather than typed in as
coordinates. In `model_route_comparison.png` the right-hand panel looks like the
object; the left-hand panel looks like a diagram of it.

**What it cannot do at all:**

- **No parts.** The mesh is one fused surface: 14,585 disconnected shells, no
  watertight volume, no separate magazine, no bore, no bolt carrier, no springs.
  You cannot field-strip it, animate a reload, or measure the receiver.
- **The far side is invented.** Only one view went in, so the left side is a
  plausible continuation of the right side, not evidence.
- **No texture.** Two attempts to get one failed and are recorded in
  `artifacts/hunyuan/` and in [`tool_log.md`](tool_log.md#difficulties): the 2.0
  Space's `/generation_all` (shape + texture) raises a bare `NameError` for an
  anonymous caller, and 2.1 - which does shape and texture in one call - refuses
  anonymous jobs with *"the requested GPU duration (270s) is larger than the
  maximum allowed"*, i.e. it wants Hugging Face PRO. Every public fork of the
  2.0 Space that was tried was either paused or in a runtime error state.
- **Not dimensionally trustworthy.** The service returns a correctly proportioned
  mesh at an arbitrary scale; 870 mm exists here only because the length was
  normalised afterwards to the published figure.

## Why Blender, and why headless

There is no Blender on this machine, so the route was: download the portable
build into `artifacts/tools/` (git-ignored), drive it with
`blender -b --python`, and render with Cycles on the RTX 3060 through the OptiX
backend. Nothing was installed system-wide; deleting `artifacts/tools/` removes
every trace of Blender. The image-to-3D route came later and is additive: it
answered the part the hand-built model is weakest at (silhouette) and failed at
the part the hand-built model is strongest at (parts).

## Export notes

- `ak47_type2.glb` was exported with the glTF exporter using the "apply
  modifiers" option, so the bevels are baked into the mesh. It opens in any
  glTF viewer; the materials are Principled BSDF translated to glTF PBR, so the
  procedural wood grain does **not** survive the export - the GLB shows flat
  colours, while the renders show the grain.
- `ak47_type2.blend` keeps the full node setup and the studio lighting rig, so
  the stills can be re-rendered exactly.
