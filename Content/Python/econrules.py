"""Placeholder economy ruleset v0 — SCAFFOLDING, not design.

The beta twin's tick rules (Docs/BETA_TWIN_PLAN.md): buy parcels,
collect rent per CityTick, one global demand dial. Every number here is
a placeholder awaiting the owner's economy notes; the MACHINERY
(per-recipe ladders, loud growth blocks, fresh-read constants) is the
part that survives their arrival.

GROWTH RETIRED FROM tick() 2026-09-03 — the owner's own word, watching
a balance hit 312k in one session at automatic pacing: "their growth is
supposed to be a factor of game performance (trading success/failure)
and user initiated upgrades/modifications." tick() now ONLY accrues
rent; a tier changes exclusively via upgrade() below, player-initiated
and priced, never a threshold crossing on its own. This is a genuine
retirement, not a flag: the growth_threshold-driven branch is gone from
tick(), not gated off — econrules.json's own growth_threshold value is
left in place (unread by anything now) rather than deleted, since
removing a JSON key is a bigger, more consequential call than this
pass's own scope.

Design constraints honoured:
  - CONSTANTS LIVE IN econrules.json AND ARE READ FRESH each call site
    that ticks. Not module-level: this machine's bytecode cache lives
    outside the repo and serves stale code on same-size same-second
    edits (HANDOFF traps) - ruleset tuning is exactly that edit
    pattern, so the hot numbers bypass import entirely.
  - LADDERS ARE PER-RECIPE, read from recipes.tier_count - the office
    has FOUR deliberately larger tiers, the catalogue six; nothing here
    assumes uniformity (BETA_TWIN_PLAN seam 5).
  - A tier-up whose asset is not baked BLOCKS LOUDLY with a reason -
    never a silent null-mesh resolve (the S17 scar, applied forward).
    tier_up_allowed still enforces this; only its CALLER moved, from
    tick() to upgrade() - the constraint was never about automation.
  - Pure module: no unreal, no editor, self-tested with hand-computed
    known answers.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# 2026-09-06: the rules file lives under Content/Stacktown/Rules, staged into a
# packaged app as a UFS file (Config/ subfolders are not staged; Content/Python
# cannot cook). One copy, read by the Python oracle and by the C++ economy.
RULES_PATH = os.path.normpath(os.path.join(HERE, '..', 'Stacktown', 'Rules', 'econrules.json'))
BAKED_DIR = os.path.normpath(os.path.join(
    HERE, '..', 'Stacktown', 'Baked'))

import recipes  # ladder lengths + asset names come from the catalogue


def rules():
    """The constants, read fresh from JSON every call. See docstring."""
    with open(RULES_PATH) as f:
        return json.load(f)


def asset_exists(rid, tier, width, baked_dir=BAKED_DIR):
    name = recipes.asset_name(rid, int(tier), float(width))
    return os.path.exists(os.path.join(baked_dir, name + '.uasset'))


def recipe_mult(rid, which, r=None):
    """2026-09-06 night (NIGHT_PLAN.md, working defaults): a recipe is a TYPE
    that behaves differently - office and tower cost more and earn more than
    vernacular. Unknown recipes are vernacular (1.0). 'which' is 'price' or
    'rent'."""
    r = r or rules()
    return float(r.get('recipe_mult', {}).get(rid, {}).get(which, 1.0))


def price(rid, tier, width, r=None):
    r = r or rules()
    return (r['price_base'] + r['price_per_100uu'] * (float(width) / 100.0)
            + r['price_per_tier'] * int(tier)) * recipe_mult(rid, 'price', r)


def rent(rid, tier, demand, r=None):
    r = r or rules()
    return r['rent_per_tier'] * (int(tier) + 1) * float(demand) * recipe_mult(rid, 'rent', r)


def tier_up_allowed(rid, tier, width, baked_dir=BAKED_DIR):
    """(ok, reason). Loud about every distinct refusal."""
    nxt = int(tier) + 1
    if nxt >= recipes.tier_count(rid):
        return False, 'top of ladder (%s has %d tiers)' % (
            rid, recipes.tier_count(rid))
    if not asset_exists(rid, nxt, width, baked_dir):
        return False, 'GROWTH BLOCKED: %s not baked' % \
            recipes.asset_name(rid, nxt, float(width))
    return True, ''


def tick(state):
    """One CityTick. state = {'money': float, 'demand': float,
    'parcels': {pid: {'rid','tier','width','owned','accum','wear',...}}}.
    Returns (new_state, events). A lot's tier NEVER changes here (growth
    retired, D20). Since 2026-09-06 night (NIGHT_PLAN.md, working
    defaults) three things move:
      RENT   - every owned, un-failed lot earns rent at the demand the tick
               STARTED with; a failed lot earns nothing until repaired.
      WEAR   - every owned, un-failed lot wears by 1 per tick; at
               wear_ticks_per_tier x (tier+1) it WEARS OUT: failed=True,
               event {'type': 'worn_out', 'pid': pid}. Wear resets on buy,
               upgrade and repair. 150 ticks per tier is the patina's own
               maturity constant (init_unreal: AGE_MATURE_TICKS), so a lot
               wears out as its patina completes - a long-loved block is
               old and then it needs a hand again.
      DEMAND - moves toward demand_default + demand_gain x owned lots
               - demand_loss x for-sale lots, by demand_rate of the gap per
               tick, clamped to [demand_min, demand_max]. Owning raises it,
               leaving pads unbought lowers it; Price and rent follow.
    Pure - caller owns persistence."""
    r = rules()
    s = json.loads(json.dumps(state))   # defensive copy, JSON-clean
    events = []
    demand = float(s['demand'])
    owned = 0
    for_sale = 0
    for pid, p in sorted(s['parcels'].items()):
        if not p.get('owned'):
            for_sale += 1
            continue
        owned += 1
        if p.get('failed'):
            continue
        earned = rent(p['rid'], p['tier'], demand, r)
        s['money'] += earned
        p['accum'] = p.get('accum', 0.0) + earned
        p['wear'] = p.get('wear', 0) + 1
        if p['wear'] >= r['wear_ticks_per_tier'] * (int(p['tier']) + 1):
            p['failed'] = True
            events.append({'type': 'worn_out', 'pid': pid, 'amount': 0.0})
    target = r['demand_default'] + r['demand_gain'] * owned - r['demand_loss'] * for_sale
    demand = demand + r['demand_rate'] * (target - demand)
    demand = min(r['demand_max'], max(r['demand_min'], demand))
    s['demand'] = demand
    return s, events


def buy(state, pid):
    """(new_state, ok, reason)."""
    r = rules()
    s = json.loads(json.dumps(state))
    p = s['parcels'].get(pid)
    if p is None:
        return s, False, 'no such parcel'
    if p.get('owned'):
        return s, False, 'already owned'
    cost = price(p['rid'], p['tier'], p['width'], r)
    if s['money'] < cost:
        return s, False, 'insufficient funds (%.0f < %.0f)' % (
            s['money'], cost)
    s['money'] -= cost
    p['owned'] = True
    p['accum'] = 0.0
    p['wear'] = 0
    p['failed'] = False
    return s, True, ''


# PERFORMANCE (task D, 2026-09-03): a per-lot value, -1.0 (worst) to
# +1.0 (best), 0.0 NEUTRAL - the same shape cpdmap.py already uses for
# Attention (a per-instance scalar around a neutral default), reused
# here rather than inventing a second convention for the same kind of
# value. Read by premium() below. Written by NOTHING yet (owner's
# ruling (2): "performance = PLAYER TRADES ONLY - no automatic score,
# changed by nothing until a trading system exists") - every lot sits
# at this default until that system exists to move it.
PERFORMANCE_NEUTRAL = 0.0


def climb(tier):
    """Upgrade cost multiplier that CLIMBS with each level - the
    owner's own word, 2026-09-03. Linear in the tier being climbed
    FROM: upgrading a tier-3 lot costs 4x what a tier-0 lot's own first
    upgrade costs. A curve, not just a bigger flat price, is the one
    thing the owner's word actually requires - the exact shape is a
    placeholder like every other number in this file (module
    docstring), pending the owner's real economy notes."""
    return int(tier) + 1


