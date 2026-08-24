#!/usr/bin/env python3
"""Run Python inside the live UE editor via UE's own remote execution channel."""
import sys, time, os
sys.path.insert(0, "/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python")
import remote_execution as rx

def run(code, mode=None, timeout=25):
    cfg = rx.RemoteExecutionConfig()
    cfg.multicast_group_endpoint = ('239.0.0.1', 6766)
    cfg.multicast_bind_address = '0.0.0.0'
    cfg.multicast_ttl = 1
    rem = rx.RemoteExecution(cfg)
    rem.start()
    try:
        want = os.environ.get('UEPY_PROJECT_ROOT',
                              '/Users/ben/Documents/Unreal Projects/StacktownAlpha/')
        def _proot(nd):
            nd = nd if isinstance(nd, dict) else (getattr(nd, 'data', None) or {})
            return nd.get('project_root') or ''
        # Wait for OUR node, not for any node. Exiting on the first responder
        # meant the other agent's editor could win the race and this would
        # report "no node for project" while ours was simply still answering.
        t0 = time.time()
        while time.time() - t0 < timeout:
            if any(_proot(n) == want for n in rem.remote_nodes):
                break
            time.sleep(0.4)
        nodes = list(rem.remote_nodes)          # snapshot: the property rebuilds
        if not nodes:
            return None, 'NO NODE FOUND'
        # Another agent's editor is on the same multicast group. nodes[0] is
        # whichever answered first - a coin flip. Pin to THIS project root and
        # refuse to guess. The script itself asserts the project too, so a
        # mis-selection here cannot silently mutate the wrong build.
        proot = _proot
        matches = [nd for nd in nodes if proot(nd) == want]
        if not matches:
            return None, ('NO NODE FOR %r (saw: %s)'
                          % (want, ', '.join(proot(n) or '?' for n in nodes)))
        if len(matches) > 1:
            return None, 'AMBIGUOUS: %d editors report %r' % (len(matches), want)
        node = matches[0]
        if len(nodes) > 1:
            others = [proot(n) for n in nodes if n.get('node_id') != node.get('node_id')]
            sys.stderr.write('[uepy] %d editors visible; using %s (ignoring: %s)\n'
                             % (len(nodes), want, ', '.join(o or '?' for o in others)))
        # open_command_connection takes the node ID STRING, not the node dict.
        # Passing the dict worked by luck while only one editor was on the
        # group; with a second editor present it connected to whichever one it
        # felt like - in practice the other agent's.
        node_id = node['node_id'] if isinstance(node, dict) else node
        rem.open_command_connection(node_id)
        mode = mode or rx.MODE_EXEC_FILE
        res = rem.run_command(code, exec_mode=mode)
        return res, None
    finally:
        try: rem.close_command_connection()
        except Exception: pass
        rem.stop()

if __name__ == '__main__':
    code = sys.argv[1] if len(sys.argv) > 1 else 'print("hello")'
    # MODE_EXEC_FILE takes a PATH. Sending source text worked by fallback until
    # a script tripped it and UE reported "Could not load Python file" with the
    # source echoed as the filename. The editor is on this machine, so hand it
    # the absolute path and let it load the file itself.
    if os.path.isfile(code): code = os.path.abspath(code)
    res, err = run(code)
    if err: print('ERROR:', err); sys.exit(1)
    print('success:', res.get('success'))
    for o in res.get('output') or []:
        print(f"[{o.get('type')}] {o.get('output')}")
    if res.get('result') not in (None, 'None'): print('result:', res.get('result'))
