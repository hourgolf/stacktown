"""CityTick state bridge — persists econrules.py's live state to disk and
wraps tick()/buy()/reset() for the Blueprint-callable boundary.

Architecture this implements: Docs/ECONOMY_TICK_CONTRACT.md. Blueprint
drives (calls this once per CityTick / buy attempt); econrules.py stays
the sole EXECUTED authority, never re-derived. This module is PURE — no
`unreal` import — so it is self-testable standalone exactly like
econrules.py. The thin Blueprint-callable wrapper that calls into these
functions and does nothing else lives in init_unreal.py, registered at
editor startup so it survives a restart (see the contract's condition 1).

State survives PIE stop/start AND editor restarts by living on disk
(owner's word, 2026-09-01: persist across sessions, with a loud reset
verb) — the same pattern econrules.py already uses for constants, applied
here to live state instead.
"""
import json
import os

import econrules

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, 'citystate.json')


def seed_state():
    """A fresh city, straight from econrules.json's declared start."""
    r = econrules.rules()
    return {'money': r['money_start'], 'demand': r['demand_default'],
            'parcels': {}}


def load_state(state_path=STATE_PATH):
    """Current persisted state, seeding fresh if none exists yet."""
    if not os.path.exists(state_path):
        return seed_state()
    with open(state_path) as f:
        return json.load(f)


def save_state(state, state_path=STATE_PATH):
    with open(state_path, 'w') as f:
        json.dump(state, f)


def city_tick(state, state_path=STATE_PATH):
    """One CityTick: advance via econrules, persist, return (state, events).
    Identical to econrules.tick(state) plus the persist — see the
    boundary-equality acceptance test in ECONOMY_TICK_CONTRACT.md."""
    new_state, events = econrules.tick(state)
    save_state(new_state, state_path)
    return new_state, events


def city_buy(state, pid, state_path=STATE_PATH):
    """One buy attempt: apply via econrules, persist iff it succeeded."""
    new_state, ok, reason = econrules.buy(state, pid)
    if ok:
        save_state(new_state, state_path)
    return new_state, ok, reason


def ensure_parcel(state, pid, rid, width, state_path=STATE_PATH):
    """Register a parcel the first time the driver sees its actor.
    Idempotent — if pid already exists, the existing entry (possibly grown
    via TIER_UP, possibly owned) wins untouched and this is a no-op; a
    pin's declared identity is only ever a STARTING seed, never re-applied
    over live state (PARCELIZATION_CONTRACT.md's original §2 reasoning,
    unchanged by the amendment).

    TIER ALWAYS SEEDS AT 0, regardless of any tier the caller might
    associate with rid. This is the amendment's A2 fix: the pin table's
    own `tier` field (testcity_pins.PINS) describes an intended EVENTUAL
    massing for the pre-built-demo case and is deliberately never read
    here — a fresh parcel starts small and grows via city_tick, per the
    owner's "play from scratch" direction. Seeding from a pin's declared
    tier here was the bug this function replaces: buying a parcel whose
    pin declared tier 6 would have shown the full mature building
    instantly instead of starting at 0 and growing up.

    Persists only when it actually inserts something — most calls, after
    the first tick, are no-ops (every known parcel already has an entry),
    and a no-op call has nothing new to persist. Same "persist iff
    something changed" idiom as city_buy."""
    if pid in state['parcels']:
        return state, False
    state['parcels'][pid] = {'rid': rid, 'tier': 0, 'width': width,
                              'owned': False, 'accum': 0.0}
    save_state(state, state_path)
    return state, True


def city_reset(state_path=STATE_PATH):
    """Wipe persisted state, reseed from money_start. LOUD by design —
    the owner chose persistence on the condition of an easy way out of
    it, so a deliberate reset must never be mistakable for a bug in the
    evidence."""
    fresh = seed_state()
    save_state(fresh, state_path)
    print('CITYSTATE RESET: state file wiped, reseeded from money_start=%.1f'
          % fresh['money'])
    return fresh


