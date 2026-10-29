// ---------- 1. Translations (English / Thai) ----------
const TEXT = {
  en: {
    title: "Just Say It",placeholder: "Tell Max… e.g. pay rent on the 5th · move #2 to friday",
    placeholderShort: "Tell Max… e.g. move #2 to Fri", add: "Go", category: "Category",
    save: "Save", cancel: "Cancel", aiOff: "Max is offline, so the task was added without date/category.",
    aiToday: "AI used today", limitAsk: "Daily AI limit in tokens (one task ≈ 1,500):", notes: "Details / notes…",
    limitHit: "Today's AI limit is reached, task added without AI. Click the usage bar to raise the limit.",
    low: "Low", med: "Medium", high: "High", search: "Search tasks…",
    sortManual: "My order", sortDue: "Due date", sortPriority: "Priority",
    all: "All", active: "Active", done: "Done", overdue: "Overdue", clear: "Clear done",
    empty: "Nothing here yet", left: (n) => `${n} task${n === 1 ? "" : "s"} left`,
    remind: "Task due", editHint: "Double-click to edit", locale: "en-GB", thinking: "…",
    notFound: (q) => `Couldn't find task "${q}"`, which: (nums) => `Which one? ${nums}`,
    nothing: "Nothing to change. Try e.g. \"move #2 to friday\".", sureDelete: (x) => `Delete ${x}?`, yes: "Yes, delete", no: "No",
    cmdOffline: "Max is offline, so only \"done #2\", \"undo #2\" and \"delete #2\" work right now.",
    backupMenu: "Backup", backupNow: "Back up now", restore: "Restore…", exportFile: "Export file", importFile: "Import file",
    backupNote: "Your tasks are backed up automatically before changes. File attachments are not included.",
    backupDone: (name) => `Backed up: ${name}`, noBackups: "No backups yet.", tasksN: (n) => `${n} task${n === 1 ? "" : "s"}`,
    backupFail: "Couldn't reach the app server, so nothing was backed up. Use \"Export file\" instead.",
    sureRestore: (when, n) => `Replace your tasks with the backup from ${when} (${n})? Your current tasks are backed up first.`,
    sureImport: (n) => `Replace your tasks with ${n} from this file? Your current tasks are backed up first.`,
    yesRestore: "Yes, restore", yesImport: "Yes, import", restored: (n) => `Done. You now have ${n}.`,
    badFile: "That file isn't a task export from this app.",
    changedElsewhere: "Your tasks were changed in another window, so the latest list is shown. This window's last change was saved as a backup (Backup › Restore).",
    breakdown: "Break it down", stepsThinking: "Max is thinking of steps…", addSelected: "Add selected",
    stepsOffline: "Break it down needs Max, the AI server on your PC.", stepsFail: "Max couldn't come up with steps right now. Is Ollama running? Try again.",
    stepsPick: "Max suggests these steps. Pick the ones to add:", removeStep: "Remove step",
    morning: "Good morning", afternoon: "Good afternoon", evening: "Good evening", comma: ", ",
    dueToday: (n) => `${n} due today`, overdueN: (n) => `${n} overdue`, nothingDue: "Nothing due today",
    team: "Team", teamWorking: (n) => ` · ${n} working`,
    maxThinking: "Max is thinking…", maxReady: "Max ready", maxOffline: "Max offline",
    maxAdded: (n, text, when) => `Max added #${n}: ${text}${when ? " · " + when : ""}`, maxUpdated: (n) => `Max updated #${n}`,
    maxDone: (n) => `Max marked #${n} done`, maxUndone: (n) => `Max reopened #${n}`,
  },
  th: {
    title: "บอกมาได้เลย",placeholder: "บอก Max… เช่น จ่ายค่าเช่าวันที่ 5 · เลื่อน #2 เป็นวันศุกร์",
    placeholderShort: "บอก Max… เช่น เลื่อน #2 เป็นศุกร์", add: "ทำ", category: "หมวดหมู่",
    save: "บันทึก", cancel: "ยกเลิก", aiOff: "Max ออฟไลน์อยู่ จึงเพิ่มงานโดยไม่มีวันที่/หมวดหมู่",
    aiToday: "AI ที่ใช้วันนี้", limitAsk: "ขีดจำกัด AI ต่อวัน (โทเคน, 1 งาน ≈ 1,500):", notes: "รายละเอียด / โน้ต…",
    limitHit: "ใช้ AI ครบขีดจำกัดวันนี้แล้ว เพิ่มงานโดยไม่ใช้ AI กดที่แถบเพื่อเพิ่มขีดจำกัด",
    low: "ต่ำ", med: "กลาง", high: "สูง", search: "ค้นหางาน…",
    sortManual: "ลำดับของฉัน", sortDue: "วันครบกำหนด", sortPriority: "ความสำคัญ",
    all: "ทั้งหมด", active: "ยังไม่เสร็จ", done: "เสร็จแล้ว", overdue: "เลยกำหนด", clear: "ลบงานที่เสร็จ",
    empty: "ยังไม่มีงาน", left: (n) => `เหลือ ${n} งาน`,
    remind: "ถึงเวลางาน", editHint: "ดับเบิลคลิกเพื่อแก้ไข", locale: "th-TH", thinking: "…",
    notFound: (q) => `ไม่พบงาน "${q}"`, which: (nums) => `หมายถึงงานไหน? ${nums}`,
    nothing: "ไม่มีอะไรให้เปลี่ยน ลองพิมพ์ เช่น \"เลื่อน #2 เป็นวันศุกร์\"", sureDelete: (x) => `ลบ ${x} ใช่ไหม?`, yes: "ใช่ ลบเลย", no: "ไม่",
    cmdOffline: "Max ออฟไลน์อยู่ ตอนนี้ใช้ได้แค่ \"เสร็จ #2\", \"undo #2\" และ \"ลบ #2\"",
    backupMenu: "สำรองข้อมูล", backupNow: "สำรองตอนนี้", restore: "กู้คืน…", exportFile: "ส่งออกไฟล์", importFile: "นำเข้าไฟล์",
    backupNote: "แอปสำรองงานให้อัตโนมัติก่อนทุกการแก้ไข แต่ไม่รวมไฟล์แนบ",
    backupDone: (name) => `สำรองแล้ว: ${name}`, noBackups: "ยังไม่มีข้อมูลสำรอง", tasksN: (n) => `${n} งาน`,
    backupFail: "ติดต่อเซิร์ฟเวอร์ของแอปไม่ได้ จึงยังไม่ได้สำรอง ใช้ \"ส่งออกไฟล์\" แทนได้",
    sureRestore: (when, n) => `แทนที่งานทั้งหมดด้วยข้อมูลสำรองเมื่อ ${when} (${n}) ใช่ไหม? งานปัจจุบันจะถูกสำรองไว้ก่อน`,
    sureImport: (n) => `แทนที่งานทั้งหมดด้วย ${n} จากไฟล์นี้ใช่ไหม? งานปัจจุบันจะถูกสำรองไว้ก่อน`,
    yesRestore: "ใช่ กู้คืน", yesImport: "ใช่ นำเข้า", restored: (n) => `เรียบร้อย ตอนนี้มี ${n}`,
    badFile: "ไฟล์นี้ไม่ใช่ไฟล์งานที่ส่งออกจากแอปนี้",
    changedElsewhere: "งานถูกแก้ไขจากหน้าต่างอื่น จึงแสดงรายการล่าสุด การแก้ไขล่าสุดของหน้านี้ถูกสำรองไว้ (สำรองข้อมูล › กู้คืน)",
    breakdown: "แตกเป็นขั้นตอน", stepsThinking: "Max กำลังคิดขั้นตอน…", addSelected: "เพิ่มที่เลือก",
    stepsOffline: "การแตกเป็นขั้นตอนต้องใช้ Max (เซิร์ฟเวอร์ AI บนคอมของคุณ)", stepsFail: "Max ยังคิดขั้นตอนไม่ออกตอนนี้ Ollama เปิดอยู่ไหม? ลองอีกครั้ง",
    stepsPick: "Max แนะนำขั้นตอนเหล่านี้ เลือกที่จะเพิ่ม:", removeStep: "ลบขั้นตอน",
    morning: "สวัสดีตอนเช้า", afternoon: "สวัสดีตอนบ่าย", evening: "สวัสดีตอนเย็น", comma: " ",
    dueToday: (n) => `ครบกำหนดวันนี้ ${n}`, overdueN: (n) => `เลยกำหนด ${n}`, nothingDue: "ไม่มีงานครบกำหนดวันนี้",
    team: "ทีม", teamWorking: (n) => ` · ทำงานอยู่ ${n}`,
    maxThinking: "Max กำลังคิด…", maxReady: "Max พร้อม", maxOffline: "Max ออฟไลน์",
    maxAdded: (n, text, when) => `Max เพิ่ม #${n}: ${text}${when ? " · " + when : ""} แล้ว`, maxUpdated: (n) => `Max แก้ #${n} แล้ว`,
    maxDone: (n) => `Max ทำเครื่องหมาย #${n} ว่าเสร็จแล้ว`, maxUndone: (n) => `Max เปิด #${n} ใหม่แล้ว`,
  },
};

