"""Editor startup registration.

PythonScriptPlugin auto-runs any Content/Python/init_unreal.py at editor
boot. This is the in-process economy driver for
Docs/ECONOMY_TICK_CONTRACT.md option (b'): a registered Slate post-tick
callback reads/writes CityStateJSON on the PIE GameInstance directly,
whenever a PIE world exists. No Blueprint call crosses into Python at
all — BP's whole job is reading CityStateJSON (display) and writing
BuyRequestPID (the buy verb).

Grew a second responsibility 2026-09-01, PARCELIZATION_CONTRACT.md's
amendment (A1/A6): the same driver also finds every individual BP_Parcel
actor each throttled tick and pushes its Owned/Tier straight onto the
actor's own Blueprint variables, in the same in-process way it already
pushes CityStateJSON onto the GameInstance. This is what lets ResolveMesh
stay pure Blueprint (reads its own simple variables, never parses JSON)
while still being driven entirely from citystate.json.

History: an earlier version of this file exposed a BlueprintFunctionLibrary
(CityTickBridge) meant to be called FROM Blueprint graphs. That path is
dead — the owner's careful palette check (Context Sensitive off, bare
"city" search) found no such nodes anywhere; the earlier "condition 1
closed" call was a name collision with BP_Parcel's own legacy CityTick
event, not the real bridge. Python-defined UFunctions do not reach
Blueprint's action database in this project's setup, and "Execute Python
Script" is editor-utility-only (unavailable in Actor/Pawn graphs), so
neither the original design nor its fallback survive contact with the
real palette. Superseded 2026-09-01 — see ECONOMY_TICK_CONTRACT.md.

Stage 1 (heartbeat only, no economy logic) proven separately before this
— registration, periodic firing, and the double-registration guard all
confirmed working in isolation. This is stage 2: the real driver.

Grew a third responsibility 2026-09-01, resolving ECONOMY_TICK_CONTRACT.md's
"HUD — still an open design question": rather than teach Blueprint to parse
CityStateJSON (the contract is explicit that only Python ever does that),
the driver now ALSO pushes a handful of derived, already-parsed scalars —
GameInstance.Money/Demand, and per-parcel Price/Accum — the same one-way
JSON-to-Blueprint-variable shape _sync_parcels already established for
Owned/Tier. Blueprint still never interprets the JSON string itself.

Grew a fourth responsibility 2026-09-02, PLACEMENT_GRID.md's owner
-authorized v0: a placement channel, request-and-clear shaped exactly
like BuyRequestPID (GameInstance.PlaceRequestX/Y, BP's whole job is
writing a world-space hit location). This is the ONE place
placement.place() is called and the ONE place a placement-created
BP_Parcel is spawned — into the GAME world specifically
(`gw`/get_game_world(), never the editor world; see HANDOFF.md's
world-split trap), labelled with the exact pid placement.py assigned,
so _sync_parcels discovers it afterward through the same path every
other parcel already uses. Identity only at spawn, same as
mk_testcity_builds.py's own discipline — mesh is deliberately untouched
here; the spawned actor's own BeginPlay/Tick resolve it, not this
driver.
"""
import os
import time

import citylayout as _citylayout
import citytick as _citytick
import cpdmap as _cpdmap
import econrules as _econrules
import placement as _placement
import testcity_pins as _testcity_pins
import unreal
import woodmap as _woodmap

_WOOD_MI_PATH = '/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s'

# Channel indices from cpdmap.py, the one authority - never hardcoded
# here, per the map's own warning about exactly this class of drift.
_CPD_AGE = _cpdmap.index('Age')
_CPD_ATTENTION = _cpdmap.index('Attention')
_CPD_FAILURE = _cpdmap.index('Failure')
_CPD_SCORCH = _cpdmap.index('Scorch')
# ECONOMY_TICK_CONTRACT.md, "Patina's Age channel" - tunable, not measured.
_AGE_MATURE_TICKS = 150.0

# A placed lot's Y-CENTER, not the road edge itself - found live,
# 2026-09-02, the session right after the from-scratch loop was first
# proven end to end: the owner's placed pad stretched into the road.
# citylayout.HALF (1130) is the FACADE line - the edge where the
# footway ends and buildable ground begins, the same Y a pinned block's
# own envelope starts at (blocks()['arterial_edge']). A PINNED lot never
# shows this bug because its baked mesh's origin is its LEFT-FRONT
# CORNER (mk_testcity_builds.py's own convention comment) - placing that
# origin AT the facade line puts the mesh's front edge there and it
# extends backward through its own geometry. The empty-lot PLACEHOLDER
# (a stock engine cube, PARCELIZATION_CONTRACT.md A4) is CENTER-origin
# instead - placing its center at the facade line pushes half its depth
# forward, into the road. Fix: center it HALF the block depth further
# back, so the near edge (not the center) lands on the facade line -
# derived from citylayout's own constants, never a literal, so it can't
# silently desync from BLOCK_DEPTH/HALF the way a copied number could.
_PAD_CENTER_Y = _citylayout.HALF + _citylayout.BLOCK_DEPTH / 2.0

