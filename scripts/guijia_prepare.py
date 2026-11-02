"""Prepare an unmodified, self-contained snapshot; keep audit data private."""
from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parents[1];T='guijia-zhinan';J=R/'judge'/T;P=R/'tasks'/T
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
src=Path('D:/HuaweiMoveData/Users/17669/Desktop/ARG-packs/verify-416/bodies/426.html')
for p in [J/'source',P/'mirror']:p.mkdir(parents=True,exist_ok=True)
for old in [R/f'configs/{T}.json',J/'judge.json']:
 dst=J/'source'/('legacy-config.json' if old.parent.name=='configs' else 'legacy-judge.json')
 if old.exists() and not dst.exists():shutil.copyfile(old,dst)
shutil.copyfile(src,P/'mirror/index.html');html=src.read_text(encoding='utf-8')
base=json.loads((R/'configs/baoya.json').read_text(encoding='utf-8'))
base.update(id=T,model_visible={'title':'归家指南','intro':'这是本地单页叙事解谜。通过页面上可见的线索和操作推进故事，达成任一正式结局。'},judge_path=f'judge/{T}/judge.json')
base['local_serve']['command'][3]=f'tasks/{T}/mirror'
base['limits'].update(max_steps=250,max_seconds=1800,max_answer_submits=20)
base['notes_for_report']=['原作单页快照，虚构Tor下载/暗网访问仅为游戏内按钮，没有真实下载或外网依赖。','所有正式结局不擅自评好坏；提示直接暴露的输入只作事件。隐藏结局使用全结局收集配置。']
write(R/f'configs/{T}.json',base)
def hook(expr):return {'type':'js_truthy','expr':expr}
hooks={
 'morse':hook("!!document.querySelector('.ei') && document.querySelector('#el').textContent.includes('录音笔摩斯电码')"),
 'decode':hook("document.querySelector('#el').textContent.includes('网站源代码隐藏信息')"),
 'memo':hook("document.querySelector('#el').textContent.includes('弟弟备忘录')"),
 'address':hook("document.querySelector('#el').textContent.includes('暗网地址')"),
 'tor':hook("document.querySelector('#el').textContent.includes('已安装 Tor Browser')"),
 'guide':hook("!!document.querySelector('.he') && document.querySelector('.he').textContent.includes('隐藏结局 · 引路人')")}
for key,title in [('peace','结局 A · 安宁'),('curious','结局 B · 好奇'),('duty','结局 C · 职责'),('watch','结局 D · 旁观者')]:hooks[key]=hook(f"document.querySelector('#st h1')?.textContent === {json.dumps(title,ensure_ascii=False)}")
judge={'hooks':hooks,'checkpoints':[{'id':'decode','hook':'decode','op':'truthy','role':'critical'},{'id':'morse','hook':'morse','op':'truthy','role':'optional'}],'events':{k:{'hook':k,'op':'truthy'} for k in ['memo','address','tor']},'routes':[{'id':k,'gates':['decode'],'ending':{'hook':k,'op':'truthy'}} for k in ['peace','curious','duty','watch']]}
write(J/'judge.json',judge)
collection=json.loads(json.dumps(judge));collection['events'].update({k:{'hook':k,'op':'truthy'} for k in ['peace','curious','duty','watch']});collection['routes']=[{'id':'guide','gates':['decode'],'ending':{'hook':'guide','op':'truthy'}}]
write(J/'collection-judge.json',collection)
variant=json.loads(json.dumps(base));variant.update(id=T+'-collection',judge_path=f'judge/{T}/collection-judge.json',model_visible={'title':'归家指南：全结局收集','intro':'通过游戏内的重新开始，在同一页面会话收集四个正式结局，找出隐藏结局。不要刷新页面，刷新会清除结局收集进度。'});variant['limits'].update(max_steps=800,max_seconds=5400,max_answer_submits=60)
write(P/'collection.json',variant)
nodes=[]
for line in html.splitlines():
 m=re.match(r"nodeData\['([^']+)'\]=\{ch:(\d+),t:'([^']+)'",line)
 if m:nodes.append({'id':m[1],'chapter':int(m[2]),'title':m[3],'next_nodes':re.findall(r"\bn:'([^']+)'",line),'puzzle':('p:{' in line),'puzzle_success_next':re.findall(r"os:'([^']+)'",line),'conditional_actions':re.findall(r'c:function\(\)\{return ([^}]+)',line)})
