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
    cmdLimit: "Today's AI limit is reached, so Max can't do this one. Use the number instead, e.g. \"done #2\", or click the usage bar to raise the limit.",
    backupMenu: "Backup", backupNow: "Back up now", restore: "Restore…", exportFile: "Export file", importFile: "Import file",
    backupNote: "Your tasks are backed up automatically before changes. File attachments are not included.",
    backupDone: (name) => `Backed up: ${name}`, noBackups: "No backups yet.", tasksN: (n) => `${n} task${n === 1 ? "" : "s"}`,
    backupFail: "Couldn't reach the app server, so nothing was backed up. Use \"Export file\" instead.",
    sureRestore: (when, n) => `Replace your tasks with the backup from ${when} (${n})? Your current tasks are backed up first.`,
    sureImport: (n) => `Replace your tasks with ${n} from this file? Your current tasks are backed up first.`,
    yesRestore: "Yes, restore", yesImport: "Yes, import", restored: (n) => `Done. You now have ${n}.`,
    badFile: "That file isn't a task export from this app.",
    changedElsewhere: "Your tasks were changed in another window, so the latest list is shown. This window's last change was saved as a backup (Backup › Restore).",
    focusStart: "Focus 25 min", focusPause: "Pause", focusResume: "Resume", focusStop: "Stop focus", focusPlus: "+5 min",
    remindMore: (n) => `+${n} more`, repeatTitle: (m) => (m ? `Remind again every ${m} min` : "Remind again: off"), snoozeBtn: "Snooze", snooze10: "10 min", snooze60: "1 hour", snoozeTomorrow: "Tomorrow", remindClose: "Dismiss",
    focusPaused: "Paused", focusNice: (n) => `Nice focus! Mark #${n} done?`, focusDone: "Done", focusNotYet: "Not yet", focusBody: "Focus time is over",
    breakdown: "Break it down", stepsThinking: "Max is thinking of steps…", addSelected: "Add selected",
    stepsOffline: "Break it down needs Max, the AI server on your PC.", stepsFail: "Max couldn't come up with steps right now. Is Ollama running? Try again.",
    stepsPick: "Max suggests these steps. Pick the ones to add:", removeStep: "Remove step",
    morning: "Good morning", afternoon: "Good afternoon", evening: "Good evening", comma: ", ",
    dueToday: (n) => `${n} due today`, overdueN: (n) => `${n} overdue`, nothingDue: "Nothing due today",
    team: "Team", teamWorking: (n) => ` · ${n} working`,
    maxThinking: "Max is thinking…", maxReady: "Max ready", maxOffline: "Max offline", maxChecking: "Max: checking…",
    notifyBlocked: "Reminders are blocked for this site. To allow them: click the icon left of the address bar › Notifications › Allow, then reload.",
    notifyNone: "This browser can't show reminders.", limitSaved: (n) => `Daily AI limit: ${n} tokens`,
    sureClear: (n) => `Delete ${n} done task${n === 1 ? "" : "s"}?`, yesClear: "Yes, delete",
    askWhich: "Which one?", askWhichTask: "Which task?", askWhen: (x) => `When is "${x}"?`,
    today: "Today", tomorrow: "Tomorrow", pickDate: "Pick date", noDate: "No date", ok: "OK", askDate: "Which day?",
    askDetails: "Quick details so Max can plan better", suggestSteps: "Suggest steps", skipSuggest: "Skip, just suggest",
    ask_where: "Where?", ask_when: "When?", ask_budget: "Budget?",
    eg_where: "e.g. Chiang Mai", eg_when: "e.g. 20–22 Nov", eg_budget: "e.g. ฿2,000", tripDetails: "Trip details",
    noTasks: "No tasks to choose from.", notDoneYet: (n) => `#${n} isn't done yet, so there is nothing to undo.`,
    alreadyDone: (n) => `#${n} is already done.`,
    maxAdded: (n, text, when) => `Max added #${n}: ${text}${when ? " · " + when : ""}`, maxUpdated: (n) => `Max updated #${n}`, deleted: (n) => `Deleted #${n}`,
    maxDone: (n) => `Max marked #${n} done`, maxUndone: (n) => `Max reopened #${n}`,
    // Ask Max (answers to questions): the filter is turned into words by filterBits() below
    whenLabel: { today: "due today", tomorrow: "due tomorrow", week: "due this week", nextweek: "due next week", overdue: "overdue", none: "with no date" },
    dateLabel: (d) => `due ${d}`, priLabel: { high: "high priority", low: "low priority" }, catLabel: (c) => c,
    ansDone: "done", ansAbout: (x) => `about "${x}"`,
    ansCount: (n, b) => {
      const over = b.scope === "overdue"; // "overdue" goes before the word tasks, other dates after
      const words = [over ? b.scope : "", ...b.adj].filter(Boolean).join(" ");
      const tail = [over ? "" : b.scope, b.about].filter(Boolean).join(" ");
      return `${n} ${words ? words + " " : ""}task${n === 1 ? "" : "s"}${tail ? " " + tail : words ? "" : " left"}`;
    },
    ansNone: (f, b, label) => {
      const plain = !b.adj.length && !b.about;
      const friendly = { "": "No open tasks. All clear!", today: "Nothing due today. Enjoy!", tomorrow: "Nothing due tomorrow.", overdue: "Nothing overdue. Nice work!" };
      return (plain && friendly[f.when]) || `No tasks found: ${label}`;
    },
    ansMore: (n) => `+${n} more`, ansShowAll: "Show all in list", ansFiltered: "Filtered:", ansClear: "Clear filter", ansClose: "Close",
    ansMoveTomorrow: "Move all to tomorrow", sureMoveAll: (n) => `Move ${n} overdue task${n === 1 ? "" : "s"} to tomorrow? The times stay the same.`,
    yesMove: "Yes, move", movedN: (n) => `Moved ${n} task${n === 1 ? "" : "s"} to tomorrow`,
    greetReply: "Hi! Tell me a task, or ask 'what is due today?'",
    stCompliment: "Thanks! What can I do for you?",
    stThanks: "You're welcome!",
    stChat: "Thanks for chatting! Tell me a task, or ask 'what is due today?'",
    ansOffline: "Max is offline, so I can only answer simple questions here: today, tomorrow, this week, overdue, high priority, or how many are left.",
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
    cmdLimit: "ใช้ AI ครบขีดจำกัดวันนี้แล้ว Max จึงทำคำสั่งนี้ไม่ได้ ใช้เลขงานแทน เช่น \"เสร็จ #2\" หรือกดที่แถบเพื่อเพิ่มขีดจำกัด",
    backupMenu: "สำรองข้อมูล", backupNow: "สำรองตอนนี้", restore: "กู้คืน…", exportFile: "ส่งออกไฟล์", importFile: "นำเข้าไฟล์",
    backupNote: "แอปสำรองงานให้อัตโนมัติก่อนทุกการแก้ไข แต่ไม่รวมไฟล์แนบ",
    backupDone: (name) => `สำรองแล้ว: ${name}`, noBackups: "ยังไม่มีข้อมูลสำรอง", tasksN: (n) => `${n} งาน`,
    backupFail: "ติดต่อเซิร์ฟเวอร์ของแอปไม่ได้ จึงยังไม่ได้สำรอง ใช้ \"ส่งออกไฟล์\" แทนได้",
    sureRestore: (when, n) => `แทนที่งานทั้งหมดด้วยข้อมูลสำรองเมื่อ ${when} (${n}) ใช่ไหม? งานปัจจุบันจะถูกสำรองไว้ก่อน`,
    sureImport: (n) => `แทนที่งานทั้งหมดด้วย ${n} จากไฟล์นี้ใช่ไหม? งานปัจจุบันจะถูกสำรองไว้ก่อน`,
    yesRestore: "ใช่ กู้คืน", yesImport: "ใช่ นำเข้า", restored: (n) => `เรียบร้อย ตอนนี้มี ${n}`,
    badFile: "ไฟล์นี้ไม่ใช่ไฟล์งานที่ส่งออกจากแอปนี้",
    changedElsewhere: "งานถูกแก้ไขจากหน้าต่างอื่น จึงแสดงรายการล่าสุด การแก้ไขล่าสุดของหน้านี้ถูกสำรองไว้ (สำรองข้อมูล › กู้คืน)",
    focusStart: "โฟกัส 25 นาที", focusPause: "หยุดชั่วคราว", focusResume: "เริ่มต่อ", focusStop: "หยุดโฟกัส", focusPlus: "+5 นาที",
    remindMore: (n) => `อีก ${n} งาน`, repeatTitle: (m) => (m ? `เตือนซ้ำทุก ${m} นาที` : "เตือนซ้ำ: ปิด"), snoozeBtn: "เลื่อน", snooze10: "10 นาที", snooze60: "1 ชั่วโมง", snoozeTomorrow: "พรุ่งนี้", remindClose: "ปิด",
    focusPaused: "หยุดอยู่", focusNice: (n) => `โฟกัสได้ดีมาก! ทำ #${n} เสร็จแล้วใช่ไหม?`, focusDone: "เสร็จแล้ว", focusNotYet: "ยังไม่เสร็จ", focusBody: "หมดเวลาโฟกัสแล้ว",
    breakdown: "แตกเป็นขั้นตอน", stepsThinking: "Max กำลังคิดขั้นตอน…", addSelected: "เพิ่มที่เลือก",
    stepsOffline: "การแตกเป็นขั้นตอนต้องใช้ Max (เซิร์ฟเวอร์ AI บนคอมของคุณ)", stepsFail: "Max ยังคิดขั้นตอนไม่ออกตอนนี้ Ollama เปิดอยู่ไหม? ลองอีกครั้ง",
    stepsPick: "Max แนะนำขั้นตอนเหล่านี้ เลือกที่จะเพิ่ม:", removeStep: "ลบขั้นตอน",
    morning: "สวัสดีตอนเช้า", afternoon: "สวัสดีตอนบ่าย", evening: "สวัสดีตอนเย็น", comma: " ",
    dueToday: (n) => `ครบกำหนดวันนี้ ${n}`, overdueN: (n) => `เลยกำหนด ${n}`, nothingDue: "ไม่มีงานครบกำหนดวันนี้",
    team: "ทีม", teamWorking: (n) => ` · ทำงานอยู่ ${n}`,
    maxThinking: "Max กำลังคิด…", maxReady: "Max พร้อม", maxOffline: "Max ออฟไลน์", maxChecking: "Max: กำลังตรวจสอบ…",
    notifyBlocked: "การแจ้งเตือนของเว็บนี้ถูกบล็อกอยู่ วิธีเปิด: กดไอคอนซ้ายของช่องที่อยู่เว็บ › การแจ้งเตือน › อนุญาต แล้วโหลดหน้าใหม่",
    notifyNone: "เบราว์เซอร์นี้แสดงการแจ้งเตือนไม่ได้", limitSaved: (n) => `ขีดจำกัด AI ต่อวัน: ${n} โทเคน`,
    sureClear: (n) => `ลบงานที่เสร็จแล้ว ${n} งาน ใช่ไหม?`, yesClear: "ใช่ ลบเลย",
    askWhich: "หมายถึงงานไหน?", askWhichTask: "งานไหน?", askWhen: (x) => `"${x}" เมื่อไหร่?`,
    today: "วันนี้", tomorrow: "พรุ่งนี้", pickDate: "เลือกวัน", noDate: "ไม่ระบุวัน", ok: "ตกลง", askDate: "วันไหน?",
    askDetails: "ขอรายละเอียดสั้นๆ ให้ Max วางแผนได้ดีขึ้น", suggestSteps: "ขอขั้นตอน", skipSuggest: "ข้าม แนะนำเลย",
    ask_where: "ที่ไหน?", ask_when: "เมื่อไหร่?", ask_budget: "งบเท่าไหร่?",
    eg_where: "เช่น เชียงใหม่", eg_when: "เช่น 20–22 พ.ย.", eg_budget: "เช่น 2,000 บาท", tripDetails: "รายละเอียดทริป",
    noTasks: "ยังไม่มีงานให้เลือก", notDoneYet: (n) => `#${n} ยังไม่เสร็จ จึงไม่มีอะไรให้ยกเลิก`,
    alreadyDone: (n) => `#${n} เสร็จไปแล้ว`,
    maxAdded: (n, text, when) => `Max เพิ่ม #${n}: ${text}${when ? " · " + when : ""} แล้ว`, maxUpdated: (n) => `Max แก้ #${n} แล้ว`, deleted: (n) => `ลบ #${n} แล้ว`,
    maxDone: (n) => `Max ทำเครื่องหมาย #${n} ว่าเสร็จแล้ว`, maxUndone: (n) => `Max เปิด #${n} ใหม่แล้ว`,
    whenLabel: { today: "วันนี้", tomorrow: "พรุ่งนี้", week: "สัปดาห์นี้", nextweek: "สัปดาห์หน้า", overdue: "ที่เลยกำหนด", none: "ที่ไม่มีวันที่" },
    dateLabel: (d) => `วันที่ ${d}`, priLabel: { high: "สำคัญ", low: "ไม่รีบ" }, catLabel: (c) => `หมวด ${c}`,
    ansDone: "ที่เสร็จแล้ว", ansAbout: (x) => `เกี่ยวกับ "${x}"`,
    ansCount: (n, b, f) => {
      const after = ["overdue", "none"].includes(f.when); // these go after the word งาน, the other dates before it
      const front = after ? "" : b.scope;
      const rest = [b.adj.join(" "), after ? b.scope : "", b.about].filter(Boolean).join(" ");
      return `${front}มี ${n} งาน${rest ? " " + rest : front ? "" : "คงเหลือ"}`;
    },
    ansNone: (f, b, label) => {
      const plain = !b.adj.length && !b.about;
      const friendly = { "": "ไม่มีงานเหลือ เคลียร์หมดแล้ว", today: "วันนี้ว่าง ไม่มีงานค้าง", tomorrow: "พรุ่งนี้ว่าง ไม่มีงาน", overdue: "ไม่มีงานที่เลยกำหนด เยี่ยมมาก" };
      return (plain && friendly[f.when]) || `ไม่พบงาน: ${label}`;
    },
    ansMore: (n) => `และอีก ${n} งาน`, ansShowAll: "แสดงทั้งหมดในรายการ", ansFiltered: "กรองอยู่:", ansClear: "ล้างตัวกรอง", ansClose: "ปิด",
    ansMoveTomorrow: "ย้ายทั้งหมดไปพรุ่งนี้", sureMoveAll: (n) => `ย้าย ${n} งานที่เลยกำหนดไปพรุ่งนี้? เวลาเดิมคงไว้`,
    yesMove: "ใช่ ย้ายเลย", movedN: (n) => `ย้าย ${n} งานไปพรุ่งนี้แล้ว`,
    greetReply: "สวัสดี! บอกงานที่ต้องทำได้เลย หรือถามว่า 'วันนี้มีอะไรบ้าง'",
    stCompliment: "ขอบคุณค่ะ! มีอะไรให้ช่วยไหม",
    stThanks: "ยินดีค่ะ!",
    stChat: "ขอบคุณที่คุยด้วยนะ! บอกงานได้เลย หรือถามว่า 'วันนี้มีอะไรบ้าง'",
    ansOffline: "Max ออฟไลน์ ตอบได้เฉพาะคำถามง่าย ๆ ที่นี่: วันนี้ พรุ่งนี้ สัปดาห์นี้ เลยกำหนด งานสำคัญ หรือเหลือกี่งาน",
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
// detailsAsked: Max already asked the trip details for Break it down (answered or skipped), so not again
let todos = load("todos", []).map((x) => ({ due: "", priority: "med", cat: "", notified: false, notes: "", files: [], steps: [], detailsAsked: false, ...x }));

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

