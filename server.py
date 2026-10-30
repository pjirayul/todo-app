"""Small web server for the to-do app.

- Serves index.html, style.css and script.js
- POST /api/parse turns a sentence like "pay rent tomorrow 9am urgent"
  into a task using AI, or runs a command on an existing task
  ("move #2 to friday", "delete laundry", "done #3").

Run:  python server.py   then open http://127.0.0.1:8000
Test copy:  python server.py --test   then open http://127.0.0.1:8001  (own database, never touches your real data)
"""

import difflib
import ipaddress
import json
import os
import re
import shutil
import sqlite3
import sys
import threading
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

# ---------- Settings: change these to switch AI ----------
# "Max" is the owner's name for this AI assistant (command bar, dates, Break it down).
AI_PROVIDER = "ollama"          # "ollama" (free, on this PC) or "claude" (needs ANTHROPIC_API_KEY)
# Two brains: a fast one for the command bar, a smarter (slower) one for Break it down.
# If the smart one is missing or too slow, Max falls back to the fast one by itself.
FAST_MODEL = "qwen2.5:3b"
# Smart brain for Break it down. OFF for now (= the fast one): on this PC (4 GB graphics card) the 7B
# and the 3B can't stay loaded together, so each switch reloads a model: 7B ~50 s per Break it down,
# and the next command bar answer ~22 s instead of 1-2 s. To try it: SMART_MODEL = "qwen2.5:7b"
SMART_MODEL = FAST_MODEL
# One AI call per sentence that understands everything (add / change / done / undo / delete / question / chat);
# Python then checks every part. False = the old road (a "gate" call, then a parse call), kept as the easy undo.
ONE_CALL = True   # owner chose accuracy (30 Oct): exam 97.4% at warm avg 1.25 s. Speed limit for keep/undo is now 1.4 s. Set False to go back to two small calls.
SMART_TIMEOUT = 20              # seconds to wait for the smart brain before falling back to the fast one
CLAUDE_MODEL = "claude-haiku-5-5"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"  # lists the models Ollama has
OLLAMA_KEEP_ALIVE = "2h"  # keep the model in memory between commands (Ollama's default 5 min means a slow first call)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# The AI only copies date words into fields; Python does the calendar math (small models get it wrong)
INSTRUCTIONS = (
    "You turn one to-do sentence (English or Thai) into a structured task. Do NOT calculate dates, "
    "just fill the fields from the words used.\n"
    "The sentence may contain typos. "
    "text: short task title in the SAME language as the sentence, without date/time/priority words, "
    "with spelling mistakes fixed (e.g. lundry -> laundry, grocerys -> groceries, dentis -> dentist).\n"
    "priority: high for urgent/ASAP/ด่วน/important, low for someday/maybe/ไม่รีบ, otherwise med.\n"
    "category: one short English word like Work, Home, Shopping, Health, Study, Money, Personal "
    "(reuse an existing category when it fits; Work only for job tasks).\n"
    "when: none | today | tomorrow (พรุ่งนี้) | day_after_tomorrow (มะรืน) | in_days (\"in 3 days\") | "
    "weekday (\"Friday\", \"วันศุกร์\") | date (a day number like \"the 5th\", \"20 November\", \"วันที่ 5\").\n"
    "in_days: number for in_days, else 0. weekday: English day name for weekday, else \"\".\n"
    "next_week: true only if the sentence says next week / next Friday / สัปดาห์หน้า.\n"
    "day: day of month for date, else 0. month: month number 1-12 if a month is named, else 0.\n"
    "next_month: true if the sentence says next month / เดือนหน้า.\n"
    "time: 24h HH:MM if a time is said (5pm=17:00, บ่ายสาม=15:00, evening=18:00, morning=09:00, tonight=20:00), else \"\".\n"
    "Keep words written in CAPITALS (like TEST or ATM) exactly as written.\n"
    "The examples only show the format: never copy their words, use only the words of the sentence."
)

# The exact shape we want back
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "priority": {"type": "string", "enum": ["low", "med", "high"]},
        "category": {"type": "string"},
        "when": {"type": "string", "enum": ["none", "today", "tomorrow", "day_after_tomorrow", "in_days", "weekday", "date"]},
        "in_days": {"type": "integer"},
        "weekday": {"type": "string", "enum": [""] + WEEKDAYS},
        "next_week": {"type": "boolean"},
        "day": {"type": "integer"},
        "month": {"type": "integer"},
        "next_month": {"type": "boolean"},
        "time": {"type": "string"},
    },
    "required": ["text", "priority", "category", "when", "in_days", "weekday", "next_week", "day", "month", "next_month", "time"],
}


