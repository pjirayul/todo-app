# Team handover — for a fresh chat (cloud or PC)
Written 11 Nov 2026 (cloud session, while the PC Claude was unavailable). Read this, CLAUDE.md and STATUS.md first.

## Who does what (see CLAUDE.md)
Toto leads and plans, Kimi builds, George styles, Lewis researches, Bono tests, GP checks designs (never edits code).
A fresh chat plays **Toto** and runs the others as sub-agents, one job at a time.
Role files live in `.claude/agents/` **on the owner's PC only** (gitignored). In a cloud chat, use the one-line roles above.

## Where the work is
- Plan: the owner's work queue ("▶ NEXT", 11 Nov 00:35) — build only "brain-proof" parts (screen cards, Python checks,
  data fields, exam lines). No more prompt tuning for the small model; #17 (several things in one sentence) is PARKED.
- Done: #16 can't-do card (3cc3637), max-offline.js offline rules (5f76643, 985f88e),
  **job 9 server + offline part** (this branch): `done_at` column, "what did I finish today / yesterday / this week /
  on Monday" uses the day a task was ticked. 302 unit tests OK, offline rules 70/70.

## Next steps (in order)
1. **Job 9 page part (Kimi):** script.js `markDone()` sets `todo.doneAt` (local `YYYY-MM-DDTHH:MM`); the repeat copy gets
   `doneAt: ""`; both "undo done" spots (applyCommand uncomplete, checkbox untick) clear it; `cleanTodos()` keeps it
   (only on done tasks); the `/api/parse` task list (`tasks: todos.map(...)`) sends `doneAt`. Bump `?v=` in index.html.
   Run `python -m unittest` and `node tools-js/test_offline_rules.js` (first `python tools-js/make_offline_cases.py`).
2. **Bono batch check** of #16 + offline rules + job 9 (test copy on 8001, PC only).
3. **Calendar mockups A/B/C (George, job 10)** → owner picks.
4. **Push live** (77+ commits) — only after Bono PASS and the owner's Go.

## Cloud chat limits
No access to the PC (no 8000/8001 server, no Ollama, no Max exam, no `backups/`). Unit tests and Node tests do run.
Pushes go to the `claude/...` branch only; never to main / GitHub Pages without the owner's Go.
