"""Decisions archive: archive_decisions (temp files only, never the real decisions.json)."""
import json
import os
import tempfile
import unittest
from datetime import datetime

import server

NOW = datetime(2026, 11, 8, 12, 0)  # frozen "now"


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.old = (server.DECISIONS_FILE, server.DECISIONS_ARCHIVE_FILE)
        self.dir = tempfile.TemporaryDirectory()
        server.DECISIONS_FILE = os.path.join(self.dir.name, "d.json")
        server.DECISIONS_ARCHIVE_FILE = os.path.join(self.dir.name, "a.json")
        self.save([
            {"id": 1, "title": "Open", "status": "open"},
            {"id": 2, "title": "Old ทดสอบ", "status": "answered", "answer": "Go", "answeredAt": "2026-10-30 10:00"},
            {"id": 3, "title": "Recent", "status": "answered", "answer": "No-go", "answeredAt": "2026-11-05 10:00"},
        ])

    def tearDown(self):
        server.DECISIONS_FILE, server.DECISIONS_ARCHIVE_FILE = self.old
        self.dir.cleanup()

    def save(self, items):
        with open(server.DECISIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f)

    def archive(self):
        with open(server.DECISIONS_ARCHIVE_FILE, encoding="utf-8") as f:
            return json.load(f)

    def test_manual_moves_only_answered_and_keeps_open(self):
        self.assertEqual(server.archive_decisions(now=NOW), 2)
        self.assertEqual([d["id"] for d in server.load_decisions()], [1])
        self.assertEqual([d["id"] for d in self.archive()], [2, 3])
        self.assertIn("ทดสอบ", open(server.DECISIONS_ARCHIVE_FILE, encoding="utf-8").read())  # ensure_ascii=False

    def test_auto_moves_only_older_than_7_days(self):
        self.assertEqual(server.archive_decisions(older_than_days=7, now=NOW), 1)
        self.assertEqual([d["id"] for d in server.load_decisions()], [1, 3])
        self.assertEqual([d["id"] for d in self.archive()], [2])

    def test_appends_never_overwrites(self):
        with open(server.DECISIONS_ARCHIVE_FILE, "w", encoding="utf-8-sig") as f:
            json.dump([{"id": 99, "title": "Earlier"}], f)
        server.archive_decisions(now=NOW)
        self.assertEqual([d["id"] for d in self.archive()], [99, 2, 3])

    def test_nothing_to_move_writes_nothing(self):
        self.save([{"id": 1, "status": "open"}])
        self.assertEqual(server.archive_decisions(now=NOW), 0)
        self.assertFalse(os.path.exists(server.DECISIONS_ARCHIVE_FILE))

    def test_bad_date_is_left_alone_by_auto(self):
        self.save([{"id": 5, "status": "answered", "answeredAt": "yesterday"}])
        self.assertEqual(server.archive_decisions(older_than_days=7, now=NOW), 0)
        self.assertEqual(len(server.load_decisions()), 1)


if __name__ == "__main__":
    unittest.main()
