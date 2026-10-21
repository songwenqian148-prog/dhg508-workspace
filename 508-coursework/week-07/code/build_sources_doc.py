"""Write research/sources.md from the fetched Commons metadata plus the text
sources actually read for this assignment.

The point of generating the image table instead of typing it: every Commons
file page, author and licence string comes straight from provenance.json, so
the attribution cannot drift from what was downloaded.

Usage: python code/build_sources_doc.py
"""

from __future__ import annotations

import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "sources" / "raw" / "provenance.json"
OUT = ROOT / "research" / "sources.md"
ACCESSED = "20 October 2026"

# What each downloaded picture was actually used for.
USED_FOR = {
    "01_ak47_general_view.png": "side-view proportions of the Type 2 (this is the picture I measured: 870 mm = 1220 px)",
    "02_ak47_type1_type2_comparison.png": "Type 1 vs Type 2 receivers, stocks, grips and handguards side by side",
    "03_ak47_type3_aks47_comparison.png": "Type 3 receiver and the AKS-47 folding stock, to see what the Type 3 changed",
    "04_ak47_type1_receiver_detail.jpg": "what a stamped Type 1 receiver and its rivets look like",
    "05_ak47_trigger_group_detail.jpg": "trigger group parts (fire control), not a Type 2-specific feature",
    "06_ak47_royal_armouries_detail.jpg": "a museum AK dated 1953 (Royal Armouries PR.5428), i.e. inside the Type 2 production run",
    "07_ak47_cross_section_diagram.jpg": "cut-away of the gas system and bolt group for the 3D layout",
    "08_ak47_disassembled_parts.jpg": "field-strip order: magazine, cover, spring, bolt carrier",
    "09_ak47_disassembly_view.jpg": "second view of the same disassembled set",
    "10_ak47_field_stripped.jpg": "field-stripped layout on a modern clone",
    "11_ak47_converted_parts.jpg": "converted (civilian) Izhmash parts, useful only for furniture shapes",
    "12_ak47_repair_disassembly.jpg": "parts layout during repair",
    "14_ak47_athens_museum_3quarter_view.jpg": "three-quarter view of a real AK for the 3D camera angles",
    "15_ak47_type2_right_side_view.jpg": "clearest Type 2 side view; the reference for stock, grip, magazine and receiver proportions",
    "16_ak47_bolt_carrier_gas_piston.jpg": "bolt carrier and long-stroke gas piston",
    "17_ak47_rear_sight_detail.jpg": "tangent rear sight and its graduation",
    "18_ak47_type1_magazine.png": "slab-sided early steel magazine, which the Type 2 also used",
    "19_ak47_aks_folding_stock.jpg": "folding stock variant, not modelled (fixed-stock rifle chosen)",
    "20_akm_muzzle_detail.jpg": "AKM slanted muzzle brake: the thing that is *not* on a Type 2",
    "AK-47_assault_rifle.jpg": "same Commons file as the .webp below, mislabelled .jpg on disk",
    "AK-47_type_II_noBG.png.webp": "Type 2 cut-out used as the header image on Wikipedia, and as the Hunyuan3D input",
}