// Running on this PC with server.py? On GitHub Pages there is no server, so the parts that need it
// (Max, database, backups, team status) are skipped instead of failing in the console.
// The PC's Tailscale names/IP (phone access) count as the server too; pjirayul.github.io does not.
const LOCAL = ["127.0.0.1", "localhost", "desktop-ldeu8ir"].includes(location.hostname) ||
  location.hostname.endsWith(".ts.net") || location.hostname.startsWith("100.");
const firstVisit = load("settings", null) === null;
let settings = { lang: "en", theme: "light", aiLimit: 20000, repeatMin: 0, ...load("settings", {}) };

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
let view = { filter: "all", cat: "", search: "", sort: "manual", nums: null, label: "" }; // nums: only these tasks ("Show all in list" from an answer)
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
  drawRemind();
  drawFocus(); // only the bar's own text (the bar lives outside the list)

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
    if (view.nums && !view.nums.includes(x.num)) return false;
    const num = view.search.trim().match(/^#(\d+)$/); // "#3" finds task number 3
    if (num) return x.num === Number(num[1]);
    return x.text.toLowerCase().includes(view.search.toLowerCase());
  });
  if (view.sort === "due") visible.sort((a, b) => (a.due || "9999").localeCompare(b.due || "9999"));
  if (view.sort === "priority") visible.sort((a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]);

  // "Filtered: … ×" chip while an answer's list is applied
  $("num-filter").hidden = !view.nums;
  $("num-filter").innerHTML = view.nums
    ? `<button class="chip active" data-clear-nums title="${t("ansClear")}">${t("ansFiltered")} ${escapeHtml(view.label)} ×</button>` : "";

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
      <button class="edit focus-btn" title="${t("focusStart")}" aria-label="${t("focusStart")}"><svg class="i" aria-hidden="true"><use href="#i-timer"/></svg></button>
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

