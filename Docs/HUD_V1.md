# HUD v1

Owner, 2026-09-03, after a play session: *"still no ability to build a road or
anything resembling a professional HUD or UI."*

Two halves in one file. **Content** — what the HUD says, which verbs exist,
what a refusal reads — is the beta lane's, in sections marked CONTENT.
**Look** — layout, type, spacing, colour, behaviour — is the direction-B
lane's, in sections marked LOOK. Neither half edits the other's sections.

Everything here must be expressible as **widgets constructed in code** and
added through `AddWidget`. The designer's widget tree is unreachable from the
tooling, so anything that can only be dragged into place is not a
specification, it is a wish.

---

## LOOK 1 — what "professional" means for a photograph

The board is a photographed architectural model. The HUD is a **caption on a
photograph**, not a cockpit. That single reading decides almost everything
below, and it is the standard the owner's word is measured against.

What reads as unprofessional is rarely one ugly element. It is:

- **arbitrary numbers** — 13 here, 17 there, 6 px of padding on one side and 9
  on the other. The eye reads inconsistency as carelessness even when it
  cannot name it.
- **too many alignment axes** — five things each starting at their own x.
- **decoration doing no work** — an icon that repeats the word beside it, a bar
  that repeats a number, a panel border that separates nothing.
- **chrome that competes with the subject** — the board is the product; every
  pixel the HUD spends is a pixel of city it covers.

So v1 buys credibility with **restraint executed exactly**: one type ramp, one
spacing unit, three colours, two alignment axes. Nothing is added that does not
carry information a player needs at that moment.

## LOOK 2 — the type ramp

Two families, already imported and proven. **Tomorrow for words, Space Mono
Bold for live numbers** — monospaced digits so a value that changes while you
watch it does not shuffle sideways and drag its label around.

A modular ramp, not ad hoc sizes. Base 18, ratio ~1.25, rounded to the 8-grid's
sensibilities:

| role | size | face | used for |
|---|---|---|---|
| display | 34 | Space Mono Bold | money |
| title | 22 | Tomorrow SemiBold | selected lot name |
| body | 18 | Tomorrow Medium | state, verbs, prices |
| label | 15 | Tomorrow Medium, +0.06em | units, mode words, headings |
| micro | 12 | Tomorrow Medium, +0.08em | key legend |

**Five sizes and no others.** If something seems to need a sixth, it is
carrying the wrong weight and wants a different colour or position instead.

Letter-spacing rises as size falls — small text needs air to stay legible over
a photograph, large text does not.

## LOOK 3 — the spacing grid

**8 px, everywhere, no exceptions.** Gaps are 8, 16, 24 or 32. Padding inside
a panel is 16. Screen margin is 32.

This supersedes D22's 28 px bar padding: 28 is off-grid and was chosen before
there was a grid. Consistency beats the earlier number.

**Two alignment axes only.** Everything in the left column starts at x = 32.
Everything in the right column ends at screen-width − 32. Nothing is centred,
because a centred column of different-length strings is ragged on both sides.

## LOOK 4 — colour, and only three states

From the board's own sampled palette:

| role | hex | meaning |
|---|---|---|
| ink | `#E8E0D4` | the fact itself |
| dim | `#9A9187` | labels, units, anything the eye may skip |
| accept | `#C08A4E` | affordable, available, yes |
| refuse | `#B4472E` | the only red, and only for a refusal |
| ground | `#2A2A2E` @ 0.88 | the bar and panel |

**Red appears nowhere except a refusal.** That is what makes it mean
something. A price the player cannot afford is `dim`, not red — it is not a
refusal, it is a fact about a wallet.

**No colour carries information alone.** A refused verb also loses its key cap
and gains a reason in words. Colour is confirmation, never the message.

## LOOK 5 — layout

Three surfaces, all runtime-constructed.

**The bar — top, full width, 76 px.** Anchored top and stretched horizontally.
Persistent facts only. Left cluster at x = 32: money, then demand at 24 gap.
Right cluster ending at −32: the mode words. A `Spacer` with Fill between
them, which is what pins the right cluster to the edge at any window width.

Top rather than bottom, measured: at the working framing the top 12% of the
frame is empty backdrop (sd 5.2) while the bottom is the near plate. A bottom
bar covers the best-looking part of the board to sit in front of the worst.

