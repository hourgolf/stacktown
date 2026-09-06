# Trade adapter charter — a separate service, paper-only

The coordinator's task, 2026-09-04, answering the owner's own definition
of a trade (`ECONOMY_TICK_CONTRACT.md`, "What a trade is," quoted in
full there): a real Alpaca **paper** trade, strategy translated from a
TradingView Pine script the owner will supply, running as its own
Python service entirely outside the editor. This document is the
charter for that service — architecture, safety rules, open questions.
**No code exists yet for the adapter itself.** The only code this pass
adds is pure, already-landed, and already proven never to touch a
brokerage at all: `econrules.py`'s ledger-reward functions (section 1)
and the ledger schema (section 5) they read. Everything else below is
design for someone to build later, not a description of something
running today.

## 0. The rule — read this before anything else in this document

**Alpaca credentials (`APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`) live
ONLY as environment variables in the owner's own shell, on the owner's
own machine, read directly by the adapter process at its own startup.**
They are:

- **never** typed into a chat message, by the owner or anyone else;
- **never** written to any file this repository tracks — not
  `citystate.json`, not a `.env` committed to the repo, not a config
  file, not a log;
- **never** read, handled, or passed along by Claude, any lane, or the
  coordinator, in any form — this includes never being asked FOR them,
  never being asked to "just paste them here to test," and never being
  generated as a placeholder that looks real;
- the owner's alone to set, rotate, and revoke, entirely outside this
  project's own tooling.

If a key ever appears in a chat message, a file diff, a log line, or
anywhere else it should not be, treat it as compromised — the fix is
the owner rotating it at Alpaca's own dashboard immediately, not
deleting the line and moving on.

## 1. What already exists (done, this pass)

`econrules.py`, self-tested 17/17 (`is_win`, `trade_count_reward`,
`trade_outcome_bonus`, `apply_trade_ledger` — the last is the one real
entry point). **This code never places an order, never imports
anything Alpaca-related, and never sees a credential.** It reads
`pnl` off entries in an already-written ledger (section 5's own
schema) and converts NEW entries — tracked by `state['trades_processed']`,
a new top-level state field, idempotent by construction — into money:
a flat credit at every `trade_credits_per_n`-th closed trade regardless
of outcome, and a flat bonus per winning trade (`is_win`: closed profit,
`pnl > 0`, the PROPOSED default for the owner's own open question in
section 8). Three new placeholder constants in `econrules.json`
(`trade_credits_per_n=10`, `trade_credit_amount=20`,
`trade_bonus_per_win=5`) — scaffolding, the same discipline every other
number in that file already holds to, not final answers.

Explicitly NOT decided by this function: whether "bonus toward
upgrades" (the owner's own phrase) should land as money directly (what
it does today), a nudge to a lot's own `performance` value, or
something else — `ECONOMY_TICK_CONTRACT.md`'s own record of the
owner's words already names "escalation factors... still to be worked
out." This function computes a reward amount; it does not commit to
the reward's final shape.

## 2. Scope and boundary

**"The game never places orders; it consumes outcomes"** —
`ECONOMY_TICK_CONTRACT.md`'s own framing of the owner's words, and the
single sentence that decides every architecture choice below. The
adapter is a wall, not a bridge: strategy and execution live entirely
on its side; the game only ever reads a ledger of trades ALREADY
closed. Nothing in `Content/Python/` (editor-loaded, `PythonScriptPlugin`
-bound) ever imports an Alpaca client, ever holds a credential, or ever
calls an order-placing function — that boundary is structural, not a
convention someone has to remember.

Runs as its own process, entirely outside the editor: no PIE
dependency, no `unreal` import, nothing about it needs Blueprint or the
game world at all. It writes one file (the ledger); the driver's own
`_sync_parcels`-style polling already knows how to read a file
(`citystate.json` itself is the precedent) and call
`econrules.apply_trade_ledger` — a few lines next to the other
request-consuming code, not built in this pass since the adapter itself
doesn't exist yet to produce a real ledger to consume.

## 3. Inputs

1. **Strategy module** — the owner's Pine script, translated to Python
   by this lane once supplied. Self-tested against RECORDED bars before
   it ever runs against anything live — same discipline as every other
   module in this project (`econrules.py`, `placement.py`): known
   inputs, hand- or reference-checked outputs, proven standalone before
   it drives anything real.
2. **Ticker** — one symbol, read from adapter config (an environment
   variable or a small local config file, never hardcoded and never
   assumed) — not sensitive the way a credential is, but still the
   owner's own choice, not this charter's.
