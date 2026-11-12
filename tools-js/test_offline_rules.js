// Runs every sentence in .claude/docs/offline-rules-cases.json through max-offline.js and prints pass / fail.
// Run from the app folder:   node tools-js/test_offline_rules.js
// "Today" is fixed inside the list (Wed 28 Oct 2026, 10:00), so results never depend on the real date.
// Exit code 0 = all passed, 1 = something failed.
"use strict";
const fs = require("fs");
const path = require("path");
const MaxOffline = require("../max-offline.js");

const list = JSON.parse(fs.readFileSync(path.join(__dirname, "..", ".claude", "docs", "offline-rules-cases.json"), "utf8"));

// Compare as text with sorted keys, so key order never matters
const plain = (v) => JSON.stringify(v, (k, x) => (x && typeof x === "object" && !Array.isArray(x)
  ? Object.keys(x).sort().reduce((o, key) => { o[key] = x[key]; return o; }, {}) : x));

// Only these parts of the command are compared (the same ones the page uses)
const KEEP = ["action", "priority", "repeat", "num", "changes", "missing", "choices", "text", "due", "category", "filter", "nums"];
const pick = (cmd) => (cmd ? KEEP.reduce((o, k) => (k in cmd ? Object.assign(o, { [k]: cmd[k] }) : o), {}) : null);

// A "several" card is compared by its labels, its tasks and the "One task" text (not the random id)
const cardView = (cmd) => (cmd && cmd.case === "several"
  ? { card: "several", labels: cmd.options.map((o) => o.label),
      tasks: cmd.options[0].do.tasks.map((t) => ["text", "due", "priority", "category", "repeat"].reduce((o, k) => Object.assign(o, { [k]: t[k] }), {})),
      one: cmd.options[1].do.text } : null);

let passed = 0;
const failed = [];
for (const c of list.cases) {
  const out = MaxOffline.understand(c.text, JSON.parse(JSON.stringify(list.todos)), list.now);
  const got = out && out.case === "several" ? cardView(out) : pick(out);
  const ok = plain(got) === plain(c.expect);
  if (ok) passed++; else failed.push(c);
  console.log(`${ok ? "PASS" : "FAIL"}  #${String(c.id).padStart(2, "0")} [${c.kind}] ${c.text}`);
  if (!ok) {
    console.log("      expected:", plain(c.expect));
    console.log("      got:     ", plain(got));
  }
}
console.log(`\n${passed} of ${list.cases.length} passed` + (failed.length ? `, ${failed.length} FAILED` : ""));
process.exit(failed.length ? 1 : 0);
