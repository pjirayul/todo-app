"""Automatic tests for Max's pure-Python logic in server.py.

Run from the app folder:   python -m unittest
No AI, no Ollama, no server and no real data are used:
- the AI call (parse_with_ollama) is replaced by a tiny fake,
- About me (load_memory) is replaced by the default times,
- "now" is frozen to Wednesday 28 Oct 2026, 10:00, so the tests never depend on today's date.
"""
import json
import os
import pathlib
import re
import unittest
from datetime import datetime, timedelta
from unittest import mock

import server

NOW_TEXT = "2026-10-28T10:00"                       # a Wednesday
NOW = datetime.strptime(NOW_TEXT, "%Y-%m-%dT%H:%M")


def fake_ai(prompt, *args, **kwargs):
    """Stands in for Max's AI. Like the real small model it copies the sentence as the title
    and reads a simple clock time; Python (the code under test) does everything else."""
    sentence = prompt.split("Sentence:")[-1].strip()
    time = ""
    m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", sentence, re.I)
    if m:
        hour = int(m.group(1)) % 12 + (12 if m.group(2).lower() == "pm" else 0)
        time = f"{hour:02d}:00"
    return {"text": sentence, "when": "none", "time": time, "priority": "med", "category": "", "tokens": 0}


def ai_says(intent, target=""):
    """A fake AI that sees a command (the real one does for "delete zebra"): the default fake only ever says "add"."""
    def ai(prompt, *a, **k):
        return {**fake_ai(prompt), "intent": intent, "target": target, "change": "", "reply": ""}
    return ai


def default_memory():
    return mock.patch.object(server, "load_memory", return_value=server.clean_memory({}))


PATHS = []


def ask(sentence, tasks=(), chosen=None, ai=fake_ai):
    """Run the command bar logic with the fake AI and the default About me."""
    with mock.patch.object(server, "parse_with_ollama", ai), default_memory(), \
         mock.patch.object(server, "AI_PROVIDER", "ollama"):
        result = server.run_command(sentence, NOW_TEXT, [], list(tasks), chosen)
    PATHS.append(result.pop("path"))   # every result says "rules" or "ai"; tests that care read PATHS[-1]
    return result


# Some tasks to talk about
TASKS = [
    {"num": 1, "text": "Do laundry", "done": False, "due": "2026-10-30T09:00"},
    {"num": 2, "text": "Call mom", "done": False, "due": ""},
    {"num": 3, "text": "Pay rent", "done": True, "due": ""},
    {"num": 9, "text": "Buy milk", "done": False, "due": ""},
]
DENTIST = [{"num": 4, "text": "Dentist", "done": False, "due": "2026-10-29T16:30"}]
CALLS = [{"num": 5, "text": "Call mom", "done": False}, {"num": 6, "text": "Call dad", "done": False}]


class ResolveDue(unittest.TestCase):
    def due(self, **task):
        return server.resolve_due(task, NOW)

    def test_no_date(self):
        self.assertEqual(self.due(when="none"), "")

    def test_today_and_tomorrow_use_morning_time(self):
        self.assertEqual(self.due(when="today"), "2026-10-28T09:00")
        self.assertEqual(self.due(when="tomorrow"), "2026-10-29T09:00")
        self.assertEqual(self.due(when="day_after_tomorrow"), "2026-10-30T09:00")

    def test_clock_times(self):
        self.assertEqual(self.due(when="today", time="20:00"), "2026-10-28T20:00")
        self.assertEqual(self.due(when="tomorrow", time="15:00"), "2026-10-29T15:00")

    def test_weekday_is_the_next_one_coming_up(self):
        self.assertEqual(self.due(when="weekday", weekday="Friday"), "2026-10-30T09:00")
        # Same weekday as today (Wednesday): plain "wednesday" is today, "next wednesday" is +7 (owner rule 30 Oct)
        self.assertEqual(self.due(when="weekday", weekday="Wednesday"), "2026-10-28T09:00")
        self.assertEqual(self.due(when="weekday", weekday="Wednesday", next_week=True), "2026-11-04T09:00")
        # A weekday already past this week -> next week's
        self.assertEqual(self.due(when="weekday", weekday="Monday"), "2026-11-02T09:00")

    def test_next_week_weekday(self):
        # "next friday" = first Friday strictly after today (Wednesday 28 Oct -> this week's Friday)
        self.assertEqual(self.due(when="weekday", weekday="Friday", next_week=True), "2026-10-30T09:00")
        # "friday next week" = the Friday inside next Mon-Sun week
        self.assertEqual(self.due(when="weekday", weekday="Friday", next_week=True, week_after=True), "2026-11-06T09:00")

    def test_the_fifth(self):
        self.assertEqual(self.due(when="date", day=5), "2026-11-05T09:00")     # 5th already passed: next month
        self.assertEqual(self.due(when="date", day=30), "2026-10-30T09:00")    # still ahead this month

    def test_day_and_month(self):
        self.assertEqual(self.due(when="date", day=25, month=12), "2026-12-25T09:00")
        self.assertEqual(self.due(when="date", day=1, month=3), "2027-03-01T09:00")   # March passed: next year

    def test_31st_in_short_month_uses_last_day(self):
        self.assertEqual(self.due(when="date", day=31, month=11), "2026-11-30T09:00")

    def test_in_days(self):
        self.assertEqual(self.due(when="in_days", in_days=3), "2026-10-31T09:00")

    def test_owner_morning_time_from_about_me(self):
        times = dict(server.DEFAULT_TIMES, morning="07:30")
        self.assertEqual(server.resolve_due({"when": "tomorrow"}, NOW, times), "2026-10-29T07:30")


class ThaiWordsAndDates(unittest.TestCase):
    def test_thai_times(self):
        self.assertEqual(server.thai_time("ส่งรายงานบ่ายสาม"), "15:00")
        self.assertEqual(server.thai_time("นัดสองทุ่ม"), "20:00")
        self.assertEqual(server.thai_time("บ่ายสามครึ่ง"), "15:30")
        self.assertEqual(server.thai_time("เที่ยง"), "12:00")
        self.assertEqual(server.thai_time("ตีสอง"), "02:00")
        self.assertEqual(server.thai_time("5 โมงเย็น"), "17:00")
        self.assertEqual(server.thai_time("buy milk"), "")

    def test_weekdays(self):
        self.assertEqual(server.weekday_in("ส่งงานวันศุกร์"), "Friday")
        self.assertEqual(server.weekday_in("call bank friday"), "Friday")
        self.assertEqual(server.weekday_in("buy milk"), "")

    def test_next_markers(self):
        self.assertTrue(server.NEXT_WEEK.search("call bank next friday"))
        self.assertTrue(server.NEXT_WEEK.search("ประชุมวันศุกร์หน้า"))
        self.assertFalse(server.NEXT_WEEK.search("call bank friday"))

    def test_thai_weekday_and_time(self):
        self.assertEqual(ask("ส่งรายงานวันศุกร์บ่ายสาม")["due"], "2026-10-30T15:00")

    def test_thai_next_friday(self):
        self.assertEqual(ask("ประชุมวันศุกร์หน้า")["due"], "2026-10-30T09:00")   # now is Wednesday

    def test_thai_tomorrow_and_tonight(self):
        self.assertEqual(ask("ซื้อนมพรุ่งนี้")["due"], "2026-10-29T09:00")
        self.assertEqual(ask("ซื้อนมคืนนี้")["due"], "2026-10-28T20:00")


class TypoFixing(unittest.TestCase):
    def test_date_typos(self):
        self.assertEqual(server.fix_date_typos("call bank frday"), "call bank friday")
        self.assertEqual(server.fix_date_typos("pay rent tmrw"), "pay rent tomorrow")
        self.assertEqual(server.fix_date_typos("tomorow"), "tomorrow")
        self.assertEqual(server.fix_date_typos("พรุ่งนี สวัสดี"), "พรุ่งนี้ สวัสดี")

    def test_normal_words_are_left_alone(self):
        self.assertEqual(server.fix_date_typos("pay rent"), "pay rent")   # "rent" must not become "urgent"


