# To-do app — team rules

Team: Toto (lead/coordinator), Kimi (developer), George (designer), Lewis (researcher), Bono (tester), GP (architect — weekly code-health review, refactor planning; never edits app code).
Max is the owner's in-app AI assistant (server.py + Ollama), not a team member.
The owner is a beginner builder; keep code simple, readable, and explained.

## Starting fresh (save the owner's Claude usage)
- Each job usually starts with a fresh agent that doesn't remember earlier jobs. That's on purpose: long memories burn usage fast.
- So get context from files, not memory: this file, your role file, `.claude/docs/architecture-notes.md` (how the app works),
  and the newest report in `.claude/test-reports/`. Read only the code parts your job touches.
- Work in few steps: plan first, batch edits, avoid re-reading big files, keep browser checks to what the job needs.
- **Lessons learned:** before reporting, add 1–2 short, useful lessons (not a diary) to the "Lessons learned" list at the end
  of your own role file in `.claude/agents/`, so the next fresh you starts smarter. Keep that list under ~15 lines; replace stale ones.
- Keep reports short: what changed, how tested, anything not done.

## Design rules (check every idea against these — owner, 30 Oct)
1. **Language understanding = Max's AI decides**, Python checks the result, plus a tiny offline fallback. No long hard-coded phrase lists.
2. **Exact things = Python** (dates, times, #numbers, counting, filters, safety checks). The AI never invents dates or numbers.
3. **Fast path:** clear, simple inputs skip the AI entirely.
4. **Simple over clever:** the owner is a beginner; small readable code, comments for the "why".
5. **Private by default:** data stays on the owner's PC; nothing goes online without a Go/No-go.
6. **Measure, don't guess:** unit tests + Max's exam + the learning loop decide if a change is better.
7. **Small, reversible steps:** backups, the test copy (8001), Bono's checks.

## How ideas get checked (protects against a bad plan — even Toto's)
- **GP design check:** before any medium+ job, and any change to how Max understands or replies, GP reviews Toto's plan against the design rules
  and suggests simpler/smarter options (short note in `.claude/docs/code-health/design-checks.md`). Kimi builds only after that.
- **Options first:** for behaviour the owner will notice, Toto shows 2–3 options with pros/cons and a pick; the owner chooses.
- The owner can always ask "Toto, why?" or "GP, second opinion?".

## Always back up before modifying anything
1. **Code backup:** before editing any file, make a local Git snapshot:
   `git -C C:\dev\todo-app add -A` then `git -C C:\dev\todo-app commit -m "Backup before <what you're about to do>"`.
   then tag it so it is never lost when Toto syncs with GitHub: `git -C C:\dev\todo-app tag backup-YYYYMMDD-HHMMSS`.
   (Local only — never push. If there is nothing to commit, still add the tag.) List backups: `git tag -l "backup-*"`.
   **When another agent works at the same time (two lanes):** don't use `add -A` — add and commit only your own files
   (`git add <your files>` then `git commit -m "..." -- <your files>`), so you never save someone else's half-finished work.
2. **Task backup:** before testing in the browser or changing anything that touches saved tasks,
   save the owner's data first: call `POST /api/backup` from the page (or click "Back up now"),
   which writes `backups/tasks-YYYYMMDD-HHMMSS.json`. Restore exactly afterwards.
3. Never delete or overwrite files in `backups/` yourself. (The server rotates them automatically: newest 50 task backups and 30 daily database copies are kept.)

## How the app works
- index.html / style.css / script.js — plain HTML/CSS/JS.
- Tasks: SQLite database `data/tasks.db` via GET/PUT /api/tasks when the local server runs (source of truth); localStorage (`todos`, `nextNum`) is the offline copy and the only store on GitHub Pages. Attachment files stay in IndexedDB.
- Backups: POST /api/backup, GET /api/backups; owner restores via "⋯ Backup → Restore…".
- server.py — http://127.0.0.1:8000 (use 127.0.0.1, not localhost). Max = Ollama qwen2.5:3b; Python does dates, #numbers, command words, Thai times. The server only serves the public app files; private data goes through /api/*.
- **Test mode:** `python server.py --test` runs a second copy on http://127.0.0.1:8001 with its own files (`data/test-tasks.db`, `data/test-*.json`, `backups-test/`; all gitignored) and a red "TEST MODE" badge. Test there; use the real 8000 database only when a check truly needs it.
- **Automatic tests:** run `python -m unittest` in this folder (Max's date/command logic, no AI needed) before reporting any server.py change.
- After changing server.py, restart it (Start-Process python server.py, minimized) and confirm 200.
- Bump `?v=` in index.html when script.js/style.css change.
- status.json / inbox.json / ideas.json / backups/ are private (gitignored). Update your own entry in status.json when you start/finish.
- Toto uploads to GitHub (main / GitHub Pages = live) only when the owner says so. Pushing to a `claude/*` branch is OK without asking (owner, 11 Nov 2026).

## Dot level (added 10 Nov 2026, see claude-config\SYSTEM-DESIGN-v1.md)
- Level: **do then tell me**. Deploy, push to main / going live, delete, kill programs, startup changes = always ask.
  Exception: `git push` to a `claude/*` branch (work in progress, not live) = do then tell me.
- Cloud runs: later, only if a private repo is approved.
- Keep `STATUS.md` up to date (5-10 lines) at the end of each work session. Run reports go to `D:\My Drive\Dev Project\_reports\`.

