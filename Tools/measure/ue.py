#!/usr/bin/env python3
"""Persistent client for the native Unreal MCP bridge (UE 5.8, streamable HTTP)."""
import json, math, sys, os, urllib.request

URL = "http://127.0.0.1:8000/mcp"
SIDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mcp_sid")
_id = [100]

def _post(payload, sid=None, notify=False):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if sid: req.add_header("Mcp-Session-Id", sid)
    with urllib.request.urlopen(req, timeout=180) as r:
        got = r.headers.get("Mcp-Session-Id")
        body = r.read().decode()
    if notify: return got, None
    if body.startswith("event:") or body.startswith("data:"):
        for line in body.splitlines():
            if line.startswith("data:"):
                body = line[5:].strip(); break
    return got, (json.loads(body) if body.strip() else None)

def session():
    if os.path.exists(SIDF):
        sid = open(SIDF).read().strip()
        try:
            _id[0] += 1
            _, r = _post({"jsonrpc":"2.0","id":_id[0],"method":"ping"}, sid)
            if r is not None and "error" not in r: return sid
        except Exception: pass
    sid, _ = _post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2025-06-18","capabilities":{},
        "clientInfo":{"name":"stacktown-stage0","version":"1.0"}}})
    _post({"jsonrpc":"2.0","method":"notifications/initialized"}, sid, notify=True)
    open(SIDF,"w").write(sid or "")
    return sid

def call(name, args=None, sid=None):
    sid = sid or session()
    _id[0] += 1
    _, r = _post({"jsonrpc":"2.0","id":_id[0],"method":"tools/call",
                  "params":{"name":name,"arguments":args or {}}}, sid)
    if r is None: return "<empty>"
    if "error" in r: return "ERROR: " + json.dumps(r["error"])
    res = r.get("result", {})
    txt = "".join(c.get("text","") for c in res.get("content", []))
    if res.get("isError"): txt = "TOOL-ERROR: " + txt
    return txt

class ToolError(RuntimeError):
    """An MCP tool refused the call and said why, in plain text."""


def tool(toolset, name, args=None, raw=False):
    """Call an MCP tool. RAISES ToolError when the editor refuses.

    WHY THIS RAISES. The server answers a refusal with a bare string -
    "TOOL-ERROR: Cannot create actors while PIE is active." - not with JSON
    and not with a non-200. Every caller here does json.loads() on the reply,
    so a refusal surfaced as JSONDecodeError: Expecting value: line 1 column
    1, which names neither the tool nor the reason.

    That cost a real diagnosis on 29 Aug: a whole verification bake failed on
    every actor, and the traceback sent me looking at a dead MCP session and
    then at a missing toolset before the actual message - PIE was running -
    turned up three layers down, only because I called the tool by hand and
    printed the reply instead of parsing it.

    The message was there the entire time. Nothing was reading it. Pass
    raw=True to get the old behaviour when a caller wants to inspect the
    refusal itself.
    """
    if name == 'CaptureViewport' and _lens_depth == 0:
        _assert_lens()
    a = {"tool_name": name, "arguments": args or {}}
    if toolset: a["toolset_name"] = toolset
    r = call("call_tool", a)
    if not raw and isinstance(r, str) and r.lstrip().startswith('TOOL-ERROR'):
        raise ToolError('%s.%s: %s' % (toolset or '?', name,
                                       r.lstrip()[len('TOOL-ERROR'):].lstrip(': ')))
    return r