// The owner's name in the greeting ("Good morning, Jirayu") — change it here
const OWNER_NAME = "Jirayu";

// ---------- 2. Saved data and settings ----------
const load = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
};
const save = (key, value) => {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
};

// A task looks like: { id, num, text, done, due, priority, cat, notified, notes, files, steps }
// steps is the task's checklist from "Break it down": [{ text, done }]
// Older saved tasks get defaults for the new fields
let todos = load("todos", []).map((x) => ({ due: "", priority: "med", cat: "", notified: false, notes: "", files: [], steps: [], ...x }));

// Every task gets a number (#1, #2…) to refer to it in commands. Numbers never change and are
// never reused, even after a delete, so "#3" always means the same task.
let nextNum = load("nextNum", 1);
for (const x of todos) {
  nextNum = Math.max(nextNum, (x.num || 0) + 1);
}
for (const x of todos) {
  if (!x.num) x.num = nextNum++; // older tasks get numbers in their current order
}
save("nextNum", nextNum);
save("todos", todos); // keep the new numbers, so a reload doesn't number them again
const newNum = () => { save("nextNum", nextNum + 1); return nextNum++; };
const firstVisit = load("settings", null) === null;
let settings = { lang: "en", theme: "light", aiLimit: 20000, ...load("settings", {}) };

// AI tokens used today; resets when the date changes
const todayKey = () => new Date().toLocaleDateString("en-CA");
let usage = load("usage", { day: todayKey(), tokens: 0 });
const usageToday = () => (usage.day === todayKey() ? usage.tokens : 0);
function addUsage(tokens) {
  usage = { day: todayKey(), tokens: usageToday() + (tokens || 0) };
  save("usage", usage);
}