// Team pill: the agents' status dots from status.json (written by Toto on this PC), read via
// api/status. On GitHub Pages there is no server, so the pill just stays hidden.
const TEAM = ["Toto", "Kimi", "George", "Lewis", "Bono"];
async function loadTeam() {
  if (!LOCAL) return; // stays hidden
  try {
    const res = await fetch(`api/status?t=${Date.now()}`, { signal: AbortSignal.timeout(5000) });
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
let maxReady = LOCAL ? null : false; // null = still checking (don't say "offline" before we know)
function drawMax() {
  $("max-status").classList.toggle("ready", maxReady === true);
  $("max-text").textContent = t(maxReady === null ? "maxChecking" : maxReady ? "maxReady" : "maxOffline");
}
// Served by "python server.py --test": a clear badge so nobody mistakes it for the real list
function showTestBadge() {
  if (document.querySelector(".test-mode-badge")) return;
  const badge = document.createElement("div");
  badge.className = "test-mode-badge";
  badge.textContent = "TEST MODE";
  document.body.prepend(badge);
}
async function loadMax() {
  if (LOCAL) {
    try {
      const res = await fetch("api/max/status", { signal: AbortSignal.timeout(5000) });
      const data = await res.json();
      maxReady = res.ok && data.ready === true;
      if (data.testMode) showTestBadge();
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
  if (openAsk?.box === box) closeAsk(); // a new message replaces an open question
  box.textContent = msg;
  box.className = warn ? "cmd-msg warn" : "cmd-msg";
};

// ---------- Max asks when unsure ----------
// One small, reusable question: a line of text, optional short inputs, and answer chips (buttons).
//   const answer = await askMax("Which one?", [{ label: "#2 Send laundry", value: 2 }, { label: "Cancel", value: null }]);
// Resolves with { value, values } (values = what was typed in the inputs, by name), or null for
// Cancel / Escape / when something else replaces the question. Python (server.py) decides WHEN to ask.
// Made to be reused later (e.g. a "Do it" button or a task chat).
let openAsk = null; // the question on screen: { box, resolve }
function closeAsk() {
  if (!openAsk) return;
  const { resolve } = openAsk;
  openAsk = null;
  resolve(null);
}
function askMax(question, choices, { inputs = [], box = $("cmd-msg") } = {}) {
  closeAsk(); // only one question at a time
  return new Promise((resolve) => {
    const q = document.createElement("span");
    q.className = "ask-q";
    q.textContent = question; // textContent: task text never runs as HTML
    const fields = inputs.map((f) => {
      const label = document.createElement("label");
      label.className = "ask-field";
      label.textContent = f.label ? f.label + " " : "";
      const input = document.createElement("input");
      input.type = f.type || "text";
      input.name = f.name;
      input.placeholder = f.placeholder || "";
      input.value = f.value || "";
      input.maxLength = 60;
      if (!f.label) input.setAttribute("aria-label", question);
      label.append(input);
      return label;
    });
    const finish = (answer) => {
      if (openAsk?.resolve !== resolve) return; // already closed
      openAsk = null;
      box.replaceChildren();
      box.className = "cmd-msg";
      $("todo-input").focus({ preventScroll: true }); // the chip is gone: keep the keyboard in a sensible place
      resolve(answer);
    };
    const chips = document.createElement("span");
    chips.className = "chips ask-chips";
    for (const c of choices) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = c.primary ? "chip active" : "chip";
      b.textContent = c.label;
      b.addEventListener("click", () => {
        if (c.value === null) return finish(null); // Cancel
        const values = {};
        for (const input of box.querySelectorAll("input")) values[input.name] = input.value.trim();
        finish({ value: c.value, values });
      });
      chips.append(b);
    }
    // Keyboard: Escape = cancel; Enter in an input = the main (first highlighted) chip
    box.onkeydown = (e) => {
      if (e.key === "Escape") { e.preventDefault(); finish(null); $("todo-input").focus(); }
      if (e.key === "Enter" && e.target.tagName === "INPUT") { e.preventDefault(); (chips.querySelector(".active") || chips.firstChild)?.click(); }
    };
    openAsk = { box, resolve };
    box.className = "cmd-msg ask";
    box.replaceChildren(q, ...fields, chips);
    (box.querySelector("input") || chips.firstChild)?.focus({ preventScroll: true });
    box.scrollIntoView({ block: "nearest" });
  });
}
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

// Learning loop: remember the tasks Max just added. If the owner deletes one within 10 minutes, Max probably
// misunderstood, so the server saves it in data/max-mistakes.json (on this PC only) for the team to learn from.
const MADE_KEY = "maxMade";
const MISTAKE_MS = 10 * 60 * 1000;
function readMade() {
  try { return JSON.parse(localStorage.getItem(MADE_KEY)) || {}; } catch { return {}; }
}
function rememberMade(num, text) {
  const made = readMade();
  for (const n in made) if (Date.now() - made[n].at > MISTAKE_MS) delete made[n]; // forget old ones
  made[num] = { text, at: Date.now() };
  try { localStorage.setItem(MADE_KEY, JSON.stringify(made)); } catch {}
}
function noteIfMistake(todo) {
  const made = readMade();
  const m = made[todo.num];
  if (!m) return;
  delete made[todo.num];
  try { localStorage.setItem(MADE_KEY, JSON.stringify(made)); } catch {}
  if (!LOCAL || Date.now() - m.at > MISTAKE_MS) return; // no server on GitHub Pages
  fetch("api/max/mistake", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: m.text, action: "add", created: new Date(m.at).toISOString(), deletedAt: new Date().toISOString() }),
    signal: AbortSignal.timeout(5000),
  }).catch(() => {}); // never slow down or block the delete
}

