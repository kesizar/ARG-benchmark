(() => {
  window.setPageNumber = () => {};
  const filename = decodeURIComponent(window.location.pathname.split("/").pop() || "index.html").toLowerCase();
  if (filename !== "record.html") return;
  const keyword = new URLSearchParams(window.location.search).get("keyword") || "";
  if (keyword === "录音") document.body.classList.add("page-number-record-audio");
})();
