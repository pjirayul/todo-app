"""Automatic tests for Max's pure-Python logic in server.py.

Run from the app folder:   python -m unittest
No AI, no Ollama, no server and no real data are used:
- the AI call (parse_with_ollama) is replaced by a tiny fake,
- About me (load_memory) is replaced by the default times,
- "now" is frozen to Wednesday 28 Oct 2026, 10:00, so the tests never depend on today's date.
"""
import pathlib
import re
import unittest
from datetime import datetime
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


def default_memory():
    return mock.patch.object(server, "load_memory", return_value=server.clean_memory({}))


def ask(sentence, tasks=(), chosen=None, ai=fake_ai):
    """Run the command bar logic with the fake AI and the default About me."""
    with mock.patch.object(server, "parse_with_ollama", ai), default_memory(), \
         mock.patch.object(server, "AI_PROVIDER", "ollama"):
        return server.run_command(sentence, NOW_TEXT, [], list(tasks), chosen)


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
        # Same weekday as today (Wednesday) means next week, not today
        self.assertEqual(self.due(when="weekday", weekday="Wednesday"), "2026-11-04T09:00")
        # A weekday already past this week -> next week's
        self.assertEqual(self.due(when="weekday", weekday="Monday"), "2026-11-02T09:00")

    def test_next_week_weekday(self):
        self.assertEqual(self.due(when="weekday", weekday="Friday", next_week=True), "2026-11-06T09:00")

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
        self.assertEqual(ask("ประชุมวันศุกร์หน้า")["due"], "2026-11-06T09:00")

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
        r = ask("delete zebra", TASKS)
        self.assertEqual((r["action"], r["missing"], r["choices"]), ("delete", "zebra", []))

    def test_unknown_number_reports_missing(self):
        self.assertEqual(ask("done #77", TASKS)["missing"], "#77")

    def test_ambiguous_match_gives_choices(self):
        r = ask("delete call", CALLS)
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
        self.assertEqual(server.pick_category("Shopping", "gym", []), "Shopping")
        self.assertEqual(server.pick_category("Work", "team meeting", []), "Work")
        self.assertEqual(server.pick_category("Work", "gym", []), "Health")      # the AI over-uses Work
        self.assertEqual(server.pick_category("Personal", "something", []), "Personal")  # no hint: kept
        self.assertEqual(server.pick_category("health", "x", []), "Health")
        self.assertEqual(server.pick_category("Family", "gym", ["Family"]), "Family")  # the owner's own

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
