# 0604 failure migration

六项错误统一调用 badEnding(pid)，显示 #view-bad，唯一操作为重新开始：failure_pd、failure_pd2、failure_decode、failure_sort、failure_pw、failure_pf 改为 terminal_failures。三个正式故事抉择 A/B/C 保持正常结局。

独立包真实 loop 验收 pd 错误、错误前负例、C 正式结局、新 context 重置，见 runs/wuren-li-an-failure-migration/verification.json。其余五种错误及各选项复用旧完整 UI 验收；游戏和其他非 harness 非 judge 文件逐字节等同，六种 hook 的表达式保持不变。旧包保存在 packs/wuren-li-an.pre-failure-migration.prepared.zip。
