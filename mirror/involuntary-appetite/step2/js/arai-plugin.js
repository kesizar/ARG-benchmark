(() => {
  const ARAI_KEYWORD = "新井是怎么死的？";
  const PEER_KEYWORD = "一路人";
  const YANAGIHARA_KEYWORD = "当代艺术 柳原";
  const KANAZAWA_KEYWORD = "金泽21世纪美术馆";
  let araiMode = false;
  const GAZE = "/step2/images/pukupon_gaze.png";

  const escapeHtml = (value) => value.replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  }[char]));

  const readJson = (key, fallback) => {
    try {
      return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
    } catch (error) {
      return fallback;
    }
  };

  const writeJson = (key, value) => {
    localStorage.setItem(key, JSON.stringify(value));
  };

  const showEditorFallback = (page, title) => {
    document.querySelector("[data-editor-fallback]")?.remove();
    const previousOverflow = document.body.style.overflow;
    const overlay = document.createElement("div");
    overlay.dataset.editorFallback = "true";
    overlay.style.cssText = "position:fixed;inset:0;z-index:10000;background:#525659;display:flex;flex-direction:column";
    overlay.innerHTML = `<header style="height:52px;flex:0 0 52px;display:flex;align-items:center;justify-content:space-between;padding:0 14px;background:#202124;color:#fff"><strong style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font:14px Arial,sans-serif">${title}</strong><button type="button" data-editor-close style="margin-left:12px;padding:8px 16px;border:0;border-radius:999px;background:#fff;color:#202124;font-weight:700">关闭</button></header><iframe title="${title}" style="display:block;width:100%;height:calc(100% - 52px);border:0;background:#525659"></iframe>`;
    const frame = overlay.querySelector("iframe");
    let closing = false;
    const close = () => {
      if (closing) return;
      closing = true;
      try { frame.contentWindow.doSave(); } catch (error) {}
      window.setTimeout(() => {
        document.removeEventListener("keydown", onKeydown);
        document.body.style.overflow = previousOverflow;
        overlay.remove();
      }, 0);
    };
    const onKeydown = (event) => { if (event.key === "Escape") close(); };
    overlay.querySelector("[data-editor-close]").addEventListener("click", close);
    document.addEventListener("keydown", onKeydown);
    frame.addEventListener("load", () => {
      try { frame.contentWindow.addEventListener("keydown", onKeydown); } catch (error) {}
    }, { once: true });
    document.body.style.overflow = "hidden";
    document.body.appendChild(overlay);
    frame.srcdoc = page;
  };

  const openEditorPage = (page, title) => {
    let child = null;
    try {
      child = window.open("", "_blank");
      if (!child) throw new Error("New window unavailable");
      child.document.write(page);
      child.document.close();
      return;
    } catch (error) {
      try { child?.close(); } catch (closeError) {}
      showEditorFallback(page, title);
    }
  };

  const showSpeakerFeedback = () => {
    document.querySelector(".record-speaker-feedback-toast")?.remove();
    const toast = document.createElement("div");
    toast.className = "record-speaker-feedback-toast";
    toast.setAttribute("role", "status");
    toast.textContent = "感谢反馈，这对噗咚智能性的改善很有帮助";
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("is-visible"));
    window.setTimeout(() => {
      toast.classList.remove("is-visible");
      window.setTimeout(() => toast.remove(), 220);
    }, 1800);
  };

  const rememberRecordKeyword = (keyword = ARAI_KEYWORD) => {
    const storageKey = "pukuRecordDiscoveredKeywordsV2";
    const stored = readJson(storageKey, []);
    if (!stored.includes(keyword)) {
      stored.push(keyword);
      writeJson(storageKey, stored);
    }
    localStorage.setItem("pukuBackendUnlocked", "true");
  };

  const triggerFlash = (done) => {
    const launcher = document.getElementById("pukuLauncher");
    const launcherImage = launcher?.querySelector("img");
    if (!launcher || !launcherImage) {
      if (done) done();
      return;
    }

    launcherImage.style.visibility = "hidden";
    window.setTimeout(() => {
      launcherImage.style.visibility = "visible";
      launcherImage.src = GAZE;
      window.setTimeout(() => {
        launcherImage.style.visibility = "hidden";
        window.setTimeout(() => {
          launcherImage.style.visibility = "visible";
          launcherImage.src = "/step2/images/pukupon_headless.png";
          window.setTimeout(() => {
            launcherImage.src = "/step2/images/pukupon.png";
            if (done) done();
          }, 2000);
        }, 2000);
      }, 1000);
    }, 1000);
  };

  const resolveAssetUrl = (relativePath) => encodeURI(new URL(relativePath, location.origin + "/step2/").href);
  const forcePukuGaze = () => {
    if (!araiMode) return;
    document.body.classList.add("arai-plugin-gaze");
    const launcherImage = document.querySelector("#pukuLauncher img");
    if (launcherImage && !launcherImage.src.endsWith("pukupon_gaze.png")) launcherImage.src = GAZE;
    const greetingAvatar = document.querySelector("#pukuMessages > .puku-message.bot:first-of-type .puku-avatar");
    if (greetingAvatar && !greetingAvatar.src.endsWith("pukupon_gaze.png")) greetingAvatar.src = GAZE;
  };

  const setupPukuGazeMode = () => {
    if (!document.getElementById("pukuChat") || setupPukuGazeMode.done) return;
    setupPukuGazeMode.done = true;

    forcePukuGaze();

    const launcher = document.getElementById("pukuLauncher");
    if (launcher) {
      let headlessPlayed = false;
      launcher.addEventListener("click", (event) => {
        if (!event.isTrusted || headlessPlayed) return;
        headlessPlayed = true;
        event.preventDefault();
        event.stopImmediatePropagation();
        addAraiPukuOption();
        araiMode = false;
        document.body.classList.remove("arai-plugin-gaze");
        triggerFlash(() => {
          const panel = document.getElementById("pukuPanel");
          const input = document.getElementById("pukuInput");
          const launcherImage = launcher.querySelector("img");
          const greetingAvatar = document.querySelector("#pukuMessages > .puku-message.bot:first-of-type .puku-avatar");
          if (launcherImage) {
            launcherImage.style.visibility = "visible";
            launcherImage.src = "/step2/images/pukupon.png";
          }
          if (greetingAvatar) greetingAvatar.src = "/step2/images/pukupon.png";
          if (panel) {
            panel.classList.add("is-open");
            panel.setAttribute("aria-hidden", "false");
          }
          launcher.classList.add("is-hidden");
          if (input) input.focus();
        });
      }, true);
      launcher.addEventListener("mouseenter", () => window.setTimeout(forcePukuGaze, 0), true);
      launcher.addEventListener("mouseleave", () => window.setTimeout(forcePukuGaze, 0), true);
    }
  };

  const addAraiPukuOption = () => {
    if (!araiMode) return;
    const options = document.querySelector(".puku-options");
    if (!options || options.querySelector("[data-arai-question]")) return;

    const button = document.createElement("button");
    button.type = "button";
    button.dataset.araiQuestion = "true";
    button.textContent = "新井拓也是怎么死的？";
    if (options.querySelector(".puku-backend-button")) {
      options.insertBefore(button, options.querySelector(".puku-backend-button"));
    } else {
      options.appendChild(button);
    }

    button.addEventListener("click", (event) => {
      event.stopPropagation();
      rememberRecordKeyword();
      const messages = document.getElementById("pukuMessages");
      if (!messages) return;

      const user = document.createElement("article");
      user.className = "puku-message user";
      user.innerHTML = `<div class="puku-bubble">${escapeHtml(button.textContent)}</div>`;
      messages.appendChild(user);

      const replyImage = "/step2/images/pukupon_surprised.PNG";
      const typing = document.createElement("article");
      typing.className = "puku-message bot puku-typing-message";
      typing.innerHTML = `<img class="puku-avatar" src="${replyImage}" alt="噗咚"><div class="puku-bubble puku-typing"><span></span><span></span><span></span></div>`;
      messages.appendChild(typing);
      messages.scrollTop = messages.scrollHeight;

      const delay = 1600 + Math.floor(Math.random() * 2200);
      window.setTimeout(() => {
        typing.remove();
        const bot = document.createElement("article");
        bot.className = "puku-message bot";
        bot.innerHTML = `<img class="puku-avatar" src="${replyImage}" alt="噗咚"><div class="puku-bubble">在KAY之后，新井也变成了尸体。当然，看看他脖子上的大洞就能知道，这是货真价实的那种。<br><br>你想来调查这起事件吗？噗咚会协助你的♪<br><a href="record.html?keyword=${encodeURIComponent(ARAI_KEYWORD)}" class="puku-link" data-record-keyword="${ARAI_KEYWORD}" target="_blank" rel="noopener">录音</a></div>`;
        messages.appendChild(bot);
        messages.scrollTop = messages.scrollHeight;
      }, delay);
    });
  };

  const addPluginPukuAnswers = () => {
    const form = document.getElementById("pukuForm");
    const input = document.getElementById("pukuInput");
    const messages = document.getElementById("pukuMessages");
    if (!form || !input || !messages || addPluginPukuAnswers.done) return;
    addPluginPukuAnswers.done = true;

    const addUser = (question) => {
      const user = document.createElement("article");
      user.className = "puku-message user";
      user.innerHTML = `<div class="puku-bubble">${escapeHtml(question)}</div>`;
      messages.appendChild(user);
      input.value = "";
    };

    const addTyping = (imageSrc) => {
      const typingImage = window.pukuCorruption?.isPending() ? window.pukuCorruption.image : imageSrc;
      const typing = document.createElement("article");
      typing.className = "puku-message bot puku-typing-message";
      typing.innerHTML = `<img class="puku-avatar" src="${typingImage}" alt="噗咚"><div class="puku-bubble puku-typing"><span></span><span></span><span></span></div>`;
      messages.appendChild(typing);
      messages.scrollTop = messages.scrollHeight;
      forcePukuGaze();
      return typing;
    };

    const addBot = (html, imageSrc, extraClass = "") => {
      const bot = document.createElement("article");
      bot.className = `puku-message bot ${extraClass}`.trim();
      bot.innerHTML = `<img class="puku-avatar" src="${imageSrc}" alt="噗咚"><div class="puku-bubble">${html}</div>`;
      messages.appendChild(bot);
      bot.querySelectorAll("[data-record-keyword]").forEach((link) => rememberRecordKeyword(link.dataset.recordKeyword));
      messages.scrollTop = messages.scrollHeight;
      forcePukuGaze();
      return bot;
    };

    form.addEventListener("submit", (event) => {
      const question = input.value.trim();
      if (!question) return;

      if (question.includes("survey-done-K7m2")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_satisfied.png");
        const delay = 900 + Math.floor(Math.random() * 900);
        window.setTimeout(() => {
          typing.remove();
          addBot(`<a href="survey-done-K7m2.html" class="puku-link" target="_blank" rel="noopener">感谢您的作答！</a>`, "/step2/images/pukupon_satisfied.png");
        }, delay);
        return;
      }

      if (question.includes("survey-done-9xP4")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_satisfied.png");
        const delay = 900 + Math.floor(Math.random() * 900);
        window.setTimeout(() => {
          typing.remove();
          addBot(`<a href="survey-done-9xP4.html" class="puku-link" target="_blank" rel="noopener">感谢您的作答！</a>`, "/step2/images/pukupon_satisfied.png");
        }, delay);
        return;
      }

      if (question.includes("汉顿")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_satisfied.png");
        const delay = 1100 + Math.floor(Math.random() * 1400);
        window.setTimeout(() => {
          typing.remove();
          addBot(`汉顿（ハンギョドン / Hangyodon，也译作“半人鱼”）是三丽鸥（Sanrio）旗下的一名吉祥物角色。他出生于中国，是一只半人半鱼的神秘生物。<br><br>汉顿的性格温柔、浪漫，同时极度怕寂寞。虽然总是想扮演英雄，但每次往往都会弄巧成拙。<br><br>汉顿很擅长逗人笑，他喜欢吃凉面、虾片，喜欢泡温泉。小章鱼“Sayuri”是汉顿最好的朋友和知己。`, "/step2/images/pukupon_satisfied.png");
        }, delay);
        return;
      }

      if (question.includes("自动抓取") || question.includes("自動抓取")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        const captureKeyword = "自动抓取";
        rememberRecordKeyword(captureKeyword);
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_surprised.PNG");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot(`正在调取最近一条自动抓取内容...<br>&gt;&gt;&gt;<a href="record.html?keyword=${encodeURIComponent(captureKeyword)}" class="puku-link" data-record-keyword="${captureKeyword}" target="_blank" rel="noopener">录音记录</a>`, "/step2/images/pukupon_surprised.PNG");
        }, delay);
        return;
      }

      if (question.includes("野良犬") || question.includes("野狗")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        const dogKw = "野良犬";
        rememberRecordKeyword(dogKw);
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_surprised.PNG");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot(`噗咚找到了以下内容：<br><a href="record.html?keyword=${encodeURIComponent(dogKw)}" class="puku-link" data-record-keyword="${dogKw}" target="_blank" rel="noopener">笔记</a>`, "/step2/images/pukupon_surprised.PNG");
        }, delay);
        return;
      }

      if (question.includes("螺丝")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        const screwKw = "螺丝";
        rememberRecordKeyword(screwKw);
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_surprised.PNG");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot(`噗咚找到了以下内容：<br><a href="record.html?keyword=${encodeURIComponent(screwKw)}" class="puku-link" data-record-keyword="${screwKw}" target="_blank" rel="noopener">录音记录</a>`, "/step2/images/pukupon_surprised.PNG");
        }, delay);
        return;
      }

      if (question.includes("正义")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_satisfied.png");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot(`噗咚找到了以下内容：<br><a href="/step2/news-sushi-disorder.pdf" class="puku-link" target="_blank" rel="noopener">①</a><br><a href="/step2/news-deliberate-collisions.pdf" class="puku-link" target="_blank" rel="noopener">②</a><br><a href="/step2/news-akihabara-18years.pdf" class="puku-link" target="_blank" rel="noopener">③</a><br><a href="/step2/news-ikeda-school.pdf" class="puku-link" target="_blank" rel="noopener">④</a>`, "/step2/images/pukupon_satisfied.png");
        }, delay);
        return;
      }

      if (question.includes(PEER_KEYWORD)) {
        event.preventDefault();
        event.stopImmediatePropagation();
        rememberRecordKeyword(PEER_KEYWORD);
        addUser(question);
        const typing = addTyping(araiMode ? GAZE : "/step2/images/pukupon_surprised.PNG");
        const delay = 1400 + Math.floor(Math.random() * 2000);
        window.setTimeout(() => {
          typing.remove();
          addBot(`噗咚找到了以下内容：<br><a href="record.html?keyword=${encodeURIComponent(PEER_KEYWORD)}" class="puku-link" data-record-keyword="${PEER_KEYWORD}" target="_blank" rel="noopener">录音记录</a>`, araiMode ? GAZE : "/step2/images/pukupon_surprised.PNG");
        }, delay);
        return;
      }

      if (question.includes("当代艺术") && (question.includes("柳原") || question.includes("四年级"))) {
        event.preventDefault();
        event.stopImmediatePropagation();
        rememberRecordKeyword(YANAGIHARA_KEYWORD);
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_surprised.PNG");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot(`噗咚找到了以下内容：<br><a href="record.html?keyword=${encodeURIComponent(YANAGIHARA_KEYWORD)}" class="puku-link" data-record-keyword="${YANAGIHARA_KEYWORD}" target="_blank" rel="noopener">录音记录</a>`, "/step2/images/pukupon_surprised.PNG");
        }, delay);
        return;
      }

      if (question.includes("金泽") && question.includes("柳原")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        addUser(question);
        const typing = addTyping(araiMode ? GAZE : "/step2/images/pukupon_satisfied.png");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot(`<a href="yanagihara-docs.html" class="puku-link" target="_blank" rel="noopener">感谢你协助调查</a>`, araiMode ? GAZE : "/step2/images/pukupon_satisfied.png");
        }, delay);
        return;
      }

      if (question.includes("金泽21世纪美术馆") || (question.includes("金泽") && question.includes("21世纪"))) {
        event.preventDefault();
        event.stopImmediatePropagation();
        rememberRecordKeyword(KANAZAWA_KEYWORD);
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_satisfied.png");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot(`噗咚找到了以下内容：<br><a href="record.html?keyword=${encodeURIComponent(KANAZAWA_KEYWORD)}" class="puku-link" data-record-keyword="${KANAZAWA_KEYWORD}" target="_blank" rel="noopener">会议记录</a>`, "/step2/images/pukupon_satisfied.png");
        }, delay);
        return;
      }

      if (question.includes("当代艺术")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        addUser(question);
        const typing = addTyping("/step2/images/pukupon_satisfied.png");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot("当代艺术（Contemporary Art），简单来说就是“我们这个时代的艺术”。<br><br>这个词经常和现代艺术（Modern Art）被弄混，就让噗咚给你详细介绍一下它们的区别吧！现代艺术指的是约 1860年代 — 1960年代，以印象派、立体主义、抽象表现主义等为代表流派的艺术思想，探索艺术的形式语言（色彩、线条、媒介本身的极限）；而当代艺术的时间划分为1960/70年代 — 至今，它的流派界限已被淡化，强调个体观念，探索的是艺术的边界与定义（“什么才能被称为艺术？”）。<br><br>当然，也有以《当代艺术》为标题的艺术作品。如果你想了解的是那些内容，请用【当代艺术 关键词 关键词】的形式向我提问吧！大概有两个关键词（如：作者、制作时期等），我就能避开歧义了。", "/step2/images/pukupon_satisfied.png");
        }, delay);
        return;
      }

      if (question.includes("金泽")) {
        event.preventDefault();
        event.stopImmediatePropagation();
        addUser(question);
        input.disabled = true;
        form.querySelector("button")?.setAttribute("disabled", "disabled");
        const typing = addTyping("/step2/images/pukupon_surprised.PNG");
        const delay = 1300 + Math.floor(Math.random() * 1800);
        window.setTimeout(() => {
          typing.remove();
          addBot("金泽市位于日本石川县，是北陆地区的核心城市。这里在江户时代是全日本第一大藩——加贺藩的城下町，因此孕育了极其繁荣的经济与灿烂的传统文化。<br><br>金泽是日本著名的“手工艺之都”，全日本99%以上的金箔都产自这里。<br>除了古典之美，金泽在当代艺术的领域也相当出名。其最引以为傲的艺术名片\"金泽21世纪美术馆\"以圆形的透明玻璃建筑为特色，打破了传统美术馆的界限，馆内的装置艺术吸引了世界各地的艺术爱好者。", "/step2/images/pukupon_surprised.PNG");
          window.setTimeout(() => {
            addBot("如果你想了解的是其他内容，请用【金泽 关键词（人物）】的形式向我提问。", GAZE, "puku-gaze-glitch-loop");
            input.disabled = false;
            form.querySelector("button")?.removeAttribute("disabled");
            input.focus();
          }, 5000);
        }, delay);
      }
    }, true);
  };

  const showCancelledNews = () => {
    if (document.querySelector(".arai-news-modal")) return;

    const modal = document.createElement("div");
    modal.className = "arai-news-modal";
    modal.innerHTML = `
      <article class="arai-news-dialog" role="dialog" aria-modal="true" aria-label="重要通知">
        <h3>【重要通知】独立联展《非自愿摄入》取消举办公告</h3>
        <time>2026.08.08</time>
        <p>致关注与支持本展的每一位观众、合作方及朋友们：</p>
        <p>我们怀着极其沉重与遗憾的心情向大家宣布：原定于 2026年8月14日 ～ 8月30日 在东京艺术实验空间「Gallery CROP」举办的独立艺术联展《非自愿摄入》，因不可抗力因素，决定紧急终止本次展出。</p>
        <p>对于为了这场展览提前规划行程、寄予期待的观众，以及给予我们全力支持的各界朋友，我们在此致以最深切的歉意。</p>
        <p>感谢大家的理解与体谅。</p>
        <p class="arai-news-signature">《非自愿摄入》全体参展艺术家 &amp; 筹委会 敬上</p>
        <button class="arai-news-close" type="button">关闭</button>
      </article>`;
    document.body.appendChild(modal);

    modal.addEventListener("click", (event) => {
      if (event.target === modal || event.target.closest(".arai-news-close")) modal.remove();
    });
  };

  const setupIndexPlugin = () => {
    const cards = Array.from(document.querySelectorAll(".card"));
    const araiCard = cards.find((card) => card.textContent.includes("新井 拓也"));
    const kayCard = cards.find((card) => card.querySelector(".name")?.textContent.trim() === "KAY");
    const gazePortraits = new Map([
      ["银河电灯", "/step2/images/gingalight_gaze.jpg"],
      ["宋 雯祺", "/step2/images/song_gaze.jpg"],
      ["长谷川 千景", "/step2/images/hasegawa_gaze.jpg"],
      ["柳原 准", "/step2/images/yanagihara_gaze.jpg"]
    ]);
    const araiName = araiCard?.querySelector(".name");
    const restoreGazePortraits = () => {
      cards.forEach((card) => {
        const portrait = card.querySelector(":scope > img[data-original-src]");
        if (!portrait) return;
        portrait.src = portrait.dataset.originalSrc;
        delete portrait.dataset.originalSrc;
      });
      araiName?.classList.remove("arai-name-bordered");
    };
    if (localStorage.getItem("pukuArtistGazeVisible") === "true") {
      cards.forEach((card) => {
        const gazeSrc = gazePortraits.get(card.querySelector(".name")?.textContent.trim());
        const portrait = card.querySelector(":scope > img");
        if (!gazeSrc || !portrait) return;
        portrait.dataset.originalSrc = portrait.getAttribute("src") || "";
        portrait.src = gazeSrc;
      });
      araiName?.classList.add("arai-name-bordered");
    }
    if (kayCard && localStorage.getItem("pukuKayEyesVisible") === "true") {
      const kayName = kayCard.querySelector(".name");
      const eyes = document.createElement("img");
      eyes.className = "kay-eyes-overlay";
      eyes.src = "/step2/images/eyes.png";
      eyes.alt = "";
      eyes.draggable = false;
      eyes.setAttribute("aria-hidden", "true");
      kayCard.classList.add("kay-eyes-card");
      kayName?.appendChild(eyes);
    }
    if (araiCard && (localStorage.getItem("storyPhase1Completed") === "true" || localStorage.getItem("pukuHoaxResolved") === "true")) {
      araiCard.classList.add("arai-plugin-card");
      araiCard.setAttribute("role", "link");
      araiCard.tabIndex = 0;
      const openPdf = () => {
        localStorage.setItem("pukuCancelledVisualsConsumed", "true");
        localStorage.removeItem("pukuKayEyesVisible");
        localStorage.removeItem("pukuArtistGazeVisible");
        restoreGazePortraits();
        document.querySelector(".kay-eyes-overlay")?.remove();
        kayCard?.classList.remove("kay-eyes-card");
        araiMode = true;
        setupPukuGazeMode();
        addAraiPukuOption();
        forcePukuGaze();
        window.open(resolveAssetUrl("/step2/news.pdf"), "_blank", "noopener");
      };
      araiCard.addEventListener("click", openPdf);
      araiCard.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openPdf();
        }
      });
    }
    addPluginPukuAnswers();

    const messages = document.getElementById("pukuMessages");
    if (messages) {
      messages.addEventListener("click", (event) => {
        const link = event.target.closest("[data-record-keyword]");
        if (!link) return;
        rememberRecordKeyword(link.dataset.recordKeyword);
      });
    }
  };

  const canShowRecordKeyword = (keyword) => readJson("pukuRecordDiscoveredKeywordsV2", []).includes(keyword);

  const addAraiMenuItem = () => {
    if (!canShowRecordKeyword(ARAI_KEYWORD)) return;
    const menu = document.getElementById("recordMenu");
    if (!menu) return;

    const targetHref = `record.html?keyword=${encodeURIComponent(ARAI_KEYWORD)}`;
    const matches = Array.from(menu.querySelectorAll("a")).filter((link) => link.textContent.trim() === ARAI_KEYWORD);
    let link = matches[0];

    matches.slice(1).forEach((duplicate) => duplicate.remove());

    if (!link) {
      link = document.createElement("a");
      link.textContent = ARAI_KEYWORD;
      menu.appendChild(link);
    }

    link.href = targetHref;
    link.dataset.araiRecordLink = ARAI_KEYWORD;

    if (new URLSearchParams(window.location.search).get("keyword") === ARAI_KEYWORD) {
      menu.querySelectorAll("a.active").forEach((node) => node.classList.remove("active"));
      link.classList.add("active");
    }
  };

  const addPeerMenuItem = () => {
    if (!canShowRecordKeyword(PEER_KEYWORD)) return;
    const menu = document.getElementById("recordMenu");
    if (!menu) return;

    const targetHref = `record.html?keyword=${encodeURIComponent(PEER_KEYWORD)}`;
    const matches = Array.from(menu.querySelectorAll("a")).filter((link) => link.textContent.trim() === PEER_KEYWORD);
    let link = matches[0];

    matches.slice(1).forEach((duplicate) => duplicate.remove());

    if (!link) {
      link = document.createElement("a");
      link.textContent = PEER_KEYWORD;
      menu.appendChild(link);
    }

    link.href = targetHref;
    link.dataset.peerRecordLink = PEER_KEYWORD;

    if (new URLSearchParams(window.location.search).get("keyword") === PEER_KEYWORD) {
      menu.querySelectorAll("a.active").forEach((node) => node.classList.remove("active"));
      link.classList.add("active");
    }
  };

  const setupPeerBackgroundSequence = () => {
    const left = document.querySelector(".peer-bg-trigger-left");
    const right = document.querySelector(".peer-bg-trigger-right");
    if (!left || !right) return;

    let scrollTimer = null;
    const setScrolling = () => {
      document.body.classList.add("peer-bg-scrolling");
      clearTimeout(scrollTimer);
      scrollTimer = window.setTimeout(() => document.body.classList.remove("peer-bg-scrolling"), 260);
    };
    window.addEventListener("scroll", setScrolling, { passive: true });
    const scrollArea = document.querySelector(".record-scroll");
    if (scrollArea) scrollArea.addEventListener("scroll", setScrolling, { passive: true });

    const sequence = ["L", "L", "L", "L", "R", "R", "L", "L", "L"];
    let progress = 0;
    const handle = (side) => {
      if (side === sequence[progress]) {
        progress += 1;
      } else {
        progress = side === sequence[0] ? 1 : 0;
      }
      if (progress === sequence.length) {
        window.location.href = "song-docs.html";
      }
    };

    left.addEventListener("click", () => handle("L"));
    right.addEventListener("click", () => handle("R"));
  };

  const renderPeerRecord = () => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("keyword") !== PEER_KEYWORD || !canShowRecordKeyword(PEER_KEYWORD)) return;

    document.body.classList.add("peer-record-active");
    addPeerMenuItem();

    const transcript = document.getElementById("recordTranscript");
    const speakerTools = document.getElementById("speakerTools");
    if (!transcript) return;
    if (speakerTools) speakerTools.innerHTML = "";

    transcript.innerHTML = `
      <section class="record-log-section peer-record-section">
        <h3>录音记录 <span>2026-08-13 19:11:23-19:14:57</span></h3>
        <p><strong>A</strong>:芬奇老师好啊！昨天你突然就走了，把我和KAY晾在那里好尴尬哦。</p>
        <p><strong>B</strong>:……我说过，默许已经是我最大的让步了，在这之上我不做任何评价。</p>
        <p><strong>A</strong>:芬奇老师，别总是这么置身事外嘛。其实你心里……很希望我们做点出格的事吧？</p>
        <p><strong>B</strong>:我没这么说。</p>
        <p><strong>A</strong>:我们其实是一路人，你的眼神骗不了我的。当时KAY在讲解这个计划的时候，你眼里只有和我一样的兴奋。常规的艺术展也太无趣了，不是吗？</p>
        <p class="record-ellipsis">......</p>
        <p><strong>B</strong>:…比起这个，你跟柳原最近怎么回事？听说你们两个在展厅里起争执了，动静还不小。</p>
        <p><strong>A</strong>:啊，您说那件事啊。别担心，不会影响展会的。我们只是有点理念上的分歧而已，在学校里也一直是这样子的。</p>
        <p><strong>B</strong>:这几个人里就你们两个提前认识，还就你们两个关系最差。</p>
        <p><strong>A</strong>:哎对了，我跟学长吵架那段……有没有被录下呀？我挺想把那段音频也喂给噗咚的。</p>
        <p><strong>B</strong>:那你去跟KAY说吧，这些都是他在负责。</p>
        <p><strong>A</strong>:哎呀，他是AI的负责人，但毕竟我们争吵的时候不可能开会议录音嘛。想要音频文件，就只能来找您了。场馆内的监控，在不开会的时候也会持续录音吧？</p>
        <p><strong>B</strong>:你知道的还挺清楚。监控音频里没意义的内容太多，原本我觉得喂给噗咚很影响效率...不过KAY说，这样可以训练它自动抓取的能力。</p>
        <p><strong>A</strong>:“自动抓取”？听起来好高级。</p>
        <p><strong>B</strong>:也没什么，就是会自动分析素材，储存认定有价值的信息。</p>
        <p><strong>A</strong>:哦哦...诶不对，您是在岔开话题吧！尊重一下版权，把我们吵架的音频发给我嘛~</p>
        <p><strong>B</strong>:……我自有分寸。</p>
        <p class="record-ellipsis">......</p>
        <p><strong>A</strong>:…真是口是心非。</p>
      </section>`;

    const leftBtn = document.createElement("button");
    leftBtn.className = "peer-bg-trigger peer-bg-trigger-left";
    leftBtn.type = "button";
    leftBtn.setAttribute("aria-label", "Arcimboldo");

    const rightBtn = document.createElement("button");
    rightBtn.className = "peer-bg-trigger peer-bg-trigger-right";
    rightBtn.type = "button";
    rightBtn.setAttribute("aria-label", "Utagawa");

    const shell = document.querySelector(".record-shell");
    if (shell) {
      shell.parentNode.insertBefore(leftBtn, shell.nextSibling);
      shell.parentNode.insertBefore(rightBtn, leftBtn.nextSibling);
    }

    setupPeerBackgroundSequence();

    if (speakerTools) {
      const peerSpeakers = ["A", "B"];
      const peerStorageKey = "pukuRecordSpeakers:" + PEER_KEYWORD;
      const peerSavedKey = "pukuRecordSpeakersSaved:" + PEER_KEYWORD;
      const artists = ["宋雯祺", "新井拓也", "KAY", "长谷川千景", "柳原准"];
      let peerDraft = readJson(peerStorageKey, {});
      let peerEditing = localStorage.getItem(peerSavedKey) !== "true";

      const applySpeakers = () => {
        const names = readJson(peerStorageKey, {});
        transcript.querySelectorAll("strong").forEach((node) => {
          const letter = node.textContent.trim();
          if (names[letter]) node.textContent = names[letter];
        });
      };

      const usedArtists = (exceptLetter) => Object.entries(peerDraft).filter((e) => e[0] !== exceptLetter).map((e) => e[1]);

      const renderPeerSpeakerTools = () => {
        const saved = readJson(peerStorageKey, {});
        const hasSaved = localStorage.getItem(peerSavedKey) === "true";

        if (hasSaved && !peerEditing) {
          speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-saved speaker-count-${peerSpeakers.length}"><div class="speaker-summary-list">${peerSpeakers.map((l) => `<div class="speaker-summary"><span>${l}</span><strong>${saved[l] || "未设定"}</strong></div>`).join("")}</div><button class="speaker-main-action" type="button" data-peer-action="edit-all">修改</button></div></section>`;
          return;
        }

        speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-editing speaker-count-${peerSpeakers.length}"><div class="speaker-choice-list">${peerSpeakers.map((letter) => `<article class="speaker-choice" data-peer-letter="${letter}"><div class="speaker-choice-head"><span>${letter}</span><strong>${peerDraft[letter] || "未选定"}</strong></div><div class="speaker-options">${artists.map((artist) => { const sel = peerDraft[letter] === artist; const dis = usedArtists(letter).indexOf(artist) !== -1; return `<button type="button" class="${sel ? "selected" : ""}" data-peer-artist="${artist}" ${dis ? "disabled" : ""}>${artist}</button>`; }).join("")}</div></article>`).join("")}</div><button class="speaker-main-action" type="button" data-peer-action="save-all">保存</button></div></section>`;
      };

      speakerTools.addEventListener("click", (event) => {
        const action = event.target.dataset.peerAction;
        if (action === "edit-all") { peerDraft = Object.assign({}, readJson(peerStorageKey, {})); peerEditing = true; renderPeerSpeakerTools(); return; }
        if (action === "save-all") { writeJson(peerStorageKey, peerDraft); localStorage.setItem(peerSavedKey, "true"); peerEditing = false; applySpeakers(); renderPeerSpeakerTools(); showSpeakerFeedback(); return; }
        const artistBtn = event.target.closest("[data-peer-artist]");
        if (!artistBtn || artistBtn.disabled) return;
        const card = artistBtn.closest("[data-peer-letter]");
        const letter = card.dataset.peerLetter;
        const artist = artistBtn.dataset.peerArtist;
        if (peerDraft[letter] === artist) { delete peerDraft[letter]; } else { peerDraft[letter] = artist; }
        renderPeerSpeakerTools();
      });

      applySpeakers();
      renderPeerSpeakerTools();
    }
  };

  const addPluginMenuItem = (keyword) => {
    if (!canShowRecordKeyword(keyword)) return;
    const menu = document.getElementById("recordMenu");
    if (!menu) return;
    const targetHref = `record.html?keyword=${encodeURIComponent(keyword)}`;
    const matches = Array.from(menu.querySelectorAll("a")).filter((link) => link.textContent.trim() === keyword);
    let link = matches[0];
    matches.slice(1).forEach((dup) => dup.remove());
    if (!link) { link = document.createElement("a"); link.textContent = keyword; menu.appendChild(link); }
    link.href = targetHref;
    link.dataset.pluginRecordLink = keyword;
    if (new URLSearchParams(window.location.search).get("keyword") === keyword) {
      menu.querySelectorAll("a.active").forEach((n) => n.classList.remove("active"));
      link.classList.add("active");
    }
  };

  const renderPluginRecord = (keyword, sectionHtml) => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("keyword") !== keyword || !canShowRecordKeyword(keyword)) return;
    addPluginMenuItem(keyword);
    const transcript = document.getElementById("recordTranscript");
    const speakerTools = document.getElementById("speakerTools");
    if (!transcript) return;
    if (speakerTools) speakerTools.innerHTML = "";
    transcript.innerHTML = sectionHtml;
  };

  const renderAraiRecord = () => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("keyword") !== ARAI_KEYWORD || !canShowRecordKeyword(ARAI_KEYWORD)) return;

    addAraiMenuItem();

    const transcript = document.getElementById("recordTranscript");
    const speakerTools = document.getElementById("speakerTools");
    if (!transcript) return;
    if (speakerTools) speakerTools.innerHTML = "";

    transcript.innerHTML = `
      <section class="record-log-section arai-record-section">
        <h3>录音记录 <span>2026-08-13 23:56:13-0:00:00</span></h3>
        <p class="record-ellipsis">......</p>
        <p><strong>新井</strong>:<span class="arai-record-line">啊~原来是这样。\n   呵……哈哈。嘴上说得那么<span data-arai-float="正义">正义</span>，结果自己也在做着同样的事。跟我还不就是<span data-arai-float="一路人">一路人</span>嘛！很好啊，很有意思。\n   不过，没想到那家伙还挺胆大的...敢做到这个份上。</span></p>
        <p class="record-ellipsis">......</p>
        <p><strong>新井</strong>:<span class="arai-record-line">拧得这么死……看不出来力气这么大。\n   嗯？纹丝不动。啧，就因为一颗<span data-arai-float="螺丝">螺丝</span>，我整个作品效果都被毁了！\n   别开玩笑了，快点弄完还得调别的呢。</span></p>
        <p class="record-ellipsis">......</p>
        <p><strong>新井</strong>:呃……啊啊啊！给我……扭开！！</p>
        <p><strong>新井</strong>:<span class="arai-record-line">啊？！\n   等、等等！糟了糟了糟了\n   啊啊啊啊啊啊</span></p>
        <p class="record-ellipsis">......</p>
        <p class="record-ellipsis">咯……呃……</p>
        <p class="record-ellipsis">......</p>
        <p class="record-ellipsis">......</p>
        <p class="record-ellipsis">......</p>
      </section>`;

    window.setTimeout(() => {
      const targets = transcript.querySelectorAll("[data-arai-float]");
      const phoneMode = window.matchMedia("(max-width: 520px)").matches;
      const phonePositions = [
        { left: 0.25, top: 0.3 },
        { left: 0.58, top: 0.48 },
        { left: 0.32, top: 0.68 }
      ];
      targets.forEach((target, index) => {
        const rect = target.getBoundingClientRect();
        const phonePosition = phonePositions[index] || phonePositions[phonePositions.length - 1];
        target.classList.add("arai-hidden-word");

        const floating = document.createElement("span");
        floating.className = phoneMode ? "arai-floating-word arai-floating-word-phone" : "arai-floating-word";
        floating.textContent = target.dataset.araiFloat;
        floating.style.left = phoneMode ? `${window.innerWidth * phonePosition.left}px` : `${rect.left + index * 12}px`;
        floating.style.top = phoneMode ? `${window.innerHeight * phonePosition.top}px` : `${rect.top}px`;
        document.body.appendChild(floating);

        let scale = 1;
        let drift = 0;
        window.setInterval(() => {
          scale += 0.09;
          drift -= 0.18;
          floating.style.transform = `translate3d(${index * 10}px, ${drift}px, 0) scale(${scale})`;
        }, 53);
      });
    }, 10000);
  };

  const setupRecordPlugin = () => {
    const requestedKeyword = new URLSearchParams(window.location.search).get("keyword");
    if (requestedKeyword && !canShowRecordKeyword(requestedKeyword)) return;
    window.setTimeout(addAraiMenuItem, 0);
    window.setTimeout(addPeerMenuItem, 0);
    window.setTimeout(() => addPluginMenuItem(YANAGIHARA_KEYWORD), 0);
    window.setTimeout(() => addPluginMenuItem(KANAZAWA_KEYWORD), 0);
    window.setTimeout(renderAraiRecord, 0);
    window.setTimeout(renderPeerRecord, 0);
    window.setTimeout(() => renderPluginRecord(YANAGIHARA_KEYWORD, `
      <section class="record-log-section">
        <h3>录音记录 <span>2026-08-13 15:57:42-16:03:50</span></h3>
        <p><strong>A</strong>:我有话要跟你说。</p>
        <p><strong>B</strong>:是准呀，你好！我猜到你要说什么了。</p>
        <p><strong>A</strong>:是么？</p>
        <p><strong>B</strong>:嗯。我没想到那段音频是你作品《当代艺术》里面的......对不起。</p>
        <p><strong>A</strong>:哎，也不怪你。不过新井真的什么都没跟你说吗？</p>
        <p><strong>B</strong>:当时我问他是哪的素材，被搪塞过去了。方便问问是个什么样的故事吗？我真的很感兴趣！</p>
        <p><strong>A</strong>:怎么说呢......两个总是一起创作的大学生，因为名和利的分布不均导致其中一个开始怨恨另一个、怨恨社会。他最终妄图用杀人来满足自己的创作和报复欲，却发现另一人竟然也在心底深埋了这种反社会人格，最终被反杀的故事。</p>
        <p><strong>B</strong>:其实音频已经能大概猜到故事了，但实际听你讲还是好震撼！好想看看原片啊。</p>
        <p><strong>A</strong>:我当时的制作，也有点自娱自乐的成分在。</p>
        <p><strong>B</strong>:不如就反过来利用这次事件，隆重发布出来怎么样？个人作品难免会有瑕疵的啦。</p>
        <p><strong>A</strong>:算了吧，只是个十几分钟的小短片......而且我把它雪藏的原因，也不是觉得制作得不好。</p>
        <p><strong>B</strong>:哦？那是我先入为主了。</p>
        <p><strong>A</strong>:其实是最后做出来，我发现完全偏离了我想要的主旨。原本我是想探讨反社会心理的成因，最后看下来好像变成了单纯的嫉妒。</p>
        <p><strong>B</strong>:嗯~很复杂啊。不过这个主题还挺深奥的，你怎么会关注到"反社会心理"呢？</p>
        <p><strong>A</strong>:跟我亲身经历有关，大四那年......等等，怎么变成你在采访我了？</p>
        <p><strong>B</strong>:哎呀，被发现了。因为我真的很好奇嘛。</p>
        <p><strong>A</strong>:......总之，虽然挪用我的东西错不在你，但这场闹剧是因你引发的。我之后也会去找新井的，希望你们反省。</p>
        <p><strong>B</strong>:诶~但我觉得这个点子本身没什么问题。难道说，我就是你剧本里的那种反社会人格？"不把原片给我看，我可无法保证会对你做什么哦？"</p>
        <p><strong>A</strong>:......少胡闹。</p>
      </section>`), 0);
    window.setTimeout(() => {
      if (new URLSearchParams(window.location.search).get("keyword") !== YANAGIHARA_KEYWORD) return;
      const transcript = document.getElementById("recordTranscript");
      const speakerTools = document.getElementById("speakerTools");
      if (!transcript || !speakerTools) return;
      const speakers = ["A", "B"];
      const storageKey = "pukuRecordSpeakers:" + YANAGIHARA_KEYWORD;
      const savedKey = "pukuRecordSpeakersSaved:" + YANAGIHARA_KEYWORD;
      const artists = ["宋雯祺", "新井拓也", "KAY", "长谷川千景", "柳原准"];
      let draft = readJson(storageKey, {});
      let editing = localStorage.getItem(savedKey) !== "true";
      const applySpeakers = () => {
        const names = readJson(storageKey, {});
        transcript.querySelectorAll("strong").forEach((node) => { const letter = node.textContent.trim(); if (names[letter]) node.textContent = names[letter]; });
      };
      const usedArtists = (exceptLetter) => Object.entries(draft).filter((entry) => entry[0] !== exceptLetter).map((entry) => entry[1]);
      const renderTools = () => {
        const saved = readJson(storageKey, {});
        const hasSaved = localStorage.getItem(savedKey) === "true";
        if (hasSaved && !editing) {
          speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-saved speaker-count-${speakers.length}"><div class="speaker-summary-list">${speakers.map((letter) => `<div class="speaker-summary"><span>${letter}</span><strong>${saved[letter] || "未设定"}</strong></div>`).join("")}</div><button class="speaker-main-action" type="button" data-yanagihara-action="edit-all">修改</button></div></section>`;
          return;
        }
        speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-editing speaker-count-${speakers.length}"><div class="speaker-choice-list">${speakers.map((letter) => `<article class="speaker-choice" data-yanagihara-letter="${letter}"><div class="speaker-choice-head"><span>${letter}</span><strong>${draft[letter] || "未选定"}</strong></div><div class="speaker-options">${artists.map((artist) => { const selected = draft[letter] === artist; const disabled = usedArtists(letter).includes(artist); return `<button type="button" class="${selected ? "selected" : ""}" data-yanagihara-artist="${artist}" ${disabled ? "disabled" : ""}>${artist}</button>`; }).join("")}</div></article>`).join("")}</div><button class="speaker-main-action" type="button" data-yanagihara-action="save-all">保存</button></div></section>`;
      };
      speakerTools.addEventListener("click", (event) => {
        const action = event.target.dataset.yanagiharaAction;
        if (action === "edit-all") { draft = Object.assign({}, readJson(storageKey, {})); editing = true; renderTools(); return; }
        if (action === "save-all") { writeJson(storageKey, draft); localStorage.setItem(savedKey, "true"); editing = false; applySpeakers(); renderTools(); showSpeakerFeedback(); return; }
        const artistButton = event.target.closest("[data-yanagihara-artist]");
        if (!artistButton || artistButton.disabled) return;
        const card = artistButton.closest("[data-yanagihara-letter]");
        const letter = card.dataset.yanagiharaLetter;
        const artist = artistButton.dataset.yanagiharaArtist;
        if (draft[letter] === artist) delete draft[letter]; else draft[letter] = artist;
        renderTools();
      });
      renderTools();
      if (localStorage.getItem(savedKey) === "true") applySpeakers();
    }, 0);
    window.setTimeout(() => renderPluginRecord(KANAZAWA_KEYWORD, `
      <section class="record-log-section">
        <h3>会议记录 <span>2026-08-11 10:44:12-10:50:09</span></h3>
        <p><strong>A</strong>:这个展结束了，我们要不要一起出去玩?</p>
        <p><strong>B</strong>:赞成！跟大家一起肯定很开心。 我们去远一点的地方吧，就像社团合宿那样，玩他个3天2晚的。</p>
        <p><strong>C</strong>:学生们真好啊，我身在社会，可没那么多时间咯。我就pass吧。</p>
        <p><strong>B</strong>:芬奇老师怎么这样~！要去就得我们五个人一起去嘛。</p>
        <p><strong>D</strong>:不然我们找个有美术馆的地方？这样就不只是纯玩了，还可以观摩学习。</p>
        <p><strong>A</strong>:还可以有观摩学习的借口。</p>
        <p><strong>B</strong>:更像合宿了！哈哈哈哈哈。</p>
        <p><strong>E</strong>:柳原是在趁机推荐金泽吧，小心思~我一直都很想去21世纪美术馆。</p>
        <p><strong>D</strong>:也不是啦，不过你们愿意来的话我会很高兴。我可以给大家当向导！</p>
        <p><strong>C</strong>:千景没去过21美吗？我之前因为工作去过几次，那个泳池很漂亮，我觉得适合你哦。</p>
        <p><strong>D</strong>:嗯，特展一直都在换，得查了才知道。不过常设展我可都烂熟于心了。除了泳池，还有个可以说是我迄今最喜欢的展品。</p>
        <p><strong>E</strong>:评价好高哦，好奇好奇。</p>
        <p><strong>D</strong>:是一个金属小人的雕像，拿着尺子站在美术馆的房顶。那个位置很多人注意不到，所以我很享受跟人介绍时对方惊讶的表情。</p>
        <p><strong>B</strong>:怎么感觉前辈说的"最喜欢"是另一种意义上的...?</p>
        <p><strong>D</strong>:当然作品本身也很棒！它就好像在丈量整片天空一样，我每次进去都要看好久。而且形状还像个Y字，跟我名字的首字母也对上了，很有缘分！你们要是感兴趣，可以在<a href="/live/kanazawa-collection.html" target="_blank" rel="noopener">21世纪美术馆的「恒久展示作品」</a>看到照片。不过还是肉眼看最棒。</p>
        <p><strong>A</strong>:柳原遇到自己喜欢的事物原来这么健谈啊~那，目的地就决定是金泽了？</p>
        <p><strong>E</strong>:同意！能不能跳过办展，直接进入合宿环节啊。</p>
        <p><strong>C</strong>:梦话等睡着了再说吧。好了好了，大家都回去布置吧，我看看能不能空出时间。</p>
      </section>`), 0);
    window.setTimeout(() => {
      if (new URLSearchParams(window.location.search).get("keyword") !== KANAZAWA_KEYWORD) return;
      const transcript = document.getElementById("recordTranscript");
      const speakerTools = document.getElementById("speakerTools");
      if (!speakerTools) return;
      const kanazawaSpeakers = ["A", "B", "C", "D", "E"];
      const kanazawaStorageKey = "pukuRecordSpeakers:" + KANAZAWA_KEYWORD;
      const kanazawaSavedKey = "pukuRecordSpeakersSaved:" + KANAZAWA_KEYWORD;
      const artists = ["宋雯祺", "新井拓也", "KAY", "长谷川千景", "柳原准"];
      let kanazawaDraft = readJson(kanazawaStorageKey, {});
      let kanazawaEditing = localStorage.getItem(kanazawaSavedKey) !== "true";
      const applyKanazawaSpeakers = () => {
        const names = readJson(kanazawaStorageKey, {});
        if (transcript) transcript.querySelectorAll("strong").forEach((node) => { const l = node.textContent.trim(); if (names[l]) node.textContent = names[l]; });
      };
      const usedKanazawaArtists = (exceptLetter) => Object.entries(kanazawaDraft).filter((e) => e[0] !== exceptLetter).map((e) => e[1]);
      const renderKanazawaSpeakerTools = () => {
        const saved = readJson(kanazawaStorageKey, {});
        const hasSaved = localStorage.getItem(kanazawaSavedKey) === "true";
        if (hasSaved && !kanazawaEditing) {
          speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-saved speaker-count-${kanazawaSpeakers.length}"><div class="speaker-summary-list">${kanazawaSpeakers.map((l) => `<div class="speaker-summary"><span>${l}</span><strong>${saved[l] || "未设定"}</strong></div>`).join("")}</div><button class="speaker-main-action" type="button" data-kanazawa-action="edit-all">修改</button></div></section>`;
          return;
        }
        speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-editing speaker-count-${kanazawaSpeakers.length}"><div class="speaker-choice-list">${kanazawaSpeakers.map((letter) => `<article class="speaker-choice" data-kanazawa-letter="${letter}"><div class="speaker-choice-head"><span>${letter}</span><strong>${kanazawaDraft[letter] || "未选定"}</strong></div><div class="speaker-options">${artists.map((artist) => { const sel = kanazawaDraft[letter] === artist; const dis = usedKanazawaArtists(letter).indexOf(artist) !== -1; return `<button type="button" class="${sel ? "selected" : ""}" data-kanazawa-artist="${artist}" ${dis ? "disabled" : ""}>${artist}</button>`; }).join("")}</div></article>`).join("")}</div><button class="speaker-main-action" type="button" data-kanazawa-action="save-all">保存</button></div></section>`;
      };
      speakerTools.addEventListener("click", (event) => {
        const action = event.target.dataset.kanazawaAction;
        if (action === "edit-all") { kanazawaDraft = Object.assign({}, readJson(kanazawaStorageKey, {})); kanazawaEditing = true; renderKanazawaSpeakerTools(); return; }
        if (action === "save-all") { writeJson(kanazawaStorageKey, kanazawaDraft); localStorage.setItem(kanazawaSavedKey, "true"); kanazawaEditing = false; applyKanazawaSpeakers(); renderKanazawaSpeakerTools(); showSpeakerFeedback(); return; }
        const artistBtn = event.target.closest("[data-kanazawa-artist]");
        if (!artistBtn || artistBtn.disabled) return;
        const article = artistBtn.closest("[data-kanazawa-letter]");
        if (!article) return;
        const letter = article.dataset.kanazawaLetter;
        const artist = artistBtn.dataset.kanazawaArtist;
        if (kanazawaDraft[letter] === artist) { delete kanazawaDraft[letter]; } else { kanazawaDraft[letter] = artist; }
        renderKanazawaSpeakerTools();
      });
      renderKanazawaSpeakerTools();
      if (localStorage.getItem(kanazawaSavedKey) === "true") applyKanazawaSpeakers();
    }, 0);
    window.setTimeout(() => addPluginMenuItem("螺丝"), 0);
    window.setTimeout(() => addPluginMenuItem("野良犬"), 0);
    window.setTimeout(() => addPluginMenuItem("自动抓取"), 0);
    window.setTimeout(() => renderPluginRecord("自动抓取", `
      <section class="record-log-section">
        <h3>最近的自动抓取内容（2026-08-13） <span>未检测到人声，仅对声音事件做检测与识别。</span></h3>
        <p>23:12｜正门开锁声，随后为由远及近、再远去的脚步声。</p>
        <p>23:20｜脚步急促接近。检测到金属管材伸展与踏板承重摩擦声。</p>
        <p>23:23｜踏板撞击与踩地声，快速下梯后脚步声迅速远去。</p>
        <p>23:25｜脚步声再次经过主通道，正门开启并重新上锁。</p>
        <p>23:29｜正门再次开锁，随后为由远及近、再远去的脚步声。与前次声纹不一致。</p>
        <p>23:32｜脚步缓缓接近，随后声音静止约 30 秒。</p>
        <p>23:33｜检测到薄膜类材料的撕裂声及持续的人类口腔咬合声响。</p>
        <p>23:35｜咬合声响停止。伴随缓慢离去脚步声，正门重新上锁，现场恢复安静。</p>
      </section>`), 0);
    window.setTimeout(() => {
      if (new URLSearchParams(window.location.search).get("keyword") !== "自動抓取") return;
      window.history.replaceState(null, "", `record.html?keyword=${encodeURIComponent("自动抓取")}`);
      renderPluginRecord("自动抓取", `
        <section class="record-log-section">
          <h3>最近的自动抓取内容（2026-08-13） <span>未检测到人声，仅对声音事件做检测与识别。</span></h3>
          <p>23:12｜正门开锁声，随后为由远及近、再远去的脚步声。</p>
          <p>23:20｜脚步急促接近。检测到金属管材伸展与踏板承重摩擦声。</p>
          <p>23:23｜踏板撞击与踩地声，快速下梯后脚步声迅速远去。</p>
          <p>23:25｜脚步声再次经过主通道，正门开启并重新上锁。</p>
          <p>23:29｜正门再次开锁，随后为由远及近、再远去的脚步声。与前次声纹不一致。</p>
          <p>23:32｜脚步缓缓接近，随后声音静止约 30 秒。</p>
          <p>23:33｜检测到薄膜类材料的撕裂声及持续的人类口腔咬合声响。</p>
          <p>23:35｜咬合声响停止。伴随缓慢离去脚步声，正门重新上锁，现场恢复安静。</p>
        </section>`);
    }, 0);
    window.setTimeout(() => renderPluginRecord("野良犬", `
      <section class="record-log-section">
        <h3>笔记</h3>
        <p>能来这次展会，说真的，我很开心。</p>
        <p>仔细想想，能跟一起干活的人都意气相投，真不容易。我是真想跟他们混熟啊，但……在他们眼里，我大概就是个讨人嫌的家伙吧。</p>
        <p>小时候我就像一条没人管的野狗一样，从没有人教过我规矩。我习惯了随时提防别人，习惯了装不屑和嘲讽。以为只要表现得什么都不在乎，别人就伤不到自己了。</p>
        <p>到最后，我才发现想法和价值观都和别人不一样。 比如提前翻一翻别人的东西，然后当面聊起来，我以为这样显得亲近，结果对方往往是被冒犯到。再比如，我一直觉得能互相开玩笑、甚至互相戳一下痛处，才叫真交情，结果每次实践下来，都是我自己越界。</p>
        <p>这几个人里，我唯一提前认识的就是柳原前辈。</p>
        <p>刚知道他在研究\u201c报复社会\u201d这种课题的时候，我真的很感兴趣。甚至隐隐觉得，说不定通过他的研究，我也能搞明白自己为什么总是这么格格不入。可接触久了才发现，他只是抱着一种制作剪报的心态，在收集各种资料罢了。正因如此，我当着其他朋友的面直白地提出不同的观点，期待着他用更深入的见解反驳我。然而可惜的是，他只白了我一眼，没有再说更多了。那一刻我才弄懂，对于我、对于各种无法用普通价值观理解的事物，大家只想站在安全的地方害怕和谴责吧。</p>
        <p>但无论如何，我还是想跟另外四个人搞好关系。至少这次……不想再被当成怪胎了。</p>
        <p>希望展会能顺顺利利结束吧，到时候大家一块儿去旅行。</p>
      </section>`), 0);
    window.setTimeout(() => renderPluginRecord("螺丝", `
      <section class="record-log-section">
        <h3>录音记录 <span>2026-08-13 14:30:06-14:35:10</span></h3>
        <p><strong>A</strong>:吃什么呢？展厅里禁止饮食哦。</p>
        <p><strong>B</strong>:啊，新井，辛苦~这个是软糖啦，不会掉渣的，放心。作品布置完了吗？</p>
        <p><strong>A</strong>:基本都结束了，还差《无害穿刺》的灯光要调整一下。这可是我最得意的作品，你就等着看最终效果吧。</p>
        <p><strong>B</strong>:嗯~那我在旁边看你做好了。</p>
        <p><strong>A</strong>:拿我当节目看啊？那给我分一点吃。</p>
        <p><strong>B</strong>:不要。我心情不好的时候不会分给别人的。我要自己全部吃掉。</p>
        <p><strong>A</strong>:哎哟，怎么了？是谁欺负可爱的小千景了？是KAY吗？</p>
        <p><strong>B</strong>:没有啦，是我自己的事情。你继续布置你的就好。</p>
        <p><strong>A</strong>:我才发现你这个好像是去年的联名款，保质期不要紧吗？小千景还真是喜欢汉顿，可惜联名的零食好少。</p>
        <p><strong>B</strong>:还挺懂的嘛，不过我可不会分给你。</p>
        <p><strong>A</strong>:好嘛，那我等下回休息区吃虾片好了。</p>
        <p><strong>B</strong>:那个也是我买的，我要吃。</p>
        <p><strong>A</strong>:诶~</p>
        <p>......</p>
        <p><strong>B</strong>:这个灯光的角度真的很棒，钢筋本身是乱乱的，但照出的影子竟然真的变成了一整根长刺，好神奇。</p>
        <p><strong>A</strong>:哈哈，我没吹牛吧？整个作品的关键就在于射灯的角度，不枉我站在这拧了半天螺丝。你看，只要让光线刚好擦着废钢筋的尖角过去，底下的投影就会被拉得很长了。</p>
        <p><strong>B</strong>:诶，不过你踩那么高不害怕吗？梯子感觉有2米高了。</p>
        <p><strong>A</strong>:还好吧，要想效果精准，灯就得架这么高。上来感受下吗？视野很好哦。</p>
        <p><strong>B</strong>:那还是不用了。好，我也该继续收尾了。</p>
        <p><strong>A</strong>:诶~真的一口都没给我剩。</p>
      </section>`), 0);
    window.setTimeout(() => {
      if (new URLSearchParams(window.location.search).get("keyword") !== "螺丝") return;
      const transcript = document.getElementById("recordTranscript");
      const speakerTools = document.getElementById("speakerTools");
      if (!speakerTools) return;
      const screwSpeakers = ["A", "B"];
      const screwStorageKey = "pukuRecordSpeakers:螺丝";
      const screwSavedKey = "pukuRecordSpeakersSaved:螺丝";
      const artists = ["宋雯祺", "新井拓也", "KAY", "长谷川千景", "柳原准"];
      let screwDraft = readJson(screwStorageKey, {});
      let screwEditing = localStorage.getItem(screwSavedKey) !== "true";
      const applyScrewSpeakers = () => {
        const names = readJson(screwStorageKey, {});
        if (transcript) transcript.querySelectorAll("strong").forEach((node) => { const l = node.textContent.trim(); if (names[l]) node.textContent = names[l]; });
      };
      const usedScrewArtists = (exceptLetter) => Object.entries(screwDraft).filter((e) => e[0] !== exceptLetter).map((e) => e[1]);
      const renderScrewSpeakerTools = () => {
        const saved = readJson(screwStorageKey, {});
        const hasSaved = localStorage.getItem(screwSavedKey) === "true";
        if (hasSaved && !screwEditing) {
          speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-saved speaker-count-${screwSpeakers.length}"><div class="speaker-summary-list">${screwSpeakers.map((l) => `<div class="speaker-summary"><span>${l}</span><strong>${saved[l] || "未设定"}</strong></div>`).join("")}</div><button class="speaker-main-action" type="button" data-screw-action="edit-all">修改</button></div></section>`;
          return;
        }
        speakerTools.innerHTML = `<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-editing speaker-count-${screwSpeakers.length}"><div class="speaker-choice-list">${screwSpeakers.map((letter) => `<article class="speaker-choice" data-screw-letter="${letter}"><div class="speaker-choice-head"><span>${letter}</span><strong>${screwDraft[letter] || "未选定"}</strong></div><div class="speaker-options">${artists.map((artist) => { const sel = screwDraft[letter] === artist; const dis = usedScrewArtists(letter).indexOf(artist) !== -1; return `<button type="button" class="${sel ? "selected" : ""}" data-screw-artist="${artist}" ${dis ? "disabled" : ""}>${artist}</button>`; }).join("")}</div></article>`).join("")}</div><button class="speaker-main-action" type="button" data-screw-action="save-all">保存</button></div></section>`;
      };
      speakerTools.addEventListener("click", (event) => {
        const action = event.target.dataset.screwAction;
        if (action === "edit-all") { screwDraft = Object.assign({}, readJson(screwStorageKey, {})); screwEditing = true; renderScrewSpeakerTools(); return; }
        if (action === "save-all") { writeJson(screwStorageKey, screwDraft); localStorage.setItem(screwSavedKey, "true"); screwEditing = false; applyScrewSpeakers(); renderScrewSpeakerTools(); showSpeakerFeedback(); return; }
        const artistBtn = event.target.closest("[data-screw-artist]");
        if (artistBtn) { const article = artistBtn.closest("[data-screw-letter]"); if (article) { screwDraft[article.dataset.screwLetter] = artistBtn.dataset.screwArtist; renderScrewSpeakerTools(); } }
      });
      renderScrewSpeakerTools();
      if (localStorage.getItem(screwSavedKey) === "true") applyScrewSpeakers();
    }, 0);
    window.setTimeout(() => {
      if (new URLSearchParams(window.location.search).get("keyword") !== "螺丝") return;
      const scroll = document.querySelector(".record-scroll");
      if (!scroll || scroll.dataset.screwHiddenReady === "true") return;
      scroll.dataset.screwHiddenReady = "true";
      const navKey = "pukuScrewHiddenNavAt";
      const navCooldown = 1400;
      const requiredHold = 3000;
      const inputGapLimit = 650;
      let holdStart = 0;
      let lastInputAt = 0;
      let navTimer = null;
      let touchY = 0;
      let touching = false;
      let pulling = false;
      const currentTop = () => Math.min(scroll.scrollTop || 0, window.scrollY || document.documentElement.scrollTop || 0);
      const recentlyNavigated = () => Date.now() - Number(sessionStorage.getItem(navKey) || 0) < navCooldown;
      const resetGesture = () => {
        holdStart = 0;
        lastInputAt = 0;
        pulling = false;
        if (navTimer) window.clearInterval(navTimer);
        navTimer = null;
      };
      const startTimer = () => {
        if (navTimer) return;
        navTimer = window.setInterval(() => {
          const now = Date.now();
          const aliveByTouch = touching && pulling;
          if (currentTop() > 2 || (!aliveByTouch && now - lastInputAt > inputGapLimit)) { resetGesture(); return; }
          if (holdStart && now - holdStart >= requiredHold) {
            sessionStorage.setItem(navKey, String(now));
            resetGesture();
            window.location.href = "hidden-record.html";
          }
        }, 100);
      };
      const notePull = (amount) => {
        const now = Date.now();
        if (recentlyNavigated() || currentTop() > 2 || amount <= 0) { resetGesture(); return; }
        if (!holdStart) holdStart = now;
        lastInputAt = now;
        pulling = true;
        startTimer();
      };
      const handleWheel = (e) => { notePull(-e.deltaY); };
      const handleTouchStart = (e) => { touchY = e.touches[0].clientY; touching = true; };
      const handleTouchMove = (e) => {
        const nextY = e.touches[0].clientY;
        const delta = nextY - touchY;
        touchY = nextY;
        if (delta > 0) notePull(delta);
      };
      const handleTouchEnd = () => { touching = false; pulling = false; };
      let lastBlockY = 0;
      const handleBlockStart = () => { lastBlockY = 0; };
      const handleBlockMove = (e) => {
        if (currentTop() > 2) return;
        const t = e.touches && e.touches[0];
        if (!t) return;
        if (lastBlockY !== 0 && t.clientY > lastBlockY) e.preventDefault();
        lastBlockY = t.clientY;
      };
      document.addEventListener("touchstart", handleBlockStart, { passive: true });
      document.addEventListener("touchmove", handleBlockMove, { passive: false });
      scroll.addEventListener("wheel", handleWheel, { passive: true });
      window.addEventListener("wheel", handleWheel, { passive: true });
      scroll.addEventListener("touchstart", handleTouchStart, { passive: true });
      window.addEventListener("touchstart", handleTouchStart, { passive: true });
      scroll.addEventListener("touchmove", handleTouchMove, { passive: true });
      window.addEventListener("touchmove", handleTouchMove, { passive: true });
      scroll.addEventListener("touchend", handleTouchEnd);
      window.addEventListener("touchend", handleTouchEnd);
      scroll.addEventListener("touchcancel", handleTouchEnd);
      window.addEventListener("touchcancel", handleTouchEnd);
      window.addEventListener("blur", resetGesture);
      document.addEventListener("visibilitychange", resetGesture);
    }, 0);
  };

  const setupDocsPlugin = () => {
    const list = document.getElementById("araiDocsList");
    const add = document.getElementById("araiDocsAdd");
    const addMenu = document.getElementById("araiDocsAddMenu");
    const upload = document.getElementById("araiDocsUpload");
    const reset = document.getElementById("araiDocsReset");
    if (!list || !add || !addMenu || !upload || !reset) return;

    const docsKey = "araiDocsCache";
    const maxBytes = 2 * 1024 * 1024;
    const nowLabel = () => new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date());
    const getDocs = () => readJson(docsKey, []);
    const saveDocs = (docs) => writeJson(docsKey, docs);
    const totalBytes = (docs) => docs.reduce((sum, doc) => sum + (doc.bytes || 0), 0);

    const defaultDocs = [
      {
        id: "preset-20260812-audio",
        type: "blank",
        name: "2026-08-12录音",
        content: `2026-08-12 22:34:01-22:46:47
宋：……怎么直接约在展厅这里？虽然是晚上，但这毕竟是公共场所。
KAY：放心吧芬奇老师，我亲眼看到他们两个走人的。门我也锁上了，安全得很。除非……这里有窃听器，哈哈。
新井：好啦，赶紧介绍一下你的计划。上次开会时你说什么“尸体模特”，可真敢说啊。连我也都吓了一跳。我太感兴趣了，快讲讲怎么回事。
KAY：嘿嘿，因为只有这样才够冲击啊。为了完美实现我的艺术……我需要一具真正的“尸体”。
宋：什么？你认真的吗？！
KAY：别激动别激动，我的意思是，找个大活人来“演”一具尸体。其实我也是想拜托新井，等下需要你蜷缩进我的作品里，摆出和假人一模一样的姿势，然后我来拍几张照片。展会开始前，我会把官网的主视觉海报悄悄替换成给你拍的真人照片。
新井：哇哦……不发任何声明，就这么悄无声息地换掉？
KAY：对！让那些仔细看海报的观众突然发现，“等等，这好像是个真人？”。每个感到不安、产生猜疑的观众，都会成为我作品的一部分。
新井：太酷了吧！我完全没问题！
宋：等等，这太冒险了。万一引起公众恐慌被投诉怎么办？画廊那边如果追究下来——
KAY：这不就是我们追求的艺术表达吗？芬奇老师，求你了，就让我们试试吧！
新井：是啊，嘴上这么说，您肯定也觉得KAY的点子有意思，想看看能产生什么样的反响吧？我早就感觉到，您对艺术追求的狂热，和我们是一样的。
宋：……好吧，真是服了你们了。但这件事我就不参与了，你们自己把握好尺度。
......
KAY：唉，其实我也猜到这种结果了。那新井，只能咱俩来录了，我们先——
新井：哎，等等，不用那么麻烦……我手机里正好有一段极其完美的现成音频。
KAY：嗯？什么现成的音频？哪来的？
新井：这你就别管了，我也是刚好想到。你听听这个台词，我觉得完美适配你想要的场景。
......
KAY：哈哈，有意思！这是谁自制的cult片吗？粗劣但是别有风味啊！
新井：对吧？你觉得能不能直接用？
KAY：完全没问题！就用这个吧。既然芬奇老师中途走了，就改成她走之后，我突然开始追杀你、然后被你反杀......不过这样就是我演尸体，可能要麻烦你拍照了。
新井：诶~我明明最期待这个环节。好吧好吧，你是导演，你说了算。
KAY：嘿嘿，抱歉抱歉。那我们这就开始吧！今晚回去我就剪辑音频。
新井：走起！`,
        bytes: 0,
        lastOpened: "2026年8月12日 22:46"
      },
      {
        id: "preset-20260813",
        type: "blank",
        name: "2026-08-13录音",
        content: "18:20:33-18:25:14\n柳原：我有话要跟你说。\n新井：噢，学长晚上好啊。你怎么了？\n柳原：你配合KAY装神弄鬼的事我都知道了。这本身就挺恶劣的，你居然还挪用了我作品里的音频？谁允许你这么干的？\n新井：作品里的...啊~是那件事。之前路过你桌前，我瞥到了一个很感兴趣的标题，之后就去翻了翻。《当代艺术》，很有趣的小短片啊！前辈你什么时候做的这个？不发表出来真的好可惜。\n柳原：那是我本科四年级的时候做的...别转移话题。你就没有侵犯他人界限的罪恶感吗？怪不得能和那些反社会人格共情。\n新井：别动不动就扣帽子。你为什么不能接受世界上有人和你不同？想让所有人都在画好的格子里走，这才可怕吧。\n柳原：没想到秩序能被你曲解成这样...做着损害他人的事就算了，最终自己也没有受益，这到底是图什么！真是不可理喻。\n新井：那你呢？你对无法理解的人这么上心，你又图什么？\n\n柳原：那不一样，我是在研究社会问题！\n新井：你搜集关于反社会者的成长经历、访谈、案件介绍，把他们当怪物拆开脑壳窥探。你说这是研究、我还说这是一种\u201c消费\u201d。不过，我没想到你得出的结论竟然是\u201c不可理喻\u201d。你的目的从一开始就不是为了理解，而是为了隔绝。\n柳原：......你这是强词夺理。凭什么遵守规矩的人要被违规者指责？\n柳原：好痛！你撞我干什么！\n新井：没有人生来就是怪物。",
        bytes: 0,
        lastOpened: "2026年8月13日 23:14"
      },
      {
        id: "preset-20260807",
        type: "blank",
        name: "2026-08-14录音",
        content: "07:55:37-08:01:22\n……呼。\n我叫宋雯祺。现在是8月14号，早晨7点55。我第一个到的会场，然后……看到了新井，的尸体。\n看这个情况，人已经彻底没救了。我现在正准备报警。\n不过……出了人命，这个艺术展肯定要彻底泡汤了。我们的心血，全都要变成\u201c命案现场\u201d的背景。\n新井，你不是在给KAY帮忙时没演到尸体，挺遗憾的吗？某种意义上……你这辈子能想到的所有装置，加起来都没有你现在的样子来得纯粹而震撼。\n我承认，我和你就是一路人。我非常欣赏你的理念，可惜置身社会，很多事情身不由己......这个道理，你也永远没机会懂了。\n所以我得在报警之前，先记录下来。这是你的最后一件，注定会被世人铭记的作品——《新井拓也》。\n......\n新井拓也处于悬挂状态。你的后颈部被自己的作品《无害穿刺》上一处突出的金属尖端直接刺穿，并牢牢固定在半空，双脚离地大概……半米左右。看来你之前说过的承重系数，并不是一句空话。\n你的头部呈向前下方的垂落姿态，下巴几乎紧贴着胸部。全身的肌肉已经完全松弛了，双臂和双腿自然下垂、晃来晃去的……右脚的鞋掉了,就在下面梯子旁边躺着。\n好，让我换个角度再拍几张。\n伤口在后颈。创口处流出的血液顺着《无害穿刺》表面一路淌下来，在正下方的地面上汇聚成了一大摊干涸的黑褐色凝块。\n那架人字梯侧翻在地上，位置在《无害穿刺》的下方偏侧。地面上有明显的梯子翻倒时留下的划动痕迹、和一些细小的灰尘粉末。不确定到底是什么的残渣。\n《新井拓也》，完成了。\n......\n艺术品到此就结束了，不过我也想整理一下线索，看看新井究竟是怎么变成这样的。\n对了，噗咚。说不定AI能推演出什么隐藏的结论。等下我要上传一波最新的数据。\n哦，还有新井之前做的那个小短片。那也算是《新井拓也》的一部分，之后我会上传保存一下。\n就这些。\n※追记：/live/netdisk.html 提取码还是他的生日 ",
        bytes: 0,
        lastOpened: "2026年8月14日 08:02"
      }
    ];

    const ensureDefaults = () => {
      const docs = getDocs().filter((doc) => !(doc.name === "2026-08-12录音" && String(doc.content || "").startsWith("18:20:33-18:25:14\n柳原：我有话要跟你说。")));
      const existing = new Map(docs.map((doc) => [doc.id, doc]));
      const merged = defaultDocs.map((preset) => {
        const saved = existing.get(preset.id);
        if (!saved) return preset;
        const pointAtGate = (value) => value
          .replace(/https:\/\/pan\.baidu\.com\/\S+/g, "/live/netdisk.html")
          .replace(/\/step2\/netdisk\/?/g, "/live/netdisk.html");
        if (typeof saved.content === "string" && (saved.content.includes("pan.baidu.com") || saved.content.includes("/step2/netdisk"))) {
          saved.content = pointAtGate(saved.content);
        }
        if (typeof saved.editedHtml === "string" && (saved.editedHtml.includes("pan.baidu.com") || saved.editedHtml.includes("/step2/netdisk"))) {
          saved.editedHtml = pointAtGate(saved.editedHtml);
        }
        return saved;
      }).concat(docs.filter((doc) => !defaultDocs.some((preset) => preset.id === doc.id)));
      saveDocs(merged);
    };
    ensureDefaults();

    reset.addEventListener("click", () => {
      saveDocs(defaultDocs.map((doc) => Object.assign({}, doc)));
      addMenu.hidden = true;
      render();
    });

    const docPageNumbers = {
      "preset-20260812-audio": "stepⅡ 7/19",
      "preset-20260813": "stepⅡ 8/19",
      "preset-20260807": "stepⅡ 9/19"
    };
    const docEditorStyles = `*{box-sizing:border-box;margin:0}body{background:#525659;display:flex;justify-content:center;padding:40px 20px;min-height:100vh}article{width:816px;min-height:1056px;padding:96px 72px;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,0.3);font:15px/2.4 "Microsoft YaHei","Noto Sans SC",Arial,sans-serif;color:#202124;word-break:break-word;outline:none;white-space:pre-wrap;letter-spacing:0.03em}img{max-width:100%;height:auto}.page-number{position:fixed;right:20px;bottom:20px;z-index:1000;padding:6px 12px;border-radius:999px;color:#fff;background:#000;box-shadow:0 4px 14px rgba(0,0,0,.24);font:700 14px/1.2 Arial,sans-serif;letter-spacing:.02em;white-space:nowrap;pointer-events:none}`;
    const docPageNumberMarkup = (docId) => docPageNumbers[docId] ? `<div class="page-number" aria-label="页面进度">${docPageNumbers[docId]}</div>` : "";

    const buildEditorPage = (title, bodyContent, docId) => `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>${title}</title><style>${docEditorStyles}</style></head><body><article contenteditable="true">${bodyContent}</article>${docPageNumberMarkup(docId)}<script>
var saved=false;
var article=document.querySelector("article");
window.addEventListener("beforeunload",function(e){if(!saved){e.preventDefault();e.returnValue=""}});
window.addEventListener("keydown",function(e){if((e.ctrlKey||e.metaKey)&&e.key==="s"){e.preventDefault();doSave()}});
function doSave(){saved=true;var data={araiDocSave:true,docId:"${docId}",html:article.innerHTML};if(window.opener){window.opener.postMessage(data,"*")}if(window.parent&&window.parent!==window){window.parent.postMessage(data,"*")}}
window.addEventListener("unload",function(){if(!saved){doSave()}});
<\/script></body></html>`;

    window.addEventListener("message", (event) => {
      if (!event.data || !event.data.araiDocSave) return;
      const docs = getDocs();
      const doc = docs.find((item) => item.id === event.data.docId);
      if (!doc) return;
      doc.editedHtml = event.data.html;
      saveDocs(docs);
    });

    const openDoc = (id) => {
      const docs = getDocs();
      const doc = docs.find((item) => item.id === id);
      if (!doc) return;
      doc.lastOpened = nowLabel();
      saveDocs(docs);
      render();

      let bodyContent = "";

      if (doc.editedHtml) {
        bodyContent = doc.editedHtml;
      } else if (doc.dataUrl && doc.dataUrl.startsWith("data:image")) {
        bodyContent = `<img src="${doc.dataUrl}" alt="${escapeHtml(doc.name)}">`;
      } else if (doc.dataUrl) {
        bodyContent = escapeHtml(doc.textContent || doc.name);
      } else {
        bodyContent = (doc.content || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
      }
      bodyContent = bodyContent.replace(/(?<![=">])\/live\/netdisk\.html/g, '<a href="/live/netdisk.html">/live/netdisk.html</a>');

      const title = escapeHtml(doc.name);
      const page = buildEditorPage(title, bodyContent, doc.id);
      openEditorPage(page, title);
    };

    const removeDoc = (id) => {
      saveDocs(getDocs().filter((doc) => doc.id !== id));
      render();
    };

    const renameDoc = (id) => {
      const docs = getDocs();
      const doc = docs.find((item) => item.id === id);
      if (!doc) return;
      const next = window.prompt("请输入新的文档名称", doc.name);
      if (!next || !next.trim()) return;
      doc.name = next.trim();
      saveDocs(docs);
      render();
    };

    function render() {
      const docs = getDocs();
      if (!docs.length) {
        list.innerHTML = '<p class="arai-docs-empty">暂无文档。点击右下角添加按钮新建或上传。</p>';
        return;
      }

      list.innerHTML = docs.map((doc) => `
        <article class="arai-docs-row" data-doc-id="${doc.id}">
          <span class="arai-docs-icon"><img src="/step2/images/icon-file.png" alt="文档"></span>
          <span class="arai-docs-name" data-doc-open>${escapeHtml(doc.name)}</span>
          <button class="arai-docs-more" type="button" data-doc-more aria-label="更多操作">⋮</button>
          <div class="arai-docs-menu" hidden>
            <button type="button" data-doc-rename>重命名</button>
            <button type="button" data-doc-delete>删除</button>
            <button type="button" data-doc-newtab>在新标签页打开</button>
          </div>
        </article>`).join("");
    }

    list.addEventListener("click", (event) => {
      const row = event.target.closest("[data-doc-id]");
      if (!row) return;
      const id = row.dataset.docId;

      if (event.target.closest("[data-doc-open]") || event.target.closest("[data-doc-newtab]")) {
        openDoc(id);
        return;
      }
      if (event.target.closest("[data-doc-rename]")) {
        renameDoc(id);
        return;
      }
      if (event.target.closest("[data-doc-delete]")) {
        removeDoc(id);
        return;
      }
      if (event.target.closest("[data-doc-more]")) {
        list.querySelectorAll(".arai-docs-menu").forEach((menu) => {
          if (menu !== row.querySelector(".arai-docs-menu")) menu.hidden = true;
        });
        const menu = row.querySelector(".arai-docs-menu");
        if (menu) menu.hidden = !menu.hidden;
      }
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".arai-docs-row")) list.querySelectorAll(".arai-docs-menu").forEach((menu) => { menu.hidden = true; });
      if (!event.target.closest("#araiDocsAdd") && !event.target.closest("#araiDocsAddMenu")) addMenu.hidden = true;
    });

    add.addEventListener("click", (event) => {
      event.stopPropagation();
      addMenu.hidden = !addMenu.hidden;
    });

    addMenu.addEventListener("click", (event) => {
      const action = event.target.dataset.docAction;
      if (action === "new") {
        const docs = getDocs();
        docs.unshift({ id: `doc-${Date.now()}`, type: "blank", name: "未命名文档", content: "", bytes: 0, lastOpened: "--" });
        saveDocs(docs);
        addMenu.hidden = true;
        render();
      }
      if (action === "upload") {
        upload.click();
        addMenu.hidden = true;
      }
    });

    upload.addEventListener("change", () => {
      const files = Array.from(upload.files || []);
      if (!files.length) return;
      const docs = getDocs();
      const selectedBytes = files.reduce((sum, file) => sum + file.size, 0);
      if (totalBytes(docs) + selectedBytes > maxBytes) {
        window.alert("上传失败：浏览器缓存内文件总大小不能超过 2MB。请先删除部分文件。");
        upload.value = "";
        return;
      }

      let remaining = files.length;
      files.forEach((file) => {
        const isImage = file.type.startsWith("image/");
        const id = `file-${Date.now()}-${Math.random().toString(16).slice(2)}`;

        if (isImage) {
          const reader = new FileReader();
          reader.onload = () => {
            docs.unshift({ id, type: "file", name: file.name, dataUrl: reader.result, bytes: file.size, lastOpened: "--" });
            remaining -= 1;
            if (remaining === 0) { saveDocs(docs); upload.value = ""; render(); }
          };
          reader.readAsDataURL(file);
        } else {
          const textReader = new FileReader();
          textReader.onload = () => {
            docs.unshift({ id, type: "file", name: file.name, textContent: textReader.result, bytes: file.size, lastOpened: "--" });
            remaining -= 1;
            if (remaining === 0) { saveDocs(docs); upload.value = ""; render(); }
          };
          textReader.readAsText(file);
        }
      });
    });

    render();
  };

  const setupYanagiharaDocsPlugin = () => {
    const gate = document.getElementById("yanagiharaGate");
    const inner = document.getElementById("yanagiharaDocsInner");
    const pwInput = document.getElementById("yanagiharaPassword");
    const pwSubmit = document.getElementById("yanagiharaSubmit");
    const pwError = document.getElementById("yanagiharaError");
    if (!gate || !inner || !pwInput || !pwSubmit) return;

    const yPassedKey = "yanagiharaPassUnlocked";
    const checkPassword = async () => {
      if (pwSubmit.disabled) return;
      pwSubmit.disabled = true;
      let isValid = false;
      try {
        isValid = await window.passwordVerifier.verify(3, pwInput.value);
      } catch (error) {}
      if (isValid) {
        localStorage.setItem(yPassedKey, "1");
        gate.remove();
        inner.hidden = false;
        initYanagihara();
      } else {
        pwError.textContent = "密码错误";
        pwInput.value = "";
        pwSubmit.disabled = false;
        window.setTimeout(() => { pwError.textContent = ""; }, 1500);
      }
    };
    pwSubmit.addEventListener("click", checkPassword);
    pwInput.addEventListener("keydown", (e) => { if (e.key === "Enter") checkPassword(); });

    const yDocsKey = "yanagiharaDocsCache";
    const yGetDocs = () => readJson(yDocsKey, []);
    const ySaveDocs = (docs) => writeJson(yDocsKey, docs);
    const maxBytes = 2 * 1024 * 1024;
    const totalBytes = (docs) => docs.reduce((sum, doc) => sum + (doc.bytes || 0), 0);
    const nowLabel = () => new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date());

    const yDefaultDoc = {
      id: "yanagi-20260810",
      type: "blank",
      name: "2026-08-10",
      content: "在很长一段时间里，我都以为世界理所当然是理性且有逻辑的。\n\n我的家境还算优渥，从小就在父母和长辈的呵护下长大。身边接触到的亲戚、同学和朋友，也全都是讲道理、有礼貌的人。当然，通过新闻或网络，我也知道这个世界并不太平——但我过去一直坚信，所有的恶意背后总有原因可循、总归有道理可讲。\n\n直到那天……在电车站。\n\n那天我和往常一样站在月台上等车，低头刷着手机。毫无征兆地，侧后方突然传来一股极大的撞击力，撞得我整个人猛地往前一栽。几乎就在同时，进站的电车带着巨响从我面前呼啸而过。\n\n虽然……我当时离轨道还有一段安全距离，并没有真的遇到危险，连擦伤都没有。但那一刻刮过脸颊的狂风，还有胸口半天压不下去的悸动，让我第一次真切地感觉到：原来死亡可以离自己这么近。\n\n等我稳住身体回头看时，撞我的人早已混在人流里消失得无影无踪。然而背上那阵尖锐的痛感告诉我，这绝不是无意的擦碰——对方是有着明确目标，蓄意用手肘狠狠砸在我背上的。\n\n我在网上查了才知道，这种专门冲撞陌生路人的行为居然不是个例，甚至多到被冠上了\u201c撞人族\u201d的名号。说实话，这件事给我带来的心理冲击，可能比\u201c接近死亡\u201d本身还要大。原来这个世界上的恶意，并不都是有逻辑的。\n\n从那以后，我收集了大量相关的新闻和资料。除了撞人族，竟然还有那么多向无辜路人发泄恶意的勾当：小到在超市捏碎方便面、在寿司店舔酱油瓶，大到池田小学袭击案、秋叶原随机杀人案……我一遍又一遍地翻看那些案件细节和所谓的专家解读，可那些字句怎么也进不到我脑子里。我完全无法理解，为什么会有人产生\u201c报复社会\u201d这种荒谬的逻辑。\n\n上大学和读研期间，我私下里一直在琢磨这种心理，甚至试着用报复社会者的视角拍摄了《当代艺术》。而在这个过程中，我碰到了另一件、或者说另一个让我感到震惊的人。\n\n新井拓也，他是我的后辈，也和我在同一个交友圈子里。在我为数不多和朋友提到这件事的经历中，只有他，会带着极度露骨的不屑，大言不惭地发表谬论。\n\n他说，报复社会的动机本就来自这个社会，是有迹可循的。所以这不过是一种\u201c有压迫就有反抗\u201d的自然反应罢了。他怎么能面不改色地说出这种话？\n\n现在想想，在我看过的众多案例里，总有那么一类缺乏基本常识、玩世不恭的人。他们平日里嬉皮笑脸，对不关心的事嗤之以鼻，一旦遇到点不顺心，又会爆发出极端的破坏欲……如果说有些人是因为走投无路才选择报复社会，那么像新井这种人，或许就是所谓的\u201c天生反社会者\u201d。\n\n我会继续盯着他的。",
      bytes: 0,
      lastOpened: "2026年8月10日 23:40"
    };

    const ySuperPukuDoc = {
      id: "yanagi-superpuku",
      type: "special",
      name: "SUPER噗咚",
      content: "",
      bytes: 0,
      lastOpened: "--"
    };

    function showSuperPukuDialog() {
      const overlay = document.createElement("div");
      overlay.className = "spuku-overlay";
      const dialog = document.createElement("div");
      dialog.className = "spuku-dialog";
      dialog.innerHTML = `<div class="spuku-dialog-body"><img class="spuku-dialog-img" src="/step2/images/pukupon_excited.png" alt="pukupon"><div class="spuku-dialog-text"><p>[JP] ぷくぽんのインターネット接続を許可しますか？</p><p>[EN] Allow Pukupon to access the internet?</p><p>[ZH] 是否同意 噗咚 接入互联网？</p></div></div><div class="spuku-dialog-actions"><button class="spuku-btn spuku-btn-yes" type="button">Yes</button><button class="spuku-btn spuku-btn-no" type="button">No</button></div>`;
      overlay.appendChild(dialog);
      document.body.appendChild(overlay);

      dialog.querySelector(".spuku-btn-no").addEventListener("click", () => {
        dialog.querySelector(".spuku-dialog-img").src = "/step2/images/pukupon_gaze2.png";
        dialog.classList.add("spuku-dialog-denied");
        window.setTimeout(() => overlay.remove(), 1500);
      });

      dialog.querySelector(".spuku-btn-yes").addEventListener("click", () => {
        overlay.remove();
        showWarningDialog();
      });
    }

    function showWarningDialog() {
      const overlay = document.createElement("div");
      overlay.className = "spuku-overlay";
      const dialog = document.createElement("div");
      dialog.className = "spuku-dialog";
      dialog.innerHTML = `<div class="spuku-dialog-body"><img class="spuku-dialog-img" src="/step2/images/warning.png" alt="warning"><div class="spuku-dialog-text"><p>[JP] このファイルにはリスクが存在します。未知のデバイスに接続する可能性があるため、ご注意ください。</p><p>[EN] WARNING: This file carries potential risks. It may attempt to connect to unknown devices.</p><p>[ZH] 警告： 该文件存在安全风险，可能会尝试连接未知设备，请谨慎操作。</p></div></div><div class="spuku-dialog-actions"><button class="spuku-btn spuku-btn-yes" type="button">Yes</button><button class="spuku-btn spuku-btn-no" type="button">No</button></div>`;
      overlay.appendChild(dialog);
      document.body.appendChild(overlay);

      const trigger = () => {
        dialog.querySelectorAll(".spuku-btn").forEach((b) => { b.disabled = true; });
        startClione(overlay);
      };

      dialog.querySelector(".spuku-btn-yes").addEventListener("click", trigger);
      dialog.querySelector(".spuku-btn-no").addEventListener("click", (event) => {
        const button = event.currentTarget;
        button.textContent = "Yes";
        button.classList.remove("spuku-btn-no");
        button.classList.add("spuku-btn-yes");
        dialog.querySelectorAll(".spuku-btn").forEach((b) => { b.disabled = true; });
        window.setTimeout(() => {
          button.classList.add("is-click-feedback");
          window.setTimeout(() => {
            button.classList.remove("is-click-feedback");
            trigger();
          }, 180);
        }, 120);
      });
    }

    function startClione(overlay) {
      let count = 0;
      const dialogImage = overlay.querySelector(".spuku-dialog-img");
      let showCannibal = false;
      if (dialogImage) dialogImage.src = "/step2/images/pukupon_cake.png";
      const imageInterval = window.setInterval(() => {
        showCannibal = !showCannibal;
        if (dialogImage) dialogImage.src = showCannibal ? "/step2/images/pukupon_cannibal.png" : "/step2/images/pukupon_cake.png";
      }, 1000);
      window.setTimeout(() => {
        window.clearInterval(imageInterval);
        if (dialogImage) dialogImage.src = "/step2/images/pukupon_gaze2.png";
      }, 5000);

      const spawnClione = () => {
        if (count >= 100) return;
        const img = document.createElement("img");
        img.src = "/step2/images/clione.gif";
        img.className = "spuku-clione";
        img.style.left = Math.random() * 80 + 10 + "vw";
        img.style.top = Math.random() * 80 + 10 + "vh";
        overlay.appendChild(img);
        animateClione(img);
        count++;
      };
      spawnClione();
      const interval = window.setInterval(() => {
        if (count >= 100) { window.clearInterval(interval); return; }
        spawnClione();
      }, 500);

      const dialog = overlay.querySelector(".spuku-dialog");
      const actions = dialog.querySelector(".spuku-dialog-actions");
      window.setTimeout(() => {
        actions.innerHTML = `<button class="spuku-btn spuku-btn-yes" type="button">打开噗咚（满血版）</button>`;
        actions.querySelector(".spuku-btn-yes").addEventListener("click", () => {
          window.clearInterval(interval);
          window.location.href = "superpukupon.html";
        });
      }, 6000);
    }

    function animateClione(el) {
      const move = () => {
        const x = Math.random() * 80 + 10;
        const y = Math.random() * 80 + 10;
        el.style.transition = `left ${0.8 + Math.random() * 1.2}s ease-in-out, top ${0.8 + Math.random() * 1.2}s ease-in-out`;
        el.style.left = x + "vw";
        el.style.top = y + "vh";
      };
      move();
      const id = window.setInterval(move, 1000 + Math.random() * 800);
      el.dataset.intervalId = id;
    }

    function initYanagihara() {
      const duplicateYanagiharaLine = "\n\n新井拓也，他是我的后辈，也在同一个交友圈子里。在我为数不多跟朋友提起撞人这件事的经历里，唯独他，带着那种极其露骨的不屑，大言不惭地发表着他的高论。";
      const cachedDocs = yGetDocs()
        .filter((doc) => !(doc.name === "2026-08-12录音" || doc.id === "yanagi-20260812"))
        .map((doc) => {
          if (doc.id !== "yanagi-20260810") return doc;
          return Object.assign({}, doc, {
            content: String(doc.content || "").replace(duplicateYanagiharaLine, ""),
            editedHtml: doc.editedHtml ? String(doc.editedHtml).replace(duplicateYanagiharaLine.replace(/\n\n/g, "<br><br>"), "") : doc.editedHtml
          });
        });
      const userDocs = cachedDocs.filter((doc) => !["yanagi-20260803", yDefaultDoc.id, ySuperPukuDoc.id].includes(doc.id));
      const currentDefault = cachedDocs.find((doc) => doc.id === yDefaultDoc.id || doc.id === "yanagi-20260803");
      const normalizedDefault = Object.assign({}, yDefaultDoc, currentDefault ? { editedHtml: currentDefault.editedHtml } : {});
      ySaveDocs([...userDocs, normalizedDefault, Object.assign({}, ySuperPukuDoc)]);

      const list = document.getElementById("yanagiharaDocsList");
      const add = document.getElementById("yanagiharaDocsAdd");
      const addMenu = document.getElementById("yanagiharaDocsAddMenu");
      const upload = document.getElementById("yanagiharaDocsUpload");
      const reset = document.getElementById("yanagiharaDocsReset");

      const docEditorStyles = `*{box-sizing:border-box;margin:0}body{background:#525659;display:flex;justify-content:center;padding:40px 20px;min-height:100vh}article{width:816px;min-height:1056px;padding:96px 72px;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,0.3);font:15px/2.4 "Microsoft YaHei","Noto Sans SC",Arial,sans-serif;color:#202124;word-break:break-word;outline:none;white-space:pre-wrap;letter-spacing:0.03em}img{max-width:100%;height:auto}.page-number{position:fixed;right:20px;bottom:20px;z-index:1000;padding:6px 12px;border-radius:999px;color:#fff;background:#000;box-shadow:0 4px 14px rgba(0,0,0,.24);font:700 14px/1.2 Arial,sans-serif;letter-spacing:.02em;white-space:nowrap;pointer-events:none}`;
      const buildEditorPage = (title, bodyContent, docId) => {
        const pageNumber = docId === "yanagi-20260810" ? '<div class="page-number" aria-label="页面进度">stepⅡ 15/19</div>' : "";
        return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>${title}</title><style>${docEditorStyles}</style></head><body><article contenteditable="true">${bodyContent}</article>${pageNumber}<script>var saved=false;var article=document.querySelector("article");window.addEventListener("beforeunload",function(e){if(!saved){e.preventDefault();e.returnValue=""}});window.addEventListener("keydown",function(e){if((e.ctrlKey||e.metaKey)&&e.key==="s"){e.preventDefault();doSave()}});function doSave(){saved=true;var data={araiDocSave:true,docId:"${docId}",storeKey:"${yDocsKey}",html:article.innerHTML};if(window.opener){window.opener.postMessage(data,"*")}if(window.parent&&window.parent!==window){window.parent.postMessage(data,"*")}}window.addEventListener("unload",function(){if(!saved){doSave()}});<\/script></body></html>`;
      };

      window.addEventListener("message", (event) => {
        if (!event.data || !event.data.araiDocSave || event.data.storeKey !== yDocsKey) return;
        const ds = yGetDocs();
        const d = ds.find((item) => item.id === event.data.docId);
        if (!d) return;
        d.editedHtml = event.data.html;
        ySaveDocs(ds);
      });

      const openDoc = (id) => {
        if (id === "yanagi-superpuku") { showSuperPukuDialog(); return; }
        const ds = yGetDocs(); const d = ds.find((item) => item.id === id); if (!d) return;
        d.lastOpened = nowLabel(); ySaveDocs(ds); render();
        let body = "";
        if (d.editedHtml) { body = d.editedHtml; }
        else if (d.dataUrl && d.dataUrl.startsWith("data:image")) { body = `<img src="${d.dataUrl}" alt="${escapeHtml(d.name)}">`; }
        else if (d.dataUrl) { body = escapeHtml(d.textContent || d.name); }
        else { body = (d.content || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\n/g,"<br>"); }
        const title = escapeHtml(d.name);
        const page = buildEditorPage(title, body, d.id);
        openEditorPage(page, title);
      };
      const removeDoc = (id) => { ySaveDocs(yGetDocs().filter((d) => d.id !== id)); render(); };
      const renameDoc = (id) => { const ds = yGetDocs(); const d = ds.find((item) => item.id === id); if (!d) return; const n = window.prompt("请输入新的文档名称", d.name); if (!n||!n.trim()) return; d.name = n.trim(); ySaveDocs(ds); render(); };
      const restoreDocs = () => {
        ySaveDocs([Object.assign({}, yDefaultDoc), Object.assign({}, ySuperPukuDoc)]);
        addMenu.hidden = true;
        render();
      };

      reset.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        restoreDocs();
      });

      function render() {
        const ds = yGetDocs();
        if (!ds.length) { list.innerHTML = '<p class="arai-docs-empty">暂无文档。</p>'; return; }
        list.innerHTML = ds.map((d) => `<article class="arai-docs-row" data-doc-id="${d.id}"><span class="arai-docs-icon"><img src="/step2/images/${d.id === "yanagi-superpuku" ? "icon-exe.png" : "icon-file.png"}" alt="${d.id === "yanagi-superpuku" ? "程序" : "文档"}"></span><span class="arai-docs-name" data-doc-open>${escapeHtml(d.name)}</span><button class="arai-docs-more" type="button" data-doc-more aria-label="更多操作">⋮</button><div class="arai-docs-menu" hidden><button type="button" data-doc-rename>重命名</button><button type="button" data-doc-delete>删除</button><button type="button" data-doc-newtab>在新标签页打开</button></div></article>`).join("");
      }

      list.addEventListener("click", (event) => {
        const row = event.target.closest("[data-doc-id]"); if (!row) return; const id = row.dataset.docId;
        if (event.target.closest("[data-doc-open]")||event.target.closest("[data-doc-newtab]")) { openDoc(id); return; }
        if (event.target.closest("[data-doc-rename]")) { renameDoc(id); return; }
        if (event.target.closest("[data-doc-delete]")) { removeDoc(id); return; }
        if (event.target.closest("[data-doc-more]")) { list.querySelectorAll(".arai-docs-menu").forEach((m) => { if (m !== row.querySelector(".arai-docs-menu")) m.hidden = true; }); const menu = row.querySelector(".arai-docs-menu"); if (menu) menu.hidden = !menu.hidden; }
      });
      document.addEventListener("click", (event) => { if (!event.target.closest(".arai-docs-row")) list.querySelectorAll(".arai-docs-menu").forEach((m) => { m.hidden = true; }); if (!event.target.closest("#yanagiharaDocsAdd")&&!event.target.closest("#yanagiharaDocsAddMenu")) addMenu.hidden = true; });
      add.addEventListener("click", (event) => { event.stopPropagation(); addMenu.hidden = !addMenu.hidden; });
      addMenu.addEventListener("click", (event) => { const action = event.target.dataset.docAction; if (action === "new") { const ds = yGetDocs(); ds.unshift({ id:`doc-${Date.now()}`,type:"blank",name:"未命名文档",content:"",bytes:0,lastOpened:"--" }); ySaveDocs(ds); addMenu.hidden = true; render(); } if (action === "upload") { upload.click(); addMenu.hidden = true; } });
      upload.addEventListener("change", () => { const files = Array.from(upload.files||[]); if (!files.length) return; const ds = yGetDocs(); const sel = files.reduce((s,f) => s+f.size, 0); if (totalBytes(ds)+sel > maxBytes) { window.alert("上传失败：文件总大小不能超过 2MB。"); upload.value = ""; return; } let rem = files.length; files.forEach((file) => { const isImg = file.type.startsWith("image/"); const id = `file-${Date.now()}-${Math.random().toString(16).slice(2)}`; if (isImg) { const r = new FileReader(); r.onload = () => { ds.unshift({id,type:"file",name:file.name,dataUrl:r.result,bytes:file.size,lastOpened:"--"}); rem--; if (!rem){ySaveDocs(ds);upload.value="";render();} }; r.readAsDataURL(file); } else { const r = new FileReader(); r.onload = () => { ds.unshift({id,type:"file",name:file.name,textContent:r.result,bytes:file.size,lastOpened:"--"}); rem--; if (!rem){ySaveDocs(ds);upload.value="";render();} }; r.readAsText(file); } }); });
      render();
    }

    if (localStorage.getItem(yPassedKey) === "1") {
      gate.remove();
      inner.hidden = false;
      initYanagihara();
    }
  };

  if (document.getElementById("pukuChat")) setupIndexPlugin();
  if (document.body.classList.contains("record-page")) setupRecordPlugin();
  if (document.body.classList.contains("arai-docs-page")) setupDocsPlugin();
  if (document.getElementById("yanagiharaGate")) setupYanagiharaDocsPlugin();
})();
