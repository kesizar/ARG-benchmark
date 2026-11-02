# 归一会：妹妹的升华日记 — 资源、裁判与验收

记录 `base664:0431`；原始入口 <https://019f8f12-2cef-75d4-86f4-263cb89f30e9.arena.site/>。旧快照 `ARG-packs/verify-416/bodies/431.html` 是 Arena 外壳，iframe 指向同一地址的 `?embed=true`。普通无上下文请求返回外壳，正常 iframe 请求头和原站 Referer 返回游戏本体 HTTP 200；内置浏览器普通打开原站实见游戏。非 HTTP 403。

- 原始正文：`data/preparation/results/base664-0431-embed.html`，UTF-8 SHA-256 `f6f0746cfc284f888653e0584c83e6c9f8e05998f4bbf8b27cd5e7caa612d41b`。外壳响应：`data/preparation/results/base664-0431-response.html`。
- 运行资源：网页、Tailwind 浏览器脚本、四张 Pexels 图片的九个尺寸变体、四个字体文件全部本地化，详见 `resource-inventory.json` 和 `font-inventory.json`。游戏中音频由浏览器脚本实时合成。Cloudflare 分析脚本移除。本地运行外部请求拦截，验收未记录失败请求。素材权利未经独立核实。
- 原作 `triggerEnding` 停止计时器，`restartGame` 未重新启动；本地副本仅补充重开后的 UI 刷新和重新计时。全部改动见 `localization.diff`。原始快照保留。
- 原作 50 环包括输入、拨轮、九宫格、调频和 15/30/45 三处选择。实机完整逐关检查中，47 个非选择关错误输入不推进，正确输入推进，三处正向选择得到 D；随后经快捷导航正常操作得到 B、C，此前 A 检查使用 fast_forward 并误读隐藏默认标题，不能证明失败结局触发；详见本次 route-review，A 采用虚拟时钟逐秒推进并检查遮罩可见。正常 UI 重置回到第 1 关；重开后的计时器从 02:45:00 跳至 02:44:58。证据见 `verification/acceptance.json`，截图 `verification/ending-d.png`。这是源码知情的工程验收，不是模型成绩。
- 原作 D 为 True、B 为 Normal、C 为 Dark、A 为 Bad；裁判将 A 配为 bad 终止失败、不作为通关路线；B/C/D 记录为 normal，待主代理按用户等级规则与原作说明复核。A 是超时失败，B/C/D 的分支判定详见源码 `calculateEndingsOutcome`，重置回合不保留选择。
- 原作任何时候可自由跳关，也提供显示答案并自动过关的“灵光乍现”；不能把当前层数视为通过。裁判监听可信正常验证按钮，按成功推进锁存 16 个候选推理、转换或交互点，具体见 checkpoint-spec.json；使用该关提示或跳过则不计分。21、22 附加照片3显影前置；验证脚本证实未显影直接提交不计分。自由跳关意味着这些点不是任何结局的必经点。答对不能证明模型独立推理。
- 10 关题面所给个位为 8035，系统答案 9481，提示未给出解释；47 关要求报警号码 9110 且提示添加所谓前缀，设定需审查。两关均不计入候选点；直接抄录和三个分支选择不计推理分，部分词汇翻译暂列为候选。题目普遍明示答案或可通过提示获取，正式计分需题目质量及难度复核。
- 两个包分开解压到 `runs/guiyihui-meimei-independent-3/` 并核对全部文件哈希。资源包在 8822 独立运行及正常输入首关通过；评测包在 8823 运行 `run_one.py --policy script` 得到 give_up，无裁判错误。游戏服务器只托管资源子目录，评测配置和裁判未被托管。该独立部署测试并不等同跨操作系统或真实模型测试。包 SHA-256 和具体日志见 `deployment.json`。
- Python 3.11、playwright、jsonschema、httpx、python-dotenv 及 Edge/Chrome 或 Playwright Chromium 为预装依赖，具体版本见评测包 `requirements.txt`。未调用付费 API。

- 共享运行器现支持 terminal_failures。最终评测包在独立解包目录中，以独立的一秒测试副本运行真实 loop，结果为 failure，failure_id 为 failure_timeout_A，ending_reached 为 false；该副本未进入 ZIP。原作 A 的原始 9900 秒计时另通过 Playwright 虚拟时钟逐秒推进，遮罩实际可见；该游戏与最终包游戏文件逐字节一致。此前 acceptance.json 的 A 项为假阳性，不应作为 A 的验收证据。独立解包目录中的 B/C/D 与重开复验通过。失败结果由 failure_reached/failure_id 表示，ending_tier 为 null，而不是通关路线。


## 本次逐关复审与新增裁判验收

新增 `level-audit.json`，逐关记录题面、验证答案、解法或来源、提示、可跳过性和缺陷。43 所称财务审计及 49 所称日记生日在素材内未找到；41 词义/拼写不充分限定，10 自相矛盾，47 前缀无根据，均留待审。23、29、42 的英文字词原文直接给出；24 虽可重排但日记也直接给出 AETHER。

当前工作版裁判包含 16 个可选候选，加入翻译、单位转换、字母重排与频率交互等；5 和其他翻译题仍需核对同义词与难度。新增 11 点各自在新浏览器上下文中进行了错误不推进且不计分、正确计分、提示后正确不计分、自动跳过不计分四项检查，见 `verification/new-points-acceptance.json`。50 关正常 UI 流程和 B/C/D 在新裁判下通过，见 `verification/all-points-acceptance.json`。新资源包和评测包在独立目录通过全部清单哈希、资源首关与评测 loop 启动检查，见 `deployment-new.json`。旧 A 的 9900 秒虚拟时钟与一秒副本 loop 证据按 15 个游戏文件、23 个 harness 文件、A hook 及 terminal_failures 声明的字节/结构等价复用，见 `verification/byte-equivalence.json`；裁判 init 已修改，但仅改变 50 关成功检测，未改变失败 hook。测试副本不在包内。


## 2026-10-28 独立复核（取代上文旧评分描述）

16 个候选原未显式指定 role，裁判默认均为 critical，并非文档所称可选；现仅保留11藏头、33加法、44数值换算三项关键推理结果，均可跳关且并非结局必经。5、12、20、35、46、48、50为翻译或按格式抄写；13题干的格式示例即答案2230；21为按明示设置显影并阅读，22照抄显影序列；24日记直接给AETHER，25滑块明示432，26录音文字直接给3-1-4；这些改 diagnostic。提示或跳关仍不能计点。所有判断均只依据可观察行为，不能排除猜测或先验知识。B normal、C bad、D good，A超时为终局失败；原作游戏和失败 hook 未修改。完整50关、B/C/D、重置以及独立包见 closeout；第10、41、43、47、49题缺陷仍未修复，因此全作正式推理评分继续 hold。