3. **Market data** — Alpaca's Market Data API, `https://data.alpaca.markets`
   (a separate `https://data.sandbox.alpaca.markets` also exists,
   verified against Alpaca's own current API reference this pass, not
   assumed from memory). Historical bars for the strategy's own
   self-tests; live/recent bars for real-time monitoring once running.

## 4. Execution — paper only, structurally, not just by convention

**Verified against Alpaca's own current API reference, 2026-09-04, not
assumed:**

    Live trading:   https://api.alpaca.markets
    Paper trading:  https://paper-api.alpaca.markets

**Paper and live accounts carry DIFFERENT, non-interchangeable API key
pairs** (Alpaca's own documentation: "your paper trading account will
have a different API key from your live account") — this is the
adapter's PRIMARY safety property: a paper key literally cannot
authenticate against the live endpoint. A code bug that pointed the
adapter at the wrong URL would fail to authenticate, not silently place
a real trade. Belt-and-suspenders on top of that structural fact, not
instead of it:

- **Base URL asserted at startup**, not just configured — the adapter
  refuses to run at all unless its own configured base URL contains
  `paper-api`, a hard-coded check, not a flag someone could quietly
  flip.
- **Idempotent order ids** — Alpaca's `POST /v2/orders` accepts a
  caller-supplied `client_order_id` (confirmed present in the current
  API schema this pass; the exact duplicate-submission behavior was
  NOT confirmed against live docs and needs a real check before this
  is relied on for correctness, not assumed from the field merely
  existing). The adapter derives each order's id deterministically from
  the strategy alert that triggered it, so a retried or double-fired
  alert can never place the same order twice.
- **A kill switch that needs no API call of its own to work**: a
  single local file (e.g. `STOP`) the adapter checks before every order
  submission — if present, refuse all new orders and log why, but keep
  running (so the process stays alive to report state, rather than a
  hard crash that could leave a position unmanaged). Deliberately
  file-based, not a dashboard toggle or a remote flag — the simplest
  possible off switch, reachable by anyone with shell access to the
  machine, working even if the network or Alpaca itself is unreachable.
- **Position limits**, checked BEFORE every order submission, refused
  loudly (not silently clamped) if exceeded: a max position size for
  the one configured ticker, and a max count of concurrent open
  positions. Values live in adapter config, conservative defaults,
  never inferred from account balance.

## 5. The ledger

**Format: JSON Lines (`.jsonl`), append-only** — one JSON object per
line, one line per CLOSED trade, written the instant a position closes
and never rewritten. Append-only is the point: the adapter only ever
opens the file in append mode, so a crash mid-write can corrupt at most
the last line, never history, and nothing in this design ever needs to
read-modify-write the whole file.

    {"trade_id": "...", "ticker": "...", "side": "long"|"short",
     "entry_time": "ISO 8601", "entry_price": float,
     "exit_time": "ISO 8601", "exit_price": float,
     "size": float, "pnl": float, "alert_id": "..."}

`trade_id` is the adapter's own `client_order_id` (section 4) — one
ledger line per closed round trip, not per order, so a position opened
and closed in two separate fills is still one ledger entry. `alert_id`
traces a trade back to the strategy signal that triggered it, for
debugging the translated Pine logic against what actually fired.
`econrules.apply_trade_ledger` (section 1) reads ONLY `pnl`; every
other field exists for the owner/coordinator's own auditing, not
because the reward math needs it.

**Consumption, once the adapter is real** (not built this pass): the
driver reads the ledger file (same file-polling shape `citystate.json`
itself already uses), passes the full line list to
`econrules.apply_trade_ledger(state, ledger_entries)`, persists the
result. `trades_processed` in `citystate.json` means calling this every
tick, on a ledger that's mostly unchanged since the last tick, costs
nothing extra and never double-counts — proven by self-test 17's own
idempotency case (calling twice on the same ledger is a true no-op).

**Two-process fact, 2026-09-04 (`Tools/play.sh`, `PACKAGED_BETA.md`'s
own "Interim" section): the ledger can now have MORE THAN ONE reader.**
What self-test 17 actually proves is narrower than "safe across
processes" — it proves `apply_trade_ledger` is a pure function of
(state, ledger) that never mutates the ledger and never re-reads an
entry once that STATE's own `trades_processed` has passed it. That
property holds per state file, unconditionally, regardless of how many
processes are reading the ledger — the adapter only ever APPENDS to it
and nothing else ever writes to it, so there is no read/write race on
the ledger itself, full stop.

The real question is a different one, and this design does not answer
it: if the owner's main-editor PIE and their own `Tools/play.sh` `-game`
session are BOTH running against the SAME `citystate.json` (both true
by default — the owner's own PIE was never subject to the lane-
isolation override, and `play.sh` opens the real save with no override
of its own), the two processes' drivers tick that ONE file concurrently
— trade rewards included, but no more or less exposed than rent, buy,
upgrade, or repair already are under that same condition. This is a
state-file concurrency question, not a ledger-idempotency one, and it
is `PACKAGED_BETA.md`'s own new finding — **CLOSED there, 2026-09-04**:
a pid lock file from the standalone game now steers an editor PIE off
the real save automatically while it's running, so this no longer
needs solving here too.

## 6. Fake broker, for tests

A module that replays a RECORDED session — historical bars plus a
scripted sequence of fills — implementing the same interface the real
Alpaca client would (submit order, get order status, get positions).
Its job: let the strategy module's own self-tests, and the adapter's
own order-lifecycle logic (idempotency, position limits, the kill
switch), run and prove themselves WITHOUT ever making a network call to
Alpaca, paper or otherwise — the same "self-tested standalone, no
external dependency" discipline every pure-Python module in this
project already holds to (`econrules.py`, `placement.py`,
`citylayout.py`), extended to a module whose real counterpart talks to
the outside world. CI and any self-test run should NEVER touch Alpaca's
actual paper endpoint — that endpoint is for the owner's own supervised
runs, not an automated test suite's.

## 7. What the owner must supply

- The Pine script (translated by this lane once received).
- The ticker to monitor.
- Alpaca paper-trading API keys, set as environment variables in the
  owner's OWN environment — never handled by a lane, never sent
  through chat, never written anywhere in this repository (section 0).

## 8. Open questions for the owner

1. **Position size** — how much of the paper account's capital per
   trade? Not proposed here; the adapter's own position-limit config
   (section 4) needs a real number, not a placeholder.
2. **What "successful" means** — `is_win`'s default is closed profit
   (`pnl > 0`, breakeven does not count). Confirm, or name a different
   bar (net of Alpaca's own paper-trading costs if any, a minimum size,
   something else).
3. **The credit/bonus numbers** — `trade_credits_per_n=10`,
   `trade_credit_amount=20`, `trade_bonus_per_win=5` are scaffolding
   placeholders (section 1), not proposed final values, unlike the
   "Rent cadence proposal" section elsewhere in this file's sibling
   document — no target feel was given to derive them against here, so
   they were not simulated toward one the way that section's numbers
   were.
4. **Where "bonus toward upgrades" lands** — money directly (today's
   build), a per-lot `performance` nudge (tying into the already-built
   `premium()` — noting `premium()` today gives NO discount for
   performance above neutral, only a penalty below it per ruling 3, so
   a "bonus" that raises performance would currently do nothing to
   upgrade cost unless that formula changes too), or something else —
   the owner's own "escalation factors... still to be worked out."
5. **Alpaca's exact duplicate-`client_order_id` behavior** — not a
   question for the owner, but an open technical item: verify against
   Alpaca's live API reference (not just the schema description) before
   the adapter relies on it for idempotency, since this pass could only
   confirm the field exists, not its rejection behavior on reuse.

## 7. Consumption in the C++ game (2026-09-06, coordinator)

The C++ owner (UStacktownCitySync, Phase B) reads the ledger every economy
tick (two seconds) from `Saved/Stacktown/trade_ledger.jsonl` under the
project (a packaged app: its own Saved/Stacktown), parses each line's `pnl`,
and calls UStacktownEconomy::ApplyTradeLedger, which is idempotent through
the state's `trades_processed` exactly as the Python was. A torn last line
is skipped, never counted. Rewards surface on the HUD bar ("trades: +$N
credits, +$M win bonus") until the next input. The adapter (engineering
seat, board item 6) appends to that path and never reads it; keys stay in
the adapter's environment; the game never places orders.

### 7.1 The cursor is the line count - so the file is append-only, forever

Proven live 2026-09-06 (C++-owned test game, mock adapter): the game keeps
`trades_processed` in the city state and counts every closed-trade line past
it. Ten mock trades: 10 counted, 2 events, +$20 credits +$40 win bonus, bar
message `trades: +$20 credits, +$40 win bonus`. A second read of the same
file: 0 counted. A torn last line (crash mid-write) is skipped and never
counted. Three more lines two seconds later reached the HUD bar through the
timer read (`trades: +$15 win bonus`).

The trap, also found live: DELETE or TRUNCATE the ledger and the saved cursor
outlives it - new lines below the old count are treated as already paid.
So the adapter never rotates, truncates or rewrites the file. If the file
must be replaced, the city state's `trades_processed` is reset with it (an
owner's action, not the adapter's).
