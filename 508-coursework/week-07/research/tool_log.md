# Tool log: what each tool did, what the AI did, what I checked

The assignment asks for a record of what each tool did, what the AI did, and
what I checked myself. This file is that record. Costs are in
[`README.md`](../README.md#costs); every tool below was free.

## Summary table

| Step | Tool | Version / endpoint | What it did | Cost |
| --- | --- | --- | --- | --- |
| Sources | Wikimedia Commons API | `commons.wikimedia.org/w/api.php`, 20 Oct 2026 | returned file page, author, licence, date for each of the 21 images | 0 |
| Sources | web fetch of three reference pages | Wikipedia, Modern Firearms, Royal Armouries via Flickr, 20 Oct 2026 | full page text, saved as plain text and quoted | 0 |
| Step 2 images | Pollinations text-to-image | `image.pollinations.ai/prompt/...`, anonymous tier | text-to-image, no API key, 1 image / 45 s | 0 |
| Step 3 model A | Blender (portable zip) | 4.5.14 LTS, Windows x64 | built the mesh from a Python script, Cycles renders | 0 |
| Step 3 model A | Cycles renderer | OptiX backend on an RTX 3060 Laptop | 6 stills at 1800x1200, 60-frame turntable | 0 |
| Step 3 model B | Tencent Hunyuan3D 2, image-to-3D | official Hugging Face Space, `/shape_generation`, anonymous | one photograph in, untextured mesh out, 57 s | 0 |
| Encoding | FFmpeg via `imageio-ffmpeg` | pip package | turned the PNG frames into an MP4 | 0 |
| All text | this agent (DeepSeek Harness) + the scripts | - | reading, measuring, writing, rendering, checking | 0 |

Nothing was bought; no receipts exist because nothing cost anything. The only
"spend" is electricity and about 400 MB of Blender download.

## What the AI did, and what I checked

"AI" here means the coding agent, the image generator, and the image-to-3D
service. Where the agent produced a number or a claim, the check is stated next
to it.

| Claim or artefact | Produced by | Checked how |
| --- | --- | --- |
| The Type 1 to Type 2 to Type 3 dates and reasons | agent read S1 and S2, then wrote the summary | both sources quoted verbatim in [`sources.md`](sources.md); the two agree on 1951, 1955 and 1959 |
| 870 mm / 415 mm / 4.3 kg / 30 rounds / 600 rpm | S2 specification table | read directly from the saved text, lines 878-894 of `sources/processed/text/modernfirearms_ak47.txt` |
| 3.47 kg (Type 3) | S1 variant list | read directly; S1 and S2 differ on "about 0.5 kg lighter" vs "3.47 kg", both recorded rather than averaged |
| Proportions of the 3D model (stock 241 mm, receiver 291 mm, exposed barrel 338 mm) | agent measured the pixels of `15_ak47_type2_right_side_view.jpg` | measured with `code/measure_reference.py`: 1220 px = 870 mm, then each landmark converted; the three parts add up to 870 mm |
| The hand-built model geometry | `code/build_ak47_type2.py` | rendered and looked at from five angles, then corrected four times (see below) |
| The image-to-3D mesh and its numbers | Tencent Hunyuan3D 2 via its Hugging Face Space | re-imported into Blender and printed bbox and triangle count; counted shells and watertightness with trimesh: 14,585 shells, not watertight, no texture |
| The two comparison images | Pollinations | looked at every returned file; several were unusable and are kept as evidence, not used |
| The written comparison | agent, from the images and sources | every feature claimed in `comparison.md` was pointed at in a specific source image or text line |

## What the AI got wrong, and how it was caught

This is the honest part; the failures are also the difficulties the assignment
asks for.

1. **The 3D model was first hung from a single hard-coded camera.** The first
   render framed the receiver from 30 cm and cut off both ends. Cause: a 62 mm
   lens 1 m away from a 0.87 m object. Caught by looking at the render; fixed by
   computing camera positions from distance and lens instead of guessing.
2. **The stock, grip and trigger guard floated** in the second render: the grip
   raked forward, the guard was three boxes in mid-air. Caught by comparing the
   render with `15_ak47_type2_right_side_view.jpg`; fixed by re-measuring the
   reference and moving the parts into the receiver.
3. **The wood looked like corduroy.** The procedural grain used
   `bands_direction = "X"` with a 12x mapping, which drew stripes across the
   stock instead of along it. Caught in the render, fixed to "Z" bands with lower
   distortion.
4. **The turntable orbited the rifle instead of spinning it.** The empty that
   carries the model sat at the world origin, which is the rear of the receiver,
   so the rifle swung out of frame. Caught in the rendered frames; fixed by
   putting the empty at the model's centre and offsetting every child.
5. **Blender's own FFmpeg wrote an empty MP4.** After 30 minutes the file was
   48 bytes. Caught by checking the file size; fixed by rendering PNG frames and
   encoding them outside Blender with `imageio-ffmpeg`.
6. **The image service silently downgraded the request.** `width=1024&height=768`
   came back as an 886x665 JPEG even when the file was named `.png`. Two files
   had to be re-encoded before any tool would read them;
   `code/fix_image_format.py` does that.
7. **The free image tier's rate limit looked like a server error.** `402
   FREE_LIMIT` with "Retry after 32s" arrives when more than one image per 45 s
   is requested. The generator scripts now read the hint, wait, and log every
   attempt.
8. **Hunyuan3D's texture step never ran.** Three separate walls, all recorded in
   `artifacts/hunyuan/`: 2.0's `/generation_all` raises a bare `NameError` for an
   anonymous caller even with `caption=None`; 2.1 refuses anonymous jobs with
   "the requested GPU duration (270s) is larger than the maximum allowed" (it
   wants Hugging Face PRO); every public fork of the 2.0 Space tried was paused
   or in a runtime error state. What did work was 2.0's `/shape_generation`,
   which returns an untextured mesh - so the delivered image-to-3D model has
   geometry and no surface colour.


9. **The four-stage timeline kept flattening one row.** Stacked vertically, the
   top row sat closer to the key light and read as a different metal; stacked
   horizontally, the row nearest the key light did the same. The fix was to put
   the four rows on one line and light them with a single broad source centred on
   that line, then set exposure by eye against the backdrop - five poster renders
   before the four stages matched.

## Difficulties

The one the assignment asks for, plus the others.

**Main difficulty: the generator cannot draw the object the research describes.**
This is the example. The researched prompt names the exact features of a 1953
Type 2 - milled receiver, one-piece wooden grip, wooden handguards, curved steel
magazine, no optic. What came back (`generated/final/researched/seed11_short_prompt.jpg`)
has wooden furniture and a fused mass where the receiver should be: two
buttstocks, a handguard where the barrel belongs, no workable rifle. Three
rounds of prompts and six seeds fail the same way. What I did about it:
shortened the prompt to the features a 2D generator can express, requested
several seeds, and kept the failures as evidence. What I did *not* do: use
image-to-image with the reference photograph, which would have made the
"researched" image look better while proving nothing about research.

**Second difficulty: no Blender on this machine.** Downloaded the portable
Windows build (398 MB, 35 MB/s), unpacked it into `artifacts/tools/`
(git-ignored) and ran it headless with `-b --python`, so nothing was installed
system-wide.

**Third difficulty: the shell could not start work at all.** The first command
of the session failed with `SetNamedSecurityInfoW failed (Win32 5)` - the
workspace folder was missing a permission for the signed-in user, so *every*
command failed, not just file writes. Fixed with the bundled ACL diagnosis
script, which added the missing permission for this user only and printed the
rollback command.

**Fourth difficulty: the numbers in the sources disagree slightly.** Modern
Firearms says the Type 3 was "about 0.5 kg less" than the Type 2 and gives the
1949 pattern as 4.3 kg empty; Wikipedia gives the Type 3 as 3.47 kg, which is
0.83 kg less. I did not average them. The model uses S2 for dimensions and the
discrepancy is recorded here and in `questions.md`.

**Fifth difficulty: the two 3D routes fail in opposite directions.** The
hand-built model has parts and the wrong silhouette; the Hunyuan mesh has the
right silhouette and no parts at all (14,585 shells, not watertight, far side
invented, no texture). Neither is a finished asset. The honest position is that
the pair together document what each method knows, which is why the comparison
figure puts them side by side instead of choosing one.