function askDelete(todo) {
  askYesNo($("cmd-msg"), t("sureDelete")(`#${todo.num} "${todo.text}"`), t("yes"), () => {
    backup(`before delete #${todo.num}`, true);
    noteIfMistake(todo);
    deleteTaskFiles(todo);
    todos = todos.filter((x) => x !== todo);
    update();
    $("todo-input").value = "";
    $("todo-input").focus();
    showMessage(t("deleted")(todo.num)); // confirm it is really gone
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
  const low = stripGreeting(text).toLowerCase();
  const num = low.match(/#\s*(\d+)/);
  let action = "";
  if (/^(undo|undone|uncheck|unmark|reopen|not done)\b|ยังไม่เสร็จ|ยกเลิกเสร็จ/.test(low)) action = "uncomplete";
  else if (/^(delete|remove|del|erase)\b|^ลบ/.test(low)) action = "delete";
  else if (/^(done|mark|tick|finished|completed)\b|\b(done|finished|completed)$|เสร็จ(แล้ว)?$|^เสร็จ/.test(low)) action = "complete";
  else if (/^#\s*\d/.test(low) || (/^(change|modify|move|rename|edit|update|reschedule|postpone)\b|^(เปลี่ยน|แก้|ย้าย|เลื่อน)/.test(low)
    && (num || /\sto\s|เป็น/.test(low)))) action = "update";
  if (!action) return null; // a normal new task
  if (num && action !== "update") return { action, num: Number(num[1]) };
  // "done" / "delete it" with no task named: we can ask which one, even without AI
  const rest = low.replace(/^(undo|undone|uncheck|unmark|reopen|not done|delete|remove|del|erase|done|mark|tick|finished|completed|ยังไม่เสร็จ|ยกเลิกเสร็จ|ลบ|เสร็จ(แล้ว)?)\s*/, "")
    .replace(/\s*(done|finished|completed|เสร็จ(แล้ว)?)$/, "").trim();
  if (action !== "update" && ["", "it", "this", "that", "มัน", "อันนี้", "งานนี้", "นี้"].includes(rest)) return { action, pickTask: true };
  return { action: "offline" };
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
    // Nothing to change: say so instead of "Max reopened #4" for a task that was never done
    if (todo.done === (cmd.action === "complete")) return t(todo.done ? "alreadyDone" : "notDoneYet")(todo.num);
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

// Send a sentence to Max (server.py). extra.num: the task the owner picked after "Which one?"
async function parseWithMax(text, extra = {}) {
  const now = new Date();
  const res = await fetch("api/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      now: `${now.toLocaleDateString("en-CA")}T${now.toTimeString().slice(0, 5)} ${now.toLocaleDateString("en-US", { weekday: "long" })}`,
      categories: [...new Set(todos.map((x) => x.cat).filter(Boolean))],
      tasks: todos.map((x) => ({ num: x.num, text: x.text, due: x.due, done: x.done, priority: x.priority, cat: x.cat })), // "#3"/"laundry" can be found; due keeps the time; priority + cat answer questions
      ...extra,
    }),
    signal: AbortSignal.timeout(30000), // a stuck AI must not freeze the box forever
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`); // e.g. GitHub Pages sends an HTML error page
  const data = await res.json();
  addUsage(data.tokens);
  return data;
}

// Do a command and say what happened (keeps the text in the box when it didn't work)
function finishCommand(cmd) {
  showMessage("");
  const msg = applyCommand(cmd);
  if (msg === "") {
    $("todo-input").value = ""; // worked: clear the box
    // Say what was done, also for the simple commands that work without AI ("done #2")
    const done = { complete: "maxDone", uncomplete: "maxUndone", update: "maxUpdated" }[cmd.action];
    if (done) showMessage(t(done)(cmd.num));
  }
  if (msg) showMessage(msg, !cmd.choices?.length); // "Which one?" is not a warning
  // A Yes/No question is waiting: put the focus on Yes, so Enter confirms the delete
  ($("cmd-msg").querySelector("button") || $("todo-input")).focus();
}

function addTask(task, problem = "") {
  backup(`before add "${task.text.slice(0, 40)}"`);
  const num = newNum();
  todos.push({ id: Date.now() + Math.random(), num, text: task.text, done: false, due: task.due || "", priority: task.priority || "med", cat: task.category || "", notified: false, notes: "", files: [], steps: [], detailsAsked: false });
  $("todo-input").value = "";
  update();
  flash(num);
  rememberMade(num, task.text);
  if (!problem) {
    const when = task.due ? new Date(task.due).toLocaleString(t("locale"), { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "";
    showMessage(t("maxAdded")(num, task.text, when)); // textContent inside, so task text never runs as HTML
  }
}

// ---------- Ask Max: answers to questions about the tasks ----------
// Max (server.py) recognises the question and does the counting; this draws the answer card.
// Questions never add a task. Offline (GitHub Pages, server off, AI limit) localQuestion() below
// answers the simple ones (today / tomorrow / this week / overdue / priority / done) by itself.
const QUESTION_WORDS = /^(what|what's|whats|which|show|list|how many|how much|anything|any|is there|are there|do i have|have i got|tell me|give me)\b|มีอะไร|อะไรบ้าง|กี่งาน|งานอะไร|งานค้าง|เลยกำหนด|เกินกำหนด|^แสดง|ทำอะไรดี|ต้องทำ|ทำอะไร|\bwhat (to do|should i|shall i|do i (have|need|got)|am i (doing|supposed)|have i got|else)\b|\bwhat(')?s? (is )?(my|on|the plan)\b|^my (tasks?|to-?dos?|plan|day|schedule)\b/;
// Same as GREETING in server.py: "Hi max, what to do today" -> "what to do today". Max (server) strips it too.
const GREETING = /^\s*(?:(?:hi|hey|hello|yo|ok|okay)(?=[\s,!.]|$)[\s,!.]*(?:max(?=[\s,!.:]|$)[\s,!.:]*)?|max\s*[,:!]\s*|(?:สวัสดี|หวัดดี|โอเค)(?:ครับ|ค่ะ|คะ)?\s*(?:max|แม็กซ์|แม็ก)?\s*(?:ครับ|ค่ะ|คะ)?[\s,!]*|(?:แม็กซ์|แม็ก)(?:ครับ|ค่ะ|คะ)?\s*[,:!]?\s*)/i;
const stripGreeting = (text) => text.replace(GREETING, "").trim() || text;
// "hi max" alone: nothing is left after the greeting, so it is not a task
const isGreetingOnly = (text) => GREETING.test(text) && !text.replace(GREETING, "").trim();
// Small talk seed list, same as SMALL_TALK in server.py: a speed path and the offline copy.
// Anything else that is chit-chat is recognised by Max (the AI) on the server.
const SMALL_TALK = {
  compliment: /^(?:you|u)(?:'re| are|re)?\s+(?:so |really )?(?:smart|great|awesome|amazing)(?:\s+max)?$|^(?:คุณ)?เก่ง(?:มาก|จัง)?ๆ?(?:ครับ|ค่ะ|คะ|นะ)*$/,
  thanks: /^(?:thanks|thank you|thx|ty)(?: so much| a lot)?(?:\s+max)?$|^ขอบคุณ(?:มาก)?ๆ?(?:ครับ|ค่ะ|คะ|นะ)*$/,
};
const smallTalkKind = (text) => {
  const low = stripGreeting(text).replace(/’/g, "'").toLowerCase().split(/\s+/).filter(Boolean).join(" ").replace(/[ !.?,]+$/, "");
  return Object.keys(SMALL_TALK).find((k) => SMALL_TALK[k].test(low)) || null;
};
const ANSWER_ROWS = 8; // tasks listed in the card; the rest are "+N more"
const dateKey = (d) => d.toLocaleDateString("en-CA"); // YYYY-MM-DD
const shortDate = (due) => new Date(due).toLocaleString(t("locale"), { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

// First and last day of today / tomorrow / this week (until Sunday) / next week, as YYYY-MM-DD
function dayRange(when) {
  const weekday = (new Date().getDay() + 6) % 7; // Monday = 0
  const offsets = { today: [0, 0], tomorrow: [1, 1], week: [0, 6 - weekday], nextweek: [7 - weekday, 13 - weekday] }[when];
  return offsets.map((n) => { const d = new Date(); d.setDate(d.getDate() + n); return dateKey(d); });
}

// Same rules as list_tasks() in server.py (the server's answer is the real one; this is the offline copy)
function matchesFilter(x, f) {
  if (x.done !== (f.status === "done")) return false;
  if (f.priority && x.priority !== f.priority) return false;
  if (f.cat && x.cat.toLowerCase() !== f.cat) return false;
  if (f.text && !x.text.toLowerCase().includes(f.text)) return false;
  if (f.when === "none") return !x.due;
  if (f.when === "overdue") return !!x.due && new Date(x.due) < new Date();
  if (["today", "tomorrow", "week", "nextweek"].includes(f.when)) {
    const [first, last] = dayRange(f.when);
    return !!x.due && x.due.slice(0, 10) >= first && x.due.slice(0, 10) <= last;
  }
  return true;
}

// A small offline copy of the server's question reader. null = not a question, or too tricky for here.
function localQuestion(text) {
  const low = stripGreeting(text).toLowerCase().trim();
  if (!(QUESTION_WORDS.test(low) || low.endsWith("?")) || /#\s*\d/.test(low)) return null;
  if (/monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d(st|nd|rd|th)\b|จันทร์|อังคาร|พุธ|พฤหัส|ศุกร์|เสาร์|วันอาทิตย์|วันที่|มะรืน/.test(low)) return null;
  const f = { when: "", date: "", priority: "", cat: "", status: "open", text: "" };
  let rest = low;
  const about = low.match(/(?:about|regarding|เกี่ยวกับ)\s*(.+?)(?=\s+(?:due|today|tomorrow|this|next|overdue)\b|[?.!]|$)/);
  if (about) { f.text = about[1].trim(); rest = low.replace(about[0], " "); }
  if (/overdue|\blate\b|เลยกำหนด|เกินกำหนด|งานค้าง/.test(rest)) f.when = "overdue";
  else if (/next week|สัปดาห์หน้า|อาทิตย์หน้า/.test(rest)) f.when = "nextweek";
  else if (/\bweek\b|สัปดาห์นี้|อาทิตย์นี้/.test(rest)) f.when = "week";
  else if (/tomorrow|พรุ่งนี้/.test(rest)) f.when = "tomorrow";
  else if (/\btoday\b|\btonight\b|วันนี้|คืนนี้/.test(rest)) f.when = "today";
  if (/\b(high|urgent|important|asap)\b|ด่วน|สำคัญ/.test(rest)) f.priority = "high";
  if (/\b(done|completed|finished)\b|เสร็จแล้ว/.test(rest)) f.status = "done";
  f.cat = (todos.map((x) => x.cat.toLowerCase()).find((c) => c && rest.includes(c))) || "";
  const taskWord = /\b(tasks?|to-?dos?|left|remaining|pending|outstanding|open|have)\b|งาน/.test(low);
  const strong = f.priority || f.cat || f.when === "overdue";
  const something = strong || f.when || f.text || f.status === "done";
  // "what should I do": no filter words, so the answer is the whole open list
  const natural = /what (to do|should i|shall i|do i (have|need|got)|am i (doing|supposed)|have i got|else)|what('s| is) (my|on|the plan)|^my (tasks?|to-?dos?|plan|day|schedule)|ทำอะไร|ต้องทำ/.test(low);
  if (!(/^(show|list|tell me|give me)\b/.test(low) ? taskWord || strong : something || taskWord || natural)) return null;
  const found = todos.filter((x) => matchesFilter(x, f)).sort((a, b) => (a.due || "9999").localeCompare(b.due || "9999") || a.num - b.num);
  return { action: "answer", filter: f, nums: found.map((x) => x.num) };
}

// A filter in words: { scope: "due today", adj: ["high priority", "Work"], about: 'about "rent"' }
function filterBits(f) {
  const L = TEXT[settings.lang];
  const scope = f.when === "date" ? L.dateLabel(new Date(f.date + "T00:00").toLocaleDateString(L.locale, { day: "numeric", month: "short" })) : L.whenLabel[f.when] || "";
  const cat = f.cat ? todos.map((x) => x.cat).find((c) => c.toLowerCase() === f.cat) || f.cat : ""; // show the name as typed in the list
  const adj = [f.status === "done" ? L.ansDone : "", L.priLabel[f.priority] || "", cat ? L.catLabel(cat) : ""].filter(Boolean);
  return { scope, adj, about: f.text ? L.ansAbout(f.text) : "" };
}
const filterLabel = (f) => { const b = filterBits(f); return [b.scope, ...b.adj, b.about].filter(Boolean).join(" · "); };

function hideAnswer() {
  $("answer-card").hidden = true;
  $("answer-card").replaceChildren();
}

// Put the main list back to "everything" (also used by "Show all in list")
function resetListView() {
  view = { ...view, filter: "all", cat: "", search: "", nums: null, label: "" };
  $("search").value = "";
  document.querySelectorAll("#filters .chip").forEach((c) => c.classList.toggle("active", c.dataset.filter === "all"));
}

// Click on an answer row: scroll to the task and flash it (clear the list filters first if they hide it)
function jumpToTask(num) {
  if (!document.querySelector(`.todo-item[data-num="${num}"]`)) { resetListView(); render(); }
  flash(num);
}

// "Move all to tomorrow": asks Yes/No first, keeps each task's time, backs up first
function askMoveToTomorrow(found) {
  askYesNo($("cmd-msg"), t("sureMoveAll")(found.length), t("yesMove"), () => {
    backup("before moving overdue tasks to tomorrow", true);
    const tomorrow = dayRange("tomorrow")[0];
    for (const x of found) { x.due = tomorrow + x.due.slice(10); x.notified = false; } // slice(10) = "THH:MM"
    update();
    hideAnswer();
    showMessage(t("movedN")(found.length));
  }, () => $("todo-input").focus());
}

// Draw the answer card under the command bar. Everything goes in with textContent (never as HTML).
function showAnswer(data) {
  const f = data.filter;
  const found = data.nums.map((n) => todos.find((x) => x.num === n)).filter(Boolean);
  const bits = filterBits(f);
  const card = $("answer-card");
  const make = (tag, className, text = "") => {
    const el = document.createElement(tag);
    el.className = className;
    el.textContent = text;
    return el;
  };
  const title = make("p", "answer-title", found.length ? t("ansCount")(found.length, bits, f) : t("ansNone")(f, bits, filterLabel(f)));
  const close = make("button", "answer-close", "×");
  close.type = "button";
  close.setAttribute("aria-label", t("ansClose"));
  close.addEventListener("click", () => { hideAnswer(); $("todo-input").focus(); });
  card.replaceChildren(title, close);

  if (found.length) {
    const rows = make("ul", "answer-rows");
    for (const x of found.slice(0, ANSWER_ROWS)) {
      const li = document.createElement("li");
      const row = make("button", "answer-row");
      row.type = "button";
      row.append(make("span", "num answer-num", `#${x.num}`), make("span", "answer-text", x.text));
      if (x.due) row.append(make("span", `answer-when${isOverdue(x) ? " overdue" : ""}`, shortDate(x.due)));
      if (x.cat) row.append(make("span", "tag answer-cat", `#${x.cat}`));
      row.addEventListener("click", () => jumpToTask(x.num));
      li.append(row);
      rows.append(li);
    }
    card.append(rows);
  }
  const actions = make("div", "chips answer-actions");
  const chip = (label, onClick) => {
    const b = make("button", "chip", label);
    b.type = "button";
    b.addEventListener("click", onClick);
    actions.append(b);
  };
  if (found.length > ANSWER_ROWS) {
    card.append(make("p", "answer-more", t("ansMore")(found.length - ANSWER_ROWS)));
    chip(t("ansShowAll"), () => {
      resetListView();
      view.nums = found.map((x) => x.num);
      view.label = filterLabel(f);
      render();
      $("todo-list").scrollIntoView({ block: "nearest", behavior: "smooth" });
    });
  }
  if (f.when === "overdue" && f.status === "open" && found.length) chip(t("ansMoveTomorrow"), () => askMoveToTomorrow(found));
  // (A "Plan my day" chip for today's tasks comes later, with the Max agent.)
  card.append(actions);
  card.hidden = false;
}

