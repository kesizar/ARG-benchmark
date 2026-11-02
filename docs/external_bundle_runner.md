# 外置统一运行时：独立解包任务

使用工作区中当前的 `harness` 运行已单独解包的评测包，游戏、配置、裁判、运行日志和本地服务器的工作目录均指向该解包目录；不会改写原 ZIP，也不会修改解包目录中的裁判或游戏文件。运行会在解包目录创建 `runs/`、服务器与浏览器所需的运行时文件。

先准备独立解包目录。测试模式示例，路径按实际情况替换：

```powershell
.\mirror\harness\.venv\Scripts\python.exe scripts\run_external_bundle.py --bundle-root <独立解包目录> --config configs/<题目配置>.json --policy script --run-kind test
```

正式模式必须由调用者提供已冻结清单、模型环境、模型参数档案和重复局编号：

```powershell
.\mirror\harness\.venv\Scripts\python.exe scripts\run_external_bundle.py --bundle-root <独立解包目录> --config configs/<题目配置>.json --policy llm --run-kind official --manifest <冻结清单路径> --repetition 1
```

正式模式会按共享 `harness.loop` 校验预算、截图、清单与配置/裁判哈希及模型参数档案。启动器不会自行提供这些字段，不会将测试局标为正式局，不会修复已有配置或冻结题集；如果配置的预算、截图要求、模型或清单未满足约束，正式运行会被拒绝。历史包中的运行时不会因此改变；此模式依赖同事可获取的同一版本工作区代码和 Python/浏览器环境。

当前离线测试仅检查参数传递、目录限制及正式模式不接受脚本策略；未因这项适配调用付费模型，也未对所有游戏做正常 UI 或完整部署验收。候选包是否可在新 harness 下正常运行，须另记针对受影响接口的验证结果。将该启动器用于正式评测前还需冻结共享 harness 的版本及依赖，并完成相应验收。

## 候选包内置运行时

`packs/protocol-v1-b-candidates/` 的候选包额外包含 `_protocol_runtime/`，可以在独立解包目录内使用该运行时；游戏、原评测代码和原包均保留。以已有 Python 环境执行：

```powershell
<Python解释器> <解包目录>/_protocol_runtime/scripts/run_external_bundle.py --bundle-root <解包目录> --config <包内配置相对路径> --policy script --run-kind test
```

43 个候选包均通过目标字段、B 档截图字段和包内运行时代码的结构检查。《2TorEEale》已在独立目录用候选包启动并脚本退出，输出了新版目标与进度字段；这是一次接入冒烟，不代表其他游戏或完整流程已经验收。正式运行仍需事先冻结符合协议的参考轨迹、预算、模型档案和题集。
