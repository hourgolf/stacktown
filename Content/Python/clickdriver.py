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


for _name in ('LeftMouseButton', 'B', 'N', 'U', 'H', 'G', 'L', 'Q', 'E', 'MouseScrollUp', 'MouseScrollDown'):
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


def _hold_selection(gw, gi, rig):
    """Every tick while a lot is selected: keep it highlighted and keep its
    line on screen (2026-09-04, owner: "when I select a lot it is only
    selected for a second"). Any driver write to a BP_Parcel re-runs its
    construction script, which resets its Highlighted flag; the parcel's own
    tick then swaps the highlight material back off. Re-asserting here makes
    the Python selection the one that shows."""
    sel = _selected(rig)
    if sel is None:
        _st['sel_line'] = None
        return
    try:
        if not sel.get_editor_property('Highlighted'):
            sel.call_method('SetHighlighted', args=(True,))
    except Exception:
        pass
    line = _st.get('sel_line')
    if line:
        n = _st.get('sel_line_tick', 0) + 1
        _st['sel_line_tick'] = n
        if n % 60 == 0:
            line = _selection_line(gi, sel) or line
            _st['sel_line'] = line
        unreal.SystemLibrary.print_string(gw, line, True, False, unreal.LinearColor(0.7, 1.0, 0.8, 1.0), 0.6, 'selline')


def _selection_line(gi, actor):
    try:
        label = actor.get_actor_label()
        owned = actor.get_editor_property('Owned'); tier = actor.get_editor_property('Tier')
        status = 'owned, level %d' % tier if owned else 'for sale'
        if owned:
            import init_unreal as iu, econrules
            st = iu._read_state(gi); p = st['parcels'].get(label, {})
            try:
                price = econrules.upgrade_price(p.get('rid', 'vernacular'), int(p.get('tier', tier)), float(p.get('performance', 0.0) or 0.0))
                hint = '[U] upgrade $%.0f   [H] repair' % price
            except Exception:
                hint = '[U] upgrade   [H] repair'
        else:
            hint = '[B] buy $%.0f' % float(actor.get_editor_property('Price'))
        return '%s  %s   %s' % (label, status, hint)
    except Exception:
        return None


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
    if actor is None:
        _st['sel_line'] = None
    # never mirrored into the rig - see the tick's note on the rig's writes


def click_at_hit(gw, gi, rig, actor, x, y):
    """The whole left-click decision, given what the cursor trace found."""
    if _is_parcel(actor):
        _set_selected(rig, actor)
        label = actor.get_actor_label()
        try:
            owned = actor.get_editor_property('Owned'); tier = actor.get_editor_property('Tier')
            status = 'owned, level %d' % tier if owned else 'for sale'
            if owned:
                import init_unreal as iu, econrules
                st = iu._read_state(gi); p = st['parcels'].get(label, {})
                try:
                    price = econrules.upgrade_price(p.get('rid', 'vernacular'), int(p.get('tier', tier)), float(p.get('performance', 0.0) or 0.0))
                    hint = '[U] upgrade $%.0f   [H] repair' % price
                except Exception:
                    hint = '[U] upgrade   [H] repair'
            else:
                hint = '[B] buy $%.0f' % float(actor.get_editor_property('Price'))
        except Exception:
            status = ''; hint = ''
        _st['sel_line'] = '%s  %s   %s' % (label, status, hint)
        _st['sel_line_tick'] = 0
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
    """REPAIR the selected lot (pay to repair, owner's ruling 4). Bound to H:
    R is the rig's pedestal-up key (Docs/LENSRIG_P0.md)."""
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


