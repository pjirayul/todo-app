"""Tests for #17: several things in one sentence. Fake AI only. Shared trailing day + explicit lists ("Add 3 tasks: a, b, c")."""
import unittest

import server
from tests.test_max import no_ai
from tests.test_tellmore import parts_ai, run


def tasks_of(card):
    return card["options"][0]["do"]["tasks"]


class SharedDay(unittest.TestCase):
    def test_trailing_day_goes_to_every_part(self):
        r = run("buy milk and call mom tomorrow", ai=parts_ai(["buy milk", "call mom tomorrow"]))
        self.assertEqual((r["action"], r["case"]), ("clarify", "several"))
        t = tasks_of(r)
        self.assertEqual([x["text"] for x in t], ["Buy milk", "Call mom"])
        self.assertEqual([x["due"][:10] for x in t], ["2026-10-29", "2026-10-29"])   # "now" is Wed 28 Oct

    def test_day_dropped_by_the_ai_still_shared(self):
        r = run("call Tom and email Ann tomorrow", ai=parts_ai(["call Tom", "email Ann"]))
        self.assertEqual([x["due"][:10] for x in tasks_of(r)], ["2026-10-29"] * 2)

    def test_shared_time_and_own_day_win(self):
        r = run("buy milk and call mom at 5pm", ai=parts_ai(["buy milk", "call mom at 5pm"]))
        self.assertEqual([x["due"][11:] for x in tasks_of(r)], ["17:00", "17:00"])
        r = run("buy milk friday and call mom tomorrow", ai=parts_ai(["buy milk friday", "call mom tomorrow"]))
        self.assertEqual([x["due"][:10] for x in tasks_of(r)], ["2026-10-30", "2026-10-29"])

    def test_thai_shared_day(self):
        r = run("ซื้อนมและโทรหาแม่พรุ่งนี้", ai=parts_ai(["ซื้อนม", "โทรหาแม่พรุ่งนี้"]))
        self.assertEqual(r["case"], "several")
        self.assertEqual([x["due"][:10] for x in tasks_of(r)], ["2026-10-29"] * 2)

    def test_no_day_anywhere_stays_undated(self):
        r = run("buy milk and call mom", ai=parts_ai(["buy milk", "call mom"]))
        self.assertEqual([x["due"] for x in tasks_of(r)], ["", ""])

    def test_check_parts_and_source(self):
        s = "buy milk and call mom tomorrow"
        self.assertEqual(server.check_parts(["buy milk", "call mom tomorrow"], s), ["buy milk", "call mom tomorrow"])
        self.assertEqual(server.check_parts(["buy milk tomorrow", "call mom"], "buy milk tomorrow and call mom"), [])
        self.assertEqual(server.shared_day_source(["buy milk", "call mom tomorrow"], s), "call mom tomorrow")
        self.assertEqual(server.shared_day_source(["buy milk", "call mom"], s), s)
        self.assertEqual(server.shared_day_source(["a b", "c d"], "a b and c d"), "")


class ExplicitList(unittest.TestCase):
    def test_list_with_count(self):
        r = run("Add 3 tasks: buy milk, call mom, pay rent", ai=no_ai)   # no AI call at all
        self.assertEqual((r["action"], r["case"], r["path"]), ("clarify", "several", "rules"))
        self.assertEqual([x["text"] for x in tasks_of(r)], ["Buy milk", "Call mom", "Pay rent"])

    def test_last_and_cuts_when_the_count_says_so(self):
        self.assertEqual(server.list_parts("add 3 tasks: buy milk, call mom and pay rent"), ["buy milk", "call mom", "pay rent"])

    def test_wrong_count_or_too_short_is_not_a_list(self):
        self.assertEqual(server.list_parts("add 4 tasks: buy milk, call mom, pay rent"), [])
        self.assertEqual(server.list_parts("add tasks: buy milk, call mom"), [])   # no count: needs 2+ commas
        self.assertEqual(server.list_parts("add tasks: buy milk, call mom, pay rent"), ["buy milk", "call mom", "pay rent"])
        self.assertEqual(server.list_parts("buy milk, call mom, pay rent"), [])
        self.assertEqual(server.list_parts("add milk"), [])

    def test_each_item_has_its_own_day(self):
        r = run("add 2 tasks: buy milk tomorrow, call mom friday", ai=no_ai)
        self.assertEqual([x["due"][:10] for x in tasks_of(r)], ["2026-10-29", "2026-10-30"])

    def test_thai_list(self):
        r = run("เพิ่ม 3 งาน: ซื้อนม, โทรหาแม่, จ่ายค่าเช่า", ai=no_ai)
        self.assertEqual(r["case"], "several")
        self.assertEqual(len(tasks_of(r)), 3)

    def test_one_task_button_is_a_plain_add(self):
        r = run("add 2 tasks: buy milk, call mom", ai=no_ai)
        self.assertEqual(r["options"][1]["label"], "opt_one")
        self.assertEqual(r["options"][1]["do"]["action"], "add")


if __name__ == "__main__":
    unittest.main()
