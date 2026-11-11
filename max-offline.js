// max-offline.js - "online Max": Python's clear-sentence rules (server.py) copied to plain JavaScript.
//
// WHY: on GitHub Pages there is no server, no AI and no Python. These rules read the CLEAR sentences
// (a task with a day/time, "#3 done", "move #3 to friday", "what's due today") so the page can answer
// them without anything online. They are also the fast path / offline backup if a real AI is added later.
//
// RULES OF THIS FILE
// - Same answers as Python. Every function below says which server.py function it copies. The shared test
//   list (.claude/docs/offline-rules-cases.json) holds answers that Python itself produced.
// - Not sure = return null. Never guess a date. (script.js then uses its old fallback.)
// - No framework, no build step, no network. Works in a browser (window.MaxOffline) and in Node (tools-js/).
//
// USE:  const cmd = MaxOffline.understand(text, todos, new Date());   // cmd or null
// The command has the same shape script.js already uses:
//   { action: "add", text, due, priority, category, repeat }          -> addTask(cmd)
//   { action: "complete" | "uncomplete" | "delete", num }             -> finishCommand(cmd)
//   { action: "update", num, changes: { due } }                       -> finishCommand(cmd)
//   { action: "<same>", missing: "#99", choices: [] }                 -> finishCommand(cmd) says "can't find #99"
//   { action: "answer", filter, nums }                                -> showAnswer(cmd)
(function (root) {
  "use strict";

  // ---------- Regex helper ----------
  // Python's \b treats Thai letters and digits as word characters; JavaScript's does not. This macro
  // gives JavaScript the same \b, so "5pm" next to Thai text is read the same way.
  const WORD = "[\\p{L}\\p{N}_]";
  const BOUNDARY = "(?:(?<!" + WORD + ")(?=" + WORD + ")|(?<=" + WORD + ")(?!" + WORD + "))";
  const rx = (src, flags = "") => new RegExp(src.replace(/\\b/g, BOUNDARY), flags + "u");
  const raw = String.raw;
  const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const global = (re) => new RegExp(re.source, re.flags + "g");        // same pattern, replace-all
  const startsWith = (re, text) => new RegExp(re.source, re.flags + "y").exec(text); // Python re.match

  // ---------- Calendar helpers (UTC dates, so summer time never moves a day) ----------
  const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const EN_DAYS = WEEKDAYS.map((d) => d.toLowerCase()).join("|");
  const pad = (n) => String(n).padStart(2, "0");
  const makeDay = (y, m, d) => new Date(Date.UTC(y, m - 1, d));
  const addDays = (dt, n) => new Date(dt.getTime() + n * 86400000);
  const isoDay = (dt) => dt.toISOString().slice(0, 10);
  const weekdayIndex = (dt) => (dt.getUTCDay() + 6) % 7;                 // Monday = 0
  const mod = (a, n) => ((a % n) + n) % n;
  // server.py add_months: the first day of the month n months after dt
  const addMonths = (dt, n) => {
    const m = dt.getUTCMonth() + n;
    return new Date(Date.UTC(dt.getUTCFullYear() + Math.floor(m / 12), mod(m, 12), 1));
  };
  // server.py weekday_date: "friday" = nearest on or after today; after = "next friday" = strictly after today
  function weekdayDate(name, today, after) {
    const gap = WEEKDAYS.indexOf(name) - weekdayIndex(today);
    return addDays(today, after ? mod(gap - 1, 7) + 1 : mod(gap, 7));
  }

  // "now" can be a Date, or the text the page sends ("2026-10-28T10:00 Wednesday")
  function parseNow(value) {
    if (value instanceof Date && !isNaN(value)) {
      return { y: value.getFullYear(), m: value.getMonth() + 1, d: value.getDate(), hh: value.getHours(), mm: value.getMinutes() };
    }
    const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/.exec(String(value || ""));
    return m ? { y: +m[1], m: +m[2], d: +m[3], hh: +(m[4] || 0), mm: +(m[5] || 0) } : null;
  }

  const DEFAULT_TIMES = { morning: "09:00", afternoon: "13:00", evening: "18:00", tonight: "20:00" };

  // ---------- Month names (server.py MONTHS) ----------
  const MONTH_ROWS = [["january", "jan", "มกราคม", "ม.ค."], ["february", "feb", "กุมภาพันธ์", "ก.พ."],
    ["march", "mar", "มีนาคม", "มี.ค."], ["april", "apr", "เมษายน", "เม.ย."], ["may", "", "พฤษภาคม", "พ.ค."],
    ["june", "jun", "มิถุนายน", "มิ.ย."], ["july", "jul", "กรกฎาคม", "ก.ค."], ["august", "aug", "สิงหาคม", "ส.ค."],
    ["september", "sep", "กันยายน", "ก.ย."], ["october", "oct", "ตุลาคม", "ต.ค."],
    ["november", "nov", "พฤศจิกายน", "พ.ย."], ["december", "dec", "ธันวาคม", "ธ.ค."]];
  const MONTHS = {};
  MONTH_ROWS.forEach((row, i) => row.forEach((name) => { if (name) MONTHS[name] = i + 1; }));
  MONTHS.sept = 9;
  const AMBIGUOUS_MONTHS = ["may", "march"]; // normal words too: they only count next to a day number
  const monthPattern = (names) => names.slice().sort((a, b) => b.length - a.length).map(escapeRe).join("|");
  const isAscii = (s) => /^[\x00-\x7f]*$/.test(s);
  const EN_MONTH = monthPattern(Object.keys(MONTHS).filter(isAscii));
  const TH_MONTH = monthPattern(Object.keys(MONTHS).filter((n) => !isAscii(n)));
  const MONTH_DAY_SRC = raw`\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(` + EN_MONTH + raw`)\b|` +
    raw`\b(` + EN_MONTH + raw`)\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b(?!:|\s*(?:am|pm)\b)|` +
    raw`(\d{1,2})\s*(?:เดือน\s*)?(` + TH_MONTH + ")";
  const BARE_MONTHS = raw`\b(?:` + monthPattern(Object.keys(MONTHS).filter((n) => isAscii(n) && !AMBIGUOUS_MONTHS.includes(n))) + raw`)\b|`;

  // Did the text name a day? (server.py DAY_HINTS)
  const DAY_HINTS = rx(
    raw`\b(today|tonight|tomorrow|next|week|month|` + EN_DAYS + raw`|in \d+ days?|in (\d+|a|one|two|three) weeks?|weekend|` +
    raw`end of (the |this )?month|(start|beginning) of next month|\d{1,2}(st|nd|rd|th))\b|\d{1,2}/\d{1,2}|` +
    BARE_MONTHS + MONTH_DAY_SRC + "|" + TH_MONTH + "|" +
    raw`มะรืน|พรุ่งนี้|วันนี้|คืนนี้|จันทร์|อังคาร|พุธ|พฤหัส|ศุกร์|เสาร์|วันอาทิตย์|วันที่\s*\d+|(สัปดาห์|อาทิตย์|เดือน)หน้า|` +
    raw`อีก\s*\d+\s*(วัน|สัปดาห์|อาทิตย์)|สิ้นเดือน|ปลายเดือน|ต้นเดือนหน้า|สุดสัปดาห์|เสาร์อาทิตย์`, "i");

  // ---------- Date typos (server.py fix_date_typos) ----------
  const DATE_WORDS = ["today", "tonight", "tomorrow", "next", "week", "month", "morning", "evening", "afternoon", "urgent"]
    .concat(EN_DAYS.split("|"), ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]);
  const SHORTCUTS = { tmr: "tomorrow", tmrw: "tomorrow", tml: "tomorrow", "2moro": "tomorrow", "2day": "today",
    tonite: "tonight", "2nite": "tonight", nxt: "next", wk: "week", asap: "urgent" };
  const SHORT_DAYS = { mon: "monday", tue: "tuesday", tues: "tuesday", wed: "wednesday", thu: "thursday",
    thur: "thursday", thurs: "thursday", fri: "friday", sat: "saturday", sun: "sunday" };
  const THAI_TYPOS = { "พรุ่งนี": "พรุ่งนี้", "พุ่งนี้": "พรุ่งนี้", "พรุ้งนี้": "พรุ่งนี้", "พรุงนี้": "พรุ่งนี้", "วันนี": "วันนี้", "มะรือ": "มะรืน" };
  const NOT_TYPOS = ["weekly", "monthly", "daily", "nightly", "weekend", "weekends", "weekday", "weekdays", "mornings", "evenings"];
  const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);

  // Python difflib.SequenceMatcher(None, a, b).ratio(): the same "how alike are two words" number,
  // so "tomorow" -> "tomorrow" is decided exactly like on the server.
  function similarity(a, b) {
    const b2j = {};
    for (let j = 0; j < b.length; j++) (b2j[b[j]] = b2j[b[j]] || []).push(j);
    let matched = 0;
    const queue = [[0, a.length, 0, b.length]];
    while (queue.length) {
      const [alo, ahi, blo, bhi] = queue.pop();
      let besti = alo, bestj = blo, bestsize = 0, j2len = {};
      for (let i = alo; i < ahi; i++) {
        const next = {};
        for (const j of b2j[a[i]] || []) {
          if (j < blo) continue;
          if (j >= bhi) break;
          const k = next[j] = (j2len[j - 1] || 0) + 1;
          if (k > bestsize) { besti = i - k + 1; bestj = j - k + 1; bestsize = k; }
        }
        j2len = next;
      }
      if (!bestsize) continue;
      matched += bestsize;
      if (alo < besti && blo < bestj) queue.push([alo, besti, blo, bestj]);
      if (besti + bestsize < ahi && bestj + bestsize < bhi) queue.push([besti + bestsize, ahi, bestj + bestsize, bhi]);
    }
    return a.length + b.length ? (2 * matched) / (a.length + b.length) : 1;
  }

  const stripChars = (s, chars) => s.replace(new RegExp("^[" + chars + "]+|[" + chars + "]+$", "g"), "");

  function fixDateTypos(sentence) {
    for (const wrong of Object.keys(THAI_TYPOS)) {
      const right = THAI_TYPOS[wrong];
      if (sentence.includes(wrong) && !sentence.includes(right)) sentence = sentence.split(wrong).join(right);
    }
    const parts = sentence.split(" ");
    return parts.map((word, i) => {
      const low = stripChars(word.toLowerCase(), ",.!?");
      const after = i + 1 < parts.length ? parts[i + 1].toLowerCase() : "";
      if (has(SHORTCUTS, low)) return SHORTCUTS[low];
      if (has(SHORT_DAYS, low) && (after === "" || /^\d/.test(after) || ["morning", "evening", "afternoon", "night", "at"].includes(after))) return SHORT_DAYS[low];
      if (low.length >= 4 && /^[a-z]+$/.test(low) && !DATE_WORDS.includes(low) && !NOT_TYPOS.includes(low)) {
        // same first letter + very alike (ratio 0.8), so normal words like "rent" never turn into "urgent"
        let best = null;
        for (const w of DATE_WORDS) {
          if (w[0] !== low[0]) continue;
          const score = similarity(w, low);
          if (score >= 0.8 && (!best || score > best[0] || (score === best[0] && w > best[1]))) best = [score, w];
        }
        if (best) return best[1];
      }
      return word;
    }).join(" ");
  }

  // ---------- Clock times ----------
  // Parts of the day with no clock time use the owner's own times (About me); Thai words stay specific.
  const DAY_PARTS = [[rx(raw`\b(to)?night\b|คืนนี้|ทุกคืน`), "tonight"], [rx(raw`\bevening\b|ตอนเย็น|เย็นนี้|พรุ่งนี้เย็น|ทุกเย็น`), "evening"],
    [rx(raw`\bafternoon\b|ตอนบ่าย|ทุกบ่าย`), "afternoon"], [rx(raw`\bmorning\b|ตอนเช้า|เช้านี้|พรุ่งนี้เช้า|ทุกเช้า`), "morning"]];

  const THAI_NUMS = { "หนึ่ง": 1, "สอง": 2, "สาม": 3, "สี่": 4, "ห้า": 5, "หก": 6, "เจ็ด": 7, "แปด": 8, "เก้า": 9, "สิบเอ็ด": 11, "สิบสอง": 12, "สิบ": 10 };
  const N = raw`(?<n>\d{1,2}|สิบเอ็ด|สิบสอง|สิบ|หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า)`;
  const THAI_TIMES = [ // [pattern, hour(n, matchedText)] - server.py THAI_TIMES
    [raw`เที่ยงคืน`, () => 0],
    [raw`เที่ยง(วัน)?`, () => 12],
    [raw`บ่าย\s*(โมง|` + N + raw`\s*(โมง)?)`, (n) => (n === null ? 13 : n < 12 ? n + 12 : n)],
    [N + raw`\s*ทุ่ม|ทุ่ม(นึง|หนึ่ง)?`, (n) => 18 + (n || 1)],
    [raw`ตี\s*` + N, (n) => n],
    [N + raw`\s*โมง\s*(เย็น|เช้า)?`, (n, w) => (w.includes("เช้า") || n >= 12 ? n : w.includes("เย็น") || n <= 5 ? n + 12 : n)],
  ];
  const THAI_TIME_ANY = THAI_TIMES.map(([p]) => p.replace("(?<n>", "(?:")).join("|");
  const THAI_TIME_RES = THAI_TIMES.map(([p, hour]) => [new RegExp("(?:" + p + ")\\s*(ครึ่ง)?"), hour]);

  // 'บ่ายสามครึ่ง' -> '15:30', 'สองทุ่ม' -> '20:00' ('' if no Thai time word)  (server.py thai_time)
  function thaiTime(text) {
    for (const [re, hour] of THAI_TIME_RES) {
      const m = re.exec(text);
      if (!m) continue;
      const n = m.groups && m.groups.n;
      const h = hour(n === undefined ? null : /^\d+$/.test(n) ? +n : THAI_NUMS[n], m[0]);
      if (h >= 0 && h <= 23) return pad(h) + ":" + (m[0].endsWith("ครึ่ง") ? "30" : "00");
    }
    return "";
  }

  const PART_TIME_SRC = raw`\b(\d{1,2})(?:[:.]([0-5]\d))?\s*(?:o'?clock\s*)?(?:in the |at |of the )?(morning|afternoon|evening|night)\b` +
    raw`|\b(morning|afternoon|evening|night)\s+(?:at\s+)?(\d{1,2})(?![\d:/]|st|nd|rd|th)`;
  const AT_HOUR_SRC = raw`\bat (\d{1,2})(?![\d:/]|st|nd|rd|th|\s*(?:days?|weeks?|min|hours?|times))`;
  const PART_TIME = rx(PART_TIME_SRC);
  const AT_HOUR = rx(AT_HOUR_SRC);
  const CLOCK_TIME = rx(raw`\d\s*(:\s*\d\d|\.\d\d|am\b|pm\b|น\.|โมง|ทุ่ม)|\bnoon\b|\bmidnight\b|` + PART_TIME_SRC + "|" + AT_HOUR_SRC + "|" + THAI_TIME_ANY, "i");
  const timeSaid = (text) => CLOCK_TIME.test(text) || DAY_PARTS.some(([re]) => re.test(text));

  // '5pm' -> '17:00', '9:30 am' -> '09:30', '17:45' -> '17:45', 'noon' -> '12:00' ('' if none)  (server.py english_time)
  function englishTime(text) {
    let m = rx(raw`\b(\d{1,2})(?:[:.]([0-5]\d))?\s*(am|pm)\b`).exec(text);
    if (m && +m[1] >= 1 && +m[1] <= 12) return pad((+m[1] % 12) + (m[3] === "pm" ? 12 : 0)) + ":" + (m[2] || "00");
    m = PART_TIME.exec(text);
    if (m) { // "7 in the morning" = 07:00, "3 in the afternoon" = 15:00, "8 at night" = 20:00
      let hour = +(m[1] || m[5]);
      const minute = m[2] || "00", part = m[3] || m[4];
      if (hour >= 1 && hour <= 12) {
        hour = (hour % 12) + (part === "morning" ? 0 : 12);
        return pad(hour % 24) + ":" + minute;
      }
    }
    m = text.includes("น") ? rx(raw`\b([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*น\.?|\b)`).exec(text) : null;
    m = m || rx(raw`\b([01]?\d|2[0-3]):([0-5]\d)\b`).exec(text);
    if (m) return pad(+m[1]) + ":" + m[2];
    m = AT_HOUR.exec(text); // "at 5": 1-6 is the afternoon, 7-11 the morning
    if (m && +m[1] >= 1 && +m[1] <= 23) return pad(+m[1] <= 6 ? +m[1] + 12 : +m[1]) + ":00";
    if (rx(raw`\bmidnight\b`).test(text)) return "00:00";
    return rx(raw`\bnoon\b`).test(text) ? "12:00" : "";
  }

  // ---------- Day words ----------
  const THAI_WEEKDAYS = [["จันทร์", "Monday"], ["อังคาร", "Tuesday"], ["พุธ", "Wednesday"], ["พฤหัส", "Thursday"],
    ["ศุกร์", "Friday"], ["เสาร์", "Saturday"], ["วันอาทิตย์", "Sunday"]];
  const NEXT_WEEK = rx(raw`\bnext\b|(สัปดาห์|อาทิตย์|จันทร์|อังคาร|พุธ|พฤหัส(บดี)?|ศุกร์|เสาร์)หน้า`);
  const WEEK_AFTER = rx(raw`\bnext week\b|(สัปดาห์|(?<!วัน)อาทิตย์)หน้า`);
  const NOWADAYS = "ทุกวันนี้"; // "nowadays": not "today"
  const DAY_WORDS = [[["มะรืน", "day after tomorrow"], "day_after_tomorrow"], [["พรุ่งนี้", "tomorrow"], "tomorrow"],
    [["วันนี้", "today", "tonight", "คืนนี้"], "today"]];
  const WEEKS_AHEAD = rx(raw`\bin\s+(\d+|a|one|two|three)\s+weeks?\b|อีก\s*(\d+)\s*(?:สัปดาห์|อาทิตย์)`);
  const WEEKEND = rx(raw`\bweekend\b|สุดสัปดาห์|เสาร์อาทิตย์`);
  const MONTH_END_NEXT = rx(raw`\bend of next month\b|(?:สิ้น|ปลาย)เดือนหน้า`);
  const MONTH_END = rx(raw`\bend of (?:the |this )?month\b|สิ้นเดือน|ปลายเดือน`);
  const MONTH_START = rx(raw`\b(?:start|beginning) of next month\b|ต้นเดือนหน้า`);
  const SPECIAL_DAYS = [WEEKS_AHEAD, WEEKEND, MONTH_END_NEXT, MONTH_END, MONTH_START];
  const WEEK_COUNTS = { a: 1, one: 1, two: 2, three: 3 };
  const DAYS_AHEAD = rx(raw`\bin\s+(\d+)\s+days?\b|อีก\s*(\d+)\s*วัน`);

  function weekdayIn(lower) { // server.py weekday_in
    const m = rx(raw`\b(` + EN_DAYS + raw`)\b`).exec(lower);
    if (m) return m[1][0].toUpperCase() + m[1].slice(1);
    const found = THAI_WEEKDAYS.find(([thai]) => lower.includes(thai));
    return found ? found[1] : "";
  }
  function specialDay(lower) { // server.py special_day
    const m = WEEKS_AHEAD.exec(lower);
    if (m) {
      const n = m[1] || m[2];
      return { when: "in_days", in_days: 7 * Number(has(WEEK_COUNTS, n) ? WEEK_COUNTS[n] : n) };
    }
    const kinds = [[WEEKEND, "weekend"], [MONTH_END_NEXT, "month_end_next"], [MONTH_END, "month_end"], [MONTH_START, "month_start"]];
    for (const [re, label] of kinds) if (re.test(lower)) return { when: "special", special: label };
    return {};
  }
  function daysAhead(lower) { // server.py days_ahead
    const m = DAYS_AHEAD.exec(lower);
    return m ? Number(m[1] || m[2]) : 0;
  }

  // Repeating tasks ("every monday") are not in this file yet: the sentence is left alone (null)
  const ORD = raw`\d{1,2}(?:st|nd|rd|th)`;
  const TH_DAYS = "จันทร์|อังคาร|พุธ|พฤหัส|ศุกร์|เสาร์|อาทิตย์";
  const REPEAT_WORDS = rx(
    raw`\b(?:every|each)\s+month\b(?:\s+on\s+the\s+` + ORD + raw`)?|\bmonthly\b|\bevery\s+` + ORD + raw`\b|ทุกเดือน|ทุกวันที่\s*\d{1,2}` + "|" +
    raw`\b(?:every|each)\s+(?:week|` + EN_DAYS + raw`)\b|\bweekly\b|ทุกวัน(?:` + TH_DAYS + raw`)|ทุก(?:สัปดาห์|อาทิตย์)` + "|" +
    raw`\b(?:every|each)\s+(?:day|morning|afternoon|evening|night)\b|\b(?:daily|nightly)\b|ทุกวัน(?!นี้)|ทุก(?:เช้า|บ่าย|เย็น|คืน)`);

  // The real date for date words (server.py resolve_due; the "5 december" branch is not needed: those sentences return null)
  function resolveDue(task, today, times) {
    const when = task.when || "none";
    let date = null;
    if (when === "today") date = today;
    else if (when === "tomorrow" || when === "day_after_tomorrow") date = addDays(today, when === "tomorrow" ? 1 : 2);
    else if (when === "in_days" && (task.in_days || 0) > 0) date = addDays(today, task.in_days);
    else if (when === "weekday" && WEEKDAYS.includes(task.weekday)) {
      const target = WEEKDAYS.indexOf(task.weekday);
      date = task.week_after ? addDays(today, -weekdayIndex(today) + 7 + target) // "friday next week": that weekday in the next Mon-Sun week
        : weekdayDate(task.weekday, today, !!task.next_week);
    } else if (when === "special") {
      const firstNext = addMonths(makeDay(today.getUTCFullYear(), today.getUTCMonth() + 1, 1), 1);
      if (task.special === "weekend") date = addDays(today, Math.max(5 - weekdayIndex(today), 0));
      else if (task.special === "month_end") date = addDays(firstNext, -1);
      else if (task.special === "month_end_next") date = addDays(addMonths(firstNext, 1), -1);
      else if (task.special === "month_start") date = firstNext;
    }
    if (!date) return "";
    const hm = /^(\d{2}):(\d{2})$/.test(task.time || "") ? task.time : (times || DEFAULT_TIMES).morning;
    return isoDay(date) + "T" + hm;
  }

  // Day/time words Python can read alone -> the dict resolveDue needs. null = something else is in there
  // (a month, "next week"...), so only the AI could read it  (server.py rules_date)
  function rulesDate(text, times) {
    const low = fixDateTypos(text).toLowerCase().split(NOWADAYS).join(" ");
    const task = { when: "none", time: thaiTime(low) || englishTime(low) };
    const day = weekdayIn(low);
    if (day) Object.assign(task, { when: "weekday", weekday: day, next_week: NEXT_WEEK.test(low), week_after: WEEK_AFTER.test(low) });
    else if (daysAhead(low)) Object.assign(task, { when: "in_days", in_days: daysAhead(low) });
    for (const [words, when] of DAY_WORDS) {
      if (words.some((w) => low.includes(w))) { task.when = when; break; }
    }
    Object.assign(task, specialDay(low));
    // Take out every day word handled above; if DAY_HINTS still finds a date word, the AI is needed
    let left = low.replace(global(DAYS_AHEAD), " ");
    for (const re of SPECIAL_DAYS) left = left.replace(global(re), " ");
    for (const [words] of DAY_WORDS) for (const w of words) left = left.split(w).join(" ");
    left = left.replace(rx(raw`\b(` + EN_DAYS + raw`)\b|(วัน)?(` + THAI_WEEKDAYS.map(([t]) => t).join("|") + ")", "g"), " ");
    if (day) left = left.replace(rx(raw`\bnext\b`, "g"), " "); // "next friday" is fine; "next week" is not
    if (DAY_HINTS.test(left)) return null;
    const t = times || DEFAULT_TIMES;
    if (!CLOCK_TIME.test(low)) {
      for (const [re, part] of DAY_PARTS) if (re.test(low)) { task.time = t[part]; break; }
    }
    if (CLOCK_TIME.test(low) && !task.time) return null; // a clock time we could not read
    if (task.when === "none") {
      if (!task.time) return null;
      task.when = "today"; // only a time: today
    }
    return task;
  }

  // ---------- Words around a task ----------
  const GREETING = rx(raw`^\s*(?:(?:hi|hey|hello|yo|ok|okay|good\s+(?:morning|afternoon|evening))(?=[\s,!.]|$)[\s,!.]*(?:max(?=[\s,!.:]|$)[\s,!.:]*)?` +
    raw`|morning(?=\s+max(?:[\s,!.:]|$))[\s,!.]*(?:max[\s,!.:]*)?` +
    raw`|max\s*[,:!]\s*` +
    raw`|(?:สวัสดี|หวัดดี|โอเค|อรุณสวัสดิ์)(?:ครับ|ค่ะ|คะ)?\s*(?:max|แม็กซ์|แม็ก)?\s*(?:ครับ|ค่ะ|คะ)?[\s,!]*` +
    raw`|(?:แม็กซ์|แม็ก)(?:ครับ|ค่ะ|คะ)?\s*[,:!]?\s*)`, "i");
  // server.py strip_greeting: [sentence without the greeting, was there a greeting]
  function stripGreeting(sentence) {
    const rest = sentence.replace(GREETING, "").trim();
    return rest && rest !== sentence.trim() ? [rest, true] : [sentence, false];
  }
  const ADD_WORDS = rx(raw`^(add|create|new task:?)\s+|^เพิ่ม(งาน)?\s*`, "i");
  const LEAD_INS = rx(raw`^(please\s+)?(remind\s+me(\s+(to|about|of))?|remember\s+to|don'?t\s+forget(\s+to)?)\s+` +
    raw`|^(เตือน(ฉัน|ผม|เรา)?ให้|เตือน(ฉัน|ผม|เรา)|อย่าลืม)\s*`, "i");
  const stripLeadIn = (text) => text.trim().replace(LEAD_INS, "").trim() || text.trim();
  // "add buy milk" / "remind me to call mom" / typos fixed  (server.py clean_sentence)
  const cleanSentence = (sentence) => fixDateTypos(stripLeadIn(sentence.replace(ADD_WORDS, "").trim() || sentence));

  const THAI_DATE_WORDS = global(rx(
    raw`(?<!ทุก)(?:(?:ภายใน|ใน|ตอน|เมื่อ|ก่อน)\s*)?(?:มะรืนนี้|มะรืน|พรุ่งนี้|วันนี้|คืนนี้|ตอนเช้า|ตอนเย็น|ตอนบ่าย|ด่วน|ไม่รีบ|` +
    raw`(วัน)?(จันทร์|อังคาร|พุธ|พฤหัส(บดี)?|ศุกร์|เสาร์|อาทิตย์)(หน้า|นี้)?|วันที่\s*\d+|` +
    raw`(` + THAI_TIME_ANY + raw`)(\s*ครึ่ง)?|\d+\s*(โมง|ทุ่ม)|(สัปดาห์|เดือน)หน้า|อีก\s*\d+\s*(วัน|สัปดาห์|อาทิตย์)|(สิ้น|ปลาย)เดือน(หน้า)?|ต้นเดือนหน้า|สุดสัปดาห์(นี้)?|` +
    raw`(\d{1,2}\s*)?(เดือน\s*)?(` + TH_MONTH + "))"));
  const EN_DATE_WORDS = global(rx(
    raw`\b(?:(?:on|by|at|for)\s+)?(?:(?:next|this)\s+)?(?:day after tomorrow|tomorrow(?:\s+(?:morning|afternoon|evening|night))?|today|tonight|` +
    raw`this\s+(?:morning|afternoon|evening)|weekend|next week|(?:` + EN_DAYS + raw`)|` +
    raw`in\s+\d+\s+days?|\d{1,2}(?::\d\d)?\s*[ap]m|\d{1,2}:\d\d)\b`, "i"));
  const THAI_PART = global(rx(raw`\s(เช้า|เย็น|บ่าย|ค่ำ|ดึก)(\s|$)`));
  const THAI_LETTERS = /[\u0E00-\u0E7F]/;
  const TRAILING_TIME = rx(raw`\s+(?:at\s+\d{1,2}(?:[:.]\d\d)?(?:\s*(?:am|pm))?|\d{1,2}(?:[:.]\d\d)?\s*(?:am|pm))\s*$`, "i");
  const oneSpace = (s) => s.split(/\s+/).filter(Boolean).join(" ");
  const capital = (s) => s.slice(0, 1).toUpperCase() + s.slice(1);

  // The title once the day/time words are in the due date: check_task's title step + clean_title in server.py
  function makeTitle(sentence, hasTime) {
    let title = stripLeadIn(sentence);
    if (THAI_LETTERS.test(title)) { // date/time words left in a Thai title ("นัดหมอฟัน เย็น" -> "นัดหมอฟัน")
      const clean = (" " + title.replace(THAI_DATE_WORDS, " ")).replace(THAI_PART, " ");
      title = oneSpace(clean) || title;
    }
    if (hasTime && !THAI_LETTERS.test(title)) title = title.replace(TRAILING_TIME, "").trim() || title; // "Take vitamins at 7"
    title = capital(title);
    const plain = stripChars(oneSpace(title.replace(EN_DATE_WORDS, " ").replace(THAI_DATE_WORDS, " ")), " ,.");
    return capital(plain || title);
  }

  // ---------- Category (server.py pick_category, with no AI category) ----------
  const DEFAULT_CATEGORIES = ["Work", "Home", "Shopping", "Health", "Study", "Money", "Personal"];
  const CATEGORY_HINTS = [
    ["Health", rx(raw`\b(gym|run|running|jog|jogging|workout|exercise|yoga|doctor|dentist|dental|hospital|clinic|medicine|pharmacy|check-?up|vitamins?)\b|ออกกำลัง|วิ่ง|ฟิตเนส|โยคะ|หมอ|ฟัน|โรงพยาบาล|คลินิก|กินยา|ซื้อยา|ตรวจสุขภาพ`)],
    ["Home", rx(raw`\b(rent|bills?|clean|cleaning|laundry|groceries|grocery|dishes|trash|garbage|repaint|repair)\b|ค่าเช่า|ค่าน้ำ|ค่าไฟ|ทำความสะอาด|ซักผ้า|ล้างจาน|ทิ้งขยะ|ซ่อม|ซื้อของเข้าบ้าน|ตลาด`)],
    ["Study", rx(raw`\b(study|homework|exam|class|course|lecture|assignment)\b|เรียน|การบ้าน|สอบ|อ่านหนังสือ`)],
    ["Money", rx(raw`\b(pay|tax|bank|salary|budget|invoice|transfer|insurance)\b|ภาษี|ธนาคาร|โอนเงิน|เงินเดือน|ประกัน|จ่าย`)],
    ["Shopping", rx(raw`\b(buy|shopping|order|purchase)\b|ซื้อ|สั่งของ`)],
    ["Work", rx(raw`\b(meeting|report|email|client|project|deadline|boss|presentation)\b|ประชุม|รายงาน|ลูกค้า|โปรเจกต์|พรีเซนต์`)],
  ];
  const WORK_WORDS = rx(raw`\b(boss|client|team|meeting|project|report|server|code|office|colleague|deadline|presentation|email)\b|งาน|ประชุม|หัวหน้า|ลูกค้า|รายงาน|โปรเจกต์`);
  const STRONG_HINTS = [["Health", rx(raw`\b(gym|workout|dentist|doctor)\b|ยิม|หมอ`)], ["Home", rx(raw`\brent\b|ค่าเช่า`)]];
  function pickCategory(sentence, known) {
    const names = {};
    DEFAULT_CATEGORIES.concat(known).forEach((c) => { names[c.toLowerCase()] = c; }); // the owner's own spelling wins
    const lower = sentence.toLowerCase();
    if (WORK_WORDS.test(lower)) return names.work;
    for (const [name, re] of STRONG_HINTS) if (re.test(lower)) return names[name.toLowerCase()] || name;
    for (const [name, re] of CATEGORY_HINTS) if (re.test(lower)) return names[name.toLowerCase()] || name;
    return "";
  }

  // ---------- Commands on one task: #3 done / undo / delete / move (server.py command_by_rules) ----------
  const UNDO_WORDS = rx(raw`^(undo|undone|uncheck|unmark|reopen|not done)\b|ยังไม่เสร็จ|ยกเลิกเสร็จ`);
  const DELETE_WORDS = rx(raw`^(delete|remove|del|erase|cancel(?=\s*#)|get rid of)\b|^ลบ`);
  const DONE_WORDS = rx(raw`^(done|mark(?!['’])|tick|finished|completed)\b|\b(done|finished|completed)$|เสร็จ(แล้ว)?$|^เสร็จ`);
  const UPDATE_WORDS = rx(raw`^(change|modify|move|rename|set|edit|update|reschedule|postpone|push|delay)\b|^(เปลี่ยน|แก้|ย้าย|เลื่อน)`);
  const ACTION_PATTERNS = [UNDO_WORDS, DELETE_WORDS, DONE_WORDS, UPDATE_WORDS];
  const FILLER = rx(raw`^((the|task|as|is|of|to)\b|งาน|ของ|ให้เป็น|เป็น|ไปเป็น|ไป)\s*`, "i");
  const FIELD_WORDS = { category: "category", cat: "category", "หมวดหมู่": "category", "หมวด": "category", priority: "priority", "ความสำคัญ": "priority",
    date: "due", due: "due", time: "due", deadline: "due", "วันที่": "due", "เวลา": "due", name: "text", title: "text", text: "text", "ชื่อ": "text" };
  const FIELD_RE = rx("^(" + Object.keys(FIELD_WORDS).sort((a, b) => b.length - a.length).map(escapeRe).join("|") + raw`)\b\s*`, "i");
  const FIELD_RE_TH = rx(raw`^(หมวดหมู่|หมวด|ความสำคัญ|วันที่|เวลา|ชื่อ)\s*`);
  const NUMBER_FORMS = rx(raw`(?:ข้อที่|ข้อ|งานที่|งานข้อ|\bno\.?|\bnumber|\btask|\bitem)\s*(\d+)`, "i");
  const PRIORITY_WORDS = { high: 1, urgent: 1, important: 1, asap: 1, "ด่วน": 1, "สูง": 1, "สำคัญ": 1, low: 1, someday: 1, maybe: 1,
    "ไม่รีบ": 1, "ต่ำ": 1, med: 1, medium: 1, normal: 1, "กลาง": 1, "ปกติ": 1 };
  const BY_DAYS = rx(raw`^(?:by\s+(?<n>\d+|a|an|one|two|three)\s*(?<unit>days?|weeks?)|(?:อีก\s*)?(?<th>\d+)\s*(?<thunit>วัน|สัปดาห์|อาทิตย์))$`);
  const NUMBER_WORDS = { a: 1, an: 1, one: 1, two: 2, three: 3 };
  const SPLIT_TARGET = rx(raw`\s+to\s+|\s+(?=by\s+(?:\d|an?\b|one\b|two\b|three\b))|\s*(?:ให้เป็น|ไปเป็น|เป็น|ไปวัน|ไป)\s*`);

  function stripFiller(s) {
    s = stripChars(s, " .,!?:");
    for (;;) {
      let next = s.replace(FILLER, "");
      next = stripChars(next.replace(rx(raw`\s*\b(as|is|to)$`, "i"), ""), " .,!?:");
      if (next === s) return s;
      s = next;
    }
  }
  // Python re.sub(pattern, " ", text, count=2)
  function removeTwice(re, text) {
    const g = new RegExp(re.source, "giu");
    let count = 0;
    return text.replace(g, (match) => (++count <= 2 ? " " : match));
  }

  // What an update changes: only a date or time (server.py work_out_changes). null = not sure (rename, priority, hard dates)
  function updateChanges(num, change, field, rename, low, tasks, now, times) {
    if (!change || rename) return null;
    const task = tasks.find((t) => t.num === num);
    const oldDue = (task && task.due) || "";
    const nowDay = pad2date(now);
    const by = BY_DAYS.exec(change.trim().toLowerCase());
    if (by && !field && (by.groups.n || low.startsWith("เลื่อน"))) { // "delay #3 by 2 days": counted from the task's own day
      const n = by.groups.n || by.groups.th;
      let count = /^\d+$/.test(n) ? Number(n) : NUMBER_WORDS[n];
      if ((by.groups.unit || by.groups.thunit).startsWith("week") || ["สัปดาห์", "อาทิตย์"].includes(by.groups.thunit)) count *= 7;
      const base = (oldDue || nowDay).slice(0, 10).split("-").map(Number);
      return { due: isoDay(addDays(makeDay(base[0], base[1], base[2]), count)) + "T" + (oldDue.slice(11, 16) || "09:00") };
    }
    if (field && field !== "due") return null; // category / priority / name: not here
    const words = change.toLowerCase().split(/[\s,]+/).filter(Boolean);
    if (words.some((w) => has(PRIORITY_WORDS, w)) || Object.keys(PRIORITY_WORDS).some((w) => !isAscii(w) && change.includes(w))) return null;
    const fixed = fixDateTypos(change).toLowerCase();
    const day = DAY_HINTS.test(fixed), clock = timeSaid(fixed);
    if (!(day || clock || field === "due")) return null; // no date words: it would be a rename
    const rules = rulesDate(change, times);
    if (!rules) return null;
    const today = makeDay(now.y, now.m, now.d);
    let due = resolveDue(rules, today, times);
    if (clock && !day && rules.time) due = (oldDue.slice(0, 10) || nowDay) + "T" + rules.time; // only a time: keep the task's day
    else if (due && !clock && oldDue) due = due.slice(0, 11) + oldDue.slice(11);              // only a day: keep the task's time
    return due ? { due } : null;
  }
  const pad2date = (now) => now.y + "-" + pad(now.m) + "-" + pad(now.d);

  // -> { kind: "none" } (no command words: maybe a new task) | { kind: "unsure" } | { kind: "cmd", cmd }
  function commandByRules(s, tasks, now, times) {
    const NONE = { kind: "none" }, UNSURE = { kind: "unsure" };
    const numberFirst = /^(#\s*\d+)\s*(.+)/.exec(s);
    if (numberFirst && ACTION_PATTERNS.some((p) => startsWith(p, numberFirst[2].toLowerCase()))) s = numberFirst[2] + " " + numberFirst[1];
    const low = s.toLowerCase();
    let action;
    if (UNDO_WORDS.test(low)) action = "uncomplete";
    else if (DELETE_WORDS.test(low)) action = "delete";
    else if (DONE_WORDS.test(low)) action = "complete";
    else if (UPDATE_WORDS.test(low) || /^#\s*\d+/.test(low)) action = "update";
    else return NONE;

    s = s.replace(global(NUMBER_FORMS), "#$1"); // "ข้อ 3", "no. 3", "number 3" all mean #3
    let rest = s;
    for (const p of ACTION_PATTERNS) if (p.test(low)) rest = removeTwice(p, rest);
    const rename = !!startsWith(rx(raw`(rename|เปลี่ยนชื่อ)`), low);
    const numMatch = /#\s*(\d+)/.exec(rest);
    if (numMatch) rest = rest.slice(0, numMatch.index) + " " + rest.slice(numMatch.index + numMatch[0].length);
    rest = stripFiller(rest);

    // "the date of #3 to friday", "#4 priority high"
    let field = rename ? "text" : "";
    const fm = FIELD_RE.exec(rest) || FIELD_RE_TH.exec(rest);
    if (action === "update" && fm && (!rename || FIELD_WORDS[fm[1].toLowerCase()] === "text")) {
      field = FIELD_WORDS[fm[1].toLowerCase()];
      rest = stripFiller(rest.slice(fm[0].length));
    }

    let target = "", change = "";
    if (numMatch) { target = numMatch[0]; change = rest; }
    else if (action === "update") {
      const sp = SPLIT_TARGET.exec(rest);
      if (!sp) return NONE; // "set up the printer": a new task, not a command
      return UNSURE;        // update by task NAME: needs the fuzzy match / AI, not here
    } else target = rest;

    if (!numMatch) {
      const words = target.toLowerCase().trim();
      if (!words || /^#?\s*\d+$/.test(words) || ["it", "this", "that", "this one", "that one", "them", "มัน", "อันนี้", "งานนี้", "นี้"].includes(words)) return UNSURE;
      // By name: only when the words are written inside exactly ONE task title that fits ("undo" = done tasks, "done" = open ones)
      const wanted = { uncomplete: true, complete: false }[action];
      const pool = wanted === undefined ? tasks : tasks.filter((t) => !!t.done === wanted);
      const hits = pool.filter((t) => String(t.text || "").toLowerCase().includes(words));
      return hits.length === 1 ? { kind: "cmd", cmd: { action, num: hits[0].num } } : UNSURE;
    }

    const num = Number(/\d+/.exec(target)[0]);
    if (!tasks.some((t) => t.num === num)) return { kind: "cmd", cmd: { action, missing: target, choices: [] } }; // "can't find #99"
    if (action !== "update") return { kind: "cmd", cmd: { action, num } };
    const changes = updateChanges(num, change, field, rename, low, tasks, now, times);
    return changes ? { kind: "cmd", cmd: { action: "update", num, changes } } : UNSURE;
  }

  // ---------- Questions: what's due today / this week, what did I finish (server.py parse_question) ----------
  const QUESTION_START = rx(raw`^(what|what's|whats|which|show|list|how many|how much|anything|any|is there|are there|do i have|have i got|tell me|give me)\b`);
  const QUESTION_TH = rx(raw`มีอะไร|อะไรบ้าง|กี่งาน|งานอะไร|งานไหน|อันไหน|งานค้าง|เลยกำหนด|เกินกำหนด|^แสดง`);
  const NATURAL_Q = rx(raw`\bwhat (?:to do|should i|shall i|do i (?:have|need|got)|am i (?:doing|supposed)|have i got|else)\b` +
    raw`|\bwhat(?:'s| is) (?:my|on|the plan)\b|\bwhats (?:my|on)\b|^my (?:tasks?|to-?dos?|plan|day|schedule)\b|ทำอะไรดี|ต้องทำ|ทำอะไร`);
  const TASK_WORDS = rx(raw`\b(tasks?|to-?dos?|left|remaining|pending|outstanding|open|have)\b|งาน`);
  const ORDER_START = rx(raw`^(show|list|tell me|give me)\b`);
  const ABOUT = rx(raw`(?:about|regarding|containing|เกี่ยวกับ|เรื่อง)\s*(.+?)(?=\s+(?:due|today|tomorrow|this|next|on|by|before|overdue|high|urgent|in)\b|วันนี้|พรุ่งนี้|สัปดาห์|อาทิตย์|[?.!]|$)`);
  const ORDINAL_DAY = rx(raw`\b(\d{1,2})(?:st|nd|rd|th)\b|วันที่\s*(\d{1,2})`);
  const UNREAD_DAY = rx(raw`yesterday|\blast (week|month)|\bmonth\b|\d{1,2}/\d{1,2}|(jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d|\d\s*(jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)|เมื่อวาน|เดือน`);

  function nextWeekdayNamed(low, today) { // "next friday" / "วันศุกร์หน้า": the first such day strictly after today
    let name = "";
    const m = rx(raw`\bnext\s+(` + EN_DAYS + raw`)\b`).exec(low);
    if (m) name = m[1][0].toUpperCase() + m[1].slice(1);
    else {
      const t = rx(raw`(?:วัน)?(จันทร์|อังคาร|พุธ|พฤหัส|ศุกร์|เสาร์)(?:บดี)?หน้า|(วันอาทิตย์)หน้า`).exec(low);
      if (!t) return "";
      name = THAI_WEEKDAYS.find(([thai]) => thai === (t[1] || t[2]))[1];
    }
    return isoDay(weekdayDate(name, today, true));
  }

  function questionFilter(low, now, categories) {
    const f = { when: "", date: "", priority: "", cat: "", status: "open", text: "" };
    const today = makeDay(now.y, now.m, now.d);
    const names = Array.from(new Set(categories.concat(DEFAULT_CATEGORIES)));
    const num = NUMBER_FORMS.exec(low);
    if (num) { f.num = Number(num[1]); return f; } // "what is task 12?"
    const sp = specialDay(low);
    const dayWords = Object.keys(sp).length ? sp : (daysAhead(low) ? { when: "in_days", in_days: daysAhead(low) } : {});
    const about = ABOUT.exec(low);
    if (about) {
      f.text = stripChars(about[1].trim(), " ?.!");
      low = low.slice(0, about.index) + " " + low.slice(about.index + about[0].length);
      if (names.some((n) => n.toLowerCase() === f.text)) { f.cat = f.text; f.text = ""; } // "about work" = the category Work
    }
    const nextNamed = nextWeekdayNamed(low, today);
    if (rx(raw`overdue|\blate\b|past due|เลยกำหนด|เกินกำหนด|งานค้าง|ค้างอยู่`).test(low)) f.when = "overdue";
    else if (rx(raw`no (due )?date|without (a )?(due )?date|undated|ไม่มีวันที่|ไม่มีกำหนด`).test(low)) f.when = "none";
    else if (rx(raw`yesterday|เมื่อวาน`).test(low)) { f.when = "date"; f.date = isoDay(addDays(today, -1)); } // job 9
    else if (rx(raw`day after tomorrow|มะรืน`).test(low)) { f.when = "date"; f.date = isoDay(addDays(today, 2)); }
    else if (nextNamed) { f.when = "date"; f.date = nextNamed; }
    else if (dayWords.special === "weekend") f.when = "weekend";
    else if (Object.keys(dayWords).length) { f.when = "date"; f.date = resolveDue(dayWords, today, DEFAULT_TIMES).slice(0, 10); }
    else if (rx(raw`next week|สัปดาห์หน้า|อาทิตย์หน้า`).test(low)) f.when = "nextweek";
    else if (rx(raw`\bweek\b|สัปดาห์นี้|อาทิตย์นี้`).test(low)) f.when = "week";
    else if (rx(raw`tomorrow|พรุ่งนี้`).test(low)) f.when = "tomorrow";
    else if (rx(raw`\btoday\b|\btonight\b|วันนี้|คืนนี้`).test(low)) f.when = "today";
    else if (weekdayIn(low)) { f.when = "date"; f.date = isoDay(weekdayDate(weekdayIn(low), today, false)); }
    else if (ORDINAL_DAY.test(low)) {
      const g = ORDINAL_DAY.exec(low);
      const day = Number(g[1] || g[2]);
      for (const add of [0, 1]) { // this month if the day has not passed, else next month
        const first = addMonths(makeDay(now.y, now.m, 1), add);
        const date = makeDay(first.getUTCFullYear(), first.getUTCMonth() + 1, day);
        if (date.getUTCMonth() !== first.getUTCMonth()) continue; // e.g. the 31st of a 30-day month
        if (date >= today) { f.when = "date"; f.date = isoDay(date); break; }
      }
    }
    if (!f.when && UNREAD_DAY.test(low)) f.unread = true; // a day we cannot read
    if (rx(raw`\b(high|urgent|important|asap)\b|ด่วน|สำคัญ`).test(low)) f.priority = "high";
    else if (rx(raw`\blow\b|ไม่รีบ`).test(low)) f.priority = "low";
    // "what did I finish" asks for DONE tasks (same as question_filter in server.py)
    if (rx(raw`\b(done|completed|finished)\b|เสร็จแล้ว|อะไรเสร็จ|\bdid i (?:finish|complete)\b`).test(low)) {
      f.status = "done";
      // "what did I finish on monday?" = the Monday that has passed
      if (f.when === "date" && weekdayIn(low) && f.date > isoDay(today)) f.date = isoDay(addDays(makeDay(...f.date.split("-").map(Number)), -7));
    }
    for (const name of names) {
      if (!f.cat && rx("(?<!" + WORD + ")" + escapeRe(name.toLowerCase()) + "(?!" + WORD + ")").test(low)) f.cat = name.toLowerCase();
    }
    return f;
  }

  // The filter if the sentence is a question about the tasks, else null
  function parseQuestion(sentence, now, categories) {
    const raw0 = oneSpace(stripGreeting(sentence)[0]).toLowerCase();
    if (/#\s*\d/.test(raw0)) return null; // "#3" always means a command
    if (!(QUESTION_START.test(raw0) || raw0.endsWith("?") || QUESTION_TH.test(raw0) || NATURAL_Q.test(raw0))) return null;
    const low = fixDateTypos(raw0);
    const f = questionFilter(low, now, categories);
    const something = f.num || f.when || f.unread || f.priority || f.cat || f.text || f.status === "done";
    if (ORDER_START.test(low)) return TASK_WORDS.test(raw0) || f.priority || f.cat || f.when === "overdue" ? f : null;
    return something || TASK_WORDS.test(raw0) || NATURAL_Q.test(raw0) ? f : null;
  }

  function dueRange(f, today) { // server.py due_range
    const wd = weekdayIndex(today);
    const day = (n) => isoDay(addDays(today, n));
    if (f.when === "today") return [day(0), day(0)];
    if (f.when === "tomorrow") return [day(1), day(1)];
    if (f.when === "week") return [day(0), day(6 - wd)];              // today until Sunday
    if (f.when === "weekend") return [day(Math.max(5 - wd, 0)), day(6 - wd)];
    if (f.when === "nextweek") return [day(7 - wd), day(13 - wd)];    // next Monday until next Sunday
    return [f.date, f.date];
  }
  function listTasks(tasks, f, now) { // server.py list_tasks: soonest first
    if (f.num) return tasks.filter((t) => t.num === f.num);
    const today = makeDay(now.y, now.m, now.d);
    const nowText = pad2date(now) + "T" + pad(now.hh) + ":" + pad(now.mm);
    const ranged = ["today", "tomorrow", "week", "weekend", "nextweek", "date"].includes(f.when);
    let [first, last] = ranged ? dueRange(f, today) : ["", ""];
    const doneAsk = f.status === "done";
    if (doneAsk && f.when === "week") [first, last] = [isoDay(addDays(today, -weekdayIndex(today))), isoDay(today)]; // Monday until today
    const found = tasks.filter((t) => {
      // job 9: a day asked about DONE tasks = the day it was ticked (doneAt), not the due day
      const due = (doneAsk && first ? t.doneAt : t.due) || "";
      if (!!t.done !== (f.status === "done")) return false;
      if (f.priority && (t.priority || "med") !== f.priority) return false;
      if (f.cat && (t.cat || "").toLowerCase() !== f.cat.toLowerCase()) return false;
      if (f.text && !String(t.text).toLowerCase().includes(f.text.toLowerCase())) return false;
      if (f.when === "none" && due) return false;
      if (f.when === "overdue" && !(due && due < nowText)) return false;
      if (first && !(due && first <= due.slice(0, 10) && due.slice(0, 10) <= last)) return false;
      return true;
    });
    return found.sort((a, b) => (a.due || "9999").localeCompare(b.due || "9999") || a.num - b.num);
  }

  // ---------- A new task with a day or time ----------
  const TEAM = rx(raw`^(tell|ask|message|send\s+(?:a\s+message\s+)?to)\s+(toto|kimi|george|bono|lewis|gp)(?![a-z0-9])|^(บอก|ถาม|ส่งถึง|ฝากบอก)\s*(โตโต้|โตโต|โทโท|คิมิ|จอร์จ|โบโน่|โบโน|ลูอิส|ลูอีส|จีพี|toto|kimi|george|bono|lewis|gp)`, "i");
  const PRIORITY_HINT = rx(raw`\b(urgent|important|asap|someday)\b|ด่วน|สำคัญ|ไม่รีบ`);
  const JOINER = rx(raw`\s(?:and|also|then)\s|,\s*then\s|และ|แล้วก็`, "i");
  const EVENT_WORDS = rx(raw`\b(meeting|appointment|interview|dentist|doctor)s?\b|นัด|ประชุม|สัมภาษณ์`, "i");
  const TRAVEL_WORDS = rx(raw`\b(flight|hotel|trip|travel|holiday|vacation)s?\b|เที่ยวบิน|โรงแรม|เที่ยว|ทริป|จอง`, "i");

  // "buy milk and call mom": Python asks the AI to cut it in two (server.py could_be_several). Here: not sure.
  function couldBeSeveral(s) {
    const m = JOINER.exec(s);
    if (!m) return false;
    const big = (side) => side.split(/\s+/).filter(Boolean).length >= 2 || (THAI_LETTERS.test(side) && side.trim().length >= 4);
    return big(s.slice(0, m.index)) && big(s.slice(m.index + m[0].length));
  }

  const QUESTION_WORD_ANYWHERE = rx(raw`\b(what|how|which|should|when|where|who|why|anything)\b|อะไร|ไหม|มั้ย|กี่|ยังไง|ไร`);
  const TASK_LIST_WORDS = rx(raw`\b(tasks?|to-?dos?)\b`);
  const CANCEL_START = rx(raw`^(cancel|ยกเลิก)`);

  function addByRules(s, now, times, categories) {
    const sentence = cleanSentence(s);
    const lower = sentence.toLowerCase().split(NOWADAYS).join(" ");
    if (REPEAT_WORDS.test(lower) || PRIORITY_HINT.test(lower) || couldBeSeveral(s)) return null;
    // Looks like a question, or like a command we did not read ("show friday", "cancel task 3 to 5pm"): Python asks the AI. Not sure here.
    if (/\?\s*$/.test(s) || QUESTION_START.test(lower) || ORDER_START.test(lower) || QUESTION_WORD_ANYWHERE.test(lower) ||
        TASK_LIST_WORDS.test(lower) || CANCEL_START.test(lower)) return null;
    const rules = rulesDate(sentence, times);
    if (!rules) return null;
    // "dentist next week": Python offers Monday / Friday / no date. Not sure here.
    if (WEEK_AFTER.test(lower) && !weekdayIn(lower) && (EVENT_WORDS.test(lower) || TRAVEL_WORDS.test(lower))) return null;
    const due = resolveDue(rules, makeDay(now.y, now.m, now.d), times);
    const text = makeTitle(sentence, !!rules.time);
    // a day or time word still in the title means we did not understand it all
    if (!due || DAY_HINTS.test(text.toLowerCase()) || CLOCK_TIME.test(text) || DAY_PARTS.some(([re]) => re.test(text.toLowerCase()))) return null;
    return { action: "add", text, due, priority: "med", category: pickCategory(sentence, categories), repeat: "" };
  }

  // ---------- The one function script.js calls ----------
  // text: what the owner typed; todos: [{num, text, done, due, priority, cat}]; today: a Date or "YYYY-MM-DDTHH:MM"
  // times: optional About me times ({morning, afternoon, evening, tonight}); default 09:00 / 13:00 / 18:00 / 20:00
  function understand(text, todos, today, times) {
    try {
      const now = parseNow(today);
      if (!now || typeof text !== "string") return null;
      const s = oneSpace(text);
      if (!s || s.length > 500) return null;
      const tasks = (Array.isArray(todos) ? todos : []).filter((t) => t && Number.isInteger(t.num));
      const categories = Array.from(new Set(tasks.map((t) => String(t.cat || "")).filter(Boolean)));
      const clock = Object.assign({}, DEFAULT_TIMES, times || {});

      const [plain] = stripGreeting(s);
      if (TEAM.test(plain)) return null; // a message for the team: the server's job
      const filter = parseQuestion(s, now, categories);
      if (filter) {
        if (filter.unread) return null; // a day we cannot read (yesterday, a month...)
        delete filter.unread;
        return { action: "answer", filter, nums: listTasks(tasks, filter, now).map((t) => t.num) };
      }
      if (GREETING.test(s) && !s.replace(GREETING, "").trim()) return null; // just "hi max"
      const cmd = commandByRules(plain, tasks, now, clock);
      if (cmd.kind === "cmd") return cmd.cmd;
      if (cmd.kind === "unsure") return null;
      return addByRules(plain, now, clock, categories);
    } catch (err) {
      return null; // never break the page: not sure
    }
  }

  const api = { understand, rulesDate, resolveDue, fixDateTypos, thaiTime, englishTime, version: 1 };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.MaxOffline = api;
})(typeof window !== "undefined" ? window : typeof globalThis !== "undefined" ? globalThis : null);
