# The trade adapter

A separate process that writes a ledger the game reads. It is the whole of the
trade side that touches money, and it touches only **paper** money.

```
adapter  --append-->  Saved/Stacktown/trade_ledger.jsonl  --read-->  the game
```

The adapter never sees the game. The game never places an order. They share one
file, and nothing else.

## Run it

```bash
python3 Tools/trade/adapter.py --mock --count 10      # ten closed trades
python3 Tools/trade/adapter.py --mock --loop          # keep appending
python3 Tools/trade/adapter.py --check-keys           # are the keys set?
python3 Tools/trade/adapter.py --selftest             # no network, no keys
python3 Tools/trade/ledger.py                         # ledger self-test
python3 Tools/trade/strategy.py                       # strategy self-test
```

`--ledger` points it at another project's `Saved/Stacktown` — a packaged app has
its own, and the adapter never guesses which game it is feeding.

## Three rules this code enforces rather than documents

**Append-only, forever.** The game's cursor is `trades_processed` in the city
state and it is a *line count* (`Docs/TRADE_ADAPTER.md` 7.1). A rotated or
truncated ledger pays every old trade again; a rewritten line changes a trade
already paid for. So `ledger.py` has no rotate, no truncate and no rewrite
function to call, and `open_for_append` takes no mode argument. A torn last line
is tolerated by the game; each write here is one `write()` of one complete line
plus `fsync`, so tearing needs a death inside a single syscall.

**Paper only.** The endpoint is fixed to `https://paper-api.alpaca.markets` and
`--endpoint` refuses anything else. There is deliberately no flag that reaches
live trading — a flag that exists gets passed one day.

**Keys live in the environment.** `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`
are read from `os.environ` only. They are never accepted as arguments (an
argument lands in shell history and in a process list), never logged, and never
written anywhere in this repository. `--check-keys` reports only whether they
are *set*.

## What is not built

`run_live` refuses, and that refusal is the honest state rather than a stub.
`Docs/TRADE_ADAPTER.md` section 8 has four questions the owner has not answered:
position size, what "successful" means, the credit and bonus numbers, and where
a bonus lands. A live path built past them would be inventing those answers in
code — and the game pays out against the ledger it writes. The mock strategy
exists so the adapter, the ledger and the game can be exercised end to end
without a market, an account or a key; it is not a proposed strategy and is
tuned toward nothing.