def _lot_box(lot, iu, placement, state=None):
    """(cx, cy, hx, hy) of a lot's pad in world space, for ANY road: the
    lot's own road (by id, from placement's dynamic list) gives the axis
    and the centreline; the pad sits at +/-1880 from it on the lot's side."""
    half_w = (lot['x1'] - lot['x0']) / 2.0
    mid = (lot['x0'] + lot['x1']) / 2.0
    depth_h = placement.BLOCK_DEPTH / 2.0
    roads = {r['id']: r for r in placement._all_roads(state if state is not None else {'parcels': {}, 'roads': {}})}
    road = roads.get(placement.lot_road_id(lot)) or roads.get('arterial')
    if road['axis'] == 'y':
        cx = float(road['start'][0]) + (-iu._PAD_CENTER_Y if lot['side'] == road['side_plus'] else iu._PAD_CENTER_Y)
        return (cx, mid, depth_h, half_w)
    cy = float(road['start'][1]) + (iu._PAD_CENTER_Y if lot['side'] == road['side_plus'] else -iu._PAD_CENTER_Y)
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
    gi = unreal.GameplayStatics.get_game_instance(gw)
    x, y, yaw = iu._lot_transform(lot, iu._read_state(gi) if gi is not None else None)
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
        box = _lot_box(lot, iu, placement, state)
    elif reason.startswith('overlap'):
        # resolve_click gives no lot on overlap; show the refused span anyway,
        # in the winning road's frame.
        road, local = placement.resolve_road(placement._all_roads(state), x, y)
        if road is not None:
            axis = 0 if road['axis'] == 'x' else 1
            a0 = placement._snap(road['start'][axis] + local['along'] - width / 2.0)
            box = _lot_box({'x0': a0, 'x1': a0 + width, 'side': local['side'], 'road_id': road['id']}, iu, placement, state)
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


# ---- Camera: NOT here (2026-09-04). BP_LensRig's own boom-space input is
# alive and complete (Docs/LENSRIG_P0.md: A/D arc, W/S reach, R/F pedestal,
# arrows head pan/tilt, E tighter, Q wider) - a Python camera on the same
# keys gave every pose variable two writers, which the owner felt as
# "wonky" and "can't zoom out". The driver owns clicks and verbs only.
# Consequence: REPAIR moved from R (the rig's pedestal-up) to H.


# ---- Road mode (ROAD_BUILD_CONTRACT.md section 4, 2026-09-04) ----
# G toggles road mode (not a rig key). First click = start, second click =
# end; the chord is previewed through placement.resolve_road_draw - the
# same pure function draw_road uses - so the ghost cannot disagree with
# the verb. Axis-aligned segments only in v0 (the module's own rule).
ROAD_COLOR_OK = unreal.LinearColor(0.85, 0.85, 0.7, 1.0)
ROAD_COLOR_NO = unreal.LinearColor(1.0, 0.35, 0.3, 1.0)


def _road_mode_toggle(gw):
    _st['road_mode'] = not _st.get('road_mode', False)
    _st['road_start'] = None
    unreal.SystemLibrary.print_string(gw, 'ROAD MODE %s' % ('ON - click start, click end (G to leave)' if _st['road_mode'] else 'off'),
                                      True, False, ROAD_COLOR_OK, 3.0, 'roadmode')
    _log('road mode %s' % ('on' if _st['road_mode'] else 'off'))


def _road_preview(gi, x0, y0, x1, y1):
    import init_unreal as iu
    import placement
    state = iu._read_state(gi)
    try:
        pins_active = not bool(gi.get_editor_property('EmptyStart'))
    except Exception:
        pins_active = True
    ok, reason, road = placement.resolve_road_draw(state, x0, y0, x1, y1, pins_active=pins_active)
    return ok, reason, road


def _road_hover(gw, gi, pc):
    """In road mode with a start set: draw the chord to the cursor."""
    start = _st.get('road_start')
    if start is None:
        return
    hit = pc.get_hit_result_under_cursor_by_channel(unreal.TraceTypeQuery.ECC_VISIBILITY, False)
    if hit is None:
        return
    d = hit.to_dict()
    if not d.get('blocking_hit'):
        return
    loc = d['location']
    ok, reason, road = _road_preview(gi, start[0], start[1], loc.x, loc.y)
    color = ROAD_COLOR_OK if ok else ROAD_COLOR_NO
    if road is not None:
        (sx, sy), (ex, ey) = road['start'], road['end']
    else:
        sx, sy, ex, ey = start[0], start[1], loc.x, loc.y
    unreal.SystemLibrary.draw_debug_line(gw, unreal.Vector(sx, sy, GHOST_Z + 20.0), unreal.Vector(ex, ey, GHOST_Z + 20.0), color, 0.05, 40.0)
    text = 'click to lay the road' if ok else reason.split(':')[0]
    unreal.SystemLibrary.draw_debug_string(gw, unreal.Vector((sx + ex) / 2.0, (sy + ey) / 2.0, GHOST_Z + 120.0), text, None, color, 0.05)


