"""Small web server for the to-do app.

- Serves index.html, style.css and script.js
- POST /api/parse turns a sentence like "pay rent tomorrow 9am urgent"
  into a task using AI, or runs a command on an existing task
  ("move #2 to friday", "delete laundry", "done #3").

Run:  python server.py   then open http://127.0.0.1:8000
"""

import difflib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ---------- Settings: change these to switch AI ----------
AI_PROVIDER = "ollama"          # "ollama" (free, on this PC) or "claude" (needs ANTHROPIC_API_KEY)
OLLAMA_MODEL = "qwen2.5:3b"     # upgrade later, e.g. "qwen2.5:7b", after: ollama pull <name>
CLAUDE_MODEL = "claude-haiku-5-5"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

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
    "time: 24h HH:MM if a time is said (5pm=17:00, บ่ายสาม=15:00, evening=18:00, morning=09:00), else \"\"."
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


def resolve_due(task: dict, now: datetime) -> str:
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
        if task.get("next_week"):  # same weekday in the following Mon–Sun week
            date = today - timedelta(days=today.weekday()) + timedelta(days=7 + target)
        else:  # the next one coming up
            date = today + timedelta(days=(target - today.weekday() - 1) % 7 + 1)
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
        date = date.replace(hour=9)
    return date.strftime("%Y-%m-%dT%H:%M")


