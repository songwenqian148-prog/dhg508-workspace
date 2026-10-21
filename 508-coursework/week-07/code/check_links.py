"""Check that every relative link in the week's Markdown files resolves.

Images, file paths and anchors are all checked: a link to a heading is tested
against the headings of the target file, a link to a file against the file
system. External http(s) links are reported but not fetched.

Usage:
    python code/check_links.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!`)\[[^\]]*\]\(([^)]+)\)")
CODE_SPAN = re.compile(r"`[^`]*`")


def slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text)


def headings(path: pathlib.Path) -> set[str]:
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            out.add(slug(line.lstrip("#")))
    return out


def main() -> int:
    files = sorted(p for p in ROOT.rglob("*.md") if "artifacts" not in p.parts)
    problems: list[str] = []
    checked = 0
    for md in files:
        text = md.read_text(encoding="utf-8")
        text = CODE_SPAN.sub("", text)
        for target in LINK.findall(text):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:")):
                checked += 1
                continue
            path_part, _, anchor = target.partition("#")
            path_part = path_part.strip()
            dest = (md.parent / path_part).resolve() if path_part else md
            checked += 1
            if not dest.exists():
                problems.append(f"{md.relative_to(ROOT)}: missing file -> {target}")
                continue
            if anchor:
                if dest.suffix == ".md" and anchor not in headings(dest):
                    problems.append(f"{md.relative_to(ROOT)}: missing anchor -> {target}")
                elif dest.suffix != ".md":
                    problems.append(f"{md.relative_to(ROOT)}: anchor on non-markdown -> {target}")

    print(f"checked {checked} links in {len(files)} markdown files")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("all relative links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
