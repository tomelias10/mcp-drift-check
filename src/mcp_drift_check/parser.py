from __future__ import annotations
import json
import re
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

_SENSITIVE_NAMES = {
    "token", "accesstoken", "authtoken", "apikey", "secret", "password",
    "passwd", "credential", "privatekey", "clientsecret",
}
_SENSITIVE_FLAGS = {
    "--token", "--access-token", "--access_token", "--auth-token", "--auth_token",
    "--api-key", "--api_key", "--apikey", "--secret", "--password", "--passwd",
    "--credential", "--private-key", "--private_key", "--client-secret", "--client_secret",
}

def _normalize_name(value: str):
    return re.sub(r"[^a-z0-9]", "", value.lower())

def _is_sensitive_name(value: str):
    return _normalize_name(value) in _SENSITIVE_NAMES

def _redact_arg(value: str):
    lower = value.lower()
    if "authorization:" in lower:
        prefix = value[: lower.index("authorization:")] + value[lower.index("authorization:"):].split(":", 1)[0]
        return prefix + ": [REDACTED]"
    if "=" in value:
        key, rest = value.split("=", 1)
        if _is_sensitive_name(key.lstrip("-")):
            return f"{key}=[REDACTED]"
    value = re.sub(
        r"(?i)(https?://[^:/\s]+:)[^@\s]+@",
        r"\1[REDACTED]@",
        value,
    )
    value = re.sub(
        r"(?i)([?&](?:token|access_token|auth_token|api[_-]?key|secret|password|client_secret)=)[^&\s]+",
        r"\1[REDACTED]",
        value,
    )
    return value

def _redact_parts(parts):
    out=[]
    redact_next=False
    for raw in parts:
        value=str(raw)
        if redact_next:
            out.append("[REDACTED]")
            redact_next=False
            continue
        lower=value.lower()
        if lower in _SENSITIVE_FLAGS:
            out.append(value)
            redact_next=True
            continue
        matched=False
        for flag in _SENSITIVE_FLAGS:
            if lower.startswith(flag + "="):
                out.append(value.split("=", 1)[0] + "=[REDACTED]")
                matched=True
                break
        if not matched:
            out.append(_redact_arg(value))
    return out

def _command_parts(server):
    command = server.get("command") if isinstance(server, dict) else None
    args = server.get("args", []) if isinstance(server, dict) else []
    if isinstance(command, list):
        return [str(x) for x in command], None
    if not isinstance(command, str) or not command.strip():
        return [], None
    try:
        if isinstance(args, str):
            args = shlex.split(args)
        if not isinstance(args, list):
            args = []
        # Parse only as text. Nothing discovered here is ever executed.
        head = shlex.split(command)
    except ValueError:
        return [], "Command or args contain malformed shell quoting and could not be parsed safely."
    return head + [str(x) for x in args], None

def _first_positional(values):
    return next((x for x in values if x and not x.startswith("-")), None)


def _extract_package_spec(parts):
    """Return (package spec, auto-confirm context) for supported JS package runners.

    This is text parsing only. No package manager or discovered command is executed.
    """
    if not parts:
        return None, False
    exe = Path(parts[0]).name.lower()
    rest = parts[1:]

    if exe in ("npx", "npx.cmd"):
        auto_yes = any(x in ("-y", "--yes") for x in rest)
        return _first_positional(rest), auto_yes

    if exe in ("npm", "npm.cmd") and rest and rest[0] in ("exec", "x"):
        tail = rest[1:]
        auto_yes = any(x in ("-y", "--yes") for x in tail)
        if "--" in tail:
            tail = tail[tail.index("--") + 1:]
        return _first_positional(tail), auto_yes

    if exe in ("bunx", "bunx.exe"):
        return _first_positional(rest), False
    if exe in ("bun", "bun.exe") and rest and rest[0] in ("x", "bunx"):
        return _first_positional(rest[1:]), False

    if exe in ("pnpm", "pnpm.cmd", "yarn", "yarn.cmd") and rest and rest[0] == "dlx":
        return _first_positional(rest[1:]), False

    return None, False


# Backward-compatible private alias used by the 2026-09-25 npm/npx census script.
def _extract_npm_spec(parts):
    return _extract_package_spec(parts)

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
            parts, parse_error=_command_parts(server)
            rendered=shlex.join(_redact_parts(parts)) if parts else ""
            spec, auto_yes=_extract_package_spec(parts)
            if parse_error:
                package=version=None
                level, reason, rec = "REVIEW", parse_error, "Review the command syntax manually; no command was executed."
            elif spec:
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