// Attachments are stored in the browser's IndexedDB (localStorage is too small for files)
const fileDb = new Promise((resolve, reject) => {
  const req = indexedDB.open("todo-files", 1);
  req.onupgradeneeded = () => req.result.createObjectStore("files");
  req.onsuccess = () => resolve(req.result);
  req.onerror = () => reject(req.error);
});
async function fileStore(mode, action) {
  const db = await fileDb;
  return new Promise((resolve, reject) => {
    const req = action(db.transaction("files", mode).objectStore("files"));
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
const putFile = (id, blob) => fileStore("readwrite", (s) => s.put(blob, id));
const getFile = (id) => fileStore("readonly", (s) => s.get(id));
const deleteFile = (id) => fileStore("readwrite", (s) => s.delete(id));
const deleteTaskFiles = (todo) => (todo.files || []).forEach((f) => deleteFile(f.id));
let view = { filter: "all", cat: "", search: "", sort: "manual" };
let editingId = null; // the task whose edit form is open
// "Break it down" suggestions on screen (nothing is saved until "Add selected"):
// { id: task id, loading: true } while the AI thinks, then { id, steps: [...], picked: [true, ...] },
// or { id, msg } when something went wrong
let suggest = null;

const $ = (id) => document.getElementById(id);
const t = (key) => TEXT[settings.lang][key];
const phone = matchMedia("(max-width: 480px)"); // same width as the phone layout in style.css
const PRIORITY_RANK = { high: 0, med: 1, low: 2 };

// Save in this browser, and (on the local app) in the tasks database too
const saveTodos = () => { save("todos", todos); saveToDb(); };
const isOverdue = (todo) => todo.due && !todo.done && new Date(todo.due) < new Date();

// ---------- 3. Draw everything ----------
// Grey hint text in the boxes. On phones the box is narrow, so use the short version if there is one.
function setPlaceholders() {
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    const key = el.dataset.i18nPh;
    el.placeholder = t(phone.matches && TEXT.en[key + "Short"] ? key + "Short" : key);
  });
}

function render() {
  // Apply language and theme
  document.documentElement.lang = settings.lang;
  document.documentElement.dataset.theme = settings.theme;
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  document.title = t("title"); // browser tab shows the app name in the chosen language
  if ($("add-btn").disabled) $("add-btn").textContent = t("thinking"); // still waiting for AI
  setPlaceholders();
  $("lang").textContent = settings.lang === "en" ? "TH" : "EN";
  // Line icon: a sun in dark mode (click for light), a moon in light mode
  $("theme").innerHTML = `<svg class="i"><use href="#i-${settings.theme === "dark" ? "sun" : "moon"}"/></svg>`;
  $("notify").classList.toggle("on", "Notification" in window && Notification.permission === "granted");
  drawGreeting();

  // AI usage bar: green, then yellow from 70%, red when full
  const used = usageToday();
  const pct = Math.min(100, (used / settings.aiLimit) * 100);
  $("usage-text").textContent = `${used.toLocaleString()} / ${settings.aiLimit.toLocaleString()} tokens`;
  $("usage-fill").style.width = `${pct}%`;
  $("usage-fill").className = pct >= 100 ? "full" : pct >= 70 ? "warn" : "";

  // Category chips + suggestions
  const cats = [...new Set(todos.map((x) => x.cat).filter(Boolean))];
  $("cat-list").innerHTML = cats.map((c) => `<option value="${escapeHtml(c)}">`).join("");
  $("cat-filters").innerHTML = cats
    .map((c) => `<button class="chip ${view.cat === c ? "active" : ""}" data-cat="${escapeHtml(c)}">#${escapeHtml(c)}</button>`)
    .join("");

  // Pick which tasks to show
  let visible = todos.filter((x) => {
    if (view.filter === "active" && x.done) return false;
    if (view.filter === "done" && !x.done) return false;
    if (view.filter === "overdue" && !isOverdue(x)) return false;
    if (view.cat && x.cat !== view.cat) return false;
    const num = view.search.trim().match(/^#(\d+)$/); // "#3" finds task number 3
    if (num) return x.num === Number(num[1]);
    return x.text.toLowerCase().includes(view.search.toLowerCase());
  });
  if (view.sort === "due") visible.sort((a, b) => (a.due || "9999").localeCompare(b.due || "9999"));
  if (view.sort === "priority") visible.sort((a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]);

  const list = $("todo-list");
  list.innerHTML = visible.length ? "" : `<li class="empty"><svg class="i" aria-hidden="true"><use href="#i-check-circle"/></svg>${t("empty")}</li>`;
  const canDrag = view.sort === "manual" && !view.search;

  for (const todo of visible) {
    const li = document.createElement("li");
    li.className = `todo-item p-${todo.priority}${todo.done ? " done" : ""}`;
    li.dataset.id = todo.id;
    li.dataset.num = todo.num;
    li.draggable = canDrag;

    // Manual editing: text, date, priority and category in one small form
    if (todo.id === editingId) {
      li.classList.add("editing");
      li.draggable = false;
      const opt = (v) => `<option value="${v}" ${todo.priority === v ? "selected" : ""}>${t(v)}</option>`;
      li.innerHTML = `
        <form class="body edit-form">
          <div class="edit-row">
            <input class="e-text" value="${escapeHtml(todo.text)}" required>
            <input class="e-due" type="datetime-local" value="${todo.due}">
            <select class="e-priority">${opt("low")}${opt("med")}${opt("high")}</select>
            <input class="e-cat" list="cat-list" value="${escapeHtml(todo.cat)}" placeholder="${t("category")}">
            <textarea class="e-notes" placeholder="${t("notes")}">${escapeHtml(todo.notes)}</textarea>
            <input class="e-files" type="file" multiple title="Attach files">
            <button type="submit" class="primary">${t("save")}</button>
            <button type="button" class="e-cancel">${t("cancel")}</button>
          </div>
        </form>`;
      list.append(li);
      continue;
    }

    const due = todo.due
      ? `<span class="due ${isOverdue(todo) ? "overdue" : ""}"><svg class="i sm" aria-hidden="true"><use href="#i-calendar"/></svg>${new Date(todo.due).toLocaleString(t("locale"), { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>`
      : "";
    // Checklist progress, e.g. "2/5"
    const stepsDone = todo.steps.filter((s) => s.done).length;
    const progress = todo.steps.length ? `<span class="steps-count"><svg class="i sm" aria-hidden="true"><use href="#i-steps"/></svg>${stepsDone}/${todo.steps.length}</span>` : "";
    li.innerHTML = `
      <input type="checkbox" class="check" ${todo.done ? "checked" : ""}>
      <div class="body">
        <div class="text" title="${t("editHint")}">${escapeHtml(todo.text)}</div>
        <div class="meta"><span class="num">#${todo.num}</span>${due}${todo.cat ? `<span class="tag">#${escapeHtml(todo.cat)}</span>` : ""}${progress}</div>
        ${todo.notes ? `<div class="notes">${escapeHtml(todo.notes)}</div>` : ""}
        ${todo.files.length ? `<div class="files">${todo.files.map((f) =>
          `<a class="file" href="#" data-file="${f.id}" title="Open"><svg class="i sm" aria-hidden="true"><use href="#i-paperclip"/></svg>${escapeHtml(f.name)}<button class="rm" data-rm="${f.id}" title="Remove" aria-label="Remove"><svg class="i sm" aria-hidden="true"><use href="#i-x"/></svg></button></a>`).join("")}</div>` : ""}
        ${stepsHtml(todo)}
        ${suggest?.id === todo.id ? suggestHtml() : ""}
      </div>
      <button class="edit breakdown" title="${t("breakdown")}" aria-label="${t("breakdown")}"><svg class="i" aria-hidden="true"><use href="#i-breakdown"/></svg></button>
      <button class="edit" title="Edit" aria-label="Edit"><svg class="i" aria-hidden="true"><use href="#i-pencil"/></svg></button>
      <button class="delete" title="Delete" aria-label="Delete"><svg class="i" aria-hidden="true"><use href="#i-trash"/></svg></button>`;
    list.append(li);
  }

  const left = todos.filter((x) => !x.done).length;
  $("counter").textContent = t("left")(left);
}

// Header greeting by time of day, and today's summary ("Thu 29 Oct · 3 due today · 1 overdue").
// Called from render(), which also runs every 30 s (reminders), so it follows the clock.
function drawGreeting() {
  const now = new Date();
  const hour = now.getHours();
  const part = hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening";
  const name = document.createElement("em"); // the name gets the gradient colour
  name.textContent = OWNER_NAME;
  $("greet").replaceChildren(t(part) + t("comma"), name);

  // Only tasks not done yet. "Due today" leaves out ones already overdue, so nothing is counted twice.
  const open = todos.filter((x) => !x.done);
  const overdue = open.filter(isOverdue).length;
  const dueToday = open.filter((x) => x.due && x.due.slice(0, 10) === todayKey() && !isOverdue(x)).length;
  const parts = [document.createTextNode(now.toLocaleDateString(t("locale"), { weekday: "short", day: "numeric", month: "short" }))];
  if (dueToday) {
    const b = document.createElement("b");
    b.textContent = t("dueToday")(dueToday);
    parts.push(" · ", b);
  }
  if (overdue) parts.push(" · " + t("overdueN")(overdue));
  if (!dueToday && !overdue) parts.push(" · " + t("nothingDue"));
  parts.push(" · ");
  $("summary").replaceChildren(...parts);
  drawMax(); // "Max ready" in the chosen language
}

// Team pill: the four agents' status dots from status.json (written by Toto on this PC).
// On GitHub Pages there is no status.json, so the pill just stays hidden.
const TEAM = ["Toto", "Kimi", "George", "Lewis"];
async function loadTeam() {
  try {
    const res = await fetch(`status.json?t=${Date.now()}`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const statusOf = (name) => data.agents?.find((a) => a.name === name)?.status;
    $("team-avs").replaceChildren(...TEAM.map((name) => {
      const av = document.createElement("span");
      av.className = `av av-${name.toLowerCase()}`;
      av.textContent = name[0];
      const dot = document.createElement("i");
      const status = statusOf(name);
      if (status === "working" || status === "done") dot.className = status; // anything else: grey (idle)
      av.title = `${name}: ${status || "idle"}`;
      av.append(dot);
      return av;
    }));
    const working = TEAM.filter((name) => statusOf(name) === "working").length;
    $("team-working").textContent = working ? t("teamWorking")(working) : "";
    $("team").hidden = false;
  } catch {
    $("team").hidden = true; // quietly: no team data here
  }
}

// Max's status (the AI on this PC): asks server.py, which checks that Ollama is running.
// On GitHub Pages there is no server, so Max simply shows as offline.
let maxReady = false;
function drawMax() {
  $("max-status").classList.toggle("ready", maxReady);
  $("max-text").textContent = t(maxReady ? "maxReady" : "maxOffline");
}
async function loadMax() {
  if (LOCAL) {
    try {
      const res = await fetch("api/max/status", { signal: AbortSignal.timeout(5000) });
      const data = await res.json();
      maxReady = res.ok && data.ready === true;
    } catch {
      maxReady = false;
    }
  }
  drawMax();
}

// The task's saved checklist: a tick box per step, and an x icon to remove it
function stepsHtml(todo) {
  if (!todo.steps.length) return "";
  return `<ul class="steps">${todo.steps.map((s, i) => `
    <li class="step${s.done ? " step-done" : ""}">
      <label><input type="checkbox" class="step-check" data-step="${i}" ${s.done ? "checked" : ""}> <span>${escapeHtml(s.text)}</span></label>
      <button type="button" class="step-rm" data-step="${i}" title="${t("removeStep")}" aria-label="${t("removeStep")}"><svg class="i sm" aria-hidden="true"><use href="#i-x"/></svg></button>
    </li>`).join("")}</ul>`;
}

// The AI's suggested steps: pick some, then "Add selected" or "Cancel"
function suggestHtml() {
  if (suggest.loading) return `<p class="cmd-msg suggest-msg">${t("stepsThinking")}</p>`;
  if (suggest.msg) {
    return `<p class="cmd-msg warn suggest-msg">${escapeHtml(suggest.msg)}
      <button type="button" class="chip suggest-cancel">${t("cancel")}</button></p>`;
  }
  return `<div class="suggest">
    <p class="suggest-title"><svg class="i sm" aria-hidden="true"><use href="#i-wave"/></svg>${t("stepsPick")}</p>
    <ul class="steps">${suggest.steps.map((s, i) => `
      <li class="step"><label><input type="checkbox" class="suggest-pick" data-step="${i}" ${suggest.picked[i] ? "checked" : ""}> <span>${escapeHtml(s)}</span></label></li>`).join("")}
    </ul>
    <div class="chips">
      <button type="button" class="chip active suggest-add">${t("addSelected")}</button>
      <button type="button" class="chip suggest-cancel">${t("cancel")}</button>
    </div>
  </div>`;
}

// Typed text must never run as HTML
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

const findTodo = (el) => todos.find((x) => x.id === Number(el.closest(".todo-item").dataset.id));
const update = () => { saveTodos(); render(); };

// ---------- 4. The command bar: add a task, or change one ----------
// Enter or Go sends the sentence to our server. A normal sentence becomes a new task
// (AI fills in date, priority and category); "move #2 to friday", "delete laundry", "done #3"
// act on an existing task. If the AI is unreachable (e.g. on GitHub Pages), new tasks are still
// added with just their text, and the simplest commands ("done #2") still work.

// Short message under the box; textContent so typed text never runs as HTML.
// warn = true gives the amber warning look (something went wrong), otherwise a calm hint.
// box: which message box (the one under the command bar, or the one in the Backup menu)
const showMessage = (msg, warn = false, box = $("cmd-msg")) => {
  box.textContent = msg;
  box.className = warn ? "cmd-msg warn" : "cmd-msg";
};
$("todo-input").addEventListener("input", () => showMessage(""));

// Ask "Delete #4 …? [Yes] [No]" inside a message box. We don't use confirm(): some browsers
// block it and it silently says "no", so "delete #4" looked like it did nothing.
function askYesNo(box, questionText, yesText, onYes, onNo) {
  const question = document.createElement("span");
  question.textContent = questionText; // textContent: never runs as HTML
  const yes = document.createElement("button");
  yes.type = "button";
  yes.className = "chip active";
  yes.textContent = yesText;
  const no = document.createElement("button");
  no.type = "button";
  no.className = "chip";
  no.textContent = t("no");
  yes.addEventListener("click", () => { showMessage("", false, box); onYes(); });
  no.addEventListener("click", () => { showMessage("", false, box); onNo?.(); });
  const buttons = document.createElement("span");
  buttons.style.cssText = "display: flex; gap: 6px; flex: none"; // keep both buttons whole on narrow screens
  buttons.append(yes, no);
  box.className = "cmd-msg warn";
  box.replaceChildren(question, buttons);
}

function askDelete(todo) {
  askYesNo($("cmd-msg"), t("sureDelete")(`#${todo.num} "${todo.text}"`), t("yes"), () => {
    backup(`before delete #${todo.num}`, true);
    deleteTaskFiles(todo);
    todos = todos.filter((x) => x !== todo);
    update();
    $("todo-input").value = "";
    $("todo-input").focus();
  }, () => $("todo-input").focus());
}

// Briefly highlight the task a command just changed
function flash(num) {
  const li = document.querySelector(`.todo-item[data-num="${num}"]`);
  if (!li) return;
  // Remove the class when the animation ends, so the same row can flash again later
  li.classList.remove("flash");
  void li.offsetWidth; // forces the browser to notice the removal, so the animation restarts
  li.classList.add("flash");
  li.addEventListener("animationend", () => li.classList.remove("flash"), { once: true });
  li.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

// Without AI we only understand "done #2", "undo #2" and "delete #2" (same words as server.py)
function simpleCommand(text) {
  const low = text.toLowerCase();
  const num = low.match(/#\s*(\d+)/);
  let action = "";
  if (/^(undo|undone|uncheck|unmark|reopen|not done)\b|ยังไม่เสร็จ|ยกเลิกเสร็จ/.test(low)) action = "uncomplete";
  else if (/^(delete|remove|del|erase)\b|^ลบ/.test(low)) action = "delete";
  else if (/^(done|mark|tick|finished|completed)\b|\b(done|finished|completed)$|เสร็จ(แล้ว)?$|^เสร็จ/.test(low)) action = "complete";
  else if (/^#\s*\d/.test(low) || (/^(change|modify|move|rename|edit|update|reschedule|postpone)\b|^(เปลี่ยน|แก้|ย้าย|เลื่อน)/.test(low)
    && (num || /\sto\s|เป็น/.test(low)))) action = "update";
  if (!action) return null; // a normal new task
  return num && action !== "update" ? { action, num: Number(num[1]) } : { action: "offline" };
}

// Carry out a command from the server (or simpleCommand). Returns a message to show,
// "" when it worked, or null when there is nothing more to show (e.g. waiting for Yes/No).
function applyCommand(cmd) {
  if (cmd.missing !== undefined) {
    // Not found, or several tasks match: don't guess
    if (!cmd.choices?.length) return t("notFound")(cmd.missing);
    return t("which")(cmd.choices.map((n) => `#${n} ${todos.find((x) => x.num === n)?.text}`).join(" · "));
  }
  const todo = todos.find((x) => x.num === cmd.num);
  if (!todo) return t("notFound")(`#${cmd.num}`);
  if (cmd.action === "delete") {
    askDelete(todo); // deletes only after the owner clicks Yes
    return null;
  }
  if (cmd.action === "complete" || cmd.action === "uncomplete") {
    backup(`before ${cmd.action === "complete" ? "done" : "undo"} #${todo.num}`);
    todo.done = cmd.action === "complete";
  } else {
    // update: the server only sends the fields the command mentioned, so nothing else is wiped
    const c = cmd.changes;
    if (!c) return t("nothing");
    backup(`before update #${todo.num}`);
    if (c.text) todo.text = c.text;
    if (c.due) { todo.due = c.due; todo.notified = false; }
    if (c.priority) todo.priority = c.priority;
    if (c.category) todo.cat = c.category;
  }
  update();
  flash(todo.num);
  return "";
}

$("todo-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = $("todo-input").value.trim();
  if (!text) return;
  const button = $("add-btn");
  const input = $("todo-input");
  button.disabled = input.disabled = true;
  button.textContent = t("thinking");
  showMessage(t("maxThinking"));
  let task = { text, due: "", priority: "med", category: "" };
  let cmd = null;    // set when the sentence is a command for an existing task
  let problem = "";  // message to show after the box is usable again
  try {
    try {
      if (usageToday() >= settings.aiLimit) throw new Error(t("limitHit"));
      const now = new Date();
      const res = await fetch("api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          now: `${now.toLocaleDateString("en-CA")}T${now.toTimeString().slice(0, 5)} ${now.toLocaleDateString("en-US", { weekday: "long" })}`,
          categories: [...new Set(todos.map((x) => x.cat).filter(Boolean))],
          tasks: todos.map((x) => ({ num: x.num, text: x.text })), // so "#3" or "laundry" can be found
        }),
        signal: AbortSignal.timeout(30000), // a stuck AI must not freeze the box forever
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`); // e.g. GitHub Pages sends an HTML error page
      const data = await res.json();
      addUsage(data.tokens);
      if (data.action && data.action !== "add") cmd = data;
      else if (data.text) task = data;
      else throw new Error("AI gave no task");
    } catch (err) {
      console.warn("AI unavailable:", err);
      showMessage("");
      problem = err.message === t("limitHit") ? t("limitHit") : t("aiOff");
      cmd = simpleCommand(text);
      if (cmd?.action === "offline") {
        // A command we can't do without AI: keep the text so nothing is lost
        showMessage(problem === t("limitHit") ? problem : t("cmdOffline"), true);
        return;
      }
    }
    if (cmd) {
      showMessage("");
      const msg = applyCommand(cmd);
      if (msg === "") {
        input.value = ""; // worked: clear the box
        // Say what Max did (only when Max really did it, not the offline fallback)
        const done = { complete: "maxDone", uncomplete: "maxUndone", update: "maxUpdated" }[cmd.action];
        if (!problem && done) showMessage(t(done)(cmd.num));
      }
      if (msg) showMessage(msg, !cmd.choices?.length); // keep the text so the owner can fix it; "Which one?" is not a warning
      return;
    }
    backup(`before add "${task.text.slice(0, 40)}"`);
    const num = newNum();
    todos.push({ id: Date.now() + Math.random(), num, text: task.text, done: false, due: task.due || "", priority: task.priority || "med", cat: task.category || "", notified: false, notes: "", files: [], steps: [] });
    input.value = "";
    update();
    flash(num);
    if (!problem) {
      const when = task.due ? new Date(task.due).toLocaleString(t("locale"), { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "";
      showMessage(t("maxAdded")(num, task.text, when)); // textContent inside, so task text never runs as HTML
    }
  } finally {
    // Always give the box back, even if something above went wrong
    button.disabled = input.disabled = false;
    button.textContent = t("add");
    // A Yes/No question is waiting: put the focus on Yes, so Enter confirms the delete
    ($("cmd-msg").querySelector("button") || input).focus();
  }
  if (problem) showMessage(problem, true); // in-page: the owner's browser blocks alert()
});

// ---------- 5. Clicks inside the list: tick, edit, delete ----------
const openEditor = (todo) => {
  editingId = todo.id;
  render();
  document.querySelector(".editing .e-text")?.focus();
};

$("todo-list").addEventListener("click", async (e) => {
  if (e.target.dataset.rm) {
    // Remove one attachment
    e.preventDefault();
    const todo = findTodo(e.target);
    backup(`before removing a file from #${todo.num}`);
    todo.files = todo.files.filter((f) => f.id !== e.target.dataset.rm);
    deleteFile(e.target.dataset.rm);
    update();
  } else if (e.target.closest("[data-file]")) {
    // Open an attachment in a new tab
    e.preventDefault();
    const blob = await getFile(e.target.closest("[data-file]").dataset.file);
    if (blob) window.open(URL.createObjectURL(blob), "_blank");
  } else if (e.target.classList.contains("check")) {
    backup(`before ${e.target.checked ? "done" : "undo"} #${findTodo(e.target).num}`);
    findTodo(e.target).done = e.target.checked;
    update();
  } else if (e.target.classList.contains("delete")) {
    const todo = findTodo(e.target);
    backup(`before delete #${todo.num}`, true);
    deleteTaskFiles(todo);
    todos = todos.filter((x) => x !== todo);
    update();
  } else if (e.target.classList.contains("step-check")) {
    // Tick or untick one step of the checklist
    const todo = findTodo(e.target);
    backup(`before ticking a step of #${todo.num}`);
    todo.steps[Number(e.target.dataset.step)].done = e.target.checked;
    update();
  } else if (e.target.classList.contains("step-rm")) {
    const todo = findTodo(e.target);
    backup(`before removing a step from #${todo.num}`);
    todo.steps.splice(Number(e.target.dataset.step), 1);
    update();
  } else if (e.target.classList.contains("suggest-pick")) {
    // Remember the choice (the list is redrawn now and then, e.g. by reminders)
    suggest.picked[Number(e.target.dataset.step)] = e.target.checked;
  } else if (e.target.classList.contains("suggest-add")) {
    const todo = findTodo(e.target);
    const chosen = suggest.steps.filter((s, i) => suggest.picked[i]);
    suggest = null;
    if (!chosen.length) return render();
    backup(`before adding steps to #${todo.num}`);
    todo.steps.push(...chosen.map((text) => ({ text, done: false })));
    update();
  } else if (e.target.classList.contains("suggest-cancel")) {
    suggest = null;
    render();
  } else if (e.target.classList.contains("breakdown")) {
    breakDown(findTodo(e.target)); // checked before "edit": this button also has the edit class for its look
  } else if (e.target.classList.contains("edit")) {
    openEditor(findTodo(e.target));
  } else if (e.target.classList.contains("e-cancel")) {
    editingId = null;
    render();
  }
});

// "Break it down": ask the server's AI for 3-6 small steps and show them as suggestions.
// Nothing is saved here; the owner picks steps and clicks "Add selected".
async function breakDown(todo) {
  if (suggest?.loading) return; // one question at a time
  if (!LOCAL) { suggest = { id: todo.id, msg: t("stepsOffline") }; return render(); } // GitHub Pages: no AI server
  if (usageToday() >= settings.aiLimit) { suggest = { id: todo.id, msg: t("limitHit") }; return render(); }
  const mine = { id: todo.id, loading: true };
  suggest = mine;
  render();
  try {
    const res = await fetch("api/breakdown", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: todo.text, notes: todo.notes, due: todo.due }),
      signal: AbortSignal.timeout(60000), // a stuck AI must not leave "Thinking…" forever (server gives up first)
    });
    const data = await res.json();
    if (!res.ok || !Array.isArray(data.steps) || !data.steps.length) throw new Error(data.error || `HTTP ${res.status}`);
    addUsage(data.tokens);
    if (suggest !== mine) return; // cancelled, or another task was asked meanwhile
    const steps = data.steps.filter((s) => typeof s === "string");
    suggest = { id: todo.id, steps, picked: steps.map(() => true) };
  } catch (err) {
    console.warn("Break it down failed:", err);
    if (suggest === mine) suggest = { id: todo.id, msg: t("stepsFail") };
  } finally {
    if (editingId === null) render(); // don't wipe an open edit form
  }
}

