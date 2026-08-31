"""Drop every project module from the editor's import cache.

The editor process is long-lived and `import genbuild` returns whatever was
first loaded, however long ago. Roughly 18 files changed under this session
during the rebuild, so anything run from memory would be running the OLD code
while reporting on the NEW level - the worst kind of wrong, because it looks
like it worked.

Removing them from sys.modules forces the next import to read from disk. Names
are taken from what is actually loaded, not a hand-kept list, so a module added
later cannot be missed.
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
dropped = []
for name, mod in list(sys.modules.items()):
    f = getattr(mod, '__file__', None) or ''
    try:
        if f and os.path.dirname(os.path.abspath(f)) == HERE:
            del sys.modules[name]
            dropped.append(name)
    except Exception:
        pass
print('purged %d project modules from the editor cache' % len(dropped))
print('  ' + ', '.join(sorted(dropped)) if dropped else '  (cache was clean)')