_TICK_INTERVAL_S = 2.0
_PARCEL_CLASS_PATH = '/Game/Stacktown/Runtime/BP_Parcel.BP_Parcel_C'


def _log_tick_events(events):
    for kind, pid, detail in events:
        if kind == 'TIER_UP':
            unreal.log('CITY TICK: %s tiered up to %s' % (pid, detail))
        elif kind == 'GROWTH_BLOCKED':
            unreal.log_warning('CITY TICK: %s %s' % (pid, detail))


def _place_refusal_message(reason):
    """Short, specific, player-facing text for a placement refusal - the
    coordinator's own ask after the owner's "some worked, some didn't"
    report: placement.py's own reason string is precise for the log
    (exact spans, exact cause) but reads as debug output to a player -
    'overlap: [2460.0, 3280.0] crosses a pinned lot at [2460.0, 3280.0]'
    answers a question nobody but this driver is asking. The log line
    keeps the full technical reason unchanged; only the on-screen text
    is classified down to what the player actually needs: what kind of
    no, not the coordinates of it.

    Four causes exist today (placement.py's own return points): off-
    board (either check), overlap-vs-pinned, overlap-vs-placed, pool
    exhausted. All overlap collapses to one message regardless of
    whether the conflicting lot is the player's own most recent
    placement or a different one - there is one player, and "already
    built there" is the same actionable fact either way. 'near-crossing'
    is not a real cause yet (v0 is one road; the multi-road pass is
    where a near-the-crossing refusal is meant to become real) - the
    fallback below covers it if that lands before this classifier is
    revisited."""
    if reason.startswith('off-board'):
        return 'Off the board'
    if 'crosses a pinned lot' in reason:
        return "That's part of the starter city"
    if 'crosses an existing lot' in reason:
        return 'Already built there'
    if reason.startswith('pool exhausted'):
        return 'No more lots available'
    return "Can't build here"


_TEST_STATE_PATH = os.path.join(_citytick.HERE, 'citystate_test.json')
_LANE_MARKER_PATH = os.path.join(_citytick.HERE, 'lane_pie.marker')


def _state_path_source():
    """Isolation, 2026-09-03, twice-corrected same day: multiple lanes
    share this one editor and driver, and the owner's citystate.json is
    their real, persistent save - the same file every lane's PIE was
    hitting by default, which is how a lane's own testing (or a stray
    owner N-press, see HANDOFF.md) can wipe the owner's city.

    First cut put the test path behind a GameInstance bool defaulting
    OFF - wrong direction, it put the OWNER on the test path by default
    too, since a hand-started PIE never sets it either. Second cut fixed
    the default (owner's real file unless something opts out) via
    `unreal._stacktown_state_override`, set BEFORE StartPIE - but that
    needs a Python channel this lane doesn't have; file tools are all it
    has, so a marker file is the self-serve route. THREE ways to select a
    path now, in priority order, because a lane with the Python channel
    (the coordinator, driving another lane's PIE for it) and a lane
    without it (this one, editing its own files) both need a route in:

    1. `unreal._stacktown_state_override` (a path string) - the Python
       channel's route, wins over everything, same purge-proof attribute
       trick as _stacktown_driver_registered (native/compiled, survives
       _guard.py's module-cache purge).
    2. `lane_pie.marker` existing in Content/Python/ - the file-tools
       route. Its CONTENT, if non-empty (stripped), is the path to use;
       empty or whitespace-only content means _TEST_STATE_PATH. A lane
       writes this immediately before StartPIE.
    3. Neither set -> _citytick.STATE_PATH, the owner's real file,
       unconditionally. This is the safe default because it is what an
       owner's hand-started session always gets - a lane must opt OUT,
       deliberately, every time, or it is on the real file.

    The driver clears BOTH the attribute and the marker the moment PIE
    ends (see the pie_was_running transition below), so a lane's setting
    can never leak into the owner's NEXT hand-started session - including
    a marker left behind by a session that crashed mid-test, cleaned up
    at the next PIE end before the owner could ever reach it.

    Returns (path, source) where source is 'override' / 'marker' /
    'default' - the source label is what makes the PIE-start log line an
    audit trail: a lane that forgot the marker shows 'default' in the log
    against its own PIE session, catchable after the fact, not just
    prevented in the good case."""
    override = getattr(unreal, '_stacktown_state_override', None)
    if override:
        return override, 'override'
    if os.path.exists(_LANE_MARKER_PATH):
        with open(_LANE_MARKER_PATH) as f:
            content = f.read().strip()
        return (content if content else _TEST_STATE_PATH), 'marker'
    return _citytick.STATE_PATH, 'default'


