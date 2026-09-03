"""Player input for the wooden beta, handled in-process (2026-09-03).

WHY THIS EXISTS: the click chain in BP_LensRig's tick could not be
written reliably by the Blueprint DSL in this build - three rewrites in
one night compiled clean and did nothing, the graph readers disagreed
about what was wired, and calling the rig's TickBody directly via
reflection at the instant of a real press still wrote no request (probe
runs, 2026-09-03 04:16-04:31). Input therefore lives HERE, next to the
economy driver that already owns every other verb, until the packaged
port re-homes both. BP_LensRig keeps EventBeginPlay (HUD construction)
and UpdateHUD on tick; both are proven to run.

Contract (request-and-clear channels on BP_StacktownGameInstance, same
shape as before, consumed by init_unreal's economy driver):
  left click on a BP_Parcel  -> SetHighlighted(True) on it, False on the
                                previous one, rig.SelectedParcel = actor
  left click on anything else-> PlaceRequestX/Y = hit location (the
                                driver's placement.place decides)
  B with a selection         -> BuyRequestPID = the parcel's LABEL (the
                                pid is the label, never GetName - see
                                PARCELIZATION_CONTRACT.md)
  hold N for RESET_HOLD_S    -> ResetRequested = True, once per press
                                (release re-arms), with an on-screen
                                "HOLD N TO RESET" countdown while held.

Registered as its own Slate post-tick callback, guarded on the `unreal`
module like the economy driver (survives _guard.py's module purge).
Self-test hooks (no mouse needed): `unreal._stacktown_click_at(x, y)`
runs the click logic for a world-space point exactly as a real press
would after the cursor trace; `unreal._stacktown_press('B'|'N')` runs
the key edges. The physical mouse edge itself is proven separately by
the probe runs above (is_input_key_down edges reached the controller).
"""
import unreal, time

RESET_HOLD_S = 2.0
_KEY = {}
for _name in ('LeftMouseButton', 'B', 'N'):
    _k = unreal.Key(); _k.set_editor_property('key_name', _name); _KEY[_name] = _k

_st = {'world': None, 'rig': None, 'down': {}, 'n_acc': 0.0, 'n_fired': False,
       'errs': set(), 'selected': None, 'rig_mirror_failed': False}


def _log(msg):
    unreal.log('CLICK: %s' % msg)


def _find_rig(gw):
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_class().get_name() == 'BP_LensRig_C':
            return a
    return None


def _is_parcel(actor):
    return actor is not None and actor.get_class().get_name() == 'BP_Parcel_C'


def _selected(rig):
    """The selection is held HERE. BP_LensRig's SelectedParcel variable is
    not instance-editable and the rig has no setter function, so the
    reflected write is refused (tested 2026-09-03); mirroring it onto the
    rig is attempted once per selection, silently, for the HUD's benefit
    if the variable ever becomes writable."""
    sel = _st.get('selected')
    if sel is None:
        return None
    try:
        if not unreal.SystemLibrary.is_valid(sel) or not _is_parcel(sel):
            _st['selected'] = None
            return None
    except Exception:
        _st['selected'] = None
        return None
    return sel


def _set_selected(rig, actor):
    prev = _selected(rig)
    if prev is not None and prev != actor:
        try:
            prev.call_method('SetHighlighted', args=(False,))
        except Exception as e:
            _log('SetHighlighted(False) failed on %s: %s' % (prev.get_actor_label(), e))
    if actor is not None:
        try:
            actor.call_method('SetHighlighted', args=(True,))
        except Exception as e:
            _log('SetHighlighted(True) failed on %s: %s' % (actor.get_actor_label(), e))
    _st['selected'] = actor
    if not _st.get('rig_mirror_failed'):
        try:
            rig.set_editor_property('SelectedParcel', actor)
        except Exception:
            _st['rig_mirror_failed'] = True
            _log('rig.SelectedParcel is not writable; selection held in Python (HUD cluster stays collapsed until the variable is made instance-editable)')


def click_at_hit(gw, gi, rig, actor, x, y):
    """The whole left-click decision, given what the cursor trace found."""
    if _is_parcel(actor):
        _set_selected(rig, actor)
        label = actor.get_actor_label()
        try:
            owned = actor.get_editor_property('Owned'); tier = actor.get_editor_property('Tier')
            status = 'owned, tier %d' % tier if owned else 'for sale'
        except Exception:
            status = ''
        unreal.SystemLibrary.print_string(gw, '%s  %s   [B] buy' % (label, status), True, False,
                                          unreal.LinearColor(0.7, 1.0, 0.8, 1.0), 2.5, 'clickmsg')
        _log('selected %s (%s)' % (label, status))
        return 'select'
    gi.set_editor_property('PlaceRequestX', float(x))
    gi.set_editor_property('PlaceRequestY', float(y))
    _log('place request at (%.0f, %.0f) [hit %s]' % (x, y, actor.get_actor_label() if actor else 'nothing'))
    return 'place'