def add_months(d: datetime, n: int) -> datetime:
    """First day of the month n months after d."""
    m = d.month - 1 + n
    return d.replace(year=d.year + m // 12, month=m % 12 + 1, day=1)


def weekday_date(name: str, today, after: bool = False):
    """The date of a weekday. Default: nearest on or after today ("friday", "this friday").
    after=True: the first one strictly after today ("next friday": on a Friday that is +7)."""
    gap = WEEKDAYS.index(name) - today.weekday()
    return today + timedelta(days=(gap - 1) % 7 + 1 if after else gap % 7)


def resolve_due(task: dict, now: datetime, times: dict = None) -> str:
    """Turn the AI's date words into a real YYYY-MM-DDTHH:MM, or "" if no date."""
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    when = task.get("when", "none")
    date = None
    if when == "today":
        date = today
    elif when in ("tomorrow", "day_after_tomorrow"):
        date = today + timedelta(days=1 if when == "tomorrow" else 2)
    elif when == "in_days" and task.get("in_days", 0) > 0:
        date = today + timedelta(days=task["in_days"])
    elif when == "weekday" and task.get("weekday") in WEEKDAYS:
        target = WEEKDAYS.index(task["weekday"])
        if task.get("week_after"):  # "friday next week": that weekday in the following Mon–Sun week
            date = today - timedelta(days=today.weekday()) + timedelta(days=7 + target)
        else:  # "friday" = on or after today, "next friday" = strictly after today
            date = weekday_date(task["weekday"], today, bool(task.get("next_week")))
    elif when == "special":
        first_next = add_months(today.replace(day=1), 1)
        if task.get("special") == "weekend":  # the coming Saturday (Sat/Sun: today)
            date = today + timedelta(days=max(5 - today.weekday(), 0))
        elif task.get("special") == "month_end":
            date = first_next - timedelta(days=1)
        elif task.get("special") == "month_start":  # "start of next month"
            date = first_next
    elif when == "date" and 1 <= task.get("day", 0) <= 31:
        day, month = task["day"], task.get("month", 0)
        if task.get("next_month"):
            base = add_months(today, 1)
        elif 1 <= month <= 12:
            base = today.replace(month=month, day=1)
            if base < today.replace(day=1):
                base = base.replace(year=base.year + 1)
        else:
            base = today.replace(day=1)
            if day < today.day:
                base = add_months(today, 1)
        try:
            date = base.replace(day=day)
        except ValueError:  # e.g. 31 in a 30-day month: use the month's last day
            date = add_months(base, 1) - timedelta(days=1)
    if date is None:
        return ""
    try:
        hour, minute = map(int, task.get("time", "").split(":"))
        date = date.replace(hour=hour, minute=minute)
    except ValueError:
        # No time said: use the owner's "morning" time from About me (09:00 if not set)
        hour, minute = map(int, (times or DEFAULT_TIMES)["morning"].split(":"))
        date = date.replace(hour=hour, minute=minute)
    return date.strftime("%Y-%m-%dT%H:%M")


def parse_with_ollama(prompt: str, system: str = INSTRUCTIONS, schema: dict = TASK_SCHEMA,
                      timeout: int = 120, temperature: float = 0, model: str = FAST_MODEL) -> dict:
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps({
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "format": schema,   # forces the answer into our JSON shape
            "stream": False,
            "keep_alive": OLLAMA_KEEP_ALIVE,
            "options": {"temperature": temperature},
            **({"think": False} if model.startswith("qwen3") else {}),   # Qwen3 thinks by default: slow + <think> text
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        reply = json.loads(response.read())
    task = json.loads(reply["message"]["content"])
    task["tokens"] = reply.get("prompt_eval_count", 0) + reply.get("eval_count", 0)
    return task


def parse_with_claude(prompt: str) -> dict:
    import anthropic  # only needed for Claude: pip install anthropic
    from pydantic import BaseModel
    from typing import Literal

    class Task(BaseModel):
        text: str
        priority: Literal["low", "med", "high"]
        category: str
        when: Literal["none", "today", "tomorrow", "day_after_tomorrow", "in_days", "weekday", "date"]
        in_days: int
        weekday: Literal["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        next_week: bool
        day: int
        month: int
        next_month: bool
        time: str

    response = anthropic.Anthropic().messages.parse(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        output_config={"effort": "low"},
        system=INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}],
        output_format=Task,
    )
    task = response.parsed_output.model_dump()
    task["tokens"] = response.usage.input_tokens + response.usage.output_tokens
    return task


EXAMPLES = """Examples:
"call mom tomorrow evening" -> {"text":"Call mom","priority":"med","category":"Personal","when":"tomorrow","in_days":0,"weekday":"","next_week":false,"day":0,"month":0,"next_month":false,"time":"18:00"}
"ส่งรายงานวันศุกร์ บ่ายสาม ด่วน" -> {"text":"ส่งรายงาน","priority":"high","category":"Work","when":"weekday","in_days":0,"weekday":"Friday","next_week":false,"day":0,"month":0,"next_month":false,"time":"15:00"}
"จ่ายค่าเน็ตวันที่ 5 เดือนหน้า" -> {"text":"จ่ายค่าเน็ต","priority":"med","category":"Money","when":"date","in_days":0,"weekday":"","next_week":false,"day":5,"month":0,"next_month":true,"time":""}
"dentist 20 November 2pm" -> {"text":"Dentist","priority":"med","category":"Health","when":"date","in_days":0,"weekday":"","next_week":false,"day":20,"month":11,"next_month":false,"time":"14:00"}
"maybe repaint the bedroom someday" -> {"text":"Repaint the bedroom","priority":"low","category":"Home","when":"none","in_days":0,"weekday":"","next_week":false,"day":0,"month":0,"next_month":false,"time":""}
"do lundry and by grocerys tomorrow" -> {"text":"Do laundry and buy groceries","priority":"med","category":"Home","when":"tomorrow","in_days":0,"weekday":"","next_week":false,"day":0,"month":0,"next_month":false,"time":""}
"นัดหมอฟันวันศุกร์หน้า 10 โมง" -> {"text":"นัดหมอฟัน","priority":"med","category":"Health","when":"weekday","in_days":0,"weekday":"Friday","next_week":true,"day":0,"month":0,"next_month":false,"time":"10:00"}
"buy a birthday gift for dad in 3 days" -> {"text":"Buy a birthday gift for dad","priority":"med","category":"Shopping","when":"in_days","in_days":3,"weekday":"","next_week":false,"day":0,"month":0,"next_month":false,"time":""}"""


# Date words people often mistype; close matches get corrected before the AI sees them
DATE_WORDS = ["today", "tonight", "tomorrow", "next", "week", "month", "morning", "evening", "afternoon", "urgent"] + \
    [d.lower() for d in WEEKDAYS] + \
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
SHORTCUTS = {"tmr": "tomorrow", "tmrw": "tomorrow", "tml": "tomorrow", "2moro": "tomorrow", "2day": "today",
             "tonite": "tonight", "2nite": "tonight", "nxt": "next", "wk": "week", "asap": "urgent"}
# Short day names the AI often misses. Only used at the end or before a time ("gym mon 7am"),
# because "sun" and "sat" are also normal words ("buy sun cream", "sat down").
SHORT_DAYS = {"mon": "monday", "tue": "tuesday", "tues": "tuesday", "wed": "wednesday", "thu": "thursday",
              "thur": "thursday", "thurs": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday"}
THAI_TYPOS = {"พรุ่งนี": "พรุ่งนี้", "พุ่งนี้": "พรุ่งนี้", "พรุ้งนี้": "พรุ่งนี้", "พรุงนี้": "พรุ่งนี้", "วันนี": "วันนี้", "มะรือ": "มะรืน"}


def fix_date_typos(sentence: str) -> str:
    """'tomorow nxt frday' -> 'tomorrow next friday' (only date words are touched)."""
    for wrong, right in THAI_TYPOS.items():
        if wrong in sentence and right not in sentence:
            sentence = sentence.replace(wrong, right)
    words = []
    parts = sentence.split(" ")
    for i, word in enumerate(parts):
        low = word.lower().strip(",.!?")
        after = parts[i + 1].lower() if i + 1 < len(parts) else ""
        if low in SHORTCUTS:
            word = SHORTCUTS[low]
        elif low in SHORT_DAYS and (after == "" or after[0].isdigit() or after in ("morning", "evening", "afternoon", "night", "at")):
            word = SHORT_DAYS[low]
        elif len(low) >= 4 and low.isalpha() and low not in DATE_WORDS:
            # Same first letter + very similar, so normal words like "rent" never turn into "urgent"
            match = difflib.get_close_matches(low, [w for w in DATE_WORDS if w[0] == low[0]], n=1, cutoff=0.8)
            if match:
                word = match[0]
        words.append(word)
    return " ".join(words)


# Parts of the day: when no clock time is said, Python uses the owner's own times (About me).
# Thai words are kept specific ("ตอนเย็น", not "เย็น", which is also in ตู้เย็น = fridge).
DAY_PARTS = ((r"\b(to)?night\b|คืนนี้", "tonight"), (r"\bevening\b|ตอนเย็น|เย็นนี้|พรุ่งนี้เย็น", "evening"),
             (r"\bafternoon\b|ตอนบ่าย", "afternoon"), (r"\bmorning\b|ตอนเช้า|เช้านี้|พรุ่งนี้เช้า", "morning"))
# Thai clock words: Python reads them (the AI turned "บ่ายสาม" into 13:00 instead of 15:00).
# Each pattern gives the hour; "ครึ่ง" right after it means half past.
THAI_NUMS = {"หนึ่ง": 1, "สอง": 2, "สาม": 3, "สี่": 4, "ห้า": 5, "หก": 6, "เจ็ด": 7, "แปด": 8, "เก้า": 9,
             "สิบเอ็ด": 11, "สิบสอง": 12, "สิบ": 10}
_N = r"(?P<n>\d{1,2}|สิบเอ็ด|สิบสอง|สิบ|หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า)"
THAI_TIMES = (
    (r"เที่ยงคืน", lambda n, w: 0),                                   # midnight
    (r"เที่ยง(วัน)?", lambda n, w: 12),                                # noon
    (r"บ่าย\s*(โมง|" + _N + r"\s*(โมง)?)", lambda n, w: 13 if n is None else n + 12 if n < 12 else n),  # บ่ายสาม = 15
    (_N + r"\s*ทุ่ม|ทุ่ม(นึง|หนึ่ง)?", lambda n, w: 18 + (n or 1)),       # สองทุ่ม = 20, ทุ่ม / ทุ่มครึ่ง = 19:00 / 19:30
    (r"ตี\s*" + _N, lambda n, w: n),                                  # ตีสอง = 2
    # "10 โมง" = 10, "5 โมงเย็น" = 17; 1-5 โมง without เช้า is afternoon (สามโมง = 15)
    (_N + r"\s*โมง\s*(เย็น|เช้า)?",
     lambda n, w: n if "เช้า" in w or n >= 12 else n + 12 if "เย็น" in w or n <= 5 else n),
)
THAI_TIME_ANY = "|".join(p.replace("?P<n>", "?:") for p, _ in THAI_TIMES)  # one pattern for "any Thai time"


def thai_time(text: str) -> str:
    """'บ่ายสามครึ่ง' -> '15:30', 'สองทุ่ม' -> '20:00' ('' if no Thai time word)."""
    for pattern, hour in THAI_TIMES:
        m = re.search(r"(?:" + pattern + r")\s*(ครึ่ง)?", text)
        if m:
            n = m.groupdict().get("n")
            h = hour(None if n is None else int(n) if n.isdigit() else THAI_NUMS[n], m.group(0))
            if 0 <= h <= 23:
                return f"{h:02d}:{30 if m.group(0).endswith('ครึ่ง') else 0:02d}"
    return ""


# English clock phrases without am/pm: "7 in the morning", "morning 8", "at 5", "midnight"
PART_TIME = re.compile(r"\b(\d{1,2})(?:[:.]([0-5]\d))?\s*(?:o'?clock\s*)?(?:in the |at |of the )?(morning|afternoon|evening|night)\b"
                       r"|\b(morning|afternoon|evening|night)\s+(?:at\s+)?(\d{1,2})(?![\d:/]|st|nd|rd|th)")
AT_HOUR = re.compile(r"\bat (\d{1,2})(?![\d:/]|st|nd|rd|th|\s*(?:days?|weeks?|min|hours?|times))")
CLOCK_TIME = re.compile(r"\d\s*(:\s*\d\d|\.\d\d|am\b|pm\b|น\.|โมง|ทุ่ม)|\bnoon\b|\bmidnight\b|" + PART_TIME.pattern + "|" +
                        AT_HOUR.pattern + "|" + THAI_TIME_ANY, re.I)
# A little linking word stuck to a date ("ในวันศุกร์", "ภายในพรุ่งนี้", "ตอนบ่ายสาม") goes away with it; the same
# word anywhere else ("ของในตู้เย็น") stays. The lead word is tried first, so "ตอนบ่ายสาม" is cut whole.
THAI_DATE_WORDS = (r"(?:(?:ภายใน|ใน|ตอน|เมื่อ)\s*)?(?:มะรืนนี้|มะรืน|พรุ่งนี้|วันนี้|คืนนี้|ตอนเช้า|ตอนเย็น|ตอนบ่าย|ด่วน|ไม่รีบ|"
                   r"(วัน)?(จันทร์|อังคาร|พุธ|พฤหัส(บดี)?|ศุกร์|เสาร์|อาทิตย์)(หน้า|นี้)?|วันที่\s*\d+|"
                   r"(" + THAI_TIME_ANY + r")(\s*ครึ่ง)?|\d+\s*(โมง|ทุ่ม)|(สัปดาห์|เดือน)หน้า|อีก\s*\d+\s*(วัน|สัปดาห์|อาทิตย์)|สิ้นเดือน|ปลายเดือน|ต้นเดือนหน้า|สุดสัปดาห์(นี้)?)")
THAI_LETTERS = re.compile(r"[฀-๿]")

# Weekday names Python reads itself (the AI sometimes says "next week" when nobody did).
# อาทิตย์ alone also means "week", so Sunday needs "วันอาทิตย์".
THAI_WEEKDAYS = {"จันทร์": "Monday", "อังคาร": "Tuesday", "พุธ": "Wednesday", "พฤหัส": "Thursday",
                 "ศุกร์": "Friday", "เสาร์": "Saturday", "วันอาทิตย์": "Sunday"}
NEXT_WEEK = re.compile(r"\bnext\b|(สัปดาห์|อาทิตย์|จันทร์|อังคาร|พุธ|พฤหัส(บดี)?|ศุกร์|เสาร์)หน้า")
# "friday next week" = that weekday inside next Mon-Sun week; plain "next friday" = first Friday after today
WEEK_AFTER = re.compile(r"\bnext week\b|(สัปดาห์|(?<!วัน)อาทิตย์)หน้า")
# "add buy milk" / "เพิ่ม ซื้อนม": the command word itself is not part of the task
ADD_WORDS = re.compile(r"^(add|create|new task:?)\s+|^เพิ่ม(งาน)?\s*", re.I)
# "remind me to call mom" / "เตือนให้โทรหาแม่" / "อย่าลืมซื้อนม": the lead-in is not part of the title
LEAD_INS = re.compile(r"^(please\s+)?(remind\s+me(\s+(to|about|of))?|remember\s+to|don'?t\s+forget(\s+to)?)\s+"
                      r"|^(เตือน(ฉัน|ผม|เรา)?ให้|เตือน(ฉัน|ผม|เรา)|อย่าลืม)\s*", re.I)


def strip_lead_in(text: str) -> str:
    """'remind me to call mom tomorrow' -> 'call mom tomorrow' (the rest of the owner's words stay)."""
    return LEAD_INS.sub("", text.strip(), count=1).strip() or text.strip()


def weekday_in(lower: str) -> str:
    """'call bank friday' / 'ส่งงานวันศุกร์' -> 'Friday' ('' if no weekday is named)."""
    m = re.search(r"\b(" + "|".join(d.lower() for d in WEEKDAYS) + r")\b", lower)
    if m:
        return m.group(1).capitalize()
    return next((day for thai, day in THAI_WEEKDAYS.items() if thai in lower), "")


DAY_WORDS = ((("มะรืน", "day after tomorrow"), "day_after_tomorrow"),
             (("พรุ่งนี้", "tomorrow"), "tomorrow"),
             (("วันนี้", "today", "tonight", "คืนนี้"), "today"))
# Phrases Python reads exactly (the AI only had "today/tomorrow/weekday/date"): the table is in
# .claude/docs/research/date-rules-2026-10-30.md. Each one is a small regex, resolved in resolve_due.
WEEKS_AHEAD = re.compile(r"\bin\s+(\d+|a|one|two|three)\s+weeks?\b|อีก\s*(\d+)\s*(?:สัปดาห์|อาทิตย์)")
WEEKEND = re.compile(r"\bweekend\b|สุดสัปดาห์|เสาร์อาทิตย์")
MONTH_END = re.compile(r"\bend of (?:the |this )?month\b|สิ้นเดือน|ปลายเดือน")
MONTH_START = re.compile(r"\b(?:start|beginning) of next month\b|ต้นเดือนหน้า")
SPECIAL_DAYS = (WEEKS_AHEAD, WEEKEND, MONTH_END, MONTH_START)
WEEK_COUNTS = {"a": 1, "one": 1, "two": 2, "three": 3}


def special_day(lower: str) -> dict:
    """'gym this weekend' -> {'when': 'special', 'special': 'weekend'}; {} if none of these phrases is there."""
    m = WEEKS_AHEAD.search(lower)
    if m:
        n = m.group(1) or m.group(2)
        return {"when": "in_days", "in_days": 7 * int(WEEK_COUNTS.get(n) or n)}
    for pattern, label in ((WEEKEND, "weekend"), (MONTH_END, "month_end"), (MONTH_START, "month_start")):
        if pattern.search(lower):
            return {"when": "special", "special": label}
    return {}


# "in 3 days" / "อีก 3 วัน"
DAYS_AHEAD = re.compile(r"\bin\s+(\d+)\s+days?\b|อีก\s*(\d+)\s*วัน")


def days_ahead(lower: str) -> int:
    """'pay bill in 3 days' / 'จ่ายค่าเน็ตอีก 3 วัน' -> 3 (0 if not said)."""
    m = DAYS_AHEAD.search(lower)
    return int(m.group(1) or m.group(2)) if m else 0


def english_time(text: str) -> str:
    """'5pm' -> '17:00', '9:30 am' -> '09:30', '17:45' -> '17:45', 'noon' -> '12:00' ('' if none)."""
    m = re.search(r"\b(\d{1,2})(?:[:.]([0-5]\d))?\s*(am|pm)\b", text)
    if m and 1 <= int(m.group(1)) <= 12:
        hour = int(m.group(1)) % 12 + (12 if m.group(3) == "pm" else 0)
        return f"{hour:02d}:{m.group(2) or '00'}"
    m = PART_TIME.search(text)
    if m:  # "7 in the morning" = 07:00, "3 in the afternoon" = 15:00, "8 at night" = 20:00
        hour, minute, part = int(m.group(1) or m.group(5)), m.group(2) or "00", m.group(3) or m.group(4)
        if 1 <= hour <= 12:
            hour = hour % 12 + (0 if part == "morning" else 12)
            return f"{hour % 24:02d}:{minute}"
    m = re.search(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*น\.?|\b)", text) if "น" in text else None
    m = m or re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    m = AT_HOUR.search(text)  # "at 5": 1-6 is the afternoon, 7-11 the morning (nobody sets a task for 5 am without saying so)
    if m and 1 <= int(m.group(1)) <= 23:
        hour = int(m.group(1))
        return f"{hour + 12 if hour <= 6 else hour:02d}:00"
    if re.search(r"\bmidnight\b", text):
        return "00:00"
    return "12:00" if re.search(r"\bnoon\b", text) else ""


def rules_date(text: str, times: dict):
    """Day/time words Python can read alone ("friday", "tomorrow 5pm", "บ่ายสาม") -> the dict resolve_due
    needs. None = something else is in there (a month, "next week"...), so the AI must read it."""
    low = fix_date_typos(text).lower()
    task = {"when": "none", "time": thai_time(low) or english_time(low)}
    day = weekday_in(low)
    if day:
        task.update(when="weekday", weekday=day, next_week=bool(NEXT_WEEK.search(low)),
                    week_after=bool(WEEK_AFTER.search(low)))
    elif days_ahead(low):
        task.update(when="in_days", in_days=days_ahead(low))
    for words, when in DAY_WORDS:
        if any(w in low for w in words):
            task["when"] = when
            break
    task.update(special_day(low))
    # Take out every day word handled above; if DAY_HINTS still finds a date word, the AI is needed
    left = DAYS_AHEAD.sub(" ", low)
    for pattern in SPECIAL_DAYS:
        left = pattern.sub(" ", left)
    for words, _ in DAY_WORDS:
        for w in words:
            left = left.replace(w, " ")
    left = re.sub(r"\b(" + "|".join(d.lower() for d in WEEKDAYS) + r")\b|(วัน)?(" + "|".join(THAI_WEEKDAYS) + ")", " ", left)
    if day:
        left = re.sub(r"\bnext\b", " ", left)  # "next friday" is fine; "next week" is not (the AI reads it)
    if DAY_HINTS.search(left):
        return None
    if not CLOCK_TIME.search(low):
        for pattern, part in DAY_PARTS:
            if re.search(pattern, low):
                task["time"] = times[part]
                break
    if CLOCK_TIME.search(low) and not task["time"]:
        return None  # a clock time we could not read
    if task["when"] == "none":
        if not task["time"]:
            return None
        task["when"] = "today"  # only a time: the caller keeps the task's own day
    return task


def keep_capitals(title: str, sentence: str) -> str:
    """Words the owner typed in CAPITALS ("TEST", "ATM") are on purpose: keep them as typed."""
    skip = set(DATE_WORDS) | set(SHORTCUTS) | set(SHORT_DAYS) | set(PRIORITY_WORDS) | {"am", "pm"}
    for word in dict.fromkeys(re.findall(r"\b[A-Z][A-Z0-9]+\b", sentence)):
        if word.lower() in skip:
            continue
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, title, re.I):
            title = re.sub(pattern, word, title, flags=re.I)   # "Test water plants" -> "TEST water plants"
        elif sentence.startswith(word):
            title = f"{word} {title[:1].lower()}{title[1:]}"  # the AI dropped it: put it back
        else:
            title = f"{title} {word}"
    return title


# Small words the AI may leave out of a title without losing anything
FILLER_WORDS = {"a", "an", "the", "to", "me", "my", "remind", "remember", "please", "i", "need", "must", "should",
                "have", "for", "and", "of", "with"}
CAPITALS = re.compile(r"[A-Z][A-Z0-9]+")
TIME_LIKE = re.compile(r"\d+([:.]\d\d)?(am|pm|st|nd|rd|th|น\.?)?|\d{1,2}/\d{1,2}")


def own_words(sentence: str) -> list:
    """The owner's words without the date/time/priority words Python knows: 'TEST dentist friday 3pm' -> TEST, dentist."""
    skip = set(DATE_WORDS) | set(SHORTCUTS) | set(SHORT_DAYS) | set(PRIORITY_WORDS) | \
        {"am", "pm", "at", "on", "by", "in", "next", "this", "after", "day", "days", "noon", "night", "midnight"}
    s = re.sub(THAI_DATE_WORDS, " ", sentence)
    for pattern in SPECIAL_DAYS + (DAYS_AHEAD,):
        s = pattern.sub(" ", s)   # "this weekend", "in 2 weeks", "end of month" are dates, not title words
    s = re.sub(r"(on )?(the )?\d{1,2}(st|nd|rd|th)\b", " ", s)   # "pay rent on the 5th"
    s = re.sub(r"\s(เช้า|เย็น|บ่าย|ค่ำ|ดึก)(\s|$)", " ", " " + s + " ")
    return [w for w in s.split() if w.lower().strip(",.!?") not in skip and not TIME_LIKE.fullmatch(w.lower().strip(",.!?"))]


def keep_own_words(title: str, sentence: str) -> str:
    """Safety net: the AI sometimes drops real words ("TEST dentist friday 3pm" -> "TEST").
    If a word the owner typed is missing from the title, use the owner's own words instead."""
    words = own_words(sentence)
    title_words = [w.lower().strip(",.!?") for w in title.split()]

    def present(word):
        low = word.lower().strip(",.!?")
        if THAI_LETTERS.search(low) or low in FILLER_WORDS or low in title.lower() or CAPITALS.fullmatch(word):
            return True  # Thai has no spaces: checked by length below; CAPITALS: keep_capitals puts them back
        # Close enough counts, so the AI's spelling fixes ("lundry" -> "laundry") stay
        return any(difflib.SequenceMatcher(None, low, t).ratio() >= 0.75 for t in title_words)

    thai_typed = len(THAI_LETTERS.findall(" ".join(words)))
    if words and (not all(present(w) for w in words) or len(THAI_LETTERS.findall(title)) < thai_typed * 0.6):
        return " ".join(words)
    return title


# The category names the AI prompt uses. Keywords (lowercase English, Thai) that point to each one,
# checked in this order, so "pay rent" is Home (rent) before it is Money (pay).
DEFAULT_CATEGORIES = ["Work", "Home", "Shopping", "Health", "Study", "Money", "Personal"]
CATEGORY_HINTS = (
    ("Health", r"\b(gym|run|running|jog|jogging|workout|exercise|yoga|doctor|dentist|dental|hospital|clinic|medicine|"
               r"pharmacy|check-?up|vitamins?)\b|ออกกำลัง|วิ่ง|ฟิตเนส|โยคะ|หมอ|ฟัน|โรงพยาบาล|คลินิก|กินยา|ซื้อยา|ตรวจสุขภาพ"),
    ("Home", r"\b(rent|bills?|clean|cleaning|laundry|groceries|grocery|dishes|trash|garbage|repaint|repair)\b|"
             r"ค่าเช่า|ค่าน้ำ|ค่าไฟ|ทำความสะอาด|ซักผ้า|ล้างจาน|ทิ้งขยะ|ซ่อม|ซื้อของเข้าบ้าน|ตลาด"),
    ("Study", r"\b(study|homework|exam|class|course|lecture|assignment)\b|เรียน|การบ้าน|สอบ|อ่านหนังสือ"),
    ("Money", r"\b(pay|tax|bank|salary|budget|invoice|transfer|insurance)\b|ภาษี|ธนาคาร|โอนเงิน|เงินเดือน|ประกัน|จ่าย"),
    ("Shopping", r"\b(buy|shopping|order|purchase)\b|ซื้อ|สั่งของ"),
    ("Work", r"\b(meeting|report|email|client|project|deadline|boss|presentation)\b|ประชุม|รายงาน|ลูกค้า|โปรเจกต์|พรีเซนต์"),
)


# Clear work words: when one is in the sentence, hints like "run" or "clean" must never turn it into Health/Home
WORK_WORDS = re.compile(r"\b(boss|client|team|meeting|project|report|server|code|office|colleague|deadline|presentation|email)\b|"
                        r"งาน|ประชุม|หัวหน้า|ลูกค้า|รายงาน|โปรเจกต์")
# Strong, unambiguous hints: these may correct a wrong (but known) AI category
STRONG_HINTS = (
    ("Health", r"\b(gym|workout|dentist|doctor)\b|ยิม|หมอ"),
    ("Home", r"\brent\b|ค่าเช่า"),
)


def pick_category(ai_category: str, sentence: str, known: list) -> str:
    """Keep the AI's category when it is one we know; when it gave none or an odd one, use keyword hints.
    Only existing category names are used (the owner's own spelling wins: 'health' -> 'Health')."""
    names = {c.lower(): c for c in DEFAULT_CATEGORIES + list(known)}
    ai_category = (ai_category or "").strip()
    lower = sentence.lower()
    ai_known = ai_category.lower() in names
    # Work words win over every keyword hint ("send run report to boss" is Work)
    if WORK_WORDS.search(lower):
        return names["work"] if (not ai_known or ai_category.lower() in ("work", "personal")) else names[ai_category.lower()]
    # A strong hint beats the AI's default category (not the owner's own categories like "Family")
    if not ai_known or ai_category.lower() in (c.lower() for c in DEFAULT_CATEGORIES):
        for name, pattern in STRONG_HINTS:
            if re.search(pattern, lower):
                return names.get(name.lower(), name)
    # The small AI over-uses "Work" and "Personal": for those, a clear keyword ("gym") is more reliable
    if ai_known and ai_category.lower() not in ("work", "personal"):
        return names[ai_category.lower()]
    for name, pattern in CATEGORY_HINTS:
        if re.search(pattern, lower):
            return names.get(name.lower(), name)
    return names.get(ai_category.lower(), ai_category)  # no hint: whatever the AI said (may be empty)


def clean_sentence(sentence: str) -> str:
    """The sentence as the AI gets it: no "add"/"remind me to", date typos fixed."""
    sentence = ADD_WORDS.sub("", sentence).strip() or sentence
    return fix_date_typos(strip_lead_in(sentence))


def ai_prompt(sentence: str, categories: list, examples: str = None):
    """The fixed start (examples, About me, categories) comes first so Ollama can reuse it. Returns (prompt, known, memory)."""
    memory = load_memory()
    known = list(dict.fromkeys(categories + memory["categories"]))[:30]  # existing + the owner's own, no repeats
    about = memory_summary(memory)
    prompt = f"{examples or EXAMPLES}\n\n{about + chr(10) if about else ''}Existing categories: {', '.join(known) or 'none'}\nSentence: {sentence}"
    return prompt, known, memory


def parse_task(sentence: str, now: str, categories: list) -> dict:
    sentence = clean_sentence(sentence)
    prompt, known, memory = ai_prompt(sentence, categories)
    task = parse_with_ollama(prompt) if AI_PROVIDER == "ollama" else parse_with_claude(prompt)
    return check_task(task, sentence, now, known, memory)


def check_task(task: dict, sentence: str, now: str, known: list, memory: dict) -> dict:
    """Python checks what the AI said (dates, time, title, category) and returns the safe task.
    Shared by parse_task (one task per call) and understand() (one call for every kind of sentence)."""
    # Common day words are certain, so they override the AI
    lower = sentence.lower()
    # A named weekday is certain too: "วันศุกร์" on a Thursday is tomorrow, not next week's Friday
    day = weekday_in(lower)
    if day and task.get("when") != "date":
        task.update(when="weekday", weekday=day, next_week=bool(NEXT_WEEK.search(lower)),
                    week_after=bool(WEEK_AFTER.search(lower)))
    elif days_ahead(lower):  # "in 3 days" / "อีก 3 วัน": the count is exact, so Python sets it
        task.update(when="in_days", in_days=days_ahead(lower))
    for words, when in DAY_WORDS:
        if any(w in lower for w in words):
            task["when"] = when
            break
    # "this weekend", "in 2 weeks", "end of month": exact phrases the AI has no label for
    task.update(special_day(lower))
    # "tonight" / "this evening" without a clock time: the owner's own time, not the AI's guess
    if not CLOCK_TIME.search(lower):
        for pattern, part in DAY_PARTS:
            if re.search(pattern, lower):
                task["time"] = memory["times"][part]
                break
    task["time"] = thai_time(lower) or english_time(lower) or task.get("time", "")  # "บ่ายสาม" = 15:00, whatever the AI said
    # No day or time words at all: the AI made the date up ("นัดประชุมทีม" -> next Friday), so no date
    # Only a time ("ส่งรายงานบ่ายสาม", "call mom at 5pm"): today, like "tonight"
    if not DAY_HINTS.search(lower):
        task["when"] = "today" if time_said(lower) else "none"
    # Small models sometimes slip; keep the result safe for the app
    title = strip_lead_in(task.get("text") or sentence)  # the AI may put "Remind me to" back
    if THAI_LETTERS.search(sentence) and not THAI_LETTERS.search(title):
        title = sentence  # a Thai sentence got an English title: keep the owner's own words
    if THAI_LETTERS.search(title):
        # Date/time words the AI left in a Thai title ("นัดหมอฟัน เย็น" -> "นัดหมอฟัน")
        clean = re.sub(THAI_DATE_WORDS, " ", title)
        clean = re.sub(r"\s(เช้า|เย็น|บ่าย|ค่ำ|ดึก)(\s|$)", " ", " " + clean + " ")
        title = " ".join(clean.split()) or title
    title = keep_own_words(title, sentence)
    title = keep_capitals(title, sentence)
    return {
        "text": title[:1].upper() + title[1:],  # "pay rent" -> "Pay rent"
        "due": resolve_due(task, datetime.strptime(now[:16], "%Y-%m-%dT%H:%M"), memory["times"]),
        "time": task.get("time", "") if HHMM.fullmatch(str(task.get("time", ""))) else "",  # used by updates
        "priority": task.get("priority") if task.get("priority") in ("low", "med", "high") else "med",
        "category": pick_category(task.get("category", ""), sentence, known),
        "tokens": task.get("tokens", 0),
    }


# ---------- "Break it down": the AI suggests small steps for one task ----------
BREAKDOWN_INSTRUCTIONS = (
    "You are Max, a personal assistant. Split one to-do task into 3 to 6 small, concrete steps, "
    "in the order they are done. Each step is a short action (under 10 words) that starts with a verb. "
    "Make the steps fit THIS task: use its places, dates, people and notes. "
    "No numbering, no explanations, no steps that repeat the task itself. "
    "The examples only show the format: never copy their steps. Write the steps in the language you are told."
)
BREAKDOWN_SCHEMA = {
    "type": "object",
    "properties": {"steps": {"type": "array", "items": {"type": "string"}}},
    "required": ["steps"],
}
BREAKDOWN_EXAMPLES = """Examples:
Task: Renew passport -> {"steps":["Check the passport expiry date","Book an appointment at the passport office","Take a new passport photo","Bring the old passport and ID","Pay the fee and keep the receipt"]}
Task: Plan a birthday dinner for mom -> {"steps":["Pick a date that suits the family","Choose a restaurant mom likes","Book a table for everyone","Order a birthday cake"]}
Task: ทำความสะอาดห้องครัว -> {"steps":["เก็บของบนเคาน์เตอร์","ล้างจานที่ค้างอยู่","เช็ดเตาและเคาน์เตอร์","ถูพื้นห้องครัว","ทิ้งขยะ"]}
Task: ยื่นภาษีออนไลน์ -> {"steps":["รวบรวมเอกสารรายได้และค่าลดหย่อน","เข้าเว็บกรมสรรพากร","กรอกแบบฟอร์มภาษี","ตรวจทานแล้วกดยื่นแบบ","บันทึกหลักฐานการยื่น"]}"""


def breakdown_with_claude(prompt: str) -> dict:
    import anthropic  # only needed for Claude: pip install anthropic
    from pydantic import BaseModel

    class Steps(BaseModel):
        steps: list[str]

    response = anthropic.Anthropic().messages.parse(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        output_config={"effort": "low"},
        system=BREAKDOWN_INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}],
        output_format=Steps,
    )
    result = response.parsed_output.model_dump()
    result["tokens"] = response.usage.input_tokens + response.usage.output_tokens
    return result