def parse_with_ollama(prompt: str) -> dict:
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps({
            "model": OLLAMA_MODEL,
            "messages": [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": prompt}],
            "format": TASK_SCHEMA,   # forces the answer into our JSON shape
            "stream": False,
            "options": {"temperature": 0},
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
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
"ซักผ้าพรุ่งนี้" -> {"text":"ซักผ้า","priority":"med","category":"Home","when":"tomorrow","in_days":0,"weekday":"","next_week":false,"day":0,"month":0,"next_month":false,"time":""}"""


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


def parse_task(sentence: str, now: str, categories: list) -> dict:
    sentence = fix_date_typos(sentence)
    prompt = f"{EXAMPLES}\n\nExisting categories: {', '.join(categories) or 'none'}\nSentence: {sentence}"
    task = parse_with_ollama(prompt) if AI_PROVIDER == "ollama" else parse_with_claude(prompt)
    # Common day words are certain, so they override the AI
    lower = sentence.lower()
    for words, when in ((("มะรืน", "day after tomorrow"), "day_after_tomorrow"),
                        (("พรุ่งนี้", "tomorrow"), "tomorrow"),
                        (("วันนี้", "today", "tonight", "คืนนี้"), "today")):
        if any(w in lower for w in words):
            task["when"] = when
            break
    # Small models sometimes slip; keep the result safe for the app
    title = task.get("text") or sentence
    return {
        "text": title[:1].upper() + title[1:],  # "pay rent" -> "Pay rent"
        "due": resolve_due(task, datetime.strptime(now[:16], "%Y-%m-%dT%H:%M")),
        "priority": task.get("priority") if task.get("priority") in ("low", "med", "high") else "med",
        "category": task.get("category", ""),
        "tokens": task.get("tokens", 0),
    }


# ---------- Command bar: act on an existing task ----------
# Python spots the action and the target (reliable); the AI is only used to read dates.
# Each pattern must match at the START of the sentence (after lowercasing).
UNDO_WORDS = r"^(undo|undone|uncheck|unmark|reopen|not done)\b|ยังไม่เสร็จ|ยกเลิกเสร็จ"
DELETE_WORDS = r"^(delete|remove|del|erase)\b|^ลบ"
DONE_WORDS = r"^(done|mark|tick|finished|completed)\b|\b(done|finished|completed)$|เสร็จ(แล้ว)?$|^เสร็จ"
UPDATE_WORDS = r"^(change|move|rename|set|edit|update|reschedule|postpone)\b|^(เปลี่ยน|แก้|ย้าย|เลื่อน)"
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


def run_command(sentence: str, now: str, categories: list, tasks: list) -> dict:
    """Work out what the sentence wants: add a task, or change/delete/complete an existing one."""
    s = " ".join(sentence.split())
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
        return {"action": "add", **parse_task(s, now, categories)}

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
    if action == "update" and field_match:
        field = FIELD_WORDS[field_match.group(1).lower()]
        rest = strip_filler(rest[field_match.end():])

    # Which task? A number, or the words before "to"/"เป็น" (or everything, for delete/done)
    if num_match:
        target, change = num_match.group(0), rest
    elif action == "update":
        parts = re.split(r"\s+to\s+|\s*(?:ให้เป็น|ไปเป็น|เป็น|ไปวัน|ไป)\s*", rest, maxsplit=1)
        if len(parts) < 2:  # "set up the printer" is a new task, not a command
            return {"action": "add", **parse_task(s, now, categories)}
        target, change = strip_filler(parts[0]), strip_filler(parts[1])
    else:
        target, change = rest, ""
    num, choices = find_task(target, tasks)
    if num is None:
        return {"action": action, "missing": target, "choices": choices}
    if action != "update":
        return {"action": action, "num": num}

    # Only the fields the command mentions change
    if not change:
        return {"action": action, "num": num, "nothing": True}
    changes, tokens = {}, 0
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
        if field != "priority" and left:
            parsed = parse_task(change, now, categories)  # the AI reads the date words
            tokens = parsed["tokens"]
            if parsed["due"]:
                changes["due"] = parsed["due"]
            elif not priority and field != "due" and re.match(r"(change|edit|update|เปลี่ยน|แก้)", low):
                changes["text"] = change[:1].upper() + change[1:]  # "change #2 to call mom" = new name
        if not changes:
            return {"action": action, "num": num, "nothing": True, "tokens": tokens}
    return {"action": action, "num": num, "changes": changes, "tokens": tokens}


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

    def do_GET(self):
        if self.path.split("?")[0] == "/api/inbox":
            return self.send_json(load_inbox())
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/inbox":
            return self.post_inbox()
        if self.path != "/api/parse":
            return self.send_error(404)
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            sentence = str(body.get("text", ""))[:500]
            now = body.get("now") or datetime.now().strftime("%Y-%m-%dT%H:%M %A")
            # The browser sends its tasks (number + title) so commands can find "#3" or "laundry"
            tasks = [{"num": int(t["num"]), "text": str(t.get("text", ""))} for t in body.get("tasks", [])[:300]]
            result, status = run_command(sentence, now, body.get("categories", [])[:20], tasks), 200
        except urllib.error.URLError:
            result, status = {"error": "Ollama isn't running. Start the Ollama app and try again."}, 502
        except Exception as e:
            result, status = {"error": f"{type(e).__name__}: {e}"}, 500
        self.send_json(result, status)

    def post_inbox(self):
        # Only our own pages may add commands: another website open in the browser
        # could otherwise send requests to 127.0.0.1 and slip commands into the inbox.
        if self.headers.get("Origin") not in ALLOWED_ORIGINS or "application/json" not in self.headers.get("Content-Type", ""):
            return self.send_json({"error": "Not allowed"}, 403)
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            to = "Toto" if body.get("to") == "Claude" else body.get("to")  # Claude was renamed Toto
            to = to if to in ("Toto", "Kimi", "George") else "Toto"
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


# ---------- Command inbox (Team Status page) ----------
INBOX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbox.json")
ALLOWED_ORIGINS = ("http://127.0.0.1:8000", "http://localhost:8000")


def load_inbox() -> list:
    try:
        with open(INBOX_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


if __name__ == "__main__":
    print(f"To-do app running at http://127.0.0.1:8000  (AI: {AI_PROVIDER})")
    here = os.path.dirname(os.path.abspath(__file__))
    ThreadingHTTPServer(("127.0.0.1", 8000), partial(Handler, directory=here)).serve_forever()