def premium(performance):
    """Upgrade cost multiplier from a lot's own performance. Owner's
    ruling (3), 2026-09-03: poor performance costs more, and NEVER
    blocks - upgrade() below refuses only on affordability and the
    ladder/baked checks, never on performance by itself. Always >= 1.0:
    1.0 at PERFORMANCE_NEUTRAL or better, climbing to 2.0 at the worst
    (-1.0). No discount is claimed for good performance - the owner
    named only a penalty for poor performance, nothing about a bonus
    for good, so this does not invent one."""
    return 1.0 + max(0.0, -float(performance))


def upgrade_price(rid, tier, performance, r=None):
    r = r or rules()
    return r['price_base'] * climb(tier) * premium(performance)


def upgrade(state, pid):
    """(new_state, ok, reason). Player-initiated, priced - since
    2026-09-03 the ONLY way a lot's tier advances at all (tick() no
    longer does; see its own docstring). Same ladder-top/not-baked
    checks tick() used to make automatically are made HERE instead,
    since a lot still cannot show a mesh that was never baked - the
    constraint never went away, only its trigger did. Refuses on an
    unrepaired failure (ruling (4): pay to repair first) and on
    affordability, priced by upgrade_price() (climb x premium) - never
    on performance alone, per ruling (3).

    DOES NOT touch age_ticks. That field lives OUTSIDE this module's
    state schema entirely (ECONOMY_TICK_CONTRACT.md, "Patina's Age
    channel": tracked and persisted by init_unreal._sync_parcels
    directly, never by econrules.py/citytick.py - the same boundary
    that already keeps tick()'s own known-answer self-tests asserting
    exact state equality without a side field breaking them). B3's
    reset-on-upgrade ("New/upgraded buildings start pale...") is the
    DRIVER's job when UpgradeRequestPID is wired, exactly parallel to
    how it already resets on tick()-driven tier-ups today - NOT
    verified here whether that existing reset logic keys off tier
    changing at all (generic) or specifically off tick() causing it
    (narrow); flagged for whoever wires the driver side, not assumed
    either way."""
    r = rules()
    s = json.loads(json.dumps(state))
    p = s['parcels'].get(pid)
    if p is None:
        return s, False, 'no such parcel'
    if not p.get('owned'):
        return s, False, 'not owned'
    if p.get('failed'):
        return s, False, 'failed: repair before upgrading'
    ok_ladder, reason_ladder = tier_up_allowed(p['rid'], p['tier'], p['width'])
    if not ok_ladder:
        return s, False, reason_ladder
    cost = upgrade_price(p['rid'], int(p['tier']),
                          p.get('performance', PERFORMANCE_NEUTRAL), r)
    if s['money'] < cost:
        return s, False, 'insufficient funds (%.0f < %.0f)' % (
            s['money'], cost)
    s['money'] -= cost
    p['tier'] = int(p['tier']) + 1
    p['wear'] = 0
    return s, True, ''


