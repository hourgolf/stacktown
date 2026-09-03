# The wooden city's HUD — a look declaration

**Owner, 2026-09-02:** *"a clean minimalist overlay that can be placed along
the top or the bottom of the screen to maximize screen space and not distract
from the gameboard too much."* Fonts they named: **Six Caps**, **Erica One**,
**Space Mono Bold**.

This revision replaces the paper-card proposal. The sampled palette and the
excluded-with-reasons list survive unchanged; the container and the fonts are
new.

Two halves, because the engine splits them:

- **OWNER PLACES** — anchors, margins, stacking, containers. Canvas slot
  properties, designer-only, unreachable from code.
- **CODE STYLES** — font, size, colour. `SetFont` / `SetFontSize` /
  `SetColorAndOpacity` are reachable, so the beta lane sets these at
  BeginPlay and you never touch them by hand.

Widget names are fixed: `MoneyText`, `DemandText`, `SelectedNameText`,
`SelectedStateText`, `SelectedPriceText`, `BuyPromptText`.

---

## 1. TOP, not bottom — and the frame says so

**Put the bar along the TOP edge.** This is measured off the actual first-boot
play framing (`study_pose.json` — pitch −25, yaw 70, reach 19000), not
chosen by habit:

| band of the frame | sd | what is actually there |
|---|---|---|
| top 0–12% | **5.2** | **empty ground — the studio backdrop above the board** |
| 12–24% | 44.7 | buildings |
| 24–76% | 31–52 | the city, busiest region |
| 76–100% | 20–25 | **board — the near plate, closest and largest** |

The boom tilts down at 25°, so the board's far edge stops about an eighth of
the way down and everything above it is empty backdrop. **The top strip is
already dead space; the bottom strip is the player's own city at its nearest
and biggest.** A bottom bar would cover the best-looking part of the board to
sit in front of the worst-looking part of the screen.

**One caveat, stated because it is real:** that empty band is measured at the
zoomed-OUT stop. At the close stops (reach 1350 / 800) the board fills more of
the frame and the top is no longer guaranteed empty. So the bar stays **thin**
— it must be affordable at every zoom, not just the one it was measured at.

**What the HUD is now:** a single thin strip, full width, dark, with the board
running under it. Not a panel, not a card, not a plaque. Persistent facts sit
left; the selection sits right and is **absent entirely until something is
selected**.

## 2. Palette — sampled from the board, not chosen

Measured off the render (`Saved/DirectionB/wear/species/age_00.png`):

| role | hex | where it comes from |
|---|---|---|
| bar | `#2A2A2E` at 88% | one step under the studio ground `#3A3A3E` |
| ink | `#E8E0D4` | the road inlay `#DFD6C9`, lifted to read on the dark bar |
| ink, secondary | `#9A9187` | labels and units — deliberately quieter |
| accent, warm | `#C08A4E` | oak `#8C6036`, lifted for the dark ground |

The bar is a shade *under* the studio ground so it reads as a separate plane
rather than a patch of backdrop. At 88% the board passes faintly beneath it.

**State colours** for `SelectedStateText`, following D16's warm-to-cold health
axis so the HUD says the same thing the timber says — all lifted for the dark
bar:

| state | hex |
|---|---|
| refinished | `#D8A868` |
| maintained | `#C08A4E` |
| settled | `#9A9187` |
| neglected | `#8A8070` |
| rotting | `#A8AAA8` (cold — the grey) |
| burnt | `#6A6560` |

## 3. Fonts — Tomorrow for words, Space Mono Bold for numbers

Owner chose **Tomorrow** over Six Caps for labels, 2026-09-02, after a side by
side. Two families, and the division between them is a rule rather than a
taste: **anything made of words is Tomorrow; anything that is a live number is
Space Mono Bold.**

All are SIL Open Font License from Google Fonts — commercial use,
redistribution and embedding all permitted, verified at each family's OFL.

**Tomorrow** (Regular / Medium / SemiBold) for every text label. Nine weights,
real lowercase, a squarish geometric skeleton that suits a board of
right-angled timber blocks. It goes wherever the HUD goes next — tooltip,
menu, title card — which Six Caps could not, being a single-weight condensed
caps face. That reach is what decided it.

**Space Mono Bold** for `MoneyText` and `SelectedPriceText`, and this is
NOT a stylistic preference — it is read out of the font files:

