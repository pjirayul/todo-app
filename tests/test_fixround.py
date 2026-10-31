"""Tests for the 31 Oct fix round: add_many titles, "Add as new task" after Tell Max more, join_pending, short replies, body cap."""
import http.client
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from unittest import mock

import server
from tests.test_max import DENTIST
from tests.test_tellmore import parts_ai, run


class CleanTitles(unittest.TestCase):
    def test_add_many_titles_lose_date_words_but_keep_dates(self):
        r = run("buy milk tomorrow and call mom at 7pm", ai=parts_ai(["buy milk tomorrow", "call mom at 7pm"]))
        tasks = r["options"][0]["do"]["tasks"]
        self.assertEqual([t["text"] for t in tasks], ["Buy milk", "Call mom"])
        self.assertEqual(tasks[0]["due"][:10], "2026-10-29")
        self.assertTrue(tasks[1]["due"].endswith("T19:00"))

    def test_clean_title(self):
        for raw, want in [("remind me to call bob on friday", "Call bob"), ("add pay rent", "Pay rent"),
                          ("it is a new appointment tomorrow at 5pm", "It is a new appointment"), ("tomorrow", "Tomorrow")]:
            self.assertEqual(server.clean_title(raw), want, raw)

    def test_add_after_tell_more_uses_only_the_new_words(self):
        r = run("it is a new appointment tomorrow at 5pm", DENTIST, earlier="cancel dentist")
        adds = [o["do"] for o in r.get("options", []) if o["label"] == "opt_add"]
        for do in adds:
            self.assertEqual(do["text"], "It is a new appointment")


class JoinNewTask(unittest.TestCase):
    def test_new_task_phrases_are_not_joined(self):
        for text in ["remind me to call bob", "add milk", "please remind me to pay rent", "เตือนให้โทรหาแม่"]:
            self.assertEqual(server.join_pending(text, "cancel dentist", 5, []), (text, False), text)

    def test_a_real_followup_is_still_joined(self):
        task = {"num": 1, "text": "Dentist appointment", "done": False}   # shares "appointment": long text still needs a link
        self.assertTrue(server.join_pending("it is a new appointment tomorrow at 5pm", "cancel dentist", 5, [task])[1])


class ShortReplies(unittest.TestCase):
    def test_short_text_cuts_at_a_word(self):
        self.assertEqual(server.short_text("short", 80), "short")
        out = server.short_text("Typos are now handled (lundry -> Do laundry) and more words here", 40)
        self.assertTrue(out.endswith("...") and len(out) <= 43)
        self.assertNotIn("(", out[-6:])
        self.assertFalse(out[:-3].endswith(" "))
        self.assertEqual(server.short_text("a" * 100, 10), "a" * 10 + "...")


class BodyCap(unittest.TestCase):
    def test_parse_refuses_a_huge_body(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(server.Handler, directory="."))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_port)
            origin = sorted(server.ALLOWED_ORIGINS)[0]
            conn.request("POST", "/api/parse", body=b"x" * 3_000_000,
                         headers={"Origin": origin, "Content-Type": "application/json", "Host": origin.split("//")[1]})
            self.assertEqual(conn.getresponse().status, 413)
        finally:
            srv.shutdown()
            srv.server_close()


if __name__ == "__main__":
    unittest.main()
