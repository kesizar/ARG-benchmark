import json,hashlib,difflib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];task='yucai-gaozhong';base=ROOT/'tasks'/task;mirror=base/'mirror';judge=ROOT/'judge'/task
orig=judge/'original';orig.mkdir(parents=True,exist_ok=True)
for f in ['game.js','game.css','index.html']:
 if not (orig/f).exists():shutil.copy2(mirror/f,orig/f)
old=(orig/'game.js').read_text(encoding='utf-8')
new=old.replace("if (state.threads.lin) { renderMailInBag(); return; }","if (getThread('lin')) { renderMailInBag(); return; }")
new=new.replace("var t = getThread('lin');\n  if (flag('linReplied')", "var t = getThread('lin');\n  if (Array.isArray(state.linMails)) t.mails = state.linMails;\n  if (flag('linReplied')",1)
new=new.replace("t.mails.push({ me: 0, t: txt });\n  renderMailInBag();", "t.mails.push({ me: 0, t: txt });\n  state.linMails = t.mails; saveState();\n  renderMailInBag();",1)
(mirror/'game.js').write_text(new,encoding='utf-8')
(judge/'compatibility.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original/game.js',tofile='mirror/game.js')),encoding='utf-8')
cfg=json.loads((ROOT/'configs'/f'{task}.json').read_text(encoding='utf-8'));cfg.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8831/',allow_hosts=['127.0.0.1:8831'],local_serve={'enabled':True,'command':['python','scripts/serve_static.py','--root',f'tasks/{task}/mirror','--port','8831'],'cwd':'.','ready_url':'http://127.0.0.1:8831/','ready_timeout_s':20,'port':8831})
cfg['limits']={'max_steps':350,'max_seconds':3600,'max_answer_submits':30};cfg['notes_for_report']=['Public Edge responses recovered 2026-10-27. One mail-thread reload compatibility repair; original and diff evaluator-only. Authored unresolved/blank endings unreachable through original UI.']
(ROOT/'configs'/f'{task}.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
hooks={};checks=[]
for ident,expr in {'school-number':"(s.clues||{}).E",'netdisk-code':"(s.clues||{}).C",'guard-teacher':"(s.flags||{}).zhaoTrust",'report-five':"(s.flags||{}).reportOk"}.items():
 hooks[ident]={'type':'js_truthy','expr':"(()=>{let s=JSON.parse(localStorage.getItem('yc_state_v1')||'{}');return !!("+expr+")})()"};checks.append({'id':ident,'hook':ident,'op':'truthy','role':'critical'})
routes=[]
for ident,gates,tier in [('minute13',['report-five'],'normal'),('restore',['netdisk-code','guard-teacher','report-five'],'normal'),('witness13',['school-number','netdisk-code','guard-teacher','report-five'],'normal')]:
 hooks[ident]={'type':'js_truthy','expr':"(()=>{let s=JSON.parse(localStorage.getItem('yc_state_v1')||'{}');let e=document.querySelector('#ycEndT');return s.ended&&s.ending==='"+ident+"'&&e&&e.style.display==='block'})()"};routes.append({'id':ident,'tier':tier,'authored_classification':'hidden' if ident=='witness13' else 'regular','authored_label':'隐藏结局 · 二' if ident=='witness13' else ('常规结局 · 二' if ident=='minute13' else '常规结局 · 三'),'gates':gates,'ending':{'hook':ident,'op':'truthy'}})
spec={'hooks':hooks,'checkpoints':checks,'events':{},'routes':routes,'ending':None,'answer_sha256':[],'answer_hash_file':None,'request_milestones':[],'submit_conclusion':{'enabled':False,'schema':None},'rubric_path':None}
(judge/'judge.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
files=[{'path':f.relative_to(mirror).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in mirror.rglob('*') if f.is_file()]
(base/'provenance.json').write_text(json.dumps({'record_id':'base664:0408','task_id':task,'entry':'https://senior-high-school.pages.dev/','recovery':'Normal installed Edge browser response bodies; raw urllib 403, fresh Edge 200. No auth/UA/proxy changes.','snapshot':'ARG-packs/verify-416/bodies/408.html','account_requirement':'none','compatibility':'judge/yucai-gaozhong/compatibility.diff','files':files},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(files))
