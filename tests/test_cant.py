"""Tests for #16: the "I can't do that yet. Add it as a task?" card. Fake AI only (the real small model rarely says
"cant"; the exam measures that). Python's part: when a cant is accepted, and what the card's button adds."""
import unittest

from tests.test_max import fake_ai
from tests.test_tellmore import run


def cant_ai(reply="Sorry, I can't do that."):
    """A fake AI that says: this is something Max cannot do."""
    def ai(prompt, *a, **k):
        return {**fake_ai(prompt), "intent": "cant", "target": "", "change": "", "reply": reply}
    return ai


class CantCard(unittest.TestCase):
    def test_cant_gives_a_card_with_one_add_button(self):
        r = run("send an email to my boss", ai=cant_ai())
        self.assertEqual((r["action"], r["case"], r["q"]), ("clarify", "cant", "clarifyQ_cant"))
        self.assertEqual([o["label"] for o in r["options"]], ["opt_cantadd"])
        self.assertEqual(r["options"][0]["do"]["action"], "add")   # the button is a normal add, nothing else is saved
        self.assertFalse(r["more"])

    def test_the_add_button_keeps_the_owners_words(self):
        r = run("play some music for me tomorrow", ai=cant_ai())
        do = r["options"][0]["do"]
        self.assertEqual(do["action"], "add")
        self.assertTrue(do["due"].startswith("2026-"))   # Python still reads the day

    def test_thai_works_the_same(self):
        r = run("ส่งอีเมลหาเจ้านาย", ai=cant_ai("ขอโทษครับ ทำไม่ได้"))
        self.assertEqual((r["action"], r["case"]), ("clarify", "cant"))

    def test_cant_without_a_reply_is_a_plain_task(self):
        self.assertEqual(run("send an email to my boss", ai=cant_ai(""))["action"], "add")

    def test_a_number_or_command_word_is_never_cant(self):
        self.assertNotEqual(run("send #3 to my boss", ai=cant_ai()).get("case"), "cant")
        self.assertNotEqual(run("delete the email", ai=cant_ai()).get("case"), "cant")

    def test_plain_add_never_gets_the_card(self):
        self.assertEqual(run("buy milk tomorrow")["action"], "add")   # the default fake AI says add

    def test_the_card_text_exists_in_both_languages(self):
        with open("script.js", encoding="utf-8") as f:
            js = f.read()
        self.assertEqual(js.count("clarifyQ_cant:"), 2)
        self.assertEqual(js.count("opt_cantadd:"), 2)

    def test_click_is_logged_as_add(self):
        import server
        self.assertEqual(server.pick_kind("opt_cantadd"), "add")
        self.assertEqual(server.auto_flag("cant"), {})   # never switches to auto


if __name__ == "__main__":
    unittest.main()
