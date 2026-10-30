"""Max's exam: run the sentences in tests/max_exam.json through the real run_command + real Ollama.

    python tools/max_exam.py [label]        (label = a note saved with the run, e.g. "after keep-alive")
    python tools/max_exam.py --model qwen3:4b   (another model for this run only)
    python tools/max_exam.py -v             (also print every wrong answer)

Safe by design: it calls use_test_mode() first (test database, test files), checks that again, and uses
the made-up task list and fixed "now" from the exam file, so the owner's data is never read or written.
Each run is appended to data/exam-results.json (gitignored) so the trend is visible.
"""
import json
import os
import sys
import time
from datetime import datetime
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")  # Thai text in the console

import server  # noqa: E402

server.use_test_mode()
# Belt and braces: never run if the real database is still selected
assert os.path.basename(server.DB_FILE) == "test-tasks.db", "exam must run in test mode"

FIELDS = ["action", "title", "due", "priority", "category", "num", "change", "filter"]


def norm(text):
    return " ".join(str(text or "").lower().split())


def check(case, r):
    """{field: True/False} for every field the case lists."""
    act = r.get("action")
    changes = r.get("changes") or {}
    exp_change = case.get("change", {})
    want_act = case["action"] if isinstance(case["action"], list) else [case["action"]]  # a list = any is fine
    out = {"action": act in want_act}
    if "title" in case:
        out["title"] = norm(r.get("text")) in [norm(t) for t in case["title"]]
    if "due" in case:
        out["due"] = (r.get("due") or "") == case["due"]
    if "priority" in case:
        out["priority"] = r.get("priority") == case["priority"]
    if "category" in case:
        out["category"] = r.get("category") in case["category"]
    if "num" in case:
        out["num"] = r.get("num") == case["num"]
    if "change" in case:
        ok = True
        for key, want in exp_change.items():
            got = changes.get(key)
            ok = ok and (norm(got) in [norm(w) for w in want] if isinstance(want, list) else got == want)
        out["change"] = ok and bool(changes)
    if "filter" in case:
        got = r.get("filter") or {}
        out["filter"] = all(norm(got.get(k)) == norm(v) for k, v in case["filter"].items())
    return out


def main():
    verbose = "-v" in sys.argv
    args = [a for a in sys.argv[1:] if a != "-v"]
    model_override = ""
    if "--model" in args:   # try another brain for this run only: --model qwen3:4b
        i = args.index("--model")
        model_override = args[i + 1]
        del args[i:i + 2]
    words = args
    label = words[0] if words else ""
    with open(os.path.join(ROOT, "tests", "max_exam.json"), encoding="utf-8-sig") as f:
        exam = json.load(f)

    # Count every AI call; the fixed memory keeps About-me times the same on every machine
    calls = {"n": 0}
    real_ai = server.parse_with_ollama

    def counting_ai(*a, **kw):
        calls["n"] += 1
        if model_override:
            kw["model"] = model_override   # this run only; server.py's FAST_MODEL is not changed
        return real_ai(*a, **kw)

    scores = {k: [0, 0] for k in FIELDS}   # field -> [right, total]
    seconds, ai_counts, wrong = [], [], []
    with mock.patch.object(server, "parse_with_ollama", counting_ai), \
         mock.patch.object(server, "load_memory", return_value=server.clean_memory({})):
        for case in exam["cases"]:
            calls["n"] = 0
            start = time.time()
            try:
                r = server.run_command(case["s"], exam["now"], exam["categories"], [dict(t) for t in exam["tasks"]])
            except Exception as err:   # a crash is a wrong answer, not the end of the exam
                r = {"action": "error:" + type(err).__name__}
            seconds.append(time.time() - start)
            ai_counts.append(calls["n"])
            result = check(case, r)
            for field, ok in result.items():
                scores[field][0] += ok
                scores[field][1] += 1
            if not all(result.values()):
                wrong.append({"s": case["s"], "bad": [k for k, v in result.items() if not v], "got": r})

    right = sum(s[0] for s in scores.values())
    total = sum(s[1] for s in scores.values())
    warm = sorted(seconds[1:])
    p95 = warm[min(len(warm) - 1, int(len(warm) * 0.95))]
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "label": label, "model": model_override or server.FAST_MODEL,
        "sentences": len(seconds), "overall_pct": round(100 * right / total, 1),
        "fields_pct": {k: round(100 * v[0] / v[1], 1) for k, v in scores.items() if v[1]},
        "sentences_all_right": len(seconds) - len(wrong),
        "cold_first_s": round(seconds[0], 2), "warm_avg_s": round(sum(warm) / len(warm), 2), "warm_p95_s": round(p95, 2),
        "ai_calls_per_sentence": round(sum(ai_counts) / len(ai_counts), 2),
        "ai_calls_spread": {str(n): ai_counts.count(n) for n in sorted(set(ai_counts))},
        "wrong": [{"s": w["s"], "bad": w["bad"]} for w in wrong],
    }
    print(json.dumps({k: v for k, v in summary.items() if k != "wrong"}, indent=1, ensure_ascii=False))
    for w in wrong:
        print("WRONG", w["s"], w["bad"], (json.dumps(w["got"], ensure_ascii=False)[:230] if verbose else ""))

    path = os.path.join(server.DATA_DIR, "exam-results.json")
    try:
        with open(path, encoding="utf-8-sig") as f:
            history = json.load(f)
    except (FileNotFoundError, ValueError):
        history = []
    history.append(summary)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