def _state_path_for():
    return _state_path_source()[0]


def _read_state(gi):
    state_path = _state_path_for()
    raw = gi.get_editor_property('CityStateJSON')
    return _citytick.json.loads(raw) if raw else _citytick.load_state(state_path)


def _write_state(gi, state):
    gi.set_editor_property('CityStateJSON', _citytick.json.dumps(state))


def _sync_parcels(gw, gi):
    """Per PARCELIZATION_CONTRACT.md's amendment (A1/A6): find every
    BP_Parcel actor, register any not yet known to citystate.json (seeded
    at tier=0 via ensure_parcel — never the pin's declared tier, see A2),
    then push each one's current Owned/Tier back onto the actor. This
    replaces the original §2 design (each parcel calls a Python bridge
    function at its own BeginPlay) with the same in-process driver that
    already does the economy tick — that per-parcel Blueprint-to-Python
    call is the identical mechanism condition 1 already proved
    permanently impossible in this project, just discovered a second time
    for a different call site.

    One-way JSON -> actor for Owned/Tier. RecipeId/WidthUU/CornerSide are
    the actor's own immutable identity, set once by the builder at spawn —
    read here, never written.

    Also pushes Price (econrules.price(), recomputed every sync since it
    depends on Tier) and Accum (state's own accumulator, HUD-facing growth
    progress) — unconditionally, unlike Owned/Tier, since neither drives
    an expensive ResolveMesh and there is nothing to gate."""
    parcel_class = unreal.load_class(None, _PARCEL_CLASS_PATH)
    actors = unreal.GameplayStatics.get_all_actors_of_class(gw, parcel_class)
    if not actors:
        return
    state = _read_state(gi)
    changed = False
    for a in actors:
        pid = a.get_actor_label()
        if pid.startswith('POOL_'):
            # Dormant pool actors are not parcels - skip before anything
            # below tries to register or push onto them. Without this
            # every one of them was getting ensure_parcel'd as a real
            # (empty, zero-width) entry every session: correct in effect
            # (ensure_parcel never sets a 'placement' key, so neither
            # place()'s cap nor resolve_click's overlap scan ever see
            # these) but 30 wasted registrations and JSON bloat per
            # session - the kind of thing that reads as a mystery in a
            # month, found while checking a real bug, fixed while here.
            continue
        if pid not in state['parcels']:
            rid = str(a.get_editor_property('RecipeId'))
            width = a.get_editor_property('WidthUU')
            state, inserted = _citytick.ensure_parcel(
                state, pid, rid, width, _state_path_for())
            changed = changed or inserted
        p = state['parcels'][pid]
        if bool(a.get_editor_property('Owned')) != bool(p['owned']):
            a.set_editor_property('Owned', bool(p['owned']))
        if int(a.get_editor_property('Tier')) != int(p['tier']):
            a.set_editor_property('Tier', int(p['tier']))
        a.set_editor_property(
            'Price', float(_econrules.price(p['rid'], p['tier'], p['width'])))
        a.set_editor_property('Accum', float(p['accum']))
        # Species is a pure function of RecipeId alone (D3: "a building does
        # not repaint itself when it gains a storey") so this is pushed
        # unconditionally, same as Price/Accum - ResolveMesh itself decides
        # whether to actually apply it (only under DA_Catalogue_Wood), not
        # this driver. The base (no age-suffix) MI per species is used here;
        # the _a0..a3 weathering variants are a direction-B look choice, not
        # this lane's to pick.
        species = _woodmap.species_for(p['rid'])
        mi_path = _WOOD_MI_PATH % (species, species)
        mi = unreal.load_asset(mi_path)
        if mi is not None:
            a.set_editor_property('SpeciesMaterial', mi)
        # Age (ECONOMY_TICK_CONTRACT.md, "Patina's Age channel"): tracked
        # and persisted HERE, deliberately outside econrules.tick()/
        # citytick.city_tick() - both assert EXACT state equality against
        # known answers in their own self-tests, and age_ticks has nothing
        # to do with the economy those are proving. RESETS ON TIER-UP -
        # DIRECTION_B.md B3, locked: "New/upgraded buildings start pale."
        # Corrected same day it was first wired wrong (monotonic,
        # cumulative-oxidation reasoning that was coherent but never
        # checked against the owner's own locked doctrine first).
        if bool(p.get('owned')):
            if p.get('age_last_tier') != p['tier']:
                p['age_ticks'] = 0.0
                p['age_last_tier'] = p['tier']
            else:
                p['age_ticks'] = p.get('age_ticks', 0.0) + 1.0
            changed = True
        age = min(1.0, p.get('age_ticks', 0.0) / _AGE_MATURE_TICKS)
        # CUSTOM PRIMITIVE DATA MUST BE WRITTEN VIA THE FUNCTION, NEVER AS
        # A PROPERTY - a property write only touches the component's
        # editor-defaults array, which the shader never reads; the shader
        # reads the runtime per-instance array, which only
        # set_custom_primitive_data_float actually sets. A property
        # read-back proving CPD "survived" a mesh swap was proving the
        # wrong array - caught by the design lane's wear window, not by
        # this driver. Re-applied unconditionally every sync (like
        # Price/Accum), which is also what makes it survive a tier-up's
        # own SetStaticMesh without any special-case logic: the next
        # throttled sync, at most _TICK_INTERVAL_S later, re-writes it.
        building = a.get_editor_property('Building')
        building.set_custom_primitive_data_float(_CPD_AGE, age)
        building.set_custom_primitive_data_float(_CPD_ATTENTION, 0.0)
        building.set_custom_primitive_data_float(_CPD_FAILURE, 0.0)
        building.set_custom_primitive_data_float(_CPD_SCORCH, 0.0)
    if changed:
        _write_state(gi, state)


