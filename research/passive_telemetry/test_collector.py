import sqlite3
import tempfile
import unittest
from pathlib import Path

import collector


class CollectorTests(unittest.TestCase):
    def test_stable_json_is_order_independent(self):
        a = collector.stable_json({"b": 2, "a": 1})
        b = collector.stable_json({"a": 1, "b": 2})
        self.assertEqual(a, b)

    def test_event_dedup(self):
        with tempfile.TemporaryDirectory() as td:
            conn = sqlite3.connect(Path(td) / "x.db")
            collector.init_db(conn)
            payload = {"x": 1}
            self.assertTrue(collector.add_event(conn, "s", "k", "t", "2026-01-01T00:00:00Z", payload))
            self.assertFalse(collector.add_event(conn, "s", "k", "t", "2026-01-01T00:00:00Z", payload))
            self.assertTrue(collector.add_event(conn, "s", "k", "t", "2026-01-01T00:00:00Z", {"x": 2}))

    def test_snapshot_dedup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            conn = sqlite3.connect(root / "x.db")
            collector.init_db(conn)
            digest1, fresh1 = collector.write_snapshot(root, conn, "s", {"x": 1}, 1)
            digest2, fresh2 = collector.write_snapshot(root, conn, "s", {"x": 1}, 1)
            self.assertEqual(digest1, digest2)
            self.assertTrue(fresh1)
            self.assertFalse(fresh2)


if __name__ == "__main__":
    unittest.main()
