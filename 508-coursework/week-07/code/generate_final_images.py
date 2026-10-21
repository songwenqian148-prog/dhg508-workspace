"""Final image generation for Week 7, respecting the free-tier rate limit.

The first round hit `402 FREE_LIMIT: 1 image every 45 seconds per IP`. This
script reads the retry hint out of that response, waits, retries, and then
keeps a 50 second gap between requests. Both roles (the words-only baseline and
the source-based image) are asked for the same kind of picture - one whole
rifle, side view, plain background - so the comparison is about what the prompt
knows, not about composition luck.

Usage: python code/generate_final_images.py
"""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "generated" / "final"
MANIFEST = OUT / "manifest_final.json"
ENDPOINT = "https://image.pollinations.ai/prompt/"
UA = "DHG508-coursework/1.0 (educational; student assignment)"

JOBS = [
    # role, prompt, seed
    ("baseline", "a photograph of an AK-47 rifle, side view, whole rifle, plain background", 11),
    ("baseline", "a photograph of an AK-47 rifle, side view, whole rifle, plain background", 41),
    ("researched",
     "full side view photograph of a 1953 Soviet AK-47 rifle, wooden buttstock, wooden handguards, "
     "brown wooden pistol grip, curved black steel magazine, no scope, plain white studio background, "
     "one complete rifle, nothing cropped", 11),
    ("researched",
     "1950s Soviet Kalashnikov rifle product photograph, full length side view, wood stock and wooden "
     "handguard, curved black magazine, tall front sight, white background", 23),
    ("researched",
     "vintage 1950s Soviet assault rifle with wooden stock, wooden handguards and a curved steel magazine, "
     "side view, white seamless background, museum catalogue photograph, whole rifle in frame", 37),
]


def request_image(prompt: str, seed: int, tries: int = 4) -> tuple[bytes, str]:
    query = urllib.parse.urlencode({"width": 1024, "height": 768, "seed": seed, "nologo": "true"})
    url = f"{ENDPOINT}{urllib.parse.quote(prompt)}?{query}"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
            if data[:1] == b"{":
                raise RuntimeError("service returned JSON instead of an image")
            if len(data) < 5_000:
                raise RuntimeError(f"small payload ({len(data)} bytes)")
            return data, url
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            hint = re.search(r"Retry after (\d+)s", body)
            wait = int(hint.group(1)) + 3 if hint else 20 * (attempt + 1)
            print(f"      HTTP {exc.code}, waiting {wait}s ({body[:120]})", flush=True)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            print(f"      error {exc}, waiting 20s", flush=True)
            time.sleep(20)
    raise RuntimeError("all attempts failed")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    for i, (role, prompt, seed) in enumerate(JOBS):
        key = f"{role}/seed{seed}"
        if key in manifest:
            print(f"CACHE {key}")
            continue
        if i:
            time.sleep(50)
        print(f"GET   {key}", flush=True)
        try:
            data, url = request_image(prompt, seed)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {key}: {exc}")
            continue
        path = OUT / role / f"seed{seed}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        manifest[key] = {
            "role": role,
            "prompt": prompt,
            "seed": seed,
            "service": "pollinations.ai anonymous free tier (no key, 1 image / 45 s)",
            "model_note": "service exposes only a default text-to-image model; no model parameter is honoured",
            "cost_usd": 0.0,
            "url": url,
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": len(data),
            "md5": hashlib.md5(data).hexdigest(),
            "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"OK    {key}: {len(data):,} bytes")
    print(f"manifest: {MANIFEST} ({len(manifest)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
