from pathlib import Path
import re,json,hashlib,shutil
R=Path(__file__).resolve().parents[1];T='k7-dangan';J=R/'judge'/T;P=R/'tasks'/T
(J/'source').mkdir(parents=True,exist_ok=True);(P/'mirror').mkdir(parents=True,exist_ok=True)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for f,n in [(R/f'configs/{T}.json','legacy-config.json'),(J/'judge.json','legacy-judge.json')]:
 if f.exists() and not (J/'source'/n).exists():shutil.copyfile(f,J/'source'/n)
src=R/'ARG-packs/verify-84/bodies/24.html';sha=hashlib.sha256(src.read_bytes()).hexdigest();assert sha=='806e73b8a49400ad7bb2746639b4e15fe52179f2c28164d22e168a9c31083da7';text=src.read_text(encoding='utf-8');payload=src.read_bytes();nl=b'\r\n' if b'\r\n' in payload else b'\n';patched=payload.replace(b'"use strict";',b'"use strict";'+nl+b'const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));',1);patched=patched.replace(b'if (!G.ghostTyping && !$cmd.disabled) $cmd.focus();',b"if (!G.ghostTyping && !$cmd.disabled && !document.getElementById('website').classList.contains('active')) $cmd.focus();",1);(P/'mirror/index.html').write_bytes(patched)
endings=[{'id':m[0],'name':m[1],'type':m[2]} for m in re.findall(r'"([EH]\d+)":\s*\{\s*id:\x27[^\x27]+\x27,\s*name:\x27([^\x27]+)\x27,\s*type:\x27([^\x27]+)\x27',text)]
reachable=set(re.findall(r"showEnding\('([EH]\d+)'\)",text));assert len(endings)==20 and len(reachable)==18
c=json.loads((R/'configs/baoya.json').read_text(encoding='utf-8'));c.update(id=T,category='arg',judge_path=f'judge/{T}/judge.json',model_visible={'title':'K7 数位典藏：第47次记录','intro':'通过本地模拟终端和站内网页探索档案，达成一个作品结局。只使用网页中可见的命令和界面，不访问外网。'})
c['local_serve']['command'][3]=f'tasks/{T}/mirror';c['limits'].update(max_steps=400,max_seconds=3600,max_answer_submits=50);c['settle_ms']=350;c['policy_script']=[{'op':'give_up'}];c['notes_for_report']=['自包含模拟终端/官网/电话，全部L1，无真实外网与账号。','原作20结局定义中E01/H03没有任何触发调用，不作为可达路线。','零严格推理点：钥匙多处直接明文，其他结局命令无证据门。'];write(R/f'configs/{T}.json',c)
h={}
for e in endings:
 if e['id'] in reachable:h[e['id']]={'type':'js_truthy','expr':f"!!G.endings['{e['id']}'] && G.gameOver && document.querySelector('#out')?.textContent.includes('{e['name']}')"}
