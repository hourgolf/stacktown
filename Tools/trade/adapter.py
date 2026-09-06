"""The trade adapter: a separate process that writes a ledger the game reads.

Docs/TRADE_ADAPTER.md. This process and the game share ONE thing, a file:

    adapter  --append-->  Saved/Stacktown/trade_ledger.jsonl  --read-->  game

THE GAME NEVER PLACES AN ORDER, and this adapter never touches the game. It does
not import anything from Content/Python, it does not open citystate.json, and it
has no idea a game exists. That boundary is the whole design: the game consumes
outcomes.

KEYS LIVE IN THE ENVIRONMENT AND NOWHERE ELSE. APCA_API_KEY_ID and
APCA_API_SECRET_KEY are read from os.environ, never taken as arguments (an
argument lands in shell history and in a process list), never logged, never
written to any file this program creates. --check-keys reports only whether they
are SET.

PAPER ONLY, enforced rather than documented: the endpoint is fixed to Alpaca's
paper host and --endpoint refuses anything else. There is no flag that reaches
live trading, because a flag that exists gets passed one day.

    python3 Tools/trade/adapter.py --mock --count 10
    python3 Tools/trade/adapter.py --mock --loop --interval 5
    python3 Tools/trade/adapter.py --check-keys
    python3 Tools/trade/adapter.py --selftest
"""
import argparse
import datetime
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ledger    # noqa: E402
import strategy  # noqa: E402

#: Alpaca PAPER. Not configurable - see the module docstring.
PAPER_ENDPOINT = 'https://paper-api.alpaca.markets'

KEY_ID_VAR = 'APCA_API_KEY_ID'
SECRET_VAR = 'APCA_API_SECRET_KEY'

PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def keys_present():
    """(key_id_set, secret_set). Reports PRESENCE only - never the values."""
    return bool(os.environ.get(KEY_ID_VAR)), bool(os.environ.get(SECRET_VAR))


def require_paper(endpoint):
    """The only endpoint this program will talk to.

    Refuses rather than warns. An adapter that could be pointed at live trading
    by a flag is one flag away from doing it, and no part of this project has
    any business placing a real order."""
    if endpoint != PAPER_ENDPOINT:
        raise SystemExit(
            'refusing: this adapter is paper-only and the endpoint is fixed to\n'
            '  %s\ngot: %s' % (PAPER_ENDPOINT, endpoint))
    return endpoint


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat().replace('+00:00', 'Z')


def run_mock(path, count, seed, win_rate, ticker, interval=0.0, quiet=False):
    """Append `count` mock closed trades. Returns how many were written."""
    s = strategy.MockStrategy(ticker=ticker, seed=seed, win_rate=win_rate)
    written = 0
    for _ in range(count):
        trade = s.next_closed_trade(now_iso())
        ledger.append_trade(path, trade)
        written += 1
        if not quiet:
            # pnl only. A ledger line is the record; stdout is for watching.
            print('appended %s pnl %+.2f' % (trade['trade_id'], trade['pnl']))
        if interval:
            time.sleep(interval)
    return written


def run_live(path, args):
    """The real path, once the owner's Pine script and answers arrive.

    NOT IMPLEMENTED, and refusing is the honest state: TRADE_ADAPTER.md 8 has
    four open questions the owner has not answered - position size, what
    "successful" means, the credit and bonus numbers, and where the bonus lands.
    A live path built past them would be inventing those answers in code, and
    the ledger it wrote would be paid out against by the game."""
    key_id, secret = keys_present()
    raise SystemExit(
        'live strategy not implemented.\n'
        '  endpoint : %s (paper, fixed)\n'
        '  %s : %s\n  %s : %s\n'
        'Waiting on TRADE_ADAPTER.md section 8: position size, what "successful"\n'
        'means, the credit/bonus numbers, and where the bonus lands. Use --mock.'
        % (require_paper(args.endpoint), KEY_ID_VAR, 'set' if key_id else 'NOT SET',
           SECRET_VAR, 'set' if secret else 'NOT SET'))


