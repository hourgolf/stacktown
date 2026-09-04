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

# TRACES ARE SIMPLE, NOT COMPLEX (2026-09-03 23:5x): bTraceComplex=True asks
# for per-triangle collision, which the baked wooden masses never carry -
# the cursor passed straight through every bought building to the board.
# Simple traces use the collision primitives: the pad cube's own box, the
# masses' box/hulls the design lane adds, the board's and roads' simple
# bodies (all measured), and NOT the ghost slab (0 prims - it must never
# eat the click that places it).

RESET_HOLD_S = 2.0
_KEY = {}


def _make_key(name):
    """An FKey by name in BOTH the editor and a standalone -game process:
    import_text is the struct's own text importer and works everywhere;
    set_editor_property('key_name') is editor-only (2026-09-04, found when
    the click driver failed to import in the standalone game)."""
    k = unreal.Key()
    try:
        k.import_text(name)
        return k
    except Exception:
        k.set_editor_property('key_name', name)
        return k


for _name in ('LeftMouseButton', 'B', 'N', 'U', 'R', 'MouseScrollUp', 'MouseScrollDown',
              'W', 'A', 'S', 'D', 'Q', 'E', 'Up', 'Down', 'Left', 'Right'):
    _KEY[_name] = _make_key(_name)

_st = {'world': None, 'rig': None, 'down': {}, 'n_acc': 0.0, 'n_fired': False,
       'errs': set(), 'selected': None, 'rig_mirror_failed': False, 'width_index': 0}


def _world():
    """The playing world in the editor (PIE) or in a standalone -game
    process - delegated to init_unreal's lookup so the two drivers agree."""
    import init_unreal as iu
    return iu._find_game_world()


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
            hint = '[U] upgrade  [R] repair' if owned else '[B] buy'
        except Exception:
            status = ''; hint = ''
        unreal.SystemLibrary.print_string(gw, '%s  %s   %s' % (label, status, hint), True, False,
                                          unreal.LinearColor(0.7, 1.0, 0.8, 1.0), 2.5, 'clickmsg')
        _log('selected %s (%s)' % (label, status))
        return 'select'
    unreal._stacktown_place_width = _current_width()
    gi.set_editor_property('PlaceRequestX', float(x))
    gi.set_editor_property('PlaceRequestY', float(y))
    _log('place request at (%.0f, %.0f) width %d [hit %s]' % (x, y, _current_width(), actor.get_actor_label() if actor else 'nothing'))
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


def press_u(gw, gi, rig):
    """UPGRADE the selected lot (owner's growth ruling 2026-09-03: growth is
    player-initiated, price climbs per level, poor performance charges a
    premium). Request rides a Python-side attribute consumed by the
    economy driver, like the width channel."""
    sel = _selected(rig)
    if sel is None:
        unreal.SystemLibrary.print_string(gw, 'Select a lot first', True, False,
                                          unreal.LinearColor(1.0, 0.85, 0.3, 1.0), 1.5, 'clickmsg')
        return False
    unreal._stacktown_upgrade_request = sel.get_actor_label()
    _log('upgrade request %s' % sel.get_actor_label())
    return True


def press_r(gw, gi, rig):
    """REPAIR the selected lot (pay to repair, owner's ruling 4)."""
    sel = _selected(rig)
    if sel is None:
        unreal.SystemLibrary.print_string(gw, 'Select a lot first', True, False,
                                          unreal.LinearColor(1.0, 0.85, 0.3, 1.0), 1.5, 'clickmsg')
        return False
    unreal._stacktown_repair_request = sel.get_actor_label()
    _log('repair request %s' % sel.get_actor_label())
    return True


def press_n_reset(gw, gi, rig):
    _set_selected(rig, None)
    gi.set_editor_property('ResetRequested', True)
    _log('RESET requested (N held %.1fs)' % RESET_HOLD_S)


