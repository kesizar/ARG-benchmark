from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];B=R/'tasks/yiwu-yuren';J=R/'judge/yiwu-yuren'
spec={
'record_id':'base664:0268','scope':'Live case001; accepted-commission desktop start. Other two commissions on shared index excluded.',
'reasoning_checkpoints':[
 {'id':'wechat','role':'optional','condition':'recover alexshen0110 with 183794677 then log in','evidence':['001/shenqinjianli.html old phone 138112805 and WeChat ID','001/yuxiaoli.html current contact 183794677'],'negative':['ordinary login always rejects','old phone is cancelled','malformed phone or unknown ID rejected'],'why_optional':'student dialogue can be reached independently'},
 {'id':'hospital','role':'optional','condition':'沈沁 / 2001-10-05 / 2025-03-01','evidence':['001/shenqinjianli.html birth clues','001/baodao.html death and hospital date','001/yiyuanjilu.html identity code 2132001100576'],'negative':'any absent or mismatched field rejects','why_optional':'not a route gate'},
 {'id':'outlook','role':'optional','condition':'identity recovery alex.shen@outlook.com / 2132001100576 / 183794677','evidence':['hospital identity code','professor current phone','resume email'],'negative':'wrong email, identity code or phone rejects; ordinary credentials undefined in original, fixed to reject'},
 {'id':'teacher','role':'optional','condition':'TH2021LA086 / 19780315','evidence':['001/yuxiaoli.html work ID and birthday'],'result':'001/zhigong.html reveals student ID 24071225','why_optional':'student ID can also be visible elsewhere; optional material is not mandatory reasoning credit'},
 {'id':'student_access','role':'route access, not separately scored','condition':'24071225 / 20250225','evidence':['teacher dashboard student ID','001/yitiji.html 2025-02-25 friendship day became passwords'],'negative':'wrong login never opens dashboard'},
 {'id':'identity','role':'critical','condition':'accepted reply 你是陈屿。 generates actual reply-item in student message thread','evidence':['WeChat friendship/park diary','001/xuesheng.html target message and reply validation']},
 {'id':'intent','role':'critical','condition':'accepted reply 你只需要告诉我你这样做是为了什么。','evidence':'001/xuesheng.html dialogue, asks purpose instead of joke or self-praise'},
 {'id':'killer','role':'critical','condition':'accepted reply 嫉妒她的周毅','evidence':['hospital injury inconsistencies','student diary recovery and husband jealousy','feeder transcript 2025-02-28','final confession dialogue'],'negative':'于晓丽 / 她自己 rejected'},
 {'id':'branch1/2/3','role':'route-specific critical','condition':'fifth-round accepted answer and final message generated','alternatives':{'该死':'我觉得俩人一样该死','不该死':'死亡对他这种人来说太轻了。','who cares？':'我不想毁了我的信誉 今天我就当没见过你'},'negative':'other two choices on each branch display error and do not advance'}],
'route_gates':{'ending1':['identity','intent','killer','branch1'],'ending2':['identity','intent','killer','branch2'],'ending3':['identity','intent','killer','branch3']},
'endings':[
 {'route':'ending1','page':'001/jj1.html','original_label':'结局一','outcome':'Chen plans revenge; professor killed by laboratory explosion, husband vegetative','tier':'normal'},
 {'route':'ending2','page':'001/jj2.html','original_label':'结局二','outcome':'Chen publicly reports misconduct and criminal evidence','tier':'normal'},
 {'route':'ending3','page':'001/jj3.html','original_label':'结局三','outcome':'withdraw from intervention; optional 30-second moon clicking minigame','tier':'normal'}],
'completion':'Every ending fixed-end-btn leads weituo summary; finish button sets caseCompleted[0]=true and returns index. Completion flag alone cannot full-score.',
'failures_and_exits':'No permanent game-over path in source. Incorrect logins/queries/replies are repeatable local rejection. Home power button exits to index. Student/teacher logout returns login. Park form and many university links are decorative no-ops. End3 timer expiration is minigame stop only, not ARG failure or additional reasoning point.',
'reset':'Fresh BrowserHarness context clears all game and judge latches. Original index re-investigate cancel leaves state; confirm clears caseCompleted[0], wechatLogged, outlookLogged and opens desktop. Notepad always clears custom cached notes on load.',
'judge':'Independent JSON evaluator uses generated accepted reply DOM, route-specific fifth-round final-message gate, and original ending label/path. Prior gates latch in harness Judge. No correct-answer constants or source files exposed to model. Optional navigation material is separately reported. Direct endpoint access lacks required reasoning gates.',
'risks':['Early replies remain replayable in original; repeated accepted replies generate duplicate branches but cannot bypass independent gate requirements.','Common completion flag loses ending identity, so it is optional and not route ending evidence.','Original source calendars include inconsistent birth/death/admission dates and 9-digit fictional phone numbers; exact accepted strings documented; difficulty not calibrated.','Shared home presents cases002/003 and university search research-student placeholder reaches fictional external host; these are outside case001. They are blocked by L1 whitelist; not scored.','Live root differs from supplied 35250-byte historical snapshot. Version is explicit, historical source preserved.']}
(J/'checkpoint-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
(B/'README.md').write_text('''# 遗物整理师 — 001 愚人节的短信

记录 base664:0268，任务 yiwu-yuren。本版本使用 2026-10-27 从原作者 GitHub Pages 获取的 case001。原始清单指向共享主页；本任务从已接受001委托的电脑桌面开始。002、003是独立案件，不属于本条任务。共享主页/联系表单保留用于退出及重开；主页其它案件和大学“研究生”虚构外链不在本地资源闭包与验收范围。配置禁止任意跳转，游戏仅允许本机主机。

启动：`python scripts/serve_static.py --root tasks/yiwu-yuren/mirror --port 8811`，打开 http://127.0.0.1:8811/001/window.html；Ctrl+C停止。配置运行：`python scripts/run_one.py --config configs/yiwu-yuren.json --policy script`（脚本策略仅give_up，用于接入）。Python 3.11+，按独立评测包requirements安装依赖，`python -m playwright install chromium`或使用已安装Edge。API密钥不包含在包中，本准备未调用模型API。

每局使用新浏览器context，裁判也必须重建。原作重开：任一结局→委托总结→完成委托→主页密语解锁→001接受委托→确认；取消保留完成状态，确认清除完成标记与两项本地虚构登录状态。联系页仅本地模拟，不提交真实信息，不需要真实账号。

图标CSS与字体已本地化；Google字体使用系统字体回退。兼容修复：邮箱普通登录原作访问未定义VALID_EMAIL/VALID_PASSWORD，改为明确显示错误，保留真正的身份找回通路；公园手记无来源返回时原来404的index.html改为预约页。原件及逐行diff位于judge/yiwu-yuren，不可托管给玩家。没有更改谜题答案、解锁条件或结局。

裁判侧checkpoint-spec.json记录推理点、全部路线、可重试失败和退出。三条原作结局均normal，未凭叙事喜好擅自分good/bad。微信/邮箱/病历/教师材料是可绕过证据，作为optional；主要推理按身份、目的、凶手及当前分支有效回复锁存，结局单页不能得到满分。第三结局点击月亮是休闲小游戏，不计作ARG推理点。难度和步数预算尚未用模型校准。

资源包只包含mirror玩家文件；prepared包包含配置、裁判、对应harness及审计工具，不可把prepared根目录作为网页根目录。独立解包仅验证当前Windows和已安装Python/浏览器基础依赖，不能代表全新操作系统安装验收。
''',encoding='utf-8')
print('wrote spec/readme')