def selftest():
    import json
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix='stacktown-adapter-')
    try:
        path = ledger.default_path(tmp)

        # 1. the mock path appends and the count is what the game will read
        n = run_mock(path, count=10, seed=5, win_rate=0.5, ticker='MOCK', quiet=True)
        assert n == 10
        assert ledger.line_count(path) == 10

        # 2. A SECOND RUN APPENDS, it does not replace. This is the property the
        #    game's line-count cursor lives on.
        run_mock(path, count=5, seed=6, win_rate=0.5, ticker='MOCK', quiet=True)
        assert ledger.line_count(path) == 15, ledger.line_count(path)

        # 3. every line carries a numeric pnl - the one field the game reads
        trades, torn = ledger.read_trades(path)
        assert not torn
        for t in trades:
            assert isinstance(t['pnl'], (int, float)), t
            json.dumps(t)

        # 4. the endpoint cannot be moved off paper
        require_paper(PAPER_ENDPOINT)
        for bad in ('https://api.alpaca.markets', 'http://localhost:9999', ''):
            try:
                require_paper(bad)
                raise AssertionError('endpoint %r must be refused' % bad)
            except SystemExit:
                pass

        # 5. key reporting says only whether they are SET, never what they are
        os.environ[KEY_ID_VAR] = 'not-a-real-key'
        try:
            assert keys_present()[0] is True
            out = '%s %s' % keys_present()
            assert 'not-a-real-key' not in out
        finally:
            del os.environ[KEY_ID_VAR]

        # 6. the live path refuses rather than inventing the owner's answers
        args = argparse.Namespace(endpoint=PAPER_ENDPOINT)
        try:
            run_live(path, args)
            raise AssertionError('the live path must refuse')
        except SystemExit as e:
            assert 'not implemented' in str(e)

        print('adapter self-check: 6/6 pass (mock appends and a second run '
              'appends rather than replacing, which is what the game\'s '
              'line-count cursor lives on; every line carries a numeric pnl; '
              'the endpoint cannot be moved off paper; key reporting says only '
              'whether a key is SET; the live path refuses rather than '
              'inventing the owner\'s four open answers)')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--ledger', default=None,
                   help='ledger path (default: Saved/Stacktown/trade_ledger.jsonl '
                        'under this project - point it at a packaged app\'s own '
                        'Saved/Stacktown to feed that game instead)')
    p.add_argument('--mock', action='store_true', help='use the mock strategy')
    p.add_argument('--count', type=int, default=1, help='trades to append per pass')
    p.add_argument('--loop', action='store_true', help='keep going until interrupted')
    p.add_argument('--interval', type=float, default=2.0, help='seconds between passes')
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--win-rate', type=float, default=0.5)
    p.add_argument('--ticker', default='MOCK')
    p.add_argument('--endpoint', default=PAPER_ENDPOINT,
                   help='paper only; anything else is refused')
    p.add_argument('--check-keys', action='store_true',
                   help='report whether the API keys are set (never their values)')
    p.add_argument('--selftest', action='store_true')
    args = p.parse_args(argv)

    if args.selftest:
        selftest()
        return 0

    if args.check_keys:
        key_id, secret = keys_present()
        print('%s : %s' % (KEY_ID_VAR, 'set' if key_id else 'NOT SET'))
        print('%s : %s' % (SECRET_VAR, 'set' if secret else 'NOT SET'))
        print('endpoint  : %s (paper, fixed)' % PAPER_ENDPOINT)
        print('keys are read from the environment only and are never written '
              'anywhere in this repository.')
        return 0 if (key_id and secret) else 1

    path = args.ledger or ledger.default_path(PROJECT_ROOT)
    if not args.mock:
        return run_live(path, args)

    require_paper(args.endpoint)
    print('appending to %s' % path)
    if not args.loop:
        run_mock(path, args.count, args.seed, args.win_rate, args.ticker)
        return 0
    try:
        while True:
            run_mock(path, args.count, args.seed, args.win_rate, args.ticker)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nstopped. %d lines in the ledger.' % ledger.line_count(path))
    return 0


if __name__ == '__main__':
    sys.exit(main())
