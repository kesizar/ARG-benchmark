from pathlib import Path
import json,shutil,hashlib,re,urllib.parse
R=Path(__file__).resolve().parents[1];T='tade-xinhao';P=R/'tasks'/T;J=R/'judge'/T;M=P/'mirror'
def w(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
D=P/'source/developer';D.mkdir(exist_ok=True)
for name in ['CLAUDE.md','故事大纲.md','scripts','tools','.gitignore']:
 s=M/name
 if s.exists():shutil.move(str(s),str(D/name))
shutil.copyfile(R/'ARG-packs/verify-416/bodies/312.html',P/'source/snapshot-312.html')
shutil.copyfile(P/'source/snapshot-312.html',M/'index.html')
files=[f for f in M.rglob('*') if f.is_file()];missing=[];external=[];refs=[]
for f in files:
 if f.suffix not in ['.html','.css','.js']:continue
 txt=f.read_text(encoding='utf8')
 for v in re.findall(r'(?:src|href)\s*=\s*[\"\']([^\"\']+)',txt):
  if '${' in v or v.startswith(('data:','#','javascript:','blob:','mailto:')):continue
  u=urllib.parse.urlsplit(v)
  if u.scheme or u.netloc:external.append({'file':f.relative_to(M).as_posix(),'ref':v});continue
  dest=(f.parent/urllib.parse.unquote(u.path)).resolve()
  if not u.path:continue
  row={'file':f.relative_to(M).as_posix(),'ref':v,'exists':dest.is_file()};refs.append(row)
  if not row['exists']:missing.append(row)
w(P/'resource-audit.json',{'source_commit':'171cbd747cfe4d717c7bfe41f6e113d3f390d4e4','snapshot_current_text_equal':True,'snapshot_bytes':125841,'mirror_files':len(files),'mirror_bytes':sum(f.stat().st_size for f in files),'literal_src_href_audit_only':True,'missing':missing,'external_literal_references':external,'refs':refs,'files':[{'path':f.relative_to(M).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]})
c=json.loads((R/'configs/baoya.json').read_text(encoding='utf8'));c.update(id=T,judge_path=f'judge/{T}/judge.json',model_visible={'title':'她的信号','intro':'调查失踪的小初，依据页面线索确认地点并探索结局。当前为本地冻结版本，真实搜索引擎访问不可用。'},entry_url='http://127.0.0.1:8831/index.html',allow_hosts=['127.0.0.1:8831'],account_requirement='none')
c['local_serve'].update(command=['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8831'],port=8831,ready_url=c['entry_url']);c['limits'].update(max_steps=1500,max_seconds=14400,max_answer_submits=200);c['notes_for_report']=['PREPARATION INCOMPLETE: candidate engineering configuration; full routes and scoring not accepted.','Original requests real-world search and multi-modal decoding; closed-network suitability unresolved.'];w(R/f'configs/{T}.json',c)
# Independent read-only candidate judge, intentionally no unverified reasoning checkpoint assignments.
hooks={}
for i in range(22):hooks[f'place_{i:02}']={'type':'js_truthy','expr':f"(()=>{{try{{return JSON.parse(localStorage.getItem('citymystery_save')||'{{}}').knownPlaceNames?.includes({i})===true}}catch(e){{return false}}}})()"}
for i in range(1,6):hooks[f'E{i:02}']={'type':'js_truthy','expr':f"document.body.classList.contains('ending-e{i:02}') && document.querySelector('.ending-id')?.textContent.trim() === 'E-{i:02}'"}
w(J/'judge.json',{'hooks':hooks,'checkpoints':[],'events':{f'place_{i:02}':{'hook':f'place_{i:02}','op':'truthy'} for i in range(22)},'routes':[{'id':f'E{i:02}','gates':[],'ending':{'hook':f'E{i:02}','op':'truthy'}} for i in range(1,6)]})
w(J/'checkpoint-spec.json',{'status':'candidate_not_formal_scoring','critical_reasoning_points':[],'observed_candidate':'22 strict place-name checks; route-specific necessity not yet accepted. Record as events until bypass and complete paths audited.','latching':'Candidate Judge stores place events and ending; fresh Judge required per reset.','endings':{'E01':'献祭','E02':'凋零','E03':'融合','E04':'安宁','E05':'生路'},'unverified':['all five full normal-UI routes','alternate E03 profile confirm/refusal','ritual, corruption and archive failures','multimodal decoding/tool and real-search policy','route-specific reasoning gates and independent score calibration']})
w(P/'provenance.json',{'record_id':'base664:0312','source_url':'https://emith233.github.io/her-signal/','snapshot':'ARG-packs/verify-416/bodies/312.html','snapshot_sha256':hashlib.sha256((M/'index.html').read_bytes()).hexdigest(),'upstream_commit':'171cbd747cfe4d717c7bfe41f6e113d3f390d4e4','modifications':['index restored to byte-identical historical snapshot; current upstream differs only line endings','non-player developer docs, generator and decoder scripts excluded from game server and retained source/developer'],'account_requirement':'none (local fictional account interfaces only)','live_parity':'index normalized text equals pinned upstream; assets pinned from current repository; historical asset hashes unavailable'})
(P/'README.md').write_text('''# 她的信号 — 恢复与候选接入\n\n状态：资源恢复完成，正式验收未完成。不可作为ready/正式计分题。\n\n启动：python scripts/serve_static.py --root tasks/tade-xinhao/mirror --port 8831\n入口：http://127.0.0.1:8831/index.html；Ctrl+C停止。UI“重置”确认后重启；每局用新browser context和新Judge。仅托管mirror，评测包根含私有裁判不得托管。\n\n基础依赖：Python 3.11+、requirements.txt及Playwright Chromium或系统Edge/Chrome另装。无真实账号、服务端或模型API依赖。游戏原说明允许真实搜索引擎/AI辅助；当前封闭L1配置不提供这些，需评估可解性。音频/图像处理支线也需能力边界复核。\n\n候选裁判只记录22个地点事件和5个结局DOM；尚未分配正式推理点，因此零计分点不代表原作无推理。不得将直接访问结局页当成正常通关。\n''',encoding='utf8')
print(json.dumps({'files':len(files),'bytes':sum(f.stat().st_size for f in files),'missing_refs':missing,'external_refs':external},ensure_ascii=False))
