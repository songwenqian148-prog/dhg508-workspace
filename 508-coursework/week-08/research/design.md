# Design: 图穷 · a historical simulation of 荆轲刺秦王

## 1. Why a simulation, and not a film

A film of the Shiji's account gives you one ending and one explanation: the
dagger missed, the king ran, the assassin died. The lesson — that the attempt
was doomed before it started — is *asserted* by the film. It cannot be felt,
because the viewer never makes a decision.

The simulation's claim is narrower and checkable. Failure was not one moment
but the accumulated cost of four decisions, each defensible alone:

1. **太子丹's plan had two incompatible aims** — capture the king alive and make
   him return the annexed land (the 曹沫 precedent), or kill him. 荆轲 takes the
   harder one, and dies saying so: 「事所以不成者，以欲生劫之，必得约契以报太子也。」
2. **The rush.** 荆轲 was waiting for a man who would have made a second hand at
   the 陛. 太子丹 suspected him, said 「日已尽矣」, and threatened to send Qin
   Wuyang first. He left angry, and alone with a thirteen-year-old.
3. **The deputy.** 秦舞阳, "人不敢忤视", collapses at the steps: 「色变振恐，群臣怪之」.
   The player has to cover for him, and go on alone.
4. **The half-step.** Even with the dagger out, 「未至身」: the sleeve tore, the
   long sword could not be drawn, and the court's rule against armed courtiers
   meant nobody could stop him — until 「王负剑」.

Only a player who has chosen 等 or 不等, 劫 or 刺, 退 or 进 can feel how much each
decision costs, and why the last half-step was already paid for. That is the
answer to 「why not a film」: the film shows the causal chain; the simulation
makes you pay for it, and then lets you spend one decision differently and watch
the world not turn.

## 2. The loop

```
walk the place → talk to whoever is there → choose (a decision, not a quiz)
      ├─ the world decides what follows (rules in engine.js)
      └─ if the choice leaves the record: a 史外 · 推演 panel, generated, labelled
→ next act
```

The player moves 荆轲 through five places (燕市 → 太子宫 → 舍人馆 → 易水 →
咸阳宫), talks to eight named people, and makes eleven decisions. Walking is not
decoration: the source gives places, not psychology, and a place you have to cross
is the cheapest honest way to make 燕市 and 咸阳宫 feel different in size.

## 3. The five acts

| act | place | what the record gives | what the player does |
| --- | --- | --- | --- |
| 一 · 燕市 | market street, reeds, river | 卫人→燕, 好读书击剑, 嗜酒, 与狗屠高渐离饮, 相泣, 盖聂, 鲁句践, 田光 | drink and talk (高渐离 is agentic), recall Yuci and Handan, hear Tian Guang and watch him kill himself |
| 二 · 太子宫 | hall, mats, curtain | 太子丹's plan, 鞠武's rejected advice, 樊於期 sheltered | accept the plan (劫/刺/advice), walk to the guest house |
| 三 · 舍人馆 | small room | 樊於期's grief, his suicide | decide how to ask for his head |
| 四 · 备具 | the hall again | 徐夫人匕首 + 药焠 + 血濡缕, 秦舞阳为副, 荆轲有所待 | be hurried; decide whether to wait; talk to the boy |
| 五 · 易水 | river bank, sand, reeds, water | 白衣冠, 高渐离击筑, 变徵, the song, 终已不顾 | sing, look back or not, board |
| 六 · 咸阳宫 | hall, red pillars, throne | 九宾, 武阳色变, 图穷匕见, 袖绝, 环柱, 药囊, 王负剑, 断股, 八创, 中柱, 箕踞而骂 | the strike, the chase, the throw — and then the ending |
| 尾声 | — | 燕王喜斩丹, 秦灭燕, 高渐离筑击, 鲁句践之叹 | read, and see the list of what you changed |

Maps: `game/js/maps.js`. Script: `game/js/story.js` (58 nodes, 141 lines).

## 4. Branches

Every branch has a **historical default** (the option marked 史实) and deviations
that declare a divergence. Deviations do not rewrite the record; they fork it and
are labelled.

