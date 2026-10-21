# Prompts

Every prompt that produced something, kept verbatim, with the file it produced.
Nothing was edited after generation: the comparison sheet uses the files exactly
as the service returned them.

## The pair that is used

**A, words alone** - `generated/final/baseline/seed11.jpg`, seed 11:

> a photograph of an AK-47 rifle, side view, whole rifle, plain background

**B, from the sources** - `generated/final/researched/wooden_stock.jpg`, seed 61:

> a photograph of an AK-47 rifle with a wooden stock and wooden handguard, no
> scope, side view, whole rifle, plain background

Both were sent to
`https://image.pollinations.ai/prompt/<prompt>?width=1024&height=768&seed=<seed>&nologo=true`,
which returns an 886×665 JPEG (it ignores the requested size) and allows one
image every 45 seconds per address.

## Why B is so short

B is the third researched prompt, not the first. The prompt was cut down after
each longer version made the picture worse - which is itself the main
difficulty, written up in [`tool_log.md`](tool_log.md#difficulties).

| Attempt | Prompt length | What came back |
| --- | --- | --- |
| 1 | 150 words, the whole research: milled receiver, pinned socket, single grip bolt, sling loop, sight, finish | two receivers, two magazines, a second barrel (`generated/b_from_sources/seed23.png`) |
| 2 | 40 words, same facts in catalogue-photo form | wooden jumble, no assemblable rifle (`generated/final/researched/seed11.jpg`) |
| 3 (used) | 20 words, only what a 2D generator can express: wooden furniture, no scope, side view | a coherent wooden-stocked rifle, plus invented rail and hand (`generated/final/researched/wooden_stock.jpg`) |

The three facts kept in attempt 3 are the three the sources most clearly
establish and that the baseline contradicts:

| Clause | Where it comes from |
| --- | --- |
| "wooden stock and wooden handguard" | [S2](sources.md): one-piece wooden grip, wooden stock, wooden handguards; visible in `15_ak47_type2_right_side_view.jpg` |
| "no scope" | a 1953 rifle has a tangent rear sight, not an optic; [S3](sources.md) dates the object inside the Type 2 run |
| "side view, whole rifle" | both images must be comparable, and the baseline kept cropping or duplicating the object |

The facts that were dropped from the prompt - milled receiver, pinned stock
socket, single grip bolt, sling loop position, no bayonet lug - did not
disappear from the work. They became the checklist used to judge every
candidate (see [`comparison.md`](comparison.md)), and they are the specification
for the 3D model in [`../code/build_ak47_type2.py`](../code/build_ak47_type2.py).

## Prompt ledger

| File | Prompt | Seed | Outcome |
| --- | --- | --- | --- |
| `generated/a_words_only/seed11.png` | round 1 baseline: "a photograph of an AK-47 assault rifle on a table" | 11 | black rifle with an invented scope and case |
| `generated/a_words_only/seed23.png` | round 1 baseline, same prompt | 23 | cropped close-up, two magazines |
| `generated/a_words_only/seed37.png` | round 1 baseline, same prompt | 37 | not used |
| `generated/b_from_sources/seed23.png` | round 1 researched, 150 words | 23 | two receivers, two magazines - kept as evidence |
| `generated/final/baseline/seed11.jpg` | A, final | 11 | **used**, left panel of the sheet |
| `generated/final/researched/seed11.jpg` | round 2 researched, 40 words | 11 | wooden jumble - kept as evidence |
| `generated/final/researched/wooden_stock.jpg` | B, final, 20 words | 61 | **used**, right panel of the sheet |
| `generated/final/*/seed23`, `seed37`, `seed41` | same prompts, extra seeds | 23/37/41 | blocked by the 45 s rate limit; a few error stubs remain in the log |

The request that failed is kept in `generated/final/log.txt` and `log2.txt`,
with the service's own `402 FREE_LIMIT` message and the retry delays. The
manifests (`generated/manifest.json`, `generated/final/manifest_final.json`)
record prompt, seed, service, byte count, MD5, and cost 0 for every image.

## Note on the generator

The service advertises only a default text-to-image model. Passing
`model=flux`, `model=turbo` or `model=sana` made no difference to the returned
bytes, so the manifests record "model requested" and a note that the parameter is
not honoured. This matters for reproducibility: another run of the same prompt
and seed may not return the same picture.
