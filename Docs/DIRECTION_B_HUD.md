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

**Font assets — the ones to bind, corrected 2026-09-02:**

    /Game/Stacktown/UI/Fonts/Tomorrow-Regular_Font
    /Game/Stacktown/UI/Fonts/Tomorrow-Medium_Font
    /Game/Stacktown/UI/Fonts/Tomorrow-SemiBold_Font
    /Game/Stacktown/UI/Fonts/SpaceMono-Bold_Font

**These are `UFont` assets, and the earlier claim that a raw `FontFace` would
do was wrong.** `SlateFontInfo(font_object=<FontFace>)` assigns and reads back
true — and renders every glyph as the missing-glyph box. The beta lane's
control settled it: Roboto, a UFont, draws real glyphs through the identical
`SetFont` path with the identical typeface value, while a FontFace beside it
draws boxes. Raw FontFace via SlateFontInfo does not draw in this build.

**Ruled out on the way, by measurement rather than argument:** `LoadingPolicy`
reads `LazyLoad` with a `SourceFilename` outside Content, which looks exactly
like a face streaming from a missing file. It is not — each `.uasset` is its
`.ttf` plus about 1.5 KB (`F_Tomorrow_Regular` 61,091 against 59,520), so the
font data is embedded and LazyLoad only governs when that payload is paged in.

**Typeface name:** pass **empty / `None`** — that is the value the Roboto
control renders with. The typeface entries could not be read from Python (the
same struct reader that cannot see `TypefaceEntry` returns an empty list here,
so "empty" means "cannot see", not "is empty"), and rendering is the only test
that settles it.

`Content/Python/import_fonts_composite.py` rebuilds all four: the engine's
`FontFileImportFactory` carries `batch_create_font_asset`, so it constructs
the UFont beside the face and nothing has to hand-build a Typeface — which is
what defeated the first attempt.

**Tidy owed:** the four original `F_*` FontFace assets still sit in that
folder and draw boxes. Nothing should reference them. They are left in place
rather than deleted mid-diagnosis; retiring them needs the owner's word.

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

## 7. Reset confirmation — designed, NOT YET BUILT (2026-09-03)

**Why this exists.** A stray N press wiped six built towers back to a
fresh seed, mid-owner-session — `citytick.city_reset()` is, by its own
docstring, "LOUD by design," and it is: the log line is unmissable, the
state file visibly changes. What it was never checked against is
whether the KEY that fires it is exactly as loud. It wasn't — one tap,
no confirmation, full wipe, same input weight as panning the camera.
This section specifies the fix. It is a specification, not a build —
the editor is held for the owner's own play session; nobody implements
this until that hold lifts.

**The gesture: HOLD, not double-tap.** Both were on the table. Hold-to-
confirm wins on a single ground: a double-press has no honest way to
show its own state on screen before the second press lands — there is
nothing to display except "you have N seconds left to press again,"
which is a countdown wearing a different gesture. A hold's own
progress *is* its display — the player's finger is still on the key
while the prompt is up, so "keep holding" reads as continuous cause and
effect the way a second, separate keypress cannot. It also matches
the coordinator's own naming of the on-screen text as "hold to reset,"
not "press again to reset."

**Threshold: 2.0 seconds.** Long enough that a single accidental tap
(the exact failure mode this exists to prevent) can never cross it —
even a held key from a stuck keyboard event reads as a deliberate
choice by two seconds, where one tap does not. Short enough that a
genuinely-intended reset does not feel punished for being genuine.

**On-screen feedback: text, not a meter.** Section 6 already rules out
progress bars and meters for game state, and holds to that reasoning
here even though this is input feedback, not economy state — a filling
bar is exactly the "mobile game" UI tell section 6 exists to keep out,
and this HUD has no precedent for one anywhere. The prompt is a single
line of plain text, the same channel `SelectTick`'s selection debug
line used before the real HUD existed
(`Development|PrintString`, a stable `Key` so repeated calls replace
rather than stack, short `Duration` so it vanishes the instant the key
is released rather than lingering as a stale message) — this is
authored on purpose as a TRANSIENT system message, not a persistent
bar element, so it deliberately does NOT go through the
GameViewportSubsystem construction section 5 specifies. Building it as
a seventh permanent widget would mean new layout math for something
that is invisible 99% of a session; PrintString is the right tool for
a rare, input-driven, self-clearing message, not a compromise standing
in for a "real" one.

**Copy:** `"HOLD N TO RESET — <n>s"` where `<n>` counts DOWN from 2.0 to
0.0 at one decimal place, so the number the player watches is "how much
longer," matching the direction they're already holding toward, not a
count-up that reads like a stopwatch. Colour: reuse the accent bronze
already declared in section 2 (`#C08A4E`) converted through the same
sRGB curve section 2 already specifies — a new colour for a single
transient line is exactly the kind of one-off swatch section 2's "no
large-scale albedo variation" reasoning argues against, even though
that reasoning was written about materials, not UI.

**BP_LensRig additions — exactly what the graph needs, nothing left
implicit:**

    Variable   NHoldTime  (Float, NOT instance-editable, internal only)
    Variable   NHoldFired (Bool,  NOT instance-editable, internal only)

**The accumulator is `DeltaSeconds`, not a wall-clock timestamp.**
Every other timed thing in this graph (`FInterpTo`'s camera easing) is
already driven off the tick's own `DeltaSeconds`, and this stays
consistent with it rather than introducing a second notion of time via
an absolute `GetTimeSeconds` difference — the two would drift under
anything that changes simulation rate, and there is no reason for a
2-second confirm gesture to be exempt from the same clock the boom's
own motion already trusts.

**A RELEASE LATCH is required, not optional — caught before build,
2026-09-03.** The first cut of this spec reset `NHoldTime` to `0.0`
the instant it fired and left it at that: with `EventTick` polling at
frame rate, a hold that continues past the 2.0s threshold would cross
it again 2.0s later, and again, for as long as the key stays down —
one long press could fire `SetResetRequested` more than once, each one
a fresh wipe attempt racing the driver's own consume-and-clear tick.
The fix is a second bool, `NHoldFired`, that gates the fire condition
and is cleared ONLY on release, not on fire:

    if IsInputKeyDown(PlayerController, "N"):
        if not NHoldFired:
            NHoldTime = NHoldTime + DeltaSeconds
            if NHoldTime >= 2.0:
                <cast to BP_StacktownGameInstance>
                SetResetRequested(true, GameInstance)
                NHoldFired = true
            else:
                remaining = 2.0 - NHoldTime
                PrintString(
                    "HOLD N TO RESET — " + ToString(remaining, 1 decimal) + "s",
                    Duration=0.15, Key="ResetConfirm",
                    TextColor=(the section-2 accent, sRGB-converted))
    else:
        NHoldTime = 0.0
        NHoldFired = false

Once `NHoldFired` is true, the whole inner block is skipped for the
rest of that hold — no more accumulation, no more prompt, exactly one
`SetResetRequested` per press-to-release cycle. The `else` branch is
the only place either variable is cleared, so the gesture only re-arms
after a genuine release: the player must let go and press again to
fire a second reset, which is the entire point of a confirm gesture —
holding harder or longer than 2.0s must never do MORE than a clean
2.0s hold does.

**What this does NOT change:** `SetResetRequested`'s own consumer
(`init_unreal.py`'s reset channel) is untouched — this is entirely a
gate in FRONT of the same existing verb, not a new reset pathway. The
owner has already been told, in plain language, that a bare N wipes
the session; this specification is the fix for the NEXT owner and every
player after them, not a substitute for that warning while it's still
unbuilt.
