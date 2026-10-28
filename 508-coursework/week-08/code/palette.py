"""Shared palette for the Week 8 pixel assets of *荆轲刺秦王*.

The set is deliberately muted: ink black to bone white, one red (Qin's
cinnabar), one green (jade).  ``make_pixel_assets.py`` imports every colour
from here, so the whole art set can be re-graded -- colder, darker, greyer --
by editing the hex strings below and re-running the generator.

Colours are plain hex strings in :data:`PALETTE`; the helpers turn them into
Pillow RGBA tuples and derive shades.  Nothing here is random, so the same
input always yields byte-identical output.

Material notes (Warring States / Qin, 227 BC): black lacquer with red trim for
Qin, undyed silk and hemp elsewhere, no later imperial yellows.
"""

from __future__ import annotations

#: The shared palette.  The first sixteen are the agreed base colours; the
#: last four are the human colours every sprite and portrait needs.
PALETTE: dict[str, str] = {
    "ink": "#241d18",
    "ash": "#4b4038",
    "slate": "#6b7380",
    "bone": "#ffe6c2",
    "silk": "#fff4e0",
    "blood": "#d8452f",
    "cinnabar": "#e35a3c",
    "earth": "#b07848",
    "clay": "#d39a63",
    "jade": "#6fb98a",
    "indigo": "#4a6bb0",
    "gold": "#f2c14e",
    "snow": "#fffaf2",
    "water": "#58a8c8",
    "dark_water": "#3d7f9c",
    "bronze": "#d8a94f",
    # Skin and hair: cartoon figures need warmer, flatter colour than the ink
    # version did.
    "skin": "#f6c9a0",
    "skin_shadow": "#dda276",
    "hair": "#30231c",
    "hair_grey": "#b9b1a5",
}

#: Every colour as an RGBA tuple, filled in on first use.
_RGBA: dict[str, tuple[int, int, int, int]] = {}


def hex_to_rgba(value: str) -> tuple[int, int, int, int]:
    """Turn ``"#rrggbb"`` (or ``"#rrggbbaa"``) into an RGBA tuple."""
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) == 6:
        text += "ff"
    if len(text) != 8:
        raise ValueError(f"not a hex colour: {value!r}")
    return (
        int(text[0:2], 16),
        int(text[2:4], 16),
        int(text[4:6], 16),
        int(text[6:8], 16),
    )


def colour(value: str | tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Resolve a palette name, a hex string, or an RGBA tuple to RGBA."""
    if isinstance(value, tuple):
        if len(value) == 3:
            return (value[0], value[1], value[2], 255)
        return value
    try:
        return _RGBA[value]
    except KeyError:
        if value in PALETTE:
            rgba = hex_to_rgba(PALETTE[value])
        else:
            rgba = hex_to_rgba(value)
        _RGBA[value] = rgba
        return rgba


def shade(value: str | tuple[int, int, int, int], factor: float) -> tuple[int, int, int, int]:
    """Multiply a colour's brightness by ``factor`` (clamped, alpha kept).

    ``factor`` below 1 darkens, above 1 lightens; 1.0 returns the colour.
    """
    r, g, b, a = colour(value)
    return (
        max(0, min(255, round(r * factor))),
        max(0, min(255, round(g * factor))),
        max(0, min(255, round(b * factor))),
        a,
    )


def mix(
    first: str | tuple[int, int, int, int],
    second: str | tuple[int, int, int, int],
    t: float,
) -> tuple[int, int, int, int]:
    """Blend ``first`` into ``second`` by ``t`` (0 -> first, 1 -> second)."""
    r1, g1, b1, a1 = colour(first)
    r2, g2, b2, a2 = colour(second)
    return (
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
        round(a1 + (a2 - a1) * t),
    )


def lighten(value: str | tuple[int, int, int, int], t: float) -> tuple[int, int, int, int]:
    """Mix a colour towards bone (never towards pure white)."""
    return mix(value, PALETTE["bone"], t)


def darken(value: str | tuple[int, int, int, int], t: float) -> tuple[int, int, int, int]:
    """Mix a colour towards ink."""
    return mix(value, PALETTE["ink"], t)


TRANSPARENT: tuple[int, int, int, int] = (0, 0, 0, 0)
