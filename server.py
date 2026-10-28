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

INSTRUCTIONS = (
    "You turn one to-do sentence (English or Thai) into a structured task. "
    "text: short task title in the user's language, without the date/time/priority words. "
    "due: date-time as YYYY-MM-DDTHH:MM resolved from the current time given "
    "(e.g. 'tomorrow'/'พรุ่งนี้' = the next day; a day without a time = 09:00), or \"\" if none. "
    "priority: high for urgent/ASAP/ด่วน/important, low for someday/maybe/ไม่รีบ, otherwise med. "
    "category: one short English word like Work, Home, Shopping, Health, Study, Money, Personal; "
    "reuse one of the existing categories when it fits."
)

# The exact shape we want back
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "due": {"type": "string"},
        "priority": {"type": "string", "enum": ["low", "med", "high"]},
        "category": {"type": "string"},
    },
    "required": ["text", "due", "priority", "category"],
}


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
        return json.loads(json.loads(response.read())["message"]["content"])


def parse_with_claude(prompt: str) -> dict:
    import anthropic  # only needed for Claude: pip install anthropic
    from pydantic import BaseModel
    from typing import Literal

    class Task(BaseModel):
        text: str
        due: str
        priority: Literal["low", "med", "high"]
        category: str

    response = anthropic.Anthropic().messages.parse(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        output_config={"effort": "low"},
        system=INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}],
        output_format=Task,
    )
    return response.parsed_output.model_dump()


EXAMPLES = """Examples (if today is 2026-01-05 Monday):
"call mom tomorrow evening" -> {"text":"Call mom","due":"2026-01-06T18:00","priority":"med","category":"Personal"}
"ส่งรายงานวันศุกร์ บ่ายสาม ด่วน" -> {"text":"ส่งรายงาน","due":"2026-01-09T15:00","priority":"high","category":"Work"}
"maybe repaint the bedroom someday" -> {"text":"Repaint the bedroom","due":"","priority":"low","category":"Home"}
Keep text in the SAME language as the sentence. Only use Work for job tasks."""


def parse_task(sentence: str, now: str, categories: list) -> dict:
    # Small models are bad at calendar math, so give them the next 7 days directly
    today = datetime.strptime(now[:10], "%Y-%m-%d")
    days = ", ".join(
        f"{(today + timedelta(days=i)):%A}={(today + timedelta(days=i)):%Y-%m-%d}" for i in range(1, 8)
    )
    prompt = (
        f"{EXAMPLES}\n\nNow: {now}\nNext 7 days: {days}\n"
        f"Existing categories: {', '.join(categories) or 'none'}\nSentence: {sentence}"
    )
    task = parse_with_ollama(prompt) if AI_PROVIDER == "ollama" else parse_with_claude(prompt)
    # Small models sometimes slip; keep the result safe for the app
    if task.get("priority") not in ("low", "med", "high"):
        task["priority"] = "med"
    try:
        datetime.strptime(task.get("due", ""), "%Y-%m-%dT%H:%M")
    except ValueError:
        task["due"] = ""
    task["text"] = task.get("text") or sentence
    return task


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