def press_b(gw, gi, rig):
    sel = _selected(rig)
    if sel is None:
        unreal.SystemLibrary.print_string(gw, 'Select a lot first', True, False,
                                          unreal.LinearColor(1.0, 0.85, 0.3, 1.0), 1.5, 'clickmsg')
        _log('B with no selection')
        return False
    pid = sel.get_actor_label()
    gi.set_editor_property('BuyRequestPID', pid)
    _log('buy request %s' % pid)
    return True


def press_n_reset(gw, gi, rig):
    _set_selected(rig, None)
    gi.set_editor_property('ResetRequested', True)
    _log('RESET requested (N held %.1fs)' % RESET_HOLD_S)


def _tick(dt):
    try:
        gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if gw is None:
            if _st['world'] is not None:
                _st.update(world=None, rig=None, down={}, n_acc=0.0, n_fired=False, selected=None)
            return
        pc = unreal.GameplayStatics.get_player_controller(gw, 0)
        gi = unreal.GameplayStatics.get_game_instance(gw)
        if pc is None or gi is None:
            return
        if _st['world'] is not gw or _st['rig'] is None:
            _st['world'] = gw
            _st['rig'] = _find_rig(gw)
            _log('session start; rig=%s' % (_st['rig'].get_name() if _st['rig'] else None))
        rig = _st['rig']
        if rig is None:
            return
        edges = {}
        for name, key in _KEY.items():
            down = pc.is_input_key_down(key)
            edges[name] = down and not _st['down'].get(name, False)
            _st['down'][name] = down
        if edges['LeftMouseButton']:
            hit = pc.get_hit_result_under_cursor_by_channel(unreal.TraceTypeQuery.ECC_VISIBILITY, True)
            if hit is None:
                _log('click hit nothing')
            else:
                d = hit.to_dict()
                if not d.get('blocking_hit'):
                    _log('click hit nothing')
                else:
                    loc = d['location']
                    click_at_hit(gw, gi, rig, d.get('hit_actor'), loc.x, loc.y)
        if edges['B']:
            press_b(gw, gi, rig)
        if _st['down'].get('N', False):
            _st['n_acc'] += dt
            if not _st['n_fired']:
                remaining = max(0.0, RESET_HOLD_S - _st['n_acc'])
                unreal.SystemLibrary.print_string(gw, 'HOLD N TO RESET  %.1f' % remaining, True, False,
                                                  unreal.LinearColor(1.0, 0.4, 0.3, 1.0), 0.3, 'nhold')
                if _st['n_acc'] >= RESET_HOLD_S:
                    _st['n_fired'] = True
                    press_n_reset(gw, gi, rig)
        else:
            _st['n_acc'] = 0.0
            _st['n_fired'] = False
    except Exception as e:
        k = str(e)[:80]
        if k not in _st['errs']:
            _st['errs'].add(k)
            unreal.log_warning('CLICK: error %s' % e)


def _click_at(x, y):
    """Self-test: run the left-click decision for a world point (no mouse)."""
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if gw is None:
        return 'no PIE world'
    gi = unreal.GameplayStatics.get_game_instance(gw)
    rig = _st['rig'] or _find_rig(gw)
    start = unreal.Vector(float(x), float(y), 3000.0); end = unreal.Vector(float(x), float(y), -3000.0)
    hit = unreal.SystemLibrary.line_trace_single(gw, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
                                                 unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return 'trace hit nothing at (%s, %s)' % (x, y)
    d = hit.to_dict(); loc = d['location']
    return click_at_hit(gw, gi, rig, d.get('hit_actor'), loc.x, loc.y)


def _press(name):
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if gw is None:
        return 'no PIE world'
    gi = unreal.GameplayStatics.get_game_instance(gw)
    rig = _st['rig'] or _find_rig(gw)
    if name == 'B':
        return 'buy requested' if press_b(gw, gi, rig) else 'no selection'
    if name == 'N':
        press_n_reset(gw, gi, rig); return 'reset requested'
    return 'unknown key'


def register():
    old = getattr(unreal, '_stacktown_clickdriver_handle', None)
    if old is not None:
        unreal.unregister_slate_post_tick_callback(old)
    probe = getattr(unreal, '_stacktown_click_probe', None)
    if probe is not None:
        unreal.unregister_slate_post_tick_callback(probe)
        unreal._stacktown_click_probe = None
    unreal._stacktown_clickdriver_handle = unreal.register_slate_post_tick_callback(_tick)
    unreal._stacktown_click_at = _click_at
    unreal._stacktown_press = _press
    unreal.log('CLICK DRIVER: registered (hold N %.1fs to reset)' % RESET_HOLD_S)


register()
