# 游戏类别与运行层级

当前数据准备使用两个独立维度。`category` 描述游戏类别，`runtime_layer` 描述运行时是否依赖真实外部环境。这个定义替代旧规格中仅对 ARG 使用 `arg_layer` 的约定。

## 运行层级

- L1：游戏依赖的材料、逻辑和状态均可在本地提供。可以是静态文件、完整网页镜像、文字冒险解释器或本地工具场景。多个页面或域名的原作，只要完整本地化，仍可属于 L1。允许访问的游戏主机仅为本机地址；外部资源请求会被拦截。被测模型 API 是评测基础设施，不属于游戏外部依赖。
- L3：游戏仍需真实在线页面、远端服务或账号状态。允许游戏实际需要的明确主机白名单，不要求只能有一个域名；禁止任意外网访问和攻略搜索。不启动本地游戏服务。每局仍使用本机浏览器的新 context。

本阶段新配置只使用 L1 和 L3。历史 L2“封闭材料”本地夹具迁入 L1，旧文件名保留以免破坏调用路径。旧运行报告中的 L2 不重写、不冒称已符合新定义，汇总时保留历史标签。其他没有层级信息的旧报告保持未分类，不猜成 L1。

`runtime_layer` 分类只表示配置中的运行方式，不是资源完整性或正式题目准备完成的证明。比如在线网页配置可标为 L3，但仍可能暂时无法访问、缺失判分点或无法重置。

## 配置示例

```json
{
  "category": "web_puzzle",
  "runtime_layer": "L1",
  "account_requirement": "none"
}
```

网页解谜也可以填 L3；ARG 也可以填 L1。账号需求使用独立的 `account_requirement`，取值为 `none`、`test_account` 或 `unknown`，缺省为 unknown，不将未核查的游戏自动标成无需账号。

账号题还需要独立准备可用测试账号、登录方式、每局状态恢复和远端副作用处置。目前没有自动注入账号或复用登录态的实现；本次两条 API 测试均无需账号，不能据此认定账号通路已验收。

新任务使用 `scripts/new_task.py --runtime-layer L1` 或 `--runtime-layer L3`，不再受游戏类别限制。静态题和文字冒险的当前生成模板仅支持本地通路。在线模板需填写真实游戏入口、主机和裁判，生成模板不等于完成题目。

## 日志与兼容

新 `summary.json`、CSV 与 Markdown 汇总输出 `runtime_layer`，按 `category × runtime_layer × obs_mode × model` 分组。历史 summary 仍可从 `arg_layer` 读取原标签。加载旧任务配置时有兼容识别，但新 schema 要求显式的 `runtime_layer`。

本次配置迁移按现有入口和已有层级进行，没有重新判定 748 条原始记录的资源完整性。迁移记录见 `data/preparation/runtime-layer-migration.json`，全配置检查见 `data/preparation/runtime-layer-validation.json`。

## 真实模型 API 冒烟验证

本次使用同一作品分别验证本地 L1 和原站 L3，减少作品差异对链路判断的影响：

```powershell
$env:OPENAI_MODEL='deepseek-flash'
mirror\harness\.venv\Scripts\python.exe scripts\run_one.py --config configs\samples\wuluo-cun-api-smoke.json --policy llm
mirror\harness\.venv\Scripts\python.exe scripts\run_one.py --config configs\samples\wuluo-cun-l3-api-smoke.json --policy llm
```

每条只运行四步，要求接口实际接收 B 档截图，不能在图片失败后偷偷降为文字测试。它验证真实 API 返回动作、浏览器推进、裁判读取和日志生成；不要求通关，也不能代替对每条数据的完整流程验证。

DeepSeek 官方文档说明 `deepseek-flash` 当前由 DeepSeek-V4.1-Flash-1017 提供服务。接口响应只返回该别名，没有独立版本号；本次版本判定依据为官方映射：[官方调用说明](https://api-docs.deepseek.com/quick_start/agent_integrations/)。

实际运行证据及适用范围保存在 `data/preparation/harness-api-smoke.json`。本次未验证账号题、多个真实域名间的跳转或所有不同解释器与工具适配。
