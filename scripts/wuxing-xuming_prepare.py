from pathlib import Path
import json,re,shutil,difflib,hashlib
R=Path(__file__).resolve().parents[1];J=R/'judge/wuxing-xuming';S=J/'source/recovered';T=R/'tasks/wuxing-xuming';M=T/'mirror';M.mkdir(parents=True,exist_ok=True)
a=json.loads((J/'recovery-audit.json').read_text(encoding='utf8'));core=['index.html','act2.html','act3.html','act4.html']; refs=set(core)
for name in core:
 text=(S/name).read_text(encoding='utf8')
 refs.update(re.findall(r'''["']([^"']+\.(?:png|mp4))["']''',text))
for name in refs:
 if name.startswith(('http:','https:','data:')):continue
 f=S/name
 if not f.is_file() or f.read_bytes().startswith(b'<!DOCTYPE html>') and not name.endswith('.html'):raise ValueError(name)
 shutil.copyfile(f,M/name)
patch=[]
for name in core:
 p=M/name;old=p.read_text(encoding='utf8');new=old
 new=re.sub(r'<script src="https://beacon\.cdn\.qq\.com/[^\"]+"></script>','<!-- Offline compatibility: analytics SDK omitted. -->',new)
 new=new.replace("location.href='https://3000-ca57f7f0f3764f878b7e6dd0a5346d55.e2b.ap-beijing.sandbox.cloudstudio.club/'","location.href='index.html'")
 p.write_text(new,encoding='utf8');patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original/'+name,tofile='mirror/'+name))
(J/'compatibility.diff').write_text(''.join(patch),encoding='utf8')
if not (J/'source/legacy-config.json').exists(): shutil.copyfile(R/'configs/wuxing-xuming.json',J/'source/legacy-config.json')
if not (J/'source/legacy-judge.json').exists(): shutil.copyfile(J/'judge.json',J/'source/legacy-judge.json')
c=json.loads((R/'configs/wuxing-xuming.json').read_text(encoding='utf8'));c.update(runtime_layer='L1',account_requirement='none',entry_url='http://127.0.0.1:8831/',allow_hosts=['127.0.0.1','localhost'],local_serve={'enabled':True,'command':['python','scripts/serve_static.py','--root','tasks/wuxing-xuming/mirror','--port','8831'],'cwd':'.','ready_url':'http://127.0.0.1:8831/'});c['limits']={'max_steps':600,'max_seconds':7200,'max_answer_submits':50};c['notes_for_report']=['2026-10-27 preparation: recovered current four-act main case. See task README, judge checkpoint-spec, source and acceptance evidence. Original cached index retained; do not reuse legacy five-point judgement.','Separate archive catalogue games are linked works, excluded from four-act main-case score and not yet locally complete. Main case has non-prerequisite navigation that can skip reasoning; see risk report.'];(R/'configs/wuxing-xuming.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
def h(expr,page='index.html'):
 return {'type':'js_truthy','expr':f"(['{page}'].includes(location.pathname.split('/').pop())"+(' || location.pathname.endsWith(\'/\')' if page=='index.html' else '')+") && ("+expr+")"}
checks={
'mark':h("document.getElementById('markProg')?.textContent.includes('5 / 5') && document.getElementById('penSvg')?.classList.contains('show')"),
'step':h("document.getElementById('quizStepAns')?.classList.contains('ok')"),
'cuff':h("document.getElementById('cuffReveal')?.classList.contains('show')"),
'flaw':h("document.getElementById('quizFlawAns')?.classList.contains('ok')",'act2.html'),
'drawer':h("document.getElementById('drawerContent')?.classList.contains('show') && document.getElementById('drawerPwd')?.disabled",'act2.html'),
'fingerprint':h("document.getElementById('fpVerdict')?.classList.contains('show')",'act3.html'),
'alias':h("document.getElementById('fleeVerdict')?.classList.contains('show')",'act4.html')}
for i in range(7):checks['timeline-'+str(i+1)]=h(f"document.getElementById('slot{i}')?.classList.contains('filled')",'act3.html')
for i in range(5):checks['network-'+str(i+1)]=h(f"document.querySelector('.js-slot[data-slot=\"{i}\"]')?.classList.contains('placed')",'act4.html')
checks['ending-A']=h("document.getElementById('finale')?.classList.contains('show') && document.getElementById('brA')?.classList.contains('sel')",'act2.html');checks['ending-B']=h("document.getElementById('finale')?.classList.contains('show') && document.getElementById('brB')?.classList.contains('sel')",'act2.html');checks['ending-final']=h("document.getElementById('finale')?.classList.contains('show')",'act4.html')
# Retrieval/archiving is diagnostic, independent from reasoning points.
checks['funds']=h("document.getElementById('fundVerdict')?.classList.contains('show')",'act3.html');checks['archive-evidence']=h("document.querySelectorAll('.ec.found').length===4");checks['pending-butt']=h("document.getElementById('buttEvi')?.classList.contains('picked')")
j={'hooks':checks,'checkpoints':[{'id':k,'hook':k,'op':'truthy','role':'diagnostic' if k in ['funds','archive-evidence','pending-butt'] else 'critical'} for k in checks if not k.startswith('ending-')],'events':{},'routes':[{'id':'main-final','tier':'good','gates':['network-'+str(i+1) for i in range(5)],'ending':{'hook':'ending-final','op':'truthy'}}],'ending':{'hook':'ending-final','op':'truthy'},'answer_sha256':[],'submit_conclusion':{'enabled':False,'schema':None}}
(J/'judge.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
(T/'provenance.json').write_text(json.dumps({'record_id':'base664:0214','version':'live 2026-10-27 recovered four-act main case','origin':'https://wuxing-altar.pages.dev/','source_snapshot':'ARG-packs/verify-416/bodies/214.html','files':[{'path':p.relative_to(M).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in M.rglob('*') if p.is_file()]},ensure_ascii=False,indent=2),encoding='utf8')
print('main files',len(refs),'checkpoints',len(j['checkpoints']))