class AddingTasks(unittest.TestCase):
    def test_add_word_is_stripped(self):
        self.assertEqual(ask("add buy milk")["text"], "Buy milk")
        self.assertEqual(ask("Add buy milk")["text"], "Buy milk")
        self.assertEqual(ask("เพิ่ม ซื้อนม")["text"], "ซื้อนม")
        self.assertEqual(ask("เพิ่มงาน ซื้อนม")["text"], "ซื้อนม")

    def test_plain_task_has_no_date(self):
        r = ask("buy milk")
        self.assertEqual((r["action"], r["text"], r["due"]), ("add", "Buy milk", ""))

    def test_tomorrow_3pm(self):
        self.assertEqual(ask("call mom tomorrow 3pm")["due"], "2026-10-29T15:00")

    def test_N1_title_keeps_owners_words(self):
        # The AI dropped everything but "TEST": Python must put the owner's words back
        def lazy_ai(prompt, *a, **k):
            return dict(fake_ai(prompt), text="TEST")
        r = ask("TEST dentist frday 3pm", ai=lazy_ai)
        self.assertEqual(r["text"], "TEST dentist")
        self.assertEqual(r["due"], "2026-10-30T15:00")

    def test_N1_with_a_normal_ai(self):
        r = ask("TEST dentist frday 3pm")
        self.assertIn("TEST", r["text"])
        self.assertIn("dentist", r["text"].lower())
        self.assertEqual(r["due"], "2026-10-30T15:00")

    def test_capitals_are_kept(self):
        def ai(prompt, *a, **k):
            return dict(fake_ai(prompt), text="Pay the atm fee")
        self.assertIn("ATM", ask("pay the ATM fee", ai=ai)["text"])

    def test_only_a_time_means_today(self):
        self.assertEqual(ask("call mom at 5pm")["due"], "2026-10-28T17:00")


class CommandWords(unittest.TestCase):
    def test_done(self):
        self.assertEqual(ask("done #2", TASKS), {"action": "complete", "num": 2})
        self.assertEqual(ask("mark #2 as done", TASKS), {"action": "complete", "num": 2})
        self.assertEqual(ask("finished laundry", TASKS)["num"], 1)
        self.assertEqual(ask("งาน #2 เสร็จแล้ว", TASKS), {"action": "complete", "num": 2})

    def test_undo(self):
        self.assertEqual(ask("undo pay rent", TASKS), {"action": "uncomplete", "num": 3})
        self.assertEqual(ask("undo #3", TASKS), {"action": "uncomplete", "num": 3})

    def test_delete(self):
        self.assertEqual(ask("delete #9", TASKS), {"action": "delete", "num": 9})
        self.assertEqual(ask("delete lundry", TASKS), {"action": "delete", "num": 1})   # typo in the name
        self.assertEqual(ask("ลบ #2", TASKS), {"action": "delete", "num": 2})

    def test_move_to_a_day(self):
        r = ask("move #2 to monday", TASKS)           # task 2 has no date yet: morning time
        self.assertEqual((r["action"], r["num"]), ("update", 2))
        self.assertEqual(r["changes"]["due"], "2026-11-02T09:00")

    def test_day_only_keeps_existing_time(self):
        r = ask("move #4 to monday", DENTIST)
        self.assertEqual(r["changes"]["due"], "2026-11-02T16:30")

    def test_time_only_keeps_existing_day(self):
        r = ask("move #4 to 5pm", DENTIST)
        self.assertEqual(r["changes"]["due"], "2026-10-29T17:00")

    def test_rename_forms(self):
        r = ask("rename #9 to Buy oat milk", TASKS)
        self.assertEqual((r["action"], r["num"], r["changes"]), ("update", 9, {"text": "Buy oat milk"}))
        r = ask("#9 rename to Buy oat milk", TASKS)        # number first
        self.assertEqual((r["num"], r["changes"]), (9, {"text": "Buy oat milk"}))

    def test_change_to_text_is_a_rename(self):
        self.assertEqual(ask("change #2 to call dad", TASKS)["changes"], {"text": "Call dad"})

    def test_modify_priority_and_category(self):
        self.assertEqual(ask("modify #2 priority high", TASKS)["changes"], {"priority": "high"})
        self.assertEqual(ask("change category of #2 to Family", TASKS)["changes"], {"category": "Family"})

    def test_rename_does_not_touch_date(self):
        self.assertNotIn("due", ask("rename #1 to Wash clothes", TASKS)["changes"])

    def test_no_to_means_new_task(self):
        self.assertEqual(ask("set up the printer", TASKS)["action"], "add")

    def test_modify_with_nothing_to_change(self):
        self.assertTrue(ask("modify #2", TASKS).get("nothing"))


class AskWhenUnsure(unittest.TestCase):
    def test_missing_target_asks_which(self):
        self.assertEqual(ask("done", TASKS), {"action": "complete", "pickTask": True})
        self.assertEqual(ask("delete it", TASKS), {"action": "delete", "pickTask": True})

    def test_unknown_task_reports_missing(self):
        r = ask("delete zebra", TASKS, ai=ai_says("delete", "zebra"))
        self.assertEqual((r["action"], r["missing"], r["choices"]), ("delete", "zebra", []))

    def test_unknown_number_reports_missing(self):
        self.assertEqual(ask("done #77", TASKS)["missing"], "#77")

    def test_ambiguous_match_gives_choices(self):
        r = ask("delete call", CALLS, ai=ai_says("delete", "call"))
        self.assertEqual(r["action"], "delete")
        self.assertIsNone(r.get("num"))
        self.assertEqual(sorted(r["choices"]), [5, 6])

    def test_chosen_number_settles_the_question(self):
        self.assertEqual(ask("delete call", CALLS, chosen=6), {"action": "delete", "num": 6})

    def test_event_and_travel_words(self):
        for text in ("meeting with Tom", "dentist", "book a flight", "hotel in Penang", "นัดหมอ", "จองโรงแรม", "ประชุมทีม"):
            self.assertTrue(server.ask_words(text), text)
        for text in ("buy milk", "pay rent", "call mom"):
            self.assertFalse(server.ask_words(text), text)

    def test_new_event_without_a_day_or_time_asks_when(self):
        r = ask("meeting with Tom")
        self.assertTrue(r["askWhen"])
        self.assertEqual(r["due"], "")
        self.assertEqual(r["time"], "09:00")     # Max's morning time is used with the day the owner picks

    def test_event_with_only_a_time_is_today(self):
        # Note: the comment in add_task suggests "meeting with Tom at 3pm" should ask "When?", but a time
        # alone means today (same rule as "call mom at 5pm"), so no question. Kept as the current behaviour.
        r = ask("meeting with Tom at 3pm")
        self.assertNotIn("askWhen", r)
        self.assertEqual(r["due"], "2026-10-28T15:00")

    def test_event_with_a_day_does_not_ask(self):
        r = ask("meeting with Tom tomorrow 3pm")
        self.assertNotIn("askWhen", r)
        self.assertEqual(r["due"], "2026-10-29T15:00")

    def test_event_without_ai_uses_morning_time(self):
        with default_memory():
            r = server.add_without_ai("dentist")
        self.assertTrue(r["askWhen"])
        self.assertEqual(r["time"], "09:00")

    def test_normal_task_without_ai_has_no_question(self):
        r = server.add_without_ai("add buy milk")
        self.assertNotIn("askWhen", r)
        self.assertEqual(r["text"], "Buy milk")

    def test_breakdown_questions(self):
        self.assertEqual(server.breakdown_questions("buy milk", "", ""), [])        # not an event: just suggest
        self.assertEqual(server.breakdown_questions("trip", "", ""), ["where", "when", "budget"])
        self.assertEqual(server.breakdown_questions("trip to Chiang Mai", "", "2026-11-05T09:00"), [])
        self.assertEqual(server.breakdown_questions("meeting", "", ""), ["where", "when"])  # no budget for meetings
        self.assertEqual(server.breakdown_questions("trip", "Trip details: Phuket", ""), [])


if __name__ == "__main__":
    unittest.main()


def ai_dropping_dates(title, category=""):
    """A fake AI that answers with the given title/category (like a model that tidied the sentence)."""
    return lambda prompt, *a, **k: {"text": title, "when": "none", "time": "", "priority": "med",
                                    "category": category, "tokens": 0}


