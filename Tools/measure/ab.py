"""A/B a material parameter with the return control built in.

Every result this returns has been checked two ways:
  * the frame was SETTLED before measuring (two consecutive captures within the
    noise floor), because the first capture after a material edit is a
    transient - measured at 47.5 mean-abs-diff on an identical scene;
  * the parameter was RESTORED and the frame re-measured, and if it does not
    come back to the baseline the result is reported as VOID rather than as a
    number. A run whose baseline drifted cannot tell an effect from the drift,
    and this project has already published two conclusions that were drift.
"""
import subprocess, json, img, cap2, settle

FLOOR = 4.3

def setp(entries):
    r = subprocess.run(['./runparam.sh', json.dumps(entries)], capture_output=True, text=True)
    if 'WRONG' in r.stdout or 'ERROR' in r.stdout:
        raise SystemExit('param set refused: %s' % r.stdout[:300])

def baseline(tag='ab_base', view='zoom'):
    im, p, n = settle.settled(tag, view, verbose=False)
    return im

def trial(tag, entries, restores, base, stat, view='zoom'):
    """Apply entries, settle, measure `stat(im)`, restore, verify return."""
    setp(entries)
    im, _, _ = settle.settled(tag, view, verbose=False)
    val = stat(im)
    whole = img.mean_abs_diff(base, im)
    setp(restores)
    back, _, _ = settle.settled(tag + '_r', view, verbose=False)
    ret = img.mean_abs_diff(base, back)
    return {'stat': val, 'whole': whole, 'return': ret,
            'ok': ret <= FLOOR, 'img': im}

def report(name, r, base_stat, sigma=None):
    flag = '' if r['ok'] else '   *** VOID: return control %.2f > %.2f ***' % (r['return'], FLOOR)
    s = '  %-28s stat %8.4f (%+8.4f)   whole-frame %7.3f   ret %.2f%s' % (
        name, r['stat'], r['stat'] - base_stat, r['whole'], r['return'], flag)
    if sigma:
        s += '\n      %.1f sigma' % (abs(r['stat'] - base_stat) / sigma)
    print(s)