if __name__ == '__main__':
    # KNOWN ANSWERS, hand-computed against econrules.json's shipped values
    # and cross-checked against econrules.py called directly (the boundary
    # this module exists to cross). Uses a THROWAWAY state path so this
    # never touches the real citystate.json — a self-test that writes
    # production state is not a self-test, it is a bug.
    r = econrules.rules()
    assert (r['money_start'], r['demand_default']) == (100, 1.0), \
        'econrules.json changed - recompute the known answers below WITH it'
    # OUTSIDE Content/ (2026-09-03, see placement.py): the editor's
    # auto-reimport treats a JSON under Content/ as a DataTable source.
    _TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Saved', 'SelfTest')
    os.makedirs(_TEST_DIR, exist_ok=True)
    TEST_PATH = os.path.join(_TEST_DIR, '_selftest_citystate.json')
    try:
        if os.path.exists(TEST_PATH):
            os.remove(TEST_PATH)

        # 1. No file yet -> load_state seeds from econrules.json exactly.
        s = load_state(TEST_PATH)
        assert s == {'money': 100.0, 'demand': 1.0, 'parcels': {}}, s

        # 2. city_buy matches econrules.buy() exactly and persists on
        #    success (same known-answer parcel as econrules.py's own #3).
        s['parcels']['P1'] = {'rid': 'vernacular', 'tier': 0, 'width': 1230,
                               'owned': False, 'accum': 0.0}
        direct_s, ok_direct, _ = econrules.buy(json.loads(json.dumps(s)), 'P1')
        s, ok, why = city_buy(s, 'P1', TEST_PATH)
        assert ok and ok_direct and why == ''
        assert s == direct_s, (s, direct_s)
        assert abs(s['money'] - 25.4) < 1e-9, s['money']

        # 3. Persisted file round-trips byte-for-byte through JSON — the
        #    boundary ECONOMY_TICK_CONTRACT.md's acceptance test cares
        #    about: what got saved is exactly what reloads.
        with open(TEST_PATH) as f:
            reloaded = json.load(f)
        assert reloaded == s, (reloaded, s)

        # 4. city_tick matches econrules.tick() exactly across a real
        #    tier-up (mirrors econrules.py's own known-answer #3: 4 ticks
        #    of rent 10 from accum 0 crosses threshold 40, money ends at
        #    65.4, tier 1).
        direct_s2 = json.loads(json.dumps(s))
        events_direct = []
        for _ in range(4):
            direct_s2, e = econrules.tick(direct_s2)
            events_direct += e
        events = []
        for _ in range(4):
            s, e = city_tick(s, TEST_PATH)
            events += e
        assert s == direct_s2, (s, direct_s2)
        assert abs(s['money'] - 65.4) < 1e-9, s['money']
        assert events == events_direct == [('TIER_UP', 'P1', 1)], events

        # 5. GROWTH_BLOCKED survives the boundary too, not just the happy
        #    path — the specific case ECONOMY_TICK_CONTRACT.md §4 asks for.
        s['parcels']['OF'] = {'rid': 'office', 'tier': 0, 'width': 2050,
                               'owned': True, 'accum': 39.9}
        direct_s3, events_direct3 = econrules.tick(json.loads(json.dumps(s)))
        s, events3 = city_tick(s, TEST_PATH)
        assert s == direct_s3, (s, direct_s3)
        assert events3 and events3[0][0] == 'GROWTH_BLOCKED', events3
        assert events3 == events_direct3, (events3, events_direct3)

        # 6. Reset wipes to a fresh seed regardless of what came before,
        #    and the file on disk matches what was returned.
        s = city_reset(TEST_PATH)
        assert s == {'money': 100.0, 'demand': 1.0, 'parcels': {}}, s
        with open(TEST_PATH) as f:
            assert json.load(f) == s

        # 7. ensure_parcel seeds tier=0 ALWAYS (amendment A2) regardless of
        #    what the caller might associate with the recipe, is idempotent
        #    (a second call is a no-op that doesn't touch a since-grown
        #    tier), and persists only on the insert, not the no-op.
        s, inserted = ensure_parcel(s, 'SW2', 'tower', 1230, TEST_PATH)
        assert inserted is True
        assert s['parcels']['SW2'] == {
            'rid': 'tower', 'tier': 0, 'width': 1230,
            'owned': False, 'accum': 0.0}, s['parcels']['SW2']
        with open(TEST_PATH) as f:
            assert json.load(f) == s, 'insert did not persist'
        # simulate growth, then re-call ensure_parcel with the SAME args -
        # it must not roll the grown tier back to 0
        s['parcels']['SW2']['owned'] = True
        s['parcels']['SW2']['tier'] = 3
        pre_reensure = json.loads(json.dumps(s))
        s, inserted_again = ensure_parcel(s, 'SW2', 'tower', 1230, TEST_PATH)
        assert inserted_again is False
        assert s == pre_reensure, \
            'ensure_parcel mutated an already-registered (and grown) parcel'
        assert s['parcels']['SW2']['tier'] == 3, \
            'a no-op ensure_parcel call rolled tier back - the exact bug ' \
            'A2 exists to prevent'

        print('citytick self-check: 7/7 pass (pure-Python side of the '
              'boundary; the Blueprint-callable half is proven in the '
              'editor window per ECONOMY_TICK_CONTRACT.md condition 1)')
    finally:
        if os.path.exists(TEST_PATH):
            os.remove(TEST_PATH)
