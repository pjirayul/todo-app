"""Tests for the can't-do fixes, batch 1 (owner decisions #18 clean titles, #19 vague dates, #20 task questions).
Fake AI only, frozen "now" (Wednesday 28 Oct 2026): the AI says what the real 3B model says, Python must fix it."""
import unittest

import server
from tests.test_max import ask, fake_ai


def ai_says_task(text, **fields):
    """A fake AI that answers with this title and these date fields (like the small model does)."""
    def ai(prompt, *a, **k):
        return {**fake_ai(prompt), "text": text, **fields}
    return ai


def date_guess(text, day, month=0, next_month=False):
    """The AI made up 'a date' (the 3B model does this for 'next month' or 'before March')."""
    return ai_says_task(text, when="date", day=day, month=month, next_month=next_month)


class CleanTitles(unittest.TestCase):
    def test_amount_is_kept(self):
        r = ask("Pay rent on the 1st of every month, it is 12000 baht", ai=ai_says_task("Pay rent"))
        self.assertEqual(r["text"], "Pay rent 12000 baht")
        self.assertEqual((r["repeat"], r["due"][:10]), ("month", "2026-11-01"))

    def test_thai_amount_is_kept(self):
        self.assertEqual(ask("จ่ายค่าเช่า 12000 บาท", ai=ai_says_task("จ่ายค่าเช่า"))["text"], "จ่ายค่าเช่า 12000 บาท")

    def test_phone_number_is_kept(self):
        self.assertIn("0812345678", ask("Call 0812345678 tomorrow", ai=ai_says_task("Call"))["text"])

    def test_small_numbers_are_not_amounts(self):
        self.assertEqual(ask("pay rent 5th", ai=ai_says_task("Pay rent"))["text"], "Pay rent")
        self.assertEqual(ask("Dentist 20 November 2026", ai=ai_says_task("Dentist"))["text"], "Dentist")   # a year is not money

    def test_amount_already_in_title_is_not_doubled(self):
        self.assertEqual(ask("pay 1,500 baht to Tom", ai=ai_says_task("Pay 1500 baht to Tom"))["text"], "Pay 1500 baht to Tom")

    def test_weekly_stays_in_the_middle_of_a_title(self):
        self.assertEqual(ask("Do the weekly report", ai=ai_says_task("Do the weekly report"))["text"], "Do the weekly report")
        self.assertEqual(ask("Do the weekly report every friday", ai=ai_says_task("Do the weekly report every friday"))["text"],
                         "Do the weekly report")

    def test_weekly_at_the_end_is_the_repeat(self):
        r = ask("Water plants daily", ai=ai_says_task("Water plants daily"))
        self.assertEqual((r["text"], r["repeat"]), ("Water plants", "day"))

    def test_weekly_is_not_turned_into_week_by_the_typo_fixer(self):
        self.assertIn("weekly", server.fix_date_typos("do the weekly report"))

    def test_trailing_at_hour_goes_when_the_time_was_read(self):
        r = ask("Take vitamins every morning at 7", ai=ai_says_task("Take vitamins at 7"))
        self.assertEqual((r["text"], r["repeat"], r["due"][11:]), ("Take vitamins", "day", "07:00"))
        self.assertEqual(ask("Meeting notes at 3pm", ai=ai_says_task("Meeting notes at 3pm"))["text"], "Meeting notes")

    def test_a_number_in_the_title_is_not_a_time(self):
        self.assertEqual(ask("Buy 2 tickets", ai=ai_says_task("Buy 2 tickets"))["text"], "Buy 2 tickets")

    def test_thai_before_word_goes_with_the_date(self):
        self.assertEqual(ask("ส่งงานก่อนวันศุกร์", ai=ai_says_task("ส่งงานก่อนวันศุกร์"))["text"], "ส่งงาน")

    def test_thai_end_of_next_month_title_and_date(self):
        r = ask("ต่อภาษีรถก่อนสิ้นเดือนหน้า", ai=ai_says_task("ต่อภาษีรถก่อนสิ้นเดือนหน้า"))
        self.assertEqual((r["text"], r["due"][:10]), ("ต่อภาษีรถ", "2026-11-30"))

    def test_punctuation_is_not_an_own_word(self):
        self.assertNotIn(",", server.own_words("pay rent , please"))


