import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp_drift_check.cli import main


class CliTests(unittest.TestCase):
    def test_scan_workspace_reports_repo_relative_config_path(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root / ".mcp.json").write_text(
                json.dumps({
                    "mcpServers": {
                        "example": {
                            "command": "npx",
                            "args": ["example-package@1.2.3"],
                        }
                    }
                }),
                encoding="utf-8",
            )
            old_cwd=Path.cwd()
            try:
                os.chdir(root)
                stdout=io.StringIO()
                with redirect_stdout(stdout):
                    code=main(["scan-workspace", "--json"])
            finally:
                os.chdir(old_cwd)
            self.assertEqual(code, 0)
            findings=json.loads(stdout.getvalue())
            self.assertEqual(findings[0]["config_path"], ".mcp.json")


if __name__ == "__main__":
    unittest.main()
