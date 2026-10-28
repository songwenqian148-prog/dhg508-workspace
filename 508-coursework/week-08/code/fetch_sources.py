"""Fetch the Shiji chapters this simulation rests on, from Chinese Wikisource.

    python code/fetch_sources.py

Writes, for each chapter:
    sources/raw/<slug>.wikitext.txt       the page as served (kept, unedited)
    sources/processed/<slug>.txt          cleaned plain text
    sources/raw/provenance.json           url, fetch time, pageid, revision, licence

The transcription on zh.wikisource.org is public domain (the Shiji is a Han
dynasty text); the wiki page itself is CC BY-SA 4.0, which is why the url and
the revision id are kept beside every file.
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "sources" / "raw"
PROCESSED = HERE / "sources" / "processed"
API = "https://zh.wikisource.org/w/api.php"
UA = "dhg508-coursework/1.0 (historical simulation coursework; contact: songwenqian148@gmail.com)"

CHAPTERS = [
    # slug, page title, what it gives this project
    ("shiji_086_cike", "史記/卷086", "刺客列傳 - the spine of the simulation: Jing Ke from Wei to the Qin court"),
    ("shiji_006_qinshihuang", "史記/卷006", "秦始皇本紀 - the Qin side of the attempt, and what followed in Yan"),
    ("shiji_034_yan", "史記/卷034", "燕召公世家 - Crown Prince Dan, and King Xi of Yan killing him to appease Qin"),
]


def fetch_wikitext(title: str) -> dict:
    query = urllib.parse.urlencode(
        {
            "action": "parse",
            "page": title,
            "prop": "wikitext|revid",
            "redirects": "1",
            "format": "json",
            "formatversion": "2",
        }
    )
    req = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    if "error" in data:
        raise RuntimeError(f"{title}: {data['error'].get('info')}")
    return data["parse"]


def strip_templates(text: str) -> str:
    """Remove {{nested|templates}} innermost-first; the chapter body needs none of them."""
    pattern = re.compile(r"\{\{[^{}]*\}\}", re.S)
    for _ in range(40):
        new = pattern.sub("", text)
        if new == text:
            return new
        text = new
    return text


def clean(wikitext: str) -> str:
    text = wikitext
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<(onlyinclude|noinclude|includeonly)[^>]*>", "", text)
    text = re.sub(r"</(onlyinclude|noinclude|includeonly)>", "", text)
    text = strip_templates(text)
    text = re.sub(r"<[^>]+>", "", text)                       # stray html tags
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)   # [[a|b]] -> b
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)            # [[a]] -> a
    text = re.sub(r"\[https?://[^\]]*\]", "", text)            # external links
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"__[A-Z]+__", "", text)
    text = re.sub(r"^[*#:;]+\s*", "", text, flags=re.M)        # list markup
    text = re.sub(r"^=+\s*(.*?)\s*=+$", r"【\1】", text, flags=re.M)  # headings
    text = text.replace("-{-{", "-{").replace("}-}-", "}-")
    text = text.replace("-{", "").replace("}-", "")   # 繁简转换标记 -{字}- -> 字
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    out, blank = [], False
    for line in lines:
        if line:
            out.append(line)
            blank = False
        elif not blank and out:
            out.append("")
            blank = True
    return "\n".join(out).strip() + "\n"


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    provenance = []
    for slug, title, role in CHAPTERS:
        print(f"fetching {title} ...", flush=True)
        page = fetch_wikitext(title)
        wikitext = page["wikitext"]
        (RAW / f"{slug}.wikitext.txt").write_text(wikitext, encoding="utf-8")
        plain = clean(wikitext)
        (PROCESSED / f"{slug}.txt").write_text(plain, encoding="utf-8")
        record = {
            "slug": slug,
            "title": title,
            "role": role,
            "url": "https://zh.wikisource.org/wiki/" + urllib.parse.quote(title),
            "api": f"{API}?action=parse&page={urllib.parse.quote(title)}&prop=wikitext",
            "pageid": page.get("pageid"),
            "revid": page.get("revid"),
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "licence": "text: public domain (Western Han); transcription: CC BY-SA 4.0, zh.wikisource.org",
            "chars_wikitext": len(wikitext),
            "chars_plain": len(plain),
        }
        if page.get("revid"):
            record["permalink"] = f"https://zh.wikisource.org/w/index.php?oldid={page['revid']}"
        provenance.append(record)
        print(f"  {len(wikitext)} chars wikitext -> {len(plain)} chars plain, revid {page.get('revid')}")

    (RAW / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"provenance written to {RAW / 'provenance.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
