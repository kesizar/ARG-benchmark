# HANDOFF — 五行续命坛 / base664:0214

结论：四幕主案工程、独立裁判和正常 UI 验收完成；不将整个门户的四部另名往期小游戏算作已经准备。总体保守留 scope/content review，勿直接计入748条全标准完成。

沿用 task ID wuxing-xuming；端口8831–8833均已停止。原来的214快照正文经忽略空行/换行后与原站恢复 index完全一致（snapshot-live.diff为空），不是新编页面。主案4 HTML+26 PNG+1 MP4共31文件，图像全部解码、视频1280x720/5.041667s可播，全部文件HTTP hash正确。原件在 source，网络 MIME/hash请求见 recovery-audit.json。

configs/wuxing-xuming.json 为L1/no account。19个推理点，3个检索诊断。密码必须解锁成功DOM，输入15未提交0分；五尸须真实5/5阵图，不再用原作重置后遗留的enabled按钮。A/B只是中间等价文本支线，正式终局仅act4一个。无失败结局，误答可重试。源码 checkFinish / runCompare / pickFrag / clickSlot / openFinale和条件见 checkpoint-spec.json。

最终双包已分别独立解包以新context全程验收：runs/wuxing-xuming/deployed-game 与 deployed-evaluator，各PASS60阶段、完整19/19；每个时间链与照片有负例，空/错/未提交、回放、局部重置、刷新、新context、新裁判、返回后新卷宗是/否均覆盖。page_errors为空；Windows Edge156.0.4314.42。验证标准包另以stdlib静态服务器检验31文件、视频、评测端路径404、评测manifest67-entry包内哈希全通过；证据 deployment-integrity.json。

关键风险：原作act3允许不做资金/指纹直接拼时间链；act4只要求5照片，化名问题与前幕非必经，实测仅5点评分也能终局；裁判未虚构必经门。resetMarks没有重新disable下一幕按钮；原样保留并正确判分。人物/资金/指纹文字前后有矛盾，AFIS与照片匹配难度低。两处兼容diff仅去统计SDK与将结尾旧沙箱回跳本地首页，不改谜题。

下一步只需主代理核对main-case scope：主页girls-traces/silent-judgment/jiangwan-land/vanished-flight为另名往期作品，未做全资源/全UI。恢复crawl首次误把这些作品相对图片当root请求，HTML回退误图已留MIME证据而不进入游戏包；若需要整门户，按各自页面URL做urljoin的正确递归恢复，不能用这些错误响应宣称素材缺失或站点失效。不要重复已经两次完整通过的四幕主案。

包：packs/wuxing-xuming.game.zip（纯游戏）；packs/wuxing-xuming.prepared.zip（评测隔离）；packs/wuxing-xuming.recovery.zip（恢复证据）。精确hash见delivery-manifest.json与result。资源不依赖任何账号或在线服务；无API调用、购买、push。未验证跨OS或真实模型API。
