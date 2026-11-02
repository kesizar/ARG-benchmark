# ARG-benchmark

用 ARG 和其他解谜测试模型的多种能力。总的能力框架尚未定名。

给同事交接请先看 [统一交付说明](docs/delivery.md)：通过 `scripts/build_delivery.py` 生成固定版本目录，随后统一使用 `run.ps1` / `benchmark.py` 列题、检查、试跑和执行。源码工作区本身不是已冻结交付版；正式实验清单需单独验收与冻结。

游戏类别与运行方式独立配置：所有类别均可使用 `runtime_layer` 标记本地 L1 或真实在线 L3。定义、迁移兼容和 API 验证说明见 [docs/runtime_layers.md](docs/runtime_layers.md)。

当前题是《非自愿摄入 / INVOLUNTARY APPETITE》。模型在本机浏览器里调查这份镜像，不访问原站。

- `mirror/involuntary-appetite/`：游戏镜像
- `mirror/serve_game.py`：本地服务，`http://127.0.0.1:8766/live/index.html`
- `mirror/harness/`：早期调查 agent，仍可 `python mirror/harness/run.py --selfcheck`
- `harness/`：评测循环。模型只看 `model_visible` 和自己写的笔记；裁判在 `judge/`

密钥放在仓库根目录的 `.env`，字段见 `.env.example`。

假策略跑《非自愿摄入》（会自己拉起本地服务）。本机 Playwright 在 `mirror/harness/.venv`：

```bash
mirror\harness\.venv\Scripts\python scripts/validate_config.py configs/involuntary-appetite.json
mirror\harness\.venv\Scripts\python scripts/run_one.py --config configs/involuntary-appetite.json --policy script --obs-mode B
```

结果在 `runs/involuntary-appetite/B/<时间>/`。`steps.jsonl` 给复盘，`judge.jsonl` 只给裁判。说明见 `docs/harness_spec.md`。

接入下一道真题不用改 harness，步骤在 `docs/add_task.md`。生成空目录：

```bash
mirror\harness\.venv\Scripts\python scripts/new_task.py --id my-game --category web_puzzle --port 8770
```

文字冒险把 `.z5` 或 `.z8` 放到配置里的 `if.story_file`，并安装 `jericho`。容器隔离默认关闭，见 `docs/sandbox.md`。
