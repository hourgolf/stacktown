"""Which buildings each gate rule is entitled to judge.

Why this exists, stated plainly because it is the whole design:

    The gate encodes "articulated street building" as its only definition
    of good.

GATE-03 wants parts per m2 of elevation, GATE-07 wants mass behind the front
third, GATE-08 wants a rear face that carries parts. Those are the right
questions for a terrace and the WRONG questions for a warehouse or a barn -
an industrial shell is defined precisely by not being an articulated street
elevation. A gate that refuses correct work teaches people to pass it with
--force, and a forced gate is worse than no gate: it still stamps the mesh.

So the applicability is declared, on BOTH sides, before any such geometry
exists:

  - every archetype here declares what "good" means for it and which rules
    do not apply to it (with a reason - a skip without a reason is a rule
    quietly turned off);
  - every rule in modelgate.py declares, via `judges=`, which archetypes it
    is entitled to judge.

That is a double-entry ledger, deliberately. It is NOT the two-copies-of-0.70
drift this project forbids: thresholds are still spelled once (in qc.py) and
read from there. What is written twice is the yes/no applicability matrix,
and `check_declarations` fails the whole gate the moment the two entries
disagree - adding a rule forces a decision about every archetype, adding an
archetype forces a decision about every rule, and neither can happen by
accident or omission.

Three doctrines carried over from the rest of the project:

  1. FAIL CLOSED. An archetype this file does not list raises
     UnknownArchetype - it never falls through to 'street'. Same doctrine as
     citygeom.zone_layouts: a name nobody declared is a bug, not a default.
  2. SKIPS ARE VISIBLE. A rule an archetype exempts appears in the verdict
     as an explicit SKIPPED line. This project's worst bug class is checks
     that silently stop having an opinion (DETAIL-01 after a merge,
     core_check on street-side edges); a silent archetype skip would be the
     same bug installed on purpose.
  3. THRESHOLDS LIVE IN qc.py. An archetype may override a rule's threshold,
     but the override VALUE is a qc.py constant. Never a second copy of a
     number that exists elsewhere.

Pure functions over plain data, no `unreal` import, self-tested against
planted defects - for the same reason modelgate.py is.
"""
import contextlib

from qc import DETAIL_MIN_INDUSTRIAL

DEFAULT = 'street'


class UnknownArchetype(KeyError):
    """An archetype nobody declared. Raised, never defaulted."""


# name -> dict(
#   good:      one line saying what a CORRECT model of this archetype is,
#   exempt:    {rule_id: reason} - rules that do not judge this archetype;
#              the reason is printed in the verdict's SKIPPED line,
#   overrides: {rule_id: {CONSTANT_NAME: value}} - thresholds this archetype
#              is judged at instead of the street value. The value must be a
#              qc.py constant, and the CONSTANT_NAME must be one the rule
#              actually reads, or `patched` refuses to run.
# )
#
# 'industrial' and 'agricultural-structure' are SPECULATIVE: no such geometry
# exists yet. That is the point - the definition of good is declared before
# the first model is built, so the gate never meets one it has no opinion
# about. Declaring the archetype here is mandatory BEFORE building for it.
ARCHETYPES = {
    'street': dict(
        good='an articulated street elevation: dense parts, glazed floors, '
             'a dressed rear, mass through the depth',
        exempt={},
        overrides={},
    ),
    'industrial': dict(
        good='a working shell: large plain elevations, mass as one honest '
             'volume, openings where work needs them - correct by NOT being '
             'an articulated street front',
        exempt={
            'GATE-07': 'a shed is one volume; articulation behind the front '
                       'third is the street question, not the works question',
            'GATE-08': 'the rear of a depot is a working wall with a door in '
                       'it, not an elevation to dress',
        },
        overrides={
            # judged, but at the industrial density - a shed still has SOME
            # fittings (doors, vents, downpipes), it is not a featureless box
            'GATE-03': dict(DETAIL_MIN=DETAIL_MIN_INDUSTRIAL),
        },
    ),
    'agricultural-structure': dict(
        good='a plain timber or sheet shell standing on open land: a barn is '
             'correct exactly where a street building would be defective',
        exempt={
            'GATE-03': 'plainness is the point; parts per m2 of elevation is '
                       'the street measure a barn is defined by not having',
            'GATE-07': 'a barn is one volume front to back; there is no '
                       '"front third" to hide behind',
            'GATE-08': 'the back of a barn is the same wall as the front of '
                       'it, and neither is dressed',
            'GATE-09': 'a hay loft is a floor with no window mandate; '
                       'openings follow the work, not the storey count',
        },
        overrides={},
    ),
}


