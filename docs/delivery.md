# ARG-benchmark 统一交付使用说明

交付目录包含一份固定共享运行时、`packages/` 中的原始 ZIP、冻结入口清单 `catalogue.json` 和文件校验清单 `RELEASE.json`。每次运行都使用交付目录中的共享运行时，不使用旧 ZIP 内的历史运行时。修改代码或替换题包后应重新生成版本，不能混用旧版本结果。

这是工程交付版本。暂计合格、工程检查通过、正式实验验收是不同状态；本目录不把历史资源验收自动变成正式题集。完整游戏和限定章节/目标保留各自范围。已知不兼容条目仍随资源交付，并在入口清单中明确阻塞原因。

## 同事首次安装（Windows）

需要 Python 3.11，联网安装依赖与 Chromium。请在此目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

安装脚本仅对本次 PowerShell 进程设置执行策略，创建此目录的 `.venv`，安装锁定版本依赖、Chromium，并在 `.env` 不存在时创建配置模板。已有 `.env` 不会覆盖。Python 解释器可用 `-Python <python.exe完整路径>` 指定。

这份锁文件记录了实际验证环境的版本；未随包附带 Python、浏览器或离线 wheel，跨系统环境仍需验证。

依赖锁也包含所选 Baba 网格任务的 NumPy、Gym、绘图库等依赖。该任务原配置使用 A 档文字网格观察，直接通过网格适配器运行，不需要文字冒险解释器。

编辑交付目录根下的 `.env`。所有题目共用这一份配置，无需往每个 ZIP 填密钥：

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=填自己的密钥
OPENAI_BASE_URL=https://自己的兼容服务地址/v1
OPENAI_MODEL=账号实际可用的模型ID
```

原生 Anthropic 接口见 `delivery.env.example`。当前环境变量优先于 `.env`。`LLM_MAX_OUTPUT_TOKENS` 留空时，测试模式默认 1024，正式模式默认 32768；实际模型限制和推理参数需要在正式实验前核实。不要把自己的 `.env`、`.venv` 或含模型输出的 `work/` 重新发给别人。

## 同一入口

```powershell
.\run.ps1 list
.\run.ps1 list --all
.\run.ps1 doctor --browser --api
.\run.ps1 verify --all
.\run.ps1 smoke --task base664:0169
.\run.ps1 run --task base664:0169
.\run.ps1 batch --all-local --dry-run
.\run.ps1 batch --task base664:0169 --task added84:0048
```

也可将 `.\run.ps1` 换成 `.\.venv\Scripts\python.exe benchmark.py`。

- `list` 显示可经共享运行时启动检查的条目；`--all` 同时显示阻塞条目及原因。用精确 key 选择多单元记录。`PRECHECK OK` 只是工程配置检查通过，不等于完成真实 API 或完整游戏验收。
- `doctor --api` 只检查密钥和模型字段是否填写，不连接供应商、不消耗 API。`--browser` 实际启动并关闭 Chromium。
- `verify --all` 重新核对全部共享代码和资源 ZIP 的 SHA-256。`--task KEY` 只核对共享文件与所选资源。
- `smoke` 不用 API；在独立解包副本中观察初始界面、执行一次 `give_up` 并保存结果。它不代表通关，不计正式成绩，也不证明全部交互可用。L3 任务仍会访问实际游戏网站。
- `run` 默认调用填写的模型，属于测试局，会产生供应商费用。`--policy script` 可使用包内原有脚本策略。
- `batch` 串行执行明确选中的题目；`--all-local` 选择工程检查通过的 L1 条目，排除在线 L3。先用 `--dry-run` 查看范围，不调用模型。默认每题测试一局；`--repeats N` 可指定次数。批次遇单题错误会记录并继续，最终非零退出表示存在失败尝试，不代表模型得分。
- 每次生成独立 `work/<会话ID>/bundle/`，避免上次存档污染；运行记录在其中的 `runs/`，会话凭据说明在 `receipt.json`。不能同时运行使用同一端口的题目。

`TEST ONLY` 表示可测试启动，但正式入口配置检查尚有阻塞；`BLOCKED` 表示现有包不能直接走该共享入口。专用解释器、特殊后端与在线账号条件需要按条目说明补齐。本工具不会静默修改原始配置或绕过检查。

## 正式运行

正式实验另需经过确认的题单、参考预算、模型参数指纹、重复次数和验收证据。`RELEASE.json` 固定的是交付内容，不能替代实验的 manifest。当前入口保留原正式约束：

```powershell
.\run.ps1 run --task base664:0169 --official --manifest .\experiment.json --repetition 1
```

需在 `.env` 填写相应 `LLM_EXPERIMENT_PROFILE`。模型参数、配置和裁判的哈希必须与实验 manifest 一致。旧包缺字段会明确拒绝；修复后要重新冻结配置与版本。正式模式不接受脚本策略。

共享裁判支持原包已有的 `target_success.hook_condition`：指定目标达成会单独终止本局，不会因此标成原游戏结局或好结局。严格读取钩子的网页、存储或网络错误会让该局报错，不能作为模型未成功计分。

正式批次使用 `batch --official --manifest experiment.json`，题目与重复次数来自该 manifest，不使用 `--all-local`。遇基础设施错误记录为失败尝试，本入口不会自动把失败局换成新局、补足有效重复或算作模型零分。重跑必须按已冻结实验规则另行安排。

统一入口可收集 `work/` 下的会话，交给现有正式评分器汇总：

```powershell
.\run.ps1 report --manifest .\experiment.json --out .\report.json
```

测试局、版本不匹配和无效记录按原协议排除；缺失 summary 的会话另行记录。重复的有效局不会自动挑选成绩，评分器会拒绝重复计分。单个包的任务规格不含已验收模型档案，不能直接当成完整实验 manifest。旧的 `scripts/report_protocol.py` 仍要求 `<task>/<mode>/<run>` 布局；使用统一入口时无需人工整理这些目录。

## 维护者生成新交付

从工作区执行：

```powershell
python scripts/build_delivery.py --out dist/arg-benchmark-新版本
```

默认快照当前主索引中全部 `provisional` 与 `scoped_provisional` 记录，保留排除记录的元数据。可多次使用 `--record 原始ID` 生成明确子集。已存在的输出目录不会覆盖；未完成的构建保留 `BUILD-INCOMPLETE.json`。源 ZIP 与索引哈希不符时停止，避免把正在变动的题包误封为固定版本。生成后至少执行 `verify --all`、环境检查和代表性独立解包测试，再交付整个目录。

2026-11-02 的阻塞修复沿用 r1 的同一批 374 个原始记录。修复包及逐文件不变性检查位于 `packs/handoff-repairs-20261102-r2/`；使用其中的 `index.json` 构建后续交付，避免混入主索引的后续变化。原 ZIP 与 r1 交付保留。配置修复只涉及类别别名、截图必需标记、实际 task ID、未启用的专用提交动作额度，以及记录既有动作上限例外；游戏内提交按钮、重试次数、答案和裁判定义保持原样。历史验收中的范围限制、人工预算未校准和非盲解等说明仍然有效。

r2 的 `startup-validation.json` 记录本轮 52 个修复包的独立启动验收，并通过 ZIP 哈希与目录条目绑定；其余未改动包沿用已有证据，不冒称本轮全部重新跑过。归宁旅馆在线入口在本轮曾出现连接超时/断开，随后新上下文复验通过；此结果不能保证未来网络或站点状态。启动验收不调用模型 API，也不等于盲解、全路线验收或正式实验题单冻结。