def _road_click(gw, gi, x, y):
    start = _st.get('road_start')
    if start is None:
        _st['road_start'] = (x, y)
        unreal.SystemLibrary.print_string(gw, 'Road start set - click the end', True, False, ROAD_COLOR_OK, 2.0, 'roadmode')
        _log('road start (%.0f, %.0f)' % (x, y))
        return
    unreal._stacktown_road_request = (start[0], start[1], x, y)
    _log('road request (%.0f, %.0f) -> (%.0f, %.0f)' % (start[0], start[1], x, y))
    _st['road_start'] = None


_cam_state = {}


# The rig's own ladder, copied from its EventBeginPlay arrays (beta lane's
# read, 2026-09-04) as a FALLBACK: the leftover click chain empties those
# arrays along with the targets, so a rebuild cannot rely on reading them.
LADDER_FALLBACK = {
    'focal': [24.0, 50.0, 85.0, 135.0, 200.0],
    'standoff': [19000.0, 11168.0, 3500.0, 1350.0, 800.0],
    'height': [9000.0, 3400.0, 700.0, 1000.0, 900.0],
    'tilt': [-25.0, -10.0, -5.0, -5.0, -2.0],
}


def _ladder_tables(rig):
    """(focal, standoff, height, tilt) from the rig, or the fallback when
    the rig's arrays read empty or short."""
    try:
        f = list(rig.get_editor_property('LadderFocal')); st = list(rig.get_editor_property('LadderStandoff'))
        h = list(rig.get_editor_property('LadderHeight')); t = list(rig.get_editor_property('LadderTilt'))
        if min(len(f), len(st), len(h), len(t)) >= 5:
            return f, st, h, t
    except Exception:
        pass
    return (LADDER_FALLBACK['focal'], LADDER_FALLBACK['standoff'], LADDER_FALLBACK['height'], LADDER_FALLBACK['tilt'])


def _nearest_stop(reach):
    st = LADDER_FALLBACK['standoff']
    return min(range(len(st)), key=lambda i: abs(st[i] - reach))


def _ladder_step(rig, delta):
    """Q/E, with the stop OWNED HERE (2026-09-04). Read from the owner's game
    log: the rig's ladder arrays are empty at runtime and its StopIndex is
    reset to 0 by every reflected write we make to the rig (a write re-runs
    the construction script, which resets the rig's non-instance-editable
    variables to their class defaults - empty arrays, index 0). So the rig's
    own Q/E branch always reads Ladder[idx] of an empty array (four engine
    warnings per press) and writes 0 into all four targets, and any index it
    keeps is gone by the next frame. Neither can be trusted; this steps from
    the rung nearest the current reach (so W/S free zoom composes with the
    ladder) and writes the pose itself, after the rig's branch, on the same
    frame."""
    try:
        prev = _st.get('cam_prev')
        stop = _cam_state.get('stop', 0)
        if prev is not None and prev.get('TgtReach', 0.0) >= 300.0:
            stop = _nearest_stop(prev['TgtReach'])
        idx = max(0, min(int(stop) + int(delta), 4))
        _cam_state['stop'] = idx
        # the rig eased its live values one step toward the origin this frame
        # (its targets read 0 for the whole world tick): put them back first,
        # then aim at the new rung so the move eases from where the view was
        if prev is not None and prev.get('live'):
            for k, v in prev['live'].items():
                rig.set_editor_property(k, float(v))
        L = LADDER_FALLBACK
        rig.set_editor_property('TgtFocal', float(L['focal'][idx]))
        rig.set_editor_property('TgtReach', float(L['standoff'][idx]))
        rig.set_editor_property('TgtHeight', float(L['height'][idx]))
        rig.set_editor_property('TgtTilt', float(L['tilt'][idx]))
        _st['cam_prev'] = _cam_snapshot(rig)
        _log('ladder %s -> stop %d: reach %.0f height %.0f tilt %.1f focal %.0f' % (
            'E' if delta > 0 else 'Q', idx, L['standoff'][idx], L['height'][idx], L['tilt'][idx], L['focal'][idx]))
    except Exception as e:
        if not _cam_state.get('ladder_warned'):
            _cam_state['ladder_warned'] = True
            _log('ladder step unavailable: %s' % str(e)[:80])


