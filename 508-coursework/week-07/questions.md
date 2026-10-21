# Questions

Unresolved at the time of submission. Each one is answerable; none of them are
rhetorical.

1. **Is a 1950s factory photograph of the rifle a legitimate substitute for a
   clean object image?** The generator cannot assemble a rifle from text, but it
   can draw a convincing 1953 assembly line with rifles in it. That would satisfy
   "an image of your object at the stage you chose" in a looser sense, and it
   would look far better. I did not do it because it moves the comparison from
   "what the sources say about the object" to "what the sources say about the
   setting".

2. **How much should the prompt be trimmed to fit the generator?** The 150-word
   researched prompt named the milled receiver, the pinned stock socket, the
   single grip bolt and the sling loop, and produced nonsense. The short prompt
   that produced the least-bad image drops all of those. Is that still "an image
   from the sources", or is it an image from three source facts?

3. **Should the words-only baseline be as naive as it was?** "a photograph of an
   AK-47 rifle, side view" is what someone with the name and nothing else would
   type. Someone who had seen a photograph but done no research might type more,
   and the baseline would then be stronger. The brief says "from words alone",
   which I read as the naive version; a person marking this might read it as
   "the same words, without the research".

4. **Which weight is right for the Type 3?** S2 says the Type 3 was "about 0.5 kg
   less" than the Type 2 (4.3 - 0.5 = 3.8 kg), while S1 gives 3.47 kg. The
   difference matters if the model is ever used to argue about the cost of the
   milled receiver. I used S2 only for dimensions and left the weight
   discrepancy open.

5. **Do the CC BY-SA reference photographs need to travel with the generated
   images?** The two generated images contain no pixels from the photographs, so
   my reading is no. But the *prompt* was written from `15_ak47_type2_right_side_view.jpg`,
   which is CC BY-SA 4.0 by Vitaly V. Kuzmin, and the comparison sheet places the
   two generated images next to text derived from it. Attribution is given in
   `research/sources.md`; whether the sheet itself needs an on-image credit line
   is a question for the instructor.

6. **Is an untextured image-to-3D mesh an acceptable "3D model" for the brief?**
   Hunyuan3D 2 returned geometry in 57 s at no cost, but its texture step was
   unreachable without a key (2.0's combined endpoint errors for anonymous
   callers; 2.1 wants 270 s of GPU and therefore Hugging Face PRO). The mesh is
   in `model/ak47_hunyuan3d.glb`. If a textured result is required, the next step
   is a Tencent Cloud SecretId/SecretKey pair, which would let the same model run
   through `hunyuan.tencentcloudapi.com` with texture.
