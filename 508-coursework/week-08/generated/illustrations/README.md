# Illustrations

Two plates passed review and are used in the game; four were generated from the
same brief and rejected. All six prompts, seeds, raw bytes and sha256 are in
`manifest.json`, and the rejected images are kept in
`artifacts/illustrations-rejected/` (git-ignored) rather than deleted.

| slug | verdict | why |
| --- | --- | --- |
| `yan_market` | **used** — title screen | a dusk market lane, stalls, baskets, awnings; monochrome ink wash; the one modern note is a thin cable, which at 50% opacity reads as a wire over the street |
| `yi_river` | **used** — historical ending | a cold river, reeds, a rutted road, empty; exactly the plate the Yi farewell needs, and empty is right for a scene the game itself stages |
| `map_unrolled` | rejected | a modern institutional corridor with electric pendant lamps |
| `pillar_chase` | rejected | a symmetric colonnade of white-panelled pillars; reads as a modern gallery, no red lacquer |
| `last_laugh` | rejected | Corinthian columns, European classical architecture |
| `epilogue_zhu` | rejected | an empty industrial hall with a glazed roof; no zither |

The endpoint (Pollinations, free tier) draws landscape and empty architecture
convincingly and draws this period's *interiors and people* not at all. The first
attempt — with figures in the prompt — was worse still: a woman in a bathrobe
standing in the Yi river. Both rounds of failures are described in
`research/tool_log.md` §4 and `research/prompts.md` §3.

Rebuild the used pair with:

```powershell
python code/make_illustrations.py --only yan_market,yi_river --force
```

The game reads them from `game/assets/art/`; if a plate is missing the ending
simply keeps the last map behind the text, which is why the build works without
them.