class Months(unittest.TestCase):
    def test_month_table_reads_english_and_thai(self):
        for text, want in [("5 dec", (5, 12)), ("20th of November", (20, 11)), ("december 5", (5, 12)), ("5 ธันวาคม", (5, 12)),
                           ("12 พ.ย.", (12, 11)), ("3 ม.ค.", (3, 1)), ("1 may", (1, 5)), ("march 3", (3, 3)),
                           ("I may call tom", (0, 0)), ("before march", (0, 0)), ("nov 5pm", (0, 0)), ("5 sept", (5, 9))]:
            self.assertEqual(server.month_day(text), want, text)

    def test_thai_month_day_has_a_date(self):
        r = ask("จ่ายค่าประกัน 5 ธันวาคม", ai=ai_says_task("จ่ายค่าประกัน", when="none"))
        self.assertEqual((r["text"], r["due"]), ("จ่ายค่าประกัน", "2026-12-05T09:00"))

    def test_python_month_beats_the_ai_month(self):
        r = ask("dentist 5 dec", ai=date_guess("Dentist", 5, 11))
        self.assertEqual(r["due"], "2026-12-05T09:00")

    def test_bare_may_is_not_a_month(self):
        r = ask("I may call Tom friday", ai=date_guess("Call Tom", 1, 5))
        self.assertEqual(r["due"], "2026-10-30T09:00")   # Friday, not 1 May
        self.assertNotIn("askWhen", r)

    def test_bare_march_is_not_a_date_hint(self):
        self.assertFalse(server.DAY_HINTS.search("march in the park"))
        self.assertTrue(server.DAY_HINTS.search("pay on march 3"))

    def test_before_march_has_no_invented_day(self):
        r = ask("Renew passport before March", ai=date_guess("Renew passport", 1, 12))
        self.assertEqual(r["due"], "")

    def test_ai_date_with_no_day_number_asks_when(self):
        r = ask("Book dentist next month", ai=date_guess("Book dentist", 30, 11, True))
        self.assertEqual((r["due"], r.get("askWhen")), ("", True))
        r = ask("ไปตรวจสุขภาพประจำปีเดือนธันวาคม", ai=date_guess("ไปตรวจสุขภาพประจำปี", 1, 12))
        self.assertEqual((r["due"], r.get("askWhen"), r["text"]), ("", True, "ไปตรวจสุขภาพประจำปี"))

    def test_ai_in_days_with_no_number_typed_asks_when(self):
        r = ask("Book dentist next month", ai=ai_says_task("Book dentist", when="in_days", in_days=30))
        self.assertEqual((r["due"], r.get("askWhen")), ("", True))

    def test_counted_in_words_is_not_a_guess(self):
        for text in ["call mom in a week", "call mom in two weeks"]:
            r = ask(text, ai=ai_says_task("Call mom", when="in_days", in_days=7))
            self.assertTrue(r["due"], text)
            self.assertNotIn("askWhen", r)

    def test_a_clock_time_is_not_a_day_number(self):
        r = ask("Book dentist next month at 3pm", ai=date_guess("Book dentist", 30, 11, True))
        self.assertEqual((r["due"], r.get("askWhen")), ("", True))

    def test_typed_day_number_keeps_the_ai_date(self):
        r = ask("pay rent on the 5th", ai=date_guess("Pay rent", 5))
        self.assertEqual(r["due"], "2026-11-05T09:00")
        self.assertNotIn("askWhen", r)

    def test_plain_add_never_asks_when(self):
        r = ask("Buy milk", ai=ai_says_task("Buy milk"))
        self.assertNotIn("askWhen", r)
        self.assertEqual(r["due"], "")

    def test_end_of_next_month(self):
        for text in ["pay tax end of next month", "ต่อภาษีสิ้นเดือนหน้า", "ปลายเดือนหน้าจ่ายค่าไฟ"]:
            self.assertEqual(server.special_day(text), {"when": "special", "special": "month_end_next"}, text)
        self.assertEqual(server.special_day("end of month")["special"], "month_end")   # plain "end of month" is unchanged
        self.assertEqual(ask("pay tax end of next month", ai=ai_says_task("Pay tax"))["due"], "2026-11-30T09:00")


TASKS12 = [{"num": n, "text": f"Task {n}", "done": n == 3, "due": "", "priority": "high" if n == 12 else "med", "cat": "Work"}
           for n in range(1, 13)]


class TaskQuestions(unittest.TestCase):
    def test_task_number_question_lists_just_that_task(self):
        r = ask("What is task 12?", TASKS12)
        self.assertEqual((r["action"], r["nums"], r["filter"].get("num")), ("answer", [12], 12))

    def test_task_number_works_for_a_done_task(self):
        self.assertEqual(ask("what is task 3?", TASKS12)["nums"], [3])

    def test_hash_number_stays_a_command(self):
        self.assertNotEqual(ask("what is #3?", TASKS12).get("action"), "answer")

    def test_thai_which_task_is_a_question(self):
        r = ask("งานไหนสำคัญที่สุดตอนนี้", TASKS12)
        self.assertEqual((r["action"], r["filter"]["priority"], r["nums"]), ("answer", "high", [12]))

    def test_finished_yesterday_gets_an_honest_answer(self):
        for text, thai in [("What did I finish yesterday?", False), ("เมื่อวานทำอะไรเสร็จ", True)]:
            r = ask(text, TASKS12)
            self.assertEqual(r["action"], "smalltalk", text)
            self.assertNotIn("couldn't read", r["reply"])
            self.assertEqual(bool(server.THAI_LETTERS.search(r["reply"])), thai, text)

    def test_unreadable_day_still_says_so(self):
        self.assertIn("couldn't read", ask("what is due last month?", TASKS12)["reply"])


if __name__ == "__main__":
    unittest.main()