// Double-click a task to edit it too
$("todo-list").addEventListener("dblclick", (e) => {
  if (e.target.closest(".text")) openEditor(findTodo(e.target));
});

// Save the edit form (Enter in any field, or the Save button); Escape cancels
$("todo-list").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const todo = findTodo(form);
  backup(`before edit #${todo.num}`);
  todo.text = form.querySelector(".e-text").value.trim() || todo.text;
  todo.due = form.querySelector(".e-due").value;
  todo.priority = form.querySelector(".e-priority").value;
  todo.cat = form.querySelector(".e-cat").value.trim();
  todo.notes = form.querySelector(".e-notes").value.trim();
  for (const file of form.querySelector(".e-files").files) {
    const id = `${todo.id}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    await putFile(id, file);
    todo.files.push({ id, name: file.name });
  }
  todo.notified = false; // a new date gets a new reminder
  editingId = null;
  update();
});
$("todo-list").addEventListener("keydown", (e) => {
  if (e.key === "Escape" && editingId !== null) { editingId = null; render(); }
});

// ---------- 6. Drag to reorder ----------
let dragId = null;
$("todo-list").addEventListener("dragstart", (e) => {
  const li = e.target.closest(".todo-item");
  dragId = Number(li.dataset.id);
  li.classList.add("dragging");
});
$("todo-list").addEventListener("dragover", (e) => {
  e.preventDefault();
  const over = e.target.closest(".todo-item");
  const dragged = document.querySelector(".dragging");
  if (!over || !dragged || over === dragged) return;
  const after = e.clientY > over.getBoundingClientRect().top + over.offsetHeight / 2;
  over[after ? "after" : "before"](dragged);
});
$("todo-list").addEventListener("dragend", () => {
  // Read the new order from the screen and apply it to the data
  const order = [...document.querySelectorAll(".todo-item")].map((li) => Number(li.dataset.id));
  const shown = todos.filter((x) => order.includes(x.id));
  const sorted = order.map((id) => shown.find((x) => x.id === id));
  let i = 0;
  todos = todos.map((x) => (order.includes(x.id) ? sorted[i++] : x));
  dragId = null;
  update();
});

// ---------- 7. Search, sort, filters, settings ----------
$("search").addEventListener("input", (e) => { view.search = e.target.value; render(); });
$("sort").addEventListener("change", (e) => { view.sort = e.target.value; render(); });

$("filters").addEventListener("click", (e) => {
  if (!e.target.dataset.filter) return;
  view.filter = e.target.dataset.filter;
  document.querySelectorAll("#filters .chip").forEach((c) => c.classList.toggle("active", c === e.target));
  render();
});
$("cat-filters").addEventListener("click", (e) => {
  if (e.target.dataset.cat === undefined) return;
  view.cat = view.cat === e.target.dataset.cat ? "" : e.target.dataset.cat; // click again to clear
  render();
});

$("clear-done").addEventListener("click", () => {
  if (!todos.some((x) => x.done)) return; // nothing to clear, so no backup needed
  backup("before clear done", true);
  todos.filter((x) => x.done).forEach(deleteTaskFiles);
  todos = todos.filter((x) => !x.done);
  update();
});

$("usage").addEventListener("click", () => {
  const answer = prompt(t("limitAsk"), settings.aiLimit);
  const limit = parseInt(String(answer).replace(/[^\d]/g, ""), 10);
  if (limit > 0) {
    settings.aiLimit = limit;
    save("settings", settings);
    render();
  }
});

$("lang").addEventListener("click", () => {
  settings.lang = settings.lang === "en" ? "th" : "en";
  save("settings", settings);
  render();
  loadTeam(); // "· 2 working" in the new language
});

// Phone: the three-dots button opens a small menu with language / dark mode / reminders.
// It stays open while you use it; a click outside or Escape closes it.
const setMenu = (open) => {
  $("quick").classList.toggle("open", open);
  $("more").setAttribute("aria-expanded", open);
};
$("more").addEventListener("click", () => setMenu(!$("quick").classList.contains("open")));
document.addEventListener("click", (e) => {
  // composedPath: the dark-mode button redraws its icon, so e.target may already be gone from the page
  if (!e.composedPath().some((el) => el.id === "quick" || el.id === "more")) setMenu(false);
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && $("quick").classList.contains("open")) { setMenu(false); $("more").focus(); }
});
$("theme").addEventListener("click", () => {
  settings.theme = settings.theme === "dark" ? "light" : "dark";
  save("settings", settings);
  render();
});

// ---------- 8. Reminders ----------
// Ask permission once; then every 30 seconds check for tasks that just became due.
$("notify").addEventListener("click", async () => {
  if (!("Notification" in window)) return alert("This browser doesn't support notifications.");
  await Notification.requestPermission();
  render();
});

function checkReminders() {
  let changed = false;
  for (const todo of todos) {
    if (todo.due && !todo.done && !todo.notified && new Date(todo.due) <= new Date()) {
      todo.notified = true;
      changed = true;
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification(t("remind"), { body: todo.text });
      }
    }
  }
  if (editingId !== null) return saveTodos(); // don't wipe an open edit form
  if (changed) update();
  else render(); // refresh "overdue" colors as time passes
}
setInterval(checkReminders, 30000);

// ---------- 9. Task backups ----------
// Tasks only live in this browser, so before changes we send a copy to server.py, which saves
// it in the backups/ folder. On GitHub Pages there is no server: backups are skipped silently
// (Export file still works there).
const LOCAL = ["127.0.0.1", "localhost"].includes(location.hostname);
const BACKUP_GAP = 2 * 60 * 1000; // at most one automatic backup per 2 minutes...
let lastBackup = 0;               // ...except "always" ones (delete, clear done, import, restore)

// Returns a promise with the backup's file name, or "" if it failed. Callers don't wait for it,
// so a slow or missing server never blocks the change itself.
// databaseOnly: back up what is in the tasks database, not this browser's list.
function backup(reason, always = false, databaseOnly = false) {
  if (!LOCAL) return Promise.resolve("");
  if (!always && Date.now() - lastBackup < BACKUP_GAP) return Promise.resolve("");
  lastBackup = Date.now();
  // JSON.stringify runs right now, so the copy is the data BEFORE the change
  const body = JSON.stringify(databaseOnly ? { reason } : { todos, nextNum, settings, usage, reason });
  return fetch("api/backup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    signal: AbortSignal.timeout(5000),
  })
    .then((res) => (res.ok ? res.json() : {}))
    .then((data) => data.name || "")
    .catch(() => "");
}

// One backup the first time the app is opened each day (skipped if today already has one)
async function dailyBackup() {
  if (!LOCAL) return;
  try {
    const res = await fetch("api/backups", { signal: AbortSignal.timeout(5000) });
    const list = await res.json();
    const today = todayKey().replaceAll("-", "");
    if (!list.some((b) => b.name.startsWith(`tasks-${today}`))) backup("daily backup", true);
  } catch {} // server not reachable: nothing to do
}

// Imported/restored tasks come from a file, so check every field before using it.
// Values that end up inside HTML (due, file ids) must have a safe, known format.
function cleanTodos(list) {
  if (!Array.isArray(list) || !list.every((x) => x && typeof x === "object" && typeof x.text === "string")) return null;
  const str = (v) => (typeof v === "string" ? v : "");
  return list.map((x, i) => ({
    id: Number(x.id) || Date.now() + i,
    num: Number.isInteger(x.num) && x.num > 0 ? x.num : 0,
    text: x.text,
    done: x.done === true,
    due: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(x.due) ? x.due : "",
    priority: ["low", "med", "high"].includes(x.priority) ? x.priority : "med",
    cat: str(x.cat),
    notified: x.notified === true,
    notes: str(x.notes),
    files: Array.isArray(x.files) ? x.files.filter((f) => f && /^[\w.-]+$/.test(f.id) && typeof f.name === "string") : [],
    steps: Array.isArray(x.steps)
      ? x.steps.filter((s) => s && typeof s.text === "string").map((s) => ({ text: s.text, done: s.done === true }))
      : [],
  }));
}

// Put a whole new task list in place (after Restore or Import)
function replaceTasks(list, savedNextNum) {
  todos = list;
  suggest = null;
  nextNum = Math.max(Number(savedNextNum) || 1, 1, ...todos.map((x) => x.num + 1));
  for (const x of todos) {
    if (!x.num) x.num = nextNum++;
  }
  save("nextNum", nextNum);
  editingId = null;
  update();
}

const backupMsg = (msg, warn = false) => showMessage(msg, warn, $("backup-msg"));

$("backup-now").addEventListener("click", async () => {
  backupMsg("…"); // an unreachable server can take a few seconds to answer
  const name = await backup("backed up by you", true);
  backupMsg(name ? t("backupDone")(name) : t("backupFail"), !name);
});

// Restore…: show the list of backups; clicking one asks Yes/No first
$("restore").addEventListener("click", async () => {
  const box = $("backup-list");
  backupMsg("");
  let list = [];
  try {
    list = await (await fetch("api/backups", { signal: AbortSignal.timeout(5000) })).json();
  } catch {
    return backupMsg(t("backupFail"), true);
  }
  if (!list.length) return backupMsg(t("noBackups"));
  box.replaceChildren(...list.map((b) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip";
    // textContent: the reason may contain task text, which must never run as HTML
    button.textContent = `${b.time.slice(0, 16)} · ${t("tasksN")(b.count)}${b.reason ? " · " + b.reason : ""}`;
    button.addEventListener("click", () => {
      askYesNo($("backup-msg"), t("sureRestore")(b.time.slice(0, 16), t("tasksN")(b.count)), t("yesRestore"), async () => {
        try {
          const data = await (await fetch(`api/backups/${encodeURIComponent(b.name)}`)).json();
          const tasks = cleanTodos(data.todos);
          if (!tasks) return backupMsg(t("badFile"), true);
          await backup(`before restore of ${b.name}`, true); // keep what we have now, just in case
          replaceTasks(tasks, data.nextNum);
          box.replaceChildren();
          backupMsg(t("restored")(t("tasksN")(todos.length)));
        } catch {
          backupMsg(t("backupFail"), true);
        }
      });
    });
    return button;
  }));
});

// Export file: download the tasks as JSON (works without the server, e.g. on GitHub Pages)
$("export").addEventListener("click", () => {
  const data = JSON.stringify({ app: "todo-app", exported: new Date().toISOString(), todos, nextNum }, null, 2);
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([data], { type: "application/json" }));
  link.download = `tasks-export-${todayKey()}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000); // give the download a moment to start
});

