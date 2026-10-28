"""Small web server for the to-do app.

- Serves index.html, style.css and script.js
- POST /api/parse turns a sentence like "pay rent tomorrow 9am urgent"
  into a task using AI.

Run:  python server.py   then open http://127.0.0.1:8000
"""

import json
import os
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
    "text: short task title in the SAME language as the sentence, without date/time/priority words.\n"
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
"maybe repaint the bedroom someday" -> {"text":"Repaint the bedroom","priority":"low","category":"Home","when":"none","in_days":0,"weekday":"","next_week":false,"day":0,"month":0,"next_month":false,"time":""}"""


def parse_task(sentence: str, now: str, categories: list) -> dict:
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
    return {
        "text": task.get("text") or sentence,
        "due": resolve_due(task, datetime.strptime(now[:16], "%Y-%m-%dT%H:%M")),
        "priority": task.get("priority") if task.get("priority") in ("low", "med", "high") else "med",
        "category": task.get("category", ""),
        "tokens": task.get("tokens", 0),
    }


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/parse":
            return self.send_error(404)
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            sentence = str(body.get("text", ""))[:500]
            now = body.get("now") or datetime.now().strftime("%Y-%m-%dT%H:%M %A")
            result, status = parse_task(sentence, now, body.get("categories", [])[:20]), 200
        except urllib.error.URLError:
            result, status = {"error": "Ollama isn't running. Start the Ollama app and try again."}, 502
        except Exception as e:
            result, status = {"error": f"{type(e).__name__}: {e}"}, 500

        data = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"To-do app running at http://127.0.0.1:8000  (AI: {AI_PROVIDER})")
    here = os.path.dirname(os.path.abspath(__file__))
    ThreadingHTTPServer(("127.0.0.1", 8000), partial(Handler, directory=here)).serve_forever()