def repair_price(tier, r=None):
    r = r or rules()
    return r['price_base'] * (int(tier) + 1)


def repair(state, pid):
    """(new_state, ok, reason). Owner's ruling (4), 2026-09-03: failure
    = PAY TO REPAIR. Clears the 'failed' flag on success. Nothing SETS
    that flag yet (ruling (2): performance is player-trades-only and no
    trading system exists yet to fail a lot) - this is unreachable in
    real play today, built and self-tested ahead of what will drive it,
    the same "declare before it's driven" discipline this file already
    holds constants to."""
    r = rules()
    s = json.loads(json.dumps(state))
    p = s['parcels'].get(pid)
    if p is None:
        return s, False, 'no such parcel'
    if not p.get('owned'):
        return s, False, 'not owned'
    if not p.get('failed'):
        return s, False, 'not failed'
    cost = repair_price(p['tier'], r)
    if s['money'] < cost:
        return s, False, 'insufficient funds (%.0f < %.0f)' % (
            s['money'], cost)
    s['money'] -= cost
    p['failed'] = False
    p['wear'] = 0
    return s, True, ''


# TRADE LEDGER REWARDS (2026-09-04, Docs/TRADE_ADAPTER.md - the owner's
# own definition of a trade, ECONOMY_TICK_CONTRACT.md "What a trade
# is"). This module NEVER places an order and NEVER touches Alpaca,
# credentials, or market data - it only reads an already-written ledger
# of CLOSED trades (the trade adapter's own output, a separate process
# entirely) and converts new entries into game value. "The game never
# places orders; it consumes outcomes" - that boundary is the whole
# reason this lives here rather than anywhere near the adapter.
#
# A ledger entry is {'trade_id', 'ticker', 'side', 'entry_time',
# 'entry_price', 'exit_time', 'exit_price', 'size', 'pnl'} -
# TRADE_ADAPTER.md's own schema, this module only ever reads 'pnl'.
#
# TWO of the owner's own three unknowns are placeholder constants below
# (trade_credits_per_n, trade_credit_amount, trade_bonus_per_win) -
# scaffolding, same discipline as every other number in this file. The
# THIRD - what "successful" means - is a CHOICE this module makes
# explicit and overridable (is_win below), not a constant, because the
# owner's own question ("closed profit?") is about the DEFINITION, not
# a tunable number: closed-profit (pnl > 0) is the proposed default,
# named as a default, not asserted as final.
def is_win(trade):
    """A trade counts as a WIN if it closed with pnl > 0 - the proposed
    default for the owner's own open question ("what does 'successful'
    mean - closed profit?"), not a final answer. Breakeven (pnl == 0)
    does NOT count - deliberately, so a string of scratch trades can't
    farm bonuses; the owner may want a different bar (net of
    commissions, some minimum size) once the adapter is real."""
    return float(trade['pnl']) > 0.0


