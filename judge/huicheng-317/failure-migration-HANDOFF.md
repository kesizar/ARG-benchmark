# 0358 failure migration

作者 CONTENT_AUDIT 明示理智零提前失败且不解锁 A–D，dragged 已迁至 terminal_failures；A–D 原有正式剧情路线保持 normal。

独立包真实 loop 验收 50 次错误触发 dragged 失败、49 次负例、C 正常通关、新 context 重置，见 runs/huicheng-317-failure-migration/verification.json。旧完整 UI 与支线验收以游戏及未变文件逐字节比较复用；后续仅更新说明及专属 judge 回归脚本，并确认运行时、judge、游戏字节不变。旧包保存在 packs/huicheng-317.pre-failure-migration.prepared.zip。
