# 0359 failure migration

五次错密触发假结局循环，loop_failure 已改为 terminal_failures；真、坏、隐藏剧情结局原路线及遮挡检查保留，source-view 限制不变。

独立解包真实 loop：五错终局失败、四错负例、坏剧情结局仍成功结束、新 context 重置，见 runs/fangjian404-failure-migration/verification.json。包清单通过，旧完整 UI 证据复用前核对原包游戏及其他非 harness 非 judge 文件逐字节一致。旧包为 packs/fangjian-404-yingzi.pre-failure-migration.prepared.zip。
