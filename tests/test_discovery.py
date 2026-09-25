import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from mcp_drift_check.discovery import known_config_paths

class DiscoveryTests(unittest.TestCase):
    def test_known_files_only(self):
        with TemporaryDirectory() as h, TemporaryDirectory() as c:
            home=Path(h); cwd=Path(c)
            (home/".cursor").mkdir()
            (home/".cursor/mcp.json").write_text("{}")
            (cwd/".mcp.json").write_text("{}")
            got=known_config_paths(home, cwd)
            paths={str(p) for _,p in got}
            self.assertIn(str(home/".cursor/mcp.json"), paths)
            self.assertIn(str(cwd/".mcp.json"), paths)
            self.assertEqual(len(got), 2)

if __name__ == "__main__": unittest.main()
