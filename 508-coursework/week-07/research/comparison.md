# Step 2: the two images, and the answers

**Left (A):** `generated/final/baseline/seed11.jpg`
Prompt, verbatim: `a photograph of an AK-47 rifle, side view, whole rifle, plain background`
No sources were consulted to write this. It is what the phrase "AK-47" produces.

**Right (B):** `generated/final/researched/wooden_stock.jpg`
Prompt, verbatim: `a photograph of an AK-47 rifle with a wooden stock and wooden handguard, no scope, side view, whole rifle, plain background`
Every clause after "AK-47 rifle" comes from a source, not from taste.

**Sheet for class:** [`generated/comparison_sheet.png`](../generated/comparison_sheet.png).
Both images: Pollinations text-to-image, no key, cost 0, seed 11 / 61.

## 0. The control design

This is a paired comparison with one variable: **the words that came from the
research**. B's prompt is A's prompt plus three clauses, and nothing else:

```text
A  a photograph of an AK-47 rifle,                                side view, whole rifle, plain background
B  a photograph of an AK-47 rifle with a wooden stock and wooden handguard, no scope, side view, whole rifle, plain background
```

- **Control (A):** the prompt a person writes when they know the name of the
  object and nothing else.
- **Treatment (B):** the control prompt plus the three facts the sources
  establish - wooden furniture (S2), no optic (S3 dates the object to 1953),
  and a request that keeps the whole rifle in frame so the two can be compared.
- **Held constant between the two:** the model, the requested size, the
  composition words ("side view, whole rifle, plain background"), and the *task*
  - one text prompt, one image, no reference picture supplied to the generator.
  That last part matters: neither image saw a photograph, so any resemblance to
  the real Type 2 comes from the words alone.
- **Replication:** the control prompt was also run at seeds 23 and 37
  (`generated/a_words_only/`), and the treatment prompt at a second seed
  (`generated/final/researched/seed11_short_prompt.jpg`, seed 11 - the same seed
  as the control, so the seed is held constant too). The same failure modes
  recur, which is why the single pair on the sheet is representative rather than
  cherry-picked from many attempts.

**What the matched seed shows:** [`generated/control_check.png`](../generated/control_check.png)
puts the two prompts side by side at seed 11 and again at a second seed. At seed
11 the control gives the familiar black, rail-and-optic rifle, and the treatment
gives wooden furniture wrapped around an impossible assembly - two buttstocks
and a handguard where the barrel should be. So the added words reliably change
*material and era* and reliably do not produce a *coherent rifle*. The pair used
on the class sheet is control seed 11 against treatment seed 61, because that is
the one pair where both images are legible enough to compare feature by feature;
the matched-seed pair is reproduced in the control figure so the choice cannot be
mistaken for cherry-picking.

What the design cannot control: the generator is not deterministic across its
free tier and ignores the requested resolution, so small framing differences
between A and B are generator variance, not prompt effects. Only features that
follow the words - furniture, optic, magazine curve - are read as effects.

The research behind the prompt is in
[`object_and_history.md`](object_and_history.md): the object is the AK-47
**Type 2** of 1951–1955, the version with a receiver machined from one block of
steel, wooden furniture, a wooden pistol grip on a single bolt, a separate
pinned stock socket and no bayonet - the rifle that replaced the failed stamped
Type 1 and was itself lightened into the Type 3.

## 1. What does B get right that A gets wrong or leaves vague?

| Feature | A (words alone) | B (from sources) | Which source settles it |
| --- | --- | --- | --- |
| Furniture | black polymer-looking stock and handguard; a modern rifle | wooden buttstock and wooden handguard, warm brown varnish | S2: "single-piece pistol grip made from wood"; photograph `15_...` shows wooden furniture throughout |
| Era | rails, an optic mount and a scope: post-1990s | iron sights only, no rail asked for (though one appears - see §3) | a 1953 rifle ([S3]) has a tangent rear sight, not an optic |
| Buttstock | cropped out of frame, shape unknowable | a solid wooden buttstock with a visible buttplate | `15_...`, `01_...` |
| Magazine | short, straight, and in one seed doubled | long, curved, steel | S1: "standard 30-round magazines have a pronounced curve"; S2 specification: 30 rounds |
| Receiver | smooth black slab with an invented rail on top; no milled or stamped character | dark receiver sides, no rivet rows | S2: Type 2 receiver "machined from a single block of steel" |
| What the picture is *of* | a generic modern "AK-pattern" rifle | a wooden-stocked mid-century rifle | the whole point of the stage: 1951–1955 |