h['vault']={'type':'js_truthy','expr':"G.unlocked && localStorage.getItem('k7_unlocked') === '1'"}
write(J/'judge.json',{'hooks':h,'checkpoints':[],'events':{'vault':{'hook':'vault','op':'truthy'}},'routes':[{'id':e['id'],'gates':[],'ending':{'hook':e['id'],'op':'truthy'}} for e in endings if e['id'] in reachable]})
files={m[0]:m[1] for m in re.findall(r'FILES\["([^"]+)"\]\s*=\s*`(.*?)`;',text,re.S)}
vault={m[0]:m[1] for m in re.findall(r'"(/VAULT/[^"\n]+)":\s*`(.*?)`',text[text.index('const VAULT_FILES'):text.index('const WEB_PAGES')],re.S)}
write(J/'source-inventory.json',{'files':list(files),'virtual_file_count':len(files),'vault_files':list(vault),'vault_file_count':len(vault),'endings':[{**e,'reachable':e['id'] in reachable,'rank':None,'classification':'formal_completion' if e['id'] in reachable else 'defined_but_unwired'} for e in endings],'web_pages':['index','about','staff','archive','news','bbs','contact']})
commands={'E02':'report','E03':'publish','E05':'count','E06':'respond','E07':'destroy','E08':'investigate','E11':'decode','E12':'observe','E13':'excavate','E14':'collect','E15':'goodbye'}
write(J/'flow.json',{'record_id':'added84:0024','endings':[{**e,'trigger':commands.get(e['id'],{'E04':'cat any actual unlocked VAULT file','E09':'date in browser hour23..04','E10':'listen twice','H01':'47th nonempty command','H02':'enter raw key as command','H04':'read6 hidden files then next command','H05':'100th command after unlock','E01':'no trigger in source','H03':'no trigger in source'}.get(e['id'])),'reachable':e['id'] in reachable,'rank':None} for e in endings],'commands_with_no_prerequisite':commands,'key':'Base64/hex clues exist but .MARSHALL and SEQ_A/SEQ_B/RAW.DAT explicitly print decoded pieces; .MARSHALL gives complete assembled key. Therefore vault event only, no inference credit.','hidden_six':['/STAFF/.MARSHALL','/STAFF/.VOSS','/STAFF/.FERRARI','/STAFF/.HAN.NOTE','/STAFF/.VOSS.DRAFT','/SYS/.OKONKWO.BAK'],'web':'7 local HTML views; BBS yes/no/other are alert side events, not extra ENDINGS entries.','failure':'unknown commands, wrong key, missing file are recoverable, no terminal failure ending','exit':'exit/logout/quit simulate disconnect then reconnect, no E01 trigger','continue':'Original gameOver is display state only; commands are not blocked. Normal replay explicitly uses continue to avoid racing endings.','reset':'restart clears origin localStorage and reloads. Reload alone restores vault and old ending object before boot removes storage key; new context clears all.','atmosphere':'Idle47/94/141s, repeated file reads3/7, minute5/15/30/47 and04:12 events do not affect formal ending set; source mapped, not all waited in real time.'})
write(J/'checkpoint-spec.json',{'critical_reasoning_points':[],'optional_reasoning_points':[],'events':['vault'],'why':'No defensible required inference gate: command ending jumps unconditional, actual key copied from original documents. Hidden file exploration and command counting are mechanics, not automatically reasoning.','endings':'18 routes only; require source ending state plus terminal completed render, no hidden source-text scan. Original2 unimplemented definitions documented, not repaired.'})
write(P/'provenance.json',{'record_id':'added84:0024','source_url':'https://l9o9f6.kicp.fun/','snapshot':'ARG-packs/verify-84/bodies/24.html','source_sha256':sha,'modifications':[{'type':'compatibility_missing_helper','detail':'Define sleep(ms) as Promise(setTimeout); original referenced it throughout but never declared it. Preserve all timing values, narrative, command logic and ending conditions.','original':'judge/k7-dangan/source/original.html'},{'type':'compatibility_focus','detail':'Only focus terminal on document click when simulated website panel is closed; otherwise original stole BBS input focus. No puzzle/ending logic changed.'}],'account_requirement':'none','dependencies':'inline HTML/CSS/JS, data URI noise, synthesized WebAudio; simulated web URLs are plain labels','live_origin_parity':'not checked'})
(P/'README.md').write_text('''# K7 数位典藏：第47次记录（冻结快照，补缺失延时helper）

Python3.11+、requirements.txt依赖和Playwright Chromium或Edge/Chrome需另行安装。原作引用sleep却未定义，已补标准Promise延时函数，另修网站打开时全局click抢走BBS输入焦点。原计时值、文本、判题与结局条件不改。只需本地资源，无真实账号、电话或远端服务。

标准启动：`python scripts/run_one.py --config configs/k7-dangan.json --policy script`（一动作接入冒烟，非通关）；模型用`--policy llm`，API凭据由环境提供。

手动：`python scripts/serve_static.py --root tasks/k7-dangan/mirror --port 8811`，访问http://127.0.0.1:8811/index.html；Ctrl+C停止。只托管mirror，严禁托管含私有裁判的包根目录。restart清存档并刷新；完整干净开始使用新context。原作刷新会恢复解锁状态，故不等于完整重置。

时间环境：E09只在浏览器本地23:00–04:59输入date出现。`python scripts/k7_run.py --window night --policy script`自动选择合法IANA时区让启动时处于02点，日间对照用`--window day`。仅设浏览器timezone，不改OS时钟或注入游戏状态。长期运行跨过窗口仍按原作时间机制判定。

私有验收：`python judge/k7-dangan/verify_sample.py --port 8812`，真实输入命令并点击站内链接，收集18个可达结局，核验日/夜条件与正负例。E01/H03虽然有文本但未接触发器，无法正常达成；不补造剧情。模拟BBS alert不是真实发送消息。

作品大量命令无前置、完整密钥明文，零可信推理点；工程包可跑不代表适合推理跑分。主配置首个结局即结束，私有全流程验收在同会话continue继续收集。
''',encoding='utf-8')
(J/'review.md').write_text('''# 私有审核

20个结局定义只有18个显式showEnding调用。E01/H03未接线，甚至exit也只断开再连，没有触发沉默档案员。不会为凑20路线而注入进度或补写原作。其余normal/hidden均作品正式结局，未赋高低；销毁等仅按叙事性质记录，不擅自认定为评分失败。

严格推理点0：多个结局只需help中一个单词；三段编码的解码结果、甚至完整组合密钥都在原文显示。故解锁只记事件。H01/H05为命令计数，H04为隐藏文件收集，不自动计推理分。RAW.DAT宣称偏移/二进制信息只是文本模拟，部分备份对第二段指示与RAW第三段描述冲突，保留差异待内容复核。

时间依赖E09保留机制，通过浏览器timezone环境配置正负验证，不改用户系统时间。04:12及长期恐怖事件只作氛围，源码核对但不为演出等待47分钟。随机噪声、计数器和会话ID不改变路线。

原始HTML私有存档，运行HTML补缺失sleep(ms)延时helper，并限制全局终端focus只在网站面板关闭时触发、官网/电话/BBS均模拟，无真实外站发送。未比对实时原站、跨OS或模型解题能力。无付费模型API。
''',encoding='utf-8')
print('prepared',len(files),'base files',len(vault),'vault files; reachable',len(reachable))