def _reactivate_pinned_parcels(gw, gi):
    """Session-start only, same just_started gate as _sync_parcels/
    _reactivate_placed_parcels, run BEFORE it - the starter preset is
    the base state placements layer onto, not the reverse (though since
    pins and placements draw from disjoint label ranges, POOL_PIN_* vs
    plain POOL_NN, the order only matters for log narrative, not
    correctness).

    Empty mode's other half (PARCELIZATION_CONTRACT.md's pool doctrine,
    extended 2026-09-02, "GO on empty mode" from the coordinator): the
    14 pinned lots are pre-positioned at their real, rhythm-adjusted
    transforms as dormant pool content (mk_testcity_builds.py, each
    labelled POOL_PIN_<key> for that SPECIFIC key) but never given
    identity or shown until this pass decides to, gated on GameInstance.
    EmptyStart - true (the owner's chosen default for the next session)
    leaves every one dormant, so the board opens fully empty; false
    activates all 14 at their real testcity_pins identity, the board
    every session tonight before this one was already playing on.

    DIRECT LABEL LOOKUP, not plan_reactivation's sorted allocation -
    unlike a placement (which can claim any dormant slot), each pin has
    exactly one PREDETERMINED slot by construction, so there is no
    allocation decision to make, only a "does it exist" check.

    LOCAL try/except around the EmptyStart read, same reason as every
    other request-and-clear channel in this file: the property does not
    exist on the GameInstance until the compile/save window that adds
    it lands, and a missing property must never abort the rest of this
    tick. Missing = treated as False (activate pins) - the historical,
    already-proven default that every session tonight before this one
    ran under, not a guess at what an unbuilt toggle would say."""
    try:
        empty_start = bool(gi.get_editor_property('EmptyStart'))
    except Exception:
        empty_start = False
    if empty_start:
        return
    parcel_class = unreal.load_class(None, _PARCEL_CLASS_PATH)
    by_label = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(
            gw, parcel_class):
        label = a.get_actor_label()
        if label.startswith('POOL_PIN_'):
            by_label[label] = a
    for key, pin in _testcity_pins.PINS.items():
        label = 'POOL_PIN_%s' % key
        pool_actor = by_label.get(label)
        if pool_actor is None:
            unreal.log_warning(
                'CITY REACTIVATE: pin %s has no dormant slot (%s) - '
                'pool/build desync, run mk_testcity_builds.py?'
                % (key, label))
            continue
        rid, tier = _testcity_pins.identity(key)
        _end, turn_side = _citylayout.cross_street_end(key[:2])
        corner_side = ('L' if turn_side == 'left' else 'R') \
            if pin['corner'] else ''
        pool_actor.set_editor_property('RecipeId', unreal.Name(rid))
        pool_actor.set_editor_property('WidthUU', float(pin['w']))
        pool_actor.set_editor_property('Tier', int(tier))
        pool_actor.set_editor_property('Owned', False)
        pool_actor.set_editor_property('CornerSide', corner_side)
        pool_actor.set_actor_label(key)
        pool_actor.set_actor_hidden_in_game(False)
        pool_actor.set_actor_enable_collision(True)
        unreal.log('CITY REACTIVATE: pin %s activated' % key)


