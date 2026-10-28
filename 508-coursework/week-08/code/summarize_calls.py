"""Summarise the model call log into the numbers the report quotes.

    python code/summarize_calls.py

Reads artifacts/logs/calls.jsonl and prints, then writes
artifacts/logs/summary.md: calls per kind, token totals, cost, latency.
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
LOG = PROJECT / "artifacts" / "logs" / "calls.jsonl"
OUT = PROJECT / "artifacts" / "logs" / "summary.md"


def main() -> int:
    if not LOG.is_file():
        print("no calls logged yet:", LOG)
        return 1
    rows = [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_kind = defaultdict(list)
    for row in rows:
        by_kind[row["kind"]].append(row)

    lines = ["| kind | calls | prompt tok | completion tok | cost (yuan) | median ms |", "| --- | --- | --- | --- | --- | --- |"]
    total_cost = 0.0
    total_calls = 0
    for kind, group in sorted(by_kind.items()):
        usage = [g["usage"] or {} for g in group]
        pt = sum(u.get("prompt_tokens", 0) or 0 for u in usage)
        ct = sum(u.get("completion_tokens", 0) or 0 for u in usage)
        cost = sum(g["cost_yuan"] or 0 for g in group)
        lat = [g["ms"] for g in group if g["ms"]]
        med = int(statistics.median(lat)) if lat else 0
        total_cost += cost
        total_calls += len(group)
        lines.append(f"| {kind} | {len(group)} | {pt} | {ct} | {cost:.4f} | {med} |")
    lines.append(f"| **total** | **{total_calls}** | | | **{total_cost:.4f}** | |")

    errors = [r for r in rows if r.get("error")]
    text = "\n".join(lines)
    print(text)
    print(f"\nerrors: {len(errors)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f"# Model call summary\n\n{text}\n\nerrors: {len(errors)}\n", encoding="utf-8")
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