# ---- Ghost pad (2026-09-03, owner: "go ahead with the ghost pad") ----
# While the cursor rests on empty plate, draw where a click would land and
# whether it would be accepted, using placement.resolve_click - the SAME
# pure resolver place() uses, so the preview can never disagree with the
# click. v0 draws it as a debug box (green = will place, red = refused)
# with a one-line label; a translucent pad mesh is the later polish.
GHOST_Z = 60.0
GHOST_COLOR_OK = unreal.LinearColor(0.35, 1.0, 0.55, 1.0)
GHOST_COLOR_NO = unreal.LinearColor(1.0, 0.35, 0.3, 1.0)


def _widths():
    import woodmap
    return list(woodmap.WIDTHS)


def _current_width():
    ws = _widths()
    i = max(0, min(_st.get('width_index', 0), len(ws) - 1))
    return float(ws[i])


def _cycle_width(step, gw):
    """Scroll wheel cycles the wood catalogue's width ladder for the ghost
    (PLACEMENT_GRID.md section 2.1a). Q/E deliberately NOT bound: they are
    the rig's zoom-ladder keys and would double-fire."""
    ws = _widths()
    _st['width_index'] = (_st.get('width_index', 0) + step) % len(ws)
    _st['ghost_cache'] = None
    unreal.SystemLibrary.print_string(gw, 'Lot width %d' % int(ws[_st['width_index']]), True, False,
                                      unreal.LinearColor(0.8, 0.9, 1.0, 1.0), 1.2, 'widthmsg')


def _lot_box(lot, iu, placement):
    """(cx, cy, hx, hy) of a lot's pad in world space, both roads."""
    half_w = (lot['x1'] - lot['x0']) / 2.0
    mid = (lot['x0'] + lot['x1']) / 2.0
    depth_h = placement.BLOCK_DEPTH / 2.0
    if placement.lot_road_id(lot) == 'cross':
        cx = -iu._PAD_CENTER_Y if lot['side'] == 'west' else iu._PAD_CENTER_Y
        return (cx, mid, depth_h, half_w)
    cy = iu._PAD_CENTER_Y if lot['side'] == 'north' else -iu._PAD_CENTER_Y
    return (mid, cy, half_w, depth_h)


# ---- Ghost actor (D22): a translucent pad instead of the debug box ----
# Borrows the HIGHEST-numbered dormant POOL_ parcel (activation claims the
# lowest, so they never meet until the pool is nearly exhausted), sets its
# Building component to MI_ghost_accept / MI_ghost_refuse (translucent
# instances proven through disk by mk_ghost_mi.py), drives its size
# through WidthUU (the parcel's own change-detection scales the pad) and
# parks it hidden again when the cursor leaves the plate. Runtime-only:
# nothing here is ever saved. The debug label stays for the reason text.
GHOST_MI = {'accept': '/Game/Stacktown/Materials/MI_ghost_accept',
            'refuse': '/Game/Stacktown/Materials/MI_ghost_refuse'}
GHOST_SLAB = '/Game/Stacktown/BakedWood/SM_GhostPad_w%d'


def placement_half():
    import citylayout
    return citylayout.HALF


def _ghost_actor(gw):
    g = _st.get('ghost')
    if g is not None:
        try:
            if unreal.SystemLibrary.is_valid(g):
                return g
        except Exception:
            pass
    best = None
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_class().get_name() != 'BP_Parcel_C':
            continue
        lab = a.get_actor_label()
        if lab.startswith('POOL_') and not lab.startswith('POOL_PIN_'):
            if best is None or lab > best.get_actor_label():
                best = a
    _st['ghost'] = best
    _st['ghost_shown'] = False
    return best


