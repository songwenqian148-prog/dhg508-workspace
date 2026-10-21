# Scripts

Everything in the submission is produced by these scripts. They are kept so the
work can be checked and rebuilt, not because the assignment needs code for its
own sake.

Paths are absolute to this workspace at the top of each Python file (`ROOT`);
change that one constant to run them elsewhere.

## Sources

| Script | What it does |
| --- | --- |
| `fetch_commons_metadata.py` | asks the Wikimedia Commons API for the file page, author, licence and date of the 21 reference images and writes `sources/raw/provenance.json`. Rate-limited and resumable after the first run hit HTTP 429. |
| `fetch_text_sources.py` | downloads the two text sources (Wikipedia AK-47, Modern Firearms) as plain text into `sources/processed/text/`, URL on line 1. |
| `build_sources_doc.py` | writes `research/sources.md` from `provenance.json` plus the quoted text sources, so the attribution table cannot drift from the metadata. |

## Step 2, the images

| Script | What it does |
| --- | --- |
| `generate_images.py` | round 1: one 150-word researched prompt and one naive prompt, three seeds each, written to `generated/`. |
| `generate_variants.py` | shorter prompt variants tried after round 1 (kept for the record; the rate limit stopped it). |
| `generate_final_images.py` | Python version of the final loop; it produced the first pair of round 2. |
| `gen_final.ps1` | round 2, the images actually used: one request at a time, waits out `402 FREE_LIMIT` using the retry hint, logs every attempt. |
| `gen_logged.ps1` | same idea with a long fixed wait, used while the quota was exhausted. |
| `gen_control_seed11.ps1` | the matched-seed control: prompt B at seed 11, the same seed as the control image. |
| `fix_image_format.py` | re-encodes the generator's JPEG-in-a-PNG-filename output. |
| `make_comparison_sheet.py` | draws the class sheet: the two images, labels, prompts and captions, nothing retyped by hand. |
| `make_control_check.py` | draws the 2x2 control figure: control and treatment at seed 11, then at a second seed. |
| `update_manifest.py` | reconciles `generated/final/manifest_final.json` with the files actually present, adding prompt, seed, bytes and MD5. |

## Step 3, the models

| Script | What it does |
| --- | --- |
| `measure_reference.py` | thresholds `01_ak47_general_view.png` and prints the silhouette landmarks in millimetres; this is where the model's part positions come from. |
| `build_ak47_type2.py` | builds the AK-47 Type 2 in Blender from those dimensions, sets up the studio and cameras, renders the stills, exports `.blend`/`.glb`, renders the turntable frames. Run headless; see the flags at the bottom of the file. |
| `encode_video.py` | encodes `artifacts/frames/*.png` into `artifacts/video/turntable.mp4` with the ffmpeg binary from `imageio-ffmpeg`. |
| `field_strip.py` | the exploded-view animation: borrows the geometry from `build_ak47_type2.py` via runpy, separates the rifle into seven labelled groups in field-strip order, holds, reassembles. `--poster` renders the labelled still, `--frames` renders the 168-frame sequence. |
| `encode_strip.py` | encodes a frame folder into an MP4; defaults to the field-strip frames, and takes `--frames/--out/--pattern` for other clips. |
| `variants_timeline.py` | the historical comparison: re-uses the Type 2 geometry, edits copies into the 1949 / 1951 / 1955 / 1959 stages, stacks them on a timeline and renders the 180-frame animation. |
| `hunyuan3d_try.py` | image-to-3D with Hunyuan3D 2 through its official Hugging Face Space: prepares the input image, calls `/generation_all` and falls back to `/shape_generation`, saves the GLB and a JSON record. |
| `hunyuan3d_probe.py` | the earlier probe that found which endpoints answer an anonymous call. |
| `hunyuan21_generate.py` | the Hunyuan3D 2.1 attempt (shape + texture); it fails anonymously because 2.1 asks for 270 s of GPU. |
| `hunyuan_texture_probe.py` | walks the public forks of the 2.0 Space looking for a working textured endpoint; all were paused or broken. |
| `prepare_hunyuan_asset.py` | scales the returned mesh to the published 870 mm, centres it, publishes `model/ak47_hunyuan3d.glb`, and writes the measurement JSON (vertices, triangles, shells, watertight). |
| `render_glb.py` | renders any imported GLB in the same studio as the hand-built model, so the two can be compared without a change of light or camera. |
| `make_model_comparison.py` | draws the comparison figure of the two 3D routes; a panel is drawn only when its render exists. |

## Housekeeping

| Script | What it does |
| --- | --- |
| `check_links.py` | checks every relative link and anchor in the Markdown files (it skips `artifacts/`, which is git-ignored). |
| `fix_readme_tree.py` | rewrites the README folder map in plain ASCII after an encoding round-trip mangled the box-drawing characters. |

## Commands that produced the submission

```powershell
python code/fetch_commons_metadata.py
python code/fetch_text_sources.py
python code/build_sources_doc.py
powershell -NoProfile -ExecutionPolicy Bypass -File code/gen_final.ps1
python code/update_manifest.py
python code/make_comparison_sheet.py
python code/make_control_check.py

$blender = "artifacts/tools/blender-4.5.14-windows-x64/blender.exe"
& $blender -b --python code/build_ak47_type2.py -- --hero --explode-still --export --samples 96 --gpu
& $blender -b --python code/build_ak47_type2.py -- --frames-png --gpu --samples 28 --frames 60
python code/encode_video.py

python code/hunyuan3d_try.py --shape-only --seed 1234 --steps 30 --octree 256
python code/prepare_hunyuan_asset.py artifacts/hunyuan/ak47_hunyuan3d_shape.glb ak47_hunyuan3d
& $blender -b --python code/render_glb.py -- --glb artifacts/hunyuan/ak47_hunyuan3d_shape.glb --prefix hunyuan
python code/make_model_comparison.py

python code/check_links.py
```
