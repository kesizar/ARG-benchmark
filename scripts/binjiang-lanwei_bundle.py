from pathlib import Path
import json,zipfile,hashlib,shutil,sys,subprocess,importlib.metadata
R=Path(__file__).resolve().parents[1];T='binjiang-lanwei';P=R/'tasks'/T;J=R/'judge'/T;D=R/'runs'/T/'deployment'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'README.md').write_text('''# 滨江新城烂尾楼案

base664:0159，固定公开仓库 4b04da413dd868ddfdfea383953a88905d46c178。历史入口原件保留；当前入口规范化文本相同。mirror/19文件包含18个HTML及README。仅移除装饰Font Awesome CDN链接，diff见私有judge目录。

工程源码辅助UI回放，非模型解题证明，正式评分未批准。入口要求警号但初始可见内容无警号；后续案卷/微信才有，模型提示未补答案。8个密码支线全可绕过；原作好结局只检查赵翔宇和已搜到的监控关键词，未检查是否打开/解密监控。资源中地址、PDF下载、视频均为原作模拟展示，无真实邮箱/下载/视频依赖。无账号、摄像头或付费API。

启动：python scripts/serve_static.py --root tasks/binjiang-lanwei/mirror --port 8831；http://127.0.0.1:8831/index.html；Ctrl+C停止。只托管mirror，不能托管评测根目录。每局使用fresh browser context清除全部localStorage和临时状态；结局“重新开始调查”保留发现证据/搜索历史，文档解密刷新即重置。

标准接入：python scripts/run_one.py --config configs/binjiang-lanwei.json --policy script。私有全流程：python judge/binjiang-lanwei/verify_sample.py --port 8832。基础环境Python3.11+，requirements.txt列依赖，安装Edge或Playwright Chromium；不随ZIP附带浏览器/解释器。不代表跨操作系统验收。

未使用monitor.html仅为死映射，没有可点击入口，不将其宣称为有效支线。打印/备忘录下载仅原作系统动作或提示，不生成真实证据PDF。原作报告证据标签可能双切换，用真实复选框选择；不修改题目判断。原作记事本最小化后再次打开不恢复transform，刷新桌面可继续案件，不更改该原作缺陷。

原作第三结局重写警情内容时移除ending3Exploration，随后“重新开始调查”在updateProgress产生null.textContent异常；显示搜索页但更新未完整执行。两份解包均复现，未隐藏该错误。每局fresh context可完整重置并通过全部路径，不能以菜单重开代替完整重置。
''',encoding='utf-8')
(J/'review.md').write_text('''# 私有复核

无每条路线必经的密码推理门。真相结局=正确嫌疑人+监控已搜索且选择；证据不足=正确嫌疑人+其他证据；冤枉好人=非屏蔽错误嫌疑人+至少一证据。空/警员姓名/无证据为重试失败，无结局无分。8个optional候选为camera/old_case/mail/shepherd/server/ark/daughter/forum；独立裁判仅读已显示的目标DOM并由harness锁存，不写游戏状态；普通入口/检索/翻页/收集无分。结局不采用localStorage标记，不会将已搜监控当监控解密。

入口051383仅可私有审计诊断，初始缺线索，formal=false。mail日期可从江川入职信息得出；old_case坐标来自邮件老灯塔N31 15 42.8 E121 28 26.3去符号，但邮件另一个云盘数值存在矛盾；server的02圣经典故语义含混；ark启动日来自集团公开资料；daughter女儿确诊日有明示；forum六月三十日有明示但三先驱生日交集说法不严谨；shepherd要求raven不区分大小写，来源代号语义需复核；camera十一符号到七数字1041401缺明确映射，不能因源码命中声称推理成立。8个点只是审计候选，不授予正式内容准备结论。

下游17HTML全部通过正常应用/搜索弹窗可达，含入口共18页；14检索关键词、10微信联系人、17邮件、渡鸦加载更多、两个摄像头和涂鸦、8密码正负、三结局、错误报告及重置纳入回放。记事本保存、最小化缺陷及正常刷新恢复桌面、通讯录空搜索、模拟PDF提示为非推理支持功能。Windows Edge+Python环境仅同机独立目录复验；没有模型API调用。

已知原作运行缺陷：第三结局updateWrongSuspectContent替换wrongSuspectContent.innerHTML移除ending3Exploration，随后restartGame调用updateProgress在该空节点.textContent赋值报错。两独立包均有相同堆栈；工程路径仍全部完成，runtime_clean=false，须使用fresh context重置。未为了报告干净而吞掉异常。记事本保存按钮首先打开“另存为”对话框，本次仅验收该操作和编辑内容保留，未声称磁盘下载或完整文本编辑器验收。
''',encoding='utf-8')
put(J/'flow.json',{'entry':'index police badge -> desk; only private source-assisted credential established','applications':['wechat 10 chats','evidence 14 exact-keyword documents','notepad localStorage support'],'all_html_pages':sorted(p.name for p in (P/'mirror').glob('*.html')),'password_branches':['camera','old_case','mail','shepherd','server','ark','daughter','forum'],'routes':['ending1 truth','ending2 insufficient evidence','ending3 wrong suspect'],'failure_modes':['empty/short/wrong badge','unknown search','incorrect document passwords','blank or prohibited suspect','no evidence selected'],'reset':'fresh browser context full; report retry partial; document reload clears unlocked DOM'})
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',T],check=True)
dest=R/'packs'/f'{T}.prepared.zip'
with zipfile.ZipFile(dest) as z:contents={n:z.read(n) for n in z.namelist()}
for p in [J/'resource-check.json',J/'flow.json',J/'review.md',J/'compatibility.diff']:contents[p.relative_to(R).as_posix()]=p.read_bytes()
manifest=json.loads(contents['BUNDLE-MANIFEST.json']);manifest['files']=[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(contents.items()) if n not in ['BUNDLE-MANIFEST.json']];contents['BUNDLE-MANIFEST.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in contents.items():z.writestr(n,b)
manifest['archive']=dest.relative_to(R).as_posix();manifest['archive_sha256']=sha(dest);put(R/'packs'/f'{T}.prepared.manifest.json',manifest)
res=R/'packs'/f'{T}.resources.zip'
with zipfile.ZipFile(res,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((P/'mirror').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(P/'mirror').as_posix())
 z.writestr('RESOURCE-START.txt','Game-only resources. Serve this directory with python -m http.server 8833 --bind 127.0.0.1 and open /index.html. Fresh browser context resets all state. Initial badge clue absent; no standalone solve claim. No private evaluator included.\n')
D.mkdir(parents=True,exist_ok=True)
for kind,path in [('resources',res),('evaluation',dest)]:
 target=D/kind;target.mkdir(exist_ok=True)
 with zipfile.ZipFile(path) as z:z.extractall(target)
put(J/'deployment.json',{'archives':[{'kind':kind,'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for kind,p in [('resources',res),('evaluation',dest)]],'independent_roots':{'resources':str(D/'resources'),'evaluation':str(D/'evaluation')},'base_environment':{'python':sys.version,'playwright':importlib.metadata.version('playwright'),'browser':'installed Microsoft Edge'},'cross_os':False})
print('built and independently extracted both packages')
