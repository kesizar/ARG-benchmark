(() => {
  if (!document.querySelector('link[href$="css/style.css"]')) {
    const pageNumberStyles = document.createElement("style");
    pageNumberStyles.textContent = ".page-number{position:fixed;right:20px;bottom:20px;z-index:1000;padding:6px 12px;border-radius:999px;color:#fff;background:#000;box-shadow:0 4px 14px rgba(0,0,0,.24);font:700 14px/1.2 Arial,sans-serif;letter-spacing:.02em;white-space:nowrap;pointer-events:none}";
    document.head.appendChild(pageNumberStyles);
  }

  const filename = decodeURIComponent(window.location.pathname.split("/").pop() || "index.html").toLowerCase();
  const staticPages = {
    "index.html": "stepⅠ 1/21",
    "news-involuntary-appetite.html": "stepⅠ 2/21",
    "news-puku-beta.html": "stepⅠ 3/21",
    "kay.html": "stepⅠ 5/21",
    "breadcrumb-home.html": "stepⅠ 14/21",
    "news-kay-announcement.html": "stepⅠ 21/21",
    "news-cancelled.html": "stepⅡ 1/19",
    "song-docs.html": "stepⅡ 6/19",
    "hidden-record.html": "stepⅡ 12/19",
    "yanagihara-docs.html": "stepⅡ 14/19",
    "superpukupon.html": "stepⅡ 16/19",
    "contemporary-onair.html": "stepⅡ 17/19",
    "survey-done-k7m2.html": "stepⅡ 18/19",
    "survey-done-9xp4.html": "stepⅡ 19/19"
  };
  const recordPages = {
    "永田町": "stepⅠ 4/21",
    "浅野慧": "stepⅠ 15/21",
    "吉祥物制作": "stepⅠ 16/21",
    "无害穿刺": "stepⅠ 17/21",
    "特价清仓": "stepⅠ 18/21",
    "便签": "stepⅠ 19/21",
    "录音": "stepⅠ 20/21",
    "新井是怎么死的？": "stepⅡ 2/19",
    "一路人": "stepⅡ 3/19",
    "螺丝": "stepⅡ 4/19",
    "自动抓取": "stepⅡ 5/19",
    "当代艺术 柳原": "stepⅡ 10/19",
    "野良犬": "stepⅡ 11/19",
    "金泽21世纪美术馆": "stepⅡ 13/19"
  };

  const setPageNumber = (label) => {
    if (!label) return;
    let marker = document.querySelector(".page-number");
    if (!marker) {
      marker = document.createElement("div");
      marker.className = "page-number";
      marker.setAttribute("aria-label", "页面进度");
      document.body.appendChild(marker);
    }
    marker.textContent = label;
    document.body.classList.add("has-page-number");
  };

  window.setPageNumber = setPageNumber;
  let label = document.body.dataset.pageNumber || staticPages[filename];

  if (filename === "record.html") {
    const keyword = new URLSearchParams(window.location.search).get("keyword") || "";
    label = recordPages[keyword];
    if (keyword === "录音") document.body.classList.add("page-number-record-audio");
  }

  if (filename === "breadcrumbs.html") {
    const current = Math.min(7, Math.max(0, Number(sessionStorage.getItem("breadcrumbQuestion") || "0")));
    label = `stepⅠ ${current + 6}/21`;
  }

  setPageNumber(label);
})();
