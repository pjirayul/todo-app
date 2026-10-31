"""Tests for job 0q-3: Max learns which cards the owner always accepts (auto-switch), the question and
vague-date cards, and reminders with no time. Fake AI only, frozen "now", the log is faked (the real one is never read)."""
import unittest
from unittest import mock

import server
from tests.test_max import NOW_TEXT, TASKS, DENTIST, ai_says, default_memory, fake_ai, no_ai
from tests.test_tellmore import run


def log_of(case, *picks):
    return [{"id": "", "case": case, "picked": p, "at": "2026-10-28 09:00"} for p in picks]


def with_log(entries):
    return mock.patch.object(server, "load_clarify_log", return_value=entries)


class SwitchRule(unittest.TestCase):
    def test_needs_20_answers_and_90_percent_act(self):
        with with_log(log_of("done", *["act"] * 19)):
            self.assertEqual(server.auto_flag("done"), {})            # only 19 answers: not enough
        with with_log(log_of("done", *["act"] * 20)):
            self.assertEqual(server.auto_flag("done"), {"auto": True})
        with with_log(log_of("done", *["act"] * 18 + ["add"] * 2)):
            self.assertEqual(server.auto_flag("done"), {"auto": True})  # exactly 90%
        with with_log(log_of("done", *["act"] * 17 + ["add"] * 3)):
            self.assertEqual(server.auto_flag("done"), {})

    def test_only_the_last_30_count_and_undo_counts_against(self):
        with with_log(log_of("change", *["add"] * 30 + ["act"] * 30)):
            self.assertEqual(server.auto_flag("change"), {"auto": True})   # old answers are forgotten
        with with_log(log_of("change", *["act"] * 27 + ["undo"] * 3)):
            self.assertEqual(server.auto_flag("change"), {"auto": True})
        with with_log(log_of("change", *["act"] * 26 + ["undo"] * 4)):
            self.assertEqual(server.auto_flag("change"), {})           # a bad switch drops under 90%: Max asks again

    def test_old_log_labels_still_count(self):
        with with_log(log_of("done", *["opt_complete"] * 20)):
            self.assertEqual(server.auto_flag("done"), {"auto": True})

    def test_delete_similar_pick_and_vague_never_switch(self):
        for case in ("delete", "similar", "pick", "vague"):
            with with_log(log_of(case, *["act"] * 30)):
                self.assertEqual(server.auto_flag(case), {}, case)

    def test_a_done_card_carries_the_auto_flag(self):
        # "I finished the slides": the AI finds task 9 by name -> a card, or (after learning) the same card with auto
        slides = [{"num": 9, "text": "Finish the slides", "done": False, "due": ""}]
        with with_log([]):
            r = run("I finished the slides", slides, ai=ai_says("done", "slides"))
        self.assertEqual((r["action"], r["case"], r.get("auto")), ("clarify", "done", None))
        with with_log(log_of("done", *["act"] * 25)):
            r = run("I finished the slides", slides, ai=ai_says("done", "slides"))
        self.assertEqual((r["case"], r["auto"], r["options"][0]["do"]["action"]), ("done", True, "complete"))

    def test_delete_card_never_has_auto(self):
        with with_log(log_of("delete", *["act"] * 30)):
            r = run("cancel dentist", DENTIST, ai=ai_says("delete", "dentist"))
        self.assertEqual(r["action"], "clarify")
        self.assertNotIn("auto", r)

    def test_follow_up_never_asks_twice(self):
        # the owner answered "Tell Max more": a second card has no "Tell Max more" button again
        r = run("dentist", DENTIST, earlier="cancel", ai=ai_says("delete", "dentist"))
        if r["action"] == "clarify":
            self.assertFalse(r["more"])


class LogFile(unittest.TestCase):
    def test_labels_become_kinds(self):
        self.assertEqual([server.pick_kind(x) for x in ("opt_complete", "opt_add", "opt_one", "more", "none", "undo")],
                         ["act", "add", "add", "more", "none", "undo"])


class StepTwoCases(unittest.TestCase):
    def test_ai_question_the_gate_missed_gives_a_card(self):
        # no question word and no "?": Python's gate says no, the AI says question and names a real task
        with with_log([]):
            r = run("is the dentist appointment all sorted out for me", DENTIST, ai=ai_says("question", "dentist"))
        self.assertEqual((r["action"], r["case"], r["nums"]), ("clarify", "question", [4]))
        self.assertEqual([o["label"] for o in r["options"]], ["opt_answer", "opt_add"])
        self.assertEqual(r["options"][0]["do"]["action"], "answer")

    def test_ai_question_without_a_task_is_a_plain_add(self):
        r = run("zebra grooming schedule", DENTIST, ai=ai_says("question", "zebra"))
        self.assertEqual(r["action"], "add")

    def test_plain_add_never_gets_a_card(self):
        self.assertEqual(run("is the dentist appointment all sorted out for me", DENTIST)["action"], "add")   # the AI says add

    def test_vague_date_gives_two_dates_and_no_date(self):
        r = run("dentist next week")
        self.assertEqual((r["action"], r["case"]), ("clarify", "vague"))
        self.assertEqual([o["do"]["due"][:10] for o in r["options"]], ["2026-11-02", "2026-11-06", ""])   # Mon, Fri, none
        self.assertNotIn("auto", r)

    def test_vague_date_only_for_appointments_without_a_weekday(self):
        self.assertEqual(run("write blog post next week")["action"], "add")
        self.assertEqual(run("dentist friday next week")["action"], "add")

    def test_reminder_without_a_day_asks_when(self):
        r = run("remind me to call the bank")
        self.assertEqual((r["action"], r.get("askWhen")), ("add", True))
        r = run("remind me tomorrow to call the bank")
        self.assertNotIn("askWhen", r)


if __name__ == "__main__":
    unittest.main()
