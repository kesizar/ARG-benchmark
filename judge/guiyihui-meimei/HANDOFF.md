# HANDOFF

逐关审计 `level-audit.json`；16 个可选候选，11 个新增点独立正常 UI 正误、提示、自动跳过全部通过，见 `verification/new-points-acceptance.json`。完整 50 关与 B/C/D 在新裁判下通过 `verification/all-points-acceptance.json`。两包解压验收与新评测包哈希见 `judge/guiyihui-meimei/deployment.json`。原游戏 15 文件、旧失败测试 harness 23 文件、失败 hook 及声明等价见 `verification/byte-equivalence.json`；原始 9900 秒和一秒失败 loop 据此复用。评测包不含一秒测试副本。

43、49 未找到题面所称来源；10、41、47 有缺陷，均排除。24 的 AETHER 可从日记直接抄录，即使题面要求字母重排。英译题存在同义词或难度争议；候选分类及结局等级待主代理复核，formal=false。

8821 被其他服务占用并返回 404；测试改用 8822，独立包用 8822/8823，见 `verification/port-diagnostics.json`。默认配置仍使用 8821，若被占用需替换配置端口。
