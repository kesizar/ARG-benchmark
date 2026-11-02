# 隔离

默认关闭容器。每局使用新的浏览器 context，不继承 cookie、本地存储或缓存。

任务配置里的 `isolation.container` 必须是 `false`。把它设为 `true` 时，评测会直接拒绝启动，不会悄悄改走另一套网络。

运行层级独立于游戏类别，使用 `runtime_layer`，定义见 [runtime_layers.md](runtime_layers.md)。L1 的游戏请求只能访问本机；L3 使用游戏所需的明确域名白名单和攻略站拦截，仍然跑在本机浏览器里，不启动本地游戏服务。
