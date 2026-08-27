"""Throttle the render thread for a long headless bake, and RESTORE after.

WHY. Three MetalRHI crashes today, all in the render thread
(MetalCommandList / ProcessInterruptQueue). A fastbake needs no viewport at
all - it builds geometry through GeometryScript and never draws the model -
so every frame the editor renders during a 30-minute wave is pure exposure to
the failing subsystem for no benefit.

t.MaxFPS 8 cuts the command buffers submitted per second by roughly an order
of magnitude. It is a HYPOTHESIS aimed at the subsystem that actually fails,
not a fix: the fault is a GPU/driver issue and nothing in Python prevents it.

RESTORE IS NOT OPTIONAL. Console variables are session state - they survive
level loads and saves and appear in no diff. `lumen_defaults.py` exists
because a previous diagnostic of mine left four cvars at 0 and the owner spent
a session judging a crippled renderer. Prior value was measured, not assumed:
t.MaxFPS was 0.000 (uncapped).

    rung.sh wave_throttle.py           throttle to 8 fps

TO RESTORE, USE cvar.py - NOT AN ARGUMENT TO THIS SCRIPT:

    printf "t.MaxFPS 0\n" > "$TMPDIR/stacktown_cvar.txt" && rung.sh cvar.py

rung.sh passes ONLY the script path to uepy and forwards no arguments, so the
`restore` argv branch this file used to carry never fired - running it a second
time silently re-applied the throttle and printed that it had restored. Caught
by reading the output rather than trusting it; a restore that reports success
without a read-back is the same class of thing as a gate that passes without
looking. cvar.py takes its value from a temp FILE for exactly this reason.
"""
import unreal

PRIOR = 0.0          # measured before changing anything: uncapped
unreal.SystemLibrary.execute_console_command(None, 't.MaxFPS 8')
now = unreal.SystemLibrary.get_console_variable_float_value('t.MaxFPS')
print('THROTTLE t.MaxFPS -> 8 (read back %g)  restore with cvar.py, see header'
      % now)
