"""Bundle the whole game into one HTML file that opens by double-click.

    python code/build_single_file.py

The result, 图穷.html, has the CSS, every script and every image inlined as data
URIs, and runs from file:// because it does not use ES modules at all: the module
files are concatenated in dependency order and their import/export lines removed.

AI calls still need the local server (they go to /api/talk); with no server the
game falls back to the scripted lines in story.js, exactly as it does when the
API key is missing.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
GAME = HERE / "game"
OUT = HERE / "图穷.html"

# dependency order: a module only uses things defined before it
MODULES = ["battle.js", "story.js", "maps.js", "ai.js", "engine.js", "main.js"]

IMAGE_DIRS = [
    # pixel art first: it is what the game shows now
    ("assets/portraits/", GAME / "assets" / "portraits"),
    ("assets/sprites/", GAME / "assets" / "sprites"),
    ("assets/pixel/scenes/", GAME / "assets" / "pixel" / "scenes"),
    # the older painted art stays resolvable in case anything points at it
    ("assets/cartoon/portraits/", GAME / "assets" / "cartoon" / "portraits"),
    ("assets/cartoon/scenes/", GAME / "assets" / "cartoon" / "scenes"),
]


def strip_module_syntax(src: str) -> str:
    src = re.sub(r"^\s*import[^;]*;\s*$", "", src, flags=re.M)
    src = re.sub(r"^\s*export\s+(const|let|class|function)\b", r"\1", src, flags=re.M)
    src = re.sub(r"^\s*export\s*\{[^}]*\};?\s*$", "", src, flags=re.M)
    return src


def data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def main() -> int:
    html = (GAME / "index.html").read_text(encoding="utf-8")
    css = (GAME / "style.css").read_text(encoding="utf-8")

    script = "\n\n".join(
        f"/* ---- {name} ---- */\n" + strip_module_syntax((GAME / "js" / name).read_text(encoding="utf-8"))
        for name in MODULES
    )

    # images -> data URIs. The JS builds paths with template literals, so rewrite
    # those expressions to a lookup function instead of matching literal paths.
    images: dict[str, str] = {}
    for prefix, folder in IMAGE_DIRS:
        kind = prefix.strip("/").split("/")[-1]
        for path in sorted(folder.glob("*")):
            if path.suffix.lower() in (".png", ".jpg"):
                images[f"{kind}/{path.name}"] = data_uri(path)

    lookup = (
        "const __IMG = " + __import__("json").dumps(images) + ";\n"
        "function IMG(kind, name) {\n"
        "  return __IMG[kind + '/' + name + '.png'] || __IMG[kind + '/' + name + '.jpg'] || '';\n"
        "}\n"
    )
    script = lookup + script

    script = re.sub(r"`assets/cartoon/portraits/\$\{([^}]+)\}\.png`", r"IMG('portraits', \1)", script)
    script = re.sub(r"`assets/cartoon/scenes/\$\{([^}]+)\}\.png`", r"IMG('scenes', \1)", script)
    script = re.sub(r"`assets/legacy/portraits_hd/\$\{([^}]+)\}\.jpg`", r"IMG('portraits', \1)", script)
    script = re.sub(r"`assets/portraits/\$\{([^}]+)\}\.png`", r"IMG('portraits', \1)", script)
    script = re.sub(r"`assets/sprites/\$\{([^}]+)\}\.png`", r"IMG('sprites', \1)", script)
    script = re.sub(r"`assets/pixel/scenes/\$\{([^}]+)\}\.png`", r"IMG('scenes', \1)", script)
    script = script.replace("'assets/pixel/scenes/xianyang_hall.png'", "IMG('scenes', 'xianyang_hall')")

    for ref, uri in images.items():
        script = script.replace(ref, uri)
        html = html.replace(ref, uri)

    # inline the stylesheet
    html = re.sub(r'<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>", html)

    # the canvas draws the title art in the served build; in the single file the
    # image is inlined, so put it straight on the title screen's background
    art = images.get("scenes/yan_market.png")
    if art:
        html = html.replace(
            "</style>",
            "#titlescreen{background-image:linear-gradient(rgba(10,9,8,.58),rgba(10,9,8,.88)),"
            f'url("{art}");background-size:cover;background-position:center;}}\n</style>',
        )

    # replace the file:// warning + module loader with a plain inline script
    html = re.sub(
        r"<script>\s*// If anything throws.*?</script>",
        f"<script>\n{script}\n</script>",
        html,
        flags=re.S,
    )

    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.name}: {OUT.stat().st_size / 1024:.0f} KB, {len(images)} images inlined")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
