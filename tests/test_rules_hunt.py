"""Bono's rule hunt (.claude/docs/rule-hunt/bono_hunt.py) as normal unit tests.

Run from the app folder:   python -m unittest
Python rules only: no AI, no Ollama, no server, no real data.
"Now" is frozen to a Friday, a Sunday and a Monday (all at 10:00).

Owner's date rules (Lewis's table, .claude/docs/research/date-rules-2026-10-30.md):
- "friday" / "this friday" = nearest Friday on or after today (on a Friday: today)
- "next friday" = first Friday strictly after today (Mon -> this week's Friday, Fri -> +7)
- no clock time = 09:00; vague morning / afternoon / evening / night = 09:00 / 13:00 / 18:00 / 20:00
"""
import datetime as dt
import unittest

import server

T = server.DEFAULT_TIMES
NOWS = {
    "Fri": dt.datetime(2026, 10, 30, 10, 0),
    "Sun": dt.datetime(2026, 11, 1, 10, 0),
    "Mon": dt.datetime(2026, 11, 2, 10, 0),
}


def date_of(sentence, now):
    """What Python alone decides: the due date, or None when the sentence is left to the AI."""
    rule = server.rules_date(sentence, T)
    if rule is None:
        return None
    return server.resolve_due(rule, now, T)


