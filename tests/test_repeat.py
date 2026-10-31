"""Job 7: repeating tasks (server side). Python reads the repeat words; no AI, no real data.

"Now" is Friday 30 Oct 2026 10:00 (same as Max's exam).
"""
import datetime as dt
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

import server

NOW = dt.datetime(2026, 10, 30, 10, 0)
MEMORY = {"times": server.DEFAULT_TIMES}


def parse(sentence, ai_title=None):
    """check_task with a fake AI answer that only has a title (the AI never says anything about repeating)."""
    task = {"text": ai_title or sentence, "when": "none", "time": ""}
    return server.check_task(task, sentence, "2026-10-30T10:00", [], MEMORY)


class ReadRepeat(unittest.TestCase):
    def test_english_words(self):
        for sentence, repeat in [
            ("gym every monday at 7am", "week"), ("gym each monday", "week"), ("every week call mom", "week"),
            ("weekly report", "week"), ("take vitamins every morning", "day"), ("water the plants every day", "day"),
            ("daily standup", "day"), ("every night lock the door", "day"), ("every evening stretch", "day"),
            ("pay rent every month on the 5th", "month"), ("pay rent every 5th", "month"), ("monthly backup", "month"),
        ]:
            with self.subTest(sentence):
                self.assertEqual(server.read_repeat(sentence)[0], repeat)

    def test_thai_words(self):
        for sentence, repeat in [
            ("วิ่งทุกเช้า", "day"), ("รดน้ำต้นไม้ทุกวัน", "day"), ("ทุกเย็นเดินเล่น", "day"), ("ทุกคืนอ่านหนังสือ", "day"),
            ("ประชุมทีมทุกวันจันทร์ 10 โมง", "week"), ("ทุกวันอาทิตย์โทรหาแม่", "week"), ("ทุกสัปดาห์ส่งรายงาน", "week"),
            ("จ่ายค่าเน็ตทุกวันที่ 5", "month"), ("จ่ายค่าเช่าทุกเดือน", "month"),
        ]:
            with self.subTest(sentence):
                self.assertEqual(server.read_repeat(sentence)[0], repeat)

    def test_look_alikes_do_not_repeat(self):
        for sentence in ["every time I call mom she is late", "ask everyone about the party friday", "ทุกวันนี้รถติดมาก",
                         "บอกทุกคนเรื่องงานเลี้ยง", "call mom next week", "buy milk", "every other day gym"]:
            with self.subTest(sentence):
                self.assertEqual(server.read_repeat(sentence)[0], "")

    def test_day_updates(self):
        self.assertEqual(server.read_repeat("gym every monday")[1]["weekday"], "Monday")
        self.assertEqual(server.read_repeat("ประชุมทุกวันจันทร์")[1]["weekday"], "Monday")
        self.assertEqual(server.read_repeat("pay rent every 5th")[1]["day"], 5)
        self.assertEqual(server.read_repeat("จ่ายค่าเน็ตทุกวันที่ 5")[1]["day"], 5)
        self.assertEqual(server.read_repeat("water plants every day")[1], {})   # no day named: check_task uses today


class NextDue(unittest.TestCase):
    def test_day_skips_missed_days(self):
        # ticked 3 days late: the next one is tomorrow, not a backlog of three
        self.assertEqual(server.next_due("2026-10-27T07:00", "day", NOW), "2026-10-31T07:00")

    def test_day_ticked_earlier_today(self):
        self.assertEqual(server.next_due("2026-10-30T07:00", "day", NOW), "2026-10-31T07:00")

    def test_week_keeps_weekday_and_time(self):
        self.assertEqual(server.next_due("2026-10-26T07:00", "week", NOW), "2026-11-02T07:00")

    def test_month_clamps_to_month_end(self):
        n = dt.datetime(2026, 1, 20, 10, 0)
        self.assertEqual(server.next_due("2026-01-31T09:00", "month", n), "2026-02-28T09:00")
        self.assertEqual(server.next_due("2026-04-30T09:00", "month", dt.datetime(2026, 4, 30, 10, 0)), "2026-05-30T09:00")

    def test_month_december_to_january(self):
        self.assertEqual(server.next_due("2026-12-05T09:00", "month", dt.datetime(2026, 12, 6, 10, 0)), "2027-01-05T09:00")

    def test_far_overdue_month(self):
        self.assertEqual(server.next_due("2026-05-05T09:00", "month", NOW), "2026-11-05T09:00")

    def test_unknown_repeat_changes_nothing(self):
        self.assertEqual(server.next_due("2026-10-27T07:00", "", NOW), "2026-10-27T07:00")


