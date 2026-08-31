"""Can the MCP server be started from inside the editor?

Nothing is listening on 8000 after the restart, and geometry building goes
through it - genbuild's box() is an MCP call. rung.sh uses remote execution,
a different channel, and still works.
"""
import unreal
hits = [n for n in dir(unreal) if 'mcp' in n.lower() or 'MCP' in n]
print('unreal.* MCP symbols: %s' % (hits or 'none'))
for sub in ('McpEditorSubsystem', 'MCPServerSubsystem', 'EditorToolsetSubsystem'):
    o = getattr(unreal, sub, None)
    print('  %-28s %s' % (sub, 'present' if o else 'MISSING'))
# console commands are the other likely route
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    w = ues.get_editor_world()
    for cmd in ('MCP.Status', 'MCP.Start'):
        unreal.SystemLibrary.execute_console_command(w, cmd)
        print('  ran console: %s' % cmd)
except Exception as e:
    print('  console route failed: %s' % str(e)[:90])
