from __future__ import annotations
import json
import shlex
from pathlib import Path
from .classifier import classify_package, classify_non_package
from .models import Finding

def _walk_mcp_servers(obj):
    if isinstance(obj, dict):
        servers = obj.get("mcpServers")
        if isinstance(servers, dict):
            yield servers
        for value in obj.values():
            yield from _walk_mcp_servers(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_mcp_servers(value)

def _command_parts(server):
    command = server.get("command") if isinstance(server, dict) else None
    args = server.get("args", []) if isinstance(server, dict) else []
    if isinstance(command, list):
        return [str(x) for x in command]
    if not isinstance(command, str) or not command.strip():
        return []
    if isinstance(args, str):
        args = shlex.split(args)
    if not isinstance(args, list):
        args = []
    # Preserve a command string with embedded arguments while avoiding execution.
    head = shlex.split(command)
    return head + [str(x) for x in args]

def _extract_npm_spec(parts):
    if not parts:
        return None, False
    exe = Path(parts[0]).name.lower()
    rest = parts[1:]
    auto_yes = any(x in ("-y", "--yes") for x in rest)
    if exe in ("npx", "npx.cmd"):
        candidates = [x for x in rest if not x.startswith('-')]
        return (candidates[0] if candidates else None), auto_yes
    if exe in ("npm", "npm.cmd") and rest and rest[0] in ("exec", "x"):
        tail = rest[1:]
        if '--' in tail:
            tail = tail[tail.index('--')+1:]
        candidates = [x for x in tail if not x.startswith('-')]
        return (candidates[0] if candidates else None), auto_yes
    return None, auto_yes

def parse_config(path: str | Path, client: str = "manual"):
    p = Path(path).expanduser()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding(client, str(p), "<config>", "", None, None, "REVIEW", f"Config could not be parsed: {exc.__class__.__name__}.", "Validate the JSON configuration manually.")]
    findings=[]
    seen=set()
    for servers in _walk_mcp_servers(data):
        for name, server in servers.items():
            key=(id(servers), name)
            if key in seen:
                continue
            seen.add(key)
            parts=_command_parts(server)
            rendered=shlex.join(parts) if parts else ""
            spec, auto_yes=_extract_npm_spec(parts)
            if spec:
                package, version, level, reason, rec = classify_package(spec, auto_yes)
            elif parts:
                package=version=None
                level, reason, rec = classify_non_package(parts[0])
            else:
                package=version=None
                level, reason, rec = "REVIEW", "Server has no recognizable command and was not executed.", "Review the server configuration manually."
            findings.append(Finding(client, str(p), str(name), rendered, package, version, level, reason, rec))
    if not findings:
        findings.append(Finding(client, str(p), "<config>", "", None, None, "REVIEW", "No mcpServers block was found.", "Confirm this is an MCP configuration file."))
    return findings