class CheckTask(unittest.TestCase):
    def test_every_monday_title_and_due(self):
        for ai_title in ("Gym", "Gym every monday"):   # the AI may leave the repeat words in the title
            with self.subTest(ai_title):
                r = parse("gym every monday at 7am", ai_title)
                self.assertEqual((r["text"], r["repeat"], r["due"]), ("Gym", "week", "2026-11-02T07:00"))

    def test_every_morning_first_due_rolls_forward(self):
        r = parse("take vitamins every morning", "Take vitamins")   # 09:00 today is already past at 10:00
        self.assertEqual((r["text"], r["repeat"], r["due"]), ("Take vitamins", "day", "2026-10-31T09:00"))

    def test_every_day_7am_at_1430(self):
        r = server.check_task({"text": "Run", "when": "none", "time": ""}, "run every day 7am",
                              "2026-10-30T14:30", [], MEMORY)
        self.assertEqual((r["repeat"], r["due"]), ("day", "2026-10-31T07:00"))

    def test_every_day_later_today_stays_today(self):
        r = server.check_task({"text": "Run", "when": "none", "time": ""}, "run every day 7pm",
                              "2026-10-30T14:30", [], MEMORY)
        self.assertEqual(r["due"], "2026-10-30T19:00")

    def test_month_day(self):
        for sentence in ("pay rent every month on the 5th", "pay rent every 5th"):
            with self.subTest(sentence):
                r = parse(sentence, "Pay rent")
                self.assertEqual((r["text"], r["repeat"], r["due"]), ("Pay rent", "month", "2026-11-05T09:00"))

    def test_every_week_without_a_day_uses_today(self):
        # the AI may invent a weekday here; the owner named none, so the anchor is today's weekday
        task = {"text": "Water plants", "when": "weekday", "weekday": "Tuesday", "time": ""}
        r = server.check_task(task, "water plants every week", "2026-10-30T10:00", [], MEMORY)
        self.assertEqual((r["repeat"], r["due"]), ("week", "2026-11-06T09:00"))   # Friday 09:00 passed -> next Friday

    def test_thai(self):
        cases = [("วิ่งทุกเช้า", "วิ่ง", "day", "2026-10-31T09:00"),
                 ("ประชุมทีมทุกวันจันทร์ 10 โมง", "ประชุมทีม", "week", "2026-11-02T10:00"),
                 ("จ่ายค่าเน็ตทุกวันที่ 5", "จ่ายค่าเน็ต", "month", "2026-11-05T09:00"),
                 ("รดน้ำต้นไม้ทุกวัน", "รดน้ำต้นไม้", "day", "2026-10-31T09:00")]
        for sentence, title, repeat, due in cases:
            with self.subTest(sentence):
                r = parse(sentence, title)
                self.assertEqual((r["text"], r["repeat"], r["due"]), (title, repeat, due))

    def test_plain_tasks_do_not_repeat(self):
        for sentence in ("ask everyone about the party friday", "ทุกวันนี้รถติดมาก", "every time I call mom she is late"):
            with self.subTest(sentence):
                self.assertEqual(parse(sentence)["repeat"], "")

    def test_plain_task_keeps_its_every_word(self):
        self.assertIn("everyone", parse("ask everyone about the party friday")["text"].lower())


class Database(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [mock.patch.object(server, "DATA_DIR", self.tmp.name),
                        mock.patch.object(server, "DB_FILE", os.path.join(self.tmp.name, "t.db")),
                        mock.patch.object(server, "daily_db_copy", lambda: None)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def task(self, **extra):
        return {"id": 1.0, "num": 1, "text": "Gym", "done": False, "due": "2026-11-02T07:00", **extra}

    def test_clean_tasks_only_four_values(self):
        for value, want in [("day", "day"), ("week", "week"), ("month", "month"), ("", ""),
                            ("yearly", ""), (123, ""), (None, ""), (["day"], ""), (True, "")]:
            with self.subTest(value):
                self.assertEqual(server.clean_tasks([self.task(repeat=value)])[0]["repeat"], want)

    def test_missing_field_is_plain(self):
        # script.js does not send `repeat` yet: that must not crash, and the task is a plain one
        self.assertEqual(server.clean_tasks([self.task()])[0]["repeat"], "")

    def test_round_trip(self):
        tasks = server.clean_tasks([self.task(repeat="week"), {**self.task(), "num": 2, "text": "Other"}])
        result, status = server.save_tasks(tasks, 3, None)
        self.assertEqual(status, 200)
        self.assertEqual([t["repeat"] for t in server.load_tasks()["todos"]], ["week", ""])

    def test_save_without_the_field_clears_it_but_works(self):
        server.save_tasks(server.clean_tasks([self.task(repeat="day")]), 2, None)
        server.save_tasks(server.clean_tasks([self.task()]), 2, None)   # an old page saves without `repeat`
        self.assertEqual(server.load_tasks()["todos"][0]["repeat"], "")

    def test_old_database_is_migrated(self):
        # a database made before job 7: no repeat column
        con = sqlite3.connect(server.DB_FILE)
        con.execute("""CREATE TABLE tasks (num INTEGER PRIMARY KEY, id REAL, text TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0,
            due TEXT NOT NULL DEFAULT '', priority TEXT NOT NULL DEFAULT 'med', cat TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '', files TEXT NOT NULL DEFAULT '[]', notified INTEGER NOT NULL DEFAULT 0,
            sort INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL, updated TEXT NOT NULL,
            steps TEXT NOT NULL DEFAULT '[]', details_asked INTEGER NOT NULL DEFAULT 0)""")
        con.execute("INSERT INTO tasks (num, id, text, created, updated) VALUES (7, 1, 'Old task', 'x', 'x')")
        con.commit()
        con.close()
        todos = server.load_tasks()["todos"]
        self.assertEqual([(t["num"], t["text"], t["repeat"]) for t in todos], [(7, "Old task", "")])


if __name__ == "__main__":
    unittest.main()