def names():
    return tuple(ARCHETYPES)


def get(name):
    """The archetype record, or UnknownArchetype. NEVER a default."""
    try:
        return ARCHETYPES[name]
    except KeyError:
        raise UnknownArchetype(
            '%r is not a declared archetype (declared: %s). Declare it in '
            'archetypes.py BEFORE building for it - the gate does not '
            'default an unknown name to street.' % (name, ', '.join(names())))


def of_spec(spec):
    """The archetype a spec claims. Absent (or None) means 'street' - that
    is the entire existing catalogue - but a PRESENT unknown name raises."""
    name = spec.get('archetype')
    if name is None:
        return DEFAULT
    get(name)
    return name


def applies(arch, rule_):
    """(True, None) if `rule_` judges `arch`, else (False, reason).

    Reads BOTH declarations and refuses to answer if they disagree - a
    disagreement means someone edited one ledger entry and not the other,
    and guessing which one they meant is how a rule silently stops (or
    silently starts) having an opinion.
    """
    a = get(arch)
    rule_side = arch in (rule_.get('judges') or ())
    arch_side = rule_['id'] not in a['exempt']
    if rule_side != arch_side:
        raise RuntimeError(
            'declaration mismatch on %s / %s: the rule says judges=%s, the '
            'registry says exempt=%s. Fix BOTH ledger entries.'
            % (rule_['id'], arch, rule_.get('judges'),
               sorted(a['exempt'])))
    if rule_side:
        return True, None
    return False, a['exempt'][rule_['id']]


def overrides_for(arch, rule_id):
    return get(arch)['overrides'].get(rule_id, {})


@contextlib.contextmanager
def patched(module, overrides):
    """Run a rule with an archetype's threshold in place of the street one.

    The rule bodies are untouched - they keep reading their module-level
    constants, which is what guarantees the street path stays byte-identical
    - so an override works by rebinding the constant on the gate module for
    the duration of one rule call, and restoring it even on an exception.

    A name the module does not carry raises instead of silently binding a
    constant nothing reads - an override that does nothing is a check that
    stopped having an opinion, this project's worst bug class.
    """
    saved = {}
    for k in overrides:
        if not hasattr(module, k):
            raise AttributeError(
                'override %r names a constant %s does not read - it would '
                'silently do nothing' % (k, module.__name__))
        saved[k] = getattr(module, k)
    try:
        for k, v in overrides.items():
            setattr(module, k, v)
        yield
    finally:
        for k, v in saved.items():
            setattr(module, k, v)


