import unittest
from mcp_drift_check.classifier import classify_package, split_package_spec

class ClassifierTests(unittest.TestCase):
    def test_bare_package_high(self):
        self.assertEqual(classify_package("package")[2], "HIGH")

    def test_latest_high(self):
        self.assertEqual(classify_package("package@latest")[2], "HIGH")

    def test_exact_safe(self):
        self.assertEqual(classify_package("package@1.2.3")[2], "SAFE")

    def test_range_medium(self):
        self.assertEqual(classify_package("package@^1.2.3")[2], "MEDIUM")

    def test_scoped_exact(self):
        name, version = split_package_spec("@scope/package@1.2.3")
        self.assertEqual((name, version), ("@scope/package", "1.2.3"))
        self.assertEqual(classify_package("@scope/package@1.2.3")[2], "SAFE")

    def test_auto_yes_context(self):
        self.assertIn("-y/--yes", classify_package("package", True)[3])

if __name__ == "__main__": unittest.main()