def _ghost_show(gw, ok, box, lot):
    g = _ghost_actor(gw)
    if g is None or box is None:
        return False
    import init_unreal as iu
    x, y, yaw = iu._lot_transform(lot)
    width = abs(lot['x1'] - lot['x0'])
    try:
        g.set_actor_location_and_rotation(unreal.Vector(x, y, 2.0), unreal.Rotator(0.0, 0.0, yaw), False, False)
        comps = [c for c in g.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == 'Building']
        if comps:
            c = comps[0]
            # The baked slab for this width (design lane, D22: five assets,
            # front-left pivot, 1500 deep, 12 uu proud rim). The parcel's
            # own WidthUU is never touched, so its change-detection never
            # runs and never rescales or repositions this component.
            sm_path = GHOST_SLAB % int(width)
            sm = unreal.load_asset(sm_path)
            if sm is not None:
                if c.get_editor_property('static_mesh') != sm:
                    c.set_static_mesh(sm)
                    c.set_relative_scale3d(unreal.Vector(1.0, 1.0, 1.0))
                want = unreal.Vector(0.0, -(iu._PAD_CENTER_Y - placement_half()), 0.0)
            else:
                # no slab baked for this width: fall back to the scaled cube
                want = unreal.Vector(width / 2.0, 0.0, 0.0)
                if float(g.get_editor_property('WidthUU')) != float(width):
                    g.set_editor_property('WidthUU', float(width))
            mi = unreal.load_asset(GHOST_MI['accept' if ok else 'refuse'])
            if mi is not None and c.get_material(0) != mi:
                c.set_material(0, mi)
            cur = c.get_editor_property('relative_location')
            if abs(cur.x - want.x) > 0.5 or abs(cur.y - want.y) > 0.5:
                c.set_relative_location(want, False, False)
        if not _st.get('ghost_shown'):
            g.set_actor_enable_collision(False)
            g.set_actor_hidden_in_game(False)
            _st['ghost_shown'] = True
        return True
    except Exception as e:
        k = 'ghost:' + str(e)[:60]
        if k not in _st['errs']:
            _st['errs'].add(k); unreal.log_warning('CLICK: ghost actor error %s' % e)
        return False


def _ghost_hide():
    g = _st.get('ghost')
    if g is None or not _st.get('ghost_shown'):
        return
    try:
        g.set_actor_hidden_in_game(True)
    except Exception:
        pass
    _st['ghost_shown'] = False


def _preview(gi, x, y):
    """(ok, short_reason, box) - box is (cx, cy, hx, hy) or None."""
    import init_unreal as iu
    import placement
    state = iu._read_state(gi)
    try:
        pins_active = not bool(gi.get_editor_property('EmptyStart'))
    except Exception:
        pins_active = True
    width = _current_width()
    ok, reason, lot = placement.resolve_click(state, x, y, pins_active=pins_active, width=width)
    box = None
    if lot is not None:
        box = _lot_box(lot, iu, placement)
    elif reason.startswith('overlap'):
        # resolve_click gives no lot on overlap; show the refused span anyway,
        # in the winning road's frame.
        road, local = placement.resolve_road(placement.ROADS, x, y)
        if road is not None:
            axis = 0 if road['axis'] == 'x' else 1
            a0 = placement._snap(road['start'][axis] + local['along'] - width / 2.0)
            box = _lot_box({'x0': a0, 'x1': a0 + width, 'side': local['side'], 'road_id': road['id']}, iu, placement)
    short = iu._place_refusal_message(reason) if not ok else 'click to place  (width %d, scroll to change)' % int(width)
    ghost_lot = lot
    if ghost_lot is None and box is not None:
        # refused overlap: rebuild the lot dict the box was drawn from
        road, local = placement.resolve_road(placement.ROADS, x, y)
        if road is not None:
            axis = 0 if road['axis'] == 'x' else 1
            a0 = placement._snap(road['start'][axis] + local['along'] - width / 2.0)
            ghost_lot = {'x0': a0, 'x1': a0 + width, 'side': local['side'], 'road_id': road['id']}
    _st['ghost_lot'] = ghost_lot
    return ok, short, box


def _draw_ghost(gw, ok, text, box, x, y):
    color = GHOST_COLOR_OK if ok else GHOST_COLOR_NO
    if box is not None:
        cx, cy, hx, hy = box
        unreal.SystemLibrary.draw_debug_box(gw, unreal.Vector(cx, cy, GHOST_Z),
                                            unreal.Vector(hx, hy, 12.0), color,
                                            unreal.Rotator(0.0, 0.0, 0.0), 0.05, 3.0)
        unreal.SystemLibrary.draw_debug_string(gw, unreal.Vector(cx, cy, GHOST_Z + 80.0), text, None, color, 0.05)
    else:
        unreal.SystemLibrary.draw_debug_string(gw, unreal.Vector(x, y, GHOST_Z + 80.0), text, None, color, 0.05)


