#!/usr/bin/env python3
"""Persistent client for the native Unreal MCP bridge (UE 5.8, streamable HTTP)."""
import json, sys, os, urllib.request

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
    a = {"tool_name": name, "arguments": args or {}}
    if toolset: a["toolset_name"] = toolset
    r = call("call_tool", a)
    if not raw and isinstance(r, str) and r.lstrip().startswith('TOOL-ERROR'):
        raise ToolError('%s.%s: %s' % (toolset or '?', name,
                                       r.lstrip()[len('TOOL-ERROR'):].lstrip(': ')))
    return r

if __name__ == "__main__":
    print(call(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv)>2 else {}))
