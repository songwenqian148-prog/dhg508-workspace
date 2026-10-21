"""Generate the two comparison images for Week 7 with Pollinations.

Why this tool: the assignment allows any generator, but no image-generation API
key exists in this workspace. Pollinations serves text-to-image over plain HTTP
with no account and no key, so the whole run is reproducible and costs nothing.
The free tier is anonymous and best-effort, so every request is retried, every
seed is kept, and nothing is silently discarded.

Images produced:
  generated/a_words_only/     the "no sources, words alone" baseline
  generated/b_from_sources/   the researched image
  generated/manifest.json     prompt, seed, size, model, bytes, md5, timestamp

Usage:
    python code/generate_images.py --seeds 1 2 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "generated"
ENDPOINT = "https://image.pollinations.ai/prompt/"
UA = "DHG508-coursework/1.0 (educational; student assignment)"

# --- The two prompts -------------------------------------------------------
# A: what someone with no sources types after seeing the words "AK-47".
#    Short, one sentence, no dates, no receiver type, no furniture detail.
PROMPT_A = "a photograph of an AK-47 assault rifle on a table"

# B: built only from claims that appear in the sources collected in
#    research/sources.md (Modern Firearms on the 1951-55 Type 2, Wikipedia on
#    the 1951 milled receiver, the Commons photographs of Type 1 / Type 2 /
#    Type 3 for the visible differences).
PROMPT_B = (
    "documentary colour photograph, Soviet Kalashnikov AK-47 Type 2 rifle as made in 1951 to 1955, "
    "7.62x39mm, 870 mm long with a 415 mm barrel, blued steel with wear on the edges, "
    "machined milled steel receiver cut from one solid block, flat solid receiver sides with no "
    "rows of stamped rivets and no long lightening cut, separate steel stock socket pinned to the "
    "rear of the receiver, varnished birch wooden buttstock, one-piece wooden pistol grip fastened "
    "by a single vertical bolt under the receiver, wooden upper handguard and wooden lower handguard "
    "with the forward sling loop at the front of the lower handguard, long-stroke gas piston in a "
    "tube above the barrel, steeply curved 30-round slab-sided steel magazine, tall front sight base "
    "near the muzzle, tangent rear sight, combined safety and fire selector lever on the right side, "
    "plain museum backdrop, sharp focus, whole rifle in frame, no text, no watermark"
)

JOBS = {
    "a_words_only": PROMPT_A,
    "b_from_sources": PROMPT_B,
}


def fetch(url: str, dest: pathlib.Path, tries: int = 5) -> dict:
    delay = 8.0
    last: Exception | None = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            if len(data) < 5_000:
                raise RuntimeError(f"suspiciously small image ({len(data)} bytes)")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return {
                "bytes": len(data),
                "md5": hashlib.md5(data).hexdigest(),
                "attempts": attempt + 1,
            }
        except Exception as exc:  # noqa: BLE001
            last = exc
            print(f"      retry {attempt + 1}/{tries} after {exc}", flush=True)
            time.sleep(delay)
            delay *= 1.8
    raise RuntimeError(f"failed after {tries} attempts: {last}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[11, 23, 37])
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--model", default="flux")
    args = ap.parse_args()

    manifest_path = GEN / "manifest.json"
    manifest: dict = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for folder, prompt in JOBS.items():
        for seed in args.seeds:
            key = f"{folder}/seed{seed}"
            if key in manifest:
                print(f"CACHE {key}")
                continue
            query = urllib.parse.urlencode(
                {
                    "width": args.width,
                    "height": args.height,
                    "seed": seed,
                    "model": args.model,
                    "nologo": "true",
                }
            )
            url = f"{ENDPOINT}{urllib.parse.quote(prompt)}{'?'}{query}"
            dest = GEN / folder / f"seed{seed}.png"
            print(f"GET   {key}", flush=True)
            try:
                info = fetch(url, dest)
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL  {key}: {exc}")
                continue
            manifest[key] = {
                "prompt": prompt,
                "seed": seed,
                "width": args.width,
                "height": args.height,
                "model_requested": args.model,
                "service": "pollinations.ai (anonymous free tier, no key)",
                "cost_usd": 0.0,
                "url": url,
                "file": str(dest.relative_to(ROOT)).replace("\\", "/"),
                "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **info,
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"OK    {key}: {info['bytes']:,} bytes md5={info['md5'][:12]}")

    print(f"\nmanifest: {manifest_path} ({len(manifest)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