| font | digit advance widths |
|---|---|
| SpaceMono-Bold | **TABULAR — all ten identical** |
| Tomorrow-Medium | proportional — ten distinct, 431 to 681 units |
| Tomorrow-Bold | proportional — ten distinct, 478 to 730 units |
| SixCaps | proportional — 171 to 234 |
| EricaOne | proportional — 402 to 729 |

Tomorrow's `1` is **431 units against its `8` at 681** — a 58% spread. At
30 px that is about 7.5 px of movement per digit that changes, and a money
value ticking over several digits would visibly shuffle sideways under the
label beside it. Space Mono's ten digits are byte-identical in width, so the
number changes and nothing moves. Tomorrow carries the HUD everywhere words
appear; it does not carry the money.

**Erica One has no HUD role, and that is not a rejection of the choice.** It
is a heavy poster display face: in a thin bar it would dominate the strip and
fight the board, which is the one thing the HUD was asked not to do, and its
digits are proportional too. Its real home is the **game's wordmark — a title
card or main-menu lockup**, where being loud is the job and nothing has to
share the space. It stays in the repo for that. Worth saying plainly that the
one deliberately-loud face in a set of three is a good instinct to have had;
it just belongs on the screen before the board, not on top of it.

Not used in the HUD, kept as sources: `SixCaps.ttf` (the face Tomorrow
replaced), `SpaceMono-Regular.ttf`, `EricaOne-Regular.ttf`, and the six
Tomorrow weights the bar does not call for.

**Font assets — IMPORTED 2026-09-02, verified binding:**

    /Game/Stacktown/UI/Fonts/F_Tomorrow_Regular
    /Game/Stacktown/UI/Fonts/F_Tomorrow_Medium
    /Game/Stacktown/UI/Fonts/F_Tomorrow_SemiBold
    /Game/Stacktown/UI/Fonts/F_SpaceMono_Bold

These are **FontFace** assets, and that is the right type: `SlateFontInfo`
takes a FontFace directly — `SlateFontInfo(font_object=<FontFace>, size=N)`
binds and reads back — so no `UFont` wrapper is needed. A first attempt built
one anyway and died on `unreal.TypefaceEntry`, which Python does not expose;
the wrapper was never required. `Content/Python/import_fonts.py` rebuilds all
four in one command.

**`SlateFontInfo` also carries `letter_spacing`**, so the +0.03em on the
Tomorrow labels is a code value the beta lane sets with everything else,
rather than something to type into the designer.

Six Caps, Erica One and `SpaceMono-Regular` are committed as sources and
**deliberately not imported** — importing every downloaded file would leave
unused Font assets in the content browser looking like part of the HUD.

## 4. CODE STYLES — the beta lane sets these

Sizes are for a 1080p-tall viewport and scale with it.

| widget | font | size | colour |
|---|---|---|---|
| `MoneyText` | Space Mono Bold | 30 | `#E8E0D4` |
| `DemandText` | Tomorrow Medium | 20 | `#9A9187` |
| `SelectedNameText` | Tomorrow SemiBold | 22 | `#E8E0D4` |
| `SelectedStateText` | Tomorrow Medium | 18 | *state colour above* |
| `SelectedPriceText` | Space Mono Bold | 26 | `#C08A4E` |
| `BuyPromptText` | Tomorrow Regular | 16 | `#9A9187` |

`DemandText` and `SelectedStateText` stay **uppercase**, set in the string
rather than by the font — Tomorrow has lowercase and the labels choose not to
use it, which is a decision the copy can revisit without changing a font.
Letter-spacing **+0.03em** on the Tomorrow labels; the numbers take none.

## 5. CONSTRUCTION ORDER — the runtime build

Rewritten 2026-09-02. This half was designer instructions until the widget
root turned out unreachable to the tooling and the bar became a runtime build.
**The beta lane's code is now the spec**, so the numbers are given as slot
values rather than as a paragraph somebody has to translate into slot values
by eye — that transcription step is where a layout silently stops matching its
declaration.

**THE ROOT IS UNRESOLVED AND THIS IS WRITTEN ROOT-AGNOSTIC.** The designer's
panel cannot be referenced from the DSL, `GetWidgetFromName` is not placeable
either, and `GameViewportSubsystem.AddWidget` is being probed — which would
make the bar hostless. Everything below says **`<ROOT>`** and holds for
whichever lands. Only step 1's slot type changes with it: a Canvas root takes
the anchor/offset block; a viewport-added root takes its own alignment call
and ignores that block.

