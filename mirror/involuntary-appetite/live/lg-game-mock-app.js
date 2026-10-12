(function () {
  "use strict";
  if (window.__lgMockAppCapsuleLoaded) return;
  window.__lgMockAppCapsuleLoaded = true;

  function paramValue(name, src) {
    var re = new RegExp("[?&#]" + name + "=([^&#]*)");
    var m = re.exec(src || "");
    if (!m) return null;
    try { return decodeURIComponent(m[1]); } catch (e) { return m[1]; }
  }

  var value =
    paramValue("isMockApp", window.location.search) ||
    paramValue("isMockApp", window.location.hash);
  if (value !== "1") return;

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    for (var key in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, key)) {
        node.setAttribute(key, attrs[key]);
      }
    }
    (children || []).forEach(function (child) {
      if (typeof child === "string") {
        node.appendChild(document.createTextNode(child));
      } else {
        node.appendChild(child);
      }
    });
    return node;
  }

  function svg(markup) {
    var wrap = document.createElement("div");
    wrap.innerHTML = markup;
    return wrap.firstChild;
  }

  var pill = el("div", {
    "aria-hidden": "true",
    style:
      "position:fixed;top:12px;right:8px;z-index:2147483000;" +
      "pointer-events:none;display:flex;align-items:center;" +
      "box-sizing:border-box;width:87px;height:32px;padding:0 16px;" +
      "background:#000;border-radius:999px;",
  });

  pill.appendChild(svg(
    '<svg width="14" height="3" viewBox="0 0 18 4" xmlns="http://www.w3.org/2000/svg">' +
      '<circle cx="2" cy="2" r="2" fill="#fff"/>' +
      '<circle cx="9" cy="2" r="2" fill="#fff"/>' +
      '<circle cx="16" cy="2" r="2" fill="#fff"/></svg>'
  ));

  pill.appendChild(el("div", {
    style: "width:1px;height:18px;background:rgba(255,255,255,0.1);margin:0 10px;",
  }));

  pill.appendChild(svg(
    '<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">' +
      '<path fill-rule="evenodd" d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zm0 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13z" fill="#fff"/>' +
      '<circle cx="8" cy="8" r="3.3" fill="#fff"/></svg>'
  ));

  document.body.appendChild(pill);
})();
