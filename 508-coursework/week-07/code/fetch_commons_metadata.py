"""Fetch Wikimedia Commons metadata (URL, author, licence, date) for every
reference image used in the Week 7 assignment.

Writes sources/raw/provenance.json and prints a compact table so the
provenance table in research/sources.md can be filled in from real data
instead of guesses.

Usage:
    python code/fetch_commons_metadata.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "sources" / "raw"
OUT = RAW / "provenance.json"

API = "https://commons.wikimedia.org/w/api.php"

# Local file name -> Commons file title (without the "File:" prefix).
# Titles come from the two download scripts the student already ran
# (ak47_images/download_ak47_images*.ps1), decoded from their URL hashes.
FILES: dict[str, str] = {
    "01_ak47_general_view.png": "AK-47.png",
    "02_ak47_type1_type2_comparison.png": "AK-47 Type 1 and 2 (cropped).png",
    "03_ak47_type3_aks47_comparison.png": "AK-47 Type 3 and AKS-47.png",
    "04_ak47_type1_receiver_detail.jpg": "AK-47 Type 1 Receiver.jpg",
    "05_ak47_trigger_group_detail.jpg": "TAPCO G2 AK-47 Trigger Group & AK Hammer.jpg",
    "06_ak47_royal_armouries_detail.jpg": (
        "Royal Armouries - Up Close online exhibition - Detail of centrefire "
        "automatic rifle, Kalashnikov AK, 1953. PR.5428 (53528474954).jpg"
    ),
    "07_ak47_cross_section_diagram.jpg": "Typ-56-AK47-crossection-bayonet-removed.jpg",
    "08_ak47_disassembled_parts.jpg": "AK-disassembled.jpg",
    "09_ak47_disassembly_view.jpg": "AK-disassembled.jpg",
    "10_ak47_field_stripped.jpg": "Gp wasr-10 63 Field Stripped.jpg",
    "11_ak47_converted_parts.jpg": "Converted Izhmash AK 47.JPG",
    "12_ak47_repair_disassembly.jpg": "Weapons repair 121115-A-YI377-0151.jpg",
    "13_ak47_first_model_museum_view.jpg": "First AK 47.jpg",
    "14_ak47_athens_museum_3quarter_view.jpg": (
        "Soviet automatic rifle AK 47 at Athens War Museum on November 22, 2022.jpg"
    ),
    "15_ak47_type2_right_side_view.jpg": "AK-47 type II Part DM-ST-89-01131.jpg",
    "16_ak47_bolt_carrier_gas_piston.jpg": "AK-Bolt-Carrier-Bolt-and-Gas piston.jpg",
    "17_ak47_rear_sight_detail.jpg": "AK47-rear-sight.jpg",
    "18_ak47_type1_magazine.png": "Type 1 AK-47 Magazine.png",
    "19_ak47_aks_folding_stock.jpg": "AK folding.jpg",
    "20_akm_muzzle_detail.jpg": "AKM muzzle brake.jpg",
    # Two images were dropped into the week folder without a download script;
    # their Commons titles are resolved by searching Commons below.
    "AK-47_assault_rifle.jpg": "@search:AK-47 assault rifle",
    "AK-47_type_II_noBG.png.webp": "@search:AK-47 Type II noBG",
}

STRIP_HTML = re.compile(r"<[^>]+>")


def api(params: dict[str, str], tries: int = 6) -> dict:
    """Call the Commons API politely: one request at a time, with backoff.

    The first run hit HTTP 429 (rate limited) because it fired ~20 requests
    back to back, so every call now sleeps and retries on 429/5xx.
    """
    params = {"format": "json", "formatversion": "2", **params}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "DHG508-coursework/1.0 (educational, contact: student)"}
    )
    delay = 3.0
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            time.sleep(1.5)
            return data
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == tries - 1:
                raise
            print(f"      HTTP {exc.code}; retrying in {delay:.0f}s", file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def search_title(query: str) -> str | None:
    data = api({"action": "query", "list": "search", "srsearch": query, "srnamespace": "6", "srlimit": "5"})
    hits = data.get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def imageinfo(title: str) -> dict:
    data = api(
        {
            "action": "query",
            "titles": "File:" + title,
            "prop": "imageinfo",
            "iiprop": "url|user|timestamp|extmetadata|size|mime",
        }
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        return {}
    info = pages[0].get("imageinfo", [{}])[0]
    meta = info.get("extmetadata", {})

    def field(key: str) -> str:
        value = meta.get(key, {}).get("value", "")
        return STRIP_HTML.sub("", str(value)).strip()

    width = info.get("width")
    height = info.get("height")
    return {
        "commons_title": pages[0]["title"],
        "descriptionurl": info.get("descriptionurl", ""),
        "url": info.get("url", ""),
        "author": field("Artist"),
        "credit": field("Credit"),
        "licence": field("LicenseShortName"),
        "licence_url": field("LicenseUrl"),
        "date": field("DateTimeOriginal"),
        "description": field("ImageDescription")[:400],
        "width": width,
        "height": height,
        "mime": info.get("mime", ""),
    }


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    if OUT.exists():
        try:
            results = json.loads(OUT.read_text(encoding="utf-8"))
            print(f"Resuming with {len(results)} cached entries")
        except json.JSONDecodeError:
            results = {}
    for name, target in FILES.items():
        if name in results:
            print(f"CACHE {name}")
            continue
        local = RAW / name
        if not local.exists():
            # keep provenance for files the student has but that live one
            # directory up (the two un-scripted images)
            alt = ROOT / name
            if not alt.exists():
                print(f"SKIP  {name}: no local file", file=sys.stderr)
                continue
        title = target
        try:
            if title.startswith("@search:"):
                found = search_title(title.split("@search:", 1)[1])
                if not found:
                    print(f"WARN  {name}: Commons search found nothing", file=sys.stderr)
                    continue
                title = found.removeprefix("File:")
            info = imageinfo(title)
        except Exception as exc:  # noqa: BLE001 - keep going, report at the end
            print(f"FAIL  {name}: {exc}", file=sys.stderr)
            continue
        if not info:
            print(f"WARN  {name}: Commons returned no imageinfo for {title!r}", file=sys.stderr)
            continue
        info["local_file"] = name
        info["queried_as"] = target
        results[name] = info
        OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"OK    {name} -> {info['commons_title']} | {info['licence']} | {info['author'][:60]}")

    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {OUT} ({len(results)} entries)")
    missing = sorted(set(FILES) - set(results))
    if missing:
        print("Not resolved: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