class LeadIns(unittest.TestCase):
    def test_remind_me_to_is_stripped(self):
        self.assertEqual(server.strip_lead_in("remind me to call mom tomorrow"), "call mom tomorrow")
        self.assertEqual(server.strip_lead_in("Remind me call mom"), "call mom")
        self.assertEqual(server.strip_lead_in("don't forget to buy milk"), "buy milk")
        self.assertEqual(server.strip_lead_in("เตือนให้โทรหาแม่"), "โทรหาแม่")
        self.assertEqual(server.strip_lead_in("อย่าลืมซื้อนม"), "ซื้อนม")

    def test_other_words_are_kept(self):
        self.assertEqual(server.strip_lead_in("call the reminder office"), "call the reminder office")
        self.assertEqual(server.strip_lead_in("remind me"), "remind me")  # nothing left: keep as typed

    def test_title_of_a_remind_command(self):
        result = ask("remind me to call mom tomorrow", ai=ai_dropping_dates("Remind me to call mom"))
        self.assertEqual(result["text"], "Call mom")
        self.assertEqual(result["due"], "2026-10-29T09:00")


class CategoryHints(unittest.TestCase):
    def test_hints_when_ai_gives_none(self):
        pick = server.pick_category
        self.assertEqual(pick("", "gym at 7am", []), "Health")
        self.assertEqual(pick("", "dentist friday", []), "Health")
        self.assertEqual(pick("", "pay rent", []), "Home")        # rent is Home, not Money
        self.assertEqual(pick("", "buy groceries", []), "Home")
        self.assertEqual(pick("", "clean the kitchen", []), "Home")
        self.assertEqual(pick("", "ไปฟิตเนส", []), "Health")
        self.assertEqual(pick("", "นัดหมอฟัน", []), "Health")
        self.assertEqual(pick("", "ซักผ้า", []), "Home")
        self.assertEqual(pick("", "something else", []), "")

    def test_odd_ai_category_is_replaced(self):
        self.assertEqual(server.pick_category("Fitnessy", "go to the gym", []), "Health")
        self.assertEqual(server.pick_category("Stuff", "no hint here", []), "Stuff")  # nothing better: keep

    def test_good_ai_category_is_kept(self):
        self.assertEqual(server.pick_category("Shopping", "buy shoes", []), "Shopping")
        self.assertEqual(server.pick_category("Work", "team meeting", []), "Work")
        self.assertEqual(server.pick_category("Work", "gym", []), "Health")      # the AI over-uses Work
        self.assertEqual(server.pick_category("Personal", "something", []), "Personal")  # no hint: kept
        self.assertEqual(server.pick_category("health", "x", []), "Health")
        self.assertEqual(server.pick_category("Family", "gym", ["Family"]), "Family")  # the owner's own

    def test_work_words_are_never_overridden(self):
        pick = server.pick_category
        for text in ("run the team meeting", "send run report to boss", "clean up the project code", "repair the server",
                     "call dentist about report", "email boss about tax", "prepare class presentation for client",
                     "send report to boss", "ประชุมทีมงาน"):
            self.assertEqual(pick("Work", text, []), "Work", text)
        self.assertEqual(pick("Home", "clean the office", []), "Home")  # known non-Work category stays

    def test_strong_hints_fix_wrong_known_category(self):
        pick = server.pick_category
        self.assertEqual(pick("Home", "go to the gym tomorrow", []), "Health")
        self.assertEqual(pick("Money", "pay rent on the 5th", []), "Home")
        self.assertEqual(pick("Work", "gym friday 6pm", []), "Health")
        self.assertEqual(pick("Personal", "ไปยิม", []), "Health")
        self.assertEqual(pick("Money", "dentist on friday", []), "Health")

    def test_owner_spelling_wins(self):
        self.assertEqual(server.pick_category("", "gym", ["HEALTH"]), "HEALTH")

    def test_command_bar_uses_hints(self):
        self.assertEqual(ask("gym tomorrow 7am")["category"], "Health")


