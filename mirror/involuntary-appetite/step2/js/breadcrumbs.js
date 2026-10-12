(() => {
  const count = document.getElementById("breadcrumbCount");
  const imageA = document.getElementById("breadcrumbImageA");
  const imageB = document.getElementById("breadcrumbImageB");
  const text = document.getElementById("breadcrumbText");
  const form = document.getElementById("breadcrumbForm");
  const input = document.getElementById("breadcrumbInput");
  const message = document.getElementById("breadcrumbMessage");
  const questionNav = document.getElementById("breadcrumbQuestionNav");

  const questions = [
    {
      body: "我的学校在这里。虽然不如新宿，但██站也可以算得上一只吞吐人类的巨兽。有时在这里给交通卡充值，抬头望到那张密密麻麻的电车线路图时，我总会觉得一阵眩晕。不，不是老生常谈的“都市太大，而我太渺小”——而是每次仰望，都能从中找到几个我闻所未闻、听起来和东京的光鲜不沾边的小站名。但\"██\"这两个字，每天不知道要被多少人挂在嘴边。一张看似平等的线路图，实则有着精心安排的等级。我只觉得这只巨兽在对我说：要么一鸣惊人，要么沉沦。",
      answers: ["池袋", "いけぶくろ", "ikebukuro"]
    },
    {
      body: "大多数早晨，我都会准时出现在这里，坐扶梯上楼、刷卡出闸机——然后瞥一眼墙上的广告，再匆匆走向换乘的站台。周遭的装潢和广告换了又换，只有那张海报没有改变。我从这里经过了多少次，它就在那里静静守候了我多少次。到现在，我对它竟产生了一种奇妙的伙伴心理，但同时涌上心头的，还有深深的厌恶感。我的人生就像这张海报，好像不会再有任何变化了。我想要快点摆脱它，快点证明自己和它不一样。",
      answers: ["东新宿", "東新宿", "ひがししんじゅく", "higashishinjuku", "higashi-shinjuku"]
    },
    {
      body: "我的学校在这里。虽然不如新宿，但██站也可以算得上一只吞吐人类的巨兽。有时在这里给交通卡充值，抬头望到那张密密麻麻的电车线路图时，我总会觉得一阵眩晕。不，不是老生常谈的“都市太大，而我太渺小”——而是每次仰望，都能从中找到几个我闻所未闻、听起来和东京的光鲜不沾边的小站名。但\"██\"这两个字，每天不知道要被多少人挂在嘴边。一张看似平等的线路图，实则有着精心安排的等级。我只觉得这只巨兽在对我说：要么一鸣惊人，要么沉沦。",
      answers: ["池袋", "いけぶくろ", "ikebukuro"],
      countLabel: "①：03 / 05",
      imagePrefix: "breadcrumb----",
      prefill: "池袋",
      isTransition: true
    },
    {
      body: "这里原本对我来说很陌生，但每次有事来这里，留下的都是失败的记忆。\"很独特的想法\"——我已经分不清这算不算一句夸赞了。如果算，那为什么每当我满怀希望地介绍完自己的方案，得到了这句话后，紧接而来的只有冗长的婉拒说辞？是我太激进了吗？可如果不激进，又怎么能真正震慑人心？站台指示板上四个颜色各异的圆圈，却没有为这座车站带来应有的多彩未来。一种升腾而起的焦躁感包围着我。",
      answers: ["饭田桥", "飯田橋", "いいだばし", "iidabashi"]
    },
    {
      body: "站如其名，这里是为████服务的车站。当然，我和那里毫无关联，只是每周来附近做一次艺术工坊的助教。车站里的这幅《雅典学院》仿制品大概是为了配合周边的学院气氛，其粗劣程度却会令观者忍不住失笑吧。即便如此，敢做、能实现，就足以胜过现在的我了。雅典学院里站着的是人类智慧的象征，而艺术工坊的工作不要说象征了什么，连学习和长进都无法获得，只是一种机械的重复罢了。我何时也能人如其名，让自己的智慧被他人认可？",
      answers: ["东大前", "東大前", "とうだいまえ", "todaimae"]
    },
    {
      body: "不知道何时起，我养成了来这里闲逛的习惯。这里虽然离家很近，但总是挤满了喧闹、市井的人群，让曾经的我感到厌烦。虽然我并没有对他们改观，但，我开始学着思考这种心理。这里的每个人都在遵守着规则认真生活，为什么最终呈现在我眼中的，是一派平庸、喧嚣、非理智的景象呢？心中开始躁动，另一种声音很快在我耳畔响起：其实，不正常的是你。来的次数变多，我开始坦然接受这种观点，但随之而来的是另一种不安：一旦接受了它，那接下来呢？我会变成什么样？",
      answers: ["上野御徒町", "うえのおかちまち", "uenookachimachi", "ueno-okachimachi"]
    },
    {
      body: "我的家在这里。每每走出这个狭窄的闸机，我总会浮现出自己的单间小公寓。在大城市生活的人们，总是会在精神上把家、和离它最近的车站关联在一起。返回这个车站时会感到兴奋，踏入车站的瞬间就产生了回家的安心感。在我心中的也是相同的情感吗？可为什么，在安心和放松之外，总有一种炎炎夏日热雨般的焦躁，粘附在我的每一个角落？\n我的家不在这里。面包屑不会带我回家，我还有真正想要去到的地方。",
      answers: ["藏前", "蔵前", "くらまえ", "kuramae"]
    },
    {
      body: "我为什么会选择这个地方？不过是为了撒下最后一块面包屑的无奈之举。这里的上流社会与我无缘，街上弥漫着胜利者的傲慢，仿佛在用无形的屏障隔绝着一切不够优雅和从容的事物。这里甚至容不下一间连锁快餐店。可我却忽然意识到，我在这里承受的，都是自己的视线。是自己曾投向那些市井喧嚣的视线。原来并非我不正常，而是整个社会都处在一种悲哀的鄙夷连锁中吗？这给我带来了无可忍耐的愤怒。如果是这样，我宁愿选择不正常，选择成为异端。",
      answers: ["日本桥", "日本橋", "にほんばし", "nihonbashi"]
    }
  ];

  const progressStorageKey = "breadcrumbCompletedQuestions";
  const currentQuestionKey = "breadcrumbQuestion";
  let currentIndex = Number(sessionStorage.getItem(currentQuestionKey) || "0");
  if (currentIndex < 0 || currentIndex >= questions.length) currentIndex = 0;

  const completedQuestions = new Set((() => {
    try {
      return JSON.parse(localStorage.getItem(progressStorageKey) || "[]");
    } catch (error) {
      return [];
    }
  })());

  const saveCompletedQuestions = () => {
    localStorage.setItem(progressStorageKey, JSON.stringify(Array.from(completedQuestions).sort((a, b) => a - b)));
  };

  if (completedQuestions.size === 0) {
    const legacyProgress = Number(sessionStorage.getItem("breadcrumbMaxUnlocked") || "0");
    for (let i = 0; i < legacyProgress; i += 1) completedQuestions.add(i);
    saveCompletedQuestions();
  }

  const normalize = (value) => value.trim().toLowerCase().replace(/[\s\-・·.。駅站]/g, "");

  const normalQuestionsBefore = (index) => questions.slice(0, index).filter((question) => !question.isTransition).length;

  const getCountLabel = (index) => {
    const question = questions[index];
    if (question.countLabel) return question.countLabel;
    if (index < 5) return `①：${String(index + 1).padStart(2, "0")} / 05`;
    return `②：${String(index - 4).padStart(2, "0")} / 03`;
  };

  const getImagePrefix = (index) => {
    const question = questions[index];
    if (question.imagePrefix) return question.imagePrefix;
    return `breadcrumb${String(normalQuestionsBefore(index) + 1).padStart(2, "0")}-`;
  };

  const renderQuestionNav = () => {
    const buttons = [];

    if (currentIndex > 0) {
      buttons.push(`<button type="button" data-nav-question="${currentIndex - 1}">上一题</button>`);
    }

    if (currentIndex < questions.length - 1 && completedQuestions.has(currentIndex)) {
      buttons.push(`<button type="button" data-nav-question="${currentIndex + 1}">下一题</button>`);
    } else if (currentIndex === questions.length - 1 && completedQuestions.has(currentIndex)) {
      buttons.push('<button type="button" data-nav-home>下一题</button>');
    }

    questionNav.innerHTML = buttons.join("");
  };

  const renderQuestion = () => {
    const question = questions[currentIndex];
    const imagePrefix = getImagePrefix(currentIndex);

    count.textContent = getCountLabel(currentIndex);
    if (window.setPageNumber) window.setPageNumber(`stepⅠ ${currentIndex + 6}/21`);
    imageA.src = `/step2/images/Breadcrumbs/${imagePrefix}1.jpg`;
    imageB.src = `/step2/images/Breadcrumbs/${imagePrefix}2.jpg`;
    imageA.alt = `面包屑第 ${currentIndex + 1} 页线索图一`;
    imageB.alt = `面包屑第 ${currentIndex + 1} 页线索图二`;
    text.textContent = question.body;
    input.value = question.prefill || "";
    message.textContent = "";
    renderQuestionNav();
  };

  const goToQuestion = (index) => {
    if (index < 0 || index >= questions.length) return;
    currentIndex = index;
    sessionStorage.setItem(currentQuestionKey, String(currentIndex));
    renderQuestion();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  questionNav.addEventListener("click", (event) => {
    const homeButton = event.target.closest("[data-nav-home]");
    if (homeButton) {
      window.location.href = "breadcrumb-home.html";
      return;
    }

    const button = event.target.closest("[data-nav-question]");
    if (!button) return;
    goToQuestion(Number(button.dataset.navQuestion));
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    const guess = normalize(input.value);
    const isCorrect = questions[currentIndex].answers.some((answer) => normalize(answer) === guess);

    if (!isCorrect) {
      message.textContent = "你迷路了，或许应该看看电车路线图。";
      input.select();
      return;
    }

    completedQuestions.add(currentIndex);
    saveCompletedQuestions();

    currentIndex += 1;

    if (currentIndex >= questions.length) {
      sessionStorage.removeItem(currentQuestionKey);
      window.location.href = "breadcrumb-home.html";
      return;
    }

    sessionStorage.setItem(currentQuestionKey, String(currentIndex));
    renderQuestion();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  renderQuestion();
})();
