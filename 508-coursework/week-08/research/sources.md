# Sources

Three chapters of the *Shiji* (《史记》), fetched as plain text from Chinese
Wikisource and kept unedited in `sources/raw/`. The text is a Western Han
composition and is in the public domain; the Wikisource transcription is
CC BY-SA 4.0, so the page URL and revision id are recorded with every file.

| id | text | url | revid | fetched (UTC) | chars |
| --- | --- | --- | --- | --- | --- |
| S1 | 《史记·刺客列传》卷086 | <https://zh.wikisource.org/wiki/史記/卷086> | 2388562 | 2026-10-27T16:15:09 | 7,778 |
| S2 | 《史记·秦始皇本纪》卷006 | <https://zh.wikisource.org/wiki/史記/卷006> | 7907969 | 2026-10-27T16:15:15 | 15,653 |
| S3 | 《史记·燕召公世家》卷034 | <https://zh.wikisource.org/wiki/史記/卷034> | 2559287 | 2026-10-27T16:15:16 | 3,599 |

Files: `sources/raw/*.wikitext.txt` (as served), `sources/processed/*.txt`
(cleaned: templates, `-{...}-` conversion marks, red links and list markup
removed), `sources/raw/provenance.json` (url, pageid, revid, permalink, licence,
fetch time). Rebuild with `python code/fetch_sources.py`.

## S1 刺客列传: the spine

Everything the player walks through comes from this chapter: the Yan market, the
butcher and Gao Jianli, Tian Guang's suicide, Crown Prince Dan's two-part plan,
Fan Yuqi's head, the poisoned dagger, Qin Wuyang, the Yi river farewell, the map,
the torn sleeve, the pillar, the physician's medicine bag, "王负剑", the broken
thigh, the eight wounds, the thrown dagger in the bronze pillar, and the words
"事所以不成者，以欲生劫之".

Quoted directly in the game (63 of 136 script lines carry `src`):

- 「荆轲者，卫人也。其先乃齐人，徙于卫……而之燕，燕人谓之荆卿。荆卿好读书击剑……荆轲嗜酒，日与狗屠及善击筑者高渐离饮于燕市，酒酣以往，高渐离击筑，荆轲和而歌于市中，相乐也，已而相泣，旁若无人者。」
- 「诚得劫秦王，使悉反诸侯侵地，若曹沫之与齐桓公，则大善矣；则不可，因而刺杀之。」
- 「愿得将军之首以献秦王……臣左手把其袖，右手揕其匈。」
- 「日已尽矣，荆卿岂有意哉？」 / 「往而不返者，竖子也！」
- 「风萧萧兮易水寒，壮士一去兮不复还！」
- 「图穷而匕首见……未至身，秦王惊，自引而起，袖绝……剑长，操其室。时惶急，剑坚，故不可立拔。」
- 「王负剑！」 / 「断其左股」 / 「轲被八创」 / 「倚柱而笑，箕踞以骂」 / 「中桐柱」
- 「事所以不成者，以欲生劫之，必得约契以报太子也。」
- 太史公曰：「世言荆轲，其称太子丹之命，『天雨粟，马生角』也，太过。」

## S2 秦始皇本纪: the Qin record

Used for the aftermath and for one deliberate discrepancy:

- 「二十年，燕太子丹患秦兵至国，恐，使荆轲刺秦王。秦王觉之，体解轲以徇，而使王翦、辛胜攻燕……二十一年……得太子丹之首。」

This is the *only* place that says 体解 (dismemberment) and it dates 得太子丹之首
to the 21st year, while S1 has Crown Prince Dan killed by his father on the run.
The game follows S1 (see `research/design.md`, "Two chapters disagree").

## S3 燕召公世家: Yan's own record

- 「燕见秦且灭六国，秦兵临易水，祸且至燕。太子丹阴养壮士二十人，使荆轲献督亢地图于秦，因袭刺秦王。秦王觉，杀轲……二十九年，秦攻拔我蓟，燕王亡，徙居辽东，斩丹以献秦。三十年，秦灭魏。」

Confirms 督亢, the dagger hidden in the map, and the killing of Dan by King Xi -
the version the ending uses.

## What is deliberately *not* a source

- 《战国策·燕策》 and 《燕丹子》 retell the same story with extra material
  (the白马, 天雨粟, 马生角, the song's second verse). 太史公 explicitly calls the
  prodigies 「太过」, so they are excluded from the simulation.
- Modern histories and museum reconstructions were not used to establish any
  event; they would only be needed for material culture, and the pixel art at
  16x24 cannot carry that level of evidence (see the limits in `research/design.md`).

## Where the record is silent

The simulation has to invent connective tissue. Every line the player reads is
tagged in the data (`js/story.js`): `src` = from the chapter, `inv` = invented,
untagged = narration written for this project. Counts, from
`node code/check_story.mjs`: **65 quoted, 22 invented, 49 unattributed**, of
136 lines. The item-by-item evidenced / inferred / invented table is in
`research/design.md`.