TEXT_SOURCES = """\
## 1. Text sources

Both were read in full and saved as plain text under
`sources/processed/text/`, so the quotes below can be checked against the copy
that was actually used.

### S1 - Wikipedia, "AK-47"

- URL: <https://en.wikipedia.org/wiki/AK-47>
- Accessed: {accessed}
- Saved copy: `sources/processed/text/wikipedia_ak47.txt`
- Read for: the production sequence and the published figures.

Quotes used (verbatim, with straight quotes for the typographic ones):

> The first production models had stamped sheet metal receivers with a milled
> trunnion and butt stock insert and a stamped body. Difficulties were
> encountered in welding the guide and ejector rails, causing high rejection
> rates. Instead of halting production, a heavy machined receiver was
> substituted for the sheet metal receiver. Even though production of these
> milled rifles started in 1951, they were officially referred to as AK-49 ...

> Issue of 1948/49: Type 1: The very earliest models, stamped sheet metal
> receivers, are now very rare.

> Issue of 1951: Type 2: Has a milled receiver. The barrel and chamber are
> chrome-plated to resist corrosion.

> Issue of 1954/55: Type 3: Lightened, milled receiver variant. Rifle weight is
> 3.47 kg (7.7 lb).

> The AK fires the 7.62×39mm cartridge with a muzzle velocity of 715 m/s.

> The early slab-sided steel AK-47 30-round detachable box magazines had 1 mm
> (0.039 in) sheet-metal bodies and weighed 430 g (0.95 lb) empty.

### S2 - Maxim Popenker, "Kalashnikov AK-47, AK assault rifle (USSR)", Modern Firearms

- URL: <https://modernfirearms.net/en/assault-rifles/russia-assault-rifles/ak-47-akm-eng/>
- Accessed: {accessed}
- Saved copy: `sources/processed/text/modernfirearms_ak47.txt`
- Read for: the Type 1 / Type 2 / Type 3 descriptions and the specification
  table. This is the source that gives the *visible* Type 2 features, which is
  what the image prompts and the 3D model are built from.

Quotes used (verbatim, spelling as published):

> The first mass-produced Avtomat Kalashnikova AK featured a stamped steel
> receiver ... However, by the end of 1949, it became clear that stamped
> receivers with welded bolt rails and pinned trunnions is too complex and
> results in an excessive rate of rejected receivers.

> The "AK Type 2" (produced 1951 – 1955) introduced several important changes to
> the basic design. First and most important was the new receiver, machined from
> a single block of steel, which dispensed with separate forward and rearward
> trunnions of the previous design. Other changes include a new, single-piece
> pistol grip made from wood, which was attached to a separate base below the
> receiver using a single vertical bolt. ... Wooden shoulder stock now also has
> its separate mounting socket, made from steel and pinned to the rear end of
> the receiver. Less visible changes involved improved springs, made from
> three-strand wire, stronger top cover, changes in gas piston tube, barrel, and
> bolt carrier.

> The "AK type 3" (produced 1955 – 1959) had its barrel, stock, receiver, and its
> top cover, and some trigger parts made lighter. ... The forward sling attachment
> loop was moved from the forward end of the lower handguard to the gas block,
> and a new knife-bayonet was adopted along with the gun.

> Specifications for Kalashnikov AK, pattern of 1949: Overall length 870 mm;
> Barrel length 415 mm; Weight with empty magazine 4,3 kg; Magazine capacity 30
> rounds; Rate of fire 600 rounds/minute.

> There was no provision for a bayonet. *(of the 1949 pattern, in the design
> description)*

### S3 - Royal Armouries, AK dated 1953 (PR.5428)

- URL: <https://www.flickr.com/photos/royalarmouries/53528474954/>
- Accessed: {accessed}
- Local copy: `sources/raw/06_ak47_royal_armouries_detail.jpg`
- Read for: one dated object inside the Type 2 production window. The
  Royal Armouries caption gives the date as 1953 and the accession number
  PR.5428, which is consistent with a Type 2 rifle rather than a 1949 Type 1.

**Why this matters for the argument:** the story is not "the AK-47 was designed
in 1947". It is that the *first* production rifles (Type 1, 1948/49) had stamped
receivers that could not be made reliably, so production switched to a machined
receiver (Type 2, 1951-1955), which was then lightened (Type 3, 1955-1959), and
only in 1959 did a stamped receiver come back as the AKM. A 1953 museum object
sits in the middle of that reversal. Sources S1 and S2 both state the reversal;
S3 gives a dated object from the middle of it.
"""


def clean_author(raw: str) -> str:
    """Strip the HTML that Commons puts in the Artist field, then unescape it.

    The field is HTML-escaped markup (``&lt;a href=...&gt;``), so it has to be
    unescaped before the tags can be removed, and unescaped again afterwards.
    """
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip(" ,;")
    return text or "not stated on the file page"


def clean_date(raw: str) -> str:
    """Commons dates are free text ('Taken on 12 June 2011'); keep a date or a year."""
    raw = (raw or "").strip()
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    if match:
        return match.group(0)
    match = re.search(r"\b(1[89]\d{2}|20\d{2})\b", raw)
    return match.group(0) if match else "-"


def main() -> int:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = []
    for name in sorted(provenance):
        info = provenance[name]
        author = clean_author(info.get("author", "")).replace("|", "/")
        licence = info.get("licence", "") or "see file page"
        date = clean_date(info.get("date", ""))
        rows.append(
            "| `{file}` | [{title}]({url}) | {author} | {licence} | {date} | {used} |".format(
                file=name,
                title=info["commons_title"].removeprefix("File:").replace("|", "/"),
                url=info["descriptionurl"],
                author=author,
                licence=licence,
                date=date,
                used=USED_FOR.get(name, ""),
            )
        )

    header = """\
# Sources

Everything used for this week, with where it came from and what it was used
for. Images were downloaded with the two scripts the student had already run
(`sources/raw/download_ak47_images*.ps1`); the Commons metadata below was
fetched by `code/fetch_commons_metadata.py` and is stored in
`sources/raw/provenance.json`.

{text}

## 2. Image sources (Wikimedia Commons)

All local files are in `sources/raw/`. Titles and links are the Commons file
pages; authors and licences are what those pages state, fetched on
{accessed}.

| Local file | Commons file page | Author | Licence | Date | Used for |
| --- | --- | --- | --- | --- | --- |
{rows}

## 3. Licence notes

- Public-domain files: no attribution required, but credited here anyway.
- CC BY 2.0 / 3.0 / 4.0 and CC BY-SA 2.0 / 3.0 / 4.0 files: the author and
  licence must travel with any reuse. This repository keeps the images for
  coursework analysis; the two generated images in `generated/` are new outputs
  and do not contain these photographs.
- `generated/` contains **no** downloaded photograph: no image-to-image step was
  used for the two comparison images, so that comparison is text-to-image against
  text-to-image. The image-to-3D route (Hunyuan3D) does use one of the Commons
  photographs as input; its output is a mesh, credited here and in
  `research/model_notes.md`.
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        header.format(text=TEXT_SOURCES.format(accessed=ACCESSED),
                      rows="\n".join(rows), accessed=ACCESSED),
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({len(rows)} image rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