// Short label for a task chip: "#7 Do laundry"
const taskLabel = (x) => `#${x.num} ${x.text.length > 40 ? x.text.slice(0, 39) + "…" : x.text}`;

// Several tasks fit ("done laundry") or none was named ("done it"): ask, then do it on the chosen #N
async function askWhichTask(text, cmd) {
  const options = cmd.choices?.length
    ? cmd.choices.map((n) => todos.find((x) => x.num === n)).filter(Boolean)
    // Newest first; "undo" offers done tasks, everything else the open ones
    : todos.filter((x) => x.done === (cmd.action === "uncomplete")).sort((a, b) => b.num - a.num);
  if (!options.length) return showMessage(t("noTasks"), true);
  const answer = await askMax(t(cmd.choices?.length ? "askWhich" : "askWhichTask"),
    [...options.slice(0, 4).map((x) => ({ label: taskLabel(x), value: x.num })), { label: t("cancel"), value: null }]);
  if (!answer) return; // cancelled: the text stays in the box
  let chosen = { action: cmd.action, num: answer.value };
  if (cmd.action === "update") {
    // A change needs Max again to read the new date/name, now for this task
    showMessage(t("maxThinking"));
    try {
      chosen = await parseWithMax(text, { num: answer.value });
    } catch (err) {
      console.warn("AI unavailable:", err);
      return showMessage(t("cmdOffline"), true);
    }
  }
  finishCommand(chosen);
}

