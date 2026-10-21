# artifacts/

Git-ignored working files. Nothing here is needed to read the submission; it is
here so the work can be re-run without downloading everything again.

| Path | What it is | Size |
| --- | --- | --- |
| `tools/blender-4.5.14-windows-x64.zip` | the portable Blender download | 380 MB |
| `tools/blender-4.5.14-windows-x64/` | the unpacked Blender 4.5.14 LTS | ~1 GB |
| `renders/*.png` | full-resolution 1800×1200 Cycles stills (web-size JPEG copies live in `../generated/renders/`) | ~13 MB |
| `frames/frame_0001..0060.png` | the 60 turntable frames at 1280×720 | ~55 MB |
| `video/turntable.mp4` | the encoded clip (a copy is in `../generated/turntable.mp4`) | 0.5 MB |
| `model/ak47_type2.blend`, `ak47_type2.glb` | last export written by the script (committed copies are in `../model/`) | 1.4 MB |

To rebuild from scratch: delete `tools/`, download the zip from
<https://download.blender.org/release/Blender4.5/blender-4.5.14-windows-x64.zip>,
unzip it here, and follow `../code/README.md`.
