"""The trade ledger: append-only, forever.

Docs/TRADE_ADAPTER.md 7.1. The game's cursor is `trades_processed` in the city
state, and it is A LINE COUNT. That single fact decides everything in this file:

  * a ROTATED file pays every old trade again, because the count restarts;
  * a TRUNCATED file pays them again for the same reason;
  * a REWRITTEN line changes a trade the game has already paid for.

So this module can only append. There is deliberately no rotate, no truncate and
no rewrite function anywhere in it - not as a discipline to remember, but as
code that does not exist to be called. `open_for_append` refuses any mode but
'a', which is the one place a future edit would otherwise slip a 'w' in.

A TORN LAST LINE IS TOLERATED by the game (it skips a line it cannot parse), but
tolerated is not the same as fine: every write here is a single write() call of
one complete line including its newline, followed by flush and fsync, so a torn
line needs the process to die inside one syscall rather than merely between two.

Self-test:  python3 Tools/trade/ledger.py
"""
import json
import os

#: One closed trade per line. TRADE_ADAPTER.md's own schema; the game reads
#: 'pnl' and nothing else, but the rest is what makes a ledger auditable later.
FIELDS = ('trade_id', 'ticker', 'side', 'entry_time', 'entry_price',
          'exit_time', 'exit_price', 'size', 'pnl')


def default_path(project_root):
    """Saved/Stacktown/trade_ledger.jsonl under the project the game reads.

    A packaged app has its own Saved/Stacktown; the adapter is pointed at
    whichever one the game it feeds is using, and never guesses between them."""
    return os.path.join(project_root, 'Saved', 'Stacktown', 'trade_ledger.jsonl')


def open_for_append(path):
    """The ONLY way this module opens the ledger.

    Refuses to be talked into any other mode. The whole contract is that this
    file is append-only forever, and 'w' anywhere in this module would be the
    edit that silently breaks it - so there is no parameter to pass one."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'a')


def append_trade(path, trade):
    """Append one closed trade. Returns the line written.

    ONE write() OF ONE COMPLETE LINE, then flush and fsync. The game tolerates a
    torn last line, but this makes tearing need a death inside a single syscall
    rather than between two of them."""
    missing = [f for f in FIELDS if f not in trade]
    if missing:
        raise ValueError('trade is missing %s' % ', '.join(missing))
    float(trade['pnl'])          # the one field the game reads: fail here, loudly
    line = json.dumps(trade, sort_keys=True) + '\n'
    with open_for_append(path) as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
    return line


def read_trades(path, tolerate_torn_last_line=True):
    """(trades, torn) - what the game would see.

    Present so the adapter can VERIFY what it wrote without a second parser
    disagreeing with the game's. A torn last line is skipped and reported, never
    counted; a torn line anywhere EARLIER is a corrupt ledger and raises, since
    the cursor is a line count and skipping a middle line would shift every
    trade after it."""
    if not os.path.exists(path):
        return [], False
    with open(path) as f:
        lines = f.read().split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    trades, torn = [], False
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            trades.append(json.loads(line))
        except ValueError:
            is_last = (i == len(lines) - 1)
            if is_last and tolerate_torn_last_line:
                torn = True
                continue
            raise ValueError(
                'corrupt ledger line %d of %d - a middle line cannot be skipped, '
                'the game counts lines' % (i + 1, len(lines)))
    return trades, torn


def line_count(path):
    """What the game's cursor is counting against."""
    trades, _torn = read_trades(path)
    return len(trades)


if __name__ == '__main__':
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix='stacktown-ledger-')
    try:
        p = os.path.join(tmp, 'Saved', 'Stacktown', 'trade_ledger.jsonl')

        def mk(i, pnl):
            return {'trade_id': 'T%d' % i, 'ticker': 'MOCK', 'side': 'long',
                    'entry_time': '2026-09-06T10:00:00Z', 'entry_price': 100.0,
                    'exit_time': '2026-09-06T10:05:00Z', 'exit_price': 100.0 + pnl,
                    'size': 1, 'pnl': pnl}

        # 1. appends accumulate, and the count is what the game's cursor reads
        for i in range(10):
            append_trade(p, mk(i, 1.0 if i % 2 == 0 else -1.0))
        trades, torn = read_trades(p)
        assert len(trades) == 10, len(trades)
        assert not torn
        assert line_count(p) == 10

        # 2. APPENDING NEVER REWRITES. The first line after ten more appends is
        #    still the first trade - this is the property the game's cursor
        #    depends on, so it is asserted rather than assumed.
        first_before = trades[0]
        for i in range(10, 20):
            append_trade(p, mk(i, 2.0))
        trades2, _ = read_trades(p)
        assert len(trades2) == 20, len(trades2)
        assert trades2[0] == first_before, (trades2[0], first_before)
        assert trades2[:10] == trades, 'appending changed an earlier line'

        # 3. a torn last line is tolerated and reported, never counted
        with open(p, 'a') as f:
            f.write('{"trade_id": "T20", "pn')     # died mid-write
        trades3, torn3 = read_trades(p)
        assert len(trades3) == 20, len(trades3)
        assert torn3 is True

        # 4. a torn line in the MIDDLE is not skippable: the cursor is a line
        #    count, so skipping one would shift every trade after it
        q = os.path.join(tmp, 'mid.jsonl')
        with open(q, 'a') as f:
            f.write(json.dumps(mk(0, 1.0)) + '\n')
            f.write('{ broken\n')
            f.write(json.dumps(mk(1, 1.0)) + '\n')
        try:
            read_trades(q)
            raise AssertionError('a corrupt middle line must raise')
        except ValueError as e:
            assert 'cannot be skipped' in str(e), str(e)

        # 5. a trade with no pnl is refused HERE, not silently written for the
        #    game to trip over
        bad = mk(99, 0.0)
        del bad['pnl']
        try:
            append_trade(p, bad)
            raise AssertionError('a trade with no pnl must be refused')
        except ValueError as e:
            assert 'pnl' in str(e)

        # 6. there is no way to open this file for writing
        try:
            open_for_append(p, 'w')          # noqa - deliberately wrong
            raise AssertionError('open_for_append must take no mode')
        except TypeError:
            pass

        print('ledger self-check: 6/6 pass (append-only by construction; '
              'appends never rewrite an earlier line, which is what the game\'s '
              'line-count cursor depends on; a torn LAST line is tolerated and '
              'reported, a torn MIDDLE line raises because skipping it would '
              'shift every trade after it; a trade with no pnl is refused '
              'before it reaches the file)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
