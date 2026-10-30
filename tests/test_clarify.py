"""Tests for job 0q-1: Max asks before he guesses (clarify cards). Fake AI only, frozen "now"."""
import unittest

import server
from tests.test_max import TASKS, DENTIST, CALLS, ask, ai_says, fake_ai, no_ai

SLIDES = [{"num": 7, "text": "Finish the slides", "done": False, "due": ""}]
BARE = ["cancel", "move", "change", "edit", "reschedule", "delete", "done", "ยกเลิก", "เลื่อน", "ลบ", "แก้", "เสร็จแล้ว",
        "move it", "cancel this task", "ลบอันนี้"]


class Cards(unittest.TestCase):
    def test_cancel_by_name_asks(self):
        r = ask("cancel dentist", DENTIST, ai=ai_says("delete", "dentist"))
        self.assertEqual((r["action"], r["case"], r["nums"]), ("clarify", "delete", [4]))
        self.assertEqual([o["label"] for o in r["options"]], ["opt_delete", "opt_add"])
        self.assertEqual(r["options"][0]["do"], {"action": "delete", "num": 4, "confirmed": True})
        self.assertEqual(r["options"][1]["do"]["text"], "Cancel dentist")
        self.assertTrue(r["more"])

    def test_done_by_ai_name_asks_but_command_first_is_instant(self):
        r = ask("I finished the slides", SLIDES, ai=ai_says("done", "slides"))
        self.assertEqual((r["action"], r["case"]), ("clarify", "done"))
        self.assertEqual(ask("done laundry", TASKS, ai=no_ai), {"action": "complete", "num": 1})   # no AI, no card
        self.assertEqual(ask("done #2", TASKS, ai=no_ai), {"action": "complete", "num": 2})

    def test_move_by_name_gives_ready_changes(self):
        r = ask("move the rent car thing to monday", [{"num": 13, "text": "Rent car return", "done": False, "due": ""}],
                ai=ai_says("change", "rent car"))
        if r["action"] == "clarify":   # the fake AI target decides; the do must carry the finished changes
            self.assertEqual(r["options"][0]["do"]["action"], "update")
            self.assertIn("due", r["options"][0]["do"]["changes"])

    def test_clear_move_stays_instant_and_weak_move_is_a_task(self):
        self.assertEqual(ask("move dentist to friday", DENTIST, ai=no_ai)["action"], "update")
        r = ask("Move car to garage", [{"num": 13, "text": "Rent car return", "done": False, "due": ""}])
        self.assertEqual(r["action"], "add")

    def test_similar_tasks_offer_both(self):
        r = ask("done call", CALLS)
        self.assertEqual((r["case"], sorted(r["nums"])), ("similar", [5, 6]))
        self.assertNotIn("opt_add", [o["label"] for o in r["options"]])

    def test_plain_task_never_gets_a_card(self):
        for text in ["set up the printer", "buy salt and pepper", "call the plumber", "Mark's birthday gift friday"]:
            self.assertEqual(ask(text, DENTIST + TASKS)["action"], "add", text)


class BareCommandWord(unittest.TestCase):
    def test_bare_word_asks_which_task_without_the_ai(self):
        for text in BARE:
            r = ask(text, TASKS, ai=no_ai)   # no_ai raises if the AI is called
            self.assertEqual((r["action"], r["case"]), ("clarify", "pick"), text)
            self.assertLessEqual(len(r["options"]), 3, text)

    def test_move_opens_the_editor_others_act(self):
        self.assertEqual(ask("move", TASKS, ai=no_ai)["options"][0]["do"]["action"], "edit")
        self.assertEqual(ask("cancel", TASKS, ai=no_ai)["options"][0]["do"], {"action": "delete", "num": 9, "confirmed": True})

    def test_no_tasks_keeps_the_old_message(self):
        self.assertTrue(ask("cancel", [], ai=no_ai).get("pickTask"))

    def test_words_with_a_task_are_not_bare(self):
        self.assertEqual(ask("move car to garage", [], ai=fake_ai)["action"], "add")
        self.assertEqual(server.bare_action("cancel dentist"), "")
        self.assertEqual(server.bare_action("done #2"), "")

    def test_safety_net_turns_a_command_word_task_into_the_card(self):
        # Python keeps the owner's words as the title, so the net is tested on the result it guards (any road)
        for text in ["Cancel", "Move it", "ยกเลิก"]:
            r = server.guard_bare_add({"action": "add", "text": text, "tokens": 5}, TASKS)
            self.assertEqual((r["action"], r["case"], r["tokens"]), ("clarify", "pick", 5), text)
        self.assertEqual(server.guard_bare_add({"action": "add", "text": "Cancel dentist"}, TASKS)["action"], "add")
        self.assertEqual(server.guard_bare_add({"action": "add", "text": "Milk"}, TASKS)["action"], "add")


if __name__ == "__main__":
    unittest.main()
