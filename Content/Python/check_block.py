"""City geometry check - every block in the table, not just block A.

WHAT WAS WRONG. The previous version imported LOTS from lots.py, which is
block A alone. It printed "geometry check: PASS (0 failures)" throughout the
construction of blocks B and C and that PASS covered none of them. A check that
looks like coverage and is not is worse than no check, and this project has the
scar tissue to prove it - core_check compared only street-side edges and passed
five buildings while every one of them was hollow.

ADJACENCY comes from the city table: within a block, lots sorted by x0 are
neighbours and may share up to PARTY. Lots in DIFFERENT blocks are never
neighbours and may not overlap at all.

TWO SELF-CHECKS, both derived from the table rather than hardcoded:
  1. an Assetsville flank sits at its lot edge, +/- its 15 uu thickness
  2. a block C lot's world X extent, which exercises the yaw-180 transform -
     the place a coordinate bug would actually hide
"""
import unreal, math
import _path
from city import BLOCKS

PARTY = 40.0
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def world_aabb(c):
    sm = c.static_mesh
    if not sm: return None
    b = sm.get_bounds(); o = b.origin; e = b.box_extent; t = c.get_world_transform()
    lo = [1e18]*3; hi = [-1e18]*3
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                w = t.transform_location(unreal.Vector(o.x+sx*e.x, o.y+sy*e.y, o.z+sz*e.z))
                for i, v in enumerate((w.x, w.y, w.z)):
                    lo[i] = min(lo[i], v); hi[i] = max(hi[i], v)
    return lo, hi


def lot_world_x(blk, spec):
    """Predicted world X span of a lot, through the block transform."""
    ox, oy, _ = blk['origin']; yaw = math.radians(blk['yaw'])
    xs = []
    for lx in (spec['x0'], spec['x0'] + spec['width']):
        for ly in (0.0, spec['depth']):
            xs.append(ox + lx*math.cos(yaw) - ly*math.sin(yaw))
    return min(xs), max(xs)


# --- group world AABBs by building ------------------------------------------
G = {}
for a in eas.get_all_level_actors():
    l = a.get_actor_label(); parts = l.split('_')
    k = None
    if parts[0] in ('BLD2', 'ELEV', 'CORE'): k = parts[1] if len(parts) > 1 else None
    elif l.startswith('AV_'):  k = 'AV'
    elif l.startswith('BLD_'): k = 'Stage1'
    if not k: continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if not c.is_visible(): continue
        r = world_aabb(c)
        if not r: continue
        g = G.setdefault(k, [list(r[0]), list(r[1])])
        for i in range(3):
            g[0][i] = min(g[0][i], r[0][i]); g[1][i] = max(g[1][i], r[1][i])

fail = 0

# --- self-check 1: Assetsville flank at its lot edge -------------------------
av = None
for blk in BLOCKS:
    for spec in blk['lots']:
        if spec['kind'] == 'av': av = spec
if av:
    lo_e, hi_e = av['x0'] - 15.0, av['x0'] + 15.0
    got = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith('AV_flank'):
            r = world_aabb(a.static_mesh_component)
            if r and abs(r[0][0] - lo_e) < 2: got = r; break
    ok = got is not None
    print('SELF-CHECK 1  AV flank X %s  expected %.1f..%.1f  %s'
          % ('%.1f..%.1f' % (got[0][0], got[1][0]) if ok else 'NOT FOUND',
             lo_e, hi_e, 'OK' if ok else 'MISMATCH'))
    if not ok: fail += 1

# --- self-check 2: a rotated block's lot lands where the table says ---------
probe = None
for blk in BLOCKS:
    if blk['yaw'] == 180.0 and blk['lots']:
        probe = (blk, sorted(blk['lots'], key=lambda l: l['x0'])[0]); break
if probe:
    blk, spec = probe
    ex_lo, ex_hi = lot_world_x(blk, spec)
    g = G.get(spec['name'])
    if g:
        d = max(abs(g[0][0] - ex_lo), abs(g[1][0] - ex_hi))
        ok = d < 120.0        # facade slab and flank stand proud of the lot line
        print('SELF-CHECK 2  %s (block %s, yaw 180) X %.0f..%.0f  expected %.0f..%.0f  '
              'worst %.0f uu  %s' % (spec['name'], blk['name'], g[0][0], g[1][0],
                                     ex_lo, ex_hi, d, 'OK' if ok else 'MISMATCH'))
        if not ok: fail += 1
    else:
        print('SELF-CHECK 2  %s not in the level  MISMATCH' % spec['name']); fail += 1

# --- report ------------------------------------------------------------------
print()
order, neighbours = [], set()
by_block = {}
for blk in BLOCKS:
    ls = sorted(blk['lots'], key=lambda l: l['x0'])
    names = [l['name'] for l in ls]
    # An open zone has no mass, so it is not part of the party-wall or
    # missing-building checks. Demanding a building-shaped AABB from a plaza
    # would fail it forever.
    ls = [l for l in ls if l['kind'] in ('gen', 'av')]
    names = [l['name'] for l in ls]
    if blk['name'] == 'A': names = ['Stage1'] + names
    by_block[blk['name']] = names
    order += names
    for i in range(len(names) - 1):
        neighbours.add(frozenset((names[i], names[i+1])))
# back-to-back rows of an island block share a rear party line, so any lot of
# one row may touch any lot of the other
for blk in BLOCKS:
    other = blk.get('island_with')
    if not other or other not in by_block: continue
    for a_ in by_block[blk['name']]:
        for b_ in by_block[other]:
            neighbours.add(frozenset((a_, b_)))
present = [k for k in order if k in G]
for k in present:
    lo, hi = G[k]
    print('%-8s X %7.0f..%7.0f  Y %7.0f..%7.0f  Z %6.0f..%6.0f'
          % (k, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
missing = [k for k in order if k not in G]
if missing:
    print('\nNOT IN LEVEL: %s' % ', '.join(missing)); fail += len(missing)

print()
for i in range(len(present)):
    for j in range(i + 1, len(present)):
        A, B = G[present[i]], G[present[j]]
        ov = [min(A[1][n], B[1][n]) - max(A[0][n], B[0][n]) for n in range(3)]
        if not all(v > 1.0 for v in ov): continue
        pair = frozenset((present[i], present[j]))
        share = min(ov[0], ov[1])      # a rear party line shares in Y, not X
        if pair in neighbours and share <= PARTY:
            print('party wall  %-8s / %-8s  shares %.0f uu  OK'
                  % (present[i], present[j], share))
        else:
            print('FAIL        %-8s / %-8s  overlap X%.0f Y%.0f Z%.0f  %s'
                  % (present[i], present[j], ov[0], ov[1], ov[2],
                     'too deep' if pair in neighbours else 'NOT NEIGHBOURS'))
            fail += 1
print()
print('geometry check: %s (%d failures) over %d buildings in %d blocks'
      % ('PASS' if fail == 0 else 'FAIL', fail, len(present), len(BLOCKS)))