# ---- Clicks never move the camera; keys never lose the game (2026-09-04,
# owner: "Q/E works up until I click into a lot to build - camera then drops
# down and is useless after that"). The rig's own graph still runs a click
# branch on a REAL mouse press (a headless select does not trigger it and
# leaves the camera alone - measured), and after that click the owner's log
# shows no key edges at all. Two mitigations, both driver-side:
#   1. a rolling copy of the boom targets; on a mouse-down frame any target
#      the rig's click branch moved is written back (the rig ticks before
#      this callback, so the write-back wins the frame);
#   2. keyboard focus is returned to the game viewport on every mouse-down
#      (and at session start), so a click can never strand the keys on a
#      widget.
_CAM_KEYS = ('TgtReach', 'TgtHeight', 'TgtTilt', 'TgtFocal', 'TgtAzimuth', 'TgtPan')


_LIVE_KEYS = ('Reach', 'Height', 'Tilt', 'Focal')


def _cam_snapshot(rig):
    snap = {}
    try:
        for k in _CAM_KEYS:
            snap[k] = float(rig.get_editor_property(k))
        c = rig.get_editor_property('BoardCentre')
        snap['BoardCentre'] = (c.x, c.y, c.z)
        snap['live'] = dict((k, float(rig.get_editor_property(k))) for k in _LIVE_KEYS)
    except Exception:
        return None
    return snap


def _cam_hold_on_click(rig):
    prev = _st.get('cam_prev')
    if prev is None:
        return
    now = _cam_snapshot(rig)
    if now is None:
        return
    moved = []
    for k in _CAM_KEYS:
        if abs(now[k] - prev[k]) > 1e-3:
            try:
                rig.set_editor_property(k, prev[k]); moved.append(k)
            except Exception:
                pass
    if any(abs(a - b) > 1e-3 for a, b in zip(now['BoardCentre'], prev['BoardCentre'])):
        try:
            rig.set_editor_property('BoardCentre', unreal.Vector(*prev['BoardCentre'])); moved.append('BoardCentre')
        except Exception:
            pass
    if moved:
        _log('click moved the camera (%s) - restored' % ', '.join(moved))


def _focus_game(pc):
    try:
        unreal.WidgetBlueprintLibrary.set_input_mode_game_only(pc)
    except Exception as e:
        if not _cam_state.get('focus_warned'):
            _cam_state['focus_warned'] = True
            _log('could not force game input mode: %s' % str(e)[:60])
    try:
        unreal.WidgetBlueprintLibrary.set_focus_to_game_viewport()
    except Exception:
        pass


def _cam_sanity(rig):
    """Guard for a frame where the targets read impossible (reach under the
    rig's own W clamp of 300, or focal under 1) outside a Q/E frame: restore
    the whole pose from the previous frame's snapshot. Never snaps to a rung
    (the old rebuild did, and every rebuild write reset the rig's StopIndex,
    which is what relocked the wide pose on each E press)."""
    try:
        reach = float(rig.get_editor_property('TgtReach')); focal = float(rig.get_editor_property('TgtFocal'))
    except Exception:
        return
    if reach >= 300.0 and focal >= 1.0:
        return
    try:
        prev = _st.get('cam_prev')
        if prev is not None:
            for k in _CAM_KEYS:
                rig.set_editor_property(k, float(prev[k]))
            for k, v in (prev.get('live') or {}).items():
                rig.set_editor_property(k, float(v))
            how = 'restored the previous frame'
        else:
            L = LADDER_FALLBACK; idx = int(_cam_state.get('stop', 0))
            rig.set_editor_property('TgtFocal', float(L['focal'][idx])); rig.set_editor_property('TgtReach', float(L['standoff'][idx]))
            rig.set_editor_property('TgtHeight', float(L['height'][idx])); rig.set_editor_property('TgtTilt', float(L['tilt'][idx]))
            how = 'rebuilt rung %d' % idx
        import time
        if time.time() - _cam_state.get('sanity_logged', 0.0) > 2.0:
            _cam_state['sanity_logged'] = time.time()
            _log('camera targets read zero outside Q/E - %s' % how)
    except Exception as e:
        if not _cam_state.get('sanity_warned'):
            _cam_state['sanity_warned'] = True
            _log('camera sanity unavailable: %s' % str(e)[:80])

