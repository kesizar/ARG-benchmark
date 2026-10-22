# 接入新题时的请求检查

1. 用假策略打开入口，看 `summary.json` 的 `blocked_hosts`。
2. 作品自己的脚本、字体、图片如果被拦，把对应主机加进该题的 `allow_hosts`。广告和统计域名保持拦截。
3. 带答案参数或调试参数的地址写进 `shortcut_block`，不要只靠提示词。
4. ARG L2/L3 把攻略站样例留在 `guide_block_hosts`。默认名单可以包含 `*walkthrough*`、`*spoiler*`、`*solution*`、`*guide*`。这些通配只对比主机名，页面路径里出现同样的词不会被拦。
5. 不要把裁判钩子、答案或检查点名称写进 `model_visible`。