def break_down(text: str, notes: str, due: str, model: str = None) -> dict:
    """Ask the AI for steps, then make the answer safe: 3-6 short, different steps.
    model: force one brain (for testing); normally the smart one, falling back to the fast one."""
    # Small models drift into English, so Python decides the language and says it plainly
    language = "Thai" if THAI_LETTERS.search(text) else "English"
    about = memory_summary(load_memory(), notes_only=True)
    prompt = f"{BREAKDOWN_EXAMPLES}\n\n{about + chr(10) if about else ''}Language: {language}\nTask: {text}"
    if notes:
        prompt += f"\nNotes: {notes}"
    if due:
        # Friendly date, so the AI doesn't paste "2026-10-30T09:00" into a step
        prompt += f"\nDue: {datetime.strptime(due, '%Y-%m-%dT%H:%M').strftime('%a %d %b %H:%M')}"
    brain = CLAUDE_MODEL
    if AI_PROVIDER == "ollama":
        # A little temperature gives livelier steps
        ask = lambda m, secs: parse_with_ollama(prompt, BREAKDOWN_INSTRUCTIONS, BREAKDOWN_SCHEMA,
                                                timeout=secs, temperature=0.3, model=m)
        brain = model or (SMART_MODEL if SMART_MODEL in max_status()["models"] else FAST_MODEL)
        try:
            result = ask(brain, SMART_TIMEOUT if brain != FAST_MODEL else 45)
        except Exception as e:
            if brain == FAST_MODEL or model:
                raise
            # The smart brain is missing, busy or too slow: the fast one answers instead
            print(f"Max: {brain} failed ({type(e).__name__}), using {FAST_MODEL}")
            brain = FAST_MODEL
            result = ask(brain, 30)
    else:
        result = breakdown_with_claude(prompt)
    steps, seen = [], set()
    for s in result.get("steps") or []:
        s = re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", str(s)).strip()  # drop "1." or "-" the AI may add
        if len(s) > 80:
            s = s[:79].rstrip() + "…"
        if s and s.lower() not in seen:
            seen.add(s.lower())
            steps.append(s[:1].upper() + s[1:])
    return {"steps": steps[:6], "tokens": result.get("tokens", 0), "brain": brain}


# ---------- Command bar: act on an existing task ----------
# Python spots the action and the target (reliable); the AI is only used to read dates.
# Each pattern must match at the START of the sentence (after lowercasing).
UNDO_WORDS = r"^(undo|undone|uncheck|unmark|reopen|not done)\b|ยังไม่เสร็จ|ยกเลิกเสร็จ"
DELETE_WORDS = r"^(delete|remove|del|erase|cancel(?=\s*#)|get rid of)\b|^ลบ"
DONE_WORDS = r"^(done|mark(?!['’])|tick|finished|completed)\b|\b(done|finished|completed)$|เสร็จ(แล้ว)?$|^เสร็จ"
UPDATE_WORDS = r"^(change|modify|move|rename|set|edit|update|reschedule|postpone|push|delay)\b|^(เปลี่ยน|แก้|ย้าย|เลื่อน)"
# Filler words removed around the target ("mark #2 as done", "งาน #1 เสร็จแล้ว")
FILLER = r"^((the|task|as|is|of|to)\b|งาน|ของ|ให้เป็น|เป็น|ไปเป็น|ไป)\s*"
FIELD_WORDS = {"category": "category", "cat": "category", "หมวดหมู่": "category", "หมวด": "category",
               "priority": "priority", "ความสำคัญ": "priority",
               "date": "due", "due": "due", "time": "due", "deadline": "due", "วันที่": "due", "เวลา": "due",
               "name": "text", "title": "text", "text": "text", "ชื่อ": "text"}
PRIORITY_WORDS = {"high": "high", "urgent": "high", "important": "high", "asap": "high", "ด่วน": "high", "สูง": "high",
                  "สำคัญ": "high", "low": "low", "someday": "low", "maybe": "low", "ไม่รีบ": "low", "ต่ำ": "low",
                  "med": "med", "medium": "med", "normal": "med", "กลาง": "med", "ปกติ": "med"}


def strip_filler(s: str) -> str:
    """Remove filler words from both ends: 'the laundry as done' -> 'laundry'."""
    s = s.strip(" .,!?:")
    while True:
        new = re.sub(FILLER, "", s, flags=re.I)
        new = re.sub(r"\s*\b(as|is|to)$", "", new, flags=re.I).strip(" .,!?:")
        if new == s:
            return s
        s = new


def find_task(target: str, tasks: list):
    """Match '#3' or task words (typos allowed) to one task. Returns (num, choices)."""
    m = re.fullmatch(r"#?\s*(\d+)", target.strip())
    if m:
        num = int(m.group(1))
        return (num, []) if any(t["num"] == num for t in tasks) else (None, [])
    words = target.lower().strip()
    if not words:
        return None, []
    scores = []
    for t in tasks:
        text = str(t.get("text", "")).lower()
        if words in text:
            score = 1.0  # the words appear in the task as typed
        else:
            # Compare with the whole title and with each run of the same number of words,
            # so "lundry" still finds "Do laundry"
            parts, n = text.split(), len(words.split())
            pieces = [text] + [" ".join(parts[i:i + n]) for i in range(len(parts))]
            score = max(difflib.SequenceMatcher(None, words, p).ratio() for p in pieces)
        scores.append((score, t["num"]))
    scores.sort(reverse=True)
    good = [s for s in scores if s[0] >= 0.75]
    if not good:
        return None, []
    # Two tasks that match about equally well: don't guess, ask which one
    close = [num for score, num in good if score >= good[0][0] - 0.05]
    return (close[0], []) if len(close) == 1 else (None, close[:5])


LOOSE_SKIP = {"the", "task", "thing", "tasks", "this", "that", "with", "from", "about", "please", "item"}


def find_task_loose(target: str, tasks: list):
    """find_task, and if nothing fits, the longest word of the target that only ONE task contains
    ("ploy thing" -> the task with "Ploy"; "with dentist" -> "Dentist appointment"). Used for the AI's target only."""
    num, choices = find_task(target, tasks)
    if num is not None or choices:
        return num, choices
    words = sorted({w for w in re.findall(r"\w+", target.lower()) if len(w) >= 4 and w not in LOOSE_SKIP}, key=len, reverse=True)
    for w in words:
        hits = [t["num"] for t in tasks if w in str(t.get("text", "")).lower()]
        if len(hits) == 1:
            return hits[0], []
    return None, []


# Did the change text name a day, or a clock time? Only then may the task's date/time change.
DAY_HINTS = re.compile(
    r"\b(today|tonight|tomorrow|next|week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|in \d+ days?|in (\d+|a|one|two|three) weeks?|weekend|end of (the |this )?month|(start|beginning) of next month|\d{1,2}(st|nd|rd|th))\b|\d{1,2}/\d{1,2}|"
    r"มะรืน|พรุ่งนี้|วันนี้|คืนนี้|จันทร์|อังคาร|พุธ|พฤหัส|ศุกร์|เสาร์|วันอาทิตย์|วันที่\s*\d+|(สัปดาห์|อาทิตย์|เดือน)หน้า|อีก\s*\d+\s*(วัน|สัปดาห์|อาทิตย์)|สิ้นเดือน|ปลายเดือน|ต้นเดือนหน้า|สุดสัปดาห์|เสาร์อาทิตย์", re.I)


def time_said(text: str) -> bool:
    return bool(CLOCK_TIME.search(text) or any(re.search(p, text) for p, _ in DAY_PARTS))


# ---------- "Max asks when unsure": Python decides when a question is worth it ----------
# Tasks that clearly happen at a certain time or place. Kept small on purpose: Max should only ask
# when it really helps. Both lists: "When?" on new tasks and "Quick details" before Break it down.
# Only travel also gets "Budget?" (a budget for a meeting makes no sense).
TRAVEL_WORDS = re.compile(r"\b(flight|hotel|trip|travel|holiday|vacation)s?\b|เที่ยวบิน|โรงแรม|เที่ยว|ทริป|จอง", re.I)
EVENT_WORDS = re.compile(r"\b(meeting|appointment|interview|dentist|doctor)s?\b|นัด|ประชุม|สัมภาษณ์", re.I)


