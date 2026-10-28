// ---------- 1. Translations (English / Thai) ----------
const TEXT = {
  en: {
    title: "My Tasks", placeholder: "What do you need to do?", add: "Add", category: "Category",
    low: "Low", med: "Medium", high: "High", search: "Search tasks…",
    sortManual: "My order", sortDue: "Due date", sortPriority: "Priority",
    all: "All", active: "Active", done: "Done", overdue: "Overdue", clear: "Clear done",
    empty: "Nothing here yet 🎉", left: (n) => `${n} task${n === 1 ? "" : "s"} left`,
    remind: "Task due", editHint: "Double-click to edit", locale: "en-GB",
    ai: "✨ AI", thinking: "✨ …", aiFail: "AI couldn't sort this task: ",
  },
  th: {
    title: "งานของฉัน", placeholder: "วันนี้ต้องทำอะไร?", add: "เพิ่ม", category: "หมวดหมู่",
    low: "ต่ำ", med: "กลาง", high: "สูง", search: "ค้นหางาน…",
    sortManual: "ลำดับของฉัน", sortDue: "วันครบกำหนด", sortPriority: "ความสำคัญ",
    all: "ทั้งหมด", active: "ยังไม่เสร็จ", done: "เสร็จแล้ว", overdue: "เลยกำหนด", clear: "ลบงานที่เสร็จ",
    empty: "ยังไม่มีงาน 🎉", left: (n) => `เหลือ ${n} งาน`,
    remind: "ถึงเวลางาน", editHint: "ดับเบิลคลิกเพื่อแก้ไข", locale: "th-TH",
    ai: "✨ AI", thinking: "✨ …", aiFail: "AI จัดหมวดงานนี้ไม่ได้: ",
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
let todos = load("todos", []).map((x) => ({ due: "", priority: "med", cat: "", notified: false, ...x }));
const firstVisit = load("settings", null) === null;
let settings = load("settings", { lang: "en", theme: "light" });
let view = { filter: "all", cat: "", search: "", sort: "manual" };

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
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => (el.placeholder = t(el.dataset.i18nPh)));
  $("lang").textContent = settings.lang === "en" ? "TH" : "EN";
  $("theme").textContent = settings.theme === "dark" ? "☀️" : "🌙";
  $("notify").classList.toggle("on", "Notification" in window && Notification.permission === "granted");
  $("today").textContent = new Date().toLocaleDateString(t("locale"), { weekday: "long", day: "numeric", month: "long" });

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

    const due = todo.due
      ? `<span class="due ${isOverdue(todo) ? "overdue" : ""}">📅 ${new Date(todo.due).toLocaleString(t("locale"), { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>`
      : "";
    li.innerHTML = `
      <input type="checkbox" class="check" ${todo.done ? "checked" : ""}>
      <div class="body">
        <div class="text" title="${t("editHint")}">${escapeHtml(todo.text)}</div>
        <div class="meta">${due}${todo.cat ? `<span class="tag">#${escapeHtml(todo.cat)}</span>` : ""}</div>
      </div>
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

// ---------- 4. Add a task ----------
$("todo-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("todo-input").value.trim();
  if (!text) return;
  todos.push({
    id: Date.now() + Math.random(),
    text,
    done: false,
    due: $("due-input").value,
    priority: $("priority-input").value,
    cat: $("cat-input").value.trim(),
    notified: false,
  });
  $("todo-input").value = "";
  $("due-input").value = "";
  $("todo-input").focus();
  update();
});

// ✨ AI: send the sentence to our server, which asks Claude to fill in date, priority and category
$("ai-add").addEventListener("click", async () => {
  const text = $("todo-input").value.trim();
  if (!text) return $("todo-input").focus();
  const button = $("ai-add");
  button.disabled = true;
  button.textContent = t("thinking");
  try {
    const now = new Date();
    const res = await fetch("api/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        now: `${now.toLocaleDateString("en-CA")}T${now.toTimeString().slice(0, 5)} ${now.toLocaleDateString("en-US", { weekday: "long" })}`,
        categories: [...new Set(todos.map((x) => x.cat).filter(Boolean))],
      }),
    });
    const task = await res.json();
    if (!res.ok) throw new Error(task.error || res.status);
    todos.push({ id: Date.now() + Math.random(), text: task.text, done: false, due: task.due, priority: task.priority, cat: task.category, notified: false });
    $("todo-input").value = "";
    update();
  } catch (err) {
    alert(t("aiFail") + err.message);
  } finally {
    button.disabled = false;
    button.textContent = t("ai");
  }
});

// ---------- 5. Clicks inside the list: tick, delete ----------
$("todo-list").addEventListener("click", (e) => {
  if (e.target.classList.contains("check")) {
    findTodo(e.target).done = e.target.checked;
    update();
  } else if (e.target.classList.contains("delete")) {
    const todo = findTodo(e.target);
    todos = todos.filter((x) => x !== todo);
    update();
  }
});

// Double-click to edit; Enter or clicking away saves, Escape cancels
$("todo-list").addEventListener("dblclick", (e) => {
  const el = e.target.closest(".text");
  if (!el) return;
  const todo = findTodo(el);
  el.contentEditable = "true";
  el.focus();
  document.getSelection().selectAllChildren(el);
  const finish = (keep) => {
    const text = el.textContent.trim();
    if (keep && text) todo.text = text;
    update();
  };
  el.onkeydown = (k) => {
    if (k.key === "Enter") { k.preventDefault(); el.onblur = null; finish(true); }
    if (k.key === "Escape") { el.onblur = null; finish(false); }
  };
  el.onblur = () => finish(true);
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

$("clear-done").addEventListener("click", () => { todos = todos.filter((x) => !x.done); update(); });

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
  if (changed) update();
  else render(); // refresh "overdue" colors as time passes
}
setInterval(checkReminders, 30000);

// Follow the computer's dark mode the first time
if (firstVisit && matchMedia("(prefers-color-scheme: dark)").matches) settings.theme = "dark";
render();
checkReminders();
