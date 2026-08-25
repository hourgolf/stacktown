"""Put the repository's own tool directory on sys.path.

Sixteen scripts in this directory hardcoded

    /private/tmp/claude-501/-Users-ben-Documents-New-project/<uuid>/scratchpad

which is an agent scratchpad from a session that ended. `ue.py` - the MCP
client every generator script imports - existed ONLY there. On this machine the
directory happens to survive, so everything appeared to work; in a fresh
checkout `build_block.py` fails on `import ue` before it builds anything, which
means criterion 1 of the block milestone ("one script reproduces the block")
was not actually true.

Import this instead. It locates the project from its own __file__, so it works
from Content/Python, from a temp copy made by rung.sh (via _guard.py, which
imports it through the live project dir), and from a checkout anywhere on disk.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # Content/Python -> Content -> root


def install(root=None):
    root = root or ROOT
    for p in (os.path.join(root, 'Tools', 'measure'),
              os.path.join(root, 'Content', 'Python')):
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


install()
