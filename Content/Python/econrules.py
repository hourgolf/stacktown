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
RULES_PATH = os.path.join(HERE, 'econrules.json')
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


def price(rid, tier, width, r=None):
    r = r or rules()
    return r['price_base'] + r['price_per_100uu'] * (float(width) / 100.0) \
        + r['price_per_tier'] * int(tier)


def rent(rid, tier, demand, r=None):
    r = r or rules()
    return r['rent_per_tier'] * (int(tier) + 1) * float(demand)


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
    'parcels': {pid: {'rid','tier','width','owned','accum',...}}}.
    Returns (new_state, events) - events is always [] now (kept in the
    return shape, not dropped, since citytick.city_tick and every
    caller already destructures (state, events); a lot's tier NEVER
    changes here, regardless of accum or demand - see module docstring,
    "GROWTH RETIRED FROM tick()". accum keeps accruing (still real rent
    collected, still what the HUD shows) - only the automatic threshold
    check that used to read it is gone. Pure - caller owns
    persistence."""
    r = rules()
    s = json.loads(json.dumps(state))   # defensive copy, JSON-clean
    events = []
    for pid, p in sorted(s['parcels'].items()):
        if not p.get('owned'):
            continue
        earned = rent(p['rid'], p['tier'], s['demand'], r)
        s['money'] += earned
        p['accum'] = p.get('accum', 0.0) + earned
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
    return s, True, ''


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
    assert abs(st['money'] - 32.9) < 1e-9, st['money']
    assert abs(st['parcels']['P1']['accum'] - 7.5) < 1e-9, st['parcels']['P1']
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
    assert abs(st2['money'] - 0.75) < 1e-9, st2['money']
    assert abs(st2['parcels']['OF']['accum'] - 40.65) < 1e-9, st2['parcels']['OF']
    assert st2['parcels']['OF']['tier'] == 0
    assert e2 == [], e2
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
    assert abs(st8['money'] - 750.0) < 1e-6, st8['money']
    assert abs(st8['parcels']['P1']['accum'] - 750.0) < 1e-6, \
        st8['parcels']['P1']
    assert st8['parcels']['P1']['tier'] == 0, st8['parcels']['P1']
    assert evs8 == [], 'tier-related event fired during 1000 ticks: %r' % evs8

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

    print('econrules self-check: 13/13 pass (SCAFFOLDING values; growth '
          'retired from tick() 2026-09-03 - rent still accrues, tier '
          'never moves on its own, proven at both a handful of ticks and '
          '1000; upgrade() is the only path a tier still climbs, priced '
          'by climb(tier) x premium(performance), refused on ownership/'
          'failure/ladder-top/unbaked-asset/affordability but NEVER on '
          'performance alone; repair() clears a failed lot for money, '
          'itself unreachable in real play until a trading system sets '
          'the flag it clears)')
