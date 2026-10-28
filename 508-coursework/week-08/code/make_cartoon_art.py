"""Q-version (chibi) art for 图穷: eleven portraits and five scene backgrounds.

    python code/make_cartoon_art.py                 # only what is missing
    python code/make_cartoon_art.py --force
    python code/make_cartoon_art.py --only jingke,qinwang
    python code/make_cartoon_art.py --scenes        # backgrounds only
    python code/make_cartoon_art.py --portraits     # portraits only

Style: chibi / Q版 - huge round head, tiny body, two heads tall, flat colour,
thick outline, pastel. The brief for this version does not ask for a
reconstruction of Warring-States material culture, so the designs are
character-first and are declared invented in research/design.md.

What this endpoint answers to (measured, see research/tool_log.md §4): the style
phrase must come FIRST, before the costume, and it responds to genre tokens -
"chibi", "Q version", "kawaii" - rather than to art direction words.

Outputs (all tracked; the raw bytes stay in artifacts/cartoon_raw/):
    game/assets/cartoon/portraits/<slug>.png   640x800
    game/assets/cartoon/scenes/<slug>.png      960x540
    game/assets/cartoon/manifest.json
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
RAW = HERE / "artifacts" / "cartoon_raw"
OUT = HERE / "game" / "assets" / "cartoon"
MANIFEST = OUT / "manifest.json"
ENDPOINT = "https://image.pollinations.ai/prompt/"

STYLE_PORTRAIT = ("super deformed chibi anime character, comedy spin-off style, thick black outlines, "
                  "bold flat colours, huge round head, tiny body, big round eyes with simple highlights, "
                  "tiny mouth, simple cel shading, plain bright background, no text, no watermark")

STYLE_SCENE = ("chibi style cute background, simple flat shapes, thick clean outline, pastel palette, "
               "soft warm light, empty of people, no text, no watermark")

PORTRAITS = [
    ("jingke", "荆轲", 30,
     "a young swordsman, short topknot, blue ancient Chinese robe, a sword on his back, determined eyes"),
    ("gaojianli", "高渐离", 30,
     "a quiet young musician, short hair with a cloth band, pale green robe, a small zither, soft smile"),
    ("goutu", "狗屠", 40,
     "a big cheerful butcher, short beard, leather apron, a cleaver, wide grin"),
    ("tianguang", "田光", 70,
     "a kind old man, long white beard, plain robe, wooden staff, gentle smile"),
    ("taizidan", "太子丹", 25,
     "a young prince, short hair with a small jade crown, pale silk robe, worried face"),
    ("fanyuqi", "樊於期", 50,
     "a scarred old general, grey beard, lamellar armour, torn red cape, brave frown"),
    ("qinwuyang", "秦舞阳", 13,
     "a small boy of thirteen, cropped hair, short hemp robe, a small knife, fierce little face"),
    ("qinwang", "秦王政", 30,
     "a young king, short black hair under a tall black crown, black robe with red trim, stern face"),
    ("xiawuju", "夏无且", 50,
     "a mild old physician, short beard, grey robe, a medicine pouch, worried kind eyes"),
    ("guard", "秦郎中", 30,
     "a young palace guard, short hair tied back, dark armour, a tall halberd, serious face"),
    ("mengjia", "蒙嘉", 45,
     "a smooth court official, thin moustache, dark official robe, a wooden tablet, sly smile"),
]

SCENES = [
    ("yan_market", "燕市", 101,
     "a cute ancient Chinese market street at dusk, low timber stalls, cloth awnings, clay wine jars, "
     "paper lanterns, reeds by a river"),
    ("taizi_gong", "太子宫", 102,
     "a cute quiet Chinese palace hall, wooden pillars, woven mats, a long curtain, small braziers"),
    ("fanyuqi_room", "舍人馆", 103,
     "a cute small plain room, low table, a mat, one warm oil lamp, a sword rack"),
    ("yi_river", "易水", 104,
     "a cute cold wide river at dusk, wind bent reeds, bare willows, a dirt road, pink and grey sky"),
    ("xianyang_hall", "咸阳宫", 105,
     "a cute vast dark throne hall, tall red pillars, patterned floor, glowing bronze lamps, a low "
     "throne"),
]


def fetch(prompt: str, seed: int, width: int, height: int) -> bytes:
    query = urllib.parse.urlencode({"width": width, "height": height, "seed": seed,
                                    "nologo": "true", "model": "flux"})
    req = urllib.request.Request(ENDPOINT + urllib.parse.quote(prompt) + "?" + query,
                                 headers={"User-Agent": "yishuihan/1.0 (coursework)"})
    with urllib.request.urlopen(req, timeout=180) as res:
        return res.read()


def save(raw: bytes, slug: str, kind: str, size: tuple[int, int]) -> Path:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = image.size
    image = image.crop((int(w * 0.02), int(h * 0.02), int(w * 0.98), h - 40))   # service logo
    image = image.resize(size, Image.LANCZOS)
    out = OUT / kind
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{slug}.png"
    image.save(path, optimize=True)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", help="comma separated slugs")
    ap.add_argument("--portraits", action="store_true")
    ap.add_argument("--scenes", action="store_true")
    args = ap.parse_args()

    only = set(args.only.split(",")) if args.only else None
    want_portraits = args.portraits or not args.scenes
    want_scenes = args.scenes or not args.portraits

    RAW.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {"items": []}
    done = {i["slug"] for i in manifest["items"]}
    failures = []

    jobs = []
    if want_portraits:
        jobs += [("portraits", slug, name, seed, desc, STYLE_PORTRAIT) for slug, name, seed, desc in PORTRAITS]
    if want_scenes:
        jobs += [("scenes", slug, name, seed, desc, STYLE_SCENE) for slug, name, seed, desc in SCENES]

    for index, (kind, slug, name, seed, desc, style) in enumerate(jobs):
        if only and slug not in only:
            continue
        target = OUT / kind / f"{slug}.png"
        if not args.force and slug in done and target.is_file():
            print(f"{slug}: present, skipped", flush=True)
            continue
        size = (640, 800) if kind == "portraits" else (960, 540)
        prompt = f"{style}, {desc}"
        raw = None
        for attempt in range(1, 4):
            try:
                print(f"{slug}: attempt {attempt} ...", flush=True)
                w, h = (1024, 1280) if kind == "portraits" else (1280, 720)
                raw = fetch(prompt, 7000 + index, w, h)
                break
            except urllib.error.HTTPError as exc:
                print(f"  HTTP {exc.code}; waiting 70 s", flush=True)
                time.sleep(70)
            except Exception as exc:  # noqa: BLE001
                print(f"  {exc}; waiting 30 s", flush=True)
                time.sleep(30)
        if not raw:
            failures.append(slug)
            print(f"{slug}: FAILED", flush=True)
            continue
        (RAW / f"{slug}.jpg").write_bytes(raw)
        path = save(raw, slug, kind, size)
        entry = {
            "slug": slug, "name": name, "kind": kind, "prompt": prompt, "seed": 7000 + index,
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "raw_bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "file": str(path.relative_to(HERE)).replace("\\", "/"),
        }
        manifest["items"] = [i for i in manifest["items"] if i["slug"] != slug] + [entry]
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{slug}: ok {len(raw)} bytes -> {path.name}", flush=True)
        time.sleep(60)

    if failures:
        print("failed:", ", ".join(failures))
        return 1
    print("all requested art is present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