def check_declarations(rules):
    """Every disagreement between the two ledgers, as strings. Empty = sound."""
    problems = []
    ids = {r['id'] for r in rules}
    for r in rules:
        j = r.get('judges')
        if not j:
            problems.append('%s declares no judges= - every rule must say '
                            'which archetypes it is entitled to judge'
                            % r['id'])
            continue
        for a in j:
            if a not in ARCHETYPES:
                problems.append('%s judges undeclared archetype %r'
                                % (r['id'], a))
    for name, a in ARCHETYPES.items():
        for rid in list(a['exempt']) + list(a['overrides']):
            if rid not in ids:
                problems.append('%s exempts/overrides unknown rule %r'
                                % (name, rid))
        for rid, why in a['exempt'].items():
            if not (isinstance(why, str) and why.strip()):
                problems.append('%s exempts %s without a reason - a skip '
                                'without a reason is a rule turned off'
                                % (name, rid))
        both = set(a['exempt']) & set(a['overrides'])
        if both:
            problems.append('%s both exempts and overrides %s - pick one'
                            % (name, sorted(both)))
    for r in rules:
        j = set(r.get('judges') or ())
        for name, a in ARCHETYPES.items():
            if (name in j) != (r['id'] not in a['exempt']):
                problems.append(
                    'ledger mismatch %s / %s: rule judges=%s, registry '
                    'exempt=%s' % (r['id'], name, sorted(j),
                                   sorted(a['exempt'])))
    return problems


# =========================== self-tests =====================================
# House style: every behaviour proves it can detect its own planted defect,
# and ALSO proves the clean case passes - only the pair catches a test that
# fails everything or passes everything.
SELFTESTS = {}


def _selftest(name):
    def deco(fn):
        SELFTESTS[name] = fn
        return fn
    return deco


def _mg():
    import modelgate
    return modelgate


def _legacy_findings(mg, m):
    """The pre-archetype gate loop, VERBATIM (modelgate.run as it stood
    before archetypes existed): every rule, no skips, no overrides. This is
    the 'old path' the street invariant is proved against."""
    findings = []
    for r in mg.RULES:
        for subj, detail in r['check'](m):
            findings.append((r['id'], subj, detail))
    return findings


def _blankrear(mg, archetype=None):
    """A facade plus one roof deck: fails GATE-07 and GATE-08 as a street
    building. Correct-shaped data for a speculative shed, which is the
    scaling review's exact case."""
    box = lambda y0, y1: ([0.0, y0, 0.0], [mg.SPEC['width'], y1, 400.0])
    comps = [mg._c('Wall_F%d' % i, aabb=box(0.0, 40.0)) for i in range(29)]
    comps.append(mg._c('Roof_Deck', aabb=box(0.0, 1200.0)))
    sp = dict(mg.SPEC)
    if archetype is not None:
        sp['archetype'] = archetype
    return mg.model(sp, [mg._a('BLD2_Probe_H', comps)])


def _defect_models(mg):
    """The known-answer fleet: _clean() plus one planted defect per family
    of rule, built the way the modelgate self-tests build them."""
    models = [('clean', mg._clean())]

    m = mg._clean()
    m['actors'][0]['comps'].append(mg._c('Bogus_Thing'))
    models.append(('role-less part (GATE-01)', m))

    m = mg._clean()
    m['actors'][0]['comps'].append(
        mg._c('Wall_X', mats=['WorldGridMaterial']))
    models.append(('default material (GATE-02)', m))

    thin = max(1, int(mg.elevation_m2(mg.SPEC) * mg.DETAIL_MIN) - 5)
    models.append(('thin elevation (GATE-03)', mg._clean(n=thin)))

    m = mg.model(mg.SPEC, [mg._a('BLD2_Probe_H',
                                 [mg._c('Wall_P%d' % i, mats=['MI_a'])
                                  for i in range(60)])])
    models.append(('one material (GATE-04)', m))

    m = mg._clean()
    wide = ([0.0, 0.0, 0.0],
            [mg.SPEC['width'] * 1.5, mg.SPEC['depth'], 400.0])
    m['actors'][0]['comps'].append(mg._c('Wall_Wide', aabb=wide))
    models.append(('over the parcel line (GATE-05)', m))

    m = mg._clean()
    m['actors'][0]['comps'].append(mg._c('StaticMesh12'))
    models.append(('auto-renamed part (GATE-06)', m))

    models.append(('blank rear (GATE-07/08/09)', _blankrear(mg)))

    import cores
    sp = dict(mg.SPEC)
    sp.update(floors=4, gf_h=400.0, fl_h=280.0, parapet=40.0,
              open_roof=True, style='vernacular')
    ct = max(b[1] for b in cores.bands_for(sp))
    fr = cores.bands_for(sp)[-1][2]
    bx = lambda z0, z1: ([0.0, fr + 20.0, z0],
                         [mg.SPEC['width'], fr + 220.0, z1])
    comps = [mg._c('Wall_A%d' % i, aabb=bx(0.0, ct - 40.0)) for i in range(9)]
    comps.append(mg._c('Tile_Deck2', aabb=bx(ct - 8.0, ct)))
    models.append(('coplanar with core top (GATE-10)',
                   mg.model(sp, [mg._a('BLD2_Probe_H', comps)])))
    return models


