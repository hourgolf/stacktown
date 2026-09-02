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
"""
import time

import citytick as _citytick
import econrules as _econrules
import unreal
import woodmap as _woodmap

_WOOD_MI_PATH = '/Game/Stacktown/Materials/MI_wood_%s.MI_wood_%s'

_TICK_INTERVAL_S = 2.0
_PARCEL_CLASS_PATH = '/Game/Stacktown/Runtime/BP_Parcel.BP_Parcel_C'


def _log_tick_events(events):
    for kind, pid, detail in events:
        if kind == 'TIER_UP':
            unreal.log('CITY TICK: %s tiered up to %s' % (pid, detail))
        elif kind == 'GROWTH_BLOCKED':
            unreal.log_warning('CITY TICK: %s %s' % (pid, detail))


def _read_state(gi):
    raw = gi.get_editor_property('CityStateJSON')
    return _citytick.json.loads(raw) if raw else _citytick.load_state()


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
        if pid not in state['parcels']:
            rid = str(a.get_editor_property('RecipeId'))
            width = a.get_editor_property('WidthUU')
            state, inserted = _citytick.ensure_parcel(state, pid, rid, width)
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
    if changed:
        _write_state(gi, state)


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
            state['pie_just_started'] = True
            return
        gi = unreal.GameplayStatics.get_game_instance(gw)
        if gi is None:
            return
        # A fresh PIE session's first tick runs the parcel sync
        # immediately rather than waiting up to _TICK_INTERVAL_S - avoids
        # an up-to-2s window where a just-loaded board shows authored
        # defaults instead of the reconciled state, right when selection
        # & camera feel (the thing being judged) is first on screen.
        just_started = state.pop('pie_just_started', False)

        # Reset channel: the owner's condition for accepting persistence
        # at all was an easy, loud way out of it. Same consume-and-clear
        # shape as buy, checked first so a reset always wins over
        # whatever else this tick would have done.
        if gi.get_editor_property('ResetRequested'):
            gi.set_editor_property('ResetRequested', False)
            fresh = _citytick.city_reset()
            unreal.log_warning(
                'CITYSTATE RESET (via GameInstance.ResetRequested): '
                'reseeded from money_start=%.1f' % fresh['money'])
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
            new_state, ok, reason = _citytick.city_buy(city_state, pid)
            if ok:
                unreal.log('CITY BUY: %s bought' % pid)
            else:
                unreal.log_warning('CITY BUY: %s refused - %s' % (pid, reason))
            _write_state(gi, new_state)
            _push_economy_fields(gi, new_state)

        # Economy tick, throttled Python-side (real seconds, not frames -
        # stable regardless of framerate).
        now = time.time()
        if just_started or now - state['last_tick'] >= _TICK_INTERVAL_S:
            state['last_tick'] = now
            city_state = _read_state(gi)
            new_state, events = _citytick.city_tick(city_state)
            _log_tick_events(events)
            _write_state(gi, new_state)
            _push_economy_fields(gi, new_state)
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