# (sentence, which "now", expected due)
DATES = [
    # weekdays: plain = on/after today, next = strictly after today
    ("call bank friday", "Fri", "2026-10-30T09:00"),
    ("call bank this friday", "Fri", "2026-10-30T09:00"),
    ("call bank next friday", "Fri", "2026-11-06T09:00"),
    ("call bank next monday", "Fri", "2026-11-02T09:00"),
    ("call bank next monday", "Mon", "2026-11-09T09:00"),
    ("call bank monday", "Mon", "2026-11-02T09:00"),
    ("call bank sunday", "Sun", "2026-11-01T09:00"),
    ("call bank next sunday", "Sun", "2026-11-08T09:00"),
    ("call bank saturday", "Fri", "2026-10-31T09:00"),
    ("call bank frday", "Fri", "2026-10-30T09:00"),            # typo fixed
    ("call bank next frday", "Fri", "2026-11-06T09:00"),
    ("call bank friday 5pm", "Fri", "2026-10-30T17:00"),
    ("call bank fri 5pm", "Fri", "2026-10-30T17:00"),
    # relative days
    ("call bank today", "Fri", "2026-10-30T09:00"),
    ("call bank tomorrow", "Fri", "2026-10-31T09:00"),
    ("call bank tmr", "Fri", "2026-10-31T09:00"),
    ("call bank the day after tomorrow", "Fri", "2026-11-01T09:00"),
    ("call bank day after tomorrow 5pm", "Fri", "2026-11-01T17:00"),
    ("call bank in 1 day", "Fri", "2026-10-31T09:00"),
    ("call bank in 3 days", "Fri", "2026-11-02T09:00"),
    ("call bank in a week", "Fri", "2026-11-06T09:00"),
    ("call bank in 2 weeks", "Fri", "2026-11-13T09:00"),
    ("call bank in 2 days at 4pm", "Fri", "2026-11-01T16:00"),
    ("call bank this weekend", "Fri", "2026-10-31T09:00"),
    ("call bank on the weekend", "Fri", "2026-10-31T09:00"),
    ("call bank end of month", "Fri", "2026-10-31T09:00"),
    # clock times and vague times of day
    ("call bank tonight", "Fri", "2026-10-30T20:00"),
    ("call bank tomorrow morning", "Fri", "2026-10-31T09:00"),
    ("call bank tomorrow evening", "Fri", "2026-10-31T18:00"),
    ("call bank tomorrow at 17:00", "Fri", "2026-10-31T17:00"),
    ("call bank tomorrow at 5.30pm", "Fri", "2026-10-31T17:30"),
    ("call bank tomorrow 12am", "Fri", "2026-10-31T00:00"),
    ("call bank tomorrow 12pm", "Fri", "2026-10-31T12:00"),
    ("call bank tomorrow midnight", "Fri", "2026-10-31T00:00"),
    ("call bank tomorrow noon", "Fri", "2026-10-31T12:00"),
    ("call bank tomorrow at 3 in the afternoon", "Fri", "2026-10-31T15:00"),
    ("call bank tomorrow at 7 in the morning", "Fri", "2026-10-31T07:00"),
    ("call bank tomorrow 8 pm", "Fri", "2026-10-31T20:00"),
    # Thai dates
    ("เอาของไปส่ง พรุ่งนี้", "Fri", "2026-10-31T09:00"),
    ("ส่งงาน มะรืน", "Fri", "2026-11-01T09:00"),
    ("ส่งงาน มะรืนนี้", "Fri", "2026-11-01T09:00"),
    ("ส่งงาน วันศุกร์", "Fri", "2026-10-30T09:00"),
    ("ส่งงาน วันศุกร์นี้", "Fri", "2026-10-30T09:00"),
    ("ส่งงาน ศุกร์หน้า", "Fri", "2026-11-06T09:00"),
    ("ส่งงาน วันศุกร์หน้า", "Mon", "2026-11-06T09:00"),         # Mon: this week's Friday
    ("ส่งงาน เสาร์นี้", "Fri", "2026-10-31T09:00"),
    ("ส่งงาน เสาร์หน้า", "Fri", "2026-10-31T09:00"),           # first Saturday strictly after Fri
    ("ส่งงาน วันอาทิตย์", "Fri", "2026-11-01T09:00"),
    ("ส่งงาน สิ้นเดือน", "Fri", "2026-10-31T09:00"),
    ("ส่งงาน สุดสัปดาห์", "Fri", "2026-10-31T09:00"),
    ("ส่งงาน อีก 2 สัปดาห์", "Fri", "2026-11-13T09:00"),
    ("ส่งงาน อีก 3 วัน", "Fri", "2026-11-02T09:00"),
    # Thai clock words (date part = today, so only the time is checked)
    ("นัดหมอตอนบ่ายสาม", "Fri", "T15:00"),
    ("นัดหมอ บ่ายสามครึ่ง", "Fri", "T15:30"),
    ("นัดหมอ บ่ายโมง", "Fri", "T13:00"),
    ("นัดหมอ ตอนเที่ยง", "Fri", "T12:00"),
    ("นัดหมอ ตอนสี่โมงเย็น", "Fri", "T16:00"),
    ("นัดหมอ ตี 5", "Fri", "T05:00"),
    ("นัดหมอ ห้าทุ่ม", "Fri", "T23:00"),
    ("นัดหมอ สิบเอ็ดโมง", "Fri", "T11:00"),
    ("นัดหมอ ตอนบ่ายสามโมงครึ่ง", "Fri", "T15:30"),
    ("นัดหมอ พรุ่งนี้ ห้าโมงเย็น", "Fri", "2026-10-31T17:00"),
    ("นัดหมอ พรุ่งนี้ ทุ่มครึ่ง", "Fri", "2026-10-31T19:30"),
    ("นัดหมอ พรุ่งนี้ สองทุ่ม", "Fri", "2026-10-31T20:00"),
    ("นัดหมอ พรุ่งนี้ เที่ยงคืน", "Fri", "2026-10-31T00:00"),
    ("นัดหมอ พรุ่งนี้ เที่ยง", "Fri", "2026-10-31T12:00"),
    ("นัดหมอ พรุ่งนี้ ตีสาม", "Fri", "2026-10-31T03:00"),
    ("นัดหมอ พรุ่งนี้ เก้าโมงเช้า", "Fri", "2026-10-31T09:00"),
    ("นัดหมอ พรุ่งนี้ 10 โมง", "Fri", "2026-10-31T10:00"),
    ("นัดหมอ พรุ่งนี้ 14.30 น.", "Fri", "2026-10-31T14:30"),
    ("นัดหมอ พรุ่งนี้ 14:30", "Fri", "2026-10-31T14:30"),
    ("นัดหมอ พรุ่งนี้ บ่ายสอง", "Fri", "2026-10-31T14:00"),
    ("นัดหมอ พรุ่งนี้ หกโมงเช้า", "Fri", "2026-10-31T06:00"),
    ("นัดหมอ พรุ่งนี้ หกโมงเย็น", "Fri", "2026-10-31T18:00"),
    ("นัดหมอ พรุ่งนี้ ตอนเช้า", "Fri", "2026-10-31T09:00"),
    ("นัดหมอ พรุ่งนี้ ตอนเย็น", "Fri", "2026-10-31T18:00"),
    ("นัดหมอ คืนนี้", "Fri", "2026-10-30T20:00"),
    ("ซื้อนมพรุ่งนี้เช้า", "Fri", "2026-10-31T09:00"),
]