def ask_words(text: str) -> bool:
    return bool(TRAVEL_WORDS.search(text) or EVENT_WORDS.search(text))
# "done it", "move it to friday", just "done": no task named, so Max asks which one
PRONOUNS = {"", "it", "this", "that", "this one", "that one", "them", "มัน", "อันนี้", "งานนี้", "นี้"}
# A place is named: "trip to Chiang Mai", "hotel in Penang", "ไปเชียงใหม่", "ที่ภูเก็ต"
# (เที่ยว contains ที่, so that one is skipped; "เที่ยวเชียงใหม่" names the place right after เที่ยว)
PLACE = re.compile(r"\b(to|in|at)\s+[A-Z]|(?<!เ)ที่\S|ไป(?!เที่ยว)\S|เที่ยว(?!บิน)\S")
TRIP_DETAILS = re.compile(r"Trip details:|รายละเอียดทริป:")  # the line the page saves after asking


def add_task(s: str, now: str, categories: list) -> dict:
    return finish_add(parse_task(s, now, categories), s)


def finish_add(task: dict, s: str) -> dict:
    time = task.pop("time")  # only updates need it...
    if not task["due"] and ask_words(s):
        # ...and "When?": "meeting with Tom at 3pm" has a time but no day. The page asks for the day
        # and uses this time (or the owner's morning time).
        task["askWhen"] = True
        task["time"] = time or load_memory()["times"]["morning"]
    return {"action": "add", **task, "path": "ai"}


def add_without_ai(s: str) -> dict:
    """At the daily AI limit: the task as typed, but Python still asks "When?" for meetings/trips."""
    text = ADD_WORDS.sub("", " ".join(s.split())).strip() or s
    result = {"action": "add", "text": text[:1].upper() + text[1:], "due": "", "priority": "med", "category": "", "tokens": 0}
    if ask_words(text):
        result.update(askWhen=True, time=thai_time(text.lower()) or load_memory()["times"]["morning"])
    return result


def breakdown_questions(text: str, notes: str, due: str) -> list:
    """Before Break it down on a trip/event task: which details are missing? [] = just suggest."""
    if not ask_words(text) or TRIP_DETAILS.search(notes):
        return []
    both = f"{text} {notes}"
    missing = []
    if not PLACE.search(both):
        missing.append("where")
    if not due and not DAY_HINTS.search(fix_date_typos(both).lower()):
        missing.append("when")
    return missing + ["budget"] if missing and TRAVEL_WORDS.search(text) else missing


# ---------- "Ask Max": questions about the owner's tasks ----------
# Python recognises a question, reads the filter and counts (exact). The AI is only a fallback
# that sorts an unclear question into the same filter; it never writes the answer.
# The tools below (list_tasks, count_tasks) are small on purpose: a future Max agent can call them by name.
QUESTION_START = re.compile(r"^(what|what's|whats|which|show|list|how many|how much|anything|any|is there|are there|"
                            r"do i have|have i got|tell me|give me)\b")
# "Hi max, what to do today" / "hey max add milk": a greeting or "Max," in front is not part of the sentence.
# "max" alone only counts with a comma/colon ("Max birthday gift" is a task). \b is not used for Thai words.
GREETING = re.compile(r"^\s*(?:(?:hi|hey|hello|yo|ok|okay|good\s+(?:morning|afternoon|evening))(?=[\s,!.]|$)[\s,!.]*(?:max(?=[\s,!.:]|$)[\s,!.:]*)?"
                      r"|morning(?=\s+max(?:[\s,!.:]|$))[\s,!.]*(?:max[\s,!.:]*)?"   # "morning max" (plain "morning run" is a task)
                      r"|max\s*[,:!]\s*"
                      r"|(?:สวัสดี|หวัดดี|โอเค|อรุณสวัสดิ์)(?:ครับ|ค่ะ|คะ)?\s*(?:max|แม็กซ์|แม็ก)?\s*(?:ครับ|ค่ะ|คะ)?[\s,!]*"
                      r"|(?:แม็กซ์|แม็ก)(?:ครับ|ค่ะ|คะ)?\s*[,:!]?\s*)", re.I)
# Natural ways to ask about the day that have no task word in them
NATURAL_Q = re.compile(r"\bwhat (?:to do|should i|shall i|do i (?:have|need|got)|am i (?:doing|supposed)|have i got|else)\b"
                       r"|\bwhat(?:'s| is) (?:my|on|the plan)\b|\bwhats (?:my|on)\b"
                       r"|^my (?:tasks?|to-?dos?|plan|day|schedule)\b|ทำอะไรดี|ต้องทำ|ทำอะไร")
# The loose "maybe a question" gate: a question word anywhere, a "?", or a greeting. Only then is the AI asked.
QUESTION_WORD_ANYWHERE = re.compile(r"\b(what|how|which|should|when|where|who|why|anything)\b|อะไร|ไหม|มั้ย|กี่|ยังไง|ไร")
ORDER_START = re.compile(r"^(show|list|tell me|give me)\b")  # also normal verbs ("show Tom the report"): stricter
QUESTION_TH = re.compile(r"มีอะไร|อะไรบ้าง|กี่งาน|งานอะไร|งานค้าง|เลยกำหนด|เกินกำหนด|^แสดง")
TASK_WORDS = re.compile(r"\b(tasks?|to-?dos?|left|remaining|pending|outstanding|open|have)\b|งาน")
ABOUT = re.compile(r"(?:about|regarding|containing|เกี่ยวกับ|เรื่อง)\s*(.+?)"
                   r"(?=\s+(?:due|today|tomorrow|this|next|on|by|before|overdue|high|urgent|in)\b|วันนี้|พรุ่งนี้|สัปดาห์|อาทิตย์|[?.!]|$)")
ORDINAL_DAY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b|วันที่\s*(\d{1,2})")
EMPTY_FILTER = {"when": "", "date": "", "priority": "", "cat": "", "status": "open", "text": ""}
# What the AI may answer when it sorts an unclear question (checked again by Python)
QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "is_question": {"type": "boolean"},
        "chat": {"type": "boolean"},
        "reply": {"type": "string"},
        "when": {"type": "string", "enum": ["none", "today", "tomorrow", "week", "nextweek", "overdue", "nodate"]},
        "priority": {"type": "string", "enum": ["any", "high", "low"]},
        "status": {"type": "string", "enum": ["open", "done"]},
    },
    "required": ["is_question", "chat", "reply", "when", "priority", "status"],
}
QUESTION_INSTRUCTIONS = (
    "You sort a sentence typed in a to-do app. is_question is true only if the user asks about their own tasks "
    "(what is due, what is late, how many are left) or asks what to do or which to do first. "
    "A new task to remember is NOT a question; a sentence that tells what to do, buy or pay is a task. "
    "chat is true if the sentence is only small talk to you, the assistant (a compliment, thanks, hello, how are you, "
    "a remark): then reply is ONE short friendly sentence, max 80 characters, in the same language as the user, "
    "no emoji, and you invite them to give a task. Otherwise chat is false and reply is empty. "
    "when: today, tomorrow, week (this week), nextweek, overdue, nodate (tasks without a date), or none. "
    "priority: high, low or any. status: open (default) or done. Never answer the question."
)


def next_weekday_named(low: str, today):
    """'what to do next friday' / 'วันศุกร์หน้า' -> the first such weekday strictly after today ('' if not said).
    Same meaning as the add-task road (resolve_due), so a Friday asking for "next friday" gets +7 days."""
    m = re.search(r"\bnext\s+(" + "|".join(d.lower() for d in WEEKDAYS) + r")\b", low)
    if m:
        name = m.group(1).capitalize()
    else:
        m = re.search(r"(?:วัน)?(จันทร์|อังคาร|พุธ|พฤหัส|ศุกร์|เสาร์)(?:บดี)?หน้า|(วันอาทิตย์)หน้า", low)
        if not m:
            return ""
        name = THAI_WEEKDAYS[m.group(1) or m.group(2)]
    return weekday_date(name, today, after=True).isoformat()


# Day words a question may contain that the filter cannot use (a month, "yesterday", "5 nov")
UNREAD_DAY = re.compile(r"yesterday|\blast (week|month)|\bmonth\b|\d{1,2}/\d{1,2}|"
                        r"(jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d|\d\s*(jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)|"
                        r"เมื่อวาน|เดือน")


def question_filter(low: str, now: datetime, categories: list) -> dict:
    """Read the filter out of a lower-case question: when, priority, category, done/open, text."""
    f = dict(EMPTY_FILTER)
    today = now.date()
    names = list(dict.fromkeys(list(categories) + DEFAULT_CATEGORIES))  # known category names
    day_words = special_day(low) or ({"when": "in_days", "in_days": days_ahead(low)} if days_ahead(low) else {})
    # "anything about rent due this week": the words after "about" are a text search
    m = ABOUT.search(low)
    if m:
        f["text"] = m.group(1).strip(" ?.!")
        low = low[:m.start()] + " " + low[m.end():]
        if f["text"] in [n.lower() for n in names]:  # "about work" means the category Work
            f["cat"], f["text"] = f["text"], ""
    if re.search(r"overdue|\blate\b|past due|เลยกำหนด|เกินกำหนด|งานค้าง|ค้างอยู่", low):
        f["when"] = "overdue"
    elif re.search(r"no (due )?date|without (a )?(due )?date|undated|ไม่มีวันที่|ไม่มีกำหนด", low):
        f["when"] = "none"
    elif re.search(r"day after tomorrow|มะรืน", low):  # before "tomorrow": the first words contain it
        f["when"], f["date"] = "date", (today + timedelta(days=2)).isoformat()
    elif next_weekday_named(low, today):
        f["when"], f["date"] = "date", next_weekday_named(low, today)
    elif day_words.get("special") == "weekend":
        f["when"] = "weekend"
    elif day_words:  # "in 3 days", "in 2 weeks", "end of month": Python counts the date
        f["when"], f["date"] = "date", resolve_due(day_words, now)[:10]
    elif re.search(r"next week|สัปดาห์หน้า|อาทิตย์หน้า", low):
        f["when"] = "nextweek"
    elif re.search(r"\bweek\b|สัปดาห์นี้|อาทิตย์นี้", low):
        f["when"] = "week"
    elif re.search(r"tomorrow|พรุ่งนี้", low):
        f["when"] = "tomorrow"
    elif re.search(r"\btoday\b|\btonight\b|วันนี้|คืนนี้", low):
        f["when"] = "today"
    elif weekday_in(low):
        f["when"], f["date"] = "date", weekday_date(weekday_in(low), today).isoformat()
    elif ORDINAL_DAY.search(low):
        day = int(next(g for g in ORDINAL_DAY.search(low).groups() if g))
        for add in (0, 1):  # this month if the day hasn't passed, else next month
            try:
                date = add_months(now.replace(day=1), add).replace(day=day).date()
            except ValueError:
                continue
            if date >= today:
                f["when"], f["date"] = "date", date.isoformat()
                break
    if not f["when"] and UNREAD_DAY.search(low):
        f["unread"] = True   # a day we cannot read: say so, never list everything as if it answered
    if re.search(r"\b(high|urgent|important|asap)\b|ด่วน|สำคัญ", low):
        f["priority"] = "high"
    elif re.search(r"\blow\b|ไม่รีบ", low):
        f["priority"] = "low"
    if re.search(r"\b(done|completed|finished)\b|เสร็จแล้ว", low):
        f["status"] = "done"
    for name in names:
        if not f["cat"] and re.search(r"(?<!\w)" + re.escape(name.lower()) + r"(?!\w)", low):
            f["cat"] = name.lower()
    return f


def strip_greeting(sentence: str):
    """('Hi max, what to do today') -> ('what to do today', True). Only a greeting alone is kept as it is."""
    rest = GREETING.sub("", sentence, count=1).strip()
    return (rest, True) if rest and rest != sentence.strip() else (sentence, False)


# Small talk seed list: a tiny speed path (and the offline copy in script.js SMALL_TALK). Only a whole short
# sentence matches, so "thank Olive for the gift tomorrow" stays a task. Everything else is left to the AI (chat label).
_MAX = r"(?:\s+max)?"
SMALL_TALK = {
    "compliment": re.compile(r"^(?:you|u)(?:'re| are|re)?\s+(?:so |really )?(?:smart|great|awesome|amazing)" + _MAX + r"$"
                             r"|^(?:คุณ)?เก่ง(?:มาก|จัง)?ๆ?(?:ครับ|ค่ะ|คะ|นะ)*$"),
    "thanks": re.compile(r"^(?:thanks|thank you|thx|ty)(?: so much| a lot)?" + _MAX + r"$"
                         r"|^ขอบคุณ(?:มาก)?ๆ?(?:ครับ|ค่ะ|คะ|นะ)*$"),
}


def small_talk(sentence: str):
    """'You are so smart' -> 'compliment' (also 'thanks'); anything else -> None."""
    plain = strip_greeting(sentence)[0]
    low = " ".join(plain.replace("’", "'").lower().split()).rstrip(" !.?,")
    for kind, pattern in SMALL_TALK.items():
        if pattern.match(low):
            return kind
    return None


# The AI's own friendly reply to chit-chat: one short plain line. Python cleans it (the page shows it as text only).
def clean_reply(reply) -> str:
    text = " ".join(str(reply or "").split())
    text = "".join(c for c in text if ord(c) < 0x2190 or 0x0E00 <= ord(c) <= 0x0E7F)  # no emoji / symbols
    text = text.replace("<", "").replace(">", "").strip()
    return text if 0 < len(text) <= 80 else ""  # too long or empty: the page uses its own friendly line


# Used when the AI's reply is empty, in the wrong language or off-topic ("how are you" -> "You are welcome!")
CHAT_FALLBACK = {"en": "Happy to chat! Give me a task, or ask what is due.",
                 "th": "ยินดีคุยด้วยครับ! บอกงานให้ผมได้เลย หรือถามว่ามีอะไรต้องทำ"}


def chat_reply(reply, sentence: str) -> str:
    """The AI's friendly line, checked by Python. Never empty: a short fallback line in the owner's language."""
    text = clean_reply(reply)
    thai = bool(THAI_LETTERS.search(sentence))
    if thai and not THAI_LETTERS.search(text):
        text = ""   # the 3B model sometimes answers Thai in English
    if re.search(r"welcome", text, re.I) and not re.search(r"thank|thx|ขอบคุณ", sentence, re.I):
        text = ""   # "You are welcome!" only answers a thank-you
    return text or CHAT_FALLBACK["th" if thai else "en"]


def parse_question(sentence: str, now: str, categories: list):
    """The filter if the sentence is a question about the tasks, else None (then it is a normal command)."""
    raw = " ".join(strip_greeting(sentence)[0].split()).lower()
    if re.search(r"#\s*\d", raw):
        return None  # "#3" always means a command
    if not (QUESTION_START.match(raw) or raw.endswith("?") or QUESTION_TH.search(raw) or NATURAL_Q.search(raw)):
        return None
    # Typos are fixed only for the filter ("tomorow"); the fixer would turn "many" into "may"
    low = fix_date_typos(raw)
    f = question_filter(low, datetime.strptime(now[:16], "%Y-%m-%dT%H:%M"), categories)
    something = f["when"] or f.get("unread") or f["priority"] or f["cat"] or f["text"] or f["status"] == "done"
    if ORDER_START.match(low):
        # "show Tom the report tomorrow" is a task; "show high priority work" is a question
        return f if TASK_WORDS.search(raw) or f["priority"] or f["cat"] or f["when"] == "overdue" else None
    return f if something or TASK_WORDS.search(raw) or NATURAL_Q.search(raw) else None


