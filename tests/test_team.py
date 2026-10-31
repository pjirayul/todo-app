"""Tests for job 0d: Max messages the team. The fake AI raises, so every pass proves no AI call was made."""
import json
import os
import tempfile
import unittest
from unittest import mock

import server
from tests.test_max import NOW_TEXT, default_memory, fake_ai, no_ai


def run(sentence, ai=no_ai):
    """ai=no_ai proves a message/replies never calls the AI; tasks (which do go to the AI) use fake_ai."""
    with mock.patch.object(server, "parse_with_ollama", ai), default_memory():
        return server.run_command(sentence, NOW_TEXT, [], [])


def sent(sentence):
    r = run(sentence)
    return (r.get("to"), r.get("text")) if r["action"] == "team_send" else r["action"]


class TeamSend(unittest.TestCase):
    def test_english(self):
        self.assertEqual(sent("tell Toto the build is done"), ("Toto", "the build is done"))
        self.assertEqual(sent("ask Kimi to check the login"), ("Kimi", "check the login"))
        self.assertEqual(sent("message Bono that tests pass"), ("Bono", "tests pass"))
        self.assertEqual(sent("send to Lewis: need the report"), ("Lewis", "need the report"))

    def test_thai(self):
        self.assertEqual(sent("บอก Toto ว่า build เสร็จแล้ว"), ("Toto", "build เสร็จแล้ว"))
        self.assertEqual(sent("ถาม Lewis ว่า มีรายงานไหม"), ("Lewis", "มีรายงานไหม"))
        self.assertEqual(sent("บอกโตโต้ว่าเสร็จแล้ว"), ("Toto", "เสร็จแล้ว"))

    def test_greeting_and_case(self):
        self.assertEqual(sent("hey max tell TOTO that it works"), ("Toto", "it works"))
        self.assertEqual(sent("Tell gp: ready"), ("GP", "ready"))

    def test_gp_inside_a_word_is_not_a_name(self):
        self.assertEqual(run("tell gpu fans to stop", fake_ai)["action"], "add")

    def test_false_positives_stay_tasks(self):
        for s in ("tell mom I'm late", "send Kimi the report", "บอกแม่ว่าจะกลับดึก", "remind me to tell Kimi the news"):
            self.assertEqual(run(s, fake_ai)["action"], "add", s)

    def test_bare_command_stays_a_task(self):
        self.assertEqual(run("tell George buy milk", fake_ai)["action"], "add")

    def test_empty_text_sends_nothing(self):
        self.assertEqual(sent("tell Toto"), ("Toto", ""))


class TeamReplies(unittest.TestCase):
    def test_phrases(self):
        for s in ("any replies?", "new answers", "มีตอบกลับไหม"):
            self.assertEqual(run(s)["action"], "team_replies", s)

    def test_not_a_reply_question(self):
        self.assertNotEqual(run("any replies from the bank to file", fake_ai)["action"], "team_replies")


class Inbox(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "inbox.json")
        patch = mock.patch.object(server, "INBOX_FILE", self.path)
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(self.dir.cleanup)

    def test_add_inbox_trims_and_rejects(self):
        self.assertIsNone(server.add_inbox("Mom", "hi"))
        self.assertIsNone(server.add_inbox("Toto", "   "))
        item = server.add_inbox("Toto", "x" * 1500)
        self.assertEqual(len(item["text"]), 1000)
        self.assertEqual(len(server.load_inbox()), 1)

    def test_answer_writes_to_the_test_file_and_uses_chat_shape(self):
        r = server.team_answer(run("tell Toto the build is done"), "tell Toto the build is done")
        self.assertEqual((r["action"], r["kind"]), ("smalltalk", "chat"))
        self.assertIn("Sent to Toto", r["reply"])
        self.assertEqual(server.load_inbox()[0]["text"], "the build is done")

    def test_thai_answer_and_empty(self):
        r = server.team_answer(run("บอก Toto ว่า เสร็จแล้ว"), "บอก Toto ว่า เสร็จแล้ว")
        self.assertIn("ส่งถึง Toto", r["reply"])
        r = server.team_answer(run("tell Toto"), "tell Toto")
        self.assertIn("What shall I tell", r["reply"])
        self.assertEqual(len(server.load_inbox()), 1)   # the empty one wrote nothing

    def test_replies_list(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([{"to": "Kimi", "text": "a", "reply": "done"}, {"to": "Bono", "text": "b", "reply": ""}], f)
        r = server.team_answer({"action": "team_replies"}, "any replies?")
        self.assertEqual(r["reply"], "Kimi: done")


if __name__ == "__main__":
    unittest.main()
