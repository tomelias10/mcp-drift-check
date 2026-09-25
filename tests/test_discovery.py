import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from mcp_drift_check.discovery import known_config_paths, workspace_config_paths

class DiscoveryTests(unittest.TestCase):
    def test_known_files_only(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home=Path(h); cwd=Path(c)
            (home/".cursor").mkdir()
            (home/".cursor/mcp.json").write_text("{}")
            (cwd/".mcp.json").write_text("{}")
            for rel in (".github/mcp.json", ".cursor/mcp.json", ".vscode/mcp.json", ".windsurf/mcp.json"):
                target=cwd/rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("{}")
            got=known_config_paths(home, cwd)
            paths={str(p) for _,p in got}
            self.assertIn(str(home/".cursor/mcp.json"), paths)
            self.assertIn(str(cwd/".mcp.json"), paths)
            self.assertIn(str(cwd/".github/mcp.json"), paths)
            self.assertIn(str(cwd/".cursor/mcp.json"), paths)
            self.assertIn(str(cwd/".vscode/mcp.json"), paths)
            self.assertIn(str(cwd/".windsurf/mcp.json"), paths)
            self.assertEqual(len(got), 6)

    def test_workspace_only_excludes_home_configs(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home=Path(h); cwd=Path(c)
            (home/".cursor").mkdir()
            (home/".cursor/mcp.json").write_text("{}")
            (cwd/".cursor").mkdir()
            (cwd/".cursor/mcp.json").write_text("{}")
            got=workspace_config_paths(cwd)
            paths={str(p) for _,p in got}
            self.assertEqual(paths, {str(cwd/".cursor/mcp.json")})
            self.assertNotIn(str(home/".cursor/mcp.json"), paths)

    def test_copilot_cli_default_home(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home = Path(h)
            cwd = Path(c)
            copilot_dir = home / ".copilot"
            copilot_dir.mkdir(parents=True)
            config_file = copilot_dir / "mcp-config.json"
            config_file.write_text("{}")
            got = known_config_paths(home, cwd, environ={})
            self.assertIn(("GitHub Copilot CLI", config_file), got)

    def test_copilot_cli_custom_home_skips_fallback(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c, TemporaryDirectory() as custom:
            home = Path(h)
            cwd = Path(c)
            custom_dir = Path(custom)
            fallback_file = home / ".copilot/mcp-config.json"
            fallback_file.parent.mkdir(parents=True)
            fallback_file.write_text("{}")
            custom_file = custom_dir / "mcp-config.json"
            custom_file.write_text("{}")

            got = known_config_paths(home, cwd, environ={"COPILOT_HOME": str(custom_dir)})
            paths = {str(p) for _, p in got}
            self.assertIn(str(custom_file), paths)
            self.assertNotIn(str(fallback_file), paths)
            self.assertIn(("GitHub Copilot CLI", custom_file), got)

if __name__ == "__main__": unittest.main()