| # | decision | historical default | deviations | what the world does |
| --- | --- | --- | --- | --- |
| 1 | Yuci / Handan | 嘿而逃去, 默然 | fight back | sets `sword`/`composure`; feeds the branch-4 outcome |
| 2 | 田光's death | go to the prince | refuse the charge | 史外 ending: 燕市之外 |
| 3 | Dan's plan | 劫 then 刺 | kill outright; advise alliance | recorded; the kill-only line changes the ending's framing |
| 4 | asking for Fan's head | ask directly | wait for him to offer; spare him | 史外 panel: a mission without a head cannot reach the king |
| 5 | the hurry | angry, leaves at once | wait for the man; go quietly | `waited` — the only flag that can change the outcome |
| 6 | Yi river | 「终已不顾」 | look back; weep | 史外 panel; `looked_back` |
| 7 | the strike | 把袖而揕 | seize the sword first; demand a treaty aloud | `strike` decides which branch of the attempt you are in |
| 8 | the chase | 逐秦王 | turn on the physician; throw early | changes the wound you take, and which line kills you |
| 9 | the outcome | accept the record | ask what if it had landed | 史外 ending, generated |

The mechanical weight is deliberately small: `sword`, `composure`, `trust`,
`waited`, `strike`. Only one branch reads them (node `a6_sword_check`): if you
waited for the man who never came, **or** trained the sword hand, the dagger
arrives first. Everything else changes what is said, not what is possible — which
is the point the simulation is making about the record.

## 5. What the model is allowed to do

The player types whatever they want, to whoever is in front of them. The model
answers in that person's voice and reports which of a **closed list of intents** it
recognised. It never moves the story: only an id that `story.js` already knows can
do that.

Each talk call sends the character's profile (written from S1), the scene in one
line, **what the character can perceive** as a fixed string written by me, the last
few turns, the player's words verbatim, and the closed intent list with a one-line
description each. It answers `{"reply", "intent", "option"}`: 1–3 sentences of
浅近文言, an intent id or `chitchat`, and at a decision point an option id or null.
The server checks both against the lists it sent; the engine ignores anything
unrecognised; the world's transition always comes from the script.

Two consequences matter for the brief's rule — 「the world, not the language model,
decides what actually happens」:

- **Small talk is answered in character.** 「足下今日食何物？」 gets 「粗粝之食，不足挂齿」 and
  changes nothing. The prompt forbids shrugging it off, and `code/playtest.mjs`
  checks it twice per run.
- **Intents are proposals, not commands.** A misread intent can only open a scene
  the script already contains. If the model answers `chitchat`, nothing happens.

At a decision point the same input box accepts free speech: the model is given the
option list and asked which option the player's words correspond to. If it cannot
tell, the NPC answers and the decision stays open — the game does not guess.

## 6. Counterfactuals, and how they are kept honest

The hard divergence is **played**, not narrated. When the dagger lands the game
does not open a text panel: it drops you into `a7_chaos` — the same hall, the
wounded king still standing and still able to talk, three characters to address, and
four ways to spend the half minute before the guards reach the steps (force a treaty,
finish him, run, or listen first). Only the *consequence* is generated, as a short
historical paragraph delivered inside the dialogue with the 「史外 · 推演」 tag, and
listed again under 「你所改变的历史」 on the ending card.

The generation prompt fixes the shape: 80–140 characters, historical register, no
triumph, Qin's counties and armies still exist, no mention of the model. Where a
branch has a *result*, the prompt receives an `outcome` line the model must follow —
without it the model wrote the historical failure again, which is how that
requirement was discovered (see `research/tool_log.md` §1).

The softer divergences (refusing 田光, sparing 樊於期, waiting for the guest) work the
same way: the NPC says what your choice cost, in his own voice, on a tagged line —
not in a floating panel. The historical ending is always the default path; the
divergences are reached only by choosing them.

## 7. Evidenced / inferred / invented

Required by the brief: every part of the simulation, marked. `S1` = 卷086,
`S2` = 卷006, `S3` = 卷034 (see `research/sources.md`).

