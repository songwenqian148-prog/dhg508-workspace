# Object and historical stage

## The object

A Kalashnikov AK-47 rifle, fixed wooden stock, 7.62×39 mm.

## The stage: the Type 2, 1951–1955

I am not modelling "an AK-47" in general. I am modelling one specific stage of
it: the **1951–1955 Type 2**, the version with a receiver machined from a single
block of steel, built between the abandonment of the first stamped receiver and
the lightened 1955 redesign.

That stage is interesting because the rifle's history runs *backwards* there:
the first production rifles were cheaper to make in theory, and the factory went
back to a more expensive method after they could not be made reliably.

1. **1947–1949 (Type 1).** The rifle is accepted in 1949 with a stamped sheet
   steel receiver, with the bolt rails welded inside and the trunnions pinned in
   ([S1](../research/sources.md), [S2](../research/sources.md)).
2. **End of 1949.** The stamped receiver turns out to be the problem: welding
   the guide and ejector rails gives an excessive rejection rate. Popenker
   writes that stamped receivers with welded bolt rails and pinned trunnions
   were "too complex and … excessive rate of rejected receivers"; Wikipedia says
   a "heavy machined receiver was substituted" rather than halting production
   ([S1], [S2]).
3. **1951–1955 (Type 2, the stage I chose).** A receiver machined from one block
   of steel, which also removed the separate front and rear trunnions. Other
   visible changes: a one-piece wooden pistol grip bolted to a separate base
   with a single vertical bolt, and a separate steel stock socket pinned to the
   rear of the receiver ([S2]). The rifles were officially called AK-49, because
   that is when the redesign started, and are called "Type 2" only in the
   collectors' literature ([S1]).
4. **1955–1959 (Type 3).** The same milled receiver, lightened: barrel, stock,
   receiver, top cover and some trigger parts made thinner or from cheaper
   steel; the front sling loop moves from the lower handguard to the gas block;
   a knife bayonet is adopted ([S2]). Wikipedia gives the Type 3 weight as
   3.47 kg ([S1]).
5. **1959 (AKM).** A stamped receiver comes back, now that the manufacturing
   problems are solved; the rifle drops to 3.1 kg and gains the slanted muzzle
   brake ([S1], [S2]).

So the "earlier stage" the assignment asks for is not simply "older than today":
it is a **three-year window** in which the rifle was heavier and more expensive
to build than the rifle that came before it *and* the one that came after it.
A museum object dated 1953 ([S3]) sits inside that window.

## What that gives me to draw and to model

Visible, checkable differences between the three milled/stamped stages:

| Feature | Type 1 (1948/49) | Type 2 (1951–55) | Type 3 (1955–59) | AKM (1959) |
| --- | --- | --- | --- | --- |
| Receiver | stamped, welded rails, rivets | milled from one block, flat solid sides | milled, lightened | stamped, riveted |
| Pistol grip | two thin grip panels | one-piece wood grip, single bolt | one-piece wood grip | one-piece |
| Stock attachment | butt-stock insert | separate steel socket, pinned | socket | — |
| Front sling loop | lower handguard | lower handguard | gas block | gas block |
| Bayonet | none | none | knife bayonet | knife bayonet |
| Muzzle | short brake/compensator | plain | plain | slanted brake |
| Weight, empty | — | 4.3 kg | 3.47 kg | 3.1 kg |

The same table is also built in 3D, one stage per row, in
[`generated/receiver_timeline.mp4`](../generated/receiver_timeline.mp4); what
each variant changes in the mesh is listed in
[`model_notes.md`](model_notes.md#historical-timeline-the-receiver-1949-to-1959).

Sources for the table: [S1] (dates, weights, chrome-plated barrel on the Type 2),
[S2] (receiver construction, grip, socket, sling loop, bayonet), and the
Commons photographs of Type 1 / Type 2 / Type 3 hardware
(`02_ak47_type1_type2_comparison.png`, `03_ak47_type3_aks47_comparison.png`,
`15_ak47_type2_right_side_view.jpg`) which show the receiver sides, the grip and
the sling loop directly.

## What this means for the two images

The words-only baseline does not know any of the table. It knows the phrase
"AK-47", which in most training data means the black, plastic-furniture,
optics-equipped rifle of the last thirty years. The researched prompt can ask
for the 1953 object: wooden furniture, no rails, no optic, a solid milled
receiver with no rivet rows, the sling loop still on the handguard.

Whether the generator can *draw* that is a different question, and it mostly
cannot - which is one of the difficulties written up in
[`tool_log.md`](tool_log.md#difficulties).
