# Google Fonts sources — provenance

Downloaded 2026-09-02 at the owner's explicit word, for the wooden city's
HUD (`Docs/DIRECTION_B_HUD.md`). The owner named all three families
themselves.

| file | family | bytes | license | source |
|---|---|---|---|---|
| SixCaps.ttf | Six Caps | 46,388 | SIL OFL 1.1 | https://fonts.google.com/specimen/Six+Caps |
| EricaOne-Regular.ttf | Erica One | 26,244 | SIL OFL 1.1 | https://fonts.google.com/specimen/Erica+One |
| SpaceMono-Bold.ttf | Space Mono | 98,232 | SIL OFL 1.1 | https://fonts.google.com/specimen/Space+Mono |
| SpaceMono-Regular.ttf | Space Mono | 99,356 | SIL OFL 1.1 | https://fonts.google.com/specimen/Space+Mono |
| Tomorrow-*.ttf (9) | Tomorrow | 531,180 | SIL OFL 1.1 | https://fonts.google.com/specimen/Tomorrow |

**Tomorrow** was added at the owner's word in the same session. The family
ships 18 faces; the **nine upright weights** are here (Thin through Black) and
the nine italics are not — a HUD does not use italics, and nine unused files
is clutter rather than caution. One command fetches them if that changes.

Fetched from the canonical `google/fonts` repository (`ofl/<family>/`), which
is what the specimen pages serve. `OFL-sixcaps.txt`, `OFL-ericaone.txt` and
`OFL-spacemono.txt` are each family's licence file, downloaded alongside and
kept here — every one verified to read **SIL OPEN FONT LICENSE Version 1.1**,
which permits commercial use, redistribution and embedding in a game.

All four verified as real TrueType data with `file`, not assumed from the
extension.

**Tomorrow is a candidate to replace Six Caps for labels**, and the owner
naming it late is worth taking seriously rather than filing. Six Caps is
extremely condensed and caps-only — excellent in a thin bar, fragile
everywhere else, and it commits the HUD to all-caps labels. Tomorrow is a
squarish geometric sans with nine weights, so it can carry labels AND the
prompt in one family, in mixed case, and it holds up if the HUD ever grows
past one strip. The trade is width: Tomorrow needs roughly twice the
horizontal space Six Caps does for the same string, which matters in a bar
whose whole argument is staying thin. **This is a look decision and belongs
to the owner's eye, not to a measurement** — both are downloaded, and a side
by side in the designer settles it in a minute.

**The filename was not guessable and is worth recording**: Six Caps ships as
`SixCaps.ttf`, not `SixCaps-Regular.ttf` — the pattern every other family
here follows. The first fetch 404'd; the fix was to list the directory
through the GitHub API rather than guess a second time.

## Where they are used

Per `Docs/DIRECTION_B_HUD.md`:

- **Space Mono Bold** — every live number (`MoneyText`, `SelectedPriceText`).
  Monospaced digits so a value that changes while you watch it does not
  shuffle sideways.
- **Six Caps** — labels (`DemandText`, `SelectedNameText`,
  `SelectedStateText`). Condensed caps stay legible at a large size while
  taking almost no width, which is what a thin full-width bar wants.
- **Space Mono Regular** — `BuyPromptText`, an instruction rather than a
  label.
- **Erica One** — **not used in the HUD.** A heavy poster face would dominate
  a minimal strip and fight the board for attention. Downloaded because the
  owner named it and it is the right face for a title card or main-menu
  wordmark later. Carried deliberately, not left over.

## Not yet imported

These are SOURCE files. The Font assets at
`/Game/Stacktown/UI/Fonts/F_SixCaps`, `F_SpaceMono_Bold` and
`F_SpaceMono_Regular` do not exist yet — importing is editor work and rides a
granted window.
