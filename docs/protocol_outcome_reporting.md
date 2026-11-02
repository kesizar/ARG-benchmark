# 结局与终局失败的汇总字段

`harness.protocol_report.report` 接受预先冻结的题目清单。每题可用两个布尔字段声明统计范围：`good_ending_scored` 和 `terminal_failure_scored`；不写或填 `false` 表示不纳入相应统计，不表示游戏没有好结局或终局失败。清单应在运行前确定并随每局版本标识冻结。

每局的好结局需要 `good_ending`、`ending_reached` 和对应的 `ending_tier`，未到结局须明确记录 `ending_reached=false` 且 `good_ending=false`；已到结局须标明 `good`、`normal` 或 `bad`，并与 `good_ending` 一致。无等级或信息冲突按缺失处理。终局失败需要布尔值 `failure_reached`，不能用坏结局或普通错误替代。缺失字段不等于 false。

输出的逐题 `good_ending_rate`、`terminal_failure_rate` 只在该题声明纳入、计划有效局数齐全且该指标各局均有记录时计算。逐题 `*_observed_runs` 是能判定的局数。模型级 `*_tasks` 与 `*_completed_tasks` 给出覆盖范围与完整题数；对应 `*_rate_macro` 按题等权，仅当范围非空且范围内每题均完整时计算，否则为 null。模型间只比较相同冻结题单与范围。
