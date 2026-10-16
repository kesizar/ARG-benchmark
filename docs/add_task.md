# 接入一道真题

harness 不用改。每道题只加配置、材料和裁判。主榜默认有一本笔记：模型用 `note` 替换整篇内容，之后每步都能看到。不提供按步回看旧截图。对照可以在配置里写 `"notebook": {"enabled": false}`。

```bash
mirror\harness\.venv\Scripts\python scripts/new_task.py --id my-game --category web_puzzle --port 8770
```

ARG 加上 `--layer L1`、`L2` 或 `L3`。文字冒险用 `--category text_adventure`，把 `.z5` 或 `.z8` 放到配置里的 `if.story_file`。静态题用 `--category static`。

然后：

1. 用作品文件替换 `tasks/<id>/mirror/`，或放上故事文件。
2. 只在 `model_visible` 里写给模型看的题面。
3. 在 `judge/<id>/judge.json` 里写钩子。答案用 SHA-256，不要写明文。主分只放必经解谜门。
4. 把 `configs/<id>.json` 加进 `configs/pilot_set.json` 的 `tasks`。

主分检查：

- 每个 critical 检查点用一句话写明：不解出对应的谜，玩家到不了这个状态。
- 页码比例、不同网址的个数、打开目录页，只能放进 `events`，不能当 critical。
- 正式题要有 `ending`。`configs/fixtures/` 里的接线夹具可以只有浅层的 `entered`，它们不进主榜。
- 还没有 critical 检查点时，`progress` 留空。汇总里的 `mean_progress` 跳过这些题；`endings_rate` 仍按全部局数算。

检查并开跑：

```bash
mirror\harness\.venv\Scripts\python scripts/validate_config.py configs/my-game.json
mirror\harness\.venv\Scripts\python scripts/run_one.py --config configs/my-game.json --policy script
mirror\harness\.venv\Scripts\python scripts/run_one.py --config configs/my-game.json --policy llm
mirror\harness\.venv\Scripts\python scripts/run_batch.py --set configs/pilot_set.json --policy script
mirror\harness\.venv\Scripts\python scripts/aggregate_runs.py --runs runs --out runs/aggregate.csv
```

第一次接入时看 `summary.json` 的 `blocked_hosts`。作品自己的资源域名加进 `allow_hosts`，攻略站留在 `guide_block_hosts`。清单见 `docs/cdn_checklist.md`。

`configs/fixtures/` 里的三道是通路夹具，不是正式题。正式清单只跑 `pilot_set.json` 的 `tasks`。
