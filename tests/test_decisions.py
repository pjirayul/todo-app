"""Decisions card: load_decisions / answer_decision (no server, a temp file, never the real decisions.json)."""
import json
import os
import tempfile
import unittest

import server


class DecisionsTest(unittest.TestCase):
    def setUp(self):
        self.old = server.DECISIONS_FILE
        self.dir = tempfile.TemporaryDirectory()
        server.DECISIONS_FILE = os.path.join(self.dir.name, "d.json")
        items = [{"id": 1, "title": "Thai ทดสอบ", "status": "open"},
                 {"id": 2, "title": "Old", "status": "answered", "answer": "Go"}]
        with open(server.DECISIONS_FILE, "w", encoding="utf-8-sig") as f:  # with BOM, like Windows editors
            json.dump(items, f)

    def tearDown(self):
        server.DECISIONS_FILE = self.old
        self.dir.cleanup()

    def test_missing_file_is_empty_list(self):
        os.remove(server.DECISIONS_FILE)
        self.assertEqual(server.load_decisions(), [])

    def test_answer_saves_and_keeps_thai(self):
        result, status = server.answer_decision("1", "Go", " ok ")
        self.assertEqual(status, 200)
        item = server.load_decisions()[0]
        self.assertEqual((item["status"], item["answer"], item["note"]), ("answered", "Go", "ok"))
        self.assertTrue(item["answeredAt"])
        self.assertIn("ทดสอบ", open(server.DECISIONS_FILE, encoding="utf-8").read())  # ensure_ascii=False

    def test_rejects_bad_answer_unknown_id_and_second_answer(self):
        self.assertEqual(server.answer_decision("1", "Maybe", "")[1], 400)
        self.assertEqual(server.answer_decision("99", "Go", "")[1], 404)
        self.assertEqual(server.answer_decision("2", "No-go", "")[1], 409)
        self.assertEqual(server.load_decisions()[1]["answer"], "Go")  # first answer stays

    def test_long_note_is_cut(self):
        server.answer_decision("1", "No-go", "x" * 900)
        self.assertEqual(len(server.load_decisions()[0]["note"]), 500)


if __name__ == "__main__":
    unittest.main()
