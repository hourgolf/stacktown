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

## 3. Fonts

Two families, three faces. All three are **SIL Open Font License** from Google
Fonts — free for commercial use, redistributable, embeddable.

**`Space Mono Bold` for every live number** — `MoneyText`, `SelectedPriceText`.
Monospace means the digits are all one width, so a number that changes while
you watch it does not shuffle sideways. This was the one polish concern flagged
in the first draft and the owner's instinct landed exactly on it.

**`Six Caps` for labels** — `DemandText`, `SelectedNameText`,
`SelectedStateText`. It is extremely condensed and caps-only, which is precisely
what a thin full-width bar wants: it stays legible at a large size while taking
almost no width, and it is light enough not to compete with the timber.

**`Space Mono Regular` for `BuyPromptText`.** The prompt is an instruction that
has to read instantly; Six Caps is a labelling face and a condensed caps
sentence is slower to read than it looks.

**Erica One: not recommended here, and the instinct is not wrong.** It is a
heavy poster display face — it would dominate a minimal strip and fight the
board for attention, which is the one thing the owner asked the HUD not to do.
Where it *would* be right is a title card or main-menu wordmark, where being
loud is the job. Worth keeping for that.

**Sourcing** (editor work — happens in a granted window, not before):
download each family from `fonts.google.com`, confirm the OFL on the page,
commit the `.ttf` beside the existing texture sources, then import as Font
assets at these paths so the beta lane's `SetFont` calls have targets:

    /Game/Stacktown/UI/Fonts/F_SixCaps
    /Game/Stacktown/UI/Fonts/F_SpaceMono_Bold
    /Game/Stacktown/UI/Fonts/F_SpaceMono_Regular

## 4. CODE STYLES — the beta lane sets these

Sizes are for a 1080p-tall viewport and scale with it.

| widget | font | size | colour |
|---|---|---|---|
| `MoneyText` | Space Mono Bold | 30 | `#E8E0D4` |
| `DemandText` | Six Caps | 34 | `#9A9187` |
| `SelectedNameText` | Six Caps | 38 | `#E8E0D4` |
| `SelectedStateText` | Six Caps | 30 | *state colour above* |
| `SelectedPriceText` | Space Mono Bold | 26 | `#C08A4E` |
| `BuyPromptText` | Space Mono Regular | 17 | `#9A9187` |

Six Caps sizes look large next to the Space Mono ones and are not a mistake —
the face is about a third the width of a normal caps face at the same point
size, so 34 in Six Caps and 30 in Space Mono sit at roughly the same visual
weight. Six Caps also wants **letter-spacing +2** to stop the condensed forms
crowding.

## 5. OWNER PLACES — the designer half

**The bar.**
1. Add a **Border**. Anchor: **top, stretched horizontally** (the anchor
   preset with the horizontal bar at the top). Offsets: left `0`, right `0`,
   top `0`, **height `76`**.
2. Brush colour `#2A2A2E`, alpha **0.88**. No corner radius, no outline.
3. Padding: left `28`, right `28`, top `0`, bottom `0`.
4. Inside the Border, add a **Horizontal Box**. Set its vertical alignment to
   **Fill** so both clusters centre themselves in the bar's height.

**Left cluster — always visible.**
5. In the Horizontal Box, add a **Horizontal Box** (this is the left cluster).
6. `MoneyText`, then `DemandText`. Gap **24 px** (slot padding, left = 24 on
   `DemandText`).

**The gap.**
7. Add a **Spacer** with slot **Size = Fill**. This is what pushes the
   selection cluster to the right edge and keeps it there at any window width.

**Right cluster — the selection.**
8. Add a **Horizontal Box** (the right cluster).
9. `SelectedNameText`, `SelectedStateText`, `SelectedPriceText`,
   `BuyPromptText`, in that order. Gaps: **20 px** between the first three,
   **28 px** before `BuyPromptText` — the prompt is an instruction, not
   another fact, and the extra air is what says so.
10. **Set the right cluster to Collapsed by default.** The beta lane shows it
    when a lot is selected. A permanently visible empty half-bar is the
    single fastest way a good HUD starts looking unfinished.

**Vertical alignment:** set every text block to **Center** vertically. With
two families at different sizes, top-aligning them makes the baselines
disagree and the bar look assembled rather than designed.

**Do not add a drop shadow to the bar.** The 88% alpha and the value gap
against the board are doing that job already; a shadow is the UI tell this
direction has spent months removing.

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