# --- LENS STATE IS EXPOSURE STATE ---------------------------------------
#
# POLISH_PROTOCOL's capture protocol: assert the lens before every measured
# frame. This is the enforcement, and it lives here rather than in cap2
# because cap2 is not the choke point - wood_set.py, wood_board.py, p0_reel.py
# and others call tool(APP, 'CaptureViewport') directly. tool() is the one
# door every capture in the project goes through.
#
# THE INCIDENT THIS IS THE RECEIPT FOR (31 Aug). LOOK_Post runs AEM_Manual
# with autoExposureApplyPhysicalCameraExposure true, so depthOfFieldFstop sets
# BRIGHTNESS as well as focus. A DOF study left the volume at f/22 and nothing
# restored it. Every capture afterwards came out ~6 stops under: a baked set
# measured image mean 8.0 where its own reference framing measured 102.4. It
# looked exactly like a lighting bug and cost a full diagnosis chasing lights.
# dof.py had warned about this coupling in its comments the whole time -
# "a brightness ladder wearing a depth-of-field label" - but a comment cannot
# fail a run, and a session-state restore does not survive a reload.
#
# A DECLARED STATE IS ALLOWED, an accidental one is not. dof.hero() legitimately
# shoots at f/2.8 / ISO 1568 / 1-240th; that is fine PROVIDED the script says so
# with declare_lens(). What this refuses is drift nobody declared.
GATE_LENS = (4.0, 800.0, 60.0)      # fstop, iso, shutter - dof.reset()
_expect_lens = GATE_LENS
_lens_depth = 0
_lens_warned = False


class LensStateError(Exception):
    pass


def declare_lens(fstop=None, iso=None, shutter=None):
    """Declare the lens this script intends to shoot at. No args = the gate."""
    global _expect_lens
    _expect_lens = (GATE_LENS if fstop is None
                    else (float(fstop), float(iso), float(shutter)))
    return _expect_lens


def lens_state():
    """(fstop, iso, shutter) off LOOK_Post, or None if there is no such volume."""
    import json as _json
    global _lens_depth
    _lens_depth += 1
    try:
        found = _json.loads(tool('editor_toolset.toolsets.scene.SceneTools',
                                 'find_actors', {'name': 'LOOK_Post', 'tag': '',
                                 'collision_channels': []}))['returnValue']
        if not found:
            return None
        raw = _json.loads(tool('editor_toolset.toolsets.object.ObjectTools',
                               'get_properties', {'instance': found[0],
                               'properties': ['settings']}))['returnValue']
        st = _json.loads(raw)['settings']
        return (float(st['depthOfFieldFstop']), float(st['cameraISO']),
                float(st['cameraShutterSpeed']))
    finally:
        _lens_depth -= 1


def _assert_lens():
    global _lens_warned
    got = lens_state()
    if got is None:
        if not _lens_warned:
            _lens_warned = True
            sys.stderr.write('ue: no LOOK_Post in this level - lens state '
                             'unchecked\n')
        return
    want = _expect_lens
    # RELATIVE tolerance, not exact equality. The first version compared with
    # 1e-6 absolute and false-refused a capture whose lens was IDENTICAL to
    # what it declared - "at f/4 ISO 853.381 1/60 but expects f/4 ISO 853.381
    # 1/60 ... 0.0 stops off". UE stores these as float32 and they do not
    # survive a python round-trip bit-exact, so any solved (non-round) value
    # trips it.
    #
    # The planted-defect proof missed this because every value it used was a
    # ROUND NUMBER - 4.0, 22.0, 800 - which round-trips exactly. A guard tested
    # only on tidy inputs is tested only where it cannot fail.
    #
    # 0.1% is far tighter than the eye or the measurement: an ISO error that
    # small is 0.0014 stops, while the fault this exists to catch (f/22 vs
    # f/4) is nearly five.
    if all(abs(a - b) <= max(1e-6, 1e-3 * abs(b)) for a, b in zip(got, want)):
        return
    raise LensStateError(
        'LENS STATE IS EXPOSURE STATE: LOOK_Post is at f/%g ISO %g 1/%g but '
        'this capture expects f/%g ISO %g 1/%g. The f-stop drives exposure as '
        'well as defocus, so shooting now yields a frame that is %.1f stops '
        'off and looks like a lighting fault. Either restore the gate '
        'condition (Tools/measure/dof.py: reset()) or, if this lens is '
        'intended, say so with ue.declare_lens(fstop, iso, shutter).'
        % (got[0], got[1], got[2], want[0], want[1], want[2],
           2 * math.log(got[0] / want[0], 2) - math.log(got[1] / want[1], 2)
           - math.log(want[2] / got[2], 2)))


if __name__ == "__main__":
    print(call(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv)>2 else {}))
