# Tool log

Written for the brief's last three bullets: what each tool did, what the AI did
and what I checked myself, at least one real difficulty with its example.

## Tools

| tool | version / endpoint | what it did | cost |
| --- | --- | --- | --- |
| Python | 3.14.7 | fetch and clean the sources; generate every pixel asset and every portrait; run the local server; summarise the call log | 0 |
| Pillow | 13.0.0 | draw the 128×80 tile sheet and 10 sprite sheets (16×24); crop the ten portraits | 0 |
| `deepseek-chat` | api.deepseek.com | every line a character speaks back; 11 counterfactual points | see below |
| Pollinations (image) | image.pollinations.ai, anonymous | 10 ink-wash portraits; 6 scene plates of which 2 passed review | 0 |
| Chinese Wikisource API | zh.wikisource.org | 3 chapters of the Shiji as wikitext | 0 |
| Node | 24.21 | `check_story.mjs` (structure), `playtest.mjs` (a real browser run that types into the game) | 0 |
| Chrome | headless, `--headless=new` | runs the game for the screenshots and the smoke test | 0 |
| Git | 2.x | version control only; no image or model tool | 0 |

Nothing was installed: Pillow was already present, the browser is the system one,
and the two endpoints are free or pay-per-call. `git status` in this folder touches
no tracked file except the ones listed in the README.

## What the AI did, and what I checked

| task | who | check |
| --- | --- | --- |
| the 65 quoted lines | me, copied from `sources/processed/shiji_086_cike.txt` | every `src` line re-read against the plain text file; `check_story.mjs` counts them |
| the `inv` lines and narration | drafted with an AI assistant, then rewritten by me | read against period vocabulary; no line uses a post-Han object, title or idiom that I could find |
| pixel art scripts | an AI subagent wrote `code/make_pixel_assets.py` from a written specification | independent audit script; sizes, transparency, tile seams, walk frames, determinism; previews inspected at 4× and 8× |
| the ten portraits | `code/make_portraits.py` against the free endpoint; I wrote the per-character descriptions and reviewed every result | each portrait opened and checked for sex, age and costume; 高渐离 was regenerated after coming back female; prompts and seeds in `game/assets/portraits_hd/manifest.json` |
| the two scene plates | same endpoint, after the figure prompts failed | all six opened; four rejected for showing the wrong culture, kept in `artifacts/illustrations-rejected/` |
| every line the characters speak | DeepSeek, through `/api/talk` | the server rejects any intent not in the list it sent; small talk is checked twice per run by `code/playtest.mjs`; every call logged with tokens and cost |
| counterfactual paragraphs | DeepSeek | prompt fixes register and length; output tagged 史外 · 推演 in the dialogue and on the ending card |
| the story's structure | me, plus `check_story.mjs` | 68 nodes, 7 beats, 6 endings, all reachable; every reference resolves; every character stands on a walkable tile |
| "does it run" | `code/playtest.mjs` | a real browser types two lines, makes a choice, enters the chaos scene, talks to the king and reaches an ending; zero page exceptions |
| the key | me | `git check-ignore` says `.env` is ignored; `git grep --cached` finds the key in no tracked file |

## Cost

Snapshot of `artifacts/logs/calls.jsonl` after the playtests; regenerate with
`python code/summarize_calls.py`.

| kind | calls | prompt tokens | completion tokens | cost (yuan) | median latency |
| --- | --- | --- | --- | --- | --- |
| talk (one typed line, answered in character) | 7 | 3,559 | 343 | 0.0077 | 1,151 ms |
| npc (the earlier action-list version, kept in the log) | 16 | 4,465 | 515 | 0.0107 | 882 ms |
| chronicle | 19 | 5,595 | 2,407 | 0.0272 | 1,950 ms |
| offline placeholders (`-dry`) | 2 | 0 | 0 | 0 | 0 |
| **total** | **127** | | | **0.1277** | |

Prices: `deepseek-chat` list price, yuan per million tokens — input cache-miss 2,
cache-hit 0.5, output 8. The rate table sits in `code/server.py` next to the call,
and every log row carries the token counts, so the total can be recomputed.

A ten-minute session with one character and four counterfactual panels costs
roughly **¥0.01**. The whole project, including every build, every playtest and
every failed attempt, is **¥0.07**.

## Difficulties

### 1. The model wrote history back over the branch (the one that changed the design)

The winning branch is: 荆轲 seizes the king's sword instead of his sleeve, the
dagger arrives first. The first version of that branch returned:

> 荆轲舍袖而撰王剑，剑长室坚，一时未脱。王惊起绕柱，轲持剑室追之，格于幄。群臣徒手莫敢近，侍医夏无且以药囊掷轲。左右呼王负剑，王乃拔剑断其左股……

That is the historical failure, written again — the context paragraph quotes it and
the model followed the quote, not the branch. The fix was to send the branch's
result explicitly (`outcome` in the prompt template) and to forbid the historical
ending in that line. The same request then produced the intended continuation,
quoted in `research/prompts.md` §2.

**Why it matters:** a counterfactual generator that silently reverts to the record
is worse than no counterfactual at all — it would teach false causality. The
lesson is that "describe the divergence" is not enough; the model needs the
branch's *consequence* stated as a constraint.