// Import file: read a JSON export, check it, ask Yes/No, back up, then replace
$("import").addEventListener("click", () => $("import-file").click());
$("import-file").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  e.target.value = ""; // so choosing the same file again still works
  if (!file) return;
  let data = null;
  try { data = JSON.parse(await file.text()); } catch {}
  const tasks = cleanTodos(Array.isArray(data) ? data : data?.todos); // a plain list is fine too
  if (!tasks) return backupMsg(t("badFile"), true);
  askYesNo($("backup-msg"), t("sureImport")(t("tasksN")(tasks.length)), t("yesImport"), async () => {
    await backup(`before import of ${file.name}`, true);
    replaceTasks(tasks, data?.nextNum);
    backupMsg(t("restored")(t("tasksN")(todos.length)));
  });
});

// Without the server there is nothing to back up to or restore from
$("backup-now").hidden = $("restore").hidden = !LOCAL;

// ---------- 10. Tasks database (server.py keeps them in data/tasks.db) ----------
// On the local app the database is the real list and localStorage is a copy for when the
// server is off. On GitHub Pages there is no server, so localStorage is all there is (as before).
// Attachments are not in the database: the files themselves stay in this browser (IndexedDB).
let dbState = LOCAL ? "loading" : "offline"; // "loading" -> "online" or "offline"
let dbVersion = null;  // the database version our list is based on
let saveTimer = null;  // a save is waiting (we wait 0.5 s so quick changes are sent together)
const UNSAVED = "dbUnsaved"; // localStorage flag: this browser has changes the database doesn't have yet
const setUnsaved = (on) => {
  try { on ? localStorage.setItem(UNSAVED, "1") : localStorage.removeItem(UNSAVED); } catch {}
};