def _tick(dt):
    try:
        gw = _world()
        if gw is None:
            if _st['world'] is not None:
                _st.update(world=None, rig=None, down={}, n_acc=0.0, n_fired=False, selected=None, ghost_cache=None, ghost=None, ghost_shown=False, ghost_lot=None, road_mode=False, road_start=None)
            return
        pc = unreal.GameplayStatics.get_player_controller(gw, 0)
        gi = unreal.GameplayStatics.get_game_instance(gw)
        if pc is None or gi is None:
            return
        if _st['world'] is not gw or _st['rig'] is None:
            _st['world'] = gw
            _st['rig'] = _find_rig(gw)
            _log('session start; rig=%s' % (_st['rig'].get_name() if _st['rig'] else None))
            _focus_game(pc)
            _st['cam_prev'] = None
            _cam_state['stop'] = 0
            # Interim key legend until HUD v1 carries it (owner never found road
            # mode; the legend is the cheapest discoverability there is).
            unreal.SystemLibrary.print_string(gw, 'KEYS   click: place / select   scroll: lot width   B buy   U upgrade   H repair   G road mode   L night   hold N reset   |   A/D orbit  W/S reach  Q/E zoom  R/F height  arrows aim',
                                              True, False, unreal.LinearColor(0.85, 0.9, 1.0, 1.0), 12.0, 'keylegend')
        rig = _st['rig']
        if rig is None:
            return
        edges = {}
        for name, key in _KEY.items():
            down = pc.is_input_key_down(key)
            edges[name] = down and not _st['down'].get(name, False)
            _st['down'][name] = down
        _st['edges'] = edges
        if edges.get('E'):
            _ladder_step(rig, +1)
        elif edges.get('Q'):
            _ladder_step(rig, -1)
        else:
            _cam_sanity(rig)
        if not edges['LeftMouseButton'] and not (edges.get('E') or edges.get('Q')):
            _st['cam_prev'] = _cam_snapshot(rig)
        # The rig's SelectedParcel is never written from here (2026-09-04): a
        # reflected write to the rig re-runs its construction script and resets
        # its non-instance-editable variables (StopIndex, the ladder arrays).
        # The selection lives in Python; the rig's variable stays None and its
        # HUD cluster collapsed until HUD v1 reads the selection from here.
        _hold_selection(gw, gi, rig)
        if edges['G']:
            _road_mode_toggle(gw)
            _ghost_hide()
        if edges['L']:
            import init_unreal as iu
            night = 0.0 if getattr(unreal, '_stacktown_night', 0.0) >= 0.5 else 1.0
            if iu._set_night(gw, night):
                unreal.SystemLibrary.print_string(gw, 'NIGHT' if night >= 0.5 else 'DAY', True, False,
                                                  unreal.LinearColor(0.8, 0.85, 1.0, 1.0), 1.5, 'daynight')
                _log('night -> %.0f' % night)
            else:
                unreal.SystemLibrary.print_string(gw, 'No night yet (parameter collection missing)', True, False,
                                                  unreal.LinearColor(1.0, 0.85, 0.3, 1.0), 2.0, 'daynight')
        road_mode = _st.get('road_mode', False)
        if road_mode:
            _ghost_hide()
            _road_hover(gw, gi, pc)
        elif not _st['down'].get('LeftMouseButton', False):
            _hover(gw, gi, pc)
        else:
            _ghost_hide()
        if edges['LeftMouseButton']:
            _cam_hold_on_click(rig)
            _focus_game(pc)
        if edges['LeftMouseButton'] and road_mode:
            hit = pc.get_hit_result_under_cursor_by_channel(unreal.TraceTypeQuery.ECC_VISIBILITY, False)
            if hit is not None:
                d = hit.to_dict()
                if d.get('blocking_hit'):
                    _road_click(gw, gi, d['location'].x, d['location'].y)
        elif edges['LeftMouseButton']:
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
        if edges['H']:
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
    if name in ('R', 'H'):
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
    unreal._stacktown_draw_road = lambda x0, y0, x1, y1: setattr(unreal, '_stacktown_road_request', (x0, y0, x1, y1)) or 'road requested'
    unreal._stacktown_ghost_at = lambda x, y: (_preview(unreal.GameplayStatics.get_game_instance(_world()), x, y), _ghost_show(_world(), _st['ghost_cache'][1] if _st.get('ghost_cache') else True, _preview(unreal.GameplayStatics.get_game_instance(_world()), x, y)[2], _st.get('ghost_lot')))[1]
    unreal._stacktown_set_width_index = lambda i: _st.__setitem__('width_index', int(i)) or _st.__setitem__('ghost_cache', None)
    unreal._stacktown_preview = lambda x, y: _preview(unreal.GameplayStatics.get_game_instance(_world()), x, y)
    unreal.log('CLICK DRIVER: registered (hold N %.1fs to reset)' % RESET_HOLD_S)


register()