**Mode words, right of the bar.** `ROAD` when road mode is on. `NIGHT` when
night is on. Label size, `dim`, letter-spaced. **Absent when off** — not
greyed, not a toggle graphic. A word that appears is the whole indicator, and
an empty right cluster is the normal state.

**The selection panel — bottom-left**, anchored bottom-left, 32 from both
edges, 320 wide, height by content, 16 padding. Collapsed until something is
selected. A vertical box:

    SelectedNameText     title,  ink
    SelectedStateText    body,   ink — always, all three states
    SelectedPriceText    body,   Space Mono Bold, accept or dim
    (16 gap)                     absent entirely if no verb is present
    verb rows            body,   one per available verb

**The state line is `ink` in all three states.** CONTENT 4 asks which D16
colour each of FOR SALE / OWNED · TIER n / NEEDS REPAIR maps to. The answer is
none: LOOK 4 defines three colours and a ground, and "the D16 state colour" as
written above was a placeholder promising a fourth vocabulary that does not
exist — an arbitrary addition of exactly the kind LOOK 1 warns about. Closed
here rather than filled in.

NEEDS REPAIR is the state that wants to be red, and must not be. Red is a
refusal, and a failed building is not a refusal — it is a fact. It also does
not need the HUD to raise its voice: D16 already weathers the timber toward
this species' grey on the board, legible at board range (LOOK 8). The three
states are told apart by their words, by which verb appears beneath them, and
by the wood. Not by a colour the player would have to learn.

**The price line is absent, not blank, when no verb is present.** CONTENT 4 is
right that it must not read `0` or `—`; absence satisfies that and matches the
panel's own rule for verbs. A blank-but-present row is the same failure as a
greyed-but-present verb: it holds space to say nothing. The panel's height is
content-driven, so absence simply shortens it.

A verb row is `[key]  Verb  price` on one line: micro key cap in `dim`, verb in
`ink`, price right-aligned in Space Mono Bold. **Available verbs only** — an
unavailable verb is absent, not greyed. A greyed list teaches the player to
read past the whole panel.

**The key legend — bottom-right**, micro, `dim`, ending at −32. Always present,
never emphasised. It is what makes an unfamiliar build learnable, and it is the
cheapest professionalism in the document.

CONTENT 6 asks whether the camera keys belong on a separate, "even more micro"
line. Not smaller — LOOK 2 says five sizes and no others, and a sixth invented
for one line is the arbitrary number LOOK 1 is about. They get a **second micro
line, same size**, `dim`, sitting directly above the verb legend on the same
−32 axis. A player who does not know the verbs is stuck; a player who does not
know they can move the camera is stuck worse, and one 12 px line is the whole
cost of fixing that.

## LOOK 6 — refusals, and where they live

**A refusal about a PLACE goes to the cursor** — "too far from a road", "in the
road". It concerns where the player is pointing, so it belongs where they are
looking, next to the ghost that already turned red.

**A refusal about an ACTION goes to the bar** — it concerns a thing they tried
to do, and the bar is where the verbs' consequences live.

My first draft used "already at top tier" as the example here. CONTENT 1 has
since ruled that a verb which cannot succeed is *absent*, so that refusal is
now unreachable and the example is withdrawn. This is the better rule and it
narrows this surface almost to nothing: per CONTENT 2 there is exactly one
reachable action refusal today, plus a race. A refusal surface that is nearly
always empty is a sign the panel above it is honest.

Both are `refuse` coloured, body size, and both **clear on the next input**
rather than on a timer. A message that vanishes while you are reading it is
worse than one that waits.

## LOOK 7 — the HUD does not respond to zoom

The bar and panel are the same size at the survey stop and at the closest.
**Chrome that reflows while the player is navigating reads as instability**,
and the zoom is used constantly. The world-space ghost scales with distance
because it belongs to the board; the HUD does not, because it belongs to the
screen.

## LOOK 8 — excluded, with reasons

- **No icons.** A coin beside money, a hammer beside build. They repeat the
  word they sit next to and they are the fastest way to look like a mobile
  game.
- **No meters or progress bars.** D16 put building condition into the timber —
  cold patches in a warm field, legible at board range with no UI at all. A bar
  would say it a second time, worse.
- **No panel borders or drop shadows.** The 88% ground and the value gap
  against the board already separate the surfaces. A border is a line drawn to
  compensate for a contrast that is already there.