CHAT_ADDRESSED = re.compile(r"^(?:you|u|your)\b|^คุณ")
TASK_VERBS = re.compile(r"\b(?:buy|pay|call|send|book|fix|finish|get|clean|write|email|text|pick|order|renew|submit|"
                        r"cancel|schedule|make|take|bring|return|print|check|prepare|review|plan|visit|wash|cook)\b|"
                        r"ซื้อ|จ่าย|โทร|ส่ง|จอง|ซ่อม|ทำ|เก็บ|ล้าง|นัด|ยกเลิก|เตรียม|ไป")


def maybe_chat(low: str) -> bool:
    """Could this be small talk? Short, no date/time, no clear task verb, or it talks to Max ("you ...", "คุณ...")."""
    if re.search(r"\d", low) or re.search(THAI_DATE_WORDS, low) or any(
            w in DATE_WORDS or w in SHORTCUTS or w in SHORT_DAYS or w in [d.lower() for d in WEEKDAYS]
            for w in re.findall(r"[a-z]+", low)):
        return False
    if CHAT_ADDRESSED.search(low):
        return True
    if TASK_VERBS.search(low):
        return False
    thai = bool(re.search(r"[฀-๿]", low))
    # one-word tasks ("Laundry") must stay fast, so English needs 2+ words; Thai has no spaces: 5-20 letters
    return 5 <= len(low) <= 20 if thai else 2 <= len(low.split()) <= 6


def maybe_question(low: str, greeted: bool) -> bool:
    """The loose gate: worth one AI call to decide? Clear commands and clear tasks ("pay rent on the 5th") are not."""
    if re.search(r"#\s*\d", low) or any(re.search(p, low) for p in (UNDO_WORDS, DELETE_WORDS, DONE_WORDS, UPDATE_WORDS)):
        return False
    return greeted or low.endswith("?") or bool(QUESTION_WORD_ANYWHERE.search(low)) or maybe_chat(low)


def ai_question_filter(sentence: str, rules: dict = None):
    """Fallback for an unclear question: the small AI only sorts it into the filter (checked here).
    rules: what Python's own word rules found; the AI never overrides those."""
    try:
        r = parse_with_ollama(f"Sentence: {sentence}", QUESTION_INSTRUCTIONS, QUESTION_SCHEMA, timeout=20)
    except Exception:
        return None  # no AI: treat the sentence as a normal task
    if r.get("chat") is True and r.get("is_question") is not True:
        return {"chat": True, "reply": chat_reply(r.get("reply"), sentence), "tokens": r.get("tokens", 0)}
    if r.get("is_question") is not True:
        return None
    f = dict(EMPTY_FILTER)
    f.update(rules or {})
    ai_when = {"today": "today", "tomorrow": "tomorrow", "week": "week", "nextweek": "nextweek",
               "overdue": "overdue", "nodate": "none"}.get(r.get("when"), "")
    # Python checks the AI's guess: a day or priority the owner never hinted at is dropped (the 3B model invents them)
    said = sentence.lower()
    if not re.search(r"today|tonight|tomorrow|week|overdue|late|forgot|missed|behind|date|วัน|สัปดาห์|อาทิตย์|ค้าง", said):
        ai_when = ""
    ai_priority = r.get("priority") if r.get("priority") in ("high", "low") and \
        re.search(r"urgent|important|high|low|priority|asap|ด่วน|สำคัญ|ไม่รีบ", said) else ""
    f["when"] = f["when"] or ai_when  # Python's own reading wins
    f["priority"] = f["priority"] or ai_priority
    f["status"] = "done" if f["status"] == "done" or r.get("status") == "done" else "open"
    f["tokens"] = r.get("tokens", 0)
    return f


def due_range(f: dict, now: datetime):
    """The first and last day (YYYY-MM-DD) a filter's date part covers."""
    today = now.date()
    if f["when"] == "today":
        return today.isoformat(), today.isoformat()
    if f["when"] == "tomorrow":
        day = (today + timedelta(days=1)).isoformat()
        return day, day
    if f["when"] == "week":  # today until Sunday
        return today.isoformat(), (today + timedelta(days=6 - today.weekday())).isoformat()
    if f["when"] == "weekend":  # the coming Saturday and Sunday (on a weekend: today until Sunday)
        saturday = today + timedelta(days=max(5 - today.weekday(), 0))
        return saturday.isoformat(), (today + timedelta(days=6 - today.weekday())).isoformat()
    if f["when"] == "nextweek":  # next Monday until next Sunday
        monday = today + timedelta(days=7 - today.weekday())
        return monday.isoformat(), (monday + timedelta(days=6)).isoformat()
    return f["date"], f["date"]


# ----- Tools: small, exact functions (a future Max agent can call these by name) -----
def list_tasks(tasks: list, f: dict, now: datetime) -> list:
    """Tasks that match the filter, soonest first. A task is {num, text, done, due, priority, cat}."""
    now_text = now.strftime("%Y-%m-%dT%H:%M")
    first, last = due_range(f, now) if f["when"] in ("today", "tomorrow", "week", "weekend", "nextweek", "date") else ("", "")
    found = []
    for t in tasks:
        due = t.get("due", "")
        if bool(t.get("done")) != (f["status"] == "done"):
            continue
        if f["priority"] and t.get("priority", "med") != f["priority"]:
            continue
        if f["cat"] and t.get("cat", "").lower() != f["cat"].lower():
            continue
        if f["text"] and f["text"].lower() not in t["text"].lower():
            continue
        if f["when"] == "none" and due:
            continue
        if f["when"] == "overdue" and not (due and due < now_text):
            continue
        if first and not (due and first <= due[:10] <= last):
            continue
        found.append(t)
    return sorted(found, key=lambda t: (t.get("due") or "9999", t["num"]))


def count_tasks(tasks: list, f: dict, now: datetime) -> int:
    return len(list_tasks(tasks, f, now))


TOOLS = {"list_tasks": list_tasks, "count_tasks": count_tasks}


def question_answer(sentence: str, now: str, categories: list, tasks: list, use_ai: bool = True):
    """The answer-card data if the sentence is a question, else None. Questions never add tasks."""
    plain, greeted = strip_greeting(sentence)
    f = parse_question(plain, now, categories)
    low = " ".join(plain.split()).lower()
    if f is None and use_ai and maybe_question(low, greeted):
        # Python's own reading of the words (filter only) is kept; the AI just decides "question or not"
        f = ai_question_filter(plain, question_filter(fix_date_typos(low), datetime.strptime(now[:16], "%Y-%m-%dT%H:%M"), categories))
    if f is None:
        return None
    if f.get("chat"):  # the AI says it is small talk: a friendly reply, no task
        return {"action": "smalltalk", "kind": "chat", "reply": f["reply"], "tokens": f["tokens"]}
    if f.pop("unread", False):  # honest answer instead of a list that only looks like an answer
        thai = re.search(r"[฀-๿]", sentence)
        return {"action": "smalltalk", "kind": "chat", "tokens": f.get("tokens", 0),
                "reply": "ขอโทษครับ อ่านวันนั้นไม่ออก ลองถามว่า วันนี้ พรุ่งนี้ สัปดาห์นี้ หรือชื่อวันดูนะ" if thai else
                         "Sorry, I couldn't read that day. Try today, tomorrow, this week or a weekday."}
    tokens = f.pop("tokens", 0)
    found = TOOLS["list_tasks"](tasks, f, datetime.strptime(now[:16], "%Y-%m-%dT%H:%M"))
    return {"action": "answer", "filter": f, "nums": [t["num"] for t in found], "tokens": tokens}


# ---------- One AI call that understands the whole sentence (job 0h) ----------
# The AI only reads the language (what kind of sentence, which words name a task); Python does every exact part:
# dates, #numbers (regex only), finding the task, the question filter, and the safety checks below.
INTENTS = ["add", "change", "done", "undo", "delete", "question", "chat"]
UNDERSTAND_SCHEMA = {
    "type": "object",
    "properties": {   # the task fields come FIRST: the title and dates were better when the AI wrote them before the intent
        **TASK_SCHEMA["properties"],
        "intent": {"type": "string", "enum": INTENTS},
        "target": {"type": "string"},
        "change": {"type": "string"},
        "reply": {"type": "string"},
    },
    "required": TASK_SCHEMA["required"] + ["intent", "target", "change", "reply"],
}
UNDERSTAND_INSTRUCTIONS = INSTRUCTIONS + (
    "\nFirst decide intent. add = a new task to remember: the default, and a sentence that just names something to do "
    "is add, even with a day or time. Use another intent ONLY when the sentence clearly talks about a task that already "
    "exists: change (rename it, new day or time, priority, category), done (it is finished), undo (it is not finished "
    "after all), delete (remove it), question (asks about the user's own tasks), chat (small talk to you, the assistant).\n"
    "target: for change/done/undo/delete, the words from the sentence that name the existing task, else \"\".\n"
    "change: for change, the new value in the user's own words (a day, a time, a new name, a priority), else \"\".\n"
    "reply: only for chat, ONE short friendly sentence (max 80 characters) in the language of the user, no emoji, "
    "that invites them to give a task; else \"\". Always fill text, whatever the intent."
)


def _example(sentence: str, **fields) -> str:
    """One extra example line in the same shape as EXAMPLES, with the new fields."""
    row = {"text": "", "priority": "med", "category": "", "when": "none", "in_days": 0, "weekday": "", "next_week": False,
           "day": 0, "month": 0, "next_month": False, "time": "", "intent": "add", "target": "", "change": "", "reply": ""}
    row.update(fields)
    return f'"{sentence}" -> ' + json.dumps(row, ensure_ascii=False, separators=(",", ":"))


# The task examples get the new fields; a few more show the other kinds of sentence
UNDERSTAND_EXAMPLES = "\n".join(
    [line[:-1] + ',"intent":"add","target":"","change":"","reply":""}' if "-> {" in line else line
     for line in EXAMPLES.split("\n")] + [
        _example("finished the tax form", intent="done", target="tax form", text="Tax form"),
        _example("ทำการบ้านเสร็จแล้ว", intent="done", target="การบ้าน", text="การบ้าน"),
        _example("postpone the haircut to next monday", intent="change", target="haircut", change="next monday",
                 text="Haircut", when="weekday", weekday="Monday", next_week=True),
        _example("remove the gym task", intent="delete", target="gym", text="Gym"),
        _example("what is due on friday?", intent="question", text="What is due on friday"),
        _example("you are funny", intent="chat", text="You are funny", reply="Thank you! What shall we add to your list?"),
    ])

# The command words Python needs to SEE in the sentence before it deletes, finishes or edits a task for the AI.
# Anywhere in the sentence (the rules road wants them first); "finish the report" and "cancel dentist" stay tasks.
DONE_ANY = re.compile(r"\b(done|finished|completed)\b|เสร็จ|แล้ว$")
UNDO_ANY = re.compile(r"\b(undo|undone|uncheck|unmark|reopen|not done|not finished)\b|ยังไม่เสร็จ")
DELETE_ANY = re.compile(r"\b(delete|remove|erase|del|cancel)\b|ลบ|ยกเลิก(?!เสร็จ)")
CHANGE_ANY = re.compile(r"\b(change|modify|move|rename|edit|update|reschedule|postpone|push|delay)\b|เปลี่ยน|แก้|ย้าย|เลื่อน")
INTENT_WORDS = {"done": DONE_ANY, "undo": UNDO_ANY, "delete": DELETE_ANY, "change": CHANGE_ANY}
INTENT_ACTION = {"done": "complete", "undo": "uncomplete", "delete": "delete", "change": "update"}


def understand(s: str, now: str, categories: list, tasks: list, greeted: bool = False, rules_result: dict = None):
    """One AI call, then Python checks. Returns the result dict, or None = "not sure, use the old road".
    rules_result: Python already read a command but could not find the task (the AI's target may help)."""
    sentence = clean_sentence(s)
    prompt, known, memory = ai_prompt(sentence, categories, UNDERSTAND_EXAMPLES)
    r = parse_with_ollama(prompt, UNDERSTAND_INSTRUCTIONS, UNDERSTAND_SCHEMA, timeout=60)
    as_new = lambda: finish_add(check_task(dict(r), sentence, now, known, memory), s)   # the card's "Add as new task" button
    tokens = r.get("tokens", 0)
    low = " ".join(s.split()).lower()   # the owner's raw words (fix_date_typos would turn "many" into "may")
    intent = r.get("intent") if r.get("intent") in INTENTS else "add"
    asked = maybe_question(low, greeted)   # the old gate is now only a CHECK: the AI cannot turn a plain task into a question

    if intent == "chat" and asked:
        return {"action": "smalltalk", "kind": "chat", "reply": chat_reply(r.get("reply"), s), "tokens": tokens}
    if intent == "question" and asked:
        f = question_filter(fix_date_typos(low), datetime.strptime(now[:16], "%Y-%m-%dT%H:%M"), categories)
        found = TOOLS["list_tasks"](tasks, f, datetime.strptime(now[:16], "%Y-%m-%dT%H:%M"))
        return {"action": "answer", "filter": f, "nums": [t["num"] for t in found], "tokens": tokens}

    if intent in INTENT_WORDS and INTENT_WORDS[intent].search(low):
        action, target = INTENT_ACTION[intent], " ".join(str(r.get("target") or "").split())
        target = target or low   # the AI named nothing: look for a task word anywhere in the sentence
        # By name, "undo" can only mean a done task and "done" an open one; only Python matches the words to a real task
        wanted = {"undo": True, "done": False, "change": False}.get(intent)
        pool = tasks if wanted is None else [t for t in tasks if t.get("done") is wanted]
        num, choices = find_task_loose(target, pool)
        by_name = not re.search(r"#\s*\d", low)   # a #number is exact: no card
        if num is None and target == low and rules_result is not None:
            # no task named: the page asks "Which task?"
            return (pick_card(action, tasks) | {"tokens": tokens}) if action != "update" else {"action": action, "pickTask": True, "tokens": tokens}
        if num is None and choices and by_name and action in ("complete", "delete"):
            return clarify("similar", choices, plain_do(action)) | {"tokens": tokens}   # "done call": which of the Call tasks?
        if num is None and target != low:
            return {"action": action, "missing": target, "choices": choices, "tokens": tokens}
        # (num is None and target == low: Python read no command and the AI named no task, "change car to garage": a new task, below)
        if num is not None and intent != "change":
            if intent in ("done", "delete") and by_name:
                # The AI found the task, but the owner did not say "done X" first: ask, never guess
                return clarify(intent, [num], plain_do(action), as_new()) | {"tokens": tokens}
            return {"action": action, "num": num, "tokens": tokens}
        if num is not None:
            change = " ".join(str(r.get("change") or "").split())
            if not (by_name and weak_name_match(num, target, change, tasks)):
                done = work_out_changes(num, change, "", False, low, tasks, now, categories, ai_task=r)
                done["tokens"] = done.get("tokens", 0) + tokens
                done["path"] = "ai"
                if not (by_name and done.get("nothing")):
                    if by_name:   # "move the rent car thing to monday": the changes are ready, one click applies them
                        return clarify("change", [num], lambda n: {"action": "update", "num": n, "changes": done["changes"]},
                                       as_new()) | {"tokens": done["tokens"]}
                    return done
            # else: no clear task / nothing to change: a command word without a #number is a new task (below)

    if rules_result is not None and re.search(r"#\s*\d", low):
        return None   # "done #99": keep Python's "can't find #99". Without a #number, a command word that matches no task
        #               ("Mark's birthday gift friday", "Move car to garage") is just a new task
    # (an intent the sentence has no command words for is still a plain task: its fields are already filled)
    return finish_add(check_task(r, sentence, now, known, memory), s) | {"path": "ai"}


# ---------- Max asks before he guesses (job 0q-1) ----------
# One card shape for every "are you sure what you meant?" moment. Nothing is saved until the owner clicks an option;
# every option carries its complete "do" (the same dict run_command would have returned), so a click needs no 2nd AI call.
# Python decides WHEN (a real candidate task AND a command word); plain new tasks never get a card.
def plain_do(action: str):
    """The "do" for one task: done / delete / reopen / edit. A delete click IS the confirmation."""
    return lambda num: {"action": action, "num": num, **({"confirmed": True} if action == "delete" else {})}


