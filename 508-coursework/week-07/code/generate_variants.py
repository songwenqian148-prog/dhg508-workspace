"""Second round of image generation: shorter, better-composed prompts.

The first round showed that the free Pollinations/SANA backend loses the plot
on a 150-word prompt: it produced duplicated receivers, two magazines and a
second barrel. These variants keep only the details a 2D generator can actually
show (furniture material, receiver type, magazine shape, era) and ask for a
clean side-on catalogue view instead of a table-top scene.

Output: generated/variants/<variant>/seed<seed>.png + manifest_variants.json
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "generated" / "variants"
MANIFEST = OUT / "manifest_variants.json"
ENDPOINT = "https://image.pollinations.ai/prompt/"
UA = "DHG508-coursework/1.0 (educational; student assignment)"

VARIANTS = {
    # words-alone baseline, but phrased the way a person who has seen the name
    # "AK-47" would phrase it, so the comparison is about research, not luck
    "a_naive": "a photograph of an AK-47 rifle, side view, whole rifle, plain background",
    # researched, compact: only the features a 2D generator can show
    "b_compact": (
        "1953 Soviet AK-47 Type 2 rifle, side view, full length, one rifle only, "
        "solid milled steel receiver without rivets, dark blued metal, varnished wooden buttstock, "
        "wooden pistol grip, wooden handguards, curved 30-round steel magazine, "
        "plain grey studio background, catalogue photograph"
    ),
    # researched, medium: adds the details that separate Type 2 from the AKM
    "b_medium": (
        "museum catalogue photograph, left side view, complete 1950s Soviet Kalashnikov AK-47, "
        "machined steel receiver cut from a solid block so the sides are flat and there are no rivets, "
        "blued steel with worn edges, wooden buttstock and wooden handguards with a warm red-brown "
        "varnish, one-piece wooden pistol grip, long curved 30-round steel magazine, thin barrel with "
        "a tall front sight, plain light grey background, one rifle, centred, sharp focus"
    ),
}


def fetch(url: str, dest: pathlib.Path, tries: int = 4) -> dict:
    delay = 10.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=240) as resp:
                data = resp.read()
            if len(data) < 5_000:
                raise RuntimeError(f"small payload ({len(data)} bytes)")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return {"bytes": len(data), "md5": hashlib.md5(data).hexdigest(), "attempts": attempt + 1}
        except Exception as exc:  # noqa: BLE001
            print(f"      retry {attempt + 1}/{tries}: {exc}", flush=True)
            time.sleep(delay)
            delay *= 1.6
    raise RuntimeError("all attempts failed")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    for variant, prompt in VARIANTS.items():
        for seed in (5, 17, 29):
            key = f"{variant}/seed{seed}"
            if key in manifest:
                continue
            query = urllib.parse.urlencode({"width": 1024, "height": 768, "seed": seed,
                                            "model": "flux", "nologo": "true"})
            url = f"{ENDPOINT}{urllib.parse.quote(prompt)}?{query}"
            print(f"GET   {key}", flush=True)
            try:
                info = fetch(url, OUT / variant / f"seed{seed}.png")
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL  {key}: {exc}")
                continue
            manifest[key] = {
                "prompt": prompt,
                "seed": seed,
                "model_requested": "flux",
                "service": "pollinations.ai (anonymous free tier, no key)",
                "cost_usd": 0.0,
                "url": url,
                "file": str((OUT / variant / f"seed{seed}.png").relative_to(ROOT)).replace("\\", "/"),
                "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **info,
            }
            MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"OK    {key}: {info['bytes']:,} bytes")
    print(f"manifest: {MANIFEST} ({len(manifest)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
