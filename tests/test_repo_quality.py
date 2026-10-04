import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".py", ".toml", ".txt"}
ACTION_REF = re.compile(r"\buses:\s*([^\s#]+)@([^\s#]+)")
IMMUTABLE_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
LEGACY_MCP_ROUTE = "orynval.com/" + "mcp-scan"
CURRENT_MCP_ROUTE = "orynval.com/mcp-drift-check"


class RepositoryQualityTests(unittest.TestCase):
    def test_no_legacy_mcp_scan_route_in_repository_text(self):
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "action.yml":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if LEGACY_MCP_ROUTE in text:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [], f"Legacy Orynval MCP route remains in: {offenders}")

    def test_readme_uses_current_browser_route(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn(CURRENT_MCP_ROUTE, text)

    def test_readme_relative_links_exist(self):
        text = README.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
        missing = []
        for target in links:
            target = target.strip().split()[0]
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if path and not (ROOT / path).exists():
                missing.append(target)
        self.assertEqual(missing, [], f"Broken relative README links: {missing}")

    def test_external_github_actions_are_pinned_to_commit_sha(self):
        files = [README]
        workflow_dir = ROOT / ".github" / "workflows"
        files.extend(sorted(workflow_dir.glob("*.yml")))
        files.extend(sorted(workflow_dir.glob("*.yaml")))
        offenders = []
        for path in files:
            text = path.read_text(encoding="utf-8")
            for action, ref in ACTION_REF.findall(text):
                if action.startswith("./"):
                    continue
                if not IMMUTABLE_SHA.fullmatch(ref):
                    offenders.append(f"{path.relative_to(ROOT)}: {action}@{ref}")
        self.assertEqual(offenders, [], f"Mutable GitHub Action refs remain: {offenders}")

    def test_security_hygiene_files_exist(self):
        required = [ROOT / "SECURITY.md", ROOT / ".github" / "dependabot.yml"]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [], f"Required repository security files missing: {missing}")


if __name__ == "__main__":
    unittest.main()