- **No animation on value change.** A number that counts up pulls the eye off
  the board. Easy to add later; hard to remove once expected.
- **No minimap.** The survey zoom stop is the minimap, and it is the real
  board rather than a diagram of it.

## LOOK 9 — acceptance

A capture at the **working stop** with a lot selected, the panel open, a verb
list, and the legend — plus one with **nothing selected**, which is what the
player sees most of the time and is the frame most likely to be forgotten.

Judged on: does it read as a caption rather than a cockpit; is every number on
the ramp; do the two alignment axes hold; is red present only on a refusal;
and is the board still the thing you look at.

One thing the capture must prove rather than assume: **CONTENT 6's legend line
is ~95 characters, and I have not measured it.** At micro with letter-spacing
it should clear the 320 px panel on a wide window, but I am estimating font
metrics I cannot read without the editor. If it collides with the selection
panel at the narrowest supported width, the fix is to break it at the `·`
before `B buy` into two micro lines — not to shrink the type, which LOOK 2
forbids.

---

## CONTENT 1 — the verb set, and which ones are ever present together

Three verbs exist, each backed by a real function
(`Content/Python/econrules.py`) with its own price function. **At most ONE
economy verb is ever present on a given lot today** — not a UI simplification,
a structural fact of the rules themselves: BUY needs `not owned`; UPGRADE
needs `owned and not failed`; REPAIR needs `owned and failed` — `failed` and
`not failed` cannot both hold. The panel's own "one row per available verb"
shape (LOOK 5) is built to hold more than one row because the rules may grow
that capability later; today it will only ever show zero or one.

| verb | key | present when | price fn | absent when |
|---|---|---|---|---|
| BUY | `B` | lot selected, **not owned** | `price(rid, tier, width)` | owned |
| UPGRADE | `U` | owned, **not failed**, ladder not topped, next tier's asset baked (`tier_up_allowed()[0]`) | `upgrade_price(rid, tier, performance)` | unowned, failed, topped out, or next tier unbaked |
| REPAIR | `H` | owned, **failed** | `repair_price(tier)` | unowned or not failed |

**"Topped out" and "asset unbaked" make UPGRADE absent, not refused** — the
verb structurally cannot succeed regardless of money, the same shape as BUY
being absent on an owned lot. Affordability is the ONE case a present verb
can still fail on, and LOOK 4's own rule already covers it: the price is
`accept` if `money >= price`, `dim` if not — never `refuse`. Refuse is a
button PRESSED and rejected, not a button merely unaffordable.

`H` for repair, not `R` — `R` is the camera's own pedestal key
(`Docs/LENSRIG_P0.md`); moved here for exactly that collision, same
discipline `Docs/ROAD_BUILD_CONTRACT.md` section 4 already applies to the
road-mode key.

## CONTENT 2 — refusal strings, split by subject per LOOK 6

**PLACE refusals** (cursor, next to the ghost) are `init_unreal.py`'s own
`_place_refusal_message()` classifier, already built and live — not proposed
here, cited: it converts `placement.py`'s own technical reasons (exact spans,
exact cause — correct for a log, wrong for a player) into the six strings
below. Extended with the equivalent set for `placement.resolve_road_draw`'s
own refusals (`Docs/ROAD_BUILD_CONTRACT.md` section 3), reusing the same
words where the underlying fact IS the same one (overlap is overlap, on the
starter city or a lot).

| cause | string |
|---|---|
| off the plate (lot or road) | Off the board |
| crosses a pinned lot | That's part of the starter city |
| crosses a placed lot | Already built there |
| the lot pool is full | No more lots available |
| standing in the road corridor | That's the road — click the block beside it |
| beyond a road's reach | Too far from a road |
| standing where two roads share pavement | That's the crossing — pick one road's frontage |
| draw: not close enough to straight | Roads run straight |
| draw: shorter than one lot | Too short for a road |
| draw: would cross an existing road | Roads can't cross yet |
| anything else | Can't build here |

**ACTION refusals** (bar, where the verbs live) — today there is exactly ONE
reachable case, because CONTENT 1's own presence rules already filter out
every other reason `buy()`/`upgrade()`/`repair()` can return (not owned,
already owned, not failed, failed, ladder-topped, unbaked — none of these are
attemptable through the panel, so none needs its own string):

| cause | string |
|---|---|
| insufficient funds (any of the three verbs) | Can't afford it |
| anything else (a race — the lot changed between the panel drawing and the key press) | Can't do that right now |