class OffsiteBackup(unittest.TestCase):
    def test_copies_newest_and_keeps_14(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            local, cloud = os.path.join(tmp, "backups"), os.path.join(tmp, "cloud", "JustSayIt")
            os.makedirs(local)
            os.makedirs(os.path.join(tmp, "cloud"))
            for day in range(1, 21):
                for name in (f"tasks-202610{day:02d}-120000.json", f"tasks-db-202610{day:02d}-120000.db"):
                    pathlib.Path(os.path.join(local, name)).write_text("x")
            with mock.patch.object(server, "BACKUP_DIR", local), mock.patch.object(server, "OFFSITE_BACKUP_DIR", cloud), \
                 mock.patch.object(server, "DATA_DIR", tmp), mock.patch.object(server, "TEST_MODE", False):
                server.offsite_backup()
                self.assertEqual(sorted(os.listdir(cloud))[-1], "tasks-db-20261020-120000.db")
                self.assertIn("tasks-20261020-120000.json", os.listdir(cloud))
                # a second call on the same day does nothing
                os.remove(os.path.join(cloud, "tasks-20261020-120000.json"))
                server.offsite_backup()
                self.assertNotIn("tasks-20261020-120000.json", os.listdir(cloud))
                # many days of copies: only the newest 14 of each kind stay in the cloud folder
                for day in range(1, 20):
                    pathlib.Path(os.path.join(cloud, f"tasks-202609{day:02d}-120000.json")).write_text("x")
                os.remove(os.path.join(tmp, "offsite-last.txt"))
                server.offsite_backup()
                kinds = [n for n in os.listdir(cloud) if n.startswith("tasks-2")]
                self.assertEqual(len(kinds), 14)
            self.assertEqual(len(os.listdir(local)), 40)  # local backups untouched

    def test_skipped_without_onedrive_and_in_test_mode(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "nope", "JustSayIt")
            with mock.patch.object(server, "OFFSITE_BACKUP_DIR", missing), mock.patch.object(server, "TEST_MODE", False):
                server.offsite_backup()
                self.assertFalse(os.path.exists(os.path.dirname(missing)))
            cloud = os.path.join(tmp, "JustSayIt")
            with mock.patch.object(server, "OFFSITE_BACKUP_DIR", cloud), mock.patch.object(server, "TEST_MODE", True):
                server.offsite_backup()
                self.assertFalse(os.path.exists(cloud))


# ---------- Ask Max: questions about the tasks ----------
QTASKS = [
    {"num": 1, "text": "Pay rent", "done": False, "due": "2026-10-28T09:00", "priority": "high", "cat": "Home"},
    {"num": 2, "text": "Dentist", "done": False, "due": "2026-10-28T16:00", "priority": "med", "cat": "Health"},
    {"num": 3, "text": "Send report", "done": False, "due": "2026-10-29T10:00", "priority": "high", "cat": "Work"},
    {"num": 4, "text": "Team meeting", "done": False, "due": "2026-10-30T09:00", "priority": "high", "cat": "Work"},
    {"num": 5, "text": "Call mom", "done": False, "due": "2026-10-26T09:00", "priority": "med", "cat": "Home"},
    {"num": 6, "text": "Buy milk", "done": False, "due": "", "priority": "med", "cat": ""},
    {"num": 7, "text": "Old rent receipt", "done": True, "due": "2026-10-27T09:00", "priority": "med", "cat": "Home"},
    {"num": 8, "text": "Plan trip", "done": False, "due": "2026-11-03T09:00", "priority": "med", "cat": ""},
    {"num": 9, "text": "Water bill", "done": False, "due": "2026-11-05T09:00", "priority": "low", "cat": "Money"},
]


def no_ai(*args, **kwargs):
    raise AssertionError("a question that Python understands must not call the AI")


def question(sentence, tasks=QTASKS, ai=no_ai, use_ai=True):
    with mock.patch.object(server, "parse_with_ollama", ai), default_memory():
        return server.question_answer(sentence, NOW_TEXT, [], list(tasks), use_ai)


class AskMax(unittest.TestCase):
    def nums(self, sentence):
        answer = question(sentence)
        self.assertIsNotNone(answer, sentence)
        self.assertEqual(answer["action"], "answer")
        return answer["nums"]

    def test_english_when(self):
        self.assertEqual(self.nums("what is due today?"), [1, 2])
        self.assertEqual(self.nums("what's due tomorrow"), [3])
        self.assertEqual(self.nums("what's overdue"), [5, 1])          # soonest first
        self.assertEqual(self.nums("anything late?"), [5, 1])
        self.assertEqual(self.nums("what is due this week?"), [1, 2, 3, 4])  # today until Sunday 1 Nov
        self.assertEqual(self.nums("what's due next week?"), [8, 9])
        self.assertEqual(self.nums("which tasks have no date?"), [6])
        self.assertEqual(self.nums("what is due on friday?"), [4])
        self.assertEqual(self.nums("what is due on the 5th?"), [9])

    def test_english_priority_category_status_text(self):
        self.assertEqual(self.nums("show high priority work this week"), [3, 4])
        self.assertEqual(self.nums("list my home tasks"), [5, 1])
        self.assertEqual(self.nums("how many tasks left"), [5, 1, 2, 3, 4, 8, 9, 6])
        self.assertEqual(self.nums("which tasks are done?"), [7])
        self.assertEqual(self.nums("anything about rent?"), [1])        # done #7 has "rent" too, but open is the default
        self.assertEqual(self.nums("anything about work?"), [3, 4])     # a category name means the category

    def test_thai(self):
        self.assertEqual(self.nums("วันนี้มีงานอะไรบ้าง"), [1, 2])
        self.assertEqual(self.nums("งานที่เลยกำหนด"), [5, 1])
        self.assertEqual(self.nums("พรุ่งนี้มีอะไรบ้าง"), [3])
        self.assertEqual(self.nums("มีกี่งาน"), [5, 1, 2, 3, 4, 8, 9, 6])
        self.assertEqual(self.nums("แสดงงานด่วนสัปดาห์นี้"), [1, 3, 4])
        self.assertEqual(self.nums("มีอะไรเกี่ยวกับค่าเช่า"), [])

    def test_filter_is_returned(self):
        f = question("show high priority work this week")["filter"]
        self.assertEqual((f["when"], f["priority"], f["cat"], f["status"]), ("week", "high", "work", "open"))

    def test_typos_are_fixed(self):
        self.assertEqual(self.nums("what is due tomorow?"), [3])

    def test_not_questions(self):
        for text in ["add buy milk tomorrow", "move #3 to friday", "done #2", "Buy milk", "show Tom the report tomorrow",
                     "pay rent on the 5th", "what is #3?", "ซื้อนมพรุ่งนี้", "Call mom?"]:
            self.assertIsNone(question(text, ai=lambda *a, **k: {"is_question": False, "when": "none",
                                                                   "priority": "any", "status": "open"}), text)

    def test_no_ai_for_clear_questions(self):
        # no_ai() raises if the AI is called; these must be understood by Python alone
        for text in ["what is due today?", "วันนี้มีงานอะไรบ้าง", "how many tasks left"]:
            self.assertIsNotNone(question(text))

    def test_ai_fallback_only_sorts_the_question(self):
        fake = lambda *a, **k: {"is_question": True, "when": "overdue", "priority": "any", "status": "open", "tokens": 7}
        answer = question("is there anything I forgot about?", ai=fake)
        self.assertEqual((answer["filter"]["when"], answer["nums"], answer["tokens"]), ("overdue", [5, 1], 7))
        # the AI's list is only a filter: Python still does the counting, and bad answers are ignored
        broken = lambda *a, **k: (_ for _ in ()).throw(OSError("Ollama is off"))
        self.assertIsNone(question("is there anything I forgot about?", ai=broken))
        self.assertIsNone(question("is there anything I forgot about?", use_ai=False))

    def test_through_run_command(self):
        answer = ask("what's due today?", QTASKS)
        self.assertEqual((answer["action"], answer["nums"]), ("answer", [1, 2]))
        self.assertEqual(ask("add buy milk tomorrow", QTASKS)["action"], "add")   # normal commands unchanged
        self.assertEqual(ask("done #2", QTASKS)["action"], "complete")
        self.assertEqual(ask("move #3 to friday", QTASKS)["action"], "update")

    def test_tools(self):
        f = dict(server.EMPTY_FILTER, when="today")
        self.assertEqual(server.count_tasks(QTASKS, f, NOW), 2)
        self.assertEqual([t["num"] for t in server.TOOLS["list_tasks"](QTASKS, dict(f, priority="high"), NOW)], [1])


class GreetingsAndGate(unittest.TestCase):
    """Greetings in front, natural question forms, the loose AI gate and the mistakes log."""
    YES = lambda *a, **k: {"is_question": True, "when": "none", "priority": "any", "status": "open", "tokens": 3}
    NO = lambda *a, **k: {"is_question": False, "when": "none", "priority": "any", "status": "open", "tokens": 3}

    def nums(self, sentence, ai=no_ai):
        answer = question(sentence, ai=ai)
        self.assertIsNotNone(answer, sentence)
        return answer["nums"]

    def test_strip_greeting(self):
        for text, rest in [("Hi max, what to do today", "what to do today"), ("hey max add milk", "add milk"),
                           ("Hello, what is due", "what is due"), ("ok max what's overdue", "what's overdue"),
                           ("max, done #2", "done #2"), ("สวัสดีครับ max วันนี้ทำอะไรดี", "วันนี้ทำอะไรดี"),
                           ("แม็กซ์ พรุ่งนี้มีอะไร", "พรุ่งนี้มีอะไร"), ("สวัสดีค่ะ แม็กซ์ วันนี้ต้องทำอะไร", "วันนี้ต้องทำอะไร")]:
            self.assertEqual(server.strip_greeting(text), (rest, True), text)
        # not greetings: a task that merely starts like one, or only a greeting
        for text in ["Max birthday gift", "hi-vis vest tomorrow", "okra soup for dinner", "Hi max", "Buy milk"]:
            self.assertEqual(server.strip_greeting(text), (text, False), text)

    def test_greeting_then_question_is_not_a_task(self):
        self.assertEqual(self.nums("Hi max, what to do today"), [1, 2])    # the owner's bug (task #116)
        self.assertEqual(self.nums("hey max what's due tomorrow?"), [3])
        answer = ask("Hi max, what to do today", QTASKS)
        self.assertEqual((answer["action"], answer["nums"]), ("answer", [1, 2]))

    def test_natural_question_forms(self):
        self.assertEqual(self.nums("what to do today"), [1, 2])
        self.assertEqual(self.nums("what to do tomorrow"), [3])
        self.assertEqual(self.nums("what to do this week"), [1, 2, 3, 4])
        self.assertEqual(self.nums("what should i do"), [5, 1, 2, 3, 4, 8, 9, 6])
        self.assertEqual(self.nums("what do i have"), [5, 1, 2, 3, 4, 8, 9, 6])
        self.assertEqual(self.nums("what's my plan today"), [1, 2])
        self.assertEqual(self.nums("what's my day"), [5, 1, 2, 3, 4, 8, 9, 6])
        self.assertEqual(self.nums("my tasks today"), [1, 2])

    def test_natural_thai(self):
        self.assertEqual(self.nums("วันนี้ทำอะไรดี"), [1, 2])
        self.assertEqual(self.nums("วันนี้ต้องทำอะไร"), [1, 2])
        self.assertEqual(self.nums("ต้องทำอะไรบ้าง"), [5, 1, 2, 3, 4, 8, 9, 6])
        self.assertEqual(self.nums("พรุ่งนี้มีอะไร"), [3])
        self.assertEqual(self.nums("สวัสดีครับ แม็กซ์ วันนี้ทำอะไรดี"), [1, 2])

    def test_greeting_keeps_commands_commands(self):
        add = ask("hey max add milk tomorrow", QTASKS)
        self.assertEqual(add["action"], "add")
        self.assertEqual(add["text"], "Milk tomorrow")  # no "hey max", no "add" (the fake AI keeps the date words)
        self.assertEqual(ask("Hi max, done #2", QTASKS)["action"], "complete")
        self.assertEqual(ask("ok max, delete #3", QTASKS)["action"], "delete")
        self.assertEqual(ask("hello move #3 to friday", QTASKS)["action"], "update")
        self.assertEqual(ask("สวัสดีครับ max ลบ #3", QTASKS)["action"], "delete")

    def test_greeting_alone_is_not_a_task(self):
        # no_ai: the greeting alone must not even cost an AI call
        for text in ["hi max", "Hello", "hey max!", "สวัสดี แม็กซ์", "สวัสดีครับ"]:
            self.assertEqual(ask(text, QTASKS, ai=no_ai), {"action": "greeting"}, text)
        self.assertEqual(ask("hey max buy milk", QTASKS)["action"], "add")

    def test_clear_tasks_skip_the_ai(self):
        # no_ai() raises if the AI is asked: a clear task or command must not cost the extra step
        for text in ["pay rent on the 5th", "call mom 6pm", "Buy milk", "ซื้อนมพรุ่งนี้", "done #2", "delete laundry"]:
            self.assertIsNone(question(text), text)

    def test_loose_gate_asks_the_ai(self):
        # question word anywhere, a "?", or a greeting -> the AI decides; it can say no
        for text in ["can you tell me how it goes", "do I owe anything this month", "Call mom?", "hi max, buy milk",
                     "ซื้อนมไหม", "ทำยังไงดี"]:
            calls = []
            def spy(*a, **k):
                calls.append(1)
                return self.NO()
            self.assertIsNone(question(text, ai=spy), text)
            self.assertEqual(len(calls), 1, text)
        self.assertEqual(self.nums("hi max, anything urgent for me?", ai=self.YES), [1, 3, 4])  # "urgent" is Python's filter

    def test_python_filter_wins_over_the_ai(self):
        # the AI says "overdue" but the owner typed "tomorrow": Python's reading stays
        fake = lambda *a, **k: {"is_question": True, "when": "overdue", "priority": "any", "status": "open", "tokens": 1}
        self.assertEqual(self.nums("could there be something I should know tomorrow", ai=fake), [3])

    def test_ai_offline_means_rules_only(self):
        broken = lambda *a, **k: (_ for _ in ()).throw(OSError("Ollama is off"))
        self.assertIsNone(question("hi max, buy milk", ai=broken))
        self.assertIsNone(question("hi max, buy milk", use_ai=False))
        self.assertEqual(question("hi max, what to do today", use_ai=False)["nums"], [1, 2])  # rules still answer


class SmallTalk(unittest.TestCase):
    """Chit-chat gets a friendly reply and never a task. A tiny seed list is the fast path; the AI decides the rest."""
    CHAT = lambda *a, **k: {"is_question": False, "chat": True, "reply": "Thanks! What can I do for you?", "when": "none",
                            "priority": "any", "status": "open", "tokens": 3}

    def test_seed_list_needs_no_ai(self):
        for kind, texts in {"compliment": ["You are so smart", "you're so smart", "hi max, you're so smart", "เก่งมาก", "เก่งจัง"],
                            "thanks": ["thanks", "Thank you", "thx", "ty", "thanks max!", "ขอบคุณ", "ขอบคุณมากครับ"]}.items():
            for text in texts:
                self.assertEqual(ask(text, ai=no_ai), {"action": "smalltalk", "kind": kind}, text)

    def test_ai_chat_gets_a_reply(self):
        # sentences not in the seed list reach the AI (short, no date, no task verb) and it says chat
        for text in ["you did well", "good job max", "nice one", "คุณช่วยได้ดีมาก", "how are you", "สบายดีไหม"]:
            self.assertTrue(server.maybe_chat(" ".join(text.lower().split())) or text in ("how are you", "สบายดีไหม"), text)
            with mock.patch.object(server, "ONE_CALL", False):   # this is the old two-call road (gate call, then parse)
                r = ask(text, ai=self.CHAT)
            # a Thai sentence with an English reply: the reply is dropped (the Thai fallback line is used)
            want = server.CHAT_FALLBACK["th"] if re.search("[฀-๿]", text) else "Thanks! What can I do for you?"
            self.assertEqual((r["action"], r["kind"], r["reply"]), ("smalltalk", "chat", want), text)

    def test_reply_is_cleaned(self):
        self.assertEqual(server.clean_reply("Hi <b>there</b> 😀"), "Hi bthere/b")
        self.assertEqual(server.clean_reply("x" * 81), "")
        self.assertEqual(server.clean_reply(None), "")

    def test_real_tasks_skip_the_ai(self):
        # the gate must say "no AI needed" for clear tasks and commands (so they are added fast)
        for text in ["pay rent on the 5th", "buy a smart watch", "thank Olive for the gift tomorrow", "Laundry", "call mom",
                     "ซื้อนม", "ขอบคุณคุณแม่พรุ่งนี้", "done #2", "Buy milk friday"]:
            self.assertFalse(server.maybe_question(text.lower(), False), text)
            self.assertIsNone(server.small_talk(text), text)

    def test_chat_ai_down_or_says_task(self):
        # AI off: the sentence is added as before; AI says "not chat": a task
        def down(*a, **k):
            raise RuntimeError("offline")
        with mock.patch.object(server, "parse_with_ollama", down), default_memory():
            self.assertIsNone(server.question_answer("you did well", NOW_TEXT, [], []))  # then the page adds it as plain text
        with mock.patch.object(server, "parse_with_ollama", lambda *a, **k: {"is_question": False, "chat": False, "tokens": 1}),                 default_memory():
            self.assertIsNone(server.question_answer("you did well", NOW_TEXT, [], []))

    def test_logged_mistake(self):
        # first real learning-loop case: "You are so smart" became a task
        self.assertEqual(ask("You are so smart", ai=no_ai)["action"], "smalltalk")
        self.assertFalse(server.maybe_chat("pay rent on the 5th"))
        self.assertFalse(server.maybe_chat("buy a smart watch"))
        self.assertFalse(server.maybe_chat("thank olive for the gift tomorrow"))


class MistakesLog(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.dir = tempfile.TemporaryDirectory()
        patcher = mock.patch.object(server, "MISTAKES_FILE", self.dir.name + "/max-mistakes.json")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.dir.cleanup)

    def test_logs_a_deleted_add(self):
        self.assertEqual(server.load_mistakes(), [])
        ok = server.add_mistake({"text": "Hi max, what to do today", "action": "add",
                                 "created": "2026-10-30T15:03:00Z", "deletedAt": "2026-10-30T15:04:00Z"})
        self.assertTrue(ok)
        ok = server.add_mistake({"text": "ซื้อนม", "action": "add", "created": "a", "deletedAt": "b"})
        saved = server.load_mistakes()
        self.assertEqual([m["text"] for m in saved], ["Hi max, what to do today", "ซื้อนม"])  # Thai survives
        self.assertEqual(set(saved[0]), {"text", "action", "created", "deletedAt"})

    def test_rejects_bad_records_and_caps_size(self):
        self.assertFalse(server.add_mistake({"text": "", "action": "add"}))
        self.assertFalse(server.add_mistake({"text": "x", "action": "delete"}))
        self.assertEqual(server.load_mistakes(), [])
        server.add_mistake({"text": "y" * 999, "action": "add"})
        self.assertEqual(len(server.load_mistakes()[0]["text"]), 200)

    def test_test_mode_uses_its_own_file(self):
        self.assertIn("max-mistakes", server.MISTAKES_FILE)
        self.assertTrue(server.__dict__["use_test_mode"].__doc__)


class TailscaleAccessTests(unittest.TestCase):
    def test_client_ip(self):
        for ip in ("127.0.0.1", "::1", "100.64.0.5", "100.100.100.100", "fd7a:115c:a1e0::1"):
            self.assertTrue(server.client_ip_ok(ip), ip)
        for ip in ("192.168.1.10", "8.8.8.8", "100.128.0.1", "fd00::1", "nonsense"):
            self.assertFalse(server.client_ip_ok(ip), ip)

    def test_host_allowlist(self):
        # made-up names; the owner's real ones are in data/local-hosts.json (private)
        old = server.HOST_NAMES
        server.HOST_NAMES = ("127.0.0.1", "localhost", "100.64.0.5", "my-pc", "my-pc.example-tailnet.ts.net")
        try:
            hosts = server.make_allowed_hosts(8000)
            for h in ("127.0.0.1:8000", "100.64.0.5:8000", "my-pc:8000", "my-pc.example-tailnet.ts.net:8000"):
                self.assertIn(h, hosts)
            self.assertNotIn("evil.com:8000", hosts)
            self.assertIn("100.64.0.5:8001", server.make_allowed_hosts(8001))
        finally:
            server.HOST_NAMES = old

    def test_local_hosts_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "h.json")
            self.assertEqual(server.load_local_hosts(p), ())  # missing file = none
            with open(p, "w", encoding="utf-8") as f:
                json.dump(["100.64.0.5", "My-PC"], f)
            self.assertEqual(server.load_local_hosts(p), ("100.64.0.5", "my-pc"))


