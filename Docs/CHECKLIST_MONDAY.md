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
they belonged to the retired rig. The starter city's demo lot does not
appear yet (it waits on the engineering seat's board factory). Press L for night and again for day: the lights dim, the windows glow, and
NIGHT shows at the right of the bar. Drawn roads are the plate's own grey until the
design lane rules their look.

Optional, two minutes: double-click Saved/Packaged/Mac/StacktownAlpha.app
(rebuild it first with Tools/package.sh if the date is old). It opens the
board with the camera and the HUD and nothing else: no economy, no clicks,
no roads yet. That is the pipeline a stranger's download will use.