def _reactivate_placed_parcels(gw, gi):
    """Session-start only (called once, gated on the same just_started
    signal that forces _sync_parcels' own first-tick run): restores
    every placed lot from citystate.json onto a dormant pool actor,
    exactly as the click-driven placement channel activates one, just as
    a batch instead of one at a time. Without this a placed lot's state
    entry outlives a PIE restart while the pool always boots dormant
    (map-saved content, untouched by the previous session's runtime-only
    activations) - found live, 2026-09-02, as the exact shape of the
    owner's repeated "can't build here" reports: a ghost entry with no
    actor still refuses real clicks at its own span.

    The pairing decision (which pid claims which pool label) is pure
    Python, self-tested with hand-computed answers in placement.py
    (plan_reactivation, GENERIC over which pids as of empty mode - see
    _reactivate_pinned_parcels below for the other caller) - this
    function only executes that plan against live actors, the same
    split placement.place()/the click channel already use.

    POOL_PIN_* labels are deliberately excluded from pool_actors below -
    those are reserved for _reactivate_pinned_parcels, pre-positioned at
    build time at a SPECIFIC pin's rhythm-adjusted transform, not a
    fungible slot a player placement should ever claim."""
    state = _read_state(gi)
    parcel_class = unreal.load_class(None, _PARCEL_CLASS_PATH)
    pool_actors = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(
            gw, parcel_class):
        label = a.get_actor_label()
        if label.startswith('POOL_') and not label.startswith('POOL_PIN_'):
            pool_actors[label] = a
    placed_pids = [pid for pid, p in state['parcels'].items()
                   if p.get('placement')]
    pairs, unmatched = _placement.plan_reactivation(
        placed_pids, pool_actors.keys())
    for pid, label in pairs:
        p = state['parcels'][pid]
        lot = p['placement']
        pool_actor = pool_actors[label]
        face_y = _PAD_CENTER_Y if lot['side'] == 'north' else -_PAD_CENTER_Y
        yaw = 0.0 if lot['side'] == 'north' else 180.0
        spawn_x = lot['x0'] if lot['side'] == 'north' else lot['x1']
        # IDENTICAL sequence to the click-driven activation, including
        # restoring the ACTUAL current Tier/Owned - unlike a fresh
        # placement (always Tier=0/Owned=False), a reactivated lot may
        # already have been bought and grown since it was placed, and
        # must come back exactly as it was, the same as any pinned lot
        # already does via _sync_parcels below this call.
        pool_actor.set_actor_location_and_rotation(
            unreal.Vector(spawn_x, face_y, 0.0),
            unreal.Rotator(0.0, 0.0, yaw), False, False)
        pool_actor.set_editor_property('RecipeId', unreal.Name(p['rid']))
        pool_actor.set_editor_property('WidthUU', float(p['width']))
        pool_actor.set_editor_property('Tier', int(p['tier']))
        pool_actor.set_editor_property('Owned', bool(p['owned']))
        pool_actor.set_editor_property('CornerSide', '')
        pool_actor.set_actor_label(pid)
        pool_actor.set_actor_hidden_in_game(False)
        pool_actor.set_actor_enable_collision(True)
        unreal.log('CITY REACTIVATE: %s restored at (%.0f, %.0f)'
                   % (pid, spawn_x, face_y))
    for pid in unmatched:
        unreal.log_warning(
            'CITY REACTIVATE: %s has no dormant pool actor left - '
            'state/pool desync (%d placed, %d dormant)'
            % (pid, len(pairs) + len(unmatched), len(pool_actors)))


def _push_economy_fields(gi, state):
    """One-way JSON -> GameInstance for the top-level economy scalars,
    same shape as _sync_parcels' per-parcel push. Called right after every
    _write_state so Money/Demand are never a tick stale relative to what
    was just persisted."""
    gi.set_editor_property('Money', float(state['money']))
    gi.set_editor_property('Demand', float(state['demand']))