| part of the simulation | status | basis |
| --- | --- | --- |
| 荆轲's names: 庆卿 in Wei, 荆卿 in Yan | evidenced | S1 「卫人谓之庆卿。而之燕，燕人谓之荆卿」 |
| 好读书击剑, 嗜酒, 沉深好书 | evidenced | S1 |
| 燕市 drinking with the butcher and 高渐离; 击筑; 相乐, 已而相泣, 旁若无人 | evidenced | S1 |
| 榆次论剑 with 盖聂; 邯郸 争道 with 鲁句践; both walk away | evidenced | S1 |
| 田光 recommends him, then kills himself 「以明不言」 | evidenced | S1 |
| 太子丹's 劫-or-kill plan, and its 曹沫 precedent | evidenced | S1 |
| 鞠武's alliance advice, rejected as 旷日弥久 | evidenced | S1 |
| 樊於期 shelters in Yan; 荆轲 asks for his head; he cuts his throat; 函封 | evidenced | S1 |
| 徐夫人匕首, 百金, 药焠, 「血濡缕，人无不立死者」 | evidenced | S1 |
| 督亢 map as the credential | evidenced | S1, S3 |
| 秦舞阳, thirteen, 「人不敢忤视」, made deputy | evidenced | S1 |
| 荆轲 waits for a man who does not come; 太子丹 suspects and hurries him | evidenced | S1 |
| 白衣冠 at the Yi; 变徵之声; 「风萧萧兮易水寒」; 羽声; 发尽上指冠; 终已不顾 | evidenced | S1 |
| 九宾之礼; 蒙嘉 as the intermediary | evidenced | S1 |
| 武阳 turns pale at the steps; 荆轲 covers for him | evidenced | S1 |
| 图穷匕见; 把袖; 袖绝; 剑长不可立拔; 环柱; 药囊; 王负剑; 断左股; 八创; 中铜柱; 箕踞而骂 | evidenced | S1 |
| 秦法: 群臣侍殿上者不得持尺寸之兵 | evidenced (as reported law) | S1 |
| 荆轲's dying explanation: he meant to capture, not kill | evidenced | S1 |
| 燕王喜 kills 太子丹; 秦灭燕; 高渐离's later attempt; 鲁句践's regret | evidenced | S1, and 丹's death S3 |
| 秦王 is "刚戾自用", black robes as Qin's colour | inferred | S2's characterisation + Warring-States material culture |
| the palace's pillars, mats, low dais, no chairs | inferred | period material culture; **not** a reconstruction of the Xianyang hall, which is not excavated |
| 秦舞阳's fear as a specific line of speech | inferred (words invented) | S1 gives 「色变振恐」 only; the sentence is mine, marked `inv` |
| 荆轲's own voice: 「渐离，再击一曲」 and the other `inv` lines | invented | needed to give the player a mouth; 22 lines are marked `inv` |
| the 客 who never came actually arriving (branch 5) | invented | S1 says only 「其人居远未来」; the counterfactual fills the silence |
| 燕市's dusk, the butcher's trestle, the wine jars | invented | no source describes the market |
| the ten moe portraits and five scene backgrounds | invented (representation, and deliberately so) | this version does not claim costume reconstruction: cute anime drawings that carry casting and mood, not evidence. The walkable pixel map is gone; the game is a stage: place art, a row of character portraits, and a talking panel |
| every generated 史外 paragraph | invented, and labelled so | model output, logged with prompt and cost |

## 8. Two chapters disagree

- S1: at the end 「左右既前杀轲」 and 太子丹 is killed by his father while hiding
  in 衍水.
- S2: 「秦王觉之，体解轲以徇」 and 得太子丹之首 in the 21st year.
- S3: 「秦王觉，杀轲……燕王亡，徙居辽东，斩丹以献秦」.

The game follows S1 for the attempt and S3 for Dan's death, and does not use 体解:
the simulation's last frame is 箕踞而骂, and dismemberment would be a different
scene from the one S1 describes. This is a choice, not an oversight; it is the
kind of choice the brief asks to be declared.

## 9. What this simulation does not do

- It does not model Qin's institutions, the 燕 court, or the six states' diplomacy.
  「一个人的死，换不来函谷关以东几十万人的户籍」 is stated in the 史外 text, not
  simulated.
- It does not claim the pixel palaces are archaeological. They are sets.
- It has no sound, no save file, and no combat: every outcome is a decision, not a
  reflex.
- Only two characters are agentic; the other six are scripted, because their lines
  are in the source and a model could only blur them.
