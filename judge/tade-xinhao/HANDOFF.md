# HANDOFF base664:0312 她的信号

状态：partial_recovery_not_ready，勿计ready。结果：data/preparation/results/base664-0312.json。

固定commit 171cbd747cfe4d717c7bfe41f6e113d3f390d4e4，235文件上游zip保存在tasks/tade-xinhao/source/upstream.zip；225玩家文件已恢复，入口原件字节不改；开发脚本和文档隔离在source/developer。没有丢失字面依赖，无真实账号或运行后端。

两包独立解包位于runs/tade-xinhao/deployments/{game,prepared}。分别8832、8833验首门正负/重置，通过；全部225玩家文件逐字节一致。全部五结局仅做独立裁判DOM识别单测，不是正常通关。原8831同样验收首门。服务随验证停止，无持久后台。

候选configs/tade-xinhao.json；judge无正式计分点，22地点事件/5结局hook，不应跑模型分数。路线审核在flow.json和review.md。下一步需解决原作真实搜索及下载/音图处理能力边界，再做五完整路线、失败支线和正式门。UI重置不清交易计数/首次提示，所以每局新context；全分支重置未证明。

复用命令：mirror/harness/.venv/Scripts/python.exe judge/tade-xinhao/verify_sample.py --port 8831（需要具体浏览器命令escalation）。它明确只做partial，不要升级声称完整验收。Python脚本/流程证据是私有侧资料，不托管。未改共享harness/progress，未用模型API、购买账号或push。

明确接入缺条件：原pk-unzip-hint.html要求外部解压软件；PNG/ZIP混合文件及assets/extract_lsb.py（需ffmpeg）原样保留。当前harness不提供下载后解压/外部工具动作，尚未满足原作文件谜题能力条件。详file-tool-conditions.json。不要把这些文件误报损坏或向模型提供私有答案。