# Sentences Python must NOT decide (rules_date gives None, the AI or the owner picks)
LEFT_TO_AI = [
    "call bank next week", "call bank tomorrow 5.30", "call bank tomorrow 25:00", "call bank the 5th",
    "call bank next month", "call bank on 5 nov", "call bank 5/11",
    "ส่งงาน อาทิตย์หน้า", "ส่งงาน สัปดาห์หน้า", "ส่งงาน วันที่ 5",
]

# Plain words that merely look like dates: no date at all
NOT_DATES = ["buy sun cream", "sat down with Tom"]

# sentence -> title Python keeps (date/time words and linkers cut out, owner's words kept)
TITLES = [
    ("ขอ claude จาก ploy ในวันศุกร์", "ขอ claude จาก ploy"),
    ("นัดหมอตอนบ่ายสาม", "นัดหมอ"),
    ("ซื้อนมพรุ่งนี้เช้า", "ซื้อนม"),
    ("ส่งงาน สิ้นเดือน", "ส่งงาน"),
    ("ซื้อของในตู้เย็นพรุ่งนี้", "ซื้อของในตู้เย็น"),      # "ใน" inside a word phrase stays
    ("โทรหาแม่ ภายในวันศุกร์", "โทรหาแม่"),
    ("call bank next friday at 5pm", "call bank"),
    ("pay rent on the 5th", "pay rent"),
    ("gym this weekend", "gym"),
    ("meet Tom in 2 weeks", "meet Tom"),
    ("ประชุม เสาร์นี้", "ประชุม"),
    ("เจอกัน ตอนทุ่มครึ่ง", "เจอกัน"),
    ("นัดหมอ ตอนสี่โมงเย็น", "นัดหมอ"),
    ("ส่งรายงานเมื่อวันศุกร์", "ส่งรายงาน"),
    ("ไปตลาดวันอาทิตย์", "ไปตลาด"),
    ("call bank this friday", "call bank"),
    ("lunch with Tom at noon", "lunch with Tom"),
]