// A meeting/flight/trip… with no day: "When?" Today · Tomorrow · Pick date · No date (= add it as it is)
async function askWhenThenAdd(task) {
  const day = (offset) => {
    const d = new Date();
    d.setDate(d.getDate() + offset);
    return d.toLocaleDateString("en-CA"); // YYYY-MM-DD
  };
  let answer = await askMax(t("askWhen")(task.text), [
    { label: t("today"), value: 0 }, { label: t("tomorrow"), value: 1 },
    { label: t("pickDate"), value: "pick" }, { label: t("noDate"), value: "none" },
  ]);
  if (!answer) return; // Escape: nothing added, the text stays in the box
  let date = "";
  if (answer.value === "pick") {
    answer = await askMax(t("askDate"), [{ label: t("ok"), value: "ok", primary: true }, { label: t("cancel"), value: null }],
      { inputs: [{ name: "date", type: "date", value: day(1) }] });
    if (!answer) return;
    date = answer.values.date;
  } else if (answer.value !== "none") {
    date = day(answer.value);
  }
  // The server sends the time it heard ("at 3pm"), or the owner's morning time
  let due = /^\d{4}-\d{2}-\d{2}$/.test(date) && /^\d{2}:\d{2}$/.test(task.time) ? `${date}T${task.time}` : "";
  if (due && new Date(due) <= new Date()) {
    // That time already passed today (it would be overdue at once): use the next full hour instead
    const next = new Date();
    next.setHours(next.getHours() + 1, 0, 0, 0);
    due = next.toLocaleDateString("en-CA") === date ? `${date}T${String(next.getHours()).padStart(2, "0")}:00` : `${date}T23:59`;
  }
  addTask({ ...task, due });
}

$("todo-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = $("todo-input").value.trim();
  if (!text) return;
  if (isGreetingOnly(text)) { // just "hi max": say hello, add nothing
    $("todo-input").value = "";
    return showMessage(t("greetReply"));
  }
  const talk = smallTalkKind(text); // "you are so smart" / "thanks": a friendly reply, never a task, no server call
  if (talk) {
    $("todo-input").value = "";
    hideAnswer();
    return showMessage(t("st" + talk[0].toUpperCase() + talk.slice(1)));
  }
  const button = $("add-btn");
  const input = $("todo-input");
  button.disabled = input.disabled = true;
  button.textContent = t("thinking");
  showMessage(t("maxThinking"));
  const plain = stripGreeting(text); // offline "hey max buy milk" adds "Buy milk" (the server strips it too)
  let task = { text: plain[0].toUpperCase() + plain.slice(1), due: "", priority: "med", category: "" };
  let cmd = null;       // set when the sentence is a command for an existing task
  let problem = "";     // message to show after the box is usable again
  let followUp = null;  // a question for the owner, asked once the box is usable again
  let answer = null;    // set when the sentence is a question about the tasks (nothing is added)
  hideAnswer();
  try {
    try {
      if (usageToday() >= settings.aiLimit) throw new Error(t("limitHit"));
      if (!LOCAL) throw new Error("no AI server here (GitHub Pages)"); // straight to the simple fallback
      const data = await parseWithMax(text);
      if (data.action === "smalltalk") { // Max decided it is chit-chat: show his short reply, add nothing
        $("todo-input").value = "";
        hideAnswer();
        showMessage(data.reply || t("stChat"));
        return;
      }
      if (data.action === "answer") answer = data;
      else if (data.action && data.action !== "add") cmd = data;
      else if (data.text) task = data;
      else throw new Error("AI gave no task");
    } catch (err) {
      if (LOCAL) console.warn("AI unavailable:", err);
      showMessage("");
      problem = err.message === t("limitHit") ? t("limitHit") : t("aiOff");
      answer = localQuestion(text); // simple questions need no AI
      if (!answer && !QUESTION_WORDS.test(stripGreeting(text).toLowerCase())) cmd = simpleCommand(text);
      if (!answer && !cmd && LOCAL && problem === t("limitHit")) {
        // A new task at the AI limit: Python can still ask "When?" for a meeting/trip (no AI used),
        // and still answers questions (the tricky ones: a weekday, a category)
        try {
          const data = await parseWithMax(text, { noAI: true });
          if (data.action === "answer") answer = data;
          else if (data.text) task = data;
        } catch {} // server off: add as plain text
      }
      if (answer) problem = "";
      else if (!cmd && QUESTION_WORDS.test(stripGreeting(text).toLowerCase()) && /tasks?|due|overdue|left|งาน|วันนี้|พรุ่งนี้/.test(text.toLowerCase())) {
        // Looks like a question we can't answer here: say so (and don't add it as a task)
        showMessage(t("ansOffline"), true);
        return;
      }
      if (cmd?.action === "offline") {
        // A command we can't do without AI: keep the text so nothing is lost.
        // Not the "task added" message: nothing was added.
        showMessage(t(problem === t("limitHit") ? "cmdLimit" : "cmdOffline"), true);
        return;
      }
    }
    // Python (server.py) decided whether Max should ask first
    if (answer) {
      showMessage(""); // drop "Max is thinking…"
      $("todo-input").value = "";
      showAnswer(answer);
    } else if (cmd?.pickTask || cmd?.choices?.length) followUp = () => askWhichTask(text, cmd);
    else if (cmd) finishCommand(cmd);
    else if (task.askWhen) followUp = () => askWhenThenAdd(task);
    else addTask(task, problem);
  } finally {
    // Always give the box back, even if something above went wrong
    button.disabled = input.disabled = false;
    button.textContent = t("add");
    if (!followUp) ($("cmd-msg").querySelector("button") || input).focus();
  }
  if (followUp) return followUp();
  if (problem && !cmd) showMessage(problem, true); // in-page: the owner's browser blocks alert()
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
    noteIfMistake(todo);
    deleteTaskFiles(todo);
    todos = todos.filter((x) => x !== todo);
    update();
    showMessage(t("deleted")(todo.num));
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
  } else if (e.target.classList.contains("focus-btn")) {
    startFocus(findTodo(e.target)); // checked before "edit": same look, different job
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
async function breakDown(todo, skipAsk = false) {
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
      body: JSON.stringify({ text: todo.text, notes: todo.notes, due: todo.due, skipAsk: skipAsk || todo.detailsAsked }),
      signal: AbortSignal.timeout(60000), // a stuck AI must not leave "Thinking…" forever (server gives up first)
    });
    const data = await res.json();
    if (res.ok && Array.isArray(data.ask)) {
      // A trip/event without place or date: Max asks for a few details first (no AI used yet)
      if (suggest === mine) suggest = null;
      askTripDetails(todo, data.ask);
      return;
    }
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

