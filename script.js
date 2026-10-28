// ---------- 1. Translations (English / Thai) ----------
const TEXT = {
  en: {
    title: "My Tasks", placeholder: "e.g. pay rent on the 5th of next month, urgent", add: "✨ Add", category: "Category",
    save: "Save", cancel: "Cancel", aiOff: "AI is offline, task added without date/category.",
    aiToday: "AI used today", limitAsk: "Daily AI limit in tokens (one task ≈ 1,500):", notes: "Details / notes…",
    limitHit: "Today's AI limit is reached, task added without AI. Click the usage bar to raise the limit.",
    low: "Low", med: "Medium", high: "High", search: "Search tasks…",
    sortManual: "My order", sortDue: "Due date", sortPriority: "Priority",
    all: "All", active: "Active", done: "Done", overdue: "Overdue", clear: "Clear done",
    empty: "Nothing here yet 🎉", left: (n) => `${n} task${n === 1 ? "" : "s"} left`,
    remind: "Task due", editHint: "Double-click to edit", locale: "en-GB", thinking: "✨ …",
  },
  th: {
    title: "งานของฉัน", placeholder: "เช่น จ่ายค่าเช่าวันที่ 5 เดือนหน้า ด่วน", add: "✨ เพิ่ม", category: "หมวดหมู่",
    save: "บันทึก", cancel: "ยกเลิก", aiOff: "AI ไม่ทำงาน เพิ่มงานโดยไม่มีวันที่/หมวดหมู่",
    aiToday: "AI ที่ใช้วันนี้", limitAsk: "ขีดจำกัด AI ต่อวัน (โทเคน, 1 งาน ≈ 1,500):", notes: "รายละเอียด / โน้ต…",
    limitHit: "ใช้ AI ครบขีดจำกัดวันนี้แล้ว เพิ่มงานโดยไม่ใช้ AI กดที่แถบเพื่อเพิ่มขีดจำกัด",
    low: "ต่ำ", med: "กลาง", high: "สูง", search: "ค้นหางาน…",
    sortManual: "ลำดับของฉัน", sortDue: "วันครบกำหนด", sortPriority: "ความสำคัญ",
    all: "ทั้งหมด", active: "ยังไม่เสร็จ", done: "เสร็จแล้ว", overdue: "เลยกำหนด", clear: "ลบงานที่เสร็จ",
    empty: "ยังไม่มีงาน 🎉", left: (n) => `เหลือ ${n} งาน`,
    remind: "ถึงเวลางาน", editHint: "ดับเบิลคลิกเพื่อแก้ไข", locale: "th-TH", thinking: "✨ …",
  },
};

// ---------- 2. Saved data and settings ----------
const load = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
};
const save = (key, value) => {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
};

// A task looks like: { id, text, done, due, priority, cat, notified }
// Older saved tasks get defaults for the new fields
let todos = load("todos", []).map((x) => ({ due: "", priority: "med", cat: "", notified: false, notes: "", files: [], ...x }));
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

const $ = (id) => document.getElementById(id);
const t = (key) => TEXT[settings.lang][key];
const PRIORITY_RANK = { high: 0, med: 1, low: 2 };

const saveTodos = () => save("todos", todos);
const isOverdue = (todo) => todo.due && !todo.done && new Date(todo.due) < new Date();