# (question, which "now", expected filter fields)
QUESTIONS = [
    ("what to do next friday", "Fri", {"when": "date", "date": "2026-11-06"}),
    ("what to do friday", "Fri", {"when": "date", "date": "2026-10-30"}),
    ("what's on monday", "Fri", {"when": "date", "date": "2026-11-02"}),
    ("what's on next monday", "Mon", {"when": "date", "date": "2026-11-09"}),
    ("next friday what do I have", "Fri", {"when": "date", "date": "2026-11-06"}),
    ("what do i have this weekend", "Fri", {"when": "weekend"}),
    ("what's due this friday", "Fri", {"when": "date", "date": "2026-10-30"}),
    ("what do I have in 3 days", "Fri", {"when": "date", "date": "2026-11-02"}),
    ("what's the day after tomorrow", "Fri", {"when": "date", "date": "2026-11-01"}),
    ("what do i have on the 5th", "Fri", {"when": "date", "date": "2026-11-05"}),
    ("what do i have on the 25th", "Fri", {"when": "date", "date": "2026-11-25"}),
    ("what's due next week", "Fri", {"when": "nextweek"}),
    ("what's due next week", "Sun", {"when": "nextweek"}),
    ("what's due this week", "Sun", {"when": "week"}),
    ("what's overdue", "Fri", {"when": "overdue"}),
    ("how many tasks are done", "Fri", {"status": "done"}),
    ("how many high priority tasks", "Fri", {"priority": "high"}),
    ("what's due tonight", "Fri", {"when": "today"}),
    ("พรุ่งนี้มีอะไร", "Fri", {"when": "tomorrow"}),
    ("มะรืนมีอะไรบ้าง", "Fri", {"when": "date", "date": "2026-11-01"}),
    ("วันศุกร์หน้ามีอะไร", "Fri", {"when": "date", "date": "2026-11-06"}),
    ("ศุกร์หน้ามีอะไรบ้าง", "Fri", {"when": "date", "date": "2026-11-06"}),
    ("เสาร์นี้มีอะไร", "Fri", {"when": "date", "date": "2026-10-31"}),
    ("อาทิตย์หน้ามีงานอะไร", "Fri", {"when": "nextweek"}),
    ("สัปดาห์นี้มีอะไรบ้าง", "Fri", {"when": "week"}),
    ("วันอาทิตย์มีอะไร", "Fri", {"when": "date", "date": "2026-11-01"}),
    ("อีก 3 วันมีอะไร", "Fri", {"when": "date", "date": "2026-11-02"}),
    ("งานที่ค้างอยู่", "Fri", {"when": "overdue"}),
    ("งานด่วนมีอะไรบ้าง", "Fri", {"priority": "high"}),
    ("มีงานอะไรเสร็จแล้วบ้าง", "Fri", {"status": "done"}),
]

COMMAND_TASKS = [
    {"num": 3, "text": "Call bank", "done": False, "due": "2026-11-02T09:00"},
    {"num": 4, "text": "Buy milk", "done": False, "due": ""},
    {"num": 5, "text": "Pay rent", "done": True, "due": ""},
    {"num": 13, "text": "Dentist", "done": False, "due": ""},
]
NOW_TEXT = "2026-10-30T10:00"   # Friday

# (command, expected action, expected task number)
COMMANDS = [
    ("done #3", "complete", 3), ("done 3", "complete", 3), ("#3 done", "complete", 3),
    ("mark #3 as done", "complete", 3), ("tick #3", "complete", 3), ("finished #3", "complete", 3),
    ("เสร็จ #3", "complete", 3), ("งานที่ 3 เสร็จแล้ว", "complete", 3), ("ข้อ 3 เสร็จ", "complete", 3),
    ("เสร็จข้อ 3", "complete", 3), ("task 3 done", "complete", 3), ("no. 3 done", "complete", 3),
    ("number 3 done", "complete", 3), ("done no 3", "complete", 3), ("done with #3", "complete", 3),
    ("done call bank", "complete", 3),
    ("delete #3", "delete", 3), ("delete 3", "delete", 3), ("remove #4", "delete", 4),
    ("ลบ #3", "delete", 3), ("ลบข้อ 3", "delete", 3), ("ลบงานที่ 3", "delete", 3),
    ("ลบ buy milk", "delete", 4), ("delete no. 3", "delete", 3), ("delete task 3", "delete", 3),
    ("delete number 3", "delete", 3), ("get rid of #3", "delete", 3), ("cancel #3", "delete", 3),
    ("undo #5", "uncomplete", 5), ("uncheck #5", "uncomplete", 5), ("reopen pay rent", "uncomplete", 5),
    ("ยังไม่เสร็จ #5", "uncomplete", 5),
]

