#!/usr/bin/env python3
"""Build block B only - the far side of the street, rotated 180 degrees."""
import os, subprocess, sys, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
for f in ('.mcp_sid',):
    try: os.remove(os.path.join(HERE,f))
    except OSError: pass
from city import BLOCKS
from genbuild import build as genbuild
def ue(script,label):
    t=time.time()
    r=subprocess.run(['./rung.sh',script],capture_output=True,text=True,cwd=HERE)
    ok='success: True' in r.stdout
    print('  %-20s %5.1fs %s'%(label,time.time()-t,'ok' if ok else 'FAILED'))
    for l in r.stdout.splitlines():
        if l.startswith('[Info]') and 'guard' not in l: print('      '+l[7:])
    if not ok: print('      '+r.stdout[-300:])
B=[b for b in BLOCKS if b['name']=='B'][0]
print('=== block B: %d lots, origin %s yaw %.0f ==='%(len(B['lots']),B['origin'],B['yaw']))
t=time.time()
for spec in B['lots']:
    if spec['kind']!='gen': continue
    genbuild(spec, origin=B['origin'], yaw=B['yaw'])
print('  generated in %.0fs'%(time.time()-t))
ue('step_roles.py','materials')
ue('step_cores3.py','cores')
ue('practicals.py','practicals')
print('block B complete')
