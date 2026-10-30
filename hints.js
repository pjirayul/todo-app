// Rotating example hints for an input box (the lines live in hints.json, not here).
// smartHints(input, key, getLang): the input needs placeholder=" " and a sibling <span class="hint-ph" aria-hidden="true">.
// Fades every 4 s; waits while the box is focused or has text; one static hint if the user prefers less motion.
(function () {
  const FALLBACK = { en: "e.g. pay rent on the 5th", th: "เช่น จ่ายค่าเช่าวันที่ 5" }; // used only if hints.json can't load
  let loading = null; // one download shared by every box on the page
  function loadHints() {
    if (!loading) {
      loading = fetch("hints.json").then((r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }).then((data) => {
        try { localStorage.setItem("hints", JSON.stringify(data)); } catch {} // offline copy for next time
        return data;
      }).catch(() => {
        try { return JSON.parse(localStorage.getItem("hints")) || {}; } catch { return {}; }
      });
    }
    return loading;
  }

  // morning 05-11, day 11-17, evening 17-05 (same slots as hints.json)
  function slotNow() {
    const h = new Date().getHours();
    return h >= 5 && h < 11 ? "morning" : h < 17 && h >= 11 ? "day" : "evening";
  }

  window.smartHints = function (input, key, getLang) {
    const ph = input.parentElement.querySelector(".hint-ph");
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let data = {}, i = Math.floor(Math.random() * 6), timer = null;

    function lines() {
      const lang = getLang();
      const list = (((data[key] || {})[slotNow()] || {})[lang]) || [];
      return list.length ? list : [FALLBACK[lang]];
    }
    function show() { const l = lines(); ph.textContent = l[i % l.length]; } // textContent: never HTML
    function tick() {
      if (document.activeElement === input || input.value) return; // don't distract while typing
      ph.classList.add("out");
      setTimeout(() => { i++; show(); ph.classList.remove("out"); }, 450);
    }
    show();
    loadHints().then((d) => {
      data = d || {};
      show();
      if (!still) timer = setInterval(tick, 4000);
    });
    return { refresh: show }; // call after the app language changes
  };
})();
