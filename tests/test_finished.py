"""Job 9: "What did I finish?" - the page stamps doneAt when a task is ticked, Python filters by that day."""
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

import server
from tests.test_max import ask

# Now = Wed 28 Oct 2026 10:00 (same as NOW_TEXT in test_max.py)
TASKS = [
    {"num": 1, "text": "Pay rent", "done": True, "due": "2026-10-30T09:00", "doneAt": "2026-10-28T08:15"},   # due Fri, ticked today
    {"num": 2, "text": "Call mom", "done": True, "due": "", "doneAt": "2026-10-27T19:40"},                    # ticked yesterday
    {"num": 3, "text": "Gym", "done": True, "due": "2026-10-28T07:00", "doneAt": "2026-10-26T07:30"},         # ticked Monday
    {"num": 4, "text": "Old task", "done": True, "due": "2026-10-28T09:00", "doneAt": ""},                    # done before job 9
    {"num": 5, "text": "Buy milk", "done": False, "due": "2026-10-28T18:00", "doneAt": ""},                   # still open
]
for t in TASKS:
    t.update(priority="med", cat="")


class FinishedQuestions(unittest.TestCase):
    def nums(self, text):
        r = ask(text, TASKS)
        self.assertEqual(r["action"], "answer", text)
        return r["nums"]

    def test_today_uses_the_tick_day_not_the_due_day(self):
        # #1 is due Friday but was ticked today; #4 is due today but has no tick time
        self.assertEqual(self.nums("what did I finish today?"), [1])

    def test_yesterday(self):
        self.assertEqual(self.nums("What did I finish yesterday?"), [2])
        self.assertEqual(self.nums("เมื่อวานทำอะไรเสร็จ"), [2])

    def test_this_week_is_monday_until_today(self):
        self.assertEqual(sorted(self.nums("what did I finish this week")), [1, 2, 3])

    def test_a_weekday_means_the_one_that_passed(self):
        self.assertEqual(self.nums("what did I finish on monday?"), [3])

    def test_no_day_lists_every_done_task(self):
        self.assertEqual(sorted(self.nums("what did I finish")), [1, 2, 3, 4])

    def test_open_questions_still_use_the_due_day(self):
        self.assertEqual(self.nums("what's due today"), [5])


class DoneAtIsStored(unittest.TestCase):
    def test_clean_keeps_done_at_only_on_done_tasks(self):
        clean = server.clean_tasks([
            {"num": 1, "text": "a", "done": True, "doneAt": "2026-10-28T08:15"},
            {"num": 2, "text": "b", "done": False, "doneAt": "2026-10-28T08:15"},   # reopened: no finish time
            {"num": 3, "text": "c", "done": True, "doneAt": "yesterday"},           # not a time: dropped
        ])
        self.assertEqual([t["doneAt"] for t in clean], ["2026-10-28T08:15", "", ""])

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as folder, \
             mock.patch.object(server, "DB_FILE", os.path.join(folder, "t.db")), \
             mock.patch.object(server, "daily_db_copy", lambda: None):
            tasks = server.clean_tasks([{"num": 1, "text": "a", "done": True, "doneAt": "2026-10-28T08:15"}])
            self.assertEqual(server.save_tasks(tasks, 2, None)[1], 200)
            self.assertEqual(server.load_tasks()["todos"][0]["doneAt"], "2026-10-28T08:15")

    def test_old_database_gets_the_column(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "old.db")
            con = sqlite3.connect(path)   # a database from before job 9 (no done_at)
            con.execute("CREATE TABLE tasks (id REAL, num INTEGER PRIMARY KEY, text TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, "
                        "due TEXT NOT NULL DEFAULT '', priority TEXT NOT NULL DEFAULT 'med', cat TEXT NOT NULL DEFAULT '', "
                        "notes TEXT NOT NULL DEFAULT '', files TEXT NOT NULL DEFAULT '[]', notified INTEGER NOT NULL DEFAULT 0, "
                        "sort INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL, updated TEXT NOT NULL)")
            con.execute("INSERT INTO tasks (id, num, text, done, created, updated) VALUES (1, 1, 'x', 1, 'a', 'a')")
            con.commit()
            con.close()
            with mock.patch.object(server, "DB_FILE", path):
                self.assertEqual(server.load_tasks()["todos"][0]["doneAt"], "")


if __name__ == "__main__":
    unittest.main()
