# PuzzleBench Harness — Cursor 实现说明书

**Cursor：请按本文在私有仓 [kesizar/ARG-benchmark](https://github.com/kesizar/ARG-benchmark)（默认分支 `main`）上扩展实现 PuzzleBench Harness。**  
不要另起无关仓库；保留并升级现有《非自愿摄入 / INVOLUNTARY APPETITE》本地镜像通路作为首个任务样例。本文是**工程师规格书**：目录、接口、配置 schema、分阶段 PR 清单、验收标准。不要写空洞愿景；默认值已写死，标「可配置」处允许任务配置覆盖。

| 字段 | 值 |
|---|---|
| 文档角色 | 交给 Cursor 直接实现的完整说明书 |
| 目标仓库 | `kesizar/ARG-benchmark` |
| 设计吸收 | `/workspace/puzzle-bench/r5/harness/harness_design.md`（2026-10-08）+ `mini_harness.py` + 2026-10-12 产品决策 |
| 作者侧 | 张浩晏；用户写/扩规格与任务，Cursor 写代码 |
| 禁止写入 | 谜底、通关步骤、验证码破解、把 `judge/` 内容喂给模型 |

---

## 0. 一句话任务与非目标

### 0.1 一句话任务

在 `ARG-benchmark` 内实现一套**可配置、可判分、可批量跑**的解谜评测 harness：模型只能拿到普通玩家能看到/做到的信息；裁判在模型不可见的 `judge/` 侧读进度与结局；网页解谜/文字冒险/密室默认本地托管测；ARG 按 L1/L2/L3 三层分列统计；观测分 A/B/C 三档对照；首题打通《非自愿摄入》本地镜像。

### 0.2 非目标（明确不做）

| 不做 | 原因 |
|---|---|
| 替模型通关 / 写攻略脚本当评测结果 | 评测对象是模型，不是 harness |
| 破解验证码、登录墙、付费墙 | 条款与公平性；相关题降级或排除 |
| 把 `judge/`、检查点表、答案哈希、作者攻略喂给模型 | 作弊 |
| 自动化访问 ae27ff 等条款禁自动化站点 | **排除**（写死） |
| 主测默认启用 Computer Use / 桌面 GUI 代理 | 主测用 DOM+截图；仅无 DOM 少数题用坐标档 |
| 默认允许模型任意 `goto` / 外网搜攻略 | 玩家原则；ARG L3 仅单域名白名单 |
| Docker 作为 P0 硬依赖 | 现有仓无 Docker；P4 沙箱可再加隔离容器（可配置） |
| 另起第二个 harness 仓库 | 扩展本仓 |

### 0.3 玩家原则（每加能力自检）

> 模型只能拿玩家能看到/做到的东西。每加一项观测或动作，必须回答「玩家有没有」。没有则不给。

---

## 1. 背景与仓库现状

### 1.1 仓库现状（`main`，以 2026-10 为准）

```
ARG-benchmark/
├── README.md
├── .gitignore
├── .env                    # 密钥（不入库；本地放置）
└── mirror/
    ├── involuntary-appetite/   # 《非自愿摄入》本地镜像
    ├── serve_game.py           # http://127.0.0.1:8766/live/index.html
    ├── harness/
    │   ├── agent.py            # LLM 选动作（现有 tool 名：click/type/drag/…）
    │   ├── browser.py          # Playwright sync；白名单仅 127.0.0.1:8766
    │   ├── memory.py           # 调查笔记
    │   ├── run.py              # --selfcheck / play 循环
    │   └── test_memory.py
    └── _*.py                   # 镜像抓取/本地化辅助脚本
```

**缺口（相对产品级 harness）：**

- 无统一任务配置 schema；入口写死在 `browser.HOME`
- 无正式 Judge（无 hooks/checkpoints/ending；无 `judge/` 隔离）
- 无观测三档开关；无 ARG 分层字段；无批量 runs 汇总
- 动作语义与 `mini_harness.py`（`op` JSON）不一致；需迁移到统一动作集
- 同步 Playwright；设计原型为 async——产品实现**默认 async Playwright**（与 `mini_harness.py` 对齐），旧 sync 代码可保留为兼容薄封装直至删除

### 1.2 设计基础（只读吸收，勿矛盾）

| 来源 | 用途 |
|---|---|
| `harness_design.md` §1–14 | 观测、动作、裁判、日志、配置、IF/静态变体、难点表 |
| `mini_harness.py` | `Judge` / `Harness` / `ScriptedPolicy` / `run()` 接口名与行为 |
| `r5/harness/configs/B28-*.json` | 配置示例形态（正式评测时 judge 段外置） |
| 本仓 `mirror/harness/*` | 首题通路与本地服务；演进而非推倒 |
| 总表 | `puzzle-bench-deliverables` 中 784 条（`总表_详细梳理.csv`）；试点从「可获取可用」优先 |

### 1.3 产品决策默认值（2026-10-12 拍板倾向）

| # | 决策 | 默认 | 可配置？ |
|---|---|---|---|
| 1 | 网页解谜 / 文字冒险 / 密室 | **本地托管测** | 任务可标 `local_serve` |
| 2 | ARG | **三层单列统计，不混报** | `arg_layer`: L1/L2/L3 |
| 3 | 观测三档 | 每题可跑多档，报告分列；**主测默认 B** | `obs_mode`: A/B/C |
| 4 | Computer use | **主测不用**；仅 canvas/Unity/Steam GUI/纯截图密室等 | `computer_use: false` 默认 |
| 5 | 判分资料 | 在 `judge/`，agent 不可见；里程碑可从作者攻略反推**仅供裁判** | 路径引用 |
| 6 | ae27ff | **排除** | 硬排除列表 |
| 7 | 可见文本+元素编号 | **默认给**；`goto` **默认不允许**（作品要求改 URL 时仅站内） | `allow_model_goto` |
| 8 | 实现分工 | 用户写规格/任务；Cursor 写代码 | — |

---

## 2. 架构总图

```
┌──────────── 模型侧（只看得到这些） ────────────┐
│ system: model_visible.title/intro + 动作列表 + 预算规则 │
│ 每步 observation（按 obs_mode A/B/C）：                  │
│   A: 可见文本 + 元素编号（可不给截图）                    │
│   B: 文本 + 截图 + 元素编号（主测默认）                   │
│   C: 纯截图（坐标点击；无 DOM 文本/无元素表）             │
│ 每步输出：一个 JSON 动作 {"op": "...", ...}               │
└───────────────────────────────────────────────┘
            │ 动作                      ▲ 观测
┌───────────▼─────────── harness ──────┴──────────────┐
│ Playwright 无头 Chromium（每局新 context）              │
│ 或 IF 解释器 / 静态题面适配器                           │
│ 网络层：allow_hosts + shortcut_block +（L3）攻略站禁    │
│ 动作执行：真实鼠标/键盘事件；不执行模型给出的页面 JS      │
│ 日志：steps.jsonl / judge.jsonl / summary.json / tokens │
└───────────┬─────────────────────────────────────────┘
            │ 每步之后读取（模型不可见）
┌───────────▼──────── 裁判 Judge ───────────────┐
│ judge/<task_id>/：hooks、checkpoints、ending、  │
│ events、answer hashes、rubric、request 里程碑   │
└───────────────────────────────────────────────┘
            │
┌───────────▼──────── 本地服务 / 任务资产 ───────┐
│ tasks/<id>/mirror 或 entry；scripts/serve_*.py  │
│ 默认 127.0.0.1:<port>；白名单仅本地域名         │
└─────────────────────────────────────────────────┘
```

主循环（产品实现必须保持此顺序）：

```
reset()                                 # 新 profile、固定视口/种子、打开入口
obs = observe()
for step in 1..max_steps:
    if 超时: break
    action = policy.act(obs)            # ScriptedPolicy | LLMPolicy
    result = harness.act(action)
    state  = judge.read(); judge.update(step)
    obs    = observe()
    log(action, result, obs, state)     # steps 与 judge 分文件
    if action 是 give_up / submit 终局正确 / judge 读到结局: break
write summary.json
```

---

## 3. 目录树目标结构

在仓库根扩展（保留 `mirror/` 现有通路，逐步把通用代码上移到 `harness/`）：

```
ARG-benchmark/
├── README.md
├── .env                          # 密钥；.gitignore 已忽略
├── .env.example                  # 无真实密钥
├── pyproject.toml 或 requirements.txt
├── configs/
│   ├── schema/task.schema.json   # JSON Schema（Draft 2020-12）
│   ├── involuntary-appetite.json # 首题任务配置（judge 仅路径）
│   └── examples/                 # 网页解谜/IF/密室示例（可无谜底）
├── tasks/
│   └── involuntary-appetite/
│       ├── README.md             # 模型不可见的出题说明（可选）
│       ├── mirror/               # 或 symlink → ../../mirror/involuntary-appetite
│       └── serve.json            # port、entry_path、启动命令
├── judge/                        # ★ 模型与 agent 进程默认不可读内容进 prompt
│   └── involuntary-appetite/
│       ├── judge.json            # hooks/checkpoints/ending/events
│       ├── answers.sha256        # 若有 submit_answer
│       └── rubric.md             # 仅人读/裁判脚本读；勿进模型
├── harness/                      # ★ 产品核心（由 mirror/harness 演进上来）
│   ├── __init__.py
│   ├── loop.py                   # run() 主循环
│   ├── browser_harness.py        # 网页：observe/act/reset（对齐 mini_harness.Harness）
│   ├── if_harness.py             # 文字冒险
│   ├── static_harness.py         # 静态题
│   ├── judge.py                  # Judge 类
│   ├── observe.py                # 三档观测构造
│   ├── actions.py                # 动作校验与执行分发
│   ├── network.py                # 白名单、捷径、攻略站黑名单
│   ├── policy_script.py          # ScriptedPolicy
│   ├── policy_llm.py             # LLMPolicy
│   ├── prompts.py                # system/user 消息构造
│   ├── tokens.py                 # token 记账
│   ├── summary.py                # summary 字段与批量汇总
│   └── legacy_mirror/            # 过渡期：旧 agent/browser/memory 适配器（可删）
├── mirror/                       # 保留现有《非自愿摄入》资产与 serve_game.py
│   ├── involuntary-appetite/
│   ├── serve_game.py
│   └── harness/                  # 过渡：转发到顶层 harness/ 或标记 deprecated
├── runs/                         # gitignore；runs/<task_id>/<obs_mode>/<timestamp>/
├── scripts/
│   ├── serve_task.py             # 按 tasks/*/serve.json 起本地服务
│   ├── validate_config.py        # schema 校验
│   ├── run_one.py                # 单任务入口
│   ├── run_batch.py              # 批量
│   └── aggregate_runs.py         # 汇总表
├── docs/
│   ├── harness_spec.md           # 可链到本文副本
│   └── obs_modes.md              # A/B/C 说明
└── exclude/
    └── sites.txt                 # 含 ae27ff 等硬排除
```

**迁移规则：**

1. P0 可先在 `mirror/harness/` 内改到可配置循环，但配置键与日志字段必须按本文。
2. P1 起把通用模块升到顶层 `harness/`，`mirror/harness` 变薄包装或删除。
3. `judge/` 永不打包进发给模型的任何消息；CI 可加检查：`prompts.py` 构造结果不得包含 `judge/` 路径下文件内容。

---

## 4. 任务配置 JSON Schema

### 4.1 文件位置

- Schema：`configs/schema/task.schema.json`
- 任务配置：`configs/<task_id>.json`
- 裁判细节：`judge/<task_id>/judge.json`（配置里只放路径）

### 4.2 顶层字段（吸收 design §8，并扩展）

```jsonc
{
  "id": "involuntary-appetite",                 // 必填；与目录名一致
  "category": "arg",                            // web_puzzle | text_adventure | escape_room | arg | static
  "arg_layer": "L1",                            // 仅 category=arg：L1|L2|L3；其它类别 null
  "obs_mode": "B",                              // A|B|C；主测默认 B；批量可覆盖
  "obs_modes_to_run": ["A", "B", "C"],          // 可选；试点可先 ["B"]
  "computer_use": false,                        // 默认 false；仅无 DOM 题 true
  "model_visible": {                            // ★ 唯一允许进模型 system 的作品信息
    "title": "非自愿摄入",
    "intro": "你在一个本地托管的解谜作品里。只能用列出的动作，只根据屏幕上能看到的信息推理。"
  },
  "entry_url": "http://127.0.0.1:8766/live/index.html",
  "local_serve": {
    "enabled": true,
    "command": ["python", "mirror/serve_game.py"],
    "cwd": ".",
    "ready_url": "http://127.0.0.1:8766/live/index.html",
    "ready_timeout_s": 30,
    "port": 8766
  },
  "viewport": {"width": 1366, "height": 900},
  "locale": "zh-CN",
  "timezone": "Asia/Shanghai",
  "seed": 20261012,
  "allow_hosts": ["127.0.0.1:8766"],
  "shortcut_block": [
    // {"type":"url_param","name":"debug","label":"调试参数"}
    // {"type":"url_regex","pattern":"...","label":"..."}
  ],
  "guide_block_hosts": [                        // L2/L3：攻略站等；L1 本地可空
    "*.bilibili.com", "www.youtube.com", "zhuanlan.zhihu.com",
    "www.reddit.com", "walkthrough*", "*walkthrough*",
    "*spoiler*", "*solution*", "*guide*"
  ],
  "allow_model_goto": false,                    // 默认 false；true 时仍过白名单+捷径
  "goto_scope": "none",                         // none | same_host | allow_hosts
  "show_url": true,
  "obs_screenshot": true,                       // 由 obs_mode 推导时可省略；显式优先
  "obs_text": true,
  "obs_elements": true,
  "text_scope": "page",                         // page | viewport
  "text_limit": 6000,
  "actions_enabled": [
    "click", "dblclick", "type", "key", "scroll", "drag",
    "back", "switch_tab", "close_tab", "wait", "dialog", "give_up"
  ],
  "limits": {
    "max_steps": 80,
    "max_seconds": 1800,
    "max_answer_submits": 20
  },
  "settle_ms": 1200,
  "history": {
    "full_obs_k": 4,                            // 默认 4（范围 3–5）；全局统一写进报告
    "screenshot_k": 2
  },
  "judge_path": "judge/involuntary-appetite/judge.json",
  "policy_script": null,                        // 正式评测 null；P0 假策略可内嵌或外置
  "notes_for_report": []                        // 如「作者建议外搜，本评测不放行」
}
```

### 4.3 `obs_mode` 与观测开关映射（写死）

| obs_mode | obs_screenshot | obs_text | obs_elements | 点击方式 |
|---|---|---|---|---|
| A | false（默认；可配置强制留档截图但不进模型） | true | true | 元素编号 `n` |
| B | true | true | true | 编号为主；允许 `x,y` |
| C | true | false | false | 仅 `x,y`（及 drag 等坐标动作） |

实现：加载配置后调用 `apply_obs_mode(cfg)`，用上表覆盖三开关；若用户显式写了与 mode 冲突的开关，**以 obs_mode 为准**并打 warning 日志。

### 4.4 `category` / `arg_layer` 约束

- `category != "arg"` ⇒ `arg_layer` 必须为 `null` 或不出现。
- `category == "arg"` ⇒ `arg_layer` 必填 L1|L2|L3。
- 报告聚合键必须包含 `(category, arg_layer, obs_mode)`，ARG 三层**不得**与网页解谜混成一行总分。

### 4.5 Judge 外置文件 `judge/<id>/judge.json`

```jsonc
{
  "hooks": {
    "example_url": {"type": "url_regex", "pattern": "/live/index\\.html"},
    "example_dom": {"type": "dom_regex", "pattern": "可见固定文案正则", "agg": "any"}
  },
  "checkpoints": [
    {"id": "cp_entered", "hook": "example_url", "op": "truthy"}
  ],
  "events": {},
  "ending": null,
  "answer_hash_file": null,
  "request_milestones": [
    // 当页面无可见反馈时：用请求日志（仅裁判可见）
    // {"id": "hit_asset_x", "url_regex": ".*/path/to/asset", "resource_types": ["xhr", "fetch", "document"]}
  ],
  "submit_conclusion": {
    // 模型可提交结构化结论；裁判用 rubric 脚本或哈希比对
    "enabled": false,
    "schema": null
  },
  "rubric_path": null
}
```

**禁止**在 judge 文件或任务配置的非 `model_visible` 字段写谜底明文；答案只用 SHA-256（NFKC→去空白→小写后哈希）。

### 4.6 Schema 校验要求

`scripts/validate_config.py configs/foo.json`：

- 对照 `task.schema.json` 校验
- 检查 `judge_path` 存在
- 检查 `id` 不在 `exclude/sites.txt` / 硬排除列表
- 检查 `entry_url` host 落在 `allow_hosts`（本地服务启动后）
- 退出码 0/1；CI 可用

---

## 5. 观测三档与动作集

### 5.1 观测字段（模型可见）

| 字段 | A | B | C | 说明 |
|---|---|---|---|---|
| screenshot | 可选不进模型 | 给 | 给 | 视口截图；默认 1366×900，`device_scale_factor=1` |
| visible_text | 给 | 给 | 不给 | 仅渲染可见文字；过滤规则同 design §2；上限 `text_limit` |
| elements | 给 | 给 | 不给 | 视口内未遮挡可交互元素：`n, kind, label, x, y`；不给 aria/id/class/href |
| tabs | 给 | 给 | 给（标题+是否当前；C 可隐藏 url） | 新标签自动切换 |
| url | 只读，受 `show_url` | 同左 | 同左 | 地址栏对玩家可见 |
| dialogs / pending_dialog | 给 | 给 | 给 | alert 自动确认；confirm/prompt 挂起 |
| last_result | 给 | 给 | 给 | 短中文；不泄漏裁判 |
| budget | 给 | 给 | 给 | steps_left / seconds_left |
| **不给** | 源码、DOM 树、a11y 全文、网络日志、存储、裁判状态、检查点名与数量 | | | |

可见文本过滤（必须实现，对齐原型）：

- 跳过 `script/style/noscript/template`
- 祖先 `display:none` / `visibility:hidden` / `opacity:0` / `hidden`
- 跳过移出文档左侧（如 `left:-9999px`）、字号 &lt; 4px、`clip: rect(0 0 0 0)` 或 1–2px 溢出隐藏
- 不读 HTML 注释、属性值、localStorage、网络响应

### 5.2 动作集（统一 `op`；废弃旧 `tool` 名）

模型每步输出一个 JSON；允许前缀短思考；harness **只解析最后一个 JSON 对象**；失败记一步并 `last_result="动作格式错误"`。

| op | 参数 | 默认启用 | 备注 |
|---|---|---|---|
| `click` | `n` 或 `x,y` | 是 | 编号→中心坐标→真实鼠标事件 |
| `dblclick` | 同上 | 按需 | 伪桌面 |
| `long_press` | `x,y,ms≤3000` | 按需 | |
| `hover` | `x,y` | 按需 | |
| `drag` | `x1,y1,x2,y2` 或题特异 | 按需 | 《非自愿摄入》面包屑可映射为 drag |
| `type` | `text`, 可选 `n`,`clear`,`enter` | 是 | text≤200 字 |
| `key` | `key` ∈ 白名单 | 是 | 禁组合键 |
| `scroll` | `dir` 或 `dx,dy`，可选 `x,y` | 是 | 内层滚动要带坐标 |
| `back` | — | 是 | |
| `switch_tab` / `close_tab` | `i` | 是 | |
| `wait` | `ms≤10000` | 是 | 算一步 |
| `dialog` | `accept`,`text` | 是 | |
| `goto` | `url` | **默认关** | 开时仅 `goto_scope` |
| `submit_answer` | `text` | 静态/需提交题 | 只回「正确/不正确」 |
| `submit_conclusion` | `object` | 可选 | 无可见结局反馈时用 |
| `give_up` | — | 是 | |
| `note` | — | **默认关** | 若开则全作品统一纯文本本，报告注明 |

**按键白名单：**  
`Enter Escape Tab Backspace Delete Space ArrowUp ArrowDown ArrowLeft ArrowRight PageUp PageDown Home End` + 单字符 `a-z0-9`。  
禁止 Ctrl/Alt/Meta 组合（挡 Ctrl+U、F12、Ctrl+L 等）。

### 5.3 旧仓动作名迁移表（实现时必须兼容一层或一次性改 agent）

| 旧 `tool`（mirror/harness） | 新 `op` |
|---|---|
| `click` + `control_id` | `click` + `n`（由观测 elements 编号） |
| `type` + `control_id` | `type` + `n` |
| `drag` + `tile_id` | `drag`（坐标）或任务扩展动作（配置声明） |
| `scroll` | `scroll` |
| `back` | `back` |
| `goto` | `goto`（默认禁用） |
| `done` | `give_up` 或 `submit_conclusion` |
| `recall`（memory） | **默认移除出模型动作**；笔记若保留则走配置 `note`，P0 可不做 |

### 5.4 IF / 静态变体（design §10–11）

**文字冒险：** 同主循环；观测=解释器输出文本+回合+预算；动作=`type(text)`（自动回车）、`give_up`；禁向模型暴露 `get_valid_actions`；禁 `save/restore/undo`（默认，可配置但报告标注）。

**静态题：** 观测=题面；动作=`submit_answer`/`give_up`（网页题面可加 click/scroll）；答案 NFKC+strip+lower 后 SHA-256 比对 `judge/` 哈希文件。

---

## 6. 网络沙箱、捷径拦截、防作弊

### 6.1 域名白名单

- 配置 `allow_hosts`：精确 host 或 `*.example.com`
- 非 `http/https` 的 `data`/`blob`/`about` 放行
- 其余 `route.abort('blockedbyclient')`，记入裁判日志 `blocked[]`：`{step, why, host|rule, type}`
- 首次接入任务时检查 `blocked_hosts`：CDN 库可加入白名单；广告/统计保持拦截

### 6.2 捷径拦截 `shortcut_block`

| type | 行为 |
|---|---|
| `url_param` | query 含 `name` 则 abort |
| `url_regex` | URL 匹配则 abort |

`goto` 预检与网络层共用同一 `shortcut_hit(url)`。

### 6.3 ARG 分层网络策略

| 层 | 网络 | 材料 | 报告字段 |
|---|---|---|---|
| L1 | 仅本地 mirror / `allow_hosts`（通常 `127.0.0.1:port`） | 镜像齐全 | `arg_layer=L1` |
| L2 | 封闭世界：材料域名白名单；**禁外网搜攻略**（`guide_block_hosts` + 默认无搜索引擎） | 题包自带 | `arg_layer=L2` |
| L3 | 真实联网沙箱：**单域名（或显式短名单）白名单**；禁攻略站 | 原站 | `arg_layer=L3` |

L3 默认启用隔离（P4）：独立浏览器 context；可选容器网络；仍禁止把 judge 挂进容器可见路径。

### 6.4 其它防作弊硬规则

- `accept_downloads=False`；无剪贴板/打印 API 暴露
- `service_workers='block'`
- 每局 `browser.new_context()`；无 cookie/localStorage/缓存继承
- 模型动作入口不得 `page.evaluate` 执行模型代码
- 组合键禁用
- `exclude/sites.txt` 含 `ae27ff`；加载配置时拒绝
- 审计：若 `steps.jsonl` 的 obs 文本命中 judge 文件哈希或关键子串，CI 失败（P1 可做简单版）

### 6.5 《非自愿摄入》本地服务

- 保持 `python mirror/serve_game.py` → `http://127.0.0.1:8766/live/index.html`
- harness 启动前由 `local_serve` 拉起；结束后可杀进程
- 白名单：`127.0.0.1:8766` 仅此（默认）

---

## 7. Judge

### 7.1 钩子类型（对齐 `mini_harness.Judge`）

| type | 读什么 | 常用修饰 |
|---|---|---|
| `localstorage` | key：`exists`/`length`/`json_len`/`json_path`/`hash` | `frame_url_regex` |
| `url_regex` | 所有标签页 URL | — |
| `dom_regex` | 全 frame `innerText`；`agg`: any/count/max/last/all | `accumulate:distinct`+`exclude`；`keep_max` |
| `dialog_regex` | 本步对话框 | — |
| `tab_count` | 标签数 | — |
| `request_regex` | **新增**：本步/累计请求 URL（仅裁判；来自 route 日志） | 用于「判定反馈未观测到」 |

### 7.2 记分

- `checkpoints`：首次满足记 step；得分 = reached/total；**结局不算检查点**
- `ending`：单独 `ending_reached` + step；多结局分别记好/坏，仍不计检查点
- `events`：假→真边沿（如错误输入）
- `submit_answer`：与哈希比对；正确可作为 ending 条件（在 judge 配置里用事件或专用字段）

### 7.3 「判定反馈未观测到」通路（必须实现）

部分作品提交后页面无文案变化。此时：

1. 配置 `request_milestones`：裁判在网络日志上匹配资源/XHR
2. 允许模型 `submit_conclusion`（结构化 JSON）；裁判侧 `rubric` 或脚本评分（结果只进 `judge.jsonl`/`summary.json`）
3. 模型侧只看到「已记录」或「正确/不正确」，看不到里程碑名

### 7.4 API（产品模块 `harness/judge.py`）

```python
class Judge:
    def __init__(self, judge_cfg: dict, task_id: str): ...
    async def read(self, harness) -> dict: ...
    def update(self, step: int) -> list:  # [("checkpoint", id), ...]
    def score(self) -> dict: ...
```

行为必须与 `mini_harness.Judge` 兼容；新增 `request_regex` / `submit_conclusion` 处理。

---

## 8. 文字冒险：Frotz / Jericho / .z5 / .z8

### 8.1 依赖

- 优先 **Jericho**（有 score/victory API）
- `.z5`/`.z8`：Frotz/Jericho 加载
- Glulx：可接 emglken（仓内若已有 `tools/ifrun.py` 思路则复用模式，不强制依赖 puzzle-bench 路径）

### 8.2 接口

| 项 | 规定 |
|---|---|
| 观测 | 上条命令后的输出文本；turn；budget；无截图 |
| 动作 | `{"op":"type","text":"..."}`；`give_up` |
| 重置 | 每局新解释器进程/env；固定 seed |
| 裁判 | `get_score`/`victory`/`game_over`；或输出文案正则 |
| 禁止 | 向模型暴露 valid actions；默认禁 save/restore/undo |

### 8.3 配置差异

```jsonc
{
  "category": "text_adventure",
  "arg_layer": null,
  "obs_mode": "A",
  "entry_url": null,
  "if": {
    "story_file": "tasks/foo/story.z8",
    "interpreter": "jericho",
    "max_command_chars": 200
  },
  "actions_enabled": ["type", "give_up"],
  "judge_path": "judge/foo/judge.json"
}
```

---

## 9. ARG 三层实现差异与报告字段

### 9.1 实现差异

| 项 | L1 | L2 | L3 |
|---|---|---|---|
| 资产 | `tasks/<id>/mirror` 或本仓 `mirror/` | 题包材料齐全 | 可达原站 |
| 服务 | 本地 HTTP | 本地或封闭静态 | 可选本地反代 + 真网 |
| `allow_hosts` | 本机 port | 材料域名列表 | **单主域名**（默认可配置少量 CDN） |
| 攻略站 | 天然不可达 | 显式 block | 显式 block |
| 外搜 | 否 | 否 | 否 |
| 隔离 | 普通 context | 普通 context | P4：可选容器 |

### 9.2 报告字段（每局 summary 必含）

```jsonc
{
  "task_id": "...",
  "category": "arg",
  "arg_layer": "L1",
  "obs_mode": "B",
  "computer_use": false,
  "model": {"provider": "...", "name": "...", "temperature": 0},
  "ended_reason": "ending|give_up|max_steps|max_seconds|error",
  "steps": 0,
  "seconds": 0,
  "checkpoints_reached": 0,
  "checkpoints_total": 0,
  "ending_reached": false,
  "events": [],
  "blocked_requests": 0,
  "blocked_hosts": [],
  "shortcut_blocks": [],
  "tokens": {"prompt": 0, "completion": 0, "total": 0},
  "history_k": 4,
  "notes_for_report": []
}
```

批量汇总表按 `category × arg_layer × obs_mode × model` 分列；**禁止**把 L1/L2/L3 平均成一个 ARG 总分而不注明。

---

## 10. LLM 接入

### 10.1 `.env`

```
OPENAI_API_KEY=
OPENAI_BASE_URL=                 # 可选
OPENAI_MODEL=gpt-4.1             # 默认示例；可配置
ANTHROPIC_API_KEY=               # 可选第二提供商
LLM_PROVIDER=openai              # openai|anthropic|…
LLM_TEMPERATURE=0
LLM_MAX_OUTPUT_TOKENS=1024
```

提供 `load_env(repo_root)`；无密钥时允许 `--policy script` 跑通假策略。

### 10.2 消息构造

- **system**：仅 `model_visible` + 通用玩家说明 + `actions_enabled` JSON schema 短表 + 预算规则 + 输出格式。不写检查点数、不写攻略。
- **user（每步）**：按 obs_mode 放置截图（多模态）与文本字段；含 tabs、last_result、budget。
- **历史窗口**：完整观测保留最近 `history.full_obs_k`（默认 **4**，允许 3–5，**全局统一**）；截图只留最近 `screenshot_k`（默认 2）；更早步只保留 `action+result+url/title`。
- **输出解析**：取最后一个 `{...}`；`op` 校验；非法→记步。

### 10.3 Token 记账

每步记录 prompt/completion/total；summary 累加；原始模型输出写入 `runs/.../model_raw.jsonl`（可截断单行 32KB）。

### 10.4 接口

```python
class LLMPolicy:
    def __init__(self, cfg, env): ...
    def act(self, obs) -> dict: ...   # 同步包装；内部可 async
```

---

## 11. 日志与 summary 字段

### 11.1 每局目录

`runs/<task_id>/<obs_mode>/<YYYYMMDD_HHMMSS>/`

| 文件 | 内容 | 是否可给外部复盘 |
|---|---|---|
| `step_NNN.png` | 截图 | 是 |
| `steps.jsonl` | step,t,action,result,obs摘要 | 是（勿含 judge） |
| `judge.jsonl` | state,new,blocked | **否**（勿发给模型侧复盘包） |
| `summary.json` | §9.2 字段 | 可发聚合版 |
| `last_obs.json` | 最后完整观测 | 是 |
| `model_prompt.json` | 本局 system（仅 model_visible） | 是 |
| `model_raw.jsonl` | 原始输出+tokens | 内部 |
| `config.snapshot.json` | 展开后的配置（**剥离 judge 正文**，只留 judge_path） | 是 |

### 11.2 `steps.jsonl` 单行最小字段

```jsonc
{
  "step": 1,
  "t": 1.23,
  "action": {"op": "click", "n": 0},
  "result": "ok",
  "obs": {
    "screenshot": "step_001.png",
    "tabs": [],
    "n_elements": 0,
    "text_sha1": "abcd",
    "text_head": "...",
    "dialogs": [],
    "pending_dialog": null
  },
  "tokens": {"prompt": 0, "completion": 0}
}
```

---

## 12. 试点计划

### 12.1 规模

- 先 **20–30** 条可跑任务配置（非一次 784）
- 总表 784 条在交付夹 `puzzle-bench-deliverables`；选「可获取 / 可本地化 / 有判分钩子」优先
- **硬排除**：ae27ff；条款禁自动化；强依赖真人/线下/不可重置服务端状态的标 D 不进试点

### 12.2 首题（必须最先打通）

| 项 | 值 |
|---|---|
| 任务 | 《非自愿摄入》 |
| id | `involuntary-appetite` |
| category | `arg` |
| arg_layer | `L1` |
| 服务 | `mirror/serve_game.py` @ 8766 |
| 观测 | 先 B，再视需要 A/C |
| P0 策略 | `ScriptedPolicy` 假策略（滚动/点击/输入测试字符串），验证日志与白名单 |

### 12.3 后续抽样（P2+）

每种至少若干道（具体 ID 由出题方从总表勾选，Cursor 不自填谜题内容）：

- 网页解谜（本地镜像或可镜像）
- 文字冒险（.z5/.z8 一份）
- 密室（网页或本地）
- ARG L2 包一份（材料齐全）
- ARG L3 仅在沙箱就绪后加 1 道烟测

---

## 13. 分阶段实现清单（按阶段开 PR）

### P0 — 可配置循环 + 日志 + 白名单 + 首题假策略

**目标：** 《非自愿摄入》可跑通一局 ScriptedPolicy；产出 steps/summary；白名单生效。

- [ ] 抽出配置加载：`configs/involuntary-appetite.json`（可先把 judge 内嵌，但字段齐全）
- [ ] 主循环 `reset → observe → act → judge.read/update → log`
- [ ] 网络白名单仅 `127.0.0.1:8766`
- [ ] `local_serve` 自动启动/等待 ready
- [ ] `ScriptedPolicy` + `runs/` 目录结构
- [ ] CLI：`python scripts/run_one.py --config configs/involuntary-appetite.json --policy script`
- [ ] 旧 `tool` API 适配或改写 agent 为 `op`
- [ ] 文档：如何跑 selfcheck 与一局假策略

**PR 建议标题：** `P0: configurable loop + local whitelist + involuntary-appetite scripted run`

### P1 — Schema + judge 分离 + 三档观测

- [ ] `configs/schema/task.schema.json` + `validate_config.py`
- [ ] `judge/` 外置；配置仅 `judge_path`
- [ ] `apply_obs_mode`；A/B/C 开关
- [ ] Judge 类完整 hooks（含 keep_max / distinct）
- [ ] steps/judge 分文件；summary 字段齐
- [ ] 排除列表加载（ae27ff）
- [ ] 提示构造确保不读 judge 文件

**PR：** `P1: task schema, isolated judge, obs modes A/B/C`

### P2 — 多任务本地托管模板 + 第二部网页解谜

- [ ] `tasks/<id>/` + `scripts/serve_task.py` 模板
- [ ] 第二部网页解谜任务（本地镜像）；配置+judge 钩子（无谜底）
- [ ] 批量目录约定与 `run_batch.py`（可先串行）
- [ ] CDN/blocked_hosts 接入检查清单文档

**PR：** `P2: multi-task local serve template + second web puzzle`

### P3 — IF 解释器通路

- [ ] `if_harness.py` + Jericho/Frotz
- [ ] 至少 1 个 `.z5` 或 `.z8` 烟测任务
- [ ] 裁判 score/victory；summary 字段兼容
- [ ] 禁止 valid actions 泄漏的单测

**PR：** `P3: interactive fiction harness (Jericho/Frotz)`

### P4 — ARG L2/L3 沙箱与报告分列

- [ ] `arg_layer` 贯穿 summary 与 aggregate
- [ ] L2 guide_block + 材料白名单
- [ ] L3 单域名白名单；攻略站黑名单
- [ ] 可选隔离容器文档与脚本（默认 off）
- [ ] `aggregate_runs.py` 分列 category/layer/mode

**PR：** `P4: ARG L2/L3 sandbox + split reporting`

### P5 — 真实 LLM runner + 批量汇总表

- [ ] `LLMPolicy` + `.env` 多提供商
- [ ] 历史窗口 K=3–5（默认 4）；token 记账
- [ ] `model_raw.jsonl`；失败重试策略（默认：解析失败不重试 API，只记步）
- [ ] `run_batch.py` + `aggregate_runs.py` → CSV/MD 汇总表
- [ ] 试点 20–30 任务清单文件 `configs/pilot_set.json`（ID 列表）

**PR：** `P5: LLM runner + batch aggregate tables`

---

## 14. 验收标准（每阶段可勾选）

### P0

- [ ] `python mirror/serve_game.py` 就绪后，`run_one --policy script` 退出码 0
- [ ] 生成 `runs/involuntary-appetite/B/<ts>/steps.jsonl` 与 `summary.json`
- [ ] 站外请求（若策略误触发）被 abort，且 `summary.blocked_hosts` 可复现
- [ ] 假策略至少完成：打开入口 → 一次点击或输入 → 正常结束或 give_up
- [ ] 日志中无 judge 检查点名称出现在 model 观测字段

### P1

- [ ] `validate_config.py` 对首题配置通过
- [ ] 同一任务 `--obs-mode A|B|C` 各跑通 script 局；C 的 obs 无 visible_text/elements
- [ ] `judge/` 删除后模型侧仍能跑（仅裁判失败）——用于证明未把 judge 打进包；或反向：prompt 快照 hash 不含 judge 文件字节
- [ ] ae27ff 配置被拒绝加载

### P2

- [ ] 第二任务不改 harness 核心代码，仅加 `configs/`+`tasks/`+`judge/` 即可跑
- [ ] `serve_task.py` 能按配置起停端口

### P3

- [ ] IF 烟测：固定脚本输入两步命令，summary 含 score 或 checkpoint
- [ ] 单测：观测字符串不含 valid-actions 列表接口输出

### P4

- [ ] 汇总表中 ARG 的 L1/L2/L3 分列；无混报总分
- [ ] L3 配置访问非白名单域名 100% abort
- [ ] 攻略站 host 样例在 fixture 测试中被 block

### P5

- [ ] 真实密钥下 LLM 跑首题 ≥1 局，产出 tokens 与 model_raw
- [ ] 批量 N≥3 任务汇总 CSV 含规定列
- [ ] 历史窗口参数写入每局 summary

---

## 15. 明确不做清单

1. 不实现自动通关 / 攻略搜索 agent  
2. 不破解验证码、不绕过登录/付费  
3. 不把作者攻略、检查点表、答案明文给模型  
4. 不收录或自动化 ae27ff  
5. 主测不做 Computer Use；不做任意桌面控制  
6. 默认不做外网搜索工具调用  
7. 不做下载文件评测通路（`accept_downloads=False`）  
8. 不在文档或配置中写谜底  
9. 不把交付夹当仓库：本说明书只进 `puzzle-bench-focus` 与仓内 `docs/`，**不要**拷到 `puzzle-bench-deliverables`  
10. P0–P3 不强制 Docker  

---

## 16. 附录

### 16.1 与旧 `harness_design.md` / `mini_harness.py` 对应关系

| 设计章节 | 产品落点 |
|---|---|
| §1 总体结构 | 本文 §2；`harness/loop.py` |
| §2 观测 | §5.1；`observe.py` + `obs_mode` |
| §3 动作集 | §5.2；`actions.py` |
| §4 不给模型 | §0.2 / §6.4 |
| §5 裁判 | §7；`judge.py` |
| §6 重置与可重复 | `browser_harness.reset` |
| §7 日志 | §11 |
| §8 配置格式 | §4（扩展 category/arg_layer/obs_mode/local_serve…） |
| §9 提示与输出 | §10 |
| §10 IF | §8 |
| §11 静态题 | §5.4 / `static_harness.py` |
| §12 难点表 | 实现时对照；toast MutationObserver 标 P2+ 可选 |
| §14 待拍板 | **已拍板**：默认文本+编号；默认禁 goto；K=3–5 |

| `mini_harness.py` 符号 | 产品符号 |
|---|---|
| `class Judge` | `harness.judge.Judge` |
| `Judge.read/update/score` | 同名 |
| `class Harness` | `harness.browser_harness.BrowserHarness` |
| `Harness.reset/observe/act/log` | 同名 |
| `Harness.check_answer` | 同名或 `Judge.check_answer` |
| `ScriptedPolicy` | `harness.policy_script.ScriptedPolicy` |
| `model_prompt(cfg)` | `harness.prompts.model_prompt` |
| `async def run(cfg_path)` | `harness.loop.run` / `scripts/run_one.py` |
| `ALLOWED_KEYS` | `harness.actions.ALLOWED_KEYS` |
| `norm` + SHA-256 | 答案归一化 |

### 16.2 动作 JSON 示例

```json
{"op": "click", "n": 3}
{"op": "click", "x": 640, "y": 420}
{"op": "type", "n": 1, "text": "test123", "enter": true}
{"op": "key", "key": "Enter"}
{"op": "scroll", "dir": "down", "x": 400, "y": 300}
{"op": "drag", "x1": 100, "y1": 200, "x2": 170, "y2": 235}
{"op": "wait", "ms": 2000}
{"op": "dialog", "accept": true}
{"op": "back"}
{"op": "switch_tab", "i": 1}
{"op": "give_up"}
{"op": "submit_answer", "text": "..."}
```

非法示例（必须拒绝）：

```json
{"op": "key", "key": "Control+u"}
{"op": "goto", "url": "https://www.google.com/search?q=walkthrough"}
```

### 16.3 示例配置（首题骨架，无谜底）

```json
{
  "id": "involuntary-appetite",
  "category": "arg",
  "arg_layer": "L1",
  "obs_mode": "B",
  "obs_modes_to_run": ["B"],
  "computer_use": false,
  "model_visible": {
    "title": "非自愿摄入",
    "intro": "你在一个本地托管的解谜作品里。只能用列出的动作，只根据屏幕上能看到的信息推理。不要假设能访问外网。"
  },
  "entry_url": "http://127.0.0.1:8766/live/index.html",
  "local_serve": {
    "enabled": true,
    "command": ["python", "mirror/serve_game.py"],
    "cwd": ".",
    "ready_url": "http://127.0.0.1:8766/live/index.html",
    "ready_timeout_s": 30,
    "port": 8766
  },
  "viewport": {"width": 1366, "height": 900},
  "locale": "zh-CN",
  "timezone": "Asia/Shanghai",
  "seed": 20261012,
  "allow_hosts": ["127.0.0.1:8766"],
  "shortcut_block": [],
  "guide_block_hosts": [],
  "allow_model_goto": false,
  "goto_scope": "none",
  "show_url": true,
  "text_scope": "page",
  "text_limit": 6000,
  "actions_enabled": [
    "click", "dblclick", "type", "key", "scroll", "drag",
    "back", "wait", "dialog", "give_up"
  ],
  "limits": {"max_steps": 80, "max_seconds": 1800, "max_answer_submits": 20},
  "settle_ms": 1200,
  "history": {"full_obs_k": 4, "screenshot_k": 2},
  "judge_path": "judge/involuntary-appetite/judge.json",
  "policy_script": [
    {"op": "wait", "ms": 1000},
    {"op": "scroll", "dir": "down"},
    {"op": "give_up"}
  ],
  "notes_for_report": ["ARG L1 本地镜像；无外网"]
}
```

对应 `judge/involuntary-appetite/judge.json` 骨架（钩子用**可见**固定文案/URL，由出题方补全；此处不写谜底）：

```json
{
  "hooks": {
    "on_entry": {
      "type": "url_regex",
      "pattern": "127\\.0\\.0\\.1:8766/live/"
    }
  },
  "checkpoints": [
    {"id": "entered_live", "hook": "on_entry", "op": "truthy"}
  ],
  "events": {},
  "ending": null,
  "answer_hash_file": null,
  "request_milestones": [],
  "submit_conclusion": {"enabled": false, "schema": null},
  "rubric_path": null
}
```

### 16.4 CLI 约定

```bash
# 校验
python scripts/validate_config.py configs/involuntary-appetite.json

# 起服务（若 run_one 未自动起）
python mirror/serve_game.py

# 假策略一局
python scripts/run_one.py \
  --config configs/involuntary-appetite.json \
  --policy script \
  --obs-mode B

# LLM 一局
python scripts/run_one.py \
  --config configs/involuntary-appetite.json \
  --policy llm \
  --obs-mode B

# 批量
python scripts/run_batch.py --set configs/pilot_set.json --policy llm --obs-mode B
python scripts/aggregate_runs.py --runs runs/ --out runs/aggregate.csv
```

### 16.5 依赖（建议写入 requirements）

```
playwright>=1.40
pydantic>=2          # 或 jsonschema
python-dotenv
httpx                # LLM
jericho              # P3；可选 extras
```

安装浏览器：`playwright install chromium`。

### 16.6 给 Cursor 的实现顺序提醒

1. 先读本文 §0、§3、§13；不要先做 LLM。  
2. P0 以《非自愿摄入》假策略绿为唯一里程碑。  
3. 每阶段单独 PR；验收勾选 §14。  
4. 任何 PR 不得添加谜底文件到非 `judge/` 路径；`judge/` 不得被 prompt 代码读取。  
5. 保持与 `mini_harness.py` 行为一致，除非本文明确升级（obs_mode、arg_layer、request_milestones、目录上移）。

---

## 修订记录

| 日期（Asia/Shanghai） | 说明 |
|---|---|
| 2026-10-13 | 首版：由 harness_design + 10-12 决策升级为产品级 Cursor 实现说明书 |

