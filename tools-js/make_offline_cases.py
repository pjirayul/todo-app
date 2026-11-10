"""Writes .claude/docs/offline-rules-cases.json: the sentences max-offline.js must answer like Python does.

Run from the app folder:   python tools-js/make_offline_cases.py
It only READS server.py (imports it; no AI, no Ollama, no server, no real data, About me = default times).
Every expected answer comes from Python's own functions - nothing is typed in by hand:
- commands + questions: server.run_command() (the "rules" road, no AI)
- a new task with a day/time: the same steps Python uses for a plain add without the AI
  (server.several_card): clean_sentence -> check_task -> clean_title
- "null" cases: sentences JS leaves alone (script.js then uses its old fallback). The Python answer is stored
  next to them as "python", so you can see what the server would do with it.
"""
import json
import pathlib
import re
import sys
from unittest import mock

APP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
import server  # noqa: E402

NOW_TEXT = "2026-10-28T10:00"   # a Wednesday, same fixed "today" as tests/test_max.py
TASKS = [
    {"num": 1, "text": "Do laundry", "done": False, "due": "2026-10-30T09:00", "priority": "med", "cat": "Home"},
    {"num": 2, "text": "Call mom", "done": False, "due": "2026-10-28T18:00", "priority": "med", "cat": "Personal"},
    {"num": 3, "text": "Dentist appointment", "done": False, "due": "2026-10-29T14:00", "priority": "high", "cat": "Health"},
    {"num": 4, "text": "Pay rent", "done": False, "due": "2026-10-25T09:00", "priority": "high", "cat": "Home"},
    {"num": 5, "text": "Buy milk", "done": True, "due": "2026-10-28T08:00", "priority": "med", "cat": "Shopping"},
    {"num": 6, "text": "Write report", "done": False, "due": "", "priority": "med", "cat": "Work"},
    {"num": 7, "text": "Send invoice", "done": True, "due": "2026-10-27T09:00", "priority": "low", "cat": "Money"},
    {"num": 8, "text": "Gym", "done": False, "due": "2026-10-31T07:00", "priority": "low", "cat": "Health"},
    {"num": 9, "text": "Team meeting", "done": False, "due": "2026-11-02T10:00", "priority": "med", "cat": "Work"},
    {"num": 10, "text": "Plan holiday", "done": True, "due": "2026-10-28T12:00", "priority": "med", "cat": "Personal"},
]
CATEGORIES = sorted({t["cat"] for t in TASKS})

# (kind, sentence, optional reason for "null")
CASES = [
    # --- new task with a day / time (English) ---
    ("add", "buy milk tomorrow 5pm"), ("add", "call mom tomorrow"), ("add", "Dentist friday 3pm"),
    ("add", "pay rent in 3 days"), ("add", "submit report on friday"), ("add", "gym tonight"),
    ("add", "call bank at 5pm"), ("add", "add water plants tomorrow morning"), ("add", "remind me to call dad next friday"),
    ("add", "send invoice this weekend"), ("add", "buy flowers tmrw 10am"),
("add", "pick up kids day after tomorrow 4:30pm"),
    ("add", "hey max buy eggs friday"), ("add", "lunch with Ann tomorow at 12:30"),
    # --- new task (Thai) ---
    ("add", "พรุ่งนี้ 9 โมง ซื้อนม"), ("add", "ซื้อนมพรุ่งนี้บ่ายสาม"), ("add", "โทรหาแม่วันศุกร์"),
    ("add", "จ่ายค่าเน็ตอีก 3 วัน"), ("add", "ประชุมทีมวันนี้ 2 ทุ่ม"), ("add", "ไปยิมคืนนี้"),
    # --- JS is not sure: null ---
    ("null", "buy milk", "no day or time: a plain task (script.js adds it as typed)"),
    ("null", "team offsite 5 december", "a month: only the AI reads it"),
    ("null", "finish slides in 2 weeks", "Python's own title cleaner leaves 'in 2 week' in the title: the AI would word it, JS is not sure"),
    ("null", "lunch with Ann tomorrow at noon", "'at noon' stays in Python's title: not sure"),
    ("null", "study for exam monday 7 in the morning", "'7 in the morning' stays in Python's title: not sure"),
    ("null", "gym every monday", "repeating task: not in the JS rules yet"),
    ("null", "buy milk and call mom tomorrow", "two tasks in one sentence: Python asks the AI to cut it"),
    ("null", "dentist next week", "an appointment with no weekday: Python offers Monday / Friday / no date"),
    ("null", "pay rent urgent friday", "priority word: the AI sets the priority"),
    # --- commands on one task ---
    ("cmd", "#1 done"), ("cmd", "done #2"), ("cmd", "#5 undo"), ("cmd", "undo #5"), ("cmd", "#3 delete"), ("cmd", "delete #4"),
    ("cmd", "move #1 to friday"), ("cmd", "move #2 to tomorrow 5pm"), ("cmd", "#6 tomorrow"), ("cmd", "reschedule #3 to 5pm"),
    ("cmd", "delay #1 by 2 days"), ("cmd", "done #99"), ("cmd", "ลบ #4"), ("cmd", "#2 เสร็จแล้ว"),
    ("cmd", "เลื่อน #1 เป็นวันศุกร์"), ("cmd", "done laundry"), ("cmd", "delete dentist"),
    ("null", "move laundry to friday", "a task named by words + a change: needs the fuzzy match, JS only moves #N"),
    ("null", "move #3 to 5 dec", "a month: only the AI reads it"),
    ("null", "#2 rename to call dad", "rename: not in the JS rules yet"),
    ("null", "#3 priority high", "priority change: not in the JS rules yet"),
    # --- questions ---
    ("ask", "what's due today"), ("ask", "what's due tomorrow"), ("ask", "what's due this week"), ("ask", "what is due friday"),
    ("ask", "what's overdue"), ("ask", "what have I finished"), ("finish", "what did I finish"),
    ("finish", "what did I finish today"), ("finish", "what did I finish this week"), ("ask", "show high priority tasks"), ("ask", "what's due next friday"),
    ("ask", "what do I have this weekend"), ("ask", "how many tasks are left"), ("ask", "มีอะไรต้องทำวันนี้"),
    ("ask", "งานอะไรสัปดาห์นี้"), ("ask", "anything about rent"),
    ("null", "what did I finish yesterday", "Python says it does not record the finish day: no list"),
]


