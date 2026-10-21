"""Download the text sources used for the Week 7 research, keeping the raw
text in sources/processed/text/ so every claim in research/sources.md can be
checked against what the page actually said.

Usage:
    python code/fetch_text_sources.py
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "sources" / "processed" / "text"
UA = "DHG508-coursework/1.0 (educational use; student project)"

WIKI_API = "https://en.wikipedia.org/w/api.php"

SOURCES: dict[str, str] = {
    # name -> URL
    "wikipedia_ak47.txt": WIKI_API
    + "?"
    + urllib.parse.urlencode(
        {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "format": "json",
            "redirects": "1",
            "titles": "AK-47",
        }
    ),
    "modernfirearms_ak47.txt": "https://modernfirearms.net/en/assault-rifles/russia-assault-rifles/ak-47-akm-eng/",
}

TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
ANYTAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t\r\f\v]+")
NL_RE = re.compile(r"\n{3,}")


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read()
    charset = resp.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def html_to_text(markup: str) -> str:
    markup = TAG_RE.sub(" ", markup)
    markup = re.sub(r"<br\s*/?>", "\n", markup, flags=re.I)
    markup = re.sub(r"</(p|div|li|h[1-6]|tr)>", "\n", markup, flags=re.I)
    text = ANYTAG_RE.sub("", markup)
    text = html.unescape(text)
    text = WS_RE.sub(" ", text)
    text = NL_RE.sub("\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, url in SOURCES.items():
        dest = OUTDIR / name
        try:
            body = get(url)
            if "wikipedia.org/w/api.php" in url:
                data = json.loads(body)
                pages = data["query"]["pages"]
                text = next(iter(pages.values())).get("extract", "")
            else:
                text = html_to_text(body)
            if len(text) < 500:
                raise SystemExit(f"{name}: suspiciously short extract ({len(text)} chars)")
            dest.write_text(f"SOURCE: {url}\n\n{text}", encoding="utf-8")
            print(f"OK    {name}: {len(text):,} chars")
        except Exception as exc:  # noqa: BLE001
            failed.append((name, url, str(exc)))
            print(f"FAIL  {name}: {exc}", file=sys.stderr)
        time.sleep(1.0)

    if failed:
        print("\nFailures:")
        for name, url, err in failed:
            print(f"  {name} <- {url}: {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