def _hover(gw, gi, pc):
    hit = pc.get_hit_result_under_cursor_by_channel(unreal.TraceTypeQuery.ECC_VISIBILITY, False)
    if hit is None:
        return
    d = hit.to_dict()
    if not d.get('blocking_hit') or _is_parcel(d.get('hit_actor')):
        _ghost_hide()
        return
    loc = d['location']
    key = (round(loc.x / 20.0), round(loc.y / 20.0))
    cache = _st.get('ghost_cache')
    if cache is None or cache[0] != key:
        ok, text, box = _preview(gi, loc.x, loc.y)
        cache = (key, ok, text, box)
        _st['ghost_cache'] = cache
    ok, text, box = cache[1], cache[2], cache[3]
    shown = _ghost_show(gw, ok, box, _st.get('ghost_lot')) if box is not None else False
    if not shown:
        _ghost_hide()
    # The translucent pad carries the close stops; at the far stop D22's own
    # analysis says only a RIM survives downsampling (checked on a capture,
    # 2026-09-03: the 34% fill is a smudge at reach 19000). Until a mesh rim
    # exists, the debug outline IS the rim - drawn over the pad, thinner
    # than the box-only ghost was.
    _draw_ghost(gw, ok, text, box, loc.x, loc.y)


# ---- Camera (2026-09-04): the rig re-applies its pose from its own
# variables every tick, so the driver writes the VARIABLES and the rig
# renders them. Same architecture as selection: Python owns input.
# A/D orbit (Azimuth), W/S reel (Reach, continuous), Q/E the reach ladder
# (the camera study's stops), arrows pan BoardCentre in the camera frame.
CAM_LADDER = (19000.0, 3500.0, 1350.0, 800.0)
CAM_ORBIT_DEG_S = 60.0
CAM_REEL_PER_S = 0.9          # fraction of reach per second, W in / S out
CAM_PAN_UU_S = 2500.0
_cam_state = {'warned': False}


def _rig_get(rig, name, default=None):
    for n in ('Tgt' + name, name):
        try:
            return rig.get_editor_property(n)
        except Exception:
            continue
    return default


def _rig_set(rig, name, value):
    """Write a pose value. The rig carries a TARGET twin of each pose
    variable (TgtAzimuth beside Azimuth, ...) and eases the live value
    toward it every tick, so the target is what input must move; the
    live variable is written too so a rig without easing still follows."""
    ok = False
    for n in ('Tgt' + name, name):
        try:
            rig.set_editor_property(n, value)
            ok = True
        except Exception as e:
            if not _cam_state['warned']:
                _cam_state['warned'] = True
                _log('camera: rig.%s is not writable (%s) - needs the instance-editable flag' % (n, str(e)[:60]))
    return ok


def _camera_tick(rig, pc, dt):
    down = _st['down']
    az = _rig_get(rig, 'Azimuth'); reach = _rig_get(rig, 'Reach')
    if az is None or reach is None:
        return
    d_az = (CAM_ORBIT_DEG_S * dt) * ((1 if down.get('D') else 0) - (1 if down.get('A') else 0))
    if d_az:
        _rig_set(rig, 'Azimuth', (float(az) + d_az) % 360.0)
    reel = (1 if down.get('S') else 0) - (1 if down.get('W') else 0)
    if reel:
        new_reach = float(reach) * (1.0 + reel * CAM_REEL_PER_S * dt)
        _rig_set(rig, 'Reach', max(400.0, min(30000.0, new_reach)))
    edges = _st.get('edges', {})
    if edges.get('Q') or edges.get('E'):
        # step the ladder: Q closer, E farther, from the nearest stop
        r = float(_rig_get(rig, 'Reach', reach))
        idx = min(range(len(CAM_LADDER)), key=lambda i: abs(CAM_LADDER[i] - r))
        idx = idx + (1 if edges.get('Q') else -1)
        idx = max(0, min(len(CAM_LADDER) - 1, idx))
        _rig_set(rig, 'Reach', CAM_LADDER[idx])
    px = (1 if down.get('Right') else 0) - (1 if down.get('Left') else 0)
    py = (1 if down.get('Up') else 0) - (1 if down.get('Down') else 0)
    if px or py:
        import math
        a = math.radians(float(_rig_get(rig, 'Azimuth', az)))
        # camera-frame pan: forward is toward the board centre from the camera
        fwd = (-math.cos(a), -math.sin(a)); right = (-fwd[1], fwd[0])
        step = CAM_PAN_UU_S * dt
        c = _rig_get(rig, 'BoardCentre')
        if c is not None:
            nx = c.x + step * (px * right[0] + py * fwd[0]); ny = c.y + step * (px * right[1] + py * fwd[1])
            try:
                rig.set_editor_property('BoardCentre', unreal.Vector(nx, ny, c.z))
            except Exception:
                pass