# (command, expected changes) for "move / rename" commands, "now" = Friday 30 Oct 10:00
UPDATES = [
    ("move #3 to friday", {"due": "2026-10-30T09:00"}),
    ("move #3 to next friday", {"due": "2026-11-06T09:00"}),
    ("move #3 to tomorrow 5pm", {"due": "2026-10-31T17:00"}),
    ("push #3 to monday", {"due": "2026-11-02T09:00"}),
    ("postpone #3 to tomorrow", {"due": "2026-10-31T09:00"}),
    ("reschedule #3 to saturday", {"due": "2026-10-31T09:00"}),
    ("เลื่อน #3 ไปวันศุกร์", {"due": "2026-10-30T09:00"}),
    ("เลื่อนข้อ 3 ไปพรุ่งนี้", {"due": "2026-10-31T09:00"}),
    ("เปลี่ยน #3 เป็นวันศุกร์หน้า", {"due": "2026-11-06T09:00"}),
    ("ย้าย #3 ไปมะรืน", {"due": "2026-11-01T09:00"}),
    ("change #3 time to 5pm", {"due": "2026-11-02T17:00"}),      # time only keeps the task's day
    ("#3 to friday", {"due": "2026-10-30T09:00"}),
    ("rename #3 to call dad", {"text": "Call dad"}),
    ("set #3 priority high", {"priority": "high"}),
    ("change #4 category to Shopping", {"category": "Shopping"}),
    ("update #4 tomorrow", {"due": "2026-10-31T09:00"}),
]

# Ordinary sentences that must NOT be read as commands
NOT_COMMANDS = ["set up the printer", "change the oil", "push the button", "move the car friday", "delay flight"]


class DateRules(unittest.TestCase):
    def test_dates(self):
        for sentence, k, want in DATES:
            with self.subTest(sentence=sentence, now=k):
                got = date_of(sentence, NOWS[k])
                self.assertIsNotNone(got, "Python should decide this date")
                if want.startswith("T"):          # only the clock time matters
                    self.assertTrue(got.endswith(want), got)
                else:
                    self.assertEqual(got, want)

    def test_left_to_ai(self):
        for sentence in LEFT_TO_AI:
            with self.subTest(sentence=sentence):
                self.assertIsNone(server.rules_date(sentence, T))

    def test_words_that_look_like_dates(self):
        for sentence in NOT_DATES:
            with self.subTest(sentence=sentence):
                rule = server.rules_date(sentence, T)
                self.assertTrue(rule is None or not server.resolve_due(rule, NOWS["Fri"], T))

    def test_titles_keep_owner_words(self):
        for sentence, want in TITLES:
            with self.subTest(sentence=sentence):
                got = " ".join(server.own_words(server.fix_date_typos(sentence)))
                self.assertEqual(got, want)


class QuestionRules(unittest.TestCase):
    def test_question_filters(self):
        for sentence, k, want in QUESTIONS:
            with self.subTest(sentence=sentence, now=k):
                f = server.question_filter(sentence.lower(), NOWS[k], server.DEFAULT_CATEGORIES)
                for field, value in want.items():
                    self.assertEqual(f[field], value, field)


class CommandRules(unittest.TestCase):
    def run_rules(self, sentence):
        return server.command_by_rules(sentence, NOW_TEXT, server.DEFAULT_CATEGORIES, COMMAND_TASKS)

    def test_number_commands(self):
        for sentence, action, num in COMMANDS:
            with self.subTest(sentence=sentence):
                r = self.run_rules(sentence)
                self.assertEqual((r["action"], r["num"]), (action, num))

    def test_update_commands(self):
        for sentence, changes in UPDATES:
            with self.subTest(sentence=sentence):
                r = self.run_rules(sentence)
                self.assertEqual(r["action"], "update")
                self.assertEqual(r["changes"], changes)

    def test_plain_sentences_are_not_commands(self):
        for sentence in NOT_COMMANDS:
            with self.subTest(sentence=sentence):
                self.assertIsNone(self.run_rules(sentence))

    def test_command_word_without_a_task_asks_which(self):
        for sentence in ["done", "delete it", "move it to friday"]:
            with self.subTest(sentence=sentence):
                self.assertTrue(self.run_rules(sentence).get("pickTask"))


if __name__ == "__main__":
    unittest.main()