@_selftest('ARCH-UNKNOWN')
def _t_unknown():
    """An undeclared archetype raises. Falling through to 'street' is the
    planted defect - if either call below returns instead of raising, the
    gate has a default nobody chose."""
    mg = _mg()
    try:
        of_spec(dict(archetype='warehouse'))
        return False                    # fell through - the defect
    except UnknownArchetype:
        pass
    m = _blankrear(mg, archetype='warehouse')
    try:
        mg.judge(m)                     # resolution inside the gate itself
        return False
    except UnknownArchetype:
        pass
    # and the two spellings of "no archetype" both mean street
    return (of_spec(dict()) == 'street'
            and of_spec(dict(archetype=None)) == 'street')


@_selftest('ARCH-DECL')
def _t_decl():
    """The double-entry ledger is sound, and the check SEES each way of
    breaking it: a rule with no declaration, a rule judging an undeclared
    archetype, and the two ledgers disagreeing."""
    mg = _mg()
    if check_declarations(mg.RULES):
        return False                    # the real ledgers must be sound
    if not check_declarations([dict(id='GATE-XX', judges=None)]):
        return False                    # undeclared rule not seen
    if not check_declarations([dict(id='GATE-XX', judges=('suburban',))]):
        return False                    # undeclared archetype not seen
    # a rule that claims to judge an archetype the registry exempts it from
    fake = dict(id='GATE-07', judges=names())
    if not any('mismatch' in p for p in check_declarations([fake])):
        return False
    # applies() must refuse to guess on the same mismatch, not pick a side
    try:
        applies('industrial', fake)
        return False
    except RuntimeError:
        return True


@_selftest('ARCH-STREET-IDENTICAL')
def _t_street_identical():
    """THE invariant: with archetype absent or 'street', the new path
    produces byte-identical findings to the pre-archetype loop, and no
    skips, on the clean model and every planted-defect model."""
    mg = _mg()
    for label, m in _defect_models(mg):
        legacy = _legacy_findings(mg, m)
        new, skips = mg.judge(m)        # spec carries no archetype: street
        if skips or repr(new) != repr(legacy):
            return False
        new2, skips2 = mg.judge(m, 'street')   # spelled explicitly
        if skips2 or repr(new2) != repr(legacy):
            return False
        if label != 'clean' and not legacy:
            return False                # a defect model its rule cannot see
    return True


@_selftest('ARCH-SKIP-VISIBLE')
def _t_skip_visible():
    """Every exempted rule appears in the verdict as an explicit SKIPPED
    line naming the rule, the archetype and the reason. A skip that fails
    to appear is the planted defect."""
    mg = _mg()
    for arch in ('industrial', 'agricultural-structure'):
        exempt = get(arch)['exempt']
        _, skips = mg.judge(_blankrear(mg), arch)
        if len(skips) != len(exempt):
            return False                # a skip failed to appear
        for rid, line in skips:
            if rid not in exempt or 'SKIPPED' not in line \
                    or arch not in line or exempt[rid] not in line:
                return False
    return True