// "Quick details so Max can plan better": Where? When? Budget? (only the missing ones + budget).
// The answers are saved in the task's notes as one line, so they're remembered and sent to Max.
async function askTripDetails(todo, missing) {
  const answer = await askMax(t("askDetails"), [
    { label: t("suggestSteps"), value: "go", primary: true },
    { label: t("skipSuggest"), value: "skip" },
  ], { inputs: missing.map((name) => ({ name, label: t(`ask_${name}`), placeholder: t(`eg_${name}`) })) });
  if (!answer) return; // Escape: nothing happens
  const current = todos.find((x) => x.id === todo.id); // the list may have been reloaded meanwhile
  if (!current) return;
  const parts = missing.map((name) => answer.values[name]).filter(Boolean);
  if (answer.value === "go" && parts.length) {
    current.notes = [current.notes, `${t("tripDetails")}: ${parts.join(" · ")}`].filter(Boolean).join("\n");
  }
  current.detailsAsked = true; // answered or skipped: Max doesn't ask again for this task
  update();
  breakDown(current, true);
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
$("num-filter").addEventListener("click", (e) => {
  if (e.target.closest("[data-clear-nums]")) { view.nums = null; view.label = ""; render(); }
});
$("cat-filters").addEventListener("click", (e) => {
  if (e.target.dataset.cat === undefined) return;
  view.cat = view.cat === e.target.dataset.cat ? "" : e.target.dataset.cat; // click again to clear
  render();
});

$("clear-done").addEventListener("click", () => {
  const count = todos.filter((x) => x.done).length;
  if (!count) return; // nothing to clear, so no backup needed
  // Ask Yes/No in the page first, like delete (it removes several tasks at once)
  askYesNo($("foot-msg"), t("sureClear")(count), t("yesClear"), () => {
    backup("before clear done", true);
    todos.filter((x) => x.done).forEach(deleteTaskFiles);
    todos = todos.filter((x) => !x.done);
    update();
  });
  $("foot-msg").querySelector("button").focus();
});

// Usage bar: change the daily AI limit in a small box under the command bar.
// Not prompt(): the owner's browser blocks it, and then the limit could never be raised.
$("usage").addEventListener("click", () => {
  const box = $("cmd-msg");
  const label = document.createElement("label");
  label.textContent = t("limitAsk") + " ";
  const input = document.createElement("input");
  input.type = "number";
  input.min = "1";
  input.step = "1000";
  input.value = settings.aiLimit;
  input.style.width = "8em";
  label.append(input);
  const ok = document.createElement("button");
  ok.type = "button";
  ok.className = "chip active";
  ok.textContent = t("save");
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "chip";
  cancel.textContent = t("cancel");
  const saveLimit = () => {
    const limit = parseInt(input.value, 10);
    if (!(limit > 0)) return input.focus(); // keep the box open until the number makes sense
    settings.aiLimit = limit;
    save("settings", settings);
    render();
    showMessage(t("limitSaved")(limit.toLocaleString()));
  };
  ok.addEventListener("click", saveLimit);
  cancel.addEventListener("click", () => showMessage(""));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveLimit();
    if (e.key === "Escape") showMessage("");
  });
  const buttons = document.createElement("span");
  buttons.style.cssText = "display: flex; gap: 6px; flex: none"; // same as the Yes/No buttons
  buttons.append(ok, cancel);
  box.className = "cmd-msg";
  box.replaceChildren(label, buttons);
  input.select();
});

$("lang").addEventListener("click", () => {
  settings.lang = settings.lang === "en" ? "th" : "en";
  save("settings", settings);
  hideAnswer(); // its words are in the old language
  render();
  loadTeam(); // "· 2 working" in the new language
  commandHints.refresh(); // example hints in the new language
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
  if (!("Notification" in window)) return showMessage(t("notifyNone"), true); // in-page, not alert()
  // Once blocked, the browser no longer asks, so the click looked dead: explain how to allow them
  const permission = Notification.permission === "denied" ? "denied" : await Notification.requestPermission();
  if (permission === "denied") showMessage(t("notifyBlocked"), true);
  render();
});

// "Remind again" (settings.repeatMin: 0 = off, 10, 30). Cycles on one button; no per-task field, so nothing to lose on load.
const REPEAT_STEPS = [0, 10, 30];
$("repeat").addEventListener("click", () => {
  settings.repeatMin = REPEAT_STEPS[(REPEAT_STEPS.indexOf(settings.repeatMin) + 1) % REPEAT_STEPS.length];
  save("settings", settings);
  render();
});

// Tasks showing in the banner (ids, in memory) and when each was last reminded. A reload forgets both: fine.
let ringing = [];
const lastReminded = {};

// Local "YYYY-MM-DDTHH:MM" (toISOString would be UTC and shift the day)
const localDue = (d) => `${d.toLocaleDateString("en-CA")}T${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;

function ring(todo) {
  lastReminded[todo.id] = Date.now();
  if (!ringing.includes(todo.id)) ringing.push(todo.id);
  if ("Notification" in window && Notification.permission === "granted") new Notification(t("remind"), { body: todo.text });
}

function checkReminders() {
  let changed = false;
  const now = Date.now();
  for (const todo of todos) {
    if (!todo.due || todo.done || new Date(todo.due) > now) continue;
    if (!todo.notified) {
      todo.notified = true;
      changed = true;
      ring(todo);
    } else if (settings.repeatMin) {
      // Overdue and already told: again every N minutes (first sight starts the clock, so a reload doesn't flood)
      if (lastReminded[todo.id] === undefined) lastReminded[todo.id] = now;
      else if (now - lastReminded[todo.id] >= settings.repeatMin * 60000) ring(todo);
    }
  }
  if (editingId !== null) { saveTodos(); return drawRemind(); } // don't wipe an open edit form
  if (changed) update();
  else render(); // refresh "overdue" colors as time passes
}
setInterval(checkReminders, 30000);

// The in-page banner shows the first waiting task. Text via textContent only.
function drawRemind() {
  ringing = ringing.filter((id) => todos.some((x) => x.id === id && !x.done)); // done/deleted meanwhile
  $("repeat").textContent = settings.repeatMin ? `${settings.repeatMin}m` : "off";
  $("repeat").title = t("repeatTitle")(settings.repeatMin);
  $("repeat").setAttribute("aria-label", $("repeat").title);
  $("repeat").classList.toggle("on", settings.repeatMin > 0);
  $("remind-bar").hidden = !ringing.length;
  if (!ringing.length) { $("remind-opts").hidden = true; return; }
  const todo = todos.find((x) => x.id === ringing[0]);
  $("remind-head").textContent = t("remind") + (ringing.length > 1 ? " · " + t("remindMore")(ringing.length - 1) : "");
  $("remind-title").textContent = `#${todo.num} ${todo.text}`;
  $("remind-done").textContent = t("focusDone");
  $("remind-snooze").textContent = t("snoozeBtn");
  $("remind-close").title = t("remindClose");
  $("remind-close").setAttribute("aria-label", t("remindClose"));
  const [a, b, c] = $("remind-opts").children;
  a.textContent = t("snooze10"); b.textContent = t("snooze60"); c.textContent = t("snoozeTomorrow");
}