def clarify(case: str, nums: list, make_do, add_do: dict = None) -> dict:
    """case: done | delete | change | similar | pick. At most 3 tasks, safest first, then "Add as new task"."""
    nums = nums[:3]
    options = [{"label": "opt_" + make_do(n)["action"], "num": n, "do": make_do(n)} for n in nums]
    if add_do:
        options.append({"label": "opt_add", "do": add_do})
    # The page writes the sentences from its own text table (EN/TH); "more" is for "Tell Max more…" (0q-2)
    return {"action": "clarify", "case": case, "id": uuid.uuid4().hex[:8], "q": "clarifyQ_" + case,
            "nums": nums, "options": options, "more": True}


def pick_card(action: str, tasks: list) -> dict:
    """No task named ("cancel", "done it"): offer the 3 newest tasks that fit. "move" opens the editor of the pick."""
    nums = sorted((t["num"] for t in tasks if bool(t.get("done")) is (action == "uncomplete")), reverse=True)
    if not nums:
        return {"action": action, "pickTask": True}   # nothing to pick from: the page says "no tasks"
    return clarify("pick", nums, plain_do("edit" if action == "update" else action))


BARE_FILLER = re.compile(r"\b(it|this|that|task|the)\b|อันนี้|งานนี้|มัน|นี้")


def bare_action(text: str) -> str:
    """"cancel", "move it", "ลบ": only a command word and nothing else -> its action ("" = not a bare command)."""
    rest = BARE_FILLER.sub(" ", " ".join(text.lower().split())).strip(" .,!?")
    if not rest or re.search(r"\d", rest):
        return ""
    for intent in ("undo", "done", "delete", "change"):   # undo first: "ยกเลิกเสร็จ" must not read as delete
        if INTENT_WORDS[intent].search(rest) and not INTENT_WORDS[intent].sub("", rest).strip(" .,!?"):
            return INTENT_ACTION[intent]
    return ""


def guard_bare_add(result: dict, tasks: list) -> dict:
    """Safety net: if the AI still turned a lone command word into a task ("Cancel", "Move"), ask "Which task?" instead."""
    action = bare_action(result.get("text", "")) if result.get("action") == "add" else ""
    return (pick_card(action, tasks) | {"tokens": result.get("tokens", 0)}) if action else result


def run_command(sentence: str, now: str, categories: list, tasks: list, chosen: int = None) -> dict:
    """Same as work_out_command, but every result says which road it took: "rules" (Python alone) or "ai"."""
    result = guard_bare_add(work_out_command(sentence, now, categories, tasks, chosen), tasks)
    result.setdefault("path", "ai" if result.get("tokens") else "rules")  # AI calls report their tokens
    return result


def work_out_command(sentence: str, now: str, categories: list, tasks: list, chosen: int = None) -> dict:
    """Work out what the sentence wants: add a task, or change/delete/complete an existing one.
    chosen: the #number the owner picked after Max asked "Which one?" (None normally)."""
    s = " ".join(sentence.split())
    kind = small_talk(s)
    if kind:
        return {"action": "smalltalk", "kind": kind}  # a friendly reply, no task, no AI call
    one_call = ONE_CALL and AI_PROVIDER == "ollama" and chosen is None
    # A question about the tasks: answer it, add nothing. One-call mode: only Python-clear questions here,
    # the unclear ones are decided by the single AI call below
    answer = question_answer(s, now, categories, tasks, use_ai=not one_call)
    if answer:
        return answer
    if GREETING.match(s) and not GREETING.sub("", s, count=1).strip():
        return {"action": "greeting"}  # just "hi max": the page says hello, no task is added
    greeted = strip_greeting(s)[1]
    s = strip_greeting(s)[0]  # "hey max add milk tomorrow" is the command "add milk tomorrow"
    if chosen is None and bare_action(s):
        return pick_card(bare_action(s), tasks)   # just "cancel" / "move": ask which task, no AI call
    result = command_by_rules(s, now, categories, tasks, chosen)
    if chosen is None and result and result["action"] != "update":   # no task named / several fit: a card instead of the old two-step
        if result.get("pickTask"):
            return pick_card(result["action"], tasks)
        if result.get("choices"):
            return clarify("similar", result["choices"], plain_do(result["action"]))
    if chosen is None and result and result.pop("fuzzy", False):
        # A command-word-first match that is only close ("move the rent car thing to monday"): one click, "Add as new" costs no AI call
        if result["action"] == "update":
            return clarify("change", [result["num"]], lambda n: {"action": "update", "num": n, "changes": result["changes"]}, add_without_ai(s))
        if result["action"] in ("complete", "delete"):
            return clarify("done" if result["action"] == "complete" else "delete", [result["num"]], plain_do(result["action"]), add_without_ai(s))
    if not one_call:
        return result or add_task(s, now, categories)
    if result is not None and "missing" not in result:
        return result  # a clear command Python read alone: no AI
    # Everything else: ONE AI call that understands the whole sentence, then Python checks it
    return understand(s, now, categories, tasks, greeted, result) or result or add_task(s, now, categories)


# Other ways to say #3 (only used once a command word is there, so "buy item 3" stays a task)
NUMBER_FORMS = re.compile(r"(?:ข้อที่|ข้อ|งานที่|งานข้อ|\bno\.?|\bnumber|\btask|\bitem)\s*(\d+)", re.I)


def command_by_rules(s: str, now: str, categories: list, tasks: list, chosen: int = None):
    """Python's own reading of a command (done/undo/delete/change). None = no command words: it is a new task."""
    # "#9 rename to milk" means the same as "rename #9 to milk": put the action word first
    number_first = re.match(r"(#\s*\d+)\s*(.+)", s)
    if number_first and any(re.match(p, number_first.group(2).lower())
                            for p in (UNDO_WORDS, DELETE_WORDS, DONE_WORDS, UPDATE_WORDS)):
        s = f"{number_first.group(2)} {number_first.group(1)}"
    low = s.lower()
    if re.search(UNDO_WORDS, low):
        action = "uncomplete"
    elif re.search(DELETE_WORDS, low):
        action = "delete"
    elif re.search(DONE_WORDS, low):
        action = "complete"
    elif re.search(UPDATE_WORDS, low) or re.match(r"#\s*\d+", low):
        action = "update"
    else:
        return None

    s = NUMBER_FORMS.sub(r"#\1", s)   # "ข้อ 3", "no. 3", "number 3" all mean #3
    # Remove the action words, keep what's left
    rest = s
    for pattern in (UNDO_WORDS, DELETE_WORDS, DONE_WORDS, UPDATE_WORDS):
        if re.search(pattern, low):
            rest = re.sub(pattern, " ", rest, count=2, flags=re.I)
    rename = bool(re.match(r"(rename|เปลี่ยนชื่อ)", low))

    num_match = re.search(r"#\s*(\d+)", rest)
    if num_match:
        rest = (rest[:num_match.start()] + " " + rest[num_match.end():])
    rest = strip_filler(rest)

    # "category of dentist to Health", "#4 priority high", "the date of #3 to friday"
    field = "text" if rename else ""
    field_match = re.match(r"(" + "|".join(sorted(FIELD_WORDS, key=len, reverse=True)) + r")\b\s*", rest, flags=re.I) \
        or re.match(r"(หมวดหมู่|หมวด|ความสำคัญ|วันที่|เวลา|ชื่อ)\s*", rest)
    # "rename #3 to date night" is a name, not the date field
    if action == "update" and field_match and (not rename or FIELD_WORDS[field_match.group(1).lower()] == "text"):
        field = FIELD_WORDS[field_match.group(1).lower()]
        rest = strip_filler(rest[field_match.end():])

    # Which task? A number, or the words before "to"/"เป็น" (or everything, for delete/done)
    if num_match:
        target, change = num_match.group(0), rest
    elif action == "update":
        parts = re.split(r"\s+to\s+|\s+(?=by\s+(?:\d|an?\b|one\b|two\b|three\b))|\s*(?:ให้เป็น|ไปเป็น|เป็น|ไปวัน|ไป)\s*", rest, maxsplit=1)
        if len(parts) < 2:
            if chosen:
                parts = ["", rest]  # the owner already picked the task: all of it is the change
            else:  # "set up the printer" is a new task, not a command
                return None
        target, change = strip_filler(parts[0]), strip_filler(parts[1])
    else:
        target, change = rest, ""
    if chosen and any(t["num"] == chosen for t in tasks):
        num, choices = chosen, []
    elif not num_match and target.lower() in PRONOUNS:
        return {"action": action, "pickTask": True}  # no task named: the page asks "Which task?"
    else:
        # By name, "undo" can only mean a done task and "done" an open one (a #number is always exact)
        wanted = {"uncomplete": True, "complete": False}.get(action)
        pool = tasks if num_match or wanted is None else [t for t in tasks if t.get("done") is wanted]
        num, choices = find_task(target, pool)
    if num is None:
        return {"action": action, "missing": target, "choices": choices}
    by_name = not num_match and not chosen
    # "fuzzy" = the words are not written inside the title ("lundry", "rent car thing"): work_out_command asks first
    fuzzy = by_name and target.lower().strip() not in next((str(t.get("text", "")).lower() for t in tasks if t["num"] == num), "")
    if action != "update":
        return {"action": action, "num": num} | ({"fuzzy": True} if fuzzy else {})

    if by_name and not field and weak_name_match(num, target, change, tasks):
        return None   # "move car to garage": one shared word is no clear match, so it is a new task
    result = work_out_changes(num, change, field, rename, low, tasks, now, categories)
    return None if by_name and result.get("nothing") else result | ({"fuzzy": True} if fuzzy else {})   # an update that changes nothing is never the answer


def weak_name_match(num: int, target: str, change: str, tasks: list) -> bool:
    """A name-only update ("move car to garage") that hangs on one word of a longer title, and whose change names no
    day, time or priority. Too risky to touch a task: the caller treats the sentence as a new task."""
    fixed = fix_date_typos(change).lower()
    if DAY_HINTS.search(fixed) or time_said(fixed) or BY_DAYS.match(fixed) or any(
            w in fixed.split() or (not w.isascii() and w in fixed) for w in PRIORITY_WORDS):
        return False
    text = next((str(t.get("text", "")).lower() for t in tasks if t["num"] == num), "")
    words = target.lower().strip()
    # clear = the target is at least half the title's letters ("laundry" / "Do laundry"), or shares 2+ words with it
    return len(words) * 2 < len(text) and len(set(words.split()) & set(text.split())) < 2


# "delay #3 by 2 days", "push #3 by a week", "เลื่อนข้อ 3 อีก 2 วัน": counted from the task's own day, not today
BY_DAYS = re.compile(r"(?:by\s+(?P<n>\d+|a|an|one|two|three)\s*(?P<unit>days?|weeks?)|(?:อีก\s*)?(?P<th>\d+)\s*(?P<thunit>วัน|สัปดาห์|อาทิตย์))$")
NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3}