@_selftest('ARCH-EXEMPT-ENFORCED')
def _t_exempt_enforced():
    """A rule exempted for an archetype is NOT executed against it - proved
    by counting calls, not by absence of findings. The same model must make
    the same rule fire as street, or the counter proves nothing."""
    mg = _mg()
    r7 = next(r for r in mg.RULES if r['id'] == 'GATE-07')
    calls = []
    orig = r7['check']
    r7['check'] = lambda m: (calls.append(1) or True) and orig(m)
    try:
        f, _ = mg.judge(_blankrear(mg), 'industrial')
        if calls:
            return False                # ran against an exempted archetype
        if any(rid in ('GATE-07', 'GATE-08') for rid, _s, _d in f):
            return False
        f, _ = mg.judge(_blankrear(mg), 'street')
        if not calls:
            return False                # counter inert - test sees nothing
        if not any(rid == 'GATE-07' for rid, _s, _d in f):
            return False
    finally:
        r7['check'] = orig
    return True


@_selftest('ARCH-OVERRIDE')
def _t_override():
    """An override is judged at the archetype's qc.py threshold - looser
    than street where the street number would refuse correct work, but
    still a real gate below it - and the street constant is restored
    afterwards, exceptions included."""
    import qc
    mg = _mg()
    area = mg.elevation_m2(mg.SPEC)
    mid = int(area * (qc.DETAIL_MIN + DETAIL_MIN_INDUSTRIAL) / 2.0)
    m = mg._clean(n=mid)                # between the two thresholds
    if not any(r == 'GATE-03' for r, _s, _d in mg.judge(m, 'street')[0]):
        return False                    # street must refuse it...
    if any(r == 'GATE-03' for r, _s, _d in mg.judge(m, 'industrial')[0]):
        return False                    # ...industrial must not
    thin = mg._clean(n=max(1, int(area * DETAIL_MIN_INDUSTRIAL) - 3))
    hits = [d for r, _s, d in mg.judge(thin, 'industrial')[0]
            if r == 'GATE-03']
    if len(hits) != 1 or ('under %.2f' % DETAIL_MIN_INDUSTRIAL) not in hits[0]:
        return False                    # override skipped instead of judged
    if mg.DETAIL_MIN != qc.DETAIL_MIN:
        return False                    # the street constant leaked
    # restoration survives a rule blowing up mid-call
    try:
        with patched(mg, dict(DETAIL_MIN=DETAIL_MIN_INDUSTRIAL)):
            raise ValueError('planted')
    except ValueError:
        pass
    if mg.DETAIL_MIN != qc.DETAIL_MIN:
        return False
    # and an override naming a constant the gate does not read refuses
    try:
        with patched(mg, dict(NO_SUCH_CONSTANT=1.0)):
            pass
        return False
    except AttributeError:
        return True


def selftest(verbose=False):
    """True only if every archetype behaviour sees its own planted defect."""
    ok = True
    for name in sorted(SELFTESTS):
        good = False
        try:
            good = bool(SELFTESTS[name]())
        except Exception as e:
            if verbose:
                print('  %s raised %r' % (name, e))
        if verbose:
            print('  %-24s %s' % (name, 'ok' if good else 'FAILED'))
        ok = ok and good
    return ok


if __name__ == '__main__':
    # Run everything through the CANONICAL imported instance, not this
    # __main__ one: modelgate imports `archetypes` by name, so running the
    # file directly would otherwise put two copies of UnknownArchetype in
    # play and the raise-detection test would catch the wrong class.
    import archetypes as A
    print('archetype self-tests:')
    ok = A.selftest(verbose=True)
    print('all pass:', ok)
    if ok:
        import modelgate as mg
        print('\nexample: the blank-rear model, judged as each archetype')
        for arch in A.names():
            f, skips = mg.judge(A._blankrear(mg), arch)
            print('  as %s: %d finding(s)' % (arch, len(f)))
            for rid, s, d in f:
                print('    %s %s: %s' % (rid, s, d))
            for rid, line in skips:
                print('    %s %s' % (rid, line))