def trade_count_reward(trades_before, new_trade_count, credits_per_n, credit_amount):
    """Total credits earned by new_trade_count MORE closed trades
    landing on top of trades_before already counted - regardless of
    outcome (the owner's own word). Counts N-trade MILESTONES crossed,
    not trades individually, so a credits_per_n=10 lot pays out once at
    the 10th, 20th, 30th... closed trade, never per-trade. Pure
    arithmetic, no state - the caller (apply_trade_ledger below) owns
    what "trades_before" means."""
    before_milestones = trades_before // credits_per_n
    after_milestones = (trades_before + new_trade_count) // credits_per_n
    return (after_milestones - before_milestones) * credit_amount


def trade_outcome_bonus(new_trades, bonus_per_win):
    """Total bonus across new_trades for whichever ones is_win() calls a
    win - every winning trade pays the same flat bonus (escalating it
    by size/P&L is exactly the "factors we will still need to work out"
    the owner's own words left open, not decided here)."""
    return sum(bonus_per_win for t in new_trades if is_win(t))


def apply_trade_ledger(state, ledger_entries, r=None):
    """(new_state, events). The ONLY function in this module that reads
    a trade ledger. IDEMPOTENT BY CONSTRUCTION: state['trades_processed']
    (new top-level field, default 0, NOT per-parcel) is how many leading
    ledger_entries have already been counted - only entries beyond that
    index are ever read, so calling this again with the same or a
    longer ledger never double-counts a trade, even across a session
    restart (trades_processed persists in citystate.json like every
    other field). Awards land as MONEY today - both a count reward
    (every credits_per_n closed trades) and an outcome bonus (every
    is_win() trade) - the simplest concrete thing that is definitely
    correct given the owner's own "so they can upgrade regardless of
    the success of those trades" framing. Whether "bonus toward
    upgrades" should instead move a lot's own 'performance' value, or
    something else "escalation factors... still to be worked out" might
    want, is the owner's own open question (ECONOMY_TICK_CONTRACT.md,
    "What a trade is") - not decided here; this function computes the
    reward, it does not commit to its final application.

    events is a list of ('TRADE_CREDITS', amount) / ('TRADE_BONUS',
    amount) tuples, present only when the respective amount is nonzero
    - mirrors tick()'s own event shape (a list of tuples, empty when
    nothing happened) rather than inventing a new return convention."""
    r = r or rules()
    s = json.loads(json.dumps(state))
    processed = s.get('trades_processed', 0)
    new_trades = ledger_entries[processed:]
    if not new_trades:
        return s, []
    credits = trade_count_reward(
        processed, len(new_trades),
        r['trade_credits_per_n'], r['trade_credit_amount'])
    bonus = trade_outcome_bonus(new_trades, r['trade_bonus_per_win'])
    s['money'] += credits + bonus
    s['trades_processed'] = processed + len(new_trades)
    events = []
    if credits:
        events.append(('TRADE_CREDITS', credits))
    if bonus:
        events.append(('TRADE_BONUS', bonus))
    return s, events


