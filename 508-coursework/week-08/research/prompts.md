# Prompts, verbatim

Every prompt that reached a model is recorded twice: here, and in
`artifacts/logs/calls.jsonl` (system + user text, reply, tokens, cost, latency).
Regenerate the totals with `python code/summarize_calls.py`.

## 1. Talking: free speech, closed intents

`code/server.py`, `TALK_SYSTEM`, unchanged:

```text
你在扮演《史记·刺客列传》里的一个人物，正与玩家面对面说话。玩家就是荆轲（或秦王），你是另一个人。
规则：
1. 用当事人自己的口吻说话，说人话。可以文言底子，但不要句句掉书袋、不要文绉绉地讲道理。允许口语、停顿、反问、半句没说完。
2. 带上真实的感受与私心：害怕、犹豫、疲惫、不甘、算计、对某人的偏爱或怨气。不要像个客观的解说员，也不要总结历史教训。
3. 你只知道你这个身份、这个位置能知道的事。不要说后世才知道的结局，不要背诵史书，不要提「历史」「结局」「剧情」。
4. 每次回一到三句，短一点更自然。可以不答（只写「……」），可以只回一句「你说什么？」。
5. 玩家问什么都答，包括和眼前的事无关的（吃了什么、家里怎样、天气、玩笑）。答的时候用你自己的身份与心情，答完可以自然地把话头绕回眼前正在办的事——但不要生硬地转场，不要说「我们还是说正事吧」这种话。
6. 你只说话，不决定世界发生什么。不要宣称自己做过列表以外的事。
7. intent 只表示「玩家这句话实际在做什么」，不是你想做什么。纯闲聊填 "chitchat"。
8. 若给了「可选决定」，玩家的话是在做决定时，从中选一个 id 填 option，否则填 null。
9. hint 是给玩家的路标：用你的口吻，一句话，点一下此刻能做什么；玩家已经说到点上就留空。不要用系统口气。
输出 JSON：{"reply": "你的话", "intent": "<意图 id 或 chitchat>", "option": "<决定 id 或 null>", "hint": "<一句话或空串>"}
```

User template:

```text
你是：<profile, written from 卷086 - e.g. 高渐离，燕人，善击筑…>
场景：<one line>
你能感知到的：<a fixed string written by the author; never world state or the future>
对方的身份：<荆轲，燕之上卿…>
对话至今：
- 高渐离：「荆卿，今日的酒，比昨日苦。」
- 荆轲：足下今日食何物？
可选意图：
- ask_zhu：问他方才那一曲为何那样哀，或请再击一曲
- ask_state：问他对燕国大势、秦人东来的看法
- part：告辞，起身去别处
只输出 JSON。
```

Three real exchanges from `artifacts/logs/calls.jsonl`:

```json
{"reply": "粗粝之食，不足挂齿。足下问此，莫非嫌酒无味，欲以谈佐之？",
 "intent": "chitchat", "option": null, "cost_yuan": 0.001358, "ms": 1151}
```
```json
{"reply": "一斗不过十钱，荆卿何问此？莫非欲沽之以赠人乎？",
 "intent": "chitchat", "option": null, "cost_yuan": 0.000826, "ms": 770}
```
```json
{"reply": "六国者，皆秦之仇雠也。天下不定于一，兵戈无息时。燕丹遣汝来刺，便是六国之心，汝反问我为何灭之？",
 "intent": "ask_why", "option": null, "cost_yuan": 0.001312, "ms": 1151}
```

The first two are the point of the feature: questions with no bearing on the plot
are answered *in character*, and the model reports `chitchat`, so the world does
nothing. The server re-checks `intent` against the ids it sent; an id it did not
offer becomes `chitchat`.

At a decision point the same call also carries a decision list:

```text
可选决定（玩家这句话若是在做决定，选一个）：
- treaty：把剑横在他颈上，逼他署约、尽反诸侯侵地
- kill：不再说话，补一剑
- escape：舍下秦王，趁乱夺门而出
- hear：先不杀，听他要说什么
```

The model may only name one of those ids. If it names none, the NPC answers and the
decision stays open — the engine never guesses.

## 2. The counterfactual

`CHRONICLE_SYSTEM`, unchanged:

```text
你是《史记》体例的历史推演者。玩家刚刚做出一个偏离史料的选择，你要续写一段「没有发生的历史」。
规则：
1. 冷静、具体、克制。写人物与制度如何反应，不写胜利颂歌，不写因果报应。
2. 时间跨度不要太大，只写紧接着发生的事，像史书的一小段。
3. 必须承认秦的制度与兵力仍在：一个人的选择很难让历史整体掉头。
4. 80 到 140 字。用现代汉语，文风偏史传。不要出现「如果」「假如」以外的元评论，不要提到你自己或模型。
5. 输出 JSON：{"text": "续写的段落"}
```

User template:

```text
偏离点：<the divergence, as the game declares it>
史实背景：<the passage it departs from, with the source quoted>
这一分支的实际结果（必须照此续写，不得改回史书的失败结局）：<outcome, only on branches with a result>
已经发生过的偏离：<earlier divergences>
只输出 JSON。
```

The `outcome` line exists because of a failure worth recording: on the branch where
荆轲 seizes the king's sword first, the model wrote the historical failure anyway —
「王乃拔剑断其左股」 — because the context quoted it. Naming the branch's result fixed
it (see `research/tool_log.md` §1).

## 3. The image prompts

Two families were tried against Pollinations (free, keyless, about one image every
45–70 s; the service stamps a logo the `nologo` flag does not remove).

**Rejected: figures and group scenes.** 「a tall drunken traveller in a dark
cross-collar robe… a musician striking a zhu zither… a butcher at his chopping
block」 came back as a woman in a bathrobe standing in the river; the Qin hall came
back as a Ming corridor with electric-looking lanterns. Kept in
`artifacts/illustrations-rejected/`.

**Kept: ink-wash portraits and empty places.** The portrait prompt puts the subject
first, then the style:

```text
<description: a lean Chinese man of thirty, a musician, calm heavy eyes, short beard,
hair tied with a plain cloth band, pale grey green cross collar robe, a long lacquered
zither edge in the frame, reserved and watchful>,
ink wash painting on rice paper, sumi ink, desaturated greys with one faint cinnabar
accent, plain empty paper background, half length portrait, three quarter view, soft
even light, a male figure, Warring States period China, 3rd century BC, no woman,
no text, no watermark
```

Every portrait prompt, seed, raw byte count and sha256 is in
`game/assets/portraits_hd/manifest.json`; the generator is `code/make_portraits.py`.
The `a male figure / no woman` clause was added after the first 高渐离 came back as a
woman (see `research/tool_log.md` §4).

## 4. Prompts that were *not* used

- No prompt writes history the player sees as fact. The acts, the quotations and the
  branching are fixed in `game/js/story.js`; the model writes voices and, at declared
  divergences, one labelled paragraph.
- No prompt receives the player's flags or stats when a character speaks; only the
  chronicle prompt receives a branch result.
- No few-shot examples: at a 260-token budget they cost more than they helped, and
  the JSON shape is enforced by `response_format` plus `parse_json`.

## 5. Cost

`deepseek-chat` list price in yuan per million tokens (input cache-miss 2,
cache-hit 0.5, output 8), recorded with every call. Totals in
`artifacts/logs/summary.md`; a ten-minute conversation costs about ¥0.01–0.02
because every typed line is one call.
