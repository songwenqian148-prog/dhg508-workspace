"""Make sure every image in generated/final/ has a manifest entry.

`gen_final.ps1` writes no manifest (the Python version did), so this script
reconciles the folder with the manifest: existing entries are kept, missing files
are added with the prompt they were generated from, and error stubs are removed
from the record.

Usage: python code/update_manifest.py
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
FINAL = ROOT / "generated" / "final"
MANIFEST = FINAL / "manifest_final.json"

PROMPTS = {
    "baseline": "a photograph of an AK-47 rifle, side view, whole rifle, plain background",
    "researched": (
        "a photograph of an AK-47 rifle with a wooden stock and wooden handguard, no scope, "
        "side view, whole rifle, plain background"
    ),
}
SEEDS = {"wooden_stock": 61}

# the earlier round-2 researched prompt, kept so the manifest explains seed11
EARLIER = {
    "researched/seed11": (
        "full side view photograph of a 1953 Soviet AK-47 rifle, wooden buttstock, wooden handguards, "
        "brown wooden pistol grip, curved black steel magazine, no scope, plain white studio "
        "background, one complete rifle, nothing cropped"
    )
}


def seed_of(path: pathlib.Path) -> int:
    if path.stem.startswith("seed"):
        return int(path.stem[4:])
    return SEEDS.get(path.stem, 0)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    added = 0
    for path in sorted(FINAL.glob("*/*.jpg")):
        if path.stat().st_size < 20_000:
            print(f"skip tiny/error file {path.name}")
            continue
        key = f"{path.parent.name}/{path.stem}"
        data = path.read_bytes()
        prompt = EARLIER.get(key, PROMPTS.get(path.parent.name, ""))
        entry = {
            "role": path.parent.name,
            "prompt": prompt,
            "seed": seed_of(path),
            "service": "pollinations.ai anonymous free tier (no key, 1 image / 45 s)",
            "model_note": "only a default text-to-image model is exposed; the model parameter is ignored",
            "size_returned": "886x665 JPEG (requested 1024x768)",
            "cost_usd": 0.0,
            "file": path.relative_to(ROOT).as_posix(),
            "bytes": len(data),
            "md5": hashlib.md5(data).hexdigest(),
            "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if key in manifest:
            manifest[key].update({k: v for k, v in entry.items() if k != "recorded_utc"})
        else:
            manifest[key] = entry
            added += 1
            print(f"added {key}")

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{MANIFEST.relative_to(ROOT)}: {len(manifest)} entries ({added} new)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