class FastPath(unittest.TestCase):
    """Date/time changes on existing tasks are read by Python alone (no AI call)."""
    def no_ai(self, *a, **k):
        raise AssertionError("the AI should not be called")

    def test_rules_only_updates(self):
        for s, due in (("move #1 to friday", "2026-10-30T09:00"), ("#2 tomorrow 5pm", "2026-10-29T17:00"),
                       ("move #1 to 5pm", "2026-10-30T17:00"), ("เลื่อน #1 เป็นพรุ่งนี้บ่ายสาม", "2026-10-29T15:00"),
                       ("move #1 to monday", "2026-11-02T09:00")):
            with self.subTest(s):
                r = ask(s, TASKS, ai=self.no_ai)
                self.assertEqual(r["changes"]["due"], due)
                self.assertEqual(PATHS[-1], "rules")

    def test_hard_dates_still_use_the_ai(self):
        ask("move #1 to next week", TASKS)
        self.assertEqual(PATHS[-1], "ai")
        ask("move #1 to march 5", TASKS)
        self.assertEqual(PATHS[-1], "ai")

    def test_in_n_days_english_and_thai(self):
        # The fake AI says nothing about the date: Python must set it from the count
        self.assertEqual(ask("pay internet in 3 days")["due"], "2026-10-31T09:00")
        self.assertEqual(ask("จ่ายค่าเน็ตอีก 3 วัน")["due"], "2026-10-31T09:00")
        self.assertEqual(ask("move #1 to in 2 days", TASKS)["changes"]["due"][:10], "2026-10-30")
        self.assertEqual(PATHS[-1], "rules")


