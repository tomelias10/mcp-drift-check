import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from mcp_drift_check.parser import parse_config

FIX=Path(__file__).parent / "fixtures"

class ParserTests(unittest.TestCase):
    def test_multiple_servers(self):
        findings=parse_config(FIX/"mutable.json")
        self.assertEqual(len(findings), 3)
        self.assertEqual([f.classification for f in findings], ["HIGH","HIGH","MEDIUM"])

    def test_safe_scoped_package(self):
        f=parse_config(FIX/"safe.json")[0]
        self.assertEqual(f.package, "@scope/server")
        self.assertEqual(f.declared_version, "1.2.3")
        self.assertEqual(f.classification, "SAFE")

    def test_malformed_config(self):
        f=parse_config(FIX/"malformed.json")[0]
        self.assertEqual(f.classification, "REVIEW")
        self.assertIn("could not be parsed", f.reason)

    def test_embedded_command_string(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"mcp.json"
            p.write_text('{"mcpServers":{"x":{"command":"npx -y package@1.2.3"}}}')
            f=parse_config(p)[0]
            self.assertEqual(f.classification, "SAFE")
            self.assertEqual(f.package, "package")

    def test_unknown_command_review(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"mcp.json"
            p.write_text('{"mcpServers":{"x":{"command":"uvx","args":["server"]}}}')
            self.assertEqual(parse_config(p)[0].classification, "REVIEW")

    def test_local_executable_review(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"mcp.json"
            p.write_text('{"mcpServers":{"x":{"command":"./server"}}}')
            self.assertEqual(parse_config(p)[0].classification, "REVIEW")

    def test_npm_exec_with_separator(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"mcp.json"
            p.write_text('{"mcpServers":{"x":{"command":"npm","args":["exec","--","@scope/pkg@2.0.0"]}}}')
            f=parse_config(p)[0]
            self.assertEqual((f.package, f.declared_version, f.classification), ("@scope/pkg","2.0.0","SAFE"))

if __name__ == "__main__": unittest.main()
