"""Rewrite the README folder map with clean characters.

The tree used box-drawing characters (U+2500 range); a PowerShell
`Set-Content` round-trip turned them into mojibake. This puts a plain-ASCII tree
back, which cannot be mangled by an encoding round-trip.

Usage: python code/fix_readme_tree.py
"""

from __future__ import annotations

import pathlib
import re

README = pathlib.Path(r"G:\workspeace\dhg508-workspace\508-coursework\week-07\README.md")

TREE = """```text
week-07/
|-- instructions.md            the brief, untouched
|-- README.md                  this index
|-- questions.md               what is still unresolved
|-- sources/
|   |-- raw/                   the 21 downloaded images + provenance.json + the two download scripts
|   `-- processed/text/        the two text sources as plain text, URL on line 1
|-- research/
|   |-- object_and_history.md  the object, the stage, the production reversal, the feature table
|   |-- sources.md             S1-S3 text sources with quotes, plus the image table with licences
|   |-- prompts.md             every prompt, verbatim, with seeds and outcomes
|   |-- comparison.md          the step 2 answers
|   |-- model_notes.md         all three 3D routes, what each one does and does not represent
|   `-- tool_log.md            tools, AI vs checked, costs, difficulties
|-- generated/
|   |-- comparison_sheet.png   the step 2 sheet for class
|   |-- control_check.png      control vs treatment at matched seeds
|   |-- model_route_comparison.png  Blender script vs Hunyuan3D image-to-3D
|   |-- renders/               model renders, web size (full size in artifacts/)
|   |-- turntable.mp4          one full rotation of the hand-built model
|   |-- final/                 the two images used, plus alternates, and their manifests
|   |-- a_words_only/          round 1 baseline attempts
|   `-- b_from_sources/        round 1 researched attempt (failed, kept as evidence)
|-- model/
|   |-- ak47_type2.blend       the editable Blender scene
|   |-- ak47_type2.glb         glTF export of the hand-built model
|   |-- ak47_hunyuan3d.glb     the image-to-3D mesh, scaled to 870 mm
|   `-- ak47_hunyuan3d.json    its measurements (triangles, shells, watertight)
|-- artifacts/                 git-ignored: Blender, full-resolution stills, frames, service runs
`-- code/                      the scripts that produced everything above
```"""


def main() -> int:
    text = README.read_text(encoding="utf-8")
    start = text.index("```text")
    end = text.index("```", start + 7) + 3
    fixed = text[:start] + TREE + text[end:]
    README.write_text(fixed, encoding="utf-8")

    leftovers = re.findall(r"[\u4e00-\u9fff\ufffd]", fixed)
    print(f"rewrote folder map; suspicious characters left in README: {len(leftovers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