def work_out_changes(num: int, change: str, field: str, rename: bool, low: str, tasks: list, now: str,
                     categories: list, ai_task: dict = None) -> dict:
    """What an update changes: only the fields the command mentions (day-only keeps the time, time-only keeps the day).
    ai_task: the AI's reading of the same sentence (one-call mode), so a hard date needs no second AI call."""
    action = "update"
    if not change:
        return {"action": action, "num": num, "nothing": True}
    changes, tokens, path = {}, 0, "rules"
    by = BY_DAYS.match(change.strip().lower())
    if by and not field and (by.group("n") or low.startswith("เลื่อน")):
        n = by.group("n") or by.group("th")
        count = int(n) if n.isdigit() else NUMBER_WORDS[n]
        if (by.group("unit") or by.group("thunit")).startswith(("week", "สัปดาห์", "อาทิตย์")):
            count *= 7
        old_due = next((t.get("due", "") for t in tasks if t["num"] == num), "")
        day = datetime.strptime((old_due or now)[:10], "%Y-%m-%d") + timedelta(days=count)
        return {"action": action, "num": num, "changes": {"due": day.strftime("%Y-%m-%d") + "T" + (old_due[11:16] or "09:00")},
                "tokens": 0, "path": "rules"}
    if field == "text":
        changes["text"] = change[:1].upper() + change[1:]
    elif field == "category":
        changes["category"] = change[:1].upper() + change[1:]
    else:
        words = [w for w in re.split(r"[\s,]+", change.lower()) if w]
        priority = next((PRIORITY_WORDS[w] for w in words if w in PRIORITY_WORDS), "") \
            or next((p for w, p in PRIORITY_WORDS.items() if not w.isascii() and w in change), "")
        if priority:
            changes["priority"] = priority
        left = [w for w in words if w not in PRIORITY_WORDS and w != "priority"]
        # "change #2 to call mom" = new name (also "#2 call mom"); "move" never renames
        renaming = not priority and field != "due" and \
            (re.match(r"(change|modify|edit|update|เปลี่ยน|แก้)", low) or re.match(r"#\s*\d+", low))
        fixed = fix_date_typos(change).lower()
        day, clock = bool(DAY_HINTS.search(fixed)), time_said(fixed)
        if field != "priority" and left and (day or clock or field == "due"):
            # Plain day/time words ("friday", "5pm", "tomorrow") Python reads alone; anything else asks the AI
            rules = rules_date(change, load_memory()["times"])
            if rules:
                parsed = {"due": resolve_due(rules, datetime.strptime(now[:16], "%Y-%m-%dT%H:%M"), load_memory()["times"]),
                          "time": rules["time"], "tokens": 0}
            elif ai_task:
                memory = load_memory()
                known = list(dict.fromkeys(categories + memory["categories"]))[:30]
                parsed = check_task(dict(ai_task), clean_sentence(change), now, known, memory)  # Python reads the change words
                path = "ai"
            else:
                parsed = parse_task(change, now, categories)  # the AI reads the date words
                path = "ai"
            tokens = parsed["tokens"]
            old_due = next((t.get("due", "") for t in tasks if t["num"] == num), "")
            due = parsed["due"]
            if clock and not day and parsed["time"]:
                # Only a time ("move #2 to 5pm"): keep the task's day (today if it had none)
                due = (old_due[:10] or now[:10]) + "T" + parsed["time"]
            elif due and not clock and old_due:
                due = due[:11] + old_due[11:]  # only a day ("move #2 to friday"): keep the task's time
            if due:
                changes["due"] = due
            elif renaming:
                changes["text"] = change[:1].upper() + change[1:]  # "buy sun cream": not a date after all
        elif field != "priority" and left and renaming:
            # No date or time words: a new name only, so the date stays exactly as it was
            changes["text"] = change[:1].upper() + change[1:]
        if not changes:
            return {"action": action, "num": num, "nothing": True, "tokens": tokens, "path": path}
    return {"action": action, "num": num, "changes": changes, "tokens": tokens, "path": path}


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Make the browser re-check files every time, so an old script.js never mixes with a new page
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_json(self, result, status=200):
        data = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def host_ok(self) -> bool:
        # Who is asking: only this PC or a Tailscale device (see TAILSCALE_NETS)
        if not client_ip_ok(self.client_address[0]):
            self.send_error(403, "Not allowed")
            return False
        # DNS-rebinding protection: a strange website can point its own name at 127.0.0.1, but the
        # browser still sends that name in the Host header, so we only answer our own names.
        if self.headers.get("Host") in ALLOWED_HOSTS:
            return True
        self.send_error(403, "Unknown host")
        return False

    def from_our_page(self) -> bool:
        # Only our own pages may use the POST/PUT endpoints: another website open in the browser
        # could otherwise send requests to 127.0.0.1. Sends the 403 answer itself when not allowed.
        if self.headers.get("Origin") in ALLOWED_ORIGINS and "application/json" in self.headers.get("Content-Type", ""):
            return True
        self.send_json({"error": "Not allowed"}, 403)
        return False

    def send_head(self):
        # Static files: only the app's own public files. The folder also holds private things
        # (tasks database, backups, status/inbox/memory JSON, server.py, .git, .claude): never served.
        if urlsplit(self.path).path not in PUBLIC_FILES:
            self.send_error(404)
            return None
        return super().send_head()

    def do_HEAD(self):
        if self.host_ok():
            super().do_HEAD()

    def do_GET(self):
        if not self.host_ok():
            return
        if self.path.split("?")[0] == "/api/status":
            return self.send_json(load_status())
        if self.path.split("?")[0] == "/api/inbox":
            return self.send_json(load_inbox())
        if self.path.split("?")[0] == "/api/ideas":
            return self.send_json(load_ideas())
        if self.path.split("?")[0] == "/api/decisions":
            return self.send_json(load_decisions())
        if self.path.split("?")[0] == "/api/backups":
            return self.send_json(list_backups())
        if self.path.split("?")[0] == "/api/tasks":
            return self.send_json(load_tasks())
        if self.path.split("?")[0] == "/api/max/status":
            return self.send_json({**max_status(), "testMode": TEST_MODE, "mistakes": len(load_mistakes())})  # the page shows a TEST MODE badge
        if self.path.split("?")[0] == "/api/max/memory":
            return self.send_json(load_memory())
        if self.path.startswith("/api/backups/"):
            return self.get_backup(self.path.split("?")[0][len("/api/backups/"):])
        super().do_GET()

    def do_PUT(self):
        if not self.host_ok():
            return
        if self.path == "/api/max/memory":
            return self.put_memory()
        if self.path != "/api/tasks":
            return self.send_error(404)
        if not self.from_our_page():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            tasks = clean_tasks(body.get("todos"))
            if tasks is None:
                return self.send_json({"error": "todos must be a list of tasks with a number and text"}, 400)
            result, status = save_tasks(tasks, body.get("nextNum"), body.get("baseVersion"))
            self.send_json(result, status)
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):
        if not self.host_ok():
            return
        if self.path == "/api/inbox":
            return self.post_inbox()
        if self.path == "/api/ideas/status":
            return self.post_idea_status()
        if self.path.startswith("/api/decisions/"):
            return self.post_decision(self.path[len("/api/decisions/"):])
        if self.path == "/api/max/mistake":
            return self.post_mistake()
        if self.path == "/api/backup":
            return self.post_backup()
        if self.path == "/api/breakdown":
            return self.post_breakdown()
        if self.path != "/api/parse":
            return self.send_error(404)
        if not self.from_our_page():  # no data changes here, but other sites must not make the PC run the AI
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            sentence = str(body.get("text", ""))[:500]
            now = body.get("now") or datetime.now().strftime("%Y-%m-%dT%H:%M %A")
            # The browser sends its tasks (number + title + due) so commands can find "#3" or "laundry",
            # and "move #2 to friday" can keep #2's time
            tasks = [{"num": int(t["num"]), "text": str(t.get("text", "")), "done": t.get("done") is True,
                      "priority": t.get("priority") if t.get("priority") in ("low", "med", "high") else "med",
                      "cat": str(t.get("cat", ""))[:100],  # priority + category are for questions ("high priority work")
                      "due": t["due"] if isinstance(t.get("due"), str) and DUE_FORMAT.fullmatch(t["due"]) else ""}
                     for t in body.get("tasks", [])[:300]]
            chosen = body.get("num") if isinstance(body.get("num"), int) else None  # picked after "Which one?"
            if body.get("noAI"):  # the page's daily AI limit is reached: words only, no AI
                answer = question_answer(sentence, now, body.get("categories", [])[:20], tasks, use_ai=False)
                return self.send_json(answer or add_without_ai(strip_greeting(" ".join(sentence.split()))[0]))
            result, status = run_command(sentence, now, body.get("categories", [])[:20], tasks, chosen), 200
        except urllib.error.URLError:
            result, status = {"error": "Ollama isn't running. Start the Ollama app and try again."}, 502
        except Exception as e:
            result, status = {"error": f"{type(e).__name__}: {e}"}, 500
        self.send_json(result, status)

    def post_inbox(self):
        # Only our own pages may add commands: another website open in the browser
        # could otherwise send requests to 127.0.0.1 and slip commands into the inbox.
        if not self.from_our_page():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            to = "Toto" if body.get("to") == "Claude" else body.get("to")  # Claude was renamed Toto
            to = to if to in ("Toto", "Kimi", "George", "Bono", "Lewis", "GP") else "Toto"
            text = str(body.get("text", "")).strip()[:1000]
            if not text:
                return self.send_json({"error": "Empty command"}, 400)
            inbox = load_inbox()
            inbox.append({
                "id": int(datetime.now().timestamp() * 1000),
                "to": to,
                "text": text,
                "status": "new",       # new -> working -> done (Toto updates these)
                "reply": "",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            with open(INBOX_FILE, "w", encoding="utf-8") as f:
                json.dump(inbox, f, ensure_ascii=False, indent=2)
            self.send_json({"ok": True})
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)


    def post_mistake(self):
        # Same protection as the inbox: only our own pages may write to Max's mistakes file
        if not self.from_our_page():
            return
        try:
            size = int(self.headers.get("Content-Length") or 0)
            if size > 2000:
                return self.send_json({"error": "Too long"}, 413)
            ok = add_mistake(json.loads(self.rfile.read(size)))
            self.send_json({"ok": True} if ok else {"error": "Not a mistake record"}, 200 if ok else 400)
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def post_idea_status(self):
        # Same protection as the inbox: only our own pages may change ideas
        if not self.from_our_page():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            status = body.get("status")
            if status not in ("sent", "skipped", "liked"):
                return self.send_json({"error": "Unknown status"}, 400)
            ideas = load_ideas()
            # An idea has no id, so title + date together find it
            match = [i for i in ideas if i.get("title") == body.get("title") and i.get("date") == body.get("date")]
            if not match:
                return self.send_json({"error": "Idea not found"}, 404)
            for idea in match:
                idea["status"] = status
            with open(IDEAS_FILE, "w", encoding="utf-8") as f:
                json.dump(ideas, f, ensure_ascii=False, indent=2)
            self.send_json({"ok": True})
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def post_decision(self, id_text):
        # Same protection as the inbox: only our own pages may answer decisions
        if not self.from_our_page():
            return
        try:
            size = int(self.headers.get("Content-Length") or 0)
            if size > 2000:
                return self.send_json({"error": "Too long"}, 413)
            body = json.loads(self.rfile.read(size))
            result, status = answer_decision(id_text, body.get("answer"), body.get("note", ""))
            self.send_json(result, status)
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def put_memory(self):
        # Same protection as the inbox: only our own pages may change what Max remembers
        if not self.from_our_page():
            return
        try:
            size = int(self.headers.get("Content-Length") or 0)
            if size > MEMORY_MAX_BYTES:
                return self.send_json({"error": "Too long. Keep About me short."}, 413)
            memory = clean_memory(json.loads(self.rfile.read(size)))
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            self.send_json(memory)
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def post_breakdown(self):
        # Same protection as the inbox: only our own pages may use the AI
        if not self.from_our_page():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            text = str(body.get("text", "")).strip()[:500]
            if not text:
                return self.send_json({"error": "Empty task"}, 400)
            due = str(body.get("due", ""))
            due = due if DUE_FORMAT.fullmatch(due) else ""
            notes = str(body.get("notes", ""))[:1000]
            # Trip/event task without place or date: ask first (no AI used), unless the owner said "Skip"
            ask = [] if body.get("skipAsk") else breakdown_questions(text, notes, due)
            if ask:
                return self.send_json({"ask": ask})
            result = break_down(text, notes, due)
            if not result["steps"]:
                return self.send_json({"error": "The AI gave no steps. Try again."}, 502)
            self.send_json(result)
        except TimeoutError:
            self.send_json({"error": "The AI took too long. Try again."}, 504)
        except urllib.error.URLError:
            self.send_json({"error": "Ollama isn't running. Start the Ollama app and try again."}, 502)
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def post_backup(self):
        # Same protection as the inbox: only our own pages may write backups
        if not self.from_our_page():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if "todos" in body and not isinstance(body["todos"], list):
                return self.send_json({"error": "todos must be a list"}, 400)
            self.send_json({"ok": True, "name": save_backup(body)})
        except Exception as e:
            self.send_json({"error": f"{type(e).__name__}: {e}"}, 500)

    def get_backup(self, name):
        # Strict name check, so "../server.py" or other paths can never be read
        if not BACKUP_NAME.fullmatch(name):
            return self.send_json({"error": "Bad backup name"}, 400)
        try:
            with open(os.path.join(BACKUP_DIR, name), encoding="utf-8") as f:
                return self.send_json(json.load(f))
        except FileNotFoundError:
            return self.send_json({"error": "Backup not found"}, 404)


# ---------- Task backups (tasks live in the browser; copies are saved here) ----------
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
BACKUP_NAME = re.compile(r"tasks-\d{8}-\d{6}\.json")
KEEP_BACKUPS = 50  # older automatic copies are removed so the folder doesn't grow forever


def save_backup(body: dict) -> str:
    """Write one backup file and return its name, e.g. tasks-20261028-224500.json."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    database = load_tasks() if os.path.exists(DB_FILE) else None
    if "todos" not in body:  # nothing sent from the browser: back up what is in the database
        body = {**body, "todos": database["todos"] if database else [], "nextNum": database and database["nextNum"]}
    daily_db_copy()
    now = datetime.now()
    name = now.strftime("tasks-%Y%m%d-%H%M%S.json")
    while os.path.exists(os.path.join(BACKUP_DIR, name)):  # two backups in the same second
        now += timedelta(seconds=1)
        name = now.strftime("tasks-%Y%m%d-%H%M%S.json")
    data = {
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": str(body.get("reason", ""))[:200],
        "todos": body["todos"],
        "nextNum": body.get("nextNum"),
        "settings": body.get("settings"),
        "usage": body.get("usage"),
        "database": database,  # what the tasks database held at that moment (None if there is none yet)
    }
    with open(os.path.join(BACKUP_DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Keep only the newest files. The names contain the date, so sorting them sorts by time.
    # Only files named like our backups inside backups/ are ever removed.
    old = sorted(n for n in os.listdir(BACKUP_DIR) if BACKUP_NAME.fullmatch(n))[:-KEEP_BACKUPS]
    for n in old:
        os.remove(os.path.join(BACKUP_DIR, n))
    return name


def list_backups() -> list:
    """Newest first: [{name, time, count, reason}]."""
    if not os.path.isdir(BACKUP_DIR):
        return []
    result = []
    for name in sorted((n for n in os.listdir(BACKUP_DIR) if BACKUP_NAME.fullmatch(n)), reverse=True):
        try:
            with open(os.path.join(BACKUP_DIR, name), encoding="utf-8") as f:
                data = json.load(f)
            result.append({"name": name, "time": data.get("time", ""), "count": len(data.get("todos", [])),
                           "reason": data.get("reason", "")})
        except (OSError, ValueError):
            continue  # a broken file is skipped instead of breaking the whole list
    return result


# ---------- Tasks database (SQLite, a single file: data/tasks.db) ----------
# The browser sends the whole list on every change (simple, and fine for one owner).
# "version" goes up by 1 on every save. The browser sends the version it last saw, so if another
# tab saved in between, we refuse (409) instead of silently overwriting that tab's change.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DATA_DIR, "tasks.db")
DB_COPY_NAME = re.compile(r"tasks-db-\d{8}-\d{6}\.db")
KEEP_DB_COPIES = 30  # one per day, so about a month
DB_LOCK = threading.Lock()  # two saves at the same moment must not mix (the server runs several threads)
DUE_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")


def open_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_FILE)
    con.execute("""CREATE TABLE IF NOT EXISTS tasks (
        num INTEGER PRIMARY KEY,   -- the #number the owner sees; never reused
        id REAL,                   -- the browser's own id for the task
        text TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0,
        due TEXT NOT NULL DEFAULT '',        -- YYYY-MM-DDTHH:MM or ''
        priority TEXT NOT NULL DEFAULT 'med',
        cat TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        files TEXT NOT NULL DEFAULT '[]',    -- attachment names/ids as JSON (the files stay in the browser)
        notified INTEGER NOT NULL DEFAULT 0,
        sort INTEGER NOT NULL DEFAULT 0,     -- position in "My order"
        created TEXT NOT NULL,
        updated TEXT NOT NULL,
        steps TEXT NOT NULL DEFAULT '[]',     -- checklist as JSON: [{"text": "...", "done": false}]
        details_asked INTEGER NOT NULL DEFAULT 0)""")  # Max already asked the trip details (or the owner skipped)
    # Databases made before "Break it down" have no steps column yet: add it (existing tasks get [])
    columns = [row[1] for row in con.execute("PRAGMA table_info(tasks)")]
    if "steps" not in columns:
        con.execute("ALTER TABLE tasks ADD COLUMN steps TEXT NOT NULL DEFAULT '[]'")
        con.commit()
    # Same for "Max asks when unsure": existing tasks get 0 (not asked yet)
    if "details_asked" not in columns:
        con.execute("ALTER TABLE tasks ADD COLUMN details_asked INTEGER NOT NULL DEFAULT 0")
        con.commit()
    con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")  # nextNum, version
    return con


def get_meta(con, key, default):
    row = con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return int(row[0]) if row else default


def load_tasks() -> dict:
    con = open_db()
    try:
        rows = con.execute("SELECT id, num, text, done, due, priority, cat, notified, notes, files, steps, details_asked "
                           "FROM tasks ORDER BY sort").fetchall()
        todos = [{"id": r[0], "num": r[1], "text": r[2], "done": bool(r[3]), "due": r[4], "priority": r[5],
                  "cat": r[6], "notified": bool(r[7]), "notes": r[8], "files": json.loads(r[9]),
                  "steps": json.loads(r[10]), "detailsAsked": bool(r[11])} for r in rows]
        return {"todos": todos, "nextNum": get_meta(con, "nextNum", 1), "version": get_meta(con, "version", 0)}
    finally:
        con.close()


def clean_tasks(todos):
    """Check the list from the browser; returns clean tasks, or None if it isn't a task list."""
    if not isinstance(todos, list):
        return None
    clean, seen = [], set()
    for t in todos:
        if not isinstance(t, dict) or not isinstance(t.get("text"), str):
            return None
        num = t.get("num")
        if not isinstance(num, int) or num < 1 or num in seen:  # every task needs its own number
            return None
        seen.add(num)
        files = t.get("files") if isinstance(t.get("files"), list) else []
        steps = t.get("steps") if isinstance(t.get("steps"), list) else []
        clean.append({
            "id": t.get("id") if isinstance(t.get("id"), (int, float)) else None,
            "num": num,
            "text": t["text"][:2000],
            "done": t.get("done") is True,
            "due": t["due"] if isinstance(t.get("due"), str) and DUE_FORMAT.fullmatch(t["due"]) else "",
            "priority": t.get("priority") if t.get("priority") in ("low", "med", "high") else "med",
            "cat": str(t.get("cat") or "")[:100],
            "notified": t.get("notified") is True,
            "notes": str(t.get("notes") or "")[:20000],
            "files": [{"id": str(f.get("id")), "name": str(f.get("name"))} for f in files if isinstance(f, dict)],
            "steps": [{"text": s["text"][:200], "done": s.get("done") is True}
                      for s in steps if isinstance(s, dict) and isinstance(s.get("text"), str)][:30],
            "detailsAsked": t.get("detailsAsked") is True,
        })
    return clean


def save_tasks(tasks: list, next_num, base_version):
    """Replace all tasks in one transaction. Returns (result, http status)."""
    with DB_LOCK:
        return _save_tasks(tasks, next_num, base_version)


def _save_tasks(tasks: list, next_num, base_version):
    con = open_db()
    try:
        with con:  # one transaction: either everything is saved or nothing is
            version = get_meta(con, "version", 0)
            if base_version is not None and base_version != version:
                con.rollback()
                return {"error": "changed elsewhere", **load_tasks()}, 409
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Keep each task's created time, and only touch "updated" when the task really changed
            old = {r[0]: r[1:] for r in con.execute(
                "SELECT num, id, text, done, due, priority, cat, notes, files, notified, steps, details_asked, created, updated FROM tasks")}
            con.execute("DELETE FROM tasks")
            for sort, t in enumerate(tasks):
                values = (t["id"], t["text"], int(t["done"]), t["due"], t["priority"], t["cat"], t["notes"],
                          json.dumps(t["files"], ensure_ascii=False), int(t["notified"]),
                          json.dumps(t["steps"], ensure_ascii=False), int(t["detailsAsked"]))
                before = old.get(t["num"])
                created = before[-2] if before else now
                updated = before[-1] if before and tuple(before[:-2]) == values else now
                con.execute("INSERT INTO tasks (id, text, done, due, priority, cat, notes, files, notified, steps, details_asked, "
                            "num, sort, created, updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            values + (t["num"], sort, created, updated))
            next_num = max([int(next_num) if isinstance(next_num, int) else 1, get_meta(con, "nextNum", 1)]
                           + [t["num"] + 1 for t in tasks])  # numbers are never reused
            con.execute("INSERT OR REPLACE INTO meta VALUES ('nextNum', ?)", (str(next_num),))
            con.execute("INSERT OR REPLACE INTO meta VALUES ('version', ?)", (str(version + 1),))
    finally:
        con.close()
    daily_db_copy()
    return {"ok": True, "version": version + 1, "nextNum": next_num}, 200


# Off-PC backup: a cloud-synced folder (OneDrive), so a dead disk does not take the tasks with it.
# Only used when the OneDrive folder itself exists. Never used in --test mode.
OFFSITE_BACKUP_DIR = r"C:\Users\Locha\OneDrive\JustSayIt-backups"
KEEP_OFFSITE = 14  # newest copies of each kind kept there
offsite_logged = False  # log "skipped" only once per server run


def offsite_backup():
    """Once a day: copy the newest task backup + newest daily DB copy to OFFSITE_BACKUP_DIR.
    Older files are deleted ONLY inside that offsite folder; backups/ is only read."""
    global offsite_logged
    if TEST_MODE:
        return
    if not os.path.isdir(os.path.dirname(OFFSITE_BACKUP_DIR)):  # no OneDrive here: skip quietly
        if not offsite_logged:
            print(f"Offsite backup skipped: {os.path.dirname(OFFSITE_BACKUP_DIR)} not found")
            offsite_logged = True
        return
    marker = os.path.join(DATA_DIR, "offsite-last.txt")  # remembers the last day we copied
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        if os.path.exists(marker) and open(marker, encoding="utf-8").read().strip() == today:
            return
        os.makedirs(OFFSITE_BACKUP_DIR, exist_ok=True)
        copied = []
        for pattern in (BACKUP_NAME, DB_COPY_NAME):
            names = sorted(n for n in os.listdir(BACKUP_DIR) if pattern.fullmatch(n))
            if names:  # newest of this kind
                shutil.copy2(os.path.join(BACKUP_DIR, names[-1]), os.path.join(OFFSITE_BACKUP_DIR, names[-1]))
                copied.append(names[-1])
            for old in sorted(n for n in os.listdir(OFFSITE_BACKUP_DIR) if pattern.fullmatch(n))[:-KEEP_OFFSITE]:
                os.remove(os.path.join(OFFSITE_BACKUP_DIR, old))
        with open(marker, "w", encoding="utf-8") as f:
            f.write(today)
        print(f"Offsite backup copied: {', '.join(copied) or 'nothing to copy'}")
    except OSError as e:  # OneDrive busy or full: never break saving tasks because of it
        print(f"Offsite backup failed: {e}")


def daily_db_copy():
    """Once a day: the local database copy, then the off-PC copy."""
    make_db_copy()
    offsite_backup()


def make_db_copy():
    """Once a day, copy tasks.db to backups/tasks-db-YYYYMMDD-HHMMSS.db."""
    if not os.path.exists(DB_FILE):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    now = datetime.now()
    if any(n.startswith(now.strftime("tasks-db-%Y%m%d-")) for n in os.listdir(BACKUP_DIR)):
        return  # already have today's copy
    if not load_tasks()["todos"]:
        return  # an empty database (before the first tasks arrive) is not worth a copy
    source, target = sqlite3.connect(DB_FILE), sqlite3.connect(os.path.join(BACKUP_DIR, now.strftime("tasks-db-%Y%m%d-%H%M%S.db")))
    try:
        source.backup(target)  # SQLite's own safe copy, even while the database is in use
    finally:
        source.close()
        target.close()
    for n in sorted(n for n in os.listdir(BACKUP_DIR) if DB_COPY_NAME.fullmatch(n))[:-KEEP_DB_COPIES]:
        os.remove(os.path.join(BACKUP_DIR, n))


# ---------- Max: status and "About me" memory ----------
# max-memory.json is private (gitignored): things Max should know about the owner.
# Never put passwords or other secrets in it: it is sent to the AI with every request.
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "max-memory.json")
DEFAULT_TIMES = {"morning": "09:00", "afternoon": "13:00", "evening": "18:00", "tonight": "20:00"}
HHMM = re.compile(r"([01]\d|2[0-3]):[0-5]\d")
MEMORY_MAX_BYTES = 4000


def clean_memory(m) -> dict:
    """Keep only known fields with safe sizes; missing or bad times get the defaults."""
    m = m if isinstance(m, dict) else {}
    times = m.get("times") if isinstance(m.get("times"), dict) else {}

    def words(value, count, size):  # a list of short strings
        if not isinstance(value, list):
            return []
        return [x.strip()[:size] for x in value if isinstance(x, str) and x.strip()][:count]

    return {
        "name": str(m.get("name") or "").strip()[:60],
        "times": {k: times[k] if isinstance(times.get(k), str) and HHMM.fullmatch(times[k]) else v
                  for k, v in DEFAULT_TIMES.items()},
        "people": words(m.get("people"), 30, 60),
        "categories": words(m.get("categories"), 30, 40),
        "notes": str(m.get("notes") or "").strip()[:500],
    }


def load_memory() -> dict:
    try:
        with open(MEMORY_FILE, encoding="utf-8-sig") as f:
            return clean_memory(json.load(f))
    except (FileNotFoundError, ValueError):
        return clean_memory({})


def memory_summary(m: dict, notes_only: bool = False) -> str:
    """One short line for Max's prompts (small models get confused by long ones).
    notes_only: for Break it down, where names made the AI add steps like "tell Jirayu"."""
    parts = []
    if m["name"] and not notes_only:
        parts.append(f"The owner is {m['name']}.")
    if m["people"] and not notes_only:
        parts.append(f"People they know (spell exactly): {', '.join(m['people'])}.")
    if m["notes"]:
        parts.append(f"Notes: {m['notes']}")
    return ("About the owner: " + " ".join(parts)) if parts else ""


_status = {"at": 0.0, "data": None}  # Max's status is cached for 30 s, so the page can ask often


def max_status() -> dict:
    """Is Max ready? For Ollama: is it running, and which models (brains) does it have?"""
    now = datetime.now().timestamp()
    if _status["data"] and now - _status["at"] < 30:
        return _status["data"]
    if AI_PROVIDER == "ollama":
        try:
            with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=2) as response:
                models = [m.get("name", "") for m in json.loads(response.read()).get("models", [])]
        except (OSError, ValueError):
            models = []  # Ollama is not running
        data = {"ready": FAST_MODEL in models, "models": models, "fast": FAST_MODEL,
                "smart": SMART_MODEL if SMART_MODEL in models else FAST_MODEL, "smartWanted": SMART_MODEL}
    else:
        data = {"ready": bool(os.environ.get("ANTHROPIC_API_KEY")), "models": [CLAUDE_MODEL],
                "fast": CLAUDE_MODEL, "smart": CLAUDE_MODEL, "smartWanted": CLAUDE_MODEL}
    _status.update(at=now, data=data)
    return data