class ThaiTitleLinkingWords(unittest.TestCase):
    """Job 0g-1: the little word stuck to a date goes with it, the same word elsewhere stays."""

    def title(self, sentence):
        return ask(sentence)["text"]   # the fake AI copies the sentence, so this tests Python's clean-up

    def test_linking_words_go_with_the_date(self):
        self.assertEqual(self.title("ขอ claude จาก ploy ในวันศุกร์"), "ขอ claude จาก ploy")
        self.assertEqual(self.title("ส่งรายงานภายในพรุ่งนี้"), "ส่งรายงาน")
        self.assertEqual(self.title("กินข้าวกับแม่ในวันอาทิตย์"), "กินข้าวกับแม่")
        self.assertEqual(self.title("ประชุมทีมเมื่อวันจันทร์"), "ประชุมทีม")

    def test_time_words_are_cut_whole(self):
        self.assertEqual(self.title("นัดหมอตอนบ่ายสาม"), "นัดหมอ")
        self.assertEqual(self.title("โทรหาลูกค้าตอนเย็น"), "โทรหาลูกค้า")

    def test_same_word_elsewhere_stays(self):
        self.assertEqual(self.title("ล้างของในตู้เย็นพรุ่งนี้"), "ล้างของในตู้เย็น")
        self.assertEqual(self.title("ซื้อของใช้ในบ้าน"), "ซื้อของใช้ในบ้าน")

    def test_dates_still_read(self):
        self.assertEqual(ask("ขอ claude จาก ploy ในวันศุกร์")["due"], "2026-10-30T09:00")   # Friday after Wed 28 Oct
        self.assertEqual(ask("นัดหมอตอนบ่ายสาม")["due"], "2026-10-28T15:00")

    def test_english_titles_are_not_touched(self):
        clean = lambda *a, **k: {**fake_ai(*a), "text": "check in at hotel", "when": "none", "time": "15:00"}
        self.assertEqual(ask("check in at hotel at 3pm", ai=clean)["text"], "Check in at hotel")


