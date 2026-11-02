# 当前正式实验：交接与执行

本轮直接进行正式实验。题目、资源、配置、裁判、观察方式和预算固定在 `formal-v1/task-plan.json`，每题每模型计划 3 个有效独立局。后续新增题目或修复版本进入下一版题单，不自动加入本批。

题单采用原始记录 ID 作为正式评测 ID；同名游戏不会混合计分。373 题沿用 B 档，网格题沿用其 A 档；同一题在所有模型之间使用完全相同的观察条件。SR 按题等权；Progress 仅在已明确列入的子集上汇总。未验证的描述性能力标签保留在题单，但本轮不计算能力分组或均衡分。范围限定的章节或目标按原范围报告，不能表述为整部游戏完成。

## 同事执行

1. 复制整个正式交付目录，使用 Python 3.11，运行 `powershell -ExecutionPolicy Bypass -File .\setup.ps1` 安装锁定依赖。
2. 复制 `formal-v1/models.example.json` 为 `formal-v1/models.local.json`。按确认的模型名单填写实际 API 模型 ID、服务地址、参数，并将选中的模型设为 `enabled: true`。
3. 在交付目录的 `.env` 或进程环境中设置各模型的密钥变量。模型 JSON 中的 `api_key_env` 只填写变量名称，禁止填写密钥值。不同模型可使用不同变量。该文件和密钥不进入结果归档。
4. 生成各模型的正式运行清单：

```powershell
.\run.ps1 experiment prepare-models --plan .\formal-v1\task-plan.json --models .\formal-v1\models.local.json --out .\formal-v1\models
```

此命令只固定参数与指纹，不向模型发请求。清单已经存在时不会覆盖；变更参数须另建版本。同事应填写实际接口接受的输出上限和推理参数，不能运行中自动降档或改用另一模型。

5. 执行正式实验（将 `model-id` 换成所选模型的 `id`）：

```powershell
.\run.ps1 experiment run --manifest .\formal-v1\models\model-id\manifest.json
```

同一交付目录一次执行一个模型，以避免游戏端口冲突。可按目录顺序运行所有已登记模型：

```powershell
Get-ChildItem .\formal-v1\models\*\manifest.json | Sort-Object FullName | ForEach-Object {
  .\run.ps1 experiment run --manifest $_.FullName
}
```

同一命令可用于继续中断的实验。已经记录的有效局（包括未成功的有效局）不会重复执行。每局从独立解包目录和新环境开始。每个模型计划 374 × 3 = 1,122 个有效局。

## 异常与结果

- 网络连接错误、超时及 HTTP 429/500/502/503/504 按固定规则处理：单次请求最多 3 次，整局最多 3 次独立尝试；仍无有效结果则记为缺失，不记模型零分。
- 鉴权、模型不存在、参数不支持以及不可重试的运行错误停止当前模型。保留错误记录，按真实原因处理；不得把失败响应当作模型作答。变更模型参数需登记新版本。
- 若只是纠正密钥或账号权限，且模型、端点及参数不变，可在同一命令后追加 `--retry-auth-error`，使用剩余额度继续先前的 401/403 错误局；仍保留原错误记录，最多 3 次独立尝试。
- 合法放弃、预算耗尽、游戏内失败是有效结果，禁止为改善成绩重新执行。
- 每模型的 `execution.json` 保存进度；原始日志、截图和裁判记录在 `work/official-*/`。密钥不会写入清单。
- 在线 L3 题保存实际执行时间和错误记录；站点、账号和网络状态可能变化，不能当成可离线冻结的条件。

汇总所有同题单模型：

```powershell
.\run.ps1 experiment report --plan .\formal-v1\task-plan.json --models-dir .\formal-v1\models --out .\formal-v1\results.json
```

只在每题的计划有效局都齐全时输出该模型的完整主榜分数；否则保留缺失、覆盖率和逐题数据。各模型的任务清单哈希必须相同，不能混合新旧题单。配置、裁判、资源、代码或模型参数变化后，保留旧实验并创建新版本。