# ---------- Learning loop: tasks Max added that the owner deleted a few minutes later ----------
# Private and local only (data/ is gitignored). Toto reads it to turn mistakes into rules and tests.
MISTAKES_FILE = os.path.join(DATA_DIR, "max-mistakes.json")
MISTAKES_MAX = 500  # keep the newest ones


def load_mistakes() -> list:
    try:
        with open(MISTAKES_FILE, encoding="utf-8-sig") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def add_mistake(body: dict) -> bool:
    """Save {text, action, created, deletedAt} from the page. False if it is not a usable record."""
    text = str(body.get("text", "")).strip()[:200]
    if not text or body.get("action") != "add":
        return False
    entry = {"text": text, "action": "add",
             "created": str(body.get("created", ""))[:30], "deletedAt": str(body.get("deletedAt", ""))[:30]}
    mistakes = (load_mistakes() + [entry])[-MISTAKES_MAX:]
    os.makedirs(os.path.dirname(MISTAKES_FILE), exist_ok=True)
    with open(MISTAKES_FILE, "w", encoding="utf-8") as f:
        json.dump(mistakes, f, ensure_ascii=False, indent=2)
    return True


# ---------- Command inbox (Team Status page) ----------
INBOX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbox.json")
# The names this server answers to (without the port). To add another device or name, add one line here.
# This PC's own Tailscale IP/names are private, and this code goes to a public repo, so they live in
# data/local-hosts.json (gitignored), e.g. ["100.x.y.z", "my-pc", "my-pc.my-tailnet.ts.net"]. No file = none.
LOCAL_HOSTS_FILE = os.path.join(DATA_DIR, "local-hosts.json")


def load_local_hosts(path: str = LOCAL_HOSTS_FILE) -> tuple:
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
        return tuple(str(h).strip().lower() for h in data if str(h).strip()) if isinstance(data, list) else ()
    except (OSError, ValueError):
        return ()


HOST_NAMES = ("127.0.0.1", "localhost") + load_local_hosts()
# Only these computers may connect: this PC and the owner's Tailscale network (private, logged-in
# devices only). The server listens on 0.0.0.0, so this check is what keeps home Wi-Fi/LAN and
# the internet out even if the firewall lets them through.
TAILSCALE_NETS = (ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48"))


def client_ip_ok(ip: str) -> bool:
    """True for this PC (loopback) or a Tailscale address; anything else (LAN, internet) is refused."""
    try:
        addr = ipaddress.ip_address(ip.split("%")[0])  # drop an IPv6 zone like "%12"
    except ValueError:
        return False
    if addr.is_loopback:
        return True
    return any(addr in net for net in TAILSCALE_NETS if addr.version == net.version)


def make_allowed_hosts(port: int) -> tuple:
    return tuple(f"{name}:{port}" for name in HOST_NAMES)


ALLOWED_HOSTS = make_allowed_hosts(8000)
ALLOWED_ORIGINS = tuple("http://" + host for host in ALLOWED_HOSTS)
# The only files the server hands out; everything else in the folder stays private
PUBLIC_FILES = {"/", "/index.html", "/style.css", "/script.js", "/status.html",
                "/icon.svg", "/icon-192.png", "/icon-512.png", "/apple-touch-icon.png", "/manifest.json", "/hints.json", "/hints.js"}
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json")


def load_status() -> dict:
    """Team status for the Team pill and status page (status.json itself is not served)."""
    try:
        with open(STATUS_FILE, encoding="utf-8-sig") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {"agents": [], "usage": {"windows": []}}


def load_inbox() -> list:
    try:
        with open(INBOX_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ---------- Ideas from Lewis (Team Status page) ----------
IDEAS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ideas.json")


def load_ideas() -> list:
    try:
        with open(IDEAS_FILE, encoding="utf-8-sig") as f:  # -sig: also reads files saved with a BOM
            ideas = json.load(f)
        return ideas if isinstance(ideas, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ---------- Decisions for the owner (Team Status page) ----------
DECISIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decisions.json")


def load_decisions() -> list:
    try:
        with open(DECISIONS_FILE, encoding="utf-8-sig") as f:
            items = json.load(f)
        return items if isinstance(items, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def answer_decision(id_text, answer, note) -> tuple:
    """Save Go / No-go on one OPEN decision. Returns (json answer, http status)."""
    if answer not in ("Go", "No-go"):
        return {"error": "Answer must be Go or No-go"}, 400
    items = load_decisions()
    found = [d for d in items if isinstance(d, dict) and str(d.get("id")) == id_text]
    if not found:
        return {"error": "Decision not found"}, 404
    if found[0].get("status") == "answered":
        return {"error": "Already answered"}, 409  # the first answer stays
    found[0].update({"status": "answered", "answer": answer, "note": str(note or "").strip()[:500],
                     "answeredAt": datetime.now().strftime("%Y-%m-%d %H:%M")})
    with open(DECISIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return {"ok": True}, 200


# ---------- Test mode: python server.py --test ----------
# A second copy of the server on port 8001 with its own data files, so testing never touches the
# owner's real tasks. Only the file names change; all the code is the same.
TEST_MODE = "--test" in sys.argv
PORT = 8000


def warm_up_ollama():
    """Load the model now, so the owner's first command is not slow. Never stops the server."""
    try:
        data = json.dumps({"model": FAST_MODEL, "keep_alive": OLLAMA_KEEP_ALIVE}).encode()  # no prompt = just load it
        request = urllib.request.Request(OLLAMA_URL.replace("/api/chat", "/api/generate"), data=data,
                                         headers={"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=120).close()
    except Exception:
        pass  # Ollama is off or busy: Max falls back as usual


def use_test_mode():
    """Point every private file at a test copy and allow port 8001. Called only for --test."""
    global PORT, ALLOWED_HOSTS, ALLOWED_ORIGINS, DATA_DIR, DB_FILE, BACKUP_DIR
    global MEMORY_FILE, STATUS_FILE, INBOX_FILE, IDEAS_FILE, MISTAKES_FILE, DECISIONS_FILE
    here = os.path.dirname(os.path.abspath(__file__))
    PORT = 8001
    ALLOWED_HOSTS = make_allowed_hosts(8001)
    ALLOWED_ORIGINS = tuple("http://" + host for host in ALLOWED_HOSTS)
    DATA_DIR = os.path.join(here, "data")                      # same gitignored folder...
    DB_FILE = os.path.join(DATA_DIR, "test-tasks.db")           # ...but its own database
    BACKUP_DIR = os.path.join(here, "backups-test")             # test backups, apart from backups/
    # Files Max/status read: start as a COPY of the real one (so the page looks normal), then they
    # live on their own. The real file is only ever read here, never written.
    copies = {"max-memory.json": "MEMORY_FILE", "status.json": "STATUS_FILE",
              "inbox.json": "INBOX_FILE", "ideas.json": "IDEAS_FILE"}
    MISTAKES_FILE = os.path.join(DATA_DIR, "test-max-mistakes.json")  # starts empty, never a copy
    DECISIONS_FILE = os.path.join(DATA_DIR, "test-decisions.json")  # starts empty, never a copy
    os.makedirs(DATA_DIR, exist_ok=True)
    for real_name, variable in copies.items():
        test_file = os.path.join(DATA_DIR, "test-" + real_name)
        if not os.path.exists(test_file) and os.path.exists(os.path.join(here, real_name)):
            shutil.copyfile(os.path.join(here, real_name), test_file)
        globals()[variable] = test_file


if __name__ == "__main__":
    if TEST_MODE:
        use_test_mode()
    if AI_PROVIDER == "ollama":
        threading.Thread(target=warm_up_ollama, daemon=True).start()  # in the background: start-up is not delayed
    daily_db_copy()  # also at start-up, so a day without edits still gets its backups
    print(f"To-do app {'TEST MODE ' if TEST_MODE else ''}running at http://127.0.0.1:{PORT} (also Tailscale, port {PORT})  (AI: {AI_PROVIDER})")
    here = os.path.dirname(os.path.abspath(__file__))
    ThreadingHTTPServer(("0.0.0.0", PORT), partial(Handler, directory=here)).serve_forever()