The difference is not that B is a better picture. It is that **B is a picture of
the right object for the right decade**, and A is a picture of the 2026 idea of
the object.

## 2. Which sources made the difference, and how were they used?

Three sources did the work:

1. **[S2] Modern Firearms, the Type 2 paragraph.** It supplied the two visible
   facts that changed the prompt: the furniture is wood, and the rifle is a
   1951–1955 machine - not the stamped AKM everyone pictures. The prompt clause
   "wooden stock and wooden handguard" is a direct transcription of it.
2. **[S1] Wikipedia, the variant list and magazine section.** It supplied "30
   round, curved, steel" and the date bracket: Type 2 is the 1951 issue, Type 3
   the 1954/55 lightened version. It also supplied the reason for the stage:
   the stamped Type 1 receivers were rejected in production.
3. **The Commons photographs, especially `15_ak47_type2_right_side_view.jpg`.**
   They were used *as the checking instrument*: after each generation I compared
   the result against this photograph - where the wood ends, how far the
   magazine curves, whether the sling loop is on the handguard. This is how the
   candidates that were "wooden" but not "rifle" were rejected.

How the research was used, concretely:

- It chose **which words went into the prompt** (wood, no scope, 1953).
- It chose **which words came out**: the first researched prompt also described
  the milled receiver, the pinned stock socket, the single grip bolt and the
  sling loop position. Those made the output worse, not better, so the shipped
  prompt keeps only what a 2D generator can show. The dropped facts still matter:
  they are what the 3D model is built from, and they are what the checklist
  below tests.
- It provided a **checklist to reject images**, which is the part a person with
  no sources cannot do: they have nothing to compare against, so they cannot
  tell an invention from a feature.

## 3. What did the generator still invent - in both?

**In A (words alone):**

- an optic and a mount rail on a rifle that in 1953 had a tangent rear sight;
- a soft rifle case and a wall/table setting that were never asked for;
- wrong proportions: the receiver is too long, the barrel too short, the stock is
  cut off by the frame edge;
- in another seed of the same prompt, two magazines and a second receiver.

**In B (from sources):**

- a **Picatinny-style rail and optic mount** along the top cover, despite "no
  scope" in the prompt - the model's "AK-47" prior overrides the negative;
- a **human hand** holding the fore-end, never requested;
- the **muzzle is cut off** at the right edge after asking for "whole rifle";
- the **magazine is only slightly curved**, not the pronounced 30-round curve;
- **no milled receiver**: the sides show none of the flat, rivet-free Type 2
  receiver, and no lightening pocket;
- the **sling loop is invisible**, so the Type 2-vs-Type 3 difference that the
  sources make a point of cannot be seen.

**In both:** the receiver is a black box with a rail on top; the gas block, front
sight and handguard retainer are decorative lumps; nothing shows how the parts
fit. The generator has a strong prior for "modern tactical AK" and only the
furniture responds to the prompt.

## 4. The honest conclusion

Research bought **materials, era and a checklist**. It did not buy a correct
Type 2. Anyone with no sources and no research can get A in one request; with
the research I got B, which is closer to 1953 and still wrong about the receiver,
the rail and the magazine curve.

For the class discussion the useful question is not "which picture is better"
but "which statements in each picture can I defend with a source". In A: almost
none. In B: wood, curved magazine, iron sights - three, all from [S2] and [S1],
and every one of them still has an invented detail on top of it.

The step-3 model exists because of this gap: the things the generator cannot
draw - milled receiver, pinned socket, sling loop position, no bayonet lug - are
exactly the things a mesh can hold.
