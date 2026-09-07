# Monday checklist: the C++ game (owner's test slot, 20 to 30 minutes)

Since Saturday evening the whole game runs in C++ (Docs/STATE_HANDOVER.md
Phase B): your save was migrated once into Saved/Stacktown/citystate.json
and the Python drivers are off. Everything below is the C++ code.

Launch "Play Stacktown.command" (or Tools/play.sh). The game opens on the
wide board view. Nothing else on your machine is needed. Reply in this
format, one line per item: what you did, what you saw. "Same as described"
is a fine answer; so is "no".

| # | Do this | Expected |
|---|---|---|
| 1 | Do nothing for five seconds | The board sits in the frame at the arrival angle; a dark bar across the top shows money and DEMAND; a two-line key legend sits bottom-right; nothing else on screen |
| 2 | Hold the RIGHT mouse button and drag left/right | The view orbits around the board's centre; the board stays put |
| 3 | Still right-dragging, drag up/down | The view tilts; it never goes below the board or flat enough to lose it |
| 4 | Roll the wheel forward with the cursor over a building | The view closes in on THAT building, which stays under the cursor; the lens gets longer (less perspective) |
| 5 | Roll the wheel back | The view opens out again toward the wide shot; it stops at the wide limit |
| 6 | Push the cursor against the left edge of the window | The view slides left across the board and stops at the board's edge |
| 7 | Arrow keys | Same slide, one direction per arrow |
| 8 | Move the cursor over empty plate, then press Tab a few times, then click | A ghost pad follows the cursor and changes width with Tab; a click places a lot; the camera does NOT move |
| 9 | Left-click a building | A panel appears bottom-left: name and width, its state, and one verb row with a key and a price; it stays until you select something else |
| 9b | Press the verb's key (B, U or H) | The verb happens; if you cannot afford it, "Can't afford it" appears in the bar in red and clears on your next key |
| 10 | Press N once (do not hold) | Nothing resets. (Hold N two seconds only if you WANT a reset) |
| 11 | Press G, click a start point on empty plate, click an end point 3 to 4 lots away along the same line | A grey road appears between the clicks; ROAD shows at the right of the bar while G is on; a diagonal or a very short one is refused with a short message at the cursor |
| 12 | Press G again, then click beside the new road | The ghost pad lands on the new road's own frontage; a click places the lot there |

Known and expected: Q, E, W, S, A, D, R and F no longer move the camera;
they belonged to the retired rig. Press L for night and again for day: the
lights dim, every OWNED building's windows glow, and NIGHT shows at the
right of the bar. Starter roads and drawn roads are the same pale timber
inlay, flush with the plate (the design lane is still fixing the grain
tiling: one big swirl per road is known).

THE PACKAGED APP (Saved/Packaged/Mac/StacktownAlpha.app, universal, rebuilt
2026-09-06 18:41 - rebuild with Tools/package.sh if the date is old; if step 1's pad or the selection outline is missing, the cook dropped a path-loaded asset: grep Saved/StagedBuilds/Mac/Manifest_UFSFiles_Mac.txt for it) is the
whole C++ game, not the camera-only shell it was on the 5th. It keeps its
OWN city, separate from the editor's, so the first launch is the FRESH
CITY the rules define: $100, DEMAND 1.00, the plate with its two roads and
NO lots - there are no pinned lots in a fresh C++ city; the starter towers
you see under the editor are the old test save. Proven 2026-09-06 16:40 in
a test game from the same reset:
  1. click the plate just north of the long road, near its middle - a pad
     ghost follows the cursor beforehand; the click places lot P1 at 820
     wide (TAB cycles the width first if you want a bigger one);
  2. B buys it: $66.40, so money reads $33.60 and a small tier-0 mass
     stands where the pad was; the panel reads "vernacular 820 / OWNED ·
     TIER 0 / U UPGRADE $50";
  3. wait: rent ticks every two seconds ($1 a tick at tier 0), so the
     upgrade is affordable inside half a minute; U upgrades;
  4. Cmd-Q and relaunch: the city is exactly where you left it (the app
     saves every two seconds into its own folder, named in item 15).
That is the pipeline a stranger's download will use.

## Added 2026-09-06 evening (all in the C++ game and the packaged app)

13. NIGHT: press L. The board darkens, the seven lights dim, and every
    OWNED building's windows light up; a for-sale pad stays dark. Press L
    again for day. If any owned building stays black at night, say which.
14. ROADS: the two starter roads and any road you draw (G, click, click)
    are the same pale timber inlay, flush with the plate. Note whether the
    seam reads as an inlay or as a curb, and whether the grain figure looks
    like ONE big swirl per road (known: the design lane is fixing the
    tiling).
15. TRADES (mock, no market): with the game running, append one line to
    Saved/Stacktown/trade_ledger.jsonl (under the packaged app the folder
    is ~/Library/Containers/com.YourCompany.StacktownAlpha/Data/Library/
    Application Support/Epic/StacktownAlpha/Saved/Stacktown/ - the
    citystate.json there is the app's own save):
        {"trade_id": "t1", "pnl": 12.5}
    Within two seconds money rises and the bar reads `trades: ...`. Append
    the same line again: money rises again (it is a NEW trade - the cursor
    is the line count). Never delete the file while a save exists.