def _city_driver_tick(delta_seconds):
    """Registered as the Slate post-tick callback. Runs every editor
    frame whether or not PIE is active — must no-op cleanly when there's
    no game world, and must never let an exception escape (that kills
    the callback silently for the rest of the session, with no further
    warning to anyone)."""
    state = unreal._stacktown_driver_state
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        gw = ues.get_game_world()
        if gw is None:
            if state.get('pie_was_running', False):
                # PIE just ended (this is the FIRST no-world tick after a
                # run of world-having ones, not just another one of many -
                # see pie_was_running below). Clear BOTH lane opt-out
                # routes right here, unconditionally, so neither can
                # survive to leak into the owner's NEXT hand-started
                # session - the exact leak they exist to prevent, just
                # moved one step later if this didn't run. Covers the
                # crashed-lane case too: a marker left behind by a
                # session that died mid-test is gone by the time the
                # owner could ever reach it, not just in the clean-exit
                # case.
                unreal._stacktown_state_override = None
                if os.path.exists(_LANE_MARKER_PATH):
                    os.remove(_LANE_MARKER_PATH)
            state['pie_was_running'] = False
            state['pie_just_started'] = True
            return
        state['pie_was_running'] = True
        gi = unreal.GameplayStatics.get_game_instance(gw)
        if gi is None:
            return
        # A fresh PIE session's first tick runs the parcel sync
        # immediately rather than waiting up to _TICK_INTERVAL_S - avoids
        # an up-to-2s window where a just-loaded board shows authored
        # defaults instead of the reconciled state, right when selection
        # & camera feel (the thing being judged) is first on screen.
        just_started = state.pop('pie_just_started', False)
        if just_started:
            _path, _source = _state_path_source()
            unreal.log('CITY DRIVER: session state file -> %s (%s)'
                       % (_path, _source))

        # Reset channel: the owner's condition for accepting persistence
        # at all was an easy, loud way out of it. Same consume-and-clear
        # shape as buy, checked first so a reset always wins over
        # whatever else this tick would have done.
        if gi.get_editor_property('ResetRequested'):
            gi.set_editor_property('ResetRequested', False)
            fresh = _citytick.city_reset(_state_path_for())
            unreal.log_warning(
                'CITYSTATE RESET (via GameInstance.ResetRequested): '
                'reseeded from money_start=%.1f' % fresh['money'])
            # DEACTIVATE EVERY PLACED POOL ACTOR back to dormant - a
            # placed pid is always 'P' followed by only digits
            # (_next_pid's own contract; pinned labels are always a
            # compass prefix + digit, e.g. 'SW2', never bare 'P', so
            # this can't mistake a pinned building for a placed one).
            # Pinned TC_Bld_* actors are untouched here - reset only
            # ever zeroes their Owned/Tier via the state push below,
            # same as it always has; the pool is a separate system.
            parcel_class = unreal.load_class(None, _PARCEL_CLASS_PATH)
            used_nums, placed_actors = set(), []
            for a in unreal.GameplayStatics.get_all_actors_of_class(
                    gw, parcel_class):
                label = a.get_actor_label()
                if label.startswith('POOL_PIN_'):
                    # Reserved pin slots aren't part of the numbered
                    # POOL_NN space at all - int(label[5:]) on one of
                    # these would throw (label[5:] is 'PIN_NE0', not a
                    # number). Reset never touches pin dormancy; that's
                    # _reactivate_pinned_parcels' job, gated on
                    # EmptyStart, not this channel's.
                    continue
                if label.startswith('POOL_'):
                    used_nums.add(int(label[5:]))
                elif label[:1] == 'P' and label[1:].isdigit():
                    placed_actors.append(a)
            free_nums = sorted(
                set(range(_placement.POOL_SIZE)) - used_nums)
            for a, n in zip(placed_actors, free_nums):
                a.set_actor_hidden_in_game(True)
                a.set_actor_enable_collision(False)
                a.set_actor_label('POOL_%02d' % n)
                # Zero WidthUU so the NEXT activation's WidthUU write is
                # actually a change BP_Parcel's Tick detects (LastWidthUU
                # fix, 2026-09-02) - without this, an actor deactivated
                # at WidthUU=820 and later reactivated at WidthUU=820
                # again would see no change and never re-resolve, the
                # same invisible-pad bug the fix below closes, recurring
                # on a second use of the same pool slot.
                a.set_editor_property('WidthUU', 0.0)
            if len(placed_actors) != len(free_nums):
                unreal.log_warning(
                    'CITY RESET: %d placed actors but %d free pool slots '
                    '- pool/state desync' % (
                        len(placed_actors), len(free_nums)))
            _write_state(gi, fresh)
            _push_economy_fields(gi, fresh)
            return

        # Buy channel: BP's whole job is writing this one string. We
        # consume and clear it in the same tick we act on it, so a
        # slow/absent driver can never leave a stale request re-firing.
        pid = gi.get_editor_property('BuyRequestPID')
        if pid:
            gi.set_editor_property('BuyRequestPID', '')
            city_state = _read_state(gi)
            new_state, ok, reason = _citytick.city_buy(
                city_state, pid, _state_path_for())
            if ok:
                unreal.log('CITY BUY: %s bought' % pid)
            else:
                unreal.log_warning('CITY BUY: %s refused - %s' % (pid, reason))
            _write_state(gi, new_state)
            _push_economy_fields(gi, new_state)

        # Placement channel: PLACEMENT_GRID.md section 8's v0. BP's whole
        # job is writing a world-space (x, y) hit location; this is the
        # ONLY place placement.place() ever gets called from, and the
        # ONLY place a placement-created BP_Parcel ever gets spawned -
        # one authority, matching PlaceRequestX/Y's own request-and-clear
        # shape to BuyRequestPID above. Consume-and-clear BEFORE acting,
        # same reason as buy: a slow/absent driver must never leave a
        # stale request to re-fire.
        #
        # LOCAL try/except, deliberately not relying on the outer one:
        # PlaceRequestX/Y don't exist on GameInstance until BP_LensRig's
        # click-handler window lands. Caught live 2026-09-02, the hard
        # way: get_editor_property raising here sat BEFORE the economy
        # tick and _sync_parcels in this same function body, so the
        # missing property silently aborted EVERY tick at this line -
        # not just placement, the whole driver (economy, Price/Accum,
        # CPD wear) went dead the instant this channel was added, with
        # only a once-per-session suppressed log line to show for it.
        # Every future request-and-clear channel added here needs the
        # same local guard, not just this one.
        try:
            px_req = gi.get_editor_property('PlaceRequestX')
            py_req = gi.get_editor_property('PlaceRequestY')
        except Exception:
            px_req = py_req = 0.0
        if px_req != 0.0 or py_req != 0.0:
            gi.set_editor_property('PlaceRequestX', 0.0)
            gi.set_editor_property('PlaceRequestY', 0.0)
            city_state = _read_state(gi)
            # MODE-GATED pinned-span check (found live, 2026-09-02, the
            # session right after empty mode shipped): a click refused
            # against a PIN's footprint even when EmptyStart left every
            # pin dormant - ground with nothing standing on it was
            # still off-limits. Same local-try/except-missing-property
            # pattern as EmptyStart's other reader
            # (_reactivate_pinned_parcels) - missing = pins_active=True,
            # the historical default every earlier session ran under.
            try:
                pins_active = not bool(gi.get_editor_property('EmptyStart'))
            except Exception:
                pins_active = True
            new_state, pid, ok, reason = _placement.place(
                city_state, px_req, py_req, pins_active=pins_active)
            if not ok:
                unreal.log_warning('CITY PLACE: refused - %s' % reason)
                # Owner's first live click refused silently on screen -
                # loud in the log, invisible to the player, which reads
                # as "nothing happens" rather than "off the board." The
                # LOG keeps the full technical reason; the SCREEN gets
                # _place_refusal_message's short, cause-specific
                # translation instead of the raw string - the owner's
                # "some worked, some didn't" report was the log agreeing
                # with them (all genuine overlaps) while the screen said
                # nothing precise enough to tell them why. Keyed so
                # rapid clicks replace the message instead of stacking;
                # stopgap until the HUD's BuyPromptText line can carry
                # this instead.
                unreal.SystemLibrary.print_string(
                    gi, _place_refusal_message(reason),
                    True, False, unreal.LinearColor(1.0, 0.4, 0.0, 1.0),
                    3.0, 'CityPlace')
            else:
                lot = new_state['parcels'][pid]['placement']
                # ACTIVATE A DORMANT POOL ACTOR, NEVER SPAWN - no Python
                # API in this build creates an actor in the game/PIE
                # world (checked exhaustively: World has no spawn method,
                # GameplayStatics has none for generic actors, and the
                # only spawn_actor_from_class in the whole `unreal`
                # module lives on the two editor-world-only subsystems -
                # see placement.py's POOL_SIZE comment). mk_testcity_
                # builds.py pre-placed POOL_SIZE hidden, non-colliding
                # BP_Parcel actors as map content for exactly this.
                # Lowest-numbered free one, for determinism in logs.
                parcel_class = unreal.load_class(None, _PARCEL_CLASS_PATH)
                pool_actor = None
                for a in sorted(
                        unreal.GameplayStatics.get_all_actors_of_class(
                            gw, parcel_class),
                        key=lambda x: x.get_actor_label()):
                    label = a.get_actor_label()
                    # POOL_PIN_* excluded - reserved for a specific pin,
                    # never a fungible slot a click-driven placement
                    # should claim (empty mode, 2026-09-02). Lexicographic
                    # sort already prefers plain POOL_NN labels ('0' <
                    # 'P'), so this only bites once the general pool is
                    # nearly exhausted - real, not hypothetical, worth
                    # excluding explicitly rather than relying on luck.
                    if label.startswith('POOL_') and not label.startswith(
                            'POOL_PIN_'):
                        pool_actor = a
                        break
                if pool_actor is None:
                    # Backstop only - placement.py's own POOL_SIZE check
                    # (citystate's placed-count vs POOL_SIZE) should
                    # refuse before this is ever reached. Reaching it
                    # anyway means state and the live pool have desynced,
                    # worth knowing loudly rather than crashing on it.
                    del new_state['parcels'][pid]
                    unreal.log_warning(
                        'CITY PLACE: %s accepted by placement.py but no '
                        'dormant pool actor was found live - state/pool '
                        'desync' % pid)
                    unreal.SystemLibrary.print_string(
                        gi, 'Build not wired up yet - ask the team',
                        True, False,
                        unreal.LinearColor(1.0, 0.4, 0.0, 1.0),
                        3.0, 'CityPlace')
                else:
                    face_y = _PAD_CENTER_Y if lot['side'] == 'north' else -_PAD_CENTER_Y
                    yaw = 0.0 if lot['side'] == 'north' else 180.0
                    spawn_x = (lot['x0'] if lot['side'] == 'north'
                               else lot['x1'])
                    # ORDER MATTERS (the owner's own instruction): location
                    # -> identity -> label -> hidden off -> collision on,
                    # so the actor is never momentarily visible or solid
                    # while half-configured. The parcel's own Tick
                    # change-detection is what actually resolves the
                    # placeholder mesh - not a special case, the exact
                    # path a tier-up already uses.
                    pool_actor.set_actor_location_and_rotation(
                        unreal.Vector(spawn_x, face_y, 0.0),
                        unreal.Rotator(0.0, 0.0, yaw), False, False)
                    pool_actor.set_editor_property('RecipeId', unreal.Name(
                        new_state['parcels'][pid]['rid']))
                    pool_actor.set_editor_property(
                        'WidthUU',
                        float(new_state['parcels'][pid]['width']))
                    pool_actor.set_editor_property('Tier', 0)
                    pool_actor.set_editor_property('Owned', False)
                    pool_actor.set_editor_property('CornerSide', '')
                    pool_actor.set_actor_label(pid)
                    pool_actor.set_actor_hidden_in_game(False)
                    pool_actor.set_actor_enable_collision(True)
                    unreal.log('CITY PLACE: %s activated at (%.0f, %.0f)'
                               % (pid, spawn_x, face_y))
            _write_state(gi, new_state)
            _push_economy_fields(gi, new_state)

        # Economy tick, throttled Python-side (real seconds, not frames -
        # stable regardless of framerate).
        now = time.time()
        if just_started or now - state['last_tick'] >= _TICK_INTERVAL_S:
            state['last_tick'] = now
            city_state = _read_state(gi)
            new_state, events = _citytick.city_tick(
                city_state, _state_path_for())
            _log_tick_events(events)
            _write_state(gi, new_state)
            _push_economy_fields(gi, new_state)
            if just_started:
                # Once per session, before the first _sync_parcels - the
                # starter preset (if EmptyStart is false) comes back
                # first, placed lots layer on top of it second, both
                # onto dormant pool actors, so by the time sync runs it
                # just sees already-relabelled actors and does its
                # normal per-tick push, no special first-sync case
                # needed there.
                _reactivate_pinned_parcels(gw, gi)
                _reactivate_placed_parcels(gw, gi)
            _sync_parcels(gw, gi)
    except Exception as e:
        # ONE log per incident CLASS, not every tick — an exception here
        # must never spam-flood the log or, worse, look like it killed
        # the callback when it only killed one iteration.
        cls = type(e).__name__
        if cls not in state['seen_errors']:
            state['seen_errors'].add(cls)
            unreal.log_error(
                'CITY DRIVER: %s: %s (further occurrences of this error '
                'type suppressed this session)' % (cls, e))