$("remind-snooze").addEventListener("click", () => {
  const open = $("remind-opts").hidden;
  $("remind-opts").hidden = !open;
  $("remind-snooze").setAttribute("aria-expanded", open);
});
$("remind-close").addEventListener("click", () => { ringing.shift(); drawRemind(); });
$("remind-done").addEventListener("click", () => {
  const todo = todos.find((x) => x.id === ringing[0]);
  if (todo) { backup(`before done #${todo.num}`); todo.done = true; }
  $("remind-opts").hidden = true;
  update(); // render() redraws the banner
});
$("remind-opts").addEventListener("click", (e) => {
  const pick = e.target.closest("[data-snooze]")?.dataset.snooze;
  const todo = todos.find((x) => x.id === ringing[0]);
  if (!pick || !todo) return;
  const d = new Date();
  if (pick === "tomorrow") {
    // tomorrow at the task's own time of day; a task without a time gets 09:00
    const time = /T(\d\d:\d\d)/.exec(todo.due)?.[1] || "09:00";
    d.setDate(d.getDate() + 1);
    todo.due = `${d.toLocaleDateString("en-CA")}T${time}`;
  } else {
    d.setMinutes(d.getMinutes() + Number(pick));
    todo.due = localDue(d);
  }
  todo.notified = false; // the new time gets its own reminder
  delete lastReminded[todo.id];
  ringing.shift();
  $("remind-opts").hidden = true;
  update();
});

// ---------- 8b. Focus timer ----------
// One task at a time. Saved as { id, endsAt } (ms) in localStorage only: no new task field, so nothing to
// lose on load. A paused timer keeps { id, endsAt: 0, left } instead. The clock always shows endsAt - now,
// never counted ticks, because phones pause JavaScript when locked and a reload must not lose the time.
const FOCUS_MS = 25 * 60 * 1000;
let focus = load("focus", null);
let focusTick = null; // the 1-second timer, only alive while a countdown runs
let audioCtx = null; // made on the Start tap: iPhones keep sound locked until a tap
let chimed = false;  // chime once per finished timer

const focusTodo = () => focus && todos.find((x) => x.id === focus.id);
const focusLeft = () => (focus.endsAt ? Math.max(0, focus.endsAt - Date.now()) : focus.left);
const setFocus = (value) => { focus = value; if (value) save("focus", value); else localStorage.removeItem("focus"); };

function startFocus(todo, ms = FOCUS_MS) {
  try { audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)(); audioCtx.resume(); } catch {} // no sound is fine
  chimed = false;
  setFocus({ id: todo.id, endsAt: Date.now() + ms });
  drawFocus();
}

function stopFocus() { setFocus(null); drawFocus(); }

// Two soft notes, quiet; any failure just means a silent finish
function chime() {
  try {
    [660, 880].forEach((freq, i) => {
      const osc = audioCtx.createOscillator(), gain = audioCtx.createGain(), at = audioCtx.currentTime + i * 0.35;
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, at);
      gain.gain.exponentialRampToValueAtTime(0.15, at + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.0001, at + 0.9);
      osc.connect(gain).connect(audioCtx.destination);
      osc.start(at); osc.stop(at + 1);
    });
  } catch {}
}

// Update the bar. Called every second while counting, and from render() (language/theme/task changes).
function drawFocus() {
  const bar = $("focus-bar");
  const todo = focusTodo();
  if (focus && !todo) setFocus(null); // the task was deleted meanwhile
  bar.hidden = !focus;
  clearInterval(focusTick); focusTick = null;
  if (!focus) return;
  const left = focusLeft();
  const over = focus.endsAt && left <= 0;
  const secs = Math.ceil(left / 1000);
  const clock = `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`;
  $("focus-title").textContent = `#${todo.num} ${todo.text}`;
  $("focus-time").textContent = over ? t("focusNice")(todo.num) : focus.endsAt ? clock : `${clock} · ${t("focusPaused")}`;
  $("focus-fill").style.width = over ? "100%" : `${Math.min(100, 100 - (left / FOCUS_MS) * 100)}%`;
  $("focus-run").hidden = over;
  $("focus-end").hidden = !over;
  $("focus-done").textContent = t("focusDone");
  $("focus-later").textContent = t("focusNotYet");
  $("focus-plus").textContent = t("focusPlus");
  $("focus-plus").title = t("focusPlus");
  const pauseLabel = t(focus.endsAt ? "focusPause" : "focusResume");
  $("focus-pause").title = pauseLabel;
  $("focus-pause").setAttribute("aria-label", pauseLabel);
  $("focus-pause").innerHTML = `<svg class="i" aria-hidden="true"><use href="#i-${focus.endsAt ? "pause" : "play"}"/></svg>`;
  $("focus-stop").title = t("focusStop");
  $("focus-stop").setAttribute("aria-label", t("focusStop"));
  if (over && !chimed) { // the first time we see the end
    chimed = true;
    chime();
    if ("Notification" in window && Notification.permission === "granted") new Notification(t("focusBody"), { body: todo.text });
  }
  if (focus.endsAt && !over) focusTick = setInterval(drawFocus, 1000);
}

$("focus-pause").addEventListener("click", () => {
  if (focus.endsAt) setFocus({ id: focus.id, endsAt: 0, left: focusLeft() }); // freeze the time left
  else setFocus({ id: focus.id, endsAt: Date.now() + focus.left });
  drawFocus();
});
$("focus-plus").addEventListener("click", () => {
  chimed = false;
  if (focus.endsAt) setFocus({ id: focus.id, endsAt: Math.max(Date.now(), focus.endsAt) + 5 * 60 * 1000 });
  else setFocus({ id: focus.id, endsAt: 0, left: focus.left + 5 * 60 * 1000 });
  drawFocus();
});
$("focus-stop").addEventListener("click", stopFocus);
$("focus-later").addEventListener("click", stopFocus);
$("focus-done").addEventListener("click", () => {
  const todo = focusTodo();
  stopFocus();
  if (todo && !todo.done) { backup(`before done #${todo.num}`); todo.done = true; update(); }
});

// ---------- 9. Task backups ----------
// Tasks only live in this browser, so before changes we send a copy to server.py, which saves
// it in the backups/ folder. On GitHub Pages there is no server: backups are skipped silently
// (Export file still works there).
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
    detailsAsked: x.detailsAsked === true,
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
const commandHints = smartHints($("todo-input"), "command", () => settings.lang); // rotating examples
loadTeam();
loadMax();
if (LOCAL) setInterval(() => { loadTeam(); loadMax(); }, 30000); // team dots follow status.json; Max follows Ollama
// Phone turned or window resized past 480px: swap long/short placeholder
phone.addEventListener("change", setPlaceholders); // only the hints, so an open edit form is not redrawn