def memory():
    return mock.patch.object(server, "load_memory", return_value=server.clean_memory({}))


def no_ai(*a, **k):
    raise RuntimeError("AI not available")


def run(sentence):
    """Python's whole command road with no AI. None = it needed the AI."""
    with mock.patch.object(server, "parse_with_ollama", no_ai), memory(), mock.patch.object(server, "AI_PROVIDER", "ollama"):
        try:
            return server.run_command(sentence, NOW_TEXT, CATEGORIES, [dict(t) for t in TASKS])
        except RuntimeError:
            return None


def echo_ai(prompt, *a, **k):
    """Stands in for the AI when cross-checking a plain add: copies the sentence, like tests/test_max.py fake_ai."""
    sentence = prompt.split("Sentence:")[-1].strip()
    m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", sentence, re.I)
    time = f"{int(m.group(1)) % 12 + (12 if m.group(2).lower() == 'pm' else 0):02d}:00" if m else ""
    return {"text": sentence, "when": "none", "time": time, "priority": "med", "category": "", "tokens": 0}


def expected_add(sentence):
    """A plain add without the AI (the steps of server.several_card), cross-checked against the full road."""
    plain = server.strip_greeting(" ".join(sentence.split()))[0]
    with memory():
        clean = server.clean_sentence(plain)
        task = server.check_task({"text": clean, "when": "none", "time": "", "priority": "med", "category": ""},
                                 clean, NOW_TEXT, CATEGORIES, server.load_memory())
    result = {"action": "add", "text": server.clean_title(task["text"]), "due": task["due"], "priority": task["priority"],
              "category": task["category"], "repeat": task["repeat"]}
    with mock.patch.object(server, "parse_with_ollama", echo_ai), memory(), mock.patch.object(server, "AI_PROVIDER", "ollama"):
        full = server.run_command(sentence, NOW_TEXT, CATEGORIES, [dict(t) for t in TASKS])
    if full.get("action") != "add" or full.get("due") != result["due"] or full.get("category") != result["category"]:
        raise SystemExit(f"cross-check failed for {sentence!r}: {full} vs {result}")
    return result


def simple(result):
    """The part of Python's answer that max-offline.js has to match."""
    if result is None:
        return None
    if result.get("action") == "answer":
        return {"action": "answer", "filter": result["filter"], "nums": result["nums"]}
    keep = ("action", "num", "changes", "missing", "choices", "text", "due", "category")
    return {k: result[k] for k in keep if k in result}


def main():
    cases = []
    for i, case in enumerate(CASES, 1):
        kind, sentence = case[0], case[1]
        entry = {"id": i, "kind": kind, "text": sentence}
        if kind == "add":
            entry["expect"] = expected_add(sentence)
        elif kind in ("cmd", "ask", "finish"):
            # "finish" = "what did I finish ...": Python now reads it as a done-question (server.py question_filter)
            result = run(sentence)
            if result is None:  # "done #99": Python still asks the AI once, then keeps its own "can't find #99"
                with memory():
                    result = server.command_by_rules(sentence, NOW_TEXT, CATEGORIES, [dict(t) for t in TASKS])
                if not result or "missing" not in result or not re.search(r"#\s*\d", sentence):
                    raise SystemExit(f"{sentence!r}: Python needed the AI - make it a null case")
                result["path"] = "rules"
            if result.get("path") != "rules":
                raise SystemExit(f"{sentence!r}: Python needed the AI ({result}) - make it a null case")
            entry["expect"] = simple(result)
        else:  # null
            entry["expect"] = None
            entry["why"] = case[2]
            python = run(sentence)
            entry["python"] = simple(python) if python and python.get("action") != "smalltalk" else (python.get("action") if python else "needs the AI")
        cases.append(entry)
    out = {
        "about": "Shared test list for max-offline.js. 'expect' is what Python (server.py) returned for the sentence; "
                 "null = JS must say 'not sure'. Made by tools-js/make_offline_cases.py - do not edit by hand.",
        "now": NOW_TEXT, "todos": TASKS, "cases": cases,
    }
    target = APP / ".claude" / "docs" / "offline-rules-cases.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(cases)} cases to {target}")


if __name__ == "__main__":
    main()
