from __future__ import annotations
from pathlib import Path

def known_config_paths(home: Path | None = None, cwd: Path | None = None):
    home = home or Path.home()
    cwd = cwd or Path.cwd()
    candidates = [
        ("Claude Desktop", home / "Library/Application Support/Claude/claude_desktop_config.json"),
        ("Claude Code", home / ".claude.json"),
        ("Cursor", home / ".cursor/mcp.json"),
        ("VS Code", home / "Library/Application Support/Code/User/mcp.json"),
        ("VS Code", home / ".vscode/mcp.json"),
        ("Windsurf", home / ".codeium/windsurf/mcp_config.json"),
        ("Windsurf", home / "Library/Application Support/Windsurf/User/mcp.json"),
        ("Generic", home / ".mcp.json"),
        ("Generic", cwd / ".mcp.json"),
        ("VS Code workspace", cwd / ".vscode/mcp.json"),
    ]
    out=[]; seen=set()
    for client, path in candidates:
        try: key=str(path.resolve())
        except OSError: key=str(path)
        if key not in seen and path.is_file():
            out.append((client, path))
            seen.add(key)
    return out
