import json
import unittest
from mcp_drift_check.models import Finding
from mcp_drift_check.output import render_github_annotations, render_markdown, render_sarif

class OutputTests(unittest.TestCase):
    def setUp(self):
        self.high=Finding(
            "Cursor", ".mcp.json", "example", "npx -y example-package",
            "example-package", None, "HIGH",
            "Package version is not pinned.",
            "Pin example-package to a reviewed exact version.",
        )

    def test_sarif_contains_finding(self):
        doc=json.loads(render_sarif([self.high]))
        result=doc["runs"][0]["results"][0]
        self.assertEqual(result["ruleId"], "MCP001")
        self.assertEqual(result["level"], "error")
        self.assertEqual(result["properties"]["server"], "example")

    def test_markdown_is_shareable(self):
        text=render_markdown([self.high])
        self.assertIn("| 1 | 0 | 0 | 0 |", text)
        self.assertIn("zero-execution MCP configuration preflight", text)

    def test_github_annotations_surface_high_findings(self):
        text=render_github_annotations([self.high])
        self.assertIn("::error file=.mcp.json,title=MCP Drift Check (HIGH)::", text)
        self.assertIn("example: Package version is not pinned.", text)
        self.assertNotIn("SAFE", text)

    def test_github_annotations_do_not_expose_absolute_paths(self):
        finding=Finding(
            "Claude Desktop", "/home/runner/.claude.json", "example", "npx example-package",
            "example-package", None, "HIGH", "Package version is not pinned.",
            "Pin example-package to a reviewed exact version.",
        )
        text=render_github_annotations([finding])
        self.assertNotIn("/home/runner/.claude.json", text)
        self.assertTrue(text.startswith("::error title=MCP Drift Check (HIGH)::"))

if __name__ == "__main__":
    unittest.main()
