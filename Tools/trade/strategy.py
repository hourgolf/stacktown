"""The mock strategy, standing in until the owner's Pine script arrives.

It exists so the adapter, the ledger and the game can be exercised end to end
without a market, an account or a key. It is NOT a proposed strategy and is not
tuned toward any feel - Docs/TRADE_ADAPTER.md 8.1 (position size) and 8.3 (the
credit and bonus numbers) are open questions the owner has not answered, and
inventing answers here would put placeholder numbers into a ledger the game pays
out against.

DETERMINISTIC BY SEED, so a run can be replayed. A mock that produced different
trades every run would make the game's idempotency impossible to check: the
whole point of a second read counting zero is that the file did not change.

Self-test:  python3 Tools/trade/strategy.py
"""
import random


class MockStrategy:
    """Closed trades with a declared win rate. Never places an order anywhere."""

    def __init__(self, ticker='MOCK', seed=1, win_rate=0.5,
                 size=1, price=100.0, magnitude=5.0):
        if not 0.0 <= win_rate <= 1.0:
            raise ValueError('win_rate must be between 0 and 1, got %r' % win_rate)
        self.ticker = ticker
        self.win_rate = win_rate
        self.size = size
        self.price = price
        self.magnitude = magnitude
        self._rng = random.Random(seed)
        self._n = 0

    def next_closed_trade(self, now_iso='2026-09-06T00:00:00Z'):
        """One closed trade. pnl is NEVER exactly zero.

        Breakeven does not count as a win (econrules.is_win: pnl > 0, breakeven
        deliberately excluded so a string of scratch trades cannot farm
        bonuses), so a mock that emitted zeros would be exercising the one
        outcome the reward rules are written to ignore."""
        self._n += 1
        win = self._rng.random() < self.win_rate
        pnl = self.magnitude if win else -self.magnitude
        exit_price = self.price + pnl
        return {
            'trade_id': 'MOCK-%06d' % self._n,
            'ticker': self.ticker,
            'side': 'long',
            'entry_time': now_iso,
            'entry_price': self.price,
            'exit_time': now_iso,
            'exit_price': exit_price,
            'size': self.size,
            'pnl': float(pnl),
        }


if __name__ == '__main__':
    # 1. deterministic by seed - the property the game's idempotency check needs.
    #    Draw from ONE strategy: a fresh one per call is always on its first
    #    draw, which made this pass for the wrong reason and then fail for the
    #    right one (two seeds whose first flip lands the same way).
    def draw(seed, n=20):
        s = MockStrategy(seed=seed)
        return [s.next_closed_trade() for _ in range(n)]

    a, b, c = draw(7), draw(7), draw(8)
    assert a == b, 'same seed must replay the same trades'
    assert [t['pnl'] for t in a] != [t['pnl'] for t in c], 'a different seed must differ'

    # 2. ids are unique and ordered - the ledger is a line-counted log
    ids = [t['trade_id'] for t in a]
    assert len(set(ids)) == len(ids), 'trade ids must be unique'
    assert ids == sorted(ids), 'trade ids must be ordered'

    # 3. NEVER breakeven: pnl == 0 is the one outcome is_win ignores
    assert all(t['pnl'] != 0.0 for t in a), 'a mock must not emit breakeven'

    # 4. the declared win rate is honoured, roughly
    s = MockStrategy(seed=3, win_rate=0.8)
    trades = [s.next_closed_trade() for _ in range(1000)]
    rate = sum(1 for t in trades if t['pnl'] > 0) / float(len(trades))
    assert 0.75 <= rate <= 0.85, rate

    # 5. an impossible win rate is refused rather than clamped
    for bad in (-0.1, 1.1):
        try:
            MockStrategy(win_rate=bad)
            raise AssertionError('win_rate %r must be refused' % bad)
        except ValueError:
            pass

    print('strategy self-check: 5/5 pass (deterministic by seed so a run can be '
          'replayed and the game\'s idempotency stays checkable; ids unique and '
          'ordered; never breakeven, which is the one outcome is_win ignores; '
          'declared win rate honoured; an impossible rate refused)')