// ---------- 3. Draw everything ----------
function render() {
  // Apply language and theme
  document.documentElement.lang = settings.lang;
  document.documentElement.dataset.theme = settings.theme;
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
  if ($("add-btn").disabled) $("add-btn").textContent = t("thinking"); // still waiting for AI
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => (el.placeholder = t(el.dataset.i18nPh)));
  $("lang").textContent = settings.lang === "en" ? "TH" : "EN";
  $("theme").textContent = settings.theme === "dark" ? "☀️" : "🌙";
  $("notify").classList.toggle("on", "Notification" in window && Notification.permission === "granted");
  $("today").textContent = new Date().toLocaleDateString(t("locale"), { weekday: "long", day: "numeric", month: "long" });

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
    return x.text.toLowerCase().includes(view.search.toLowerCase());
  });
  if (view.sort === "due") visible.sort((a, b) => (a.due || "9999").localeCompare(b.due || "9999"));
  if (view.sort === "priority") visible.sort((a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]);

  const list = $("todo-list");
  list.innerHTML = visible.length ? "" : `<li class="empty">${t("empty")}</li>`;
  const canDrag = view.sort === "manual" && !view.search;

  for (const todo of visible) {
    const li = document.createElement("li");
    li.className = `todo-item p-${todo.priority}${todo.done ? " done" : ""}`;
    li.dataset.id = todo.id;
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
      ? `<span class="due ${isOverdue(todo) ? "overdue" : ""}">📅 ${new Date(todo.due).toLocaleString(t("locale"), { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>`
      : "";
    li.innerHTML = `
      <input type="checkbox" class="check" ${todo.done ? "checked" : ""}>
      <div class="body">
        <div class="text" title="${t("editHint")}">${escapeHtml(todo.text)}</div>
        <div class="meta">${due}${todo.cat ? `<span class="tag">#${escapeHtml(todo.cat)}</span>` : ""}</div>
        ${todo.notes ? `<div class="notes">${escapeHtml(todo.notes)}</div>` : ""}
        ${todo.files.length ? `<div class="files">${todo.files.map((f) =>
          `<a class="file" href="#" data-file="${f.id}" title="Open">📎 ${escapeHtml(f.name)}<button class="rm" data-rm="${f.id}" title="Remove">×</button></a>`).join("")}</div>` : ""}
      </div>
      <button class="edit" title="Edit">✎</button>
      <button class="delete" title="Delete">×</button>`;
    list.append(li);
  }

  const left = todos.filter((x) => !x.done).length;
  $("counter").textContent = t("left")(left);
}

// Typed text must never run as HTML
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

const findTodo = (el) => todos.find((x) => x.id === Number(el.closest(".todo-item").dataset.id));
const update = () => { saveTodos(); render(); };

// ---------- 4. Add a task (always through AI) ----------
// Enter or ✨ Add sends the sentence to our server, where AI fills in date, priority and category.
// If the AI is unreachable (e.g. on GitHub Pages), the task is still added with just its text.
$("todo-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = $("todo-input").value.trim();
  if (!text) return;
  const button = $("add-btn");
  const input = $("todo-input");
  button.disabled = input.disabled = true;
  button.textContent = t("thinking");
  let task = { text, due: "", priority: "med", category: "" };
  let problem = ""; // message to show after the box is usable again
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
        }),
        signal: AbortSignal.timeout(30000), // a stuck AI must not freeze the box forever
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`); // e.g. GitHub Pages sends an HTML error page
      const data = await res.json();
      if (!data.text) throw new Error("AI gave no task");
      task = data;
      addUsage(data.tokens);
    } catch (err) {
      console.warn("AI unavailable:", err);
      problem = err.message === t("limitHit") ? t("limitHit") : t("aiOff");
    }
    todos.push({ id: Date.now() + Math.random(), text: task.text, done: false, due: task.due || "", priority: task.priority || "med", cat: task.category || "", notified: false, notes: "", files: [] });
    input.value = "";
    update();
  } finally {
    // Always give the box back, even if something above went wrong
    button.disabled = input.disabled = false;
    button.textContent = t("add");
    input.focus();
  }
  if (problem) alert(problem);
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
    todo.files = todo.files.filter((f) => f.id !== e.target.dataset.rm);
    deleteFile(e.target.dataset.rm);
    update();
  } else if (e.target.closest("[data-file]")) {
    // Open an attachment in a new tab
    e.preventDefault();
    const blob = await getFile(e.target.closest("[data-file]").dataset.file);
    if (blob) window.open(URL.createObjectURL(blob), "_blank");
  } else if (e.target.classList.contains("check")) {
    findTodo(e.target).done = e.target.checked;
    update();
  } else if (e.target.classList.contains("delete")) {
    const todo = findTodo(e.target);
    deleteTaskFiles(todo);
    todos = todos.filter((x) => x !== todo);
    update();
  } else if (e.target.classList.contains("edit")) {
    openEditor(findTodo(e.target));
  } else if (e.target.classList.contains("e-cancel")) {
    editingId = null;
    render();
  }
});

// Double-click a task to edit it too
$("todo-list").addEventListener("dblclick", (e) => {
  if (e.target.closest(".text")) openEditor(findTodo(e.target));
});

// Save the edit form (Enter in any field, or the Save button); Escape cancels
$("todo-list").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const todo = findTodo(form);
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

// Follow the computer's dark mode the first time
if (firstVisit && matchMedia("(prefers-color-scheme: dark)").matches) settings.theme = "dark";
render();
checkReminders();
