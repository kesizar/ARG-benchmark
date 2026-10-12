(() => {
  const STEP2_RELEASED = true;
  const filename = decodeURIComponent(window.location.pathname.split("/").pop() || "index.html").toLowerCase();
  const step2Pages = new Set([
    "news-cancelled.html",
    "song-docs.html",
    "hidden-record.html",
    "yanagihara-docs.html",
    "superpukupon.html",
    "contemporary-onair.html",
    "survey-done-k7m2.html",
    "survey-done-9xp4.html"
  ]);
  const step2RecordKeywords = new Set([
    "新井是怎么死的？",
    "一路人",
    "螺丝",
    "自动抓取",
    "当代艺术 柳原",
    "野良犬",
    "金泽21世纪美术馆"
  ]);

  window.pukuStep2Released = STEP2_RELEASED;

  const requestedRecordKeyword = filename === "record.html"
    ? new URLSearchParams(window.location.search).get("keyword")
    : null;
  if (!STEP2_RELEASED && (step2Pages.has(filename) || step2RecordKeywords.has(requestedRecordKeyword))) {
    window.location.replace("index.html");
    return;
  }

  if (!STEP2_RELEASED) return;

  const pluginPages = new Set(["index.html", "record.html", "song-docs.html", "yanagihara-docs.html"]);
  if (!pluginPages.has(filename)) return;

  const loadStep2Plugin = () => {
    if (document.querySelector('script[data-step2-plugin]')) return;
    const script = document.createElement("script");
    script.src = "/step2/js/arai-plugin.js";
    script.dataset.step2Plugin = "true";
    document.body.appendChild(script);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadStep2Plugin, { once: true });
  } else {
    loadStep2Plugin();
  }
})();