// Called after every change (from saveTodos)
function saveToDb() {
  if (!LOCAL) return;
  if (dbState === "offline") return setUnsaved(true); // sent the next time the page opens with the server on
  clearTimeout(saveTimer);
  saveTimer = setTimeout(sendToDb, 500);
}

async function sendToDb(keepalive = false) {
  clearTimeout(saveTimer);
  saveTimer = null;
  if (dbState === "loading") { saveTimer = setTimeout(sendToDb, 500); return; } // wait for the first load
  if (dbState !== "online") return;
  try {
    const res = await fetch("api/tasks", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ todos, nextNum, baseVersion: dbVersion }),
      keepalive, // lets the save finish even while the page is closing
    });
    const data = await res.json();
    if (res.status === 409) {
      // Another tab or browser saved first. Keep this window's list in a backup, then show the latest.
      backup("this window's list (clashed with another window)", true);
      useDbData(data);
      showMessage(t("changedElsewhere"), true);
      return;
    }
    if (!res.ok) throw new Error(data.error);
    dbVersion = data.version;
    if (!saveTimer) setUnsaved(false); // saved, and nothing newer is waiting
  } catch (err) {
    console.warn("Couldn't save to the database; kept in this browser:", err);
    setUnsaved(true); // tried again on the next change or next page open
  }
}