### Build order — parents before children, every time

    1  Border            "HudBar"        -> attach to <ROOT>
    2  HorizontalBox     "HudRow"        -> child of HudBar
    3  HorizontalBox     "StatusCluster" -> child of HudRow
    4  TextBlock         MoneyText       -> child of StatusCluster
    5  TextBlock         DemandText      -> child of StatusCluster
    6  Spacer            "HudSpacer"     -> child of HudRow
    7  HorizontalBox     "SelectCluster" -> child of HudRow
    8  TextBlock         SelectedNameText   -> child of SelectCluster
    9  TextBlock         SelectedStateText  -> child of SelectCluster
    10 TextBlock         SelectedPriceText  -> child of SelectCluster
    11 TextBlock         BuyPromptText      -> child of SelectCluster

A Border takes exactly **one** child, which is why HudRow exists — adding the
clusters straight to the Border silently keeps only the last one.

### Slot values

**1 · HudBar in `<ROOT>`** — a Canvas slot, if the root is a Canvas:

    Anchors        Min (0.0, 0.0)   Max (1.0, 0.0)     stretched along the top
    Offsets        Left 0   Top 0   Right 0   Bottom 76
    Alignment      (0.0, 0.0)
    AutoSize       false

With those anchors, `Offsets.Bottom` **is the bar's height**, not a margin —
Left and Right are insets from the screen edges and Top is the drop from the
anchor line. If the root is the viewport instead, skip this block and place it
with the subsystem's own top-stretched alignment; the height moves to the
Border's own size.

**HudBar itself:**

    Brush colour   #2A2A2E at alpha 0.88
    Padding        Left 28   Right 28   Top 0   Bottom 0

*On that colour:* if it renders far darker than the swatch, the value is being
taken as linear rather than sRGB. `#2A2A2E` is `(0.165, 0.165, 0.180)` as sRGB
bytes over 255 and about `(0.022, 0.022, 0.027)` once converted — construct it
from an sRGB hex rather than typing floats, and check it against section 2's
swatch rather than against the number.

**2 · HudRow in HudBar** — `HorizontalAlignment Fill`, `VerticalAlignment Fill`.
Filling vertically is what lets every text block centre itself in the bar's
height instead of sitting on its top edge.

**3 · StatusCluster in HudRow**

    Size           Auto
    VAlign         Center

**4 · MoneyText** — padding all zero.
**5 · DemandText** — `Padding Left 24`. That is the 24 px gap; it lives on the
second item, never as a margin on both.

**6 · HudSpacer in HudRow** — `Size Fill (1.0)`. This is the whole reason the
selection cluster stays pinned to the right edge at any window width; without
it the right cluster butts against the left one and the bar looks broken at
wide aspect ratios only, which is the kind of bug that ships.

**7 · SelectCluster in HudRow**

    Size           Auto
    VAlign         Center
    Visibility     Collapsed          <-- the default, set at construction

**8–10 ·** `SelectedNameText` padding 0; `SelectedStateText` and
`SelectedPriceText` each `Padding Left 20`.
**11 · BuyPromptText** — `Padding Left 28`. The wider gap is deliberate: a
prompt is an instruction, not another fact, and the extra air is what says so.

**Every TextBlock:** `VerticalAlignment Center`, and left-aligned text. With
two type families at six different sizes, top-aligning makes the baselines
disagree and the bar reads as assembled rather than designed.

### What the beta lane owns at runtime

- **Show and hide `SelectCluster`** on selection — `Collapsed` to `Visible`,
  never `Hidden`. Hidden still occupies its layout space, so the spacer would
  keep the gap open and the bar would look like it had lost something.
- **Fonts, sizes and colours** from section 4, set at BeginPlay from the
  imported FontFace assets.
- **`SelectedStateText`'s colour** per state, from section 2's table.

### Not to be added

No drop shadow on the bar, no rounded corners, no outline, and no second
background behind `SelectCluster`. One bar, one plane. The 88% alpha and the
value gap against the board already separate it; anything more is the UI tell
this direction has spent months removing.

## 6. What this deliberately leaves out

- **No icons.** A coin glyph beside Money is the fastest way to make this look
  like a mobile game. The number is the money.
- **No progress bars or meters.** D16 put building state into the timber —
  cold patches in a warm field, legible at board range with no UI at all. A bar
  would say it twice, and worse.
- **No count-up animation on value change.** A number that ticks draws the eye
  off the board. Easy to add later if the economy feels dead without it; hard
  to remove once players expect it.
- **No background behind the selection cluster.** One bar, one plane. A second
  panel inside the bar is how a minimal HUD stops being minimal.