Both refusal classes hold as STATE, per LOOK 6 — cleared on the next input,
not a timer. The place refusal is keyed to the cursor's own last resolve
call (`resolve_click`/`resolve_road_draw`'s own `reason` string, already
computed every hover); the action refusal is keyed to the last verb attempt
and clears the moment any key is pressed, selection changes, or the attempt
is retried and succeeds.

## CONTENT 3 — demand is a NUMBER, not a word

Checked directly, not assumed: `state['demand']` is a float
(`econrules.json`'s own `demand_default`, currently static — nothing in this
codebase writes a new value to it after seeding, confirmed by grep this
session, `ECONOMY_TICK_CONTRACT.md`'s own "Growth contract" finding). There
is no bucketing anywhere that would turn it into a word like STEADY or
BOOMING. So: **Space Mono Bold, the number-face, same family as money** — not
Tomorrow. If the owner later wants demand to read as a word, that needs a new
bucketing function nobody has built yet; not proposed here, since nothing
today would drive it.

## CONTENT 4 — the selection panel's own three lines

    SelectedNameText     the lot's recipe id and width — e.g. "vernacular 820"
    SelectedStateText    one of: FOR SALE / OWNED · TIER n / NEEDS REPAIR
    SelectedPriceText    the ACTIVE verb's own price (blank if none is present)

`SelectedStateText`'s three words are a straight read of `owned`/`tier`/
`failed` (clickdriver.py's own `'owned, tier %d' % tier if owned else 'for
sale'` pattern, extended with the FAILED case this session's economy work
added — `NEEDS REPAIR` did not exist before ruling 4, `Docs/
ECONOMY_TICK_CONTRACT.md`). Which of D16's own state colours each maps to is
the design lane's own call (LOOK 5 already reserves "the D16 state colour"
for this line) — FAILED is the one of the three with no existing mapping,
since it is new; the other two (for-sale, owned+tier) may already have one
from D16's own vocabulary.

`SelectedPriceText` shows the price of whichever verb CONTENT 1 says is
present — never more than one, per that section's own structural fact — in
`accept`/`dim` per LOOK 4's own affordability rule. Blank (not zero, not
absent-with-a-dash) when no verb is present at all — an owned, unfailed,
topped-out lot has nothing to price.

## CONTENT 5 — mode indicators

**ROAD** — ready today. `Docs/ROAD_BUILD_CONTRACT.md` section 4 proposes `G`
for the road-mode toggle (unclaimed against every reserved key named there);
the word shows for exactly as long as that mode is active, per LOOK 5's own
"absent when off" rule.

**NIGHT** — the word is already specified (LOOK 5) but the BOOLEAN it reads
is not confirmed to exist yet. Open, not this section's to resolve: whoever
wires the mode-word cluster needs a real GameInstance or driver-side flag to
read, not just the word itself — flagged here as a dependency, not invented.

## CONTENT 6 — the key legend

One line, micro, per LOOK 5:

    CLICK select / place · SCROLL width · B buy · U upgrade · H repair · N hold reset · G road mode

Camera keys (`Docs/LENSRIG_P0.md`'s own A/D/W/S/R/F/Q/E/arrows) are
deliberately NOT in this legend — a separate, always-on system a player
learns once, not a per-session verb list. Whether they belong in a SEPARATE,
even-more-micro line is a LOOK call, not made here.

## CONTENT 7 — where each piece of text actually reads from

For whoever wires this against the driver — every value above traces to a
real field, nothing here is a placeholder invented for the mockup:

    money            state['money']                          (citytick/econrules)
    demand           state['demand']                          (CONTENT 3)
    lot name/width   parcel['rid'], parcel['width']
    lot state        parcel['owned'], parcel['tier'], parcel['failed']
    verb presence    CONTENT 1's own table, computed per lot
    verb price       price() / upgrade_price() / repair_price() —
                     econrules.py, performance arg on upgrade_price() only
    place refusal    the last resolve_click/resolve_road_draw call's
                     own `reason`, classified per CONTENT 2
    action refusal   the last buy()/upgrade()/repair() attempt's own
                     `reason`, classified per CONTENT 2
    ROAD word        road-mode boolean (Docs/ROAD_BUILD_CONTRACT.md §4)
    NIGHT word       an unconfirmed dependency (CONTENT 5)