### 2. Two chapters of the same book disagree

S1 (刺客列传) has 荆轲 killed and 太子丹 killed by his father; S2 (秦始皇本纪) has
「体解轲以徇」 and 得太子丹之首 in the 21st year; S3 (燕召公世家) agrees with S1 on
Dan. I followed S1 for the attempt and S3 for Dan's death, and left 体解 out,
because the last frame of S1 — 箕踞而骂 — is the scene the simulation is built
towards. The choice is declared in `research/design.md` §8 rather than hidden.

### 3. Sixteen pixels cannot carry material evidence

A 16×24 figure can show a long sword and a black robe; it cannot show a Warring
States cross-collar cut, a jade pendant's shape, or the difference between a Qin
and a Yan chariot. So the art is declared **invented representation** in the
sourcing table, and the palace maps are called sets, not reconstructions. What the
art does do is make the *size difference* felt: 燕市 scrolls, 咸阳宫 does not.

### 4. The image generator, and the style word that finally worked

The first pass asked the free endpoint for *historical* scenes with people: a
drunken traveller singing in the market, mourners in white at the Yi, a king
running around a pillar. What came back:

- the Yi river farewell: a woman in a white bathrobe standing in shallow water;
- the Qin hall: a Ming-dynasty corridor with hanging lanterns, the figures reduced
  to specks at the far end;
- every image: a `pollinations.ai` logo in the corner, which `nologo=true` does not
  remove, and occasional HTTP 402/503 from the free tier.

Portraits of a single face worked better than group scenes, but they still came
back semi-realistic — and one of them, 高渐离, came back a **woman**. Adding "a male
figure, no woman" fixed the sex; nothing fixed the costume, because the model's
vocabulary is generic East Asian, not 3rd-century BC.

The turn came with a change of brief rather than a better prompt. Once the
requirement stopped being "reconstruct the period" and became "cartoon", the same
endpoint became reliable — but only after the right style word:

| style words sent | what came back |
| --- | --- |
| `2D cartoon illustration, cel shading, bold clean ink outlines, flat saturated colours` | a semi-realistic painted swordsman with soft shading — not cartoon at all |
| `children's picture book cartoon, thick black outlines, flat colors, rounded shapes` | flat colour, but a blank doll-like face |
| `anime style character portrait, cel shading, thick line art, large expressive eyes` | a stylised anime face, coherent but "cool" rather than cute |
| `kawaii moe illustration of an adorable cute young swordsman…, big sparkly eyes, faint blush, pastel palette` | the cute version: round face, huge eyes, soft pastel, and it holds across the whole cast |

The shipped set is generated from the last row — and note where the style phrase
sits: **first, before the costume description.** Put the costume first and the
costume wins; the model then paints a handsome historical portrait no matter what
style words follow.

**A second lesson, from the same set.** 「Moe」 pulls *young and feminine*: the first
attempt drew 荆轲 as a girl, and the king came back looking like a princess with a
crown. Two re-rolls fixed the king (adding `a thin black moustache` and keeping
`male`), at the cost of a European-Victorian look rather than a Chinese one. The
honest summary is that style tokens control *age and cuteness* far more reliably
than they control *sex or culture*; the cast is now labelled cute anime, with the
costume question left to the sourcing table.

The background plates went the same way: the five places (market, prince's hall,
guest room, river, Qin hall) are generated with `kawaii moe anime background …,
empty of people`, and stand behind the dialogue. The earlier ink-wash and
pixel-art directions are kept in `artifacts/illustrations-rejected/` and
`game/assets/legacy/` as the record of the previous two attempts.

### 5. Chinese glyphs, and the fix that moved them off the canvas

The first version drew dialogue on the 480×270 canvas at 13 px. There is no bitmap
CJK font on the machine, so the text was antialiased and then scaled up by the
browser: legible, but soft. The fix in this version was structural — the dialogue
layer moved into the DOM at native resolution (a real serif at 19–27 px, a real text
input, a scrollable transcript), and the canvas now only draws the place and the
walking sprites. The remaining canvas text is one 10 px hint. This is the clearest
case in the project where a limitation was removed by changing the architecture
rather than by tuning a parameter.

### 6. Operational: the workspace itself

Before the first command could run, every shell call failed with
`SetNamedSecurityInfoW failed (Win32 5)` — the sandbox could not grant itself write
access to the coursework folder, so nothing ran, including `git`. The fix was a
one-off permission repair on that folder (records: `508-coursework/acl-recovery-week07/`)
and running this session with full access. Nothing in this project needed admin
rights once the folder's own permissions were correct.

## Honest limits

- No sound. The 筑 is described, not heard.
- The portraits are mood, not costume evidence: the endpoint's vocabulary is generic
  East Asian, so the robes and crowns are plausible-looking rather than sourced.
- The model's intent reading is good but not perfect. It is bounded — a misread can
  only open a scene the script already contains — but it can still open one you did
  not mean, and the player may notice.
- The counterfactual paragraph is 80–140 characters; it is a sketch of a history, not
  a simulation of one.
- No save file: a session is one playthrough, about twenty minutes.
- Each typed line is one API call, so a long, chatty session costs more than a
  playthrough that follows the historical path.
