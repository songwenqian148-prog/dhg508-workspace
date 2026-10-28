"""Smoke test for the two model endpoints. Costs a fraction of a cent.

    python code/smoke_ai.py

Prints the JSON the game would receive, then the tail of the call log, so the
cost and latency of a real call are visible. The key itself is never printed.
"""
from __future__ import annotations

import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8765"


def post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> int:
    npc = post("/api/npc", {
        "npc": "gaojianli",
        "scene": "燕市酒肆，日暮",
        "perception": "荆轲坐在你对面，酒已半酣；狗屠在旁剔肉；市声渐稀。",
        "action": "举爵，请渐离击筑",
        "actions": ["举爵，请渐离击筑", "问：足下击筑，其声何哀？", "默然，看市中人往来"],
        "history": [],
    })
    print("NPC  ->", json.dumps(npc, ensure_ascii=False, indent=2))

    chron = post("/api/chronicle", {
        "divergence": "田光自刎之后，荆轲没有去太子宫，而是连夜离开了燕国。",
        "context": "荆轲是卫人，游于诸侯；田光以死激之。若他不受此托，燕太子丹将另求刺客。",
        "extra": [],
    })
    print("CHRONICLE ->", json.dumps(chron, ensure_ascii=False, indent=2))

    ok = bool(npc.get("say")) and bool(chron.get("text"))
    print("\nOK" if ok else "\nFAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
