"""Tests for job 0q-2: "Tell Max more…" (pending sentence) and "Add as 2 tasks?". Fake AI only, frozen "now"."""
import os
import tempfile
import unittest
from unittest import mock

import server
from tests.test_max import NOW_TEXT, TASKS, DENTIST, default_memory, fake_ai, no_ai


def parts_ai(parts):
    """A fake AI: the "cut it into parts" question gets `parts`, every other question gets the usual task answer."""
    def ai(prompt, system=None, schema=None, *a, **k):
        if schema is server.SEVERAL_SCHEMA:
            return {"parts": parts, "tokens": 0}
        return fake_ai(prompt)
    return ai


def run(sentence, tasks=(), ai=fake_ai, earlier=None, age=10):
    with mock.patch.object(server, "parse_with_ollama", ai), default_memory(), mock.patch.object(server, "AI_PROVIDER", "ollama"):
        return server.run_command(sentence, NOW_TEXT, [], list(tasks), None, earlier, age)


class JoinPending(unittest.TestCase):
    def test_related_text_is_joined(self):
        self.assertEqual(server.join_pending("tomorrow at 5pm", "buy milk", 30, []), ("buy milk, tomorrow at 5pm", True))

    def test_too_old_or_missing_is_dropped(self):
        self.assertEqual(server.join_pending("dentist", "cancel", 301, []), ("dentist", False))
        self.assertEqual(server.join_pending("dentist", "", 5, []), ("dentist", False))
        self.assertEqual(server.join_pending("dentist", "cancel", None, []), ("dentist", False))

    def test_unrelated_text_is_dropped(self):
        for text in ["done #2", "move dentist to friday", "what is due today?", "ยกเลิก dentist",
                     "please remember to water all the plants in the garden"]:
            self.assertEqual(server.join_pending(text, "buy milk", 5, TASKS), (text, False), text)

    def test_long_text_that_shares_a_word_is_related(self):
        text = "the organic one from the market near the office"
        self.assertTrue(server.join_pending(text, "buy milk", 5, TASKS + [{"num": 9, "text": "Office desk", "done": False}])[1])

    def test_joined_sentence_runs_the_normal_road(self):
        r = run("tomorrow at 5pm", earlier="buy milk")
        self.assertEqual((r["action"], r["due"]), ("add", "2026-10-29T17:00"))
        self.assertEqual(run("done #2", TASKS, earlier="buy milk", ai=no_ai)["num"], 2)

    def test_joined_card_has_no_tell_more_loop(self):
        r = run("dentist", DENTIST, earlier="cancel")
        if r["action"] == "clarify":
            self.assertFalse(r["more"])


class Several(unittest.TestCase):
    def test_two_valid_parts_give_a_card(self):
        r = run("buy milk and call mom", ai=parts_ai(["buy milk", "call mom"]))
        self.assertEqual((r["action"], r["case"], r["more"]), ("clarify", "several", True))
        self.assertEqual([o["label"] for o in r["options"]], ["opt_several", "opt_one"])
        self.assertEqual([t["text"] for t in r["options"][0]["do"]["tasks"]], ["Buy milk", "Call mom"])
        self.assertEqual(r["options"][1]["do"]["text"], "Buy milk and call mom")   # "One task" = what Max would have added

    def test_each_part_gets_its_own_python_date(self):
        r = run("buy milk tomorrow and call mom at 7pm", ai=parts_ai(["buy milk tomorrow", "call mom at 7pm"]))
        dues = [t["due"] for t in r["options"][0]["do"]["tasks"]]
        self.assertEqual(dues[0][:10], "2026-10-29")
        self.assertTrue(dues[1].endswith("T19:00"))

    def test_one_shared_day_stays_one_task(self):
        r = run("call Tom and email Ann tomorrow", ai=parts_ai(["call Tom", "email Ann tomorrow"]))
        self.assertEqual(r["action"], "add")
        r = run("call Tom and email Ann tomorrow", ai=parts_ai(["call Tom", "email Ann"]))   # the AI dropped the day
        self.assertEqual(r["action"], "add")

    def test_list_of_items_is_one_task_without_an_ai_call(self):
        for text in ["buy milk and eggs", "buy salt and pepper", "ซื้อไข่และนม"]:
            self.assertFalse(server.could_be_several(text), text)
            self.assertEqual(run(text, ai=fake_ai)["action"], "add", text)

    def test_ai_says_one_part_or_invents_words_or_fails(self):
        self.assertEqual(run("meet Tom and Ann on friday", ai=parts_ai(["meet Tom and Ann on friday"]))["action"], "add")
        self.assertEqual(run("buy milk and call mom", ai=parts_ai(["buy milk", "phone the doctor"]))["action"], "add")

        def broken(prompt, system=None, schema=None, *a, **k):
            if schema is server.SEVERAL_SCHEMA:
                raise TimeoutError("slow")
            return fake_ai(prompt)
        self.assertEqual(run("buy milk and call mom", ai=broken)["action"], "add")   # a slow AI never blocks the add

    def test_thai_parts(self):
        r = run("ล้างจานและซื้อนม", ai=parts_ai(["ล้างจาน", "ซื้อนม"]))
        self.assertEqual(r["case"], "several")

    def test_check_parts(self):
        s = "buy milk and call mom and pay rent"
        self.assertEqual(len(server.check_parts(["buy milk", "call mom", "pay rent"], s)), 3)
        self.assertEqual(server.check_parts(["buy milk"], s), [])
        self.assertEqual(server.check_parts(["a b", "c d", "e f", "g h"], "a b c d e f g h"), [])
        self.assertEqual(server.check_parts("nope", s), [])

    def test_commands_and_questions_are_not_split(self):
        r = run("done #2 and move #4 to friday", TASKS + DENTIST, ai=parts_ai(["done #2", "move #4 to friday"]))
        self.assertNotEqual(r.get("case"), "several")


class ClarifyLog(unittest.TestCase):
    def test_log_keeps_case_and_label_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "log.json")
            with mock.patch.object(server, "CLARIFY_LOG_FILE", path):
                self.assertTrue(server.add_clarify_answer({"case": "several", "picked": "opt_one", "text": "secret"}))
                self.assertFalse(server.add_clarify_answer({"case": "Bad Case!", "picked": "x"}))
                self.assertFalse(server.add_clarify_answer({"case": "done", "picked": "<script>"}))
                with open(path, encoding="utf-8") as f:
                    log = server.json.load(f)
            self.assertEqual([(e["case"], e["picked"]) for e in log], [("several", "opt_one")])
            self.assertNotIn("secret", str(log))


if __name__ == "__main__":
    unittest.main()
