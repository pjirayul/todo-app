# To-do app — team rules

Team: Toto (lead/coordinator), Kimi (developer), George (designer), Lewis (researcher).
The owner is a beginner builder; keep code simple, readable, and explained.

## Always back up before modifying anything
1. **Code backup:** before editing any file, make a local Git snapshot:
   `git -C C:\dev\todo-app add -A` then `git -C C:\dev\todo-app commit -m "Backup before <what you're about to do>"`.
   then tag it so it is never lost when Toto syncs with GitHub: `git -C C:\dev\todo-app tag backup-YYYYMMDD-HHMMSS`.
   (Local only — never push. If there is nothing to commit, still add the tag.) List backups: `git tag -l "backup-*"`.
2. **Task backup:** before testing in the browser or changing anything that touches saved tasks,
   save the owner's data first: call `POST /api/backup` from the page (or click "Back up now"),
   which writes `backups/tasks-YYYYMMDD-HHMMSS.json`. Restore exactly afterwards.
3. Never delete or overwrite files in `backups/` yourself. (The server rotates them automatically: newest 50 task backups and 30 daily database copies are kept.)

## How the app works
- index.html / style.css / script.js — plain HTML/CSS/JS.
- Tasks: SQLite database `data/tasks.db` via GET/PUT /api/tasks when the local server runs (source of truth); localStorage (`todos`, `nextNum`) is the offline copy and the only store on GitHub Pages. Attachment files stay in IndexedDB.
- Backups: POST /api/backup, GET /api/backups; owner restores via "⋯ Backup → Restore…".
- server.py — http://127.0.0.1:8000 (use 127.0.0.1, not localhost). AI via Ollama qwen2.5:3b; Python does date math.
- After changing server.py, restart it (Start-Process python server.py, minimized) and confirm 200.
- Bump `?v=` in index.html when script.js/style.css change.
- status.json / inbox.json / ideas.json / backups/ are private (gitignored). Update your own entry in status.json when you start/finish.
- Toto uploads to GitHub only when the owner says so.
