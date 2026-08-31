"""Placeholder economy ruleset v0 — SCAFFOLDING, not design.

The beta twin's tick rules (Docs/BETA_TWIN_PLAN.md): buy parcels,
collect rent per CityTick, tier-up on a rent threshold, one global
demand dial. Every number here is a placeholder awaiting the owner's
economy notes; the MACHINERY (per-recipe ladders, loud growth blocks,
fresh-read constants) is the part that survives their arrival.

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


def tick(state, baked_dir=BAKED_DIR):
    """One CityTick. state = {'money': float, 'demand': float,
    'parcels': {pid: {'rid','tier','width','owned','accum'}}}.
    Returns (new_state, events). Pure - caller owns persistence."""
    r = rules()
    s = json.loads(json.dumps(state))   # defensive copy, JSON-clean
    events = []
    for pid, p in sorted(s['parcels'].items()):
        if not p.get('owned'):
            continue
        earned = rent(p['rid'], p['tier'], s['demand'], r)
        s['money'] += earned
        p['accum'] = p.get('accum', 0.0) + earned
        if p['accum'] >= r['growth_threshold'] * (int(p['tier']) + 1):
            ok, reason = tier_up_allowed(p['rid'], p['tier'], p['width'],
                                         baked_dir)
            if ok:
                p['tier'] = int(p['tier']) + 1
                p['accum'] = 0.0
                events.append(('TIER_UP', pid, p['tier']))
            else:
                events.append(('GROWTH_BLOCKED', pid, reason))
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


if __name__ == '__main__':
    # KNOWN ANSWERS, hand-computed from econrules.json's shipped values:
    # price_base 50, price_per_100uu 2, price_per_tier 25,
    # rent_per_tier 10, growth_threshold 40, demand 1.0.
    r = rules()
    assert (r['price_base'], r['price_per_100uu'], r['price_per_tier'],
            r['rent_per_tier'], r['growth_threshold']) == (50, 2, 25, 10, 40), \
        'json changed - recompute the known answers below WITH it'
    # 1. price: vernacular t0 w1230 = 50 + 2*12.3 + 0 = 74.6
    assert abs(price('vernacular', 0, 1230) - 74.6) < 1e-9
    # 2. rent: t2 at demand 2.0 = 10*3*2 = 60
    assert abs(rent('vernacular', 2, 2.0) - 60.0) < 1e-9
    # 3. buy then tick to a tier-up: money 100, buy t0 w1230 (74.6),
    #    left 25.4; threshold t0 = 40*1 = 40 -> 4 ticks of rent 10
    #    accumulate 40 and trigger. Hand-walked: after 4 ticks money =
    #    25.4 + 40 = 65.4, tier 1, accum reset.
    st = {'money': 100.0, 'demand': 1.0, 'parcels': {
        'P1': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
               'owned': False, 'accum': 0.0}}}
    st, ok, why = buy(st, 'P1')
    assert ok, why
    assert abs(st['money'] - 25.4) < 1e-9
    evs = []
    for _ in range(4):
        st, e = tick(st)
        evs += e
    assert abs(st['money'] - 65.4) < 1e-9, st['money']
    assert st['parcels']['P1']['tier'] == 1 and evs == [('TIER_UP', 'P1', 1)]
    # 4. LADDERS ARE PER-RECIPE: office tops out at tier 3 (4 tiers).
    ok, why = tier_up_allowed('office', 3, 2050)
    assert not ok and 'top of ladder' in why and '4 tiers' in why
    # 5. GROWTH BLOCKS LOUDLY: office t0 -> t1 is declared but NOT baked
    #    (only t0 exists at w2050 today). If this assert ever fails
    #    because t1 got baked, replace with a synthetic missing asset -
    #    instrument hygiene, per protocol.
    ok, why = tier_up_allowed('office', 0, 2050)
    assert not ok and 'GROWTH BLOCKED' in why and 'office_t1' in why, why
    # 6. a blocked parcel emits the event and does NOT advance
    st2 = {'money': 0.0, 'demand': 1.0, 'parcels': {
        'OF': {'rid': 'office', 'tier': 0, 'width': 2050,
               'owned': True, 'accum': 39.9}}}
    st2, e2 = tick(st2)
    assert st2['parcels']['OF']['tier'] == 0
    assert e2 and e2[0][0] == 'GROWTH_BLOCKED', e2
    # 7. insufficient funds refuses loudly
    st3 = {'money': 1.0, 'demand': 1.0, 'parcels': {
        'P': {'rid': 'vernacular', 'tier': 0, 'width': 1230,
              'owned': False}}}
    _, ok, why = buy(st3, 'P')
    assert not ok and 'insufficient funds' in why
    print('econrules self-check: 7/7 pass (SCAFFOLDING values)')
