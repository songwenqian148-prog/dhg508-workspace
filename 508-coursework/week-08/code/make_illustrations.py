"""The six key images: ink-wash mood pieces, fetched from Pollinations.

    python code/make_illustrations.py              # fetch only what is missing
    python code/make_illustrations.py --force      # refetch everything
    python code/make_illustrations.py --only yi_river

Why landscapes and objects, with no people: the free endpoint draws convincing
ink-wash landscape and still life, but it cannot draw a Warring-States person -
the first attempt at this project produced a woman in a bathrobe standing in the
Yi river, and a Qin hall that looked like a Ming corridor. Those failures are
kept in artifacts/illustrations-rejected/ and described in research/tool_log.md.

Each image: 1024x576 from the endpoint, then the bottom 40 px (the service's
logo, which nologo=true does not remove) and a thin paper border are cropped,
and the result is saved twice -
    generated/illustrations/<slug>.png        768x432, for the README
    generated/illustrations/pixel/<slug>.png  384x216, quantised to the game palette

The raw bytes are kept untouched in artifacts/illustrations_raw/ (git-ignored),
and every prompt, seed, byte count and sha256 is written to
generated/illustrations/manifest.json.
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
RAW = HERE / "artifacts" / "illustrations_raw"
OUT = HERE / "generated" / "illustrations"
PIXEL = OUT / "pixel"
MANIFEST = OUT / "manifest.json"

ENDPOINT = "https://image.pollinations.ai/prompt/"

# Short prompts only. Long, style-first prompts were measured to drift badly on
# this endpoint - a 40-word ink-wash brief for the Yi river came back as a drawing
# of stones in a tray. The wording below puts the subject first, in one sentence,
# and the style last, and it is copied from the one prompt that worked first try.
STYLE_TAIL = ("empty of people, monochrome sumi ink wash painting on rice paper, one faint "
              "cinnabar accent, large open sky, quiet, no text")

SCENES = [
    ("yan_market", "燕市", 227001,
     "a narrow market lane inside a mud-walled town at dusk, low timber shop fronts, cloth awnings, "
     "three clay wine jars and a butcher's block in the foreground"),
    ("yi_river", "易水送别", 227002,
     "a cold wide river under a low grey sky, wind bent reeds on a muddy bank, bare willows, "
     "a rutted dirt road with one small wooden chariot far off"),
    ("map_unrolled", "图穷匕见", 227003,
     "a long unrolled silk map scroll across a dark polished floor, painted rivers and roads, "
     "a short bronze dagger lying on it, one bronze lamp"),
    ("pillar_chase", "绕柱", 227004,
     "the inside of a great dark timber hall, tall red lacquered columns in shadow, a patterned "
     "mat floor, one long straight sword in a black scabbard on the boards"),
    ("last_laugh", "倚柱而笑", 227005,
     "a dark stain across pale stone floor at the base of a thick red lacquered column, a short "
     "bronze dagger struck in the wood, cold grey light"),
    ("epilogue_zhu", "高渐离举筑", 227006,
     "a dark empty hall, a long narrow five string zither broken on the floorboards, strings "
     "snapped and curling, dust in a shaft of light from a high door"),
]

PALETTE = [
    (10, 9, 8), (20, 18, 15), (34, 29, 25), (43, 38, 34), (74, 64, 56), (85, 72, 60),
    (90, 80, 69), (107, 79, 58), (107, 97, 87), (125, 107, 85), (138, 122, 102),
    (155, 138, 114), (168, 154, 134), (201, 191, 174), (217, 207, 189), (239, 230, 212),
    (168, 53, 42), (176, 141, 79), (74, 107, 90), (47, 59, 76), (70, 89, 107),
]


def pollinations(prompt: str, seed: int, width: int = 1024, height: int = 576) -> bytes:
    query = urllib.parse.urlencode({
        "width": width, "height": height, "seed": seed, "nologo": "true", "model": "flux",
    })
    url = ENDPOINT + urllib.parse.quote(prompt) + "?" + query
    req = urllib.request.Request(url, headers={"User-Agent": "yishuihan/1.0 (coursework)"})
    with urllib.request.urlopen(req, timeout=180) as res:
        return res.read()


def process(raw: bytes, slug: str) -> tuple[Path, Path]:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = image.size
    # drop the service logo (bottom 40 px) and a thin paper border
    image = image.crop((int(w * 0.02), int(h * 0.03), int(w * 0.98), h - 40))
    web = image.resize((768, 432), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    PIXEL.mkdir(parents=True, exist_ok=True)
    web_path = OUT / f"{slug}.png"
    web.save(web_path)

    small = image.resize((384, 216), Image.NEAREST)
    pal = Image.new("P", (1, 1))
    flat = [c for rgb in PALETTE for c in rgb]
    pal.putpalette(flat + flat[: 768 - len(flat)])
    pixel_path = PIXEL / f"{slug}.png"
    small.convert("RGB").quantize(palette=pal, dither=Image.NONE).save(pixel_path)
    return web_path, pixel_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", help="comma-separated slugs")
    args = ap.parse_args()

    only = set(args.only.split(",")) if args.only else None
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {"images": []}
    done = {entry["slug"] for entry in manifest["images"]}
    failures = []

    for slug, title, seed, scene in SCENES:
        if only and slug not in only:
            continue
        if not args.force and slug in done and (OUT / f"{slug}.png").is_file():
            print(f"{slug}: present, skipped")
            continue
        prompt = f"{scene}, {STYLE_TAIL}"
        raw = None
        for attempt in range(1, 6):
            try:
                print(f"{slug}: attempt {attempt} ...", flush=True)
                raw = pollinations(prompt, seed)
                break
            except urllib.error.HTTPError as exc:
                print(f"  HTTP {exc.code}, waiting 70 s", flush=True)
                time.sleep(70)
            except Exception as exc:  # noqa: BLE001
                print(f"  {exc}, waiting 30 s", flush=True)
                time.sleep(30)
        if not raw:
            failures.append(slug)
            print(f"{slug}: FAILED after 5 attempts")
            continue

        (RAW / f"{slug}.jpg").write_bytes(raw)
        web, pixel = process(raw, slug)
        entry = {
            "slug": slug,
            "title": title,
            "prompt": prompt,
            "seed": seed,
            "endpoint": ENDPOINT,
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "raw_bytes": len(raw),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "web": str(web.relative_to(HERE)).replace("\\", "/"),
            "pixel": str(pixel.relative_to(HERE)).replace("\\", "/"),
            "crop": "2% sides, 3% top, bottom 40 px (service logo) removed",
        }
        manifest["images"] = [e for e in manifest["images"] if e["slug"] != slug] + [entry]
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{slug}: ok  {len(raw)} bytes  -> {web.name}")
        time.sleep(70)          # the free tier serves about one image every 45-70 s

    if failures:
        print("failed:", ", ".join(failures))
        return 1
    print("all requested images are present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
