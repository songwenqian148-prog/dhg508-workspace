"""Turn the remaining clickable characters into AI conversations.

Every character you can click on the stage should answer in their own voice
through /api/talk, instead of reciting one fixed line. This rewrites the node
bodies in game/js/story.js: each becomes a talk block with a short opening, a
couple of recognised intents, and a fallback line for when the server is down.

    python code/convert_talk_nodes.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

STORY = Path(__file__).resolve().parent.parent / "game" / "js" / "story.js"

# id -> (npc, profile, scene, perception, opening, intents, fallback)
CONVERSIONS: dict[str, tuple] = {
    "a1_goutu": (
        "goutu", "狗屠，燕市上卖狗肉的。粗人，嗓门大，讲义气，嘴上不饶人心里软；知道荆轲爱喝酒，也知道他最近心事重。",
        "燕市酒肆，日暮",
        "荆轲坐在对面，酒喝了半酣；高渐离在旁边击筑；你的案上还摆着没剔完的肉。",
        "狗屠把刀往案上一拍：「荆卿，你又在这儿坐一天。肉都凉了。」",
        [{"id": "ask_jingke", "desc": "问他看得出我有什么心事", "next": None},
         {"id": "order", "desc": "再要酒要肉，说些闲话", "next": None}],
        "「哼。喝你的酒吧。」他把肉片推过来，不再问了。",
    ),
    "a2_dan_talk": (
        "taizidan", "太子丹，燕国太子，曾在秦为质，受秦王轻慢。心里憋着一口气，急，怕，又不肯承认自己怕。",
        "太子宫",
        "荆轲坐在席上下首；殿外有甲士换岗；案上摊着燕国的舆图。",
        "太子丹往前挪了半席：「荆卿，丹这几夜总睡不安。你说，秦王真会因一卷图、一颗头，就肯见我的人？」",
        [{"id": "reassure", "desc": "宽他的心，让他安心等待", "next": None},
         {"id": "plan", "desc": "与他说清入秦之后的打算", "next": "a2_open"}],
        "他点点头，手还是按在舆图上没松开。",
    ),
    "a3_fan_talk": (
        "fanyuqi", "樊於期，秦国将军，兵败得罪秦王，父母宗族被杀，逃亡到燕，寄在太子门下。恨到骨头里，也怯。",
        "舍人馆",
        "荆轲站在屋中；灯很暗；你的剑横在膝上，剑鞘有裂。",
        "樊於期抬头看你，眼睛里都是红丝：「荆卿，你也是来劝我的？」",
        [{"id": "ask_hate", "desc": "问他有多恨秦王、恨到什么地步", "next": None},
         {"id": "head", "desc": "开口要他的头（引出献首之计）", "next": "a3_open"}],
        "他低下头，手指在剑鞘的裂口上来回摸。",
    ),
    "a5_gao": (
        "gaojianli", "高渐离，燕人，善击筑。荆轲的酒友，也是唯一真正懂他的人。知道这一去不回，却什么也不劝。",
        "易水边，送别",
        "荆轲穿着白衣，站在车旁；岸上的人都低着头；你的筑抱在怀里，弦已经调好了。",
        "高渐离把筑抱紧了些：「荆卿。这一段，我替你击。你要说什么，我跟着。」",
        [{"id": "ask_song", "desc": "请他击一曲送行", "next": None},
         {"id": "farewell", "desc": "与他说几句告别的话", "next": "a5_song"}],
        "他没再问，手指落在弦上。",
    ),
    "a6_king_talk": (
        "qinwang", "秦王政，此刻坐在九宾之后。刚戾自用，但此刻正看着燕使一步步上殿，心里并不轻松。",
        "咸阳宫，受图之前",
        "燕使在阶下；殿上不许携兵；你的剑很长，挂在腰间。",
        "秦王没有看你，只问左右：「燕使到了？」",
        [{"id": "summon", "desc": "命燕使上前献图", "next": "a6_open"},
         {"id": "watch", "desc": "先不动声色，看他怎么走上来", "next": None}],
        "他没有再说话，指节在案上轻轻敲了一下。",
    ),
    "a6_doctor_talk": (
        "xiawuju", "夏无且，秦王侍医。谨慎、胆小，只会看病，手里只有一个药囊。",
        "咸阳宫",
        "秦王在阶上；燕使刚上殿；你抱着药囊站在阶侧。",
        "夏无且压低声：「壮士……不，燕使。殿上不许带兵，你的图匣，可沉？」",
        [{"id": "calm", "desc": "随口敷衍他，让他别多问", "next": None},
         {"id": "ask", "desc": "问他殿上的规矩、郎中有多少", "next": None}],
        "他讪讪地退了半步，把药囊抱得更紧。",
    ),
    "a6_guard_talk": (
        "guard", "秦王殿上的郎中，按秦法无诏不得上殿。训练有素，也怕担责任。",
        "咸阳宫阶下",
        "燕使在你面前经过；殿上秦王已经坐定；你的长戟拄在地上。",
        "郎中低声提醒：「按秦法，无诏不得上殿。你若要进，还得等王上开口。」",
        [{"id": "ask_law", "desc": "问殿上的规矩、若是出事怎么办", "next": None},
         {"id": "pass", "desc": "不再多问，只管站好", "next": None}],
        "他把戟往里收了收，不再说话。",
    ),
}


def find_block(text: str, node_id: str) -> tuple[int, int]:
    """Return the character span of a node body, brace-counted."""
    key = f"\n    {node_id}: {{"
    start = text.find(key)
    if start < 0:
        raise SystemExit(f"node not found: {node_id}")
    i = text.find("{", start)
    depth = 0
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(text) and text[end] == ',':
                    end += 1      # the original node's trailing comma
                return start, end
        i += 1
    raise SystemExit(f"unbalanced braces after {node_id}")


def render(node_id: str, spec: tuple) -> str:
    npc, profile, scene, perception, opening, intents, fallback = spec
    lines = [
        f"    {node_id}: {{",
        "      // AI conversation: this character answers in their own voice.",
        "      talk: {",
        f"        npc: '{npc}',",
        f"        profile: {quote(profile)},",
        f"        scene: {quote(scene)},",
        f"        perception: {quote(perception)},",
        f"        opening: {quote(opening)},",
        "        intents: [",
    ]
    for intent in intents:
        nxt = f", next: '{intent['next']}'" if intent.get("next") else ""
        lines.append(f"          {{ id: '{intent['id']}', desc: {quote(intent['desc'])}{nxt} }},")
    lines += [
        "        ],",
        f"        fallback: {quote(fallback)},",
        "      },",
        "    },",
    ]
    return "\n".join(lines)


def quote(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main() -> int:
    text = STORY.read_text(encoding="utf-8")
    for node_id, spec in CONVERSIONS.items():
        start, end = find_block(text, node_id)
        text = text[:start] + render(node_id, spec) + text[end:]
    STORY.write_text(text, encoding="utf-8", newline="")
    print(f"converted {len(CONVERSIONS)} nodes to AI conversations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