class OneCallUnderstand(unittest.TestCase):
    """Job 0h-1: ONE AI call understands the sentence; Python checks every part of the answer."""

    def setUp(self):   # these tests are about the one-call road, whatever the server.py switch says
        patcher = mock.patch.object(server, "ONE_CALL", True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_ai(self, sentence, tasks=(), **fields):
        """Ask with a fake AI that answers `fields` on top of a plain task. Returns (result, number of AI calls)."""
        calls = []

        def ai(prompt, *a, **k):
            calls.append(1)
            row = {**fake_ai(prompt), "intent": "add", "target": "", "change": "", "reply": "", "tokens": 7}
            row.update(fields)
            return row
        return ask(sentence, tasks, ai=ai), len(calls)

    def test_plain_task_is_one_call(self):
        r, n = self.run_ai("buy bread tomorrow", when="tomorrow", text="Buy bread")
        self.assertEqual((r["action"], r["text"], r["due"], n), ("add", "Buy bread", "2026-10-29T09:00", 1))

    def test_clear_questions_and_commands_need_no_ai(self):
        for text in ["what's due today", "done #2", "move #1 to friday", "hi max", "thanks"]:
            self.assertNotEqual(ask(text, TASKS, ai=no_ai)["action"], "add", text)

    def test_done_by_the_ais_target(self):
        r, n = self.run_ai("done with dentist", DENTIST, intent="done", target="dentist")
        self.assertEqual((r["action"], r["num"], n), ("complete", 4, 1))
        r, n = self.run_ai("I finished the slides", [{"num": 7, "text": "Finish the slides", "done": False}], intent="done", target="slides")
        self.assertEqual((r["action"], r["num"]), ("complete", 7))
        r, n = self.run_ai("ซื้อนมแล้ว", [{"num": 3, "text": "ซื้อนม", "done": False}], intent="done", target="ซื้อนม")
        self.assertEqual((r["action"], r["num"]), ("complete", 3))

    def test_no_command_word_means_no_delete_or_done(self):
        for sentence, intent in [("cancel dentist", "delete"), ("finish the report", "done"), ("dentist friday", "undo")]:
            r, n = self.run_ai(sentence, DENTIST, intent=intent, target="dentist")
            self.assertEqual((r["action"], n), ("add", 1), sentence)   # a plain task, the AI's idea is ignored

    def test_ai_target_must_be_a_real_task(self):
        r, n = self.run_ai("delete the unicorn task", DENTIST, intent="delete", target="unicorn")
        self.assertEqual((r["action"], r.get("missing"), n), ("delete", "unicorn", 1))
        r, n = self.run_ai("undo dentist", DENTIST, intent="undo", target="dentist")   # open task: undo only looks at done ones
        self.assertEqual((r["action"], r.get("missing")), ("uncomplete", "dentist"))

    def test_change_keeps_what_was_not_mentioned(self):
        r, n = self.run_ai("push the dentist to monday", DENTIST, intent="change", target="dentist", change="monday",
                           when="weekday", weekday="Monday")
        self.assertEqual((r["action"], r["num"], r["changes"], n), ("update", 4, {"due": "2026-11-02T16:30"}, 0))   # time stays 16:30; "push" is a command word: no AI

    def test_change_needs_a_change_word(self):
        r, n = self.run_ai("dentist monday", DENTIST, intent="change", target="dentist", change="monday", when="weekday", weekday="Monday")
        self.assertEqual(r["action"], "add")

    def test_chat_and_question_are_checked(self):
        r, n = self.run_ai("you did well", intent="chat", reply="Thanks! What can I do for you?")
        self.assertEqual((r["action"], r["reply"], n), ("smalltalk", "Thanks! What can I do for you?", 1))
        r, n = self.run_ai("คุณช่วยได้ดีมาก", intent="chat", reply="Thanks!")
        self.assertEqual(r["reply"], server.CHAT_FALLBACK["th"])   # a Thai sentence with an English reply: dropped
        r, n = self.run_ai("buy milk", intent="chat", reply="Hello!")
        self.assertEqual(r["action"], "add")   # a plain task can't be turned into small talk
        r, n = self.run_ai("buy milk", intent="question")
        self.assertEqual(r["action"], "add")
        r, n = self.run_ai("could there be something I should know on friday", TASKS, intent="question")
        self.assertEqual((r["action"], r["nums"]), ("answer", [1]))   # the filter is Python's own reading of the words

    def test_command_words_without_a_found_task_ask_the_ai(self):
        # rules: "dentist task" is not a title; the AI's target "dentist" is
        r, n = self.run_ai("delete the dentist task", DENTIST, intent="delete", target="dentist")
        self.assertEqual((r["action"], r["num"], n), ("delete", 4, 1))
        # the AI sees no command and there is no #number: it is a new task ("Move car to garage"), not "can't find"
        r, n = self.run_ai("delete the unicorn task", DENTIST)
        self.assertEqual(r["action"], "add")
        r, n = self.run_ai("delete #99", DENTIST)   # a #number is exact: Python's "can't find #99" stays
        self.assertEqual((r["action"], r.get("missing")), ("delete", "#99"))

    def test_loose_find(self):
        tasks = [{"num": 1, "text": "Ask Ploy for Claude access"}, {"num": 2, "text": "Call mom"}, {"num": 3, "text": "Call dad"}]
        self.assertEqual(server.find_task_loose("ploy thing", tasks), (1, []))
        self.assertEqual(server.find_task_loose("the call", tasks)[0], None)   # two tasks have "call": no guess
        self.assertEqual(server.find_task_loose("unicorn", tasks), (None, []))

    def test_afternoon_is_not_noon(self):
        self.assertEqual(ask("call grandma on friday afternoon")["due"], "2026-10-30T13:00")

    def test_old_road_is_still_there(self):
        with mock.patch.object(server, "ONE_CALL", False):
            self.assertEqual(ask("buy milk tomorrow")["action"], "add")
            self.assertEqual(ask("done #2", TASKS, ai=no_ai)["action"], "complete")


class NextWeekdayOnThatWeekday(unittest.TestCase):
    """Owner bug 30 Oct (a Friday): "what to do next friday" answered for today. "next X" is never today."""
    FRIDAY = datetime(2026, 10, 30, 10, 0)

    def date(self, text):
        return server.question_filter(text, self.FRIDAY, [])["date"]

    def test_next_friday_is_seven_days_on(self):
        for text in ["what to do next friday", "what's due next friday?", "งานวันศุกร์หน้ามีอะไรบ้าง", "ศุกร์หน้ามีอะไร"]:
            self.assertEqual(self.date(text), "2026-11-06", text)

    def test_plain_friday_on_a_friday_is_today(self):
        self.assertEqual(self.date("what to do friday"), "2026-10-30")
        self.assertEqual(self.date("งานวันศุกร์มีอะไรบ้าง"), "2026-10-30")

    def test_other_days_and_sunday(self):
        self.assertEqual(self.date("what do i have on next monday"), "2026-11-02")
        self.assertEqual(self.date("วันอาทิตย์หน้ามีอะไร"), "2026-11-01")   # first Sunday after Friday 30 Oct

    def test_next_week_is_not_a_weekday(self):
        f = server.question_filter("what is due next week", self.FRIDAY, [])
        self.assertEqual((f["when"], f["date"]), ("nextweek", ""))
        self.assertEqual(server.question_filter("อาทิตย์หน้ามีอะไรบ้าง", self.FRIDAY, [])["when"], "nextweek")

    def test_adding_next_friday_on_a_friday(self):
        with mock.patch.object(server, "parse_with_ollama", fake_ai), default_memory():
            for text in ["call the bank next friday", "ส่งรายงานวันศุกร์หน้า"]:
                r = server.run_command(text, "2026-10-30T10:00", [], [])
                self.assertEqual(r["due"], "2026-11-06T09:00", text)


class NextVersusThisWeekday(unittest.TestCase):
    """Owner rule 30 Oct: "friday" / "this friday" = nearest on or after today; "next friday" = first one strictly after today."""
    NOWS = {"Mon": datetime(2026, 11, 2, 10, 0), "Wed": datetime(2026, 10, 28, 10, 0),
            "Fri": datetime(2026, 10, 30, 10, 0), "Sun": datetime(2026, 11, 1, 10, 0)}

    def test_every_weekday_on_four_days(self):
        for label, now in self.NOWS.items():
            today = now.date()
            for i, name in enumerate(server.WEEKDAYS):
                gap = (i - today.weekday()) % 7
                self.assertEqual(server.weekday_date(name, today), today + timedelta(days=gap), (label, name))
                self.assertEqual(server.weekday_date(name, today, after=True), today + timedelta(days=gap or 7), (label, name))
                low = "what is on next " + name.lower()
                self.assertEqual(server.next_weekday_named(low, today), (today + timedelta(days=gap or 7)).isoformat(), (label, name))

    def test_monday_next_friday_is_this_weeks(self):
        task = {"when": "weekday", "weekday": "Friday", "next_week": True}
        self.assertEqual(server.resolve_due(task, self.NOWS["Mon"]), "2026-11-06T09:00")
        self.assertEqual(server.resolve_due(task, self.NOWS["Fri"]), "2026-11-06T09:00")   # Friday: +7


class SpecialDays(unittest.TestCase):
    """this weekend / in N weeks / end of month / start of next month (Python reads them; Fri 30 Oct 2026)."""
    NOW = datetime(2026, 10, 30, 10, 0)

    def due(self, text, now=None):
        task = server.rules_date(text, server.DEFAULT_TIMES)
        self.assertIsNotNone(task, text)
        return server.resolve_due(task, now or self.NOW, server.DEFAULT_TIMES)

    def test_phrases(self):
        self.assertEqual(self.due("gym this weekend"), "2026-10-31T09:00")
        self.assertEqual(self.due("gym this weekend", datetime(2026, 11, 1, 10, 0)), "2026-11-01T09:00")   # Sunday: today
        self.assertEqual(self.due("pay in 2 weeks"), "2026-11-13T09:00")
        self.assertEqual(self.due("pay in a week"), "2026-11-06T09:00")
        self.assertEqual(self.due("send report end of month"), "2026-10-31T09:00")
        self.assertEqual(self.due("rent start of next month"), "2026-11-01T09:00")
        self.assertEqual(self.due("ส่งงาน สิ้นเดือน"), "2026-10-31T09:00")
        self.assertEqual(self.due("ส่งงาน สุดสัปดาห์"), "2026-10-31T09:00")
        self.assertEqual(self.due("ส่งงาน อีก 2 สัปดาห์"), "2026-11-13T09:00")
        self.assertEqual(self.due("ส่งงาน ต้นเดือนหน้า"), "2026-11-01T09:00")

    def test_check_task_keeps_them(self):
        """check_task used to blank any date whose words DAY_HINTS did not know."""
        for text, due in [("gym this weekend", "2026-10-31T09:00"), ("meet Tom in 2 weeks", "2026-11-13T09:00")]:
            r = server.check_task({"text": text, "when": "none"}, text, "2026-10-30T10:00", [], {"times": server.DEFAULT_TIMES})
            self.assertEqual(r["due"], due, text)

    def test_titles(self):
        self.assertEqual(" ".join(server.own_words("gym this weekend")), "gym")
        self.assertEqual(" ".join(server.own_words("pay rent on the 5th")), "pay rent")

    def test_question_day_after_tomorrow_and_in_days(self):
        f = server.question_filter("what's the day after tomorrow", self.NOW, [])
        self.assertEqual((f["when"], f["date"]), ("date", "2026-11-01"))
        f = server.question_filter("what do i have in 3 days", self.NOW, [])
        self.assertEqual((f["when"], f["date"]), ("date", "2026-11-02"))
        f = server.question_filter("what do i have this weekend", self.NOW, [])
        self.assertEqual(server.due_range(f, self.NOW), ("2026-10-31", "2026-11-01"))

    def test_unreadable_day_is_said(self):
        for text in ["what is due next month", "what did I finish yesterday", "อะไรบ้างเดือนนี้"]:
            r = server.question_answer(text, "2026-10-30T10:00", [], [], use_ai=False)
            self.assertEqual(r["kind"], "chat", text)
        r = server.question_answer("what to do next", "2026-10-30T10:00", [], [], use_ai=False)
        self.assertTrue(r is None or r["action"] == "answer")


class ClockPhrases(unittest.TestCase):
    """English clock phrases without am/pm, Thai ทุ่ม, "14.30 น." and the vague-time defaults (owner, 30 Oct)."""

    def test_english_phrases(self):
        for text, want in [("tomorrow at 7 in the morning", "07:00"), ("at 3 in the afternoon", "15:00"),
                           ("friday morning 8", "08:00"), ("tomorrow midnight", "00:00"), ("tomorrow at 5", "17:00"),
                           ("friday at 9", "09:00"), ("noon", "12:00"), ("8 at night", "20:00"), ("at 5th street", "")]:
            self.assertEqual(server.english_time(text), want, text)

    def test_thai_toom_and_dot_time(self):
        self.assertEqual(server.thai_time("นัดหมอ พรุ่งนี้ ทุ่มครึ่ง"), "19:30")
        self.assertEqual(server.thai_time("นัดหมอ ตอนทุ่ม"), "19:00")
        self.assertEqual(server.thai_time("สองทุ่ม"), "20:00")
        self.assertEqual(server.english_time("นัดหมอ พรุ่งนี้ 14.30 น."), "14:30")

    def test_vague_defaults(self):
        t = server.DEFAULT_TIMES
        self.assertEqual((t["morning"], t["afternoon"], t["evening"], t["tonight"]), ("09:00", "13:00", "18:00", "20:00"))
        task = server.rules_date("call bank tomorrow evening", t)
        self.assertEqual(task["time"], "18:00")
        self.assertEqual(server.rules_date("call bank friday night", t)["time"], "20:00")

    def test_rules_date_reads_them(self):
        t = server.DEFAULT_TIMES
        self.assertEqual(server.rules_date("tomorrow at 7 in the morning", t)["time"], "07:00")
        self.assertEqual(server.rules_date("tomorrow 14.30 น.", t)["time"], "14:30")
        self.assertEqual(server.rules_date("พรุ่งนี้ ทุ่มครึ่ง", t)["time"], "19:30")

    def test_titles_lose_the_time(self):
        fix = server.fix_date_typos
        self.assertEqual(" ".join(server.own_words(fix("นัดหมอ พรุ่งนี้ ทุ่มครึ่ง"))), "นัดหมอ")


class CommandForms(unittest.TestCase):
    """#N spoken other ways, push/delay/cancel, and command words that must not take over a new task."""
    TASKS = [{"num": 3, "text": "Call bank", "done": False, "due": "2026-11-02T09:00"},
             {"num": 4, "text": "Buy milk", "done": False, "due": ""}]

    def test_number_forms(self):
        for text, action in [("ข้อ 3 เสร็จ", "complete"), ("งานที่ 3 เสร็จแล้ว", "complete"), ("เสร็จข้อ 3", "complete"),
                             ("no. 3 done", "complete"), ("number 3 done", "complete"), ("done no 3", "complete"),
                             ("ลบข้อ 3", "delete"), ("ลบงานที่ 3", "delete"), ("delete no. 3", "delete"),
                             ("cancel #3", "delete"), ("get rid of #3", "delete")]:
            r = server.command_by_rules(text, "2026-10-30T10:00", [], self.TASKS)
            self.assertEqual((r["action"], r["num"]), (action, 3), text)

    def test_push_and_delay(self):
        r = server.command_by_rules("push #3 to monday", "2026-10-30T10:00", [], self.TASKS)
        self.assertEqual((r["action"], r["num"], r["changes"]), ("update", 3, {"due": "2026-11-02T09:00"}))
        r = server.command_by_rules("เลื่อนข้อ 3 ไปพรุ่งนี้", "2026-10-30T10:00", [], self.TASKS)
        self.assertEqual((r["action"], r["num"], r["changes"]), ("update", 3, {"due": "2026-10-31T09:00"}))

    def test_plain_words_stay_tasks(self):
        for text in ["push the button", "delay flight", "set up the printer", "Mark's birthday gift friday", "cancel dentist"]:
            self.assertIsNone(server.command_by_rules(text, "2026-10-30T10:00", [], self.TASKS), text)

    def test_unmatched_command_word_becomes_a_task(self):
        """The AI sees an ordinary task: Python no longer answers "can't find task" (only for a #number)."""
        r = ask("Move car to garage", self.TASKS)
        self.assertEqual((r["action"], r["text"]), ("add", "Move car to garage"))
        self.assertEqual(ask("done #99", self.TASKS)["missing"], "#99")

    def test_how_many_done_is_a_question(self):
        r = ask("how many done", self.TASKS, ai=no_ai)
        self.assertEqual((r["action"], r["filter"]["status"]), ("answer", "done"))


class Job6FixRound(unittest.TestCase):
    """Bono's full test (31 Oct): greetings, a loose task match, Thai leftovers, delay by N days, empty chat replies."""
    RENT = [{"num": 13, "text": "Rent car return", "done": False, "due": ""},
            {"num": 4, "text": "Dentist appointment", "done": False, "due": "2026-11-02T16:30"},
            {"num": 3, "text": "Pay rent", "done": False, "due": ""}]

    def test_time_of_day_greetings(self):
        for text in ["good morning", "Good morning Max", "good evening max", "good afternoon", "morning max", "อรุณสวัสดิ์",
                     "อรุณสวัสดิ์ครับ แม็กซ์"]:
            self.assertEqual(ask(text, ai=no_ai)["action"], "greeting", text)
        r = ask("good morning max, buy eggs")
        self.assertEqual((r["action"], r["text"]), ("add", "Buy eggs"))

    def test_morning_alone_is_not_a_greeting(self):
        self.assertEqual(ask("morning run tomorrow")["action"], "add")

    def test_one_shared_word_is_not_a_match(self):
        for text in ["Move car to garage", "change car to garage", "move car to the garage"]:
            self.assertIsNone(server.command_by_rules(text, NOW_TEXT, [], self.RENT), text)
        r = ask("Move car to garage", self.RENT)
        self.assertEqual((r["action"], r["text"]), ("add", "Move car to garage"))

    def test_a_clear_match_still_works(self):
        r = server.command_by_rules("move dentist appointment to friday", NOW_TEXT, [], self.RENT)
        self.assertEqual((r["num"], r["changes"]["due"][:10]), (4, "2026-10-30"))
        r = server.command_by_rules("move car to friday", NOW_TEXT, [], self.RENT)   # a date: one word is enough
        self.assertEqual(r["num"], 13)

    def test_an_update_that_changes_nothing_becomes_a_task(self):
        self.assertIsNone(server.command_by_rules("move dentist appointment to the bank", NOW_TEXT, [], self.RENT))
        self.assertTrue(server.command_by_rules("move #4 to", NOW_TEXT, [], self.RENT)["nothing"])   # a #number stays exact

    def test_thai_linking_words_leave_with_the_date(self):
        for text, want in [("ซื้อนมพรุ่งนี้ตอน 2 ทุ่ม", "ซื้อนม"), ("โทรหาแม่ตอน 3 โมงเย็นวันพฤหัส", "โทรหาแม่"),
                           ("งานเลี้ยงสุดสัปดาห์นี้", "งานเลี้ยง"), ("ล้างของในตู้เย็นพรุ่งนี้", "ล้างของในตู้เย็น")]:
            self.assertEqual(ask(text)["text"], want, text)

    def test_delay_and_push_by_n_days(self):
        for text in ["delay #4 by 2 days", "push #4 by 2 days", "postpone #4 by 2 days", "เลื่อนข้อ 4 อีก 2 วัน"]:
            r = server.command_by_rules(text, NOW_TEXT, [], self.RENT)
            self.assertEqual((r["num"], r["changes"]), (4, {"due": "2026-11-04T16:30"}), text)
        r = server.command_by_rules("push #3 by a week", NOW_TEXT, [], self.RENT)   # no date yet: counted from today
        self.assertEqual(r["changes"], {"due": "2026-11-04T09:00"})
        r = server.command_by_rules("delay dentist appointment by 3 days", NOW_TEXT, [], self.RENT)
        self.assertEqual((r["num"], r["changes"]), (4, {"due": "2026-11-05T16:30"}))

    def test_empty_or_wrong_chat_reply_gets_a_friendly_line(self):
        self.assertEqual(server.chat_reply("", "tell me a joke"), server.CHAT_FALLBACK["en"])
        self.assertEqual(server.chat_reply("", "คุณเป็นยังไงบ้าง"), server.CHAT_FALLBACK["th"])
        self.assertEqual(server.chat_reply("You are welcome!", "how are you"), server.CHAT_FALLBACK["en"])
        self.assertEqual(server.chat_reply("You're welcome!", "thanks a lot"), "You're welcome!")
        self.assertEqual(server.chat_reply("I am fine, thanks!", "how are you"), "I am fine, thanks!")
        self.assertEqual(server.chat_reply("Fine thanks!", "คุณเป็นยังไงบ้าง"), server.CHAT_FALLBACK["th"])   # English for Thai