if __name__ == '__main__':
    # KNOWN ANSWERS, hand-computed from econrules.json's shipped values:
    # price_base 50, price_per_100uu 2, price_per_tier 25,
    # rent_per_tier 0.75, growth_threshold 40 (unread), demand 1.0.
    # rent_per_tier RETUNED 2026-09-03 (ECONOMY_TICK_CONTRACT.md, "Rent
    # cadence proposal", owner-approved via the coordinator: 10 -> 0.75)
    # - the owner's "substantially slower" word, and with growth already
    # retired from tick() (part A above), rent was the ENTIRE remaining
    # source of the 312k-in-one-session runaway. Every known answer below
    # that depends on rent_per_tier is recomputed WITH the new value, not
    # left stale - upgrade()/repair() are UNAFFECTED (priced off
    # price_base/tier/performance, never rent_per_tier), so their own
    # tests below are untouched.
    r = rules()
    assert (r['price_base'], r['price_per_100uu'], r['price_per_tier'],
            r['rent_per_tier'], r['growth_threshold']) == (50, 2, 25, 0.75, 40), \
        'json changed - recompute the known answers below WITH it'
    # 1. price: vernacular t0 w1230 = 50 + 2*12.3 + 0 = 74.6
    assert abs(price('vernacular', 0, 1230) - 74.6) < 1e-9
    # 2. rent: t2 at demand 2.0 = 0.75*3*2 = 4.5
    assert abs(rent('vernacular', 2, 2.0) - 4.5) < 1e-9
    # 3. buy then tick, REWORKED 2026-09-03 (growth retired from tick(),
    #    RETUNED 2026-09-03 for the new rent_per_tier): money 100, buy t0
    #    w1230 (74.6), left 25.4; 10 ticks of rent 0.75 each accrue into
    #    money AND accum, tier never moves. Hand-walked: money = 25.4 +
    #    10*0.75 = 32.9, accum = 0 + 10*0.75 = 7.5, tier stays 0, zero
    #    events across all 10 ticks.
    st = {'money': 100.0, 'demand': 1.0, 'parcels': {
        'P1': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
               'owned': False, 'accum': 0.0}}}
    st, ok, why = buy(st, 'P1')
    assert ok, why
    assert abs(st['money'] - 25.4) < 1e-9
    evs = []
    for _ in range(10):
        st, e = tick(st)
        evs += e
    #    RE-WALKED 2026-09-06 night (demand moves, NIGHT_PLAN.md): one owned
    #    lot, none for sale -> target 1.05; d_0 = 1.0, d_{k+1} = d_k +
    #    0.1 (1.05 - d_k), so d_k = 1.05 - 0.05 x 0.9^k and rent at tick k
    #    is 0.75 d_k (the demand the tick STARTED with). Closed form, not
    #    the loop's own arithmetic:
    sum_d = 10 * 1.05 - 0.05 * (1 - 0.9 ** 10) / (1 - 0.9)
    assert abs(st['money'] - (25.4 + 0.75 * sum_d)) < 1e-9, st['money']
    assert abs(st['parcels']['P1']['accum'] - 0.75 * sum_d) < 1e-9, st['parcels']['P1']
    assert abs(st['demand'] - (1.05 - 0.05 * 0.9 ** 10)) < 1e-9, st['demand']
    assert st['parcels']['P1']['wear'] == 10, st['parcels']['P1']
    assert st['parcels']['P1']['tier'] == 0, st['parcels']['P1']
    assert evs == [], evs
    # 4. LADDERS ARE PER-RECIPE: office tops out at tier 3 (4 tiers).
    #    tier_up_allowed itself is UNCHANGED and UNRETIRED - only tick()
    #    stopped calling it; upgrade() below calls it instead.
    ok, why = tier_up_allowed('office', 3, 2050)
    assert not ok and 'top of ladder' in why and '4 tiers' in why
    # 5. GROWTH BLOCKS LOUDLY: office t0 -> t1 is declared but NOT baked
    #    (only t0 exists at w2050 today). If this assert ever fails
    #    because t1 got baked, replace with a synthetic missing asset -
    #    instrument hygiene, per protocol.
    ok, why = tier_up_allowed('office', 0, 2050)
    assert not ok and 'GROWTH BLOCKED' in why and 'office_t1' in why, why
    # 6. REWORKED 2026-09-03: this used to prove a blocked parcel emits
    #    GROWTH_BLOCKED and does not advance. It now proves the sharper
    #    claim retirement makes - tick() does NOTHING tier-related at
    #    all any more, even for the EXACT case (accum past the old
    #    threshold, next tier unbaked) that used to fire loudest: one
    #    tick just accrues rent (office t0, demand 1.0 -> earns 0.75,
    #    retuned same day), tier stays 0, events is empty.
    st2 = {'money': 0.0, 'demand': 1.0, 'parcels': {
        'OF': {'rid': 'office', 'tier': 0, 'width': 2050,
               'owned': True, 'accum': 39.9}}}
    st2, e2 = tick(st2)
    #    RE-WALKED 2026-09-06 night: an OFFICE earns 1.5x (recipe_mult):
    #    0.75 x 1.5 = 1.125; accum 39.9 + 1.125 = 41.025.
    assert abs(st2['money'] - 1.125) < 1e-9, st2['money']
    assert abs(st2['parcels']['OF']['accum'] - 41.025) < 1e-9, st2['parcels']['OF']
    assert abs(price('office', 0, 2050) - (50 + 41) * 1.6) < 1e-9, price('office', 0, 2050)
    assert abs(rent('tower', 2, 1.0) - 0.75 * 3 * 2.5) < 1e-9, rent('tower', 2, 1.0)
    assert abs(price('mystery', 0, 820) - 66.4) < 1e-9   # unknown recipe: vernacular
    assert st2['parcels']['OF']['tier'] == 0
    assert e2 == [], e2
    assert abs(st2['demand'] - 1.005) < 1e-9, st2['demand']   # one owned lot: one step toward 1.05
    # 7. insufficient funds refuses loudly
    st3 = {'money': 1.0, 'demand': 1.0, 'parcels': {
        'P': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
              'owned': False}}}
    _, ok, why = buy(st3, 'P')
    assert not ok and 'insufficient funds' in why

    # 8. NEW 2026-09-03: a lot stays at its tier across 1000 ticks - the
    #    coordinator's own ask, proving retirement holds under real
    #    volume, not just a handful of ticks. vernacular t0 w1230, rent
    #    0.75/tick at demand 1.0 (retuned same day): after 1000 ticks
    #    money = accum = 750.0 exactly (started both at 0), tier still
    #    0, no event ever fired.
    st8 = {'money': 0.0, 'demand': 1.0, 'parcels': {
        'P1': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
               'owned': True, 'accum': 0.0}}}
    evs8 = []
    for _ in range(1000):
        st8, e = tick(st8)
        evs8 += e
    #    RE-WALKED 2026-09-06 night: the lot WEARS OUT on its 150th tick
    #    (wear_ticks_per_tier 150 x (tier 0 + 1)) and earns nothing after;
    #    the tier still never moves. Rent for ticks 0..149 at
    #    d_k = 1.05 - 0.05 x 0.9^k (one owned lot, no for-sale):
    sum_d150 = 150 * 1.05 - 0.05 * (1 - 0.9 ** 150) / (1 - 0.9)
    assert abs(st8['money'] - 0.75 * sum_d150) < 1e-6, st8['money']
    assert abs(st8['parcels']['P1']['accum'] - 0.75 * sum_d150) < 1e-6, \
        st8['parcels']['P1']
    assert st8['parcels']['P1']['tier'] == 0, st8['parcels']['P1']
    assert st8['parcels']['P1']['failed'] is True and st8['parcels']['P1']['wear'] == 150, st8['parcels']['P1']
    assert evs8 == [{'type': 'worn_out', 'pid': 'P1', 'amount': 0.0}], evs8
    # 8b. repair brings it back: pay repair_price(0) = 50, wear resets,
    #     rent flows again on the next tick at the demand the city holds.
    st8r, ok8, why8 = repair(st8, 'P1')
    assert ok8, why8
    assert st8r['parcels']['P1']['failed'] is False and st8r['parcels']['P1']['wear'] == 0
    assert abs(st8r['money'] - (st8['money'] - 50.0)) < 1e-9
    st8t, e8t = tick(st8r)
    assert abs(st8t['money'] - (st8r['money'] + 0.75 * st8r['demand'])) < 1e-9 and e8t == []
    # 8c. demand falls when pads sit unbought, and clamps at the rails.
    st8d = {'money': 0.0, 'demand': 1.0, 'parcels': {
        k: {'rid': 'vernacular', 'tier': 0, 'width': 1230, 'owned': False} for k in ('A', 'B', 'C')}}
    st8d, _ = tick(st8d)
    assert abs(st8d['demand'] - 0.985) < 1e-9, st8d['demand']   # target 0.85, one step of 0.1
    st8c = {'money': 0.0, 'demand': 1.99, 'parcels': {
        'P%d' % i: {'rid': 'vernacular', 'tier': 0, 'width': 1230, 'owned': True} for i in range(40)}}
    st8c, _ = tick(st8c)
    assert abs(st8c['demand'] - 2.0) < 1e-9, st8c['demand']     # target 3.0, clamped at demand_max

    # 9. climb/premium, direct - the two factors upgrade_price multiplies.
    assert climb(0) == 1 and climb(1) == 2 and climb(3) == 4
    assert abs(premium(PERFORMANCE_NEUTRAL) - 1.0) < 1e-9  # neutral: no surcharge
    assert abs(premium(1.0) - 1.0) < 1e-9   # best: still no DISCOUNT (owner named only a penalty)
    assert abs(premium(-0.5) - 1.5) < 1e-9  # halfway to worst: halfway surcharge
    assert abs(premium(-1.0) - 2.0) < 1e-9  # worst: double

    # 10. upgrade() pricing, happy path - vernacular t0 w1230, neutral
    #     performance (unset - upgrade() defaults via .get, PERFORMANCE_
    #     NEUTRAL): cost = price_base(50) * climb(0)=1 * premium(0)=1 = 50.
    #     Money 100 -> 50 after, tier 0 -> 1.
    st10 = {'money': 100.0, 'demand': 1.0, 'parcels': {
        'P1': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
               'owned': True, 'accum': 0.0}}}
    st10, ok10, why10 = upgrade(st10, 'P1')
    assert ok10, why10
    assert abs(st10['money'] - 50.0) < 1e-9, st10['money']
    assert st10['parcels']['P1']['tier'] == 1, st10['parcels']['P1']
    # CLIMB multiplies: same lot now at tier 1, upgrading again costs
    # price_base(50) * climb(1)=2 * premium(0)=1 = 100 - money is only
    # 50, so this refuses on affordability, proving the climb happened
    # (a flat re-use of 50 would have wrongly succeeded).
    st10b, ok10b, why10b = upgrade(st10, 'P1')
    assert not ok10b and 'insufficient funds' in why10b, (ok10b, why10b)
    # PREMIUM multiplies: a fresh tier-0 lot at the WORST performance
    # costs price_base(50) * climb(0)=1 * premium(-1.0)=2.0 = 100 -
    # exactly what a lot with money 100 can just afford.
    st10c = {'money': 100.0, 'demand': 1.0, 'parcels': {
        'P2': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
               'owned': True, 'accum': 0.0, 'performance': -1.0}}}
    st10c, ok10c, why10c = upgrade(st10c, 'P2')
    assert ok10c, why10c
    assert abs(st10c['money'] - 0.0) < 1e-9, st10c['money']
    assert st10c['parcels']['P2']['tier'] == 1

    # 11. upgrade() refusals - never a graph write, never anything but
    #     these named reasons, and NEVER performance alone (ruling (3):
    #     it surcharges, it does not gate - proven directly below).
    su = {'money': 1000.0, 'demand': 1.0, 'parcels': {
        'UNOWNED': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
                    'owned': False, 'accum': 0.0},
        'FAILED': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
                   'owned': True, 'accum': 0.0, 'failed': True},
        'TOPPED': {'rid': 'office', 'tier': 3, 'width': 2050,
                  'owned': True, 'accum': 0.0},
        'UNBAKED': {'rid': 'office', 'tier': 0, 'width': 2050,
                    'owned': True, 'accum': 0.0},
        'WORST': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
                  'owned': True, 'accum': 0.0, 'performance': -1.0},
    }}
    _, ok, why = upgrade(su, 'UNOWNED')
    assert not ok and why == 'not owned', why
    _, ok, why = upgrade(su, 'FAILED')
    assert not ok and 'repair' in why, why
    _, ok, why = upgrade(su, 'TOPPED')
    assert not ok and 'top of ladder' in why, why
    _, ok, why = upgrade(su, 'UNBAKED')
    assert not ok and 'GROWTH BLOCKED' in why, why
    # WORST performance, plenty of money (1000 >> 50*1*2.0=100): succeeds
    # anyway - performance surcharges, it never blocks, per ruling (3).
    su, ok, why = upgrade(su, 'WORST')
    assert ok, why
    assert su['parcels']['WORST']['tier'] == 1

    # 12. repair(), happy path - vernacular tier 1 (climbed above), failed
    #     manually set for this test: cost = price_base(50)*(tier(1)+1) =
    #     100. Money 150 -> 50 after, failed cleared.
    st12 = {'money': 150.0, 'demand': 1.0, 'parcels': {
        'P1': {'rid': 'vernacular', 'tier': 1, 'width': 1230,
               'owned': True, 'accum': 0.0, 'failed': True}}}
    st12, ok12, why12 = repair(st12, 'P1')
    assert ok12, why12
    assert abs(st12['money'] - 50.0) < 1e-9, st12['money']
    assert st12['parcels']['P1']['failed'] is False, st12['parcels']['P1']

    # 13. repair() refusals: not owned, not failed (the default, since
    #     ruling (2) means every real lot today), insufficient funds.
    sr = {'money': 1.0, 'demand': 1.0, 'parcels': {
        'UNOWNED': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
                    'owned': False, 'accum': 0.0},
        'FINE': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
                 'owned': True, 'accum': 0.0, 'failed': False},
        'POOR': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
                 'owned': True, 'accum': 0.0, 'failed': True},
    }}
    _, ok, why = repair(sr, 'UNOWNED')
    assert not ok and why == 'not owned', why
    _, ok, why = repair(sr, 'FINE')
    assert not ok and why == 'not failed', why
    _, ok, why = repair(sr, 'POOR')
    assert not ok and 'insufficient funds' in why, why

    # 14. is_win: closed profit only - the proposed default for the
    #     owner's own open question. Breakeven does NOT count.
    assert is_win({'pnl': 5.0}) is True
    assert is_win({'pnl': -3.0}) is False
    assert is_win({'pnl': 0.0}) is False

    # 15. trade_count_reward: milestone arithmetic, not per-trade -
    #     crossing exactly one N=10 milestone pays once regardless of
    #     how the count got there (0->10 in one call, or 9->10 in one
    #     trade), and NOT crossing one pays nothing.
    assert trade_count_reward(0, 10, 10, 20) == 20    # exactly to the line
    assert trade_count_reward(9, 1, 10, 20) == 20     # 9 -> 10, one trade
    assert trade_count_reward(5, 10, 10, 20) == 20    # 5 -> 15, crosses only 10
    assert trade_count_reward(0, 25, 10, 20) == 40    # 25 -> 2 milestones
    assert trade_count_reward(10, 0, 10, 20) == 0     # no new trades, no credit

    # 16. trade_outcome_bonus: sums bonus_per_win only across WINS.
    three = [{'pnl': 5.0}, {'pnl': -2.0}, {'pnl': 10.0}]
    assert trade_outcome_bonus(three, 5) == 10.0  # 2 of 3 win

    # 17. apply_trade_ledger, the full path, IDEMPOTENT BY CONSTRUCTION.
    #     12 closed trades, 6 wins (positions 1,3,5,8,10,12 - hand-
    #     counted, not assumed): crosses the credits_per_n=10 milestone
    #     once (20) plus 6 wins * bonus_per_win(5) = 30 -> 50.0 total,
    #     trades_processed becomes 12.
    ledger = [{'pnl': p} for p in
              (10, -5, 3, -1, 8, -2, 0, 15, -3, 6, -4, 9)]
    st17 = {'money': 0.0, 'demand': 1.0, 'parcels': {}}
    st17, evs17 = apply_trade_ledger(st17, ledger)
    assert abs(st17['money'] - 50.0) < 1e-9, st17['money']
    assert st17['trades_processed'] == 12, st17['trades_processed']
    assert sorted(evs17) == [('TRADE_BONUS', 30.0), ('TRADE_CREDITS', 20)], evs17
    # Called AGAIN with the SAME ledger: no new entries beyond
    # trades_processed, so this is a true no-op - proves idempotency,
    # not just "it worked once".
    st17b, evs17b = apply_trade_ledger(st17, ledger)
    assert st17b == st17, (st17b, st17)
    assert evs17b == [], evs17b
    # A LONGER ledger (3 more trades, 2 wins, no new milestone - 12->15
    # stays under the next multiple of 10 at 20): only the new entries
    # are read, money grows by the bonus alone (2*5=10), no credits.
    ledger += [{'pnl': p} for p in (2, -1, 7)]
    st17c, evs17c = apply_trade_ledger(st17, ledger)
    assert abs(st17c['money'] - 60.0) < 1e-9, st17c['money']  # 50 + 10
    assert st17c['trades_processed'] == 15, st17c['trades_processed']
    assert evs17c == [('TRADE_BONUS', 10.0)], evs17c

    print('econrules self-check: 17/17 pass (SCAFFOLDING values; growth '
          'retired from tick() 2026-09-03 - rent still accrues, tier '
          'never moves on its own, proven at both a handful of ticks and '
          '1000; upgrade() is the only path a tier still climbs, priced '
          'by climb(tier) x premium(performance), refused on ownership/'
          'failure/ladder-top/unbaked-asset/affordability but NEVER on '
          'performance alone; repair() clears a failed lot for money, '
          'itself unreachable in real play until a trading system sets '
          'the flag it clears; apply_trade_ledger converts an already-'
          'written trade ledger into count-milestone credits and per-win '
          'bonuses, idempotent by construction - this module never '
          'places an order or touches Alpaca, it only ever reads pnl '
          'off entries a separate adapter already closed)')