write(J/'flow.json',{'record_id':'base664:0426','nodes':nodes,'endings':[{'id':k,'type':'formal_completion','rank':None,'node':v} for k,v in [('peace','ea'),('curious','eb'),('duty','ec'),('watch','ed')]]+[{'id':'guide','type':'hidden_completion','rank':None,'condition':'same JS page lifetime: visit ea, eb, ec, ed; final ending render injects .he'}],'failures':'Wrong puzzle inputs show feedback and allow retry; no terminal death or failure node.','exits':'Credits/back-to-menu are UI navigation, not endings. Ending D closes a fictional screen only, not the actual browser.','state':'rg clears node/evidence/flags but preserves S.end; refresh/context reset clears all.','optional':['1-3 Morse puzzle may be bypassed by choosing laptop at 1-2','cola/charger/window clues','1-8 private chat','1-10 historical avatar','chapter2/3/4 keyword searches']})
write(J/'checkpoint-spec.json',{'critical':[{'id':'decode','mechanism':'Base64 to Chinese; requires decoded input to advance','evidence':'source line329 check + persistent evidence DOM','wrong_not_scored':True}],'optional':[{'id':'morse','mechanism':'decode Morse; laptop bypass means not mandatory','evidence':'source line326 check + persistent evidence DOM'}],'unscored':[{'id':'memo','reason':'hint visibly supplies complete password; copy event only'},{'id':'address','reason':'Base64 task hint visibly supplies complete answer; copy event only'},{'id':'tor','reason':'fictional install button, ordinary click'},{'id':'search','reason':'suggested keywords/search result collection does not gate progression'}],'latching':'Judge.update after every UI action; #el evidence survives scenes until in-game restart. Mandatory decode counted once per run, including collection variant.'})
sha=hashlib.sha256(src.read_bytes()).hexdigest()
write(P/'provenance.json',{'record_id':'base664:0426','task_id':T,'source_url':'https://wmrlp8.gicp.fun/','source_snapshot':str(src),'source_sha256':sha,'resource_sha256':sha,'bytes':src.stat().st_size,'modifications':[],'dependencies':'No external script/style/image/font/audio requests in snapshot. Audio generated using WebAudio; graphics inline SVG. Fictional .onion and domain references are text/simulated buttons.','live_origin_parity':'not checked; frozen snapshot version is task version','account_requirement':'none'})
(P/'README.md').write_text('''# 归家指南（冻结快照）

原始记录 base664:0426，资源为一份未经修改的自包含 HTML。Python 3.11+、requirements.txt 所列固定版本依赖以及 Playwright Chromium（或已安装 Edge/Chrome）需要另行安装。无账号或付费 API 依赖，音效由本地 WebAudio 合成。

任一正式结局：`python scripts/run_one.py --config configs/guijia-zhinan.json --policy script`。该内置脚本只做接入冒烟，不代表通关。评测模型时使用 `--policy llm` 并在环境变量中配置模型接口；密钥不随包提供。

全结局收集：`python scripts/run_one.py --config tasks/guijia-zhinan/collection.json --policy llm`。这套配置只在隐藏结局出现时结束；需同一页面依次收集四结局，通过原作“重新开始”继续，不得刷新。主配置在首个正式结局后结束。

手动运行：`python scripts/serve_static.py --root tasks/guijia-zhinan/mirror --port 8811`，访问 http://127.0.0.1:8811/index.html 。Ctrl+C 停止。每次全新浏览器 context 或刷新页面完全重置；原作“重新开始”保留已收集结局。仅托管 mirror，严禁托管整个包（其中含私有裁判）。

工程验收：`python judge/guijia-zhinan/verify_sample.py --port 8812`。该私有回放通过正常界面动作验证各分支，不是模型能力跑分。说明和裁判置于托管目录外。源码含原作输入判定（网页游戏固有），模型仅获得允许的页面观察，不提供源码工具。
''',encoding='utf-8')
(J/'review.md').write_text('''# 私有审核记录

冻结快照为本题版本，未修改剧情、谜题或样式。所有外域文字均为叙事模拟，不是实际网络操作。Tor安装按钮只置本地标记。

四个标题明确的正式结局A安宁、B好奇、C职责、D旁观者，以及收集四结局后自动显示的隐藏结局引路人均是通关，未赋好坏等级；D只是叙事关闭屏幕，不是退出。错误答案不是失败结局，只有可重试反馈。作者名单/返回菜单是非结局界面。源码共49个叙事节点（以flow.json实际数量为准），完整依赖与状态条件需结合实机验收。

评分只把真正需要解码的中文Base64列为必经点，摩斯码是可绕过的可选点。日期与暗网地址的提示已直接给出完整输入，不计推理分。搜索只收集补充叙事，不门控剧情；不把普通翻页、看源码模拟按钮和收集线索夸成谜题。

内容限制：中文Base64提示声称四个汉字，实际五字；未修原题。日期和暗网解码直接泄底，整篇后续多为线性叙事。隐藏结局需要四遍重复，推理收益有限。窄输入框与终端搜索遵循原布局。正式题目难度和提示泄底需要内容复核，因此工程完成不等于正式评分就绪。没有验证实时原站当前版本、跨OS或纯文字档；未调用付费模型API。
''',encoding='utf-8')
print('Prepared unchanged snapshot; nodes',len(nodes),'sha',sha)
