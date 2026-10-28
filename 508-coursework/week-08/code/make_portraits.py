"""The ten character portraits: ink-wash, half-length, 640x800.

    python code/make_portraits.py            # fetch only what is missing
    python code/make_portraits.py --force
    python code/make_portraits.py --only jingke,qinwang

Portraits of a single person come out far better than group scenes on the free
endpoint: the prompt has one subject, one light, one background. Every returned
image is cropped (the service logo sits in the bottom 40 px) and saved to
game/assets/portraits_hd/<slug>.jpg; the raw bytes are kept in
artifacts/portraits_raw/ and every prompt, seed and sha256 is written to
game/assets/portraits_hd/manifest.json.

A portrait that comes back wrong - a modern garment, a Japanese hairstyle, a
woman where the character is a man - is re-rolled by hand and the reject kept;
see generated/illustrations/README.md for how that review is recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "artifacts" / "portraits_raw"
OUT = HERE / "game" / "assets" / "portraits_hd"
MANIFEST = OUT / "manifest.json"
ENDPOINT = "https://image.pollinations.ai/prompt/"

STYLE = ("ink wash painting on rice paper, sumi ink, desaturated greys with one faint cinnabar accent, "
         "plain empty paper background, half length portrait, three quarter view, soft even light, "
         "a male figure, Warring States period China, 3rd century BC, no woman, no text, no watermark")

PEOPLE = [
    ("jingke", "荆轲", "a gaunt weathered Chinese man of thirty five, tired steady eyes, unkempt tied "
     "hair, plain dark indigo cross collar robe, the hilt of a straight sword at his shoulder, "
     "grave and quiet"),
    ("gaojianli", "高渐离", "a lean Chinese man of thirty, a musician, calm heavy eyes, short beard, hair "
     "tied with a plain cloth band, pale grey green cross collar robe, a long lacquered zither edge in "
     "the frame, reserved and watchful"),
    ("goutu", "狗屠", "a broad Chinese butcher of forty, thick neck, short untidy beard, coarse hemp "
     "robe with a leather apron, a cleaver at his waist, blunt good humoured face, hands of a "
     "working man"),
    ("tianguang", "田光", "an old Chinese man of seventy, a recluse, long white hair and beard, deep "
     "lined face, sunken wise eyes, plain undyed robe, a wooden staff, dignified and tired"),
    ("taizidan", "太子丹", "a young Chinese prince of twenty five, a man, fine features, anxious "
     "downturned mouth, neat hair with a small jade pin, pale silk cross collar robe with a jade "
     "pendant, high born and uneasy"),
    ("fanyuqi", "樊於期", "a Chinese general of fifty, a man, scarred face, short grey beard, "
     "lamellar leather armour over a dark robe, a torn red brown cape, grief and anger held in"),
    ("qinwuyang", "秦舞阳", "a Chinese boy of thirteen, short and slight, sharp frightened eyes, "
     "cropped hair, short hemp robe, a knife at his belt, defiant and afraid at once"),
    ("qinwang", "秦王政", "a severe young Chinese king of thirty, a man, narrow cold eyes, thin mouth, "
     "hair in a tight topknot under a tall black lacquered crown, black robe with cinnabar red trim, "
     "still and dangerous"),
    ("xiawuju", "夏无且", "a Chinese court physician of fifty, a man, mild tired face, neat short "
     "beard, grey robe with a cloth medicine pouch at the belt, cautious kind eyes"),
    ("guard", "秦郎中", "a Chinese palace guard of thirty, a man, hair tied back, dark lamellar armour, "
     "halberd shaft across the frame, blank disciplined face"),
]


def fetch(prompt: str, seed: int) -> bytes:
    query = urllib.parse.urlencode({"width": 640, "height": 800, "seed": seed,
                                    "nologo": "true", "model": "flux"})
    url = ENDPOINT + urllib.parse.quote(prompt) + "?" + query
    req = urllib.request.Request(url, headers={"User-Agent": "yishuihan/1.0 (coursework)"})
    with urllib.request.urlopen(req, timeout=180) as res:
        return res.read()


def process(raw: bytes, slug: str) -> Path:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = image.size
    image = image.crop((int(w * 0.04), int(h * 0.03), int(w * 0.96), h - 40))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{slug}.jpg"
    image.save(path, quality=88, optimize=True)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", help="comma separated slugs")
    ap.add_argument("--start", type=int, default=0, help="skip the first N (rate-limit resume)")
    args = ap.parse_args()

    only = set(args.only.split(",")) if args.only else None
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {"portraits": []}
    done = {p["slug"] for p in manifest["portraits"]}
    failures = []

    for index, (slug, name, desc) in enumerate(PEOPLE):
        if index < args.start:
            continue
        if only and slug not in only:
            continue
        if not args.force and slug in done and (OUT / f"{slug}.jpg").is_file():
            print(f"{slug}: present, skipped", flush=True)
            continue
        prompt = f"{desc}, {STYLE}"
        raw = None
        for attempt in range(1, 4):
            try:
                print(f"{slug}: attempt {attempt} ...", flush=True)
                raw = fetch(prompt, 5000 + index)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"  {exc}; waiting 70 s", flush=True)
                time.sleep(70)
        if not raw:
            failures.append(slug)
            print(f"{slug}: FAILED", flush=True)
            continue

        (RAW / f"{slug}.jpg").write_bytes(raw)
        path = process(raw, slug)
        entry = {
            "slug": slug, "name": name, "prompt": prompt, "seed": 5000 + index,
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "raw_bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "file": str(path.relative_to(HERE)).replace("\\", "/"),
            "reviewed": False,
        }
        manifest["portraits"] = [p for p in manifest["portraits"] if p["slug"] != slug] + [entry]
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{slug}: ok {len(raw)} bytes", flush=True)
        time.sleep(65)

    if failures:
        print("failed:", ", ".join(failures))
        return 1
    print("all requested portraits are present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
