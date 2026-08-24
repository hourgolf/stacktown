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

def tool(toolset, name, args=None):
    a = {"tool_name": name, "arguments": args or {}}
    if toolset: a["toolset_name"] = toolset
    return call("call_tool", a)

if __name__ == "__main__":
    print(call(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv)>2 else {}))
