"""Preserve a blocked candidate; never promotes a source password to player evidence."""
from pathlib import Path
import json,hashlib,re,zipfile,html.parser,shutil
R=Path(__file__).resolve().parents[1];T='fengnian-gaiban';P=R/'tasks'/T;J=R/'judge'/T
J.mkdir(parents=True,exist_ok=True);(J/'verification').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
snap=R/'ARG-packs/verify-416/bodies/417.html';assert snap.stat().st_size==81792
assert sha(snap)=='734872ecd5e3b42b5c1736e0ef99b0d79f3a3f73c127d97d841c929ec04b70a0'
shutil.copyfile(snap,P/'entry.snapshot.html');shutil.copyfile(R/'runs/fengnian-tree.json',P/'upstream-tree.json')
U=P/'upstream';files=[{'path':p.relative_to(U).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(U.rglob('*')) if p.is_file()]
refs=[];missing=[]
for p in U.iterdir():
 if p.suffix not in ('.html','.js','.css'):continue
 text=p.read_text(encoding='utf-8'); targets=set(re.findall(r'''(?:src|href)\s*=\s*["']([^"']+)["']''',text))
 targets.update(re.findall(r'''(?:location(?:\.href)?\s*=\s*|(?:page|icon):\s*)["']([^"']+)["']''',text))
 targets.update(re.findall(r'''url\(\s*["']?([^"')\s]+)''',text))
 targets.update(re.findall(r'''["']([./A-Za-z0-9_-]+\.(?:html|css|js|png|jpg|svg|mp3)(?:\?[^"']*)?)["']''',text))
 for target in sorted(targets):
  if target.startswith(('data:','#','http:','https:')) or '<' in target or target.startswith('javascript:'):continue
  name=target.split('?')[0].split('#')[0]
  if not re.search(r'\.(html|js|css|png|jpg|svg|mp3)$',name):continue
  exists=(p.parent/name).is_file();item={'from':p.name,'to':target,'exists':exists};refs.append(item)
  if not exists:missing.append(item)
put(J/'resource-check.json',{'snapshot':{'bytes':snap.stat().st_size,'sha256':sha(snap)},'upstream_entry':{'bytes':(U/'index.html').stat().st_size,'sha256':sha(U/'index.html')},'version_parity':False,'version_note':'Archived entry differs from current complete public repository; they are separate candidate versions. No historical child-page parity claim.','public_tree_sha':json.loads((P/'upstream-tree.json').read_text())['sha'],'files':files,'references':refs,'missing_local_references':missing,'external_tool':'tieba.html displays https://www.lanren-tools.com/aes-encrypt/ as plaintext; tool not packaged or validated.','optional_external_links':['https://www.ifdian.net/a/argjy'],'camera':'wugan1 requests getUserMedia; source contains denial fallback; not exercised downstream.','account_requirement':'none in local source; external tool conditions unknown'})
assert not missing,missing
put(J/'checkpoint-spec.json',{'status':'not_ready_entry_clue_review_required','critical_reasoning_points':[],'optional_reasoning_points':[],'scoring_enabled':False,'reason':'The supplied pre-entry material does not establish the eight-digit birthday required to enter the desktop. Unlocking with the private source credential is diagnostic only, not evidence of a solved puzzle. Downstream gates/endings have not been played or approved.','pending':['Establish original author-supplied pre-entry clue or explicit benchmark-provided access credential.','Choose and freeze archived versus current version, without silently mixing them.','Determine local AES utility/tool access policy and demonstrate decryption from visible clues.','Full six-ending/branch/failure/reset UI coverage and independent private judge.','Complete evaluation package and independent full-flow deployment acceptance.']})
put(P/'provenance.json',{'record_id':'base664:0417','title':'奉念（改版）','task_id':T,'official_entry':'https://qwert987df.github.io/jhj/','config_candidates':[],'source_snapshot':'ARG-packs/verify-416/bodies/417.html','snapshot_sha256':sha(snap),'public_source':'https://github.com/qwert987df/jhj','retrieved_date':'2026-10-26','upstream_archive_sha256':sha(P/'upstream-main.zip'),'modifications':[],'status':'recovery_material_only_not_a_prepared_benchmark','api_calls':0})
(P/'README.md').write_text('''# 奉念（改版）：入口线索待核实，未验收

本目录是恢复材料，不是已准备题目。原始记录 base664:0417 无已有配置，分配 fengnian-gaiban。

entry.snapshot.html 是原81792字节入口，upstream/ 是2026-10-26下载的公开仓库完整资源。当前入口79663字节，与历史快照不等同；未混为同一版本。

入口只显示“用户”与开机密码框；三次错误后仅提示8位生日数字。没有随记录提供可见的生日线索。源码中的正确值只可用于私有诊断，不能作为玩家成功推理证据。未穷举日期，也未提供源码答案给模型。需要找到原作者入口前材料，或明确制定不计分的访问凭据之后再继续全流程。

离线查看当前候选：python scripts/serve_static.py --root tasks/fengnian-gaiban/upstream --port 8821；访问 http://127.0.0.1:8821/index.html，Ctrl+C停止。仅托管upstream，勿托管包含私有裁判的目录。新browser context清除游戏状态。

私有入口诊断：python judge/fengnian-gaiban/verify_entry.py --port 8822。依赖Python3.11、Playwright和Edge/Chromium，基础环境未打包。该诊断覆盖空/错/源码正确凭据与新context重置，完全不代表通关或评分。

恢复顺序见judge/fengnian-gaiban/checkpoint-spec.json。外部AES工具、摄像头降级、六个结局及全部支线尚未实机核验，不得用于正式评测。没有付费模型API调用。
''',encoding='utf-8')
print('preserved',len(files),'files;',len(refs),'local references; missing',len(missing))

# Final scope: source-assisted engineering replay is permitted; no model-solving claim.
check=json.loads((J/'resource-check.json').read_text(encoding='utf-8'))
assert snap.read_text(encoding='utf-8')==(U/'index.html').read_text(encoding='utf-8')
check.update(version_parity=True,version_note='Entry differs only by CRLF versus LF (2129 line endings); normalized UTF-8 text is exactly equal. Child pages frozen from the public repository; historical child snapshots unavailable.')
put(J/'resource-check.json',check)
M=P/'mirror';M.mkdir(exist_ok=True)
for p in U.iterdir():
 if p.is_file():shutil.copyfile(p,M/p.name)
shutil.copyfile(snap,M/'index.html')
cfg=json.loads((R/'configs/baoya.json').read_text(encoding='utf-8'))
cfg.update(id=T,entry_url='http://127.0.0.1:8821/index.html',judge_path=f'judge/{T}/judge.json',model_visible={'title':'奉念（改版）','intro':'只依据本地网页可见信息探索并到达任一结局。不得查看源码或私有评测文件。'},allow_hosts=['127.0.0.1:8821'])
cfg['local_serve'].update(command=['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8821'],ready_url=cfg['entry_url'],port=8821)
cfg['limits'].update(max_steps=700,max_seconds=3600,max_answer_submits=80)
cfg['notes_for_report']=['入口生日线索未随材料提供；当前只验收私有源码辅助工程回放，不能据此宣称模型能解。','全局fresh context重置；解锁后直接reload有原作TDZ异常。摄像头拒绝通路允许继续，不授权真实摄像。','AES与生辰八字换算辅助工具未提供给模型，正式推理评分待复核。']
put(R/f'configs/{T}.json',cfg)
def hook(e):return {'type':'js_truthy','expr':e}
def at(page,e='true'):return "location.pathname.endsWith('/"+page+".html') && ("+e+")"
ends=['self_end1','self_end2','real1','real2','egg','uuu']
hooks={'archive':hook(at('recycle',"document.querySelector('#doneWrap')?.classList.contains('show')")),
 'geometry':hook(at('zhiliao',"document.querySelector('#resultBox')?.style.display==='block'")),
 'identity':hook(at('em')),'base64_diary':hook(at('kill')),'birth':hook(at('real')),'black_decode':hook(at('black')),
 'unlocked':hook("location.pathname.endsWith('/index.html') && document.querySelector('#lockScreen')?.style.display==='none'"),
 'camera_denied':hook(at('wugan1',"document.body.innerText.includes('摄像头没有开启')"))}
for e in ends:hooks[e]=hook(at(e,"document.querySelector('.ec-card')?.classList.contains('show')"))
critical=[{'id':'archive','role':'critical','hook':'archive','op':'truthy'}]
optional=[{'id':k,'role':'optional','hook':k,'op':'truthy'} for k in ['geometry','identity','base64_diary','birth','black_decode']]
put(J/'judge.json',{'hooks':hooks,'checkpoints':critical+optional,'events':{k:{'hook':k,'op':'truthy'} for k in ['unlocked','camera_denied']+ends},'routes':[{'id':e,'gates':['archive'],'ending':{'hook':e,'op':'truthy'}} for e in ends]})
put(J/'checkpoint-spec.json',{'status':'engineering_replay_only_content_review_required','critical_reasoning_candidates':['archive: poem seasons->963 and physician highlighted 4/7/11->4711, concatenated password'],
 'optional_reasoning_candidates':{'geometry':'Image geometry question, accepted 30 / 30° / 30度; bypassable via search.','identity':'King doctor name/id across sources plus bm90aGluZw== -> nothing; bypassable.','black_decode':'Encrypted file black accepted; visible clue derivation still needs independent review.','base64_diary':'key1 a2 + key2 lsb + key3 A== -> a2lsbA== -> kill; bypassable.','birth':'1980-07-30 08h to sexagenary birth 庚申癸未甲辰戊辰 plus copied name and die; only other-sacrifice routes.'},
 'scoring_policy':'Candidate reasoning points only. No formal readiness until entry clue, AES support, calendrical conversion and clue sufficiency review. Search keywords, narrative clicks, questionnaire answers, poem reveal clicks alone, and moral choices are events or unscored. Private source-assisted replay is not a solve.','latching':'Judge reads actual DOM after actions, latches successful points and each completed cinematic card; bare/stale localStorage endings never score.','route_gates':'archive only for every ending; other gates are optional and must not be imposed on self or extra/true routes.','ending_classification':{'self_end1':'BAD END 01 自我献祭','self_end2':'BAD END 02 困于愧疚','real1':'REAL END 01 接受一切 (authored bad tone)','real2':'REAL END 02 改写一切 (authored bad tone)','egg':'EXTRA END 查明·打破','uuu':'TRUE END 有缘再见'},'original_runtime_bug':'index startup on unlocked reload calls budgetTick before let lastUnzip initializes; two-version entry diagnostics preserve this error.'})
put(J/'flow.json',{'core':['private diagnostic unlock','wechat clue collection','recycle archive password','hospital search god','eye cinematic','yanguang cinematic','inside search'],
 'routes':{'self':['献祭 / 祭讫','献祭自己','confirm -> self_end1 / cancel -> self_end2'],'other':['献祭 / 祭讫','献祭他人','identity/birth/key -> real','接受一切 -> real1 / 改写一切 -> real2'],'extra':['白鹿/山神/鹿神/白鹿山','丁子熙 (also present in local 马飞 chat)','egg','改写这个结局 twice -> uuu']},
 'supporting':['6 hospital navigation pages','hospital keyword map and aliases','wechat 4 contacts, doctor follow-up and moments','tieba 3 expandable posts','questionnaire 4 score bands plus incomplete error','telephone 2 audio numbers and invalid input','research accepted/wrong','linwan corrupted search inert','lens diaries, key reveal, empty/wrong searches','camera denial fallback without real camera','desktop window management and save reset'],
 'not_a_terminal_failure':'Incorrect inputs retry in place; four bad-tone narrative endings are authored outcomes, not generic error dialogs.'})
prov=json.loads((P/'provenance.json').read_text(encoding='utf-8'));prov.update(status='source_assisted_engineering_replay_candidate',entry_normalized_equal_to_current=True,mirror_entry='byte-identical original snapshot',modifications=[]);put(P/'provenance.json',prov)
(P/'README.md').write_text('''# 奉念（改版）

原始记录base664:0417，入口81792B原样冻结；公开仓库入口仅CRLF/LF差异，子页从完整公开仓库冻结。本地91个资源文件、647条静态本地引用均存在。无游戏账号，无模型API密钥。

运行：python scripts/serve_static.py --root tasks/fengnian-gaiban/mirror --port 8821；访问 http://127.0.0.1:8821/index.html；Ctrl+C停止。配置 configs/fengnian-gaiban.json 可由 scripts/run_one.py 调用。每局使用全新browser context；不要用解锁后reload代替重置，原作会触发lastUnzip初始化错误。开始菜单清档保留结局，不等于评测全重置。

私有全流程工程验收：python judge/fengnian-gaiban/verify_sample.py --port 8822。它使用源码核对凭据，经实际输入/点击回放；不是模型解谜结果。入口只有“8位生日数字”提示，没有随记录提供身份生日线索，正确凭据不会提供到模型提示。正式评分待复核。仅托管mirror，严禁托管包根目录中的私有裁判。

Python3.11+、requirements.txt依赖和Edge/Playwright Chromium需独立安装。摄像头仅使用拒绝权限后的原有降级路线，不采集真实影像。帖内AES外部工具和生辰八字换算未作为本地玩家工具部署，须在正式使用前解决工具访问/题面充分性。全部候选评分以judge/checkpoint-spec为准，不给普通检索、道德选择或翻页加推理分。
''',encoding='utf-8')
print('source-assisted engineering candidate configured')
