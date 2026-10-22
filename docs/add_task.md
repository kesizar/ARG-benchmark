# 接入一道真题

harness 不用改。每道题只加配置、材料和裁判。主榜默认有一本笔记：模型用 `note` 替换整篇内容，之后每步都能看到。不提供按步回看旧截图。对照可以在配置里写 `"notebook": {"enabled": false}`。

```bash
mirror\harness\.venv\Scripts\python scripts/new_task.py --id my-game --category web_puzzle --port 8770
```

ARG 加上 `--layer L1`、`L2` 或 `L3`。文字冒险用 `--category text_adventure`，把 `.z5` 或 `.z8` 放到配置里的 `if.story_file`。静态题用 `--category static`。

然后：

1. 用作品文件替换 `tasks/<id>/mirror/`，或放上故事文件。
2. 只在 `model_visible` 里写给模型看的题面。
3. 在 `judge/<id>/judge.json` 里写钩子。答案用 SHA-256，不要写明文。主分按路线记，不把可跳过的支线放进分母。
4. 把 `configs/<id>.json` 加进 `configs/pilot_set.json` 的 `tasks`。

主分是三列：通关率、路线进度、好结局率。步数只作效率。

- 一条路线只列这条路绕不开的门。可跳过的谜放进 `optional` 或 `events`。
- 多结局在 `routes` 里分条写，`tier` 用 `good`、`normal` 或 `bad`。走到任一真正结局都算通关。死亡、入狱、点错即失败不算结局。
- 没写 `routes` 时，全部 critical 门合成一条 `good` 路线。
- 页码比例、不同网址的个数、打开目录页，只能放进 `events`。
- 正式题要有结局。`configs/fixtures/` 里的接线夹具可以只有浅层的 `entered`，它们不进主榜。
- 没有可计分的门、也还没答对时，`progress` 留空。只有答案、没有门的题，答对后进度为 1，并记作好结局。汇总里的 `mean_progress` 跳过进度为空的局；`endings_rate` 和 `good_endings_rate` 仍按全部局数算。

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
