(() => {
  const launcher = document.getElementById("pukuLauncher");
  const panel = document.getElementById("pukuPanel");
  const closeButton = document.getElementById("pukuClose");
  const messages = document.getElementById("pukuMessages");
  const form = document.getElementById("pukuForm");
  const input = document.getElementById("pukuInput");
  const optionButtons = document.querySelectorAll("[data-question]");
  const optionsContainer = document.querySelector(".puku-options");
  const backendStorageKey = "pukuBackendUnlocked";
  const pukuImages = {
    normal: "/step2/images/pukupon.png",
    excited: "/step2/images/pukupon_excited.png",
    surprised: "/step2/images/pukupon_surprised.PNG",
    cake: "/step2/images/pukupon_cake.png",
    satisfied: "/step2/images/pukupon_satisfied.png",
    disappointed: "/step2/images/pukupon_disappointed.png",
    corrupted: "/step2/images/pukupon_hosho.png"
  };

  const randomHappy = () => Math.random() < 0.7 ? pukuImages.cake : pukuImages.satisfied;
  const resolveAssetUrl = (relativePath) => encodeURI(new URL(relativePath, location.origin + "/step2/").href);
  const launcherImage = launcher.querySelector("img");
  let corruptNextAnswer = false;

  const makeRecordLink = (keyword) => `<a href="record.html?keyword=${encodeURIComponent(keyword)}" class="puku-link" data-record-keyword="${keyword}" target="_blank" rel="noopener">会议记录</a>`;
  const pdfLink = (name, label) => `<a href="${encodeURI(new URL(name, location.origin + "/step2/").href)}" class="puku-link" target="_blank" rel="noopener noreferrer">${label}</a>`;
  const aboutLink = '<a href="index.html#about" class="puku-link">点击查看关于展览</a>';
  const artistButtons = `
    <div class="puku-inline-options">
      <button type="button" data-question="新井拓也">新井拓也</button>
      <button type="button" data-question="KAY">KAY</button>
      <button type="button" data-question="长谷川千景">长谷川千景</button>
      <button type="button" data-question="柳原准">柳原准</button>
      <button type="button" data-question="宋雯祺">宋雯祺</button>
    </div>`;

  const answers = [
    {
      keywords: ["寻木乃伊者反成木乃伊"],
      answer: `该词对应日本常用谚语「ミイラ取りがミイラになる」（直译：去搜寻木乃伊的人，自己最后也变成了木乃伊）。<br><br>【释义】 本义指原本出发去寻找、劝说或捕获某人，结果自己反而滞留不归，或反过来被对方同化、陷入了与对方完全相同的境地。<br><br>【语境拓展】 在戏剧文本与行为艺术的语境中，该词常用于展现一种“作茧自缚”或“被自身执念反噬”的荒诞结局。隐喻原本代表秩序、试图清理混乱的人，最终在对抗中跨越了界限，沦为了混乱的一部分。`
    },
    {
      keywords: ["达芬奇"],
      answer: `列奥纳多·达·芬奇（Leonardo da Vinci，儒略历1452年4月15日【公历4月23日】－1519年5月2日）是欧洲文艺复兴时期的顶级全才，被公认为人类历史上最伟大的天才之一。<br><br>达芬奇集画家、科学家、发明家、工程师、解剖学家、建筑师于一身，将艺术与科学的观察方法相结合。他在艺术领域的代表作有《蒙娜丽莎》、《最后的晚餐》、《岩间圣母》等。`
    },
    {
      keywords: ["B级片"],
      answer: `B级片（B-Movie） 最初指好莱坞黄金时代（1930—1950年代）作为“陪衬”播出的低预算电影。<br><br>如今，它泛指制作成本低、拍摄周期短、主打类型化与感官刺激的电影风格，并逐渐与邪典文化（Cult Film）划上等号。<br><br>噗咚不太清楚这些都是什么意思...但听说KAY哥哥很喜欢看呢！`
    },
    {
      keywords: ["银河电灯"],
      answer: `他好像是一位网页解谜游戏的制作者呢！不过很遗憾，噗咚只知道中文版的网站是由他来制作的，除此之外就没有更多信息了。<br><br>或许你可以从他的官网了解更多：<a href="https://ginga-light.top/" class="puku-link" target="_blank" rel="noopener">链接</a>`
    },
    {
      keywords: ["尸体模特", "肢体模特"],
      answer: `<a href="record.html?keyword=%E5%BD%95%E9%9F%B3" class="puku-link" data-record-keyword="录音" target="_blank" rel="noopener noreferrer" style="color:#8b1a1a">录音</a>`
    },
    {
      keywords: ["营业", "开馆", "开放", "时间"],
      answer: `本次展览由8月14日举办至8月30日，每日开放时间为10:00 - 16:00（每日15:30停止入场）。噗咚每天都在这里等你哦！`
    },
    {
      keywords: ["地点", "地址", "怎么去", "交通"],
      answer: `本次展览举办地为东京艺术实验空间「Gallery CROP」，您可以乘坐电车至【永田町】站，从9a出口步行2分钟即可到达。`
    },
    {
      keywords: ["This is So Contemporary"],
      answer: `《这太当代了》（This is So Contemporary）是艺术家提诺 · 赛格尔(Tino Sehgal) 于2005 年创作的一件幽默且荒诞的作品。它没有一件实体展品，全靠几个“真人保安”来完成。<br><br>当观众走进空无一物的展厅之后，一群工作人员（经过训练的保安）便突然围绕着他们开始跳舞，并大声唱到：OH! This is so contemporary, contemporary, contemporary......唱跳一段时间后，他们会瞬间静止，一本正经地报出艺术家名字和年份，随后恢复成严肃的保安站姿，仿佛一切没发生过。<br><br><img class="puku-inline-image" src="/step2/images/This-is-So-Contemporary.jpg" alt="This is So Contemporary"><br>这件作品模糊了艺术与生活的权力边界，是对消费主义和“当代艺术圈”的一次极致反讽。`
    },
    {
      keywords: ["宋芬奇", "芬奇老师"],
      answer: `呀，你连这个都知道！<br><br>“宋芬奇（Song・Vinci）”其实是大家给策展人宋雯祺姐姐起的外号啦！因为“雯祺”用日语读出来和达·芬奇的“芬奇（Vinci）”非常像，再加上她是这次艺术展的策展人，是团队的核心大脑地位，所以不知道谁开了个头之后，大家就都半开玩笑地尊称她“宋芬奇老师”了。`
    },
    {
      keywords: ["歌川国芳"],
      answer: `歌川国芳（1798年－1861年）是日本江户时代末期最具奇想色彩与现代感的大师级浮世绘画师。<br><br>国芳极其擅长打破传统的画框限制。在代表作《相马旧王城》中，他打破当时拼接多张版画的传统思路，将一整具巨大的解剖学骷髅横跨三张纸，带来震撼的电影远景透视感，对后世的妖怪漫画产生了极深远的影响。<br><br><img class="puku-inline-image" src="/step2/images/Princess-Takiyasha.jpg" alt="相马旧王城"><br>他还曾大力开发“寄生画”（用人物、猫咪、影绘等拼凑成文字或人像），创作了多幅充满诙谐色彩的视觉错误艺术作品。`
    },
    {
      keywords: ["阿尔钦博托", "Arcimboldo", "朱塞佩·阿尔钦博托", "朱塞佩阿尔钦博托"],
      answer: `朱塞佩·阿尔钦博托（Giuseppe Arcimboldo，1526年－1593年）是文艺复兴晚期极具传奇色彩的意大利宫廷画家，也是西方视觉错视与组合肖像画的鼻祖。<br><br>他最标志性的艺术风格，就是用水果、蔬菜、花卉、鱼类、甚至书籍等静物，拼凑成栩栩如生的人头肖像。无论是后世歌川国芳的“寄生画”，还是现代平面设计中常见的多联异构、错视艺术，都能看到阿尔钦博托早期奇想的影子。`
    },
    {
      keywords: ["永田町"],
      answer: `<a href="record.html?keyword=%E6%B0%B8%E7%94%B0%E7%94%BA" class="puku-link" data-record-keyword="永田町" target="_blank" rel="noopener">欢迎回家。</a>`
    },
    {
      keywords: ["无害穿刺"],
      answer: `噗咚找到了以下会议记录。<br><a href="record.html?keyword=%E6%97%A0%E5%AE%B3%E7%A9%BF%E5%88%BA" class="puku-link" data-record-keyword="无害穿刺" target="_blank" rel="noopener">会议记录</a>`
    },
    {
      keywords: ["特价清仓"],
      answer: `噗咚找到了以下会议记录。<br><a href="record.html?keyword=%E7%89%B9%E4%BB%B7%E6%B8%85%E4%BB%93" class="puku-link" data-record-keyword="特价清仓" target="_blank" rel="noopener">会议记录</a>`
    },
    {
      keywords: ["面包屑不会带我回家"],
      answer: `这是KAY制作的一组概念艺术作品。<br><br>在格林童话《糖果屋》的经典故事里，迷路的孩子在森林中沿途撒下面包屑，试图通过这些微小的标记，拼凑出一条通往归途的确定路线。<br><br>但在现代都市的错综网络中，方向与立足点往往变得更加难以捕捉。KAY将视角延伸到了我们最熟悉的日常场景——地铁站，KAY用极其私人且真诚的镜头，记录下了自己在这座城市生活、学习与创作期间，走过的七个真实坐标。<br><br>这部作品并不试图给现代人的都市生活提供一个标准答案，它更像是一封公开的个人日记：邀请每一位观者跟随这些由照片和文字连成的“面包屑”，共同去经历一场关于寻找自我、试探边界，并最终接纳真实内心的精神旅程。`
    },
    {
      keywords: ["糖果屋"],
      answer: `《糖果屋》（德语：Hänsel und Gretel，又译《韩塞尔与葛雷特》）是《格林童话》中最著名的经典故事之一，讲述了一对可怜的兄妹用智慧战胜巫婆、寻找回家之路的冒险历程。<br><br>故事中，一对亲生兄妹俩（韩塞尔与葛雷特）因饥荒而被父亲和继母遗弃，第一次他们凭借沿途丢下白石子，顺着月光找到了回家的路；但第二次，他们只能用面包屑做标记，结果全被森林里的鸟儿吃掉了。`
    },
    {
      keywords: ["冰海天使"],
      answer: `哇！你对噗咚的原型很好奇吗？<br><br>冰海天使是生活在冰冷海水里、身体半透明的小生物，只有人类小拇指一节那么大。它们游动时拍动着两翼，透明的身体中央有着像心脏一样火红的消化器官，看起来非常梦幻、就像传说中的天使。<br><br>噗咚能诞生于这种可爱的小生物，感觉非常的幸福！顺带一提，“噗咚”的名字也是在模拟冰海天使在<span class="puku-wave-text">水中游动</span>的声音哦。`
    },
    {
      keywords: ["草莓蛋糕"],
      answer: `草莓蛋糕可是噗咚在这个世界上最最最喜欢的东西了！松软的奶油、甜甜的蛋糕胚，上面再缀一颗红红的草莓……呜哇，光是想想，噗咚的口水就要流下来了。<br><br>多亏长谷川姐姐的立绘、和KAY哥哥的设定，现在只要我回答问题，就可以进入“吃蛋糕”的状态。噗咚还想吃更多的蛋糕！请多多向我发送问题吧！`
    },
    {
      keywords: ["crop"],
      answer: `Gallery CROP 是一间以现代极简为基调的独立艺术画廊，也是本次《非自愿摄入》展的举办地。<br><br>"CROP"，意指对图像与照片的裁剪。Gallery CROP 相信，裁剪与选定本身即是一种创作；画廊所能给予的是一个充满可能性的艺术空间，而余下的工作，交给走进来的每一个人。`
    },
    {
      keywords: ["购票", "票价", "门票", "价格", "多少钱", "学生票", "优惠"],
      answer: `票价：成年人 800日元  /  学生 400日元  /  学龄前儿童 免费<br><br>本次展览无线上售票渠道，仅支持现场购票。如需购买学生票，请在购票时出示相关有效证件。`
    },
    {
      keywords: ["拍照", "录像", "闪光灯", "三脚架"],
      answer: `展厅内部允许拍照及录像。为避免影响其他观众的观展体验，在拍照时请勿开启闪光灯、请勿使用三脚架等专业设备。`
    },
    {
      keywords: ["离场", "出去", "二次", "中途", "再次"],
      answer: `本次展览的门票为单次入场有效，离场后不得再次入场。展厅内没有设置洗手间，请您合理安排好观展时间。`
    },
    {
      keywords: ["洗手间", "厕所", "卫生间"],
      answer: `展厅内没有设置洗手间，请您合理安排好观展时间。`
    },
    {
      keywords: ["饮", "食", "茶", "水", "吃", "喝"],
      answer: `展会期间除瓶装饮料外，谢绝携带任何食物进入展厅。补充水分时，请和展品保持一定距离。感谢您的配合与理解。`
    },
    {
      keywords: ["便签"],
      answer: `噗咚找到了以下内容：<br><a href="record.html?keyword=${encodeURIComponent("便签")}" class="puku-link" data-record-keyword="便签" target="_blank" rel="noopener">照片</a>`
    },
    {
      keywords: ["吉祥物制作", "吉祥物", "制作噗咚"],
      answer: `噗咚找到了以下内容：<br>${makeRecordLink("吉祥物制作")}`
    },
    {
      keywords: ["浅野慧", "浅野 慧", "asano kei"],
      answer: `噗咚找到了以下内容：<br>${makeRecordLink("浅野慧")}`
    },
    {
      keywords: ["噗咚是什么", "噗咚", "puku-pon", "pukupon", "puku pon"],
      answer: `你好！我的名字叫做噗咚（Puku-Pon），是长谷川千景姐姐以真实存在的生物“<b>冰海天使</b>（Clione）”为原型设计出来的。<br><br>噗咚最大的爱好就是吃东西，尤其喜欢吃<b>草莓蛋糕</b>！虽然我被选作了《非自愿摄入》的吉祥物，但我对美食的追求都是自愿的哦！<br><br>顺便告诉你一个秘密：我现在说的这些人类语言和观展信息，全都是参展的几位艺术家哥哥姐姐们提前教给我的！如果你想更了解他们，可以直接在下方输入他们的名字（KAY、长谷川千景、新井拓也、柳原准、宋雯祺）来问我~`
    },
    {
      keywords: ["非自愿摄入", "involuntary appetite", "展览是什么", "本次展览", "美术展", "艺术展"],
      answer: `《非自愿摄入》（Involuntary Appetite）是一个探讨当代消费社会本质的小型独立美术展。在信息泛滥的当下，我们每天都在被动地接收、消费着各种庞杂的内容。本次展览通过五位年轻艺术家的独特视角，以多样的视觉语言来解构、反思这一社会现状。<br><br>你可以直接在以下链接查看有关本次展览的详细介绍。<br>${aboutLink}`
    },
    {
      keywords: ["介绍一下本次参展的艺术家们", "艺术家", "参展", "创作者", "团队"],
      answer: `本次参展的艺术家团队包括以下五位成员，<br>输入任意一位创作者的姓名，噗咚就会为你找出更详细的介绍哦。${artistButtons}`
    },
    {
      keywords: ["kay", "KAY"],
      answer: `KAY，24岁，视觉传达设计专业硕士研究生。<br><br>他在艺术创作中热衷于探讨营销与包装的价值，认为在现代社会中，一件艺术品的视觉包装和传播形式本身就极具意义。作为本次展览的技术主导之一，他不仅负责视觉概念的输出，还一手搭建了本次展览的线上网页端与数字化呈现。<br><br>※KAY的个人官网也推出了中文版喔：<a href="kay.html" class="puku-link" target="_blank" rel="noopener">链接</a>`
    },
    {
      keywords: ["长谷川千景", "长谷川", "hasegawa", "chikage"],
      answer: `长谷川千景（Hasegawa Chikage）23岁，跨媒体艺术专业硕士研究生。<br><br>她的创作风格细腻、敏感且内敛。长谷川常将镜头和艺术视角对准现代都市生活，擅长捕捉人们在面对繁华都市和他人目光时，内心产生的孤独、压力与自我消耗，并将其转化为独特的跨媒体空间语言。`
    },
    {
      keywords: ["新井拓也", "新井", "arai", "takuya"],
      answer: `新井拓也（Arai Takuya）23岁，当代雕塑专业硕士研究生。<br><br>他的创作充满了实验精神，喜欢打破常规常识。新井习惯站在不随大流的边缘视角去观察社会，善于在大家都赞同的宏大语境中发掘不一样的思维维度，并通过雕塑来冷静展现对非传统观念的思考。`
    },
    {
      keywords: ["柳原准", "柳原", "yanagihara", "jun"],
      answer: `柳原准（Yanagihara Jun）24岁，摄影专业硕士研究生。他的创作聚焦于人与外界的心理安全边界。柳原热衷于通过空间装置来探讨个人“舒适区”的建立，并将人类面对未知社会危机、复杂人际关系时的防卫心理具体地呈现出来，尝试在秩序与无序之间建立对话。`
    },
    {
      keywords: ["宋雯祺", "宋", "song", "wenqi"],
      answer: `宋雯祺（Song Wenqi）<br>毕业于油画专业的独立策展人。长期活跃于艺术界，热衷于在混乱与无序中发掘独特的美感，并致力于发掘、培育有潜力的青年艺术新星。<br><br>本次美术展正是由她一手统筹策划，并联合KAY、长谷川千景、新井拓也、柳原准四位创作者共同促成落地的关于噗咚的后续，我准备采纳KAY之前的意见，逐步把它训练成一个能自主生成答案的真正AI。嗯，感觉很有意思，甚至它本身就可以成为我们展览的一部分——它也在“非自愿摄入”我们提供的语料。从今天这期会议开始，后续开会的内容都会自动语音转文字，作为原始语料提供给噗咚的数据库。KAY，后续的训练就交给你了。大家在开会交流时还是正常发言，不用特意去迁就噗咚。”`
    }
  ];

  const normalizeChineseKeyword = (value) => {
    const phrases = [
      ["屍體模特", "尸体模特"], ["肢體模特", "肢体模特"], ["開館", "开馆"], ["開放", "开放"], ["時間", "时间"], ["怎麼去", "怎么去"],
      ["老師", "老师"], ["國芳", "国芳"], ["阿爾欽博托", "阿尔钦博托"], ["無害穿刺", "无害穿刺"], ["特價清倉", "特价清仓"],
      ["麵包屑不會帶我回家", "面包屑不会带我回家"], ["購票", "购票"], ["門票", "门票"], ["價格", "价格"], ["多少錢", "多少钱"],
      ["學生票", "学生票"], ["優惠", "优惠"], ["錄像", "录像"], ["閃光燈", "闪光灯"], ["三腳架", "三脚架"],
      ["離場", "离场"], ["洗手間", "洗手间"], ["廁所", "厕所"], ["衛生間", "卫生间"], ["便籤", "便签"], ["便簽", "便签"],
      ["吉祥物製作", "吉祥物制作"], ["製作噗咚", "制作噗咚"], ["淺野慧", "浅野慧"], ["長谷川千景", "长谷川千景"], ["長谷川", "长谷川"],
      ["柳原準", "柳原准"], ["非自願攝入", "非自愿摄入"], ["展覽", "展览"], ["美術展", "美术展"], ["藝術展", "艺术展"],
      ["介紹", "介绍"], ["參展", "参展"], ["創作者", "创作者"], ["團隊", "团队"], ["東京", "东京"], ["線路圖", "线路图"],
      ["運行", "运行"], ["語音", "语音"], ["記錄", "记录"], ["會議", "会议"], ["搜尋", "搜索"], ["檢索", "检索"],
      ["飲", "饮"], ["淺", "浅"], ["價", "价"], ["倉", "仓"], ["錄", "录"]
    ];
    return phrases.reduce((text, pair) => text.replaceAll(pair[0], pair[1]), value);
  };

  const normalize = (value) => normalizeChineseKeyword(value.trim().toLowerCase());

  const ensureBackendButton = () => {
    if (!optionsContainer || localStorage.getItem(backendStorageKey) !== "true" || optionsContainer.querySelector(".puku-backend-button")) return;

    const link = document.createElement("a");
    link.className = "puku-backend-button";
    link.href = "record.html";
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "进入后台";
    optionsContainer.appendChild(link);
  };

  const unlockBackend = () => {
    localStorage.setItem(backendStorageKey, "true");
    ensureBackendButton();
  };

  const findAnswer = (question) => {
    const normalized = normalize(question);
    let bestMatch = null;

    answers.forEach((item, answerIndex) => {
      item.keywords.forEach((keyword) => {
        const position = normalized.indexOf(normalize(keyword));
        if (position === -1) return;

        if (!bestMatch || position < bestMatch.position || (position === bestMatch.position && answerIndex < bestMatch.answerIndex)) {
          bestMatch = { item, position, answerIndex };
        }
      });
    });

    return bestMatch?.item;
  };

  const responseDelay = (html) => {
    const plainText = html.replace(/<[^>]*>/g, "");
    return Math.min(1300, Math.max(200, 200 + plainText.length * 3.4));
  };

  const getBotImage = (match) => {
    if (!match) return pukuImages.disappointed;
    if (match.answer.includes("data-record-keyword")) return pukuImages.surprised;
    return randomHappy();
  };

  const scrollToLatest = () => {
    messages.scrollTop = messages.scrollHeight;
  };

  const openImagePreview = (image) => {
    const overlay = document.createElement("div");
    overlay.className = "puku-image-preview";
    overlay.innerHTML = `<button type="button" aria-label="关闭图片预览">×</button><img src="${image.src}" alt="${image.alt || "图片预览"}">`;
    document.body.appendChild(overlay);

    overlay.addEventListener("click", (event) => {
      if (event.target === overlay || event.target.closest("button")) {
        overlay.remove();
      }
    });
  };

  const escapeHtml = (value) => value.replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  }[char]));

  const corruptPlainText = (text) => {
    const bytes = new TextEncoder().encode(text);
    return Array.from(bytes).map((byte) => String.fromCharCode(byte)).join("");
  };

  const corruptHtml = (html) => {
    const template = document.createElement("template");
    template.innerHTML = html;
    const walker = document.createTreeWalker(template.content, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      node.nodeValue = corruptPlainText(node.nodeValue || "");
      node = walker.nextNode();
    }
    return template.innerHTML;
  };

  const playWrongSound = () => {
    const audio = new Audio("/step2/images/wrong.mp3");
    audio.play().catch(() => {});
  };

  const corruptionStorageKey = "pukuCorruptNextAnswer";
  window.pukuCorruption = {
    arm: () => {
      corruptNextAnswer = true;
      localStorage.setItem(corruptionStorageKey, "true");
    },
    isPending: () => corruptNextAnswer || localStorage.getItem(corruptionStorageKey) === "true",
    consume: () => {
      if (!window.pukuCorruption.isPending()) return false;
      corruptNextAnswer = false;
      localStorage.removeItem(corruptionStorageKey);
      return true;
    },
    corruptHtml,
    playWrongSound,
    image: pukuImages.corrupted
  };

  const corruptAddedReply = (message) => {
    if (!(message instanceof Element) || message.classList.contains("puku-typing-message")) return;
    if (!message.matches(".puku-message.bot") || !window.pukuCorruption.consume()) return;
    const bubble = message.querySelector(".puku-bubble");
    const avatar = message.querySelector(".puku-avatar");
    if (bubble) bubble.innerHTML = corruptHtml(bubble.innerHTML);
    if (avatar) avatar.src = pukuImages.corrupted;
    playWrongSound();
  };

  const replyObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof Element)) return;
        corruptAddedReply(node);
        node.querySelectorAll?.(".puku-message.bot:not(.puku-typing-message)").forEach(corruptAddedReply);
      });
    });
  });
  replyObserver.observe(messages, { childList: true, subtree: true });

  const step2ReservedQuestion = (question) => {
    if (window.pukuStep2Released) return false;
    const normalized = normalizeChineseKeyword(question.trim().toLowerCase());
    return normalized.includes("新井是怎么死的") ||
      normalized.includes("新井拓也是怎么死的") ||
      normalized.includes("一路人") ||
      normalized.includes("螺丝") ||
      normalized.includes("自动抓取") ||
      normalized.includes("野良犬") ||
      normalized.includes("野狗") ||
      normalized.includes("正义") ||
      normalized.includes("汉顿") ||
      normalized.includes("survey-done-k7m2") ||
      normalized.includes("survey-done-9xp4") ||
      (normalized.includes("当代艺术") && (normalized.includes("柳原") || normalized.includes("四年级"))) ||
      (normalized.includes("金泽") && (normalized.includes("柳原") || normalized.includes("21世纪")));
  };

  const unknownResponse = (text) => `抱歉，噗咚的缓存中没有‘${escapeHtml(text)}’相关的知识。在噗咚满血复活之前，要不要先换个词问问看？`;

  const addUserMessage = (text) => {
    const message = document.createElement("article");
    message.className = "puku-message user";
    message.innerHTML = `<div class="puku-bubble">${escapeHtml(text)}</div>`;
    messages.appendChild(message);
  };

  const rememberDisplayedRecordLinks = (root) => {
    const storageKey = "pukuRecordDiscoveredKeywordsV2";
    const discovered = JSON.parse(localStorage.getItem(storageKey) || "[]");
    root.querySelectorAll("[data-record-keyword]").forEach((link) => {
      const keyword = normalizeChineseKeyword(link.dataset.recordKeyword);
      if (!discovered.includes(keyword)) discovered.push(keyword);
    });
    localStorage.setItem(storageKey, JSON.stringify(discovered));
    if (root.querySelector("[data-record-keyword]")) unlockBackend();
  };

  const addBotMessage = (html, imageSrc = pukuImages.cake) => {
    const message = document.createElement("article");
    message.className = "puku-message bot";
    message.innerHTML = `<img class="puku-avatar" src="${imageSrc}" alt="噗咚"><div class="puku-bubble">${html}</div>`;
    messages.appendChild(message);
    rememberDisplayedRecordLinks(message);
  };

  const addTypingMessage = (imageSrc = pukuImages.cake) => {
    const message = document.createElement("article");
    message.className = "puku-message bot puku-typing-message";
    message.innerHTML = `<img class="puku-avatar" src="${imageSrc}" alt="噗咚"><div class="puku-bubble puku-typing"><span></span><span></span><span></span></div>`;
    messages.appendChild(message);
    scrollToLatest();
    return message;
  };

  const ask = (question) => {
    const trimmed = question.trim();
    if (!trimmed) return;

    addUserMessage(trimmed);

    if (step2ReservedQuestion(trimmed)) {
      const typing = addTypingMessage(pukuImages.disappointed);
      const response = unknownResponse(trimmed);
      window.setTimeout(() => {
        typing.remove();
        addBotMessage(response, pukuImages.disappointed);
        scrollToLatest();
      }, responseDelay(response));
      return;
    }

    if (trimmed.includes("观测者") || trimmed.includes("基站")) {
      const typing = addTypingMessage(pukuImages.disappointed);
      window.setTimeout(() => {
        typing.remove();
        addBotMessage("......", pukuImages.disappointed);
        scrollToLatest();
        window.setTimeout(() => {
          addBotMessage(unknownResponse(trimmed), pukuImages.corrupted);
          scrollToLatest();
          window.setTimeout(() => window.pukuCorruption.arm(), 0);
        }, 1500);
      }, 500);
      return;
    }

    const match = findAnswer(trimmed);
    const response = match ? match.answer : unknownResponse(trimmed);

    if (window.pukuCorruption.consume()) {
      playWrongSound();
      const typing = addTypingMessage(pukuImages.corrupted);
      window.setTimeout(() => {
        typing.remove();
        addBotMessage(window.pukuCorruption.corruptHtml(response), pukuImages.corrupted);
        scrollToLatest();
      }, responseDelay(response));
      return;
    }

    const botImage = getBotImage(match);
    const typing = addTypingMessage(botImage);

    window.setTimeout(() => {
      typing.remove();
      addBotMessage(response, botImage);
      scrollToLatest();
    }, responseDelay(response));
  };

  launcher.addEventListener("mouseenter", () => {
    if (launcherImage) launcherImage.src = pukuImages.excited;
  });

  launcher.addEventListener("mouseleave", () => {
    if (launcherImage) launcherImage.src = pukuImages.normal;
  });

  launcher.addEventListener("click", () => {
    if (launcherImage) launcherImage.src = pukuImages.normal;
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    launcher.classList.add("is-hidden");
    ensureBackendButton();
    input.focus();
  });

  closeButton.addEventListener("click", () => {
    if (launcherImage) launcherImage.src = pukuImages.normal;
    panel.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
    launcher.classList.remove("is-hidden");
  });

  optionButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      ask(button.dataset.question || button.textContent);
    });
  });

  messages.addEventListener("click", (event) => {
    const inlineImage = event.target.closest(".puku-inline-image");
    if (inlineImage) {
      openImagePreview(inlineImage);
      return;
    }

    const button = event.target.closest("[data-question]");
    if (button) {
      ask(button.dataset.question || button.textContent);
      return;
    }

    const recordLinkElement = event.target.closest("[data-record-keyword]");
    if (recordLinkElement) {
      const keyword = normalizeChineseKeyword(recordLinkElement.dataset.recordKeyword);
      const storageKey = "pukuRecordDiscoveredKeywordsV2";
      const stored = JSON.parse(localStorage.getItem(storageKey) || "[]");
      if (!stored.includes(keyword)) {
        stored.push(keyword);
        localStorage.setItem(storageKey, JSON.stringify(stored));
      }
      unlockBackend();
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(input.value);
    input.value = "";
  });

  window.addEventListener("storage", ensureBackendButton);
  ensureBackendButton();

  // resizable panel
  const EDGE = 8;
  const MIN_W = 320;
  const MIN_H = 420;

  const getHitZone = (e) => {
    const r = panel.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    const right = r.width - x;
    const bottom = r.height - y;
    const onL = x <= EDGE;
    const onR = right <= EDGE;
    const onT = y <= EDGE;
    const onB = bottom <= EDGE;
    if (onT && onL) return "nw";
    if (onT && onR) return "ne";
    if (onB && onL) return "sw";
    if (onB && onR) return "se";
    if (onT) return "n";
    if (onB) return "s";
    if (onL) return "w";
    if (onR) return "e";
    return null;
  };

  const cursorMap = { n: "n-resize", s: "s-resize", e: "e-resize", w: "w-resize", nw: "nw-resize", ne: "ne-resize", sw: "sw-resize", se: "se-resize" };

  let resizeState = null;

  panel.addEventListener("mousemove", (e) => {
    if (resizeState) return;
    const zone = getHitZone(e);
    panel.style.cursor = zone ? cursorMap[zone] : "";
  });

  panel.addEventListener("mouseleave", () => {
    if (!resizeState) panel.style.cursor = "";
  });

  panel.addEventListener("mousedown", (e) => {
    const zone = getHitZone(e);
    if (!zone) return;
    e.preventDefault();
    const r = panel.getBoundingClientRect();
    resizeState = { zone, startX: e.clientX, startY: e.clientY, startW: r.width, startH: r.height, startRight: window.innerWidth - r.right, startBottom: window.innerHeight - r.bottom };
  });

  window.addEventListener("mousemove", (e) => {
    if (!resizeState) return;
    const { zone, startX, startY, startW, startH, startRight, startBottom } = resizeState;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const maxW = window.innerWidth - startRight - 28;
    const maxH = window.innerHeight - startBottom - 28;

    let newW = startW;
    let newH = startH;

    if (zone.includes("e")) newW = Math.min(maxW, Math.max(MIN_W, startW + dx));
    if (zone.includes("w")) newW = Math.min(maxW, Math.max(MIN_W, startW - dx));
    if (zone.includes("s")) newH = Math.min(maxH, Math.max(MIN_H, startH + dy));
    if (zone.includes("n")) newH = Math.min(maxH, Math.max(MIN_H, startH - dy));

    panel.style.width = newW + "px";
    panel.style.height = newH + "px";
  });

  window.addEventListener("mouseup", () => {
    resizeState = null;
    panel.style.cursor = "";
  });
})();