// Show the database's list (and keep a copy in localStorage)
function useDbData(data) {
  todos = cleanTodos(data.todos) || [];
  nextNum = Math.max(Number(data.nextNum) || 1, 1, ...todos.map((x) => x.num + 1));
  dbVersion = data.version;
  save("todos", todos);
  save("nextNum", nextNum);
  setUnsaved(false);
  if (editingId === null) render(); // don't wipe an open edit form
}

// When the page opens: load the list from the database
async function startDb() {
  if (!LOCAL) return;
  let data;
  try {
    const res = await fetch("api/tasks", { signal: AbortSignal.timeout(5000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.warn("Database not reachable, using this browser's copy:", err);
    dbState = "offline";
    return;
  }
  dbState = "online";
  dbVersion = data.version;
  let unsaved = false;
  try { unsaved = localStorage.getItem(UNSAVED) === "1"; } catch {}
  if (JSON.stringify(cleanTodos(todos)) === JSON.stringify(cleanTodos(data.todos))) return useDbData(data); // already the same
  if (todos.length && (!data.todos.length || unsaved)) {
    // First run (empty database), or changes made here while the server was off: this browser's list wins.
    // Back up first: the empty-database case keeps this browser's list, the other keeps the database's.
    if (data.todos.length) await backup("database before saving offline changes", true, true);
    else await backup("before moving tasks into the database", true);
    return sendToDb();
  }
  // The database has a different list: it wins, but keep this browser's old copy in a backup first
  if (todos.length) await backup("this browser's old copy, before loading the database", true);
  useDbData(data);
}

// Coming back to this tab: pick up changes made in another tab or browser
async function refreshFromDb() {
  if (dbState !== "online" || saveTimer || editingId !== null) return;
  try {
    const data = await (await fetch("api/tasks", { signal: AbortSignal.timeout(5000) })).json();
    if (data.version !== dbVersion && !saveTimer && editingId === null) useDbData(data);
  } catch {} // server off for a moment: keep what we have
}
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") refreshFromDb(); });
window.addEventListener("focus", refreshFromDb);

// Closing the page within 0.5 s of a change: send it right away
window.addEventListener("pagehide", () => { if (saveTimer) sendToDb(true); });

// Follow the computer's dark mode the first time
if (firstVisit && matchMedia("(prefers-color-scheme: dark)").matches) settings.theme = "dark";
render(); // show this browser's copy right away...
startDb().finally(() => { // ...then the database's list (when the server is on)
  checkReminders();
  dailyBackup();
});
loadTeam();
loadMax();
setInterval(() => { loadTeam(); loadMax(); }, 30000); // team dots follow status.json; Max follows Ollama
// Phone turned or window resized past 480px: swap long/short placeholder
phone.addEventListener("change", setPlaceholders); // only the hints, so an open edit form is not redrawn
