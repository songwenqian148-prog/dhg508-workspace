"""The local server for 图穷: static files, one model, and a call log.

    python code/server.py            then open http://127.0.0.1:8765

Standard library only. The API key is read from DEEPSEEK_API_KEY, or from a
.env file beside this project or at the repository root; it is never sent to
the browser and never written to a tracked file.

Two endpoints matter:

    POST /api/npc        one character decides one action, from a list the world
                         allows. The server rejects an action outside that list,
                         so the model cannot make the world do anything.

    POST /api/chronicle  a history that did not happen, labelled 史外 · 推演.

Every call - prompt, reply, tokens, cost, latency - is appended to
artifacts/logs/calls.jsonl.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
GAME = PROJECT / "game"
LOGS = PROJECT / "artifacts" / "logs"
PORT = int(os.environ.get("PORT", 8765))

API_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
# Yuan per million tokens, deepseek-chat list price (2025): input cache-miss 2,
# cache-hit 0.5, output 8. The log records both the token counts and this table so
# the cost in the report can be recomputed if the price changes.
RATES = {"input_cache_miss": 2.0, "input_cache_hit": 0.5, "output": 8.0}

NPCS = {
    "jingke": "荆轲，卫人，好读书击剑，沉深好书，善与人交",
    "gaojianli": "高渐离，燕人，善击筑，与荆轲为友",
    "goutu": "燕市狗屠，荆轲的酒友",
    "tianguang": "田光，燕之处士，智深而勇沈",
    "taizidan": "太子丹，燕太子，曾质于秦，怨秦王",
    "fanyuqi": "樊於期，秦将，得罪于秦王而亡之燕",
    "qinwuyang": "秦舞阳，燕国勇士，年十三，人不敢忤视",
    "qinwang": "秦王政，秦之王，刚戾自用",
    "xiawuju": "夏无且，秦王侍医",
    "guard": "秦王殿上的郎中",
    "mengjia": "蒙嘉，秦王宠臣，中庶子，善言辞，贪财而圆滑",
    "narrator": "旁白与裁决者，不是人物：只听玩家的决定，判断它对应哪一个选项，不要扮演任何人",
}


# --------------------------------------------------------------------- key

def load_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    for env_file in (PROJECT / ".env", PROJECT.parent.parent / ".env"):
        if not env_file.is_file():
            continue
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            if name.strip() == "DEEPSEEK_API_KEY":
                return value.strip().strip('"').strip("'")
    return ""


KEY = load_key()
# Set YISHUIHAN_DRY=1 to answer every request with a fixed, clearly-labelled
# stand-in. It exercises the same JSON contract and the same call log, and is
# how the class demo runs without a key - it is never presented as model output.
DRY = os.environ.get("YISHUIHAN_DRY") == "1"


# --------------------------------------------------------------------- model

def call_model(system: str, user: str, max_tokens: int, temperature: float) -> dict:
    """One chat completion. Returns text, usage, latency; raises on failure."""
    if not KEY:
        raise RuntimeError("no DEEPSEEK_API_KEY")
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=90) as res:
        data = json.loads(res.read().decode("utf-8"))
    ms = int((time.perf_counter() - started) * 1000)
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {}) or {}
    prompt_tokens = usage.get("prompt_tokens", 0)
    cached = usage.get("prompt_cache_hit_tokens", 0) or 0
    completion_tokens = usage.get("completion_tokens", 0)
    cost = (
        (prompt_tokens - cached) / 1_000_000 * RATES["input_cache_miss"]
        + cached / 1_000_000 * RATES["input_cache_hit"]
        + completion_tokens / 1_000_000 * RATES["output"]
    )
    return {
        "text": text,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached,
            "completion_tokens": completion_tokens,
        },
        "cost_yuan": round(cost, 6),
        "ms": ms,
        "model": data.get("model", MODEL),
    }


def parse_json(text: str) -> dict:
    """The model is asked for JSON; recover it even if it wraps the object."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def log_call(kind: str, system: str, user: str, result: dict | None, error: str | None) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "kind": kind,
        "system": system,
        "user": user,
        "reply": (result or {}).get("text"),
        "usage": (result or {}).get("usage"),
        "cost_yuan": (result or {}).get("cost_yuan"),
        "ms": (result or {}).get("ms"),
        "error": error,
    }
    with (LOGS / "calls.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------- prompts

NPC_SYSTEM = """你在扮演一个公元前三世纪的中国历史人物，出自《史记·刺客列传》。
规则：
1. 你只知道你所处时代、你所处位置能知道的事。不要提到后世才知道的事实、评价或结局。
2. 你只回一句到三句的话，用浅近文言或简洁文言，不要白话解释，不要旁白，不要括号动作。
3. action 必须严格选自「可选动作」列表，逐字复制其中一项；不得自创。
4. 你不决定世界发生了什么。你只说出你的话、提出你想做的动作；结果由游戏判定。
5. 不得宣称自己已经做到列表以外的任何事。
输出 JSON：{"say": "你说的话", "action": "可选动作中的一项"}"""


def npc_prompt(p: dict) -> tuple[str, str]:
    npc = str(p.get("npc", ""))
    profile = NPCS.get(npc, str(p.get("profile", "")))
    actions = [str(a) for a in (p.get("actions") or [])][:6]
    user = "\n".join([
        f"你是：{profile}",
        f"场景：{p.get('scene', '')}",
        f"你能感知到的：{p.get('perception', '')}",
        f"对方刚刚：{p.get('action', '')}",
        "可选动作：",
        *[f"- {a}" for a in actions],
        f"此前已经偏离史书的地方：{'；'.join(p.get('history') or []) or '无'}",
        "只输出 JSON。",
    ])
    return NPC_SYSTEM, user


CHRONICLE_SYSTEM = """你是《史记》体例的历史推演者。玩家刚刚做出一个偏离史料的选择，你要续写一段「没有发生的历史」。
规则：
1. 冷静、具体、克制。写人物与制度如何反应，不写胜利颂歌，不写因果报应。
2. 时间跨度不要太大，只写紧接着发生的事，像史书的一小段。
3. 必须承认秦的制度与兵力仍在：一个人的选择很难让历史整体掉头。
4. 80 到 140 字。用现代汉语，文风偏史传。不要出现「如果」「假如」以外的元评论，不要提到你自己或模型。
5. 输出 JSON：{"text": "续写的段落"}"""


def chronicle_prompt(p: dict) -> tuple[str, str]:
    lines = [
        f"偏离点：{p.get('divergence', '')}",
        f"史实背景：{p.get('context', '')}",
    ]
    if p.get("outcome"):
        lines.append(f"这一分支的实际结果（必须照此续写，不得改回史书的失败结局）：{p['outcome']}")
    lines.append("已经发生过的偏离：" + ("；".join(str(x) for x in (p.get('extra') or [])) or "无"))
    lines.append("只输出 JSON。")
    return CHRONICLE_SYSTEM, "\n".join(lines)


TALK_SYSTEM = """你在扮演《史记·刺客列传》里的一个人物，正与玩家面对面说话。玩家就是荆轲（或秦王），你是另一个人。
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
输出 JSON：{"reply": "你的话", "intent": "<意图 id 或 chitchat>", "option": "<决定 id 或 null>", "hint": "<一句话或空串>"}"""


def talk_prompt(p: dict) -> tuple[str, str]:
    intents = p.get("intents") or []
    options = p.get("options") or []
    history = p.get("history") or []
    npc = str(p.get("npc", ""))
    lines = [
        f"你是：{NPCS.get(npc, str(p.get('profile', '')))}",
        f"场景：{p.get('scene', '')}",
        f"你能感知到的：{p.get('perception', '')}",
        f"对方的身份：{p.get('player_role', '荆轲，燕之上卿，奉太子丹之命入秦')}",
        "对话至今：",
        *([f"- {h.get('who', '?')}：{h.get('text', '')}" for h in history[-8:]] or ["（尚无）"]),
        f"对方刚说：{p.get('text', '')}",
    ]
    if npc == "narrator":
        lines.append("你是旁白与裁决者：不要写台词，reply 只写「他停了一下，等你把话说完。」这类一句话；"
                     "重点是按玩家的话判断他选了哪个决定，填进 option。")
    if intents:
        lines.append("可选意图：")
        lines += [f"- {i.get('id')}：{i.get('desc', '')}" for i in intents]
    if options:
        lines.append("可选决定（玩家这句话若是在做决定，选一个）：")
        lines += [f"- {o.get('id')}：{o.get('label', '')}" for o in options]
    lines.append("只输出 JSON。")
    return TALK_SYSTEM, "\n".join(lines)


# -------------------------------------------------------------------- server

class Handler(BaseHTTPRequestHandler):
    server_version = "yishuihan/1.0"

    def send_body(self, status: int, body: bytes, kind: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, obj: dict) -> None:
        self.send_body(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self.serve_file(GAME / "index.html", "text/html; charset=utf-8")
        if path == "/api/health":
            return self.send_json(200, {
                "ok": True,
                "model_ready": bool(KEY) or DRY,
                "dry": DRY,
                "model": MODEL,
            })
        target = (GAME / path.lstrip("/")).resolve()
        if GAME.resolve() in target.parents and target.is_file():
            kind = {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml",
            }.get(target.suffix, "application/octet-stream")
            return self.serve_file(target, kind)
        self.send_body(404, b"not found", "text/plain; charset=utf-8")

    def serve_file(self, path: Path, kind: str) -> None:
        if not path.is_file():
            return self.send_body(404, b"not found", "text/plain; charset=utf-8")
        self.send_body(200, path.read_bytes(), kind)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self.send_json(400, {"error": "bad json"})

        if self.path == "/api/npc":
            return self.handle_npc(payload)
        if self.path == "/api/talk":
            return self.handle_talk(payload)
        if self.path == "/api/chronicle":
            return self.handle_chronicle(payload)
        self.send_json(404, {"error": "not found"})

    def handle_talk(self, p: dict) -> None:
        """Free speech: the player may type anything; the model answers in
        character and reports which listed intent (or option) it recognised.
        The world still decides: an unrecognised intent changes nothing."""
        system, user = talk_prompt(p)
        intent_ids = {str(i.get("id")) for i in (p.get("intents") or [])}
        option_ids = {str(o.get("id")) for o in (p.get("options") or [])}
        if DRY:
            reply = {"reply": "（离线占位）……", "intent": "chitchat", "option": None}
            log_call("talk-dry", system, user,
                     {"text": json.dumps(reply, ensure_ascii=False), "usage": None,
                      "cost_yuan": 0, "ms": 0}, None)
            return self.send_json(200, {**reply, "dry": True, "ms": 0})
        try:
            result = call_model(system, user, max_tokens=260, temperature=0.9)
        except Exception as exc:  # noqa: BLE001
            log_call("talk", system, user, None, str(exc))
            return self.send_json(503, {"error": str(exc)})
        data = parse_json(result["text"])
        reply = str(data.get("reply", "")).strip()
        intent = str(data.get("intent", "")).strip()
        option = data.get("option")
        option = str(option).strip() if option not in (None, "", "null") else None
        log_call("talk", system, user, result, None)
        if not reply:
            return self.send_json(502, {"error": "empty reply"})
        self.send_json(200, {
            "reply": reply,
            "intent": intent if intent in intent_ids else "chitchat",
            "requested_intent": intent,
            "option": option if option in option_ids else None,
            "requested_option": option,
            "hint": str(data.get("hint", "")).strip()[:80],
            "ms": result["ms"],
            "usage": result["usage"],
            "cost_yuan": result["cost_yuan"],
        })

    def handle_npc(self, p: dict) -> None:
        system, user = npc_prompt(p)
        allowed_list = [str(a) for a in (p.get("actions") or [])]
        if DRY:
            reply = {
                "say": "（离线占位）" + "渐离不语，只把筑横过来，一击，声音涩而长。",
                "action": allowed_list[0] if allowed_list else None,
            }
            log_call("npc-dry", system, user, {"text": json.dumps(reply, ensure_ascii=False),
                                               "usage": None, "cost_yuan": 0, "ms": 0}, None)
            return self.send_json(200, {**reply, "allowed": True, "dry": True, "ms": 0})
        try:
            result = call_model(system, user, max_tokens=220, temperature=0.92)
        except Exception as exc:  # noqa: BLE001 - reported to the client and the log
            log_call("npc", system, user, None, str(exc))
            return self.send_json(503, {"error": str(exc)})
        data = parse_json(result["text"])
        say = str(data.get("say", "")).strip()
        action = str(data.get("action", "")).strip()
        allowed = action in allowed_list
        log_call("npc", system, user, result, None)
        if not say:
            return self.send_json(502, {"error": "empty say"})
        self.send_json(200, {
            "say": say,
            "action": action if allowed else None,
            "allowed": allowed,
            "requested": action,
            "ms": result["ms"],
            "usage": result["usage"],
            "cost_yuan": result["cost_yuan"],
        })

    def handle_chronicle(self, p: dict) -> None:
        system, user = chronicle_prompt(p)
        if DRY:
            text = ("（离线占位）咸阳宫乱了三日。三日里，赵地有人杀吏，燕使的车停在函谷关外。"
                    "秦的郡县没有反，函谷关以东的户口册还在原处，只是翻页的手慢了半拍。")
            log_call("chronicle-dry", system, user,
                     {"text": text, "usage": None, "cost_yuan": 0, "ms": 0}, None)
            return self.send_json(200, {"text": text, "dry": True, "ms": 0})
        try:
            result = call_model(system, user, max_tokens=420, temperature=0.95)
        except Exception as exc:  # noqa: BLE001
            log_call("chronicle", system, user, None, str(exc))
            return self.send_json(503, {"error": str(exc)})
        data = parse_json(result["text"])
        text = str(data.get("text", "")).strip() or result["text"].strip()
        text = text[:600]
        log_call("chronicle", system, user, result, None)
        self.send_json(200, {
            "text": text,
            "ms": result["ms"],
            "usage": result["usage"],
            "cost_yuan": result["cost_yuan"],
        })

    def log_message(self, fmt: str, *args) -> None:
        print("  " + fmt % args, flush=True)


def main() -> int:
    if not KEY:
        print("! no DEEPSEEK_API_KEY: the game still runs, with the scripted fallbacks.", flush=True)
    print(f"图穷  ->  http://127.0.0.1:{PORT}   (Ctrl+C to stop)", flush=True)
    print(f"model: {MODEL} {'ready' if KEY else 'missing key'}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
