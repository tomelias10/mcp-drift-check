import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp_drift_check.discovery import known_config_paths, workspace_config_paths


class DiscoveryTests(unittest.TestCase):
    def test_known_files_only(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home = Path(h)
            cwd = Path(c)
            (home / ".cursor").mkdir()
            (home / ".cursor/mcp.json").write_text("{}")
            (cwd / ".mcp.json").write_text("{}")
            for rel in (
                ".github/mcp.json",
                ".cursor/mcp.json",
                ".vscode/mcp.json",
                ".windsurf/mcp.json",
            ):
                target = cwd / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("{}")
            got = known_config_paths(home, cwd, env={})
            paths = {str(p) for _, p in got}
            self.assertIn(str(home / ".cursor/mcp.json"), paths)
            self.assertIn(str(cwd / ".mcp.json"), paths)
            self.assertIn(str(cwd / ".github/mcp.json"), paths)
            self.assertIn(str(cwd / ".cursor/mcp.json"), paths)
            self.assertIn(str(cwd / ".vscode/mcp.json"), paths)
            self.assertIn(str(cwd / ".windsurf/mcp.json"), paths)
            self.assertEqual(len(got), 6)

    def test_workspace_only_excludes_home_configs(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home = Path(h)
            cwd = Path(c)
            (home / ".cursor").mkdir()
            (home / ".cursor/mcp.json").write_text("{}")
            (cwd / ".cursor").mkdir()
            (cwd / ".cursor/mcp.json").write_text("{}")
            got = workspace_config_paths(cwd)
            paths = {str(p) for _, p in got}
            self.assertEqual(paths, {str(cwd / ".cursor/mcp.json")})
            self.assertNotIn(str(home / ".cursor/mcp.json"), paths)

    def test_copilot_cli_default_home(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home = Path(h)
            cwd = Path(c)
            target = home / ".copilot" / "mcp-config.json"
            target.parent.mkdir(parents=True)
            target.write_text("{}")
            fallback_unused = home / "other" / "mcp-config.json"
            fallback_unused.parent.mkdir(parents=True)
            fallback_unused.write_text("{}")
            got = known_config_paths(home, cwd, env={})
            paths = {str(p) for _, p in got}
            self.assertEqual(paths, {str(target)})

    def test_copilot_cli_copilot_home_overrides_fallback(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c, TemporaryDirectory() as ch:
            home = Path(h)
            cwd = Path(c)
            copilot_home = Path(ch)
            override = copilot_home / "mcp-config.json"
            override.write_text("{}")
            fallback = home / ".copilot" / "mcp-config.json"
            fallback.parent.mkdir(parents=True)
            fallback.write_text("{}")
            got = known_config_paths(home, cwd, env={"COPILOT_HOME": str(copilot_home)})
            paths = {str(p) for _, p in got}
            self.assertEqual(paths, {str(override)})
            self.assertNotIn(str(fallback), paths)

    def test_claude_desktop_windows_appdata(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c, TemporaryDirectory() as ad:
            home = Path(h)
            cwd = Path(c)
            appdata = Path(ad)
            win_path = appdata / "Claude" / "claude_desktop_config.json"
            win_path.parent.mkdir(parents=True)
            win_path.write_text("{}")
            linux_fallback = home / ".config" / "Claude" / "claude_desktop_config.json"
            linux_fallback.parent.mkdir(parents=True)
            linux_fallback.write_text("{}")
            got = known_config_paths(home, cwd, env={"APPDATA": str(appdata)})
            paths = {str(p) for _, p in got}
            self.assertIn(str(win_path), paths)
            self.assertIn(str(linux_fallback), paths)

    def test_claude_desktop_linux_xdg_config_home(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c, TemporaryDirectory() as xdg:
            home = Path(h)
            cwd = Path(c)
            xdg_home = Path(xdg)
            xdg_path = xdg_home / "Claude" / "claude_desktop_config.json"
            xdg_path.parent.mkdir(parents=True)
            xdg_path.write_text("{}")
            fallback = home / ".config" / "Claude" / "claude_desktop_config.json"
            fallback.parent.mkdir(parents=True)
            fallback.write_text("{}")
            got = known_config_paths(home, cwd, env={"XDG_CONFIG_HOME": str(xdg_home)})
            paths = {str(p) for _, p in got}
            self.assertEqual(paths, {str(xdg_path)})
            self.assertNotIn(str(fallback), paths)

    def test_claude_desktop_linux_fallback_when_xdg_unset(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home = Path(h)
            cwd = Path(c)
            fallback = home / ".config" / "Claude" / "claude_desktop_config.json"
            fallback.parent.mkdir(parents=True)
            fallback.write_text("{}")
            got = known_config_paths(home, cwd, env={})
            paths = {str(p) for _, p in got}
            self.assertEqual(paths, {str(fallback)})

    def test_discovery_is_deduplicated(self):
        with TemporaryDirectory() as shared:
            shared_path = Path(shared)
            config = shared_path / "mcp-config.json"
            config.write_text("{}")
            home = shared_path
            cwd = shared_path
            got = known_config_paths(
                home, cwd, env={"COPILOT_HOME": str(shared_path)}
            )
            self.assertEqual(len(got), 1)


if __name__ == "__main__":
    unittest.main()
