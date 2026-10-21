# Notes: how the two figures were built, and what they are not

## Method

Each figure is assembled from parametric primitives in `code/mecha_kit.py`:
`armor()` (a box whose top face can be tapered and shifted), `prism()` (an
extruded 2D outline, used for skirts, funnels, fins and the shield), `cyl()` and
`ball()` for joints, plus `vent()` for grilles and `mirror()` for the symmetric
half. Colours are four to ten shared materials per figure, so the colour
separation is deliberate rather than painted on.

Proportion landmarks are declared at the top of each build script and were tuned
against the photographs:

| Landmark | Sazabi | Nu Gundam |
| --- | --- | --- |
| Figure height | 1.90 m (display scale) | 1.95 m |
| Head centre | 1.71 | 1.76 |
| Chest centre | 1.39 | 1.43 |
| Hip | 1.00 | 1.02 |
| Shoulder half-width | 0.30 | 0.255 |
| Leg centre | 0.135 | 0.120 |
| Pauldron size | 0.24 × 0.26 × 0.23 | 0.19 × 0.20 × 0.17 |

`code/measure_refs.py` measures the reference silhouettes as widths at fractions
of the figure height (`research/ref_measurements.json`). The numbers are dominated
by the shield and the funnels in the front views, so they were used as a sanity
check, not as a source of exact dimensions.

## What is modelled

**Sazabi (143 parts).** Mono-eye visor set in a recessed band, dome helmet, swept
crest; broad chest with a cockpit hatch and gold trim; segmented abdomen with the
gold waist pipe; oversized pauldrons with lip, side vent and swept fin; thick
forearm gauntlets; big front/side/rear skirt plates; flared calves; broad feet
with toe and heel blocks; backpack with two thrusters and six funnels on fanned
racks; beam shot rifle in the right hand; shield with a gold emblem on the left
forearm.

**Nu Gundam (130 parts).** White helmet with a yellow V-fin and a red chin, dark
eye band; navy upper chest with orange ducts and red markings; white abdomen and
skirt with red accents; smaller pauldrons with a red "A" block; slimmer arms and
legs with navy ankle/foot blocks; backpack with a propellant tank on the right and
six fin funnels stacked on the left; beam rifle; white shield with a simplified
red mark.

## What is deliberately not there

- **No articulation.** Arms and legs are built in a static A-pose; the exported
  GLB is a single static assembly, not a rig.
- **No panel lines, decals or weathering.** Adding them is a texturing job, not a
  geometry job, and it would multiply the triangle count for detail that does not
  change the silhouette.
- **No inner frame.** The joints are simple cylinders and spheres; nothing is
  visible when a plate is removed.
- **Simplified marks.** Sazabi's shield emblem is a gold lozenge; Nu's unicorn
  mark is a red chevron. Both are suggestions of the painted insignia, not
  reproductions.

## Why not image-to-3D

The same route used for the rifle in `week-07` was tried here first
(`code/image_to_3d.py`, Hunyuan3D 2 on the front photograph). The result
(`artifacts/gundam/image_to_3d/sazabi_shape.glb`, 16.6 MB) keeps the silhouette
but smears every detail: the rifle merges into the hand, the funnels become
spikes, the skirt fuses with the thighs. As a display model it was worse than the
hand-built figure, so the hand-built route was kept and the AI mesh kept only as
the comparison in this note.

That is the same trade the rifle documented: image-to-3D wins on silhouette and
loses on parts, and for a mecha whose identity is in its parts the script-built
version is the better base.

## Difficulties worth recording

1. **The first two passes read as a pink robot.** The red was a physically
   plausible albedo (0.30, 0.02, 0.02) but under the AgX view transform with a
   coat layer it rendered salmon. Dropping the albedo to 0.08 and the coat to 0.45
   fixed it. Nu's red went from 0.32 to 0.115 for the same reason.
2. **Parts floated.** The first build had feet detached from the legs and arms
   disconnected from the torso: the landmark table had been written down twice
   with different numbers. Adding the ankle guards, torso side fairings, shoulder
   covers and hip covers closed the gaps; the lesson is to derive every part's
   height from the same table instead of typing coordinates per part.
3. **The funnels read as antlers.** Mounted at shoulder height and rotated
   outward, Sazabi's six funnels looked like horns. They were moved down onto the
   pack and swept back by about 85 degrees so they sit behind the shoulders.
4. **Blender cannot write into this project.** The session sandbox allows writes
   only inside `508-coursework/week-07`, so the build scripts write to
   `week-07/artifacts/gundam/` and `code/collect.ps1` copies the results here.
   `mecha_kit.py` reads `MECHA_OUT` if a different output directory is ever
   needed.