def _tick(dt):
    try:
        gw = _world()
        if gw is None:
            if _st['world'] is not None:
                _st.update(world=None, rig=None, down={}, n_acc=0.0, n_fired=False, selected=None, ghost_cache=None, ghost=None, ghost_shown=False, ghost_lot=None)
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
        _st['edges'] = edges
        _camera_tick(rig, pc, dt)
        if not _st['down'].get('LeftMouseButton', False):
            _hover(gw, gi, pc)
        else:
            _ghost_hide()
        if edges['LeftMouseButton']:
            hit = pc.get_hit_result_under_cursor_by_channel(unreal.TraceTypeQuery.ECC_VISIBILITY, False)
            if hit is None:
                _log('click hit nothing')
            else:
                d = hit.to_dict()
                if not d.get('blocking_hit'):
                    _log('click hit nothing')
                else:
                    loc = d['location']
                    click_at_hit(gw, gi, rig, d.get('hit_actor'), loc.x, loc.y)
        if edges['MouseScrollUp']:
            _cycle_width(+1, gw)
        if edges['MouseScrollDown']:
            _cycle_width(-1, gw)
        if edges['B']:
            press_b(gw, gi, rig)
        if edges['U']:
            press_u(gw, gi, rig)
        if edges['R']:
            press_r(gw, gi, rig)
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
    gw = _world()
    if gw is None:
        return 'no PIE world'
    gi = unreal.GameplayStatics.get_game_instance(gw)
    rig = _st['rig'] or _find_rig(gw)
    start = unreal.Vector(float(x), float(y), 3000.0); end = unreal.Vector(float(x), float(y), -3000.0)
    hit = unreal.SystemLibrary.line_trace_single(gw, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
                                                 unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return 'trace hit nothing at (%s, %s)' % (x, y)
    d = hit.to_dict(); loc = d['location']
    return click_at_hit(gw, gi, rig, d.get('hit_actor'), loc.x, loc.y)


def _press(name):
    gw = _world()
    if gw is None:
        return 'no PIE world'
    gi = unreal.GameplayStatics.get_game_instance(gw)
    rig = _st['rig'] or _find_rig(gw)
    if name == 'B':
        return 'buy requested' if press_b(gw, gi, rig) else 'no selection'
    if name == 'U':
        return 'upgrade requested' if press_u(gw, gi, rig) else 'no selection'
    if name == 'R':
        return 'repair requested' if press_r(gw, gi, rig) else 'no selection'
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
    unreal._stacktown_ghost_at = lambda x, y: (_preview(unreal.GameplayStatics.get_game_instance(_world()), x, y), _ghost_show(_world(), _st['ghost_cache'][1] if _st.get('ghost_cache') else True, _preview(unreal.GameplayStatics.get_game_instance(_world()), x, y)[2], _st.get('ghost_lot')))[1]
    unreal._stacktown_set_width_index = lambda i: _st.__setitem__('width_index', int(i)) or _st.__setitem__('ghost_cache', None)
    unreal._stacktown_preview = lambda x, y: _preview(unreal.GameplayStatics.get_game_instance(_world()), x, y)
    unreal.log('CLICK DRIVER: registered (hold N %.1fs to reset)' % RESET_HOLD_S)


register()