def _ensure_screen_messages_enabled():
    """GAreScreenMessagesEnabled is PROCESS STATE, not project state — an
    editor restart reverts it, silently making every on-screen PrintString
    invisible again (the exact bug this session root-caused once already
    as Duration=0.0; this is the SAME symptom from a different cause, see
    HANDOFF.md Sec5). Calling it here means it survives every editor
    restart automatically instead of needing a manual console command
    each time. Idempotent in effect (the underlying flag is a plain
    bool), guarded here only to keep this from logging on every
    init_unreal.py re-import."""
    if getattr(unreal, '_stacktown_screen_messages_enabled', False):
        return
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = ues.get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'EnableAllScreenMessages')
    unreal._stacktown_screen_messages_enabled = True
    unreal.log('CITY DRIVER: EnableAllScreenMessages applied for this editor session')


def _register_city_driver():
    """Idempotent across repeated init_unreal.py imports within the same
    editor process. A bare module-level flag would NOT survive rung.sh's
    own module-cache purge — _guard.py drops every cached module that
    came from this project on each run (confirmed this session: repeated
    manual `import init_unreal` calls via rung.sh each re-executed this
    file's top level fresh). The guard therefore lives as an attribute
    on the `unreal` module itself, which is native/compiled and never
    purged by that logic."""
    if getattr(unreal, '_stacktown_driver_registered', False):
        unreal.log('CITY DRIVER: already registered this session, skipping')
        return
    unreal._stacktown_driver_state = {'last_tick': 0.0, 'seen_errors': set()}
    unreal._stacktown_driver_handle = unreal.register_slate_post_tick_callback(
        _city_driver_tick)
    unreal._stacktown_driver_registered = True
    unreal.log('CITY DRIVER: registered')


_register_city_driver()
_ensure_screen_messages_enabled()

# Player input (click/select/place/buy/hold-N reset) lives in clickdriver.py
# since 2026-09-03 - see its docstring for why it is not in BP_LensRig.
# Guarded so an input-side failure can never take the economy driver down.
try:
    import clickdriver  # noqa: F401  (registers its own slate callback)
except Exception as _e:
    unreal.log_warning('CLICK DRIVER: import failed - %s' % _e)
