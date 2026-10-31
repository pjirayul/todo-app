"""Job 0h-2: open task titles in the prompt, and the two check-only switches."""
import sys
import unittest

sys.argv = sys.argv[:1]
import server  # noqa: E402


class OpenTitles(unittest.TestCase):
    def test_newest_open_only_and_trimmed(self):
        tasks = [{"num": n, "text": f"Task {n}", "done": n == 5} for n in range(1, 16)]
        tasks.append({"num": 20, "text": "x" * 100, "done": False})
        titles = server.open_titles(tasks).split("; ")
        self.assertEqual(len(titles), 10)
        self.assertEqual(titles[0], "x" * server.CONTEXT_TITLE_CHARS)   # newest first, trimmed
        self.assertNotIn("Task 5", titles)                              # done tasks stay out
        self.assertLessEqual(len("; ".join(titles)), server.CONTEXT_MAX_CHARS)

    def test_empty(self):
        self.assertEqual(server.open_titles([]), "")
        self.assertEqual(server.open_titles(None), "")

    def test_prompt_has_list_only_when_given(self):
        tasks = [{"num": 1, "text": "Call mom", "done": False}]
        with_list, _, _ = server.ai_prompt("done call mom", [], tasks=tasks)
        without, _, _ = server.ai_prompt("done call mom", [])
        self.assertIn("\nOpen tasks: Call mom\n", with_list)
        self.assertNotIn("Open tasks", without)


class OwnWordsCheckOnly(unittest.TestCase):
    def test_one_lost_word_keeps_ai_title(self):
        old = server.OWN_WORDS_CHECK_ONLY
        try:
            server.OWN_WORDS_CHECK_ONLY = True
            self.assertEqual(server.keep_own_words("Take vitamins", "take vitamins every morning"), "Take vitamins")
            # "every morning" is a repeat (job 7), not title words: only "vitamins" is lost, 1 of 3 words
            self.assertEqual(server.keep_own_words("Take", "take vitamins every morning please"), "Take")
            server.OWN_WORDS_CHECK_ONLY = False
            self.assertEqual(server.keep_own_words("Take", "take vitamins every morning"), "take vitamins")
        finally:
            server.OWN_WORDS_CHECK_ONLY = old


if __name__ == "__main__":
    unittest.main()
