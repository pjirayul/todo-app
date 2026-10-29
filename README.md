# Just Say It (บอกมาได้เลย)

A to-do list you can just talk to. Type a sentence like "pay rent on the 5th" or "เลื่อน #2 เป็นวันศุกร์"
and Max, a small AI that runs on your own PC, turns it into a task or changes one. Plain HTML, CSS and
JavaScript plus a small Python server — my first learning project.

## Features
- **Command bar with Max:** add tasks in English or Thai with dates, times, priority and category
  ("call mom tomorrow evening", "ส่งรายงานวันศุกร์ บ่ายสาม ด่วน"), or change them: `move #2 to friday`,
  `rename #3 to …`, `done #4`, `undo #4`, `delete laundry`. Every task has a fixed #number.
- **Break it down:** Max suggests 3–6 small steps for a task; pick the ones you want.
- Edit, notes, attachments, priority, categories, search, sort, filters, drag to reorder, reminders.
- Thai / English, light / dark mode, works on phones.
- **Backups:** automatic backups before changes, "Back up now", Restore, Export / Import file.
- Team Status page (`status.html`): Max's status, "About me" for Max, the builder team and ideas.

## How to run it on your PC (full app)
1. Install [Python](https://www.python.org/) and [Ollama](https://ollama.com/), then get Max's model once:
   `ollama pull qwen2.5:3b`
2. Start the Ollama app.
3. In this folder run `python server.py` and open **http://127.0.0.1:8000**

Your tasks are saved in `data/tasks.db` (plus a copy in the browser). Backups go to `backups/`.
These, and the other private files (status, inbox, About me), stay on your PC: they are not uploaded
and the server never hands them out.

## GitHub Pages (the online copy)
The online copy has no server, so it is a simpler offline version:
- Works: adding, ticking, editing, deleting tasks, search, filters, reminders, Thai/English, dark mode,
  Export / Import file. Tasks are kept only in that browser.
- Simple commands work without Max: `done #2`, `undo #2`, `delete #2`.
- Not there: Max (dates/categories from sentences, Break it down), the tasks database, Back up now / Restore,
  and the Team Status data.

## Files
- `index.html` — the page
- `style.css` — how it looks
- `script.js` — how it works (translations, list, command bar, backups)
- `status.html` — Team Status page
- `server.py` — local web server, Max (Ollama), dates, database and backups
