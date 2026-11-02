from pathlib import Path
import hashlib,json,zipfile,subprocess,sys,os,copy
R=Path(__file__).resolve().parents[1];t='fangjian-404-yingzi';base=R/'runs/fangjian404-failure-migration';dest=base/'evaluation';dest.mkdir(parents=True,exist_ok=True);bundle=R/f'packs/{t}.prepared.zip';old=R/f'packs/{t}.pre-failure-migration.prepared.zip'
with zipfile.ZipFile(bundle) as z:
 for i in z.infolist():assert (dest/i.filename).resolve().is_relative_to(dest.resolve())
 z.extractall(dest)
m=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf8'))
for f in m['files']:assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
with zipfile.ZipFile(bundle) as a,zipfile.ZipFile(old) as b:
 for n in b.namelist():
  if not n.startswith('harness/') and n not in ['BUNDLE-MANIFEST.json',f'judge/{t}/judge.json']+['judge/fangjian-404-yingzi/checkpoint-spec.json', 'judge/fangjian-404-yingzi/verify_sample.py']:assert a.read(n)==b.read(n),n
cfg=json.loads((dest/f'configs/{t}.json').read_text(encoding='utf8'));cfg['entry_url']='http://127.0.0.1:8832/index.html';cfg['allow_hosts']=['127.0.0.1:8832'];cfg['local_serve'].update(command=['python','scripts/serve_static.py','--root',f'tasks/{t}/mirror','--port','8832'],port=8832,ready_url=cfg['entry_url']);cfg['settle_ms']=400
click=lambda x,y:{'op':'click','x':x,'y':y};typ=lambda s:{'op':'type','text':s,'clear':True};start=[click(892,497),click(683,487)];wrong=[click(125,61),typ('menghui19'),click(255,61),typ('wrong'),click(355,61)];success=start+[click(125,61),typ('menghua'),click(255,61),typ('031789'),click(355,61),{'op':'wait','ms':6000},{'op':'wait','ms':5000},click(505,651),click(822,696),click(923,152),click(683,510),{'op':'dialog','accept':True,'text':'往生自在'},{'op':'dialog','accept':True,'text':''},{'op':'wait','ms':9000},click(683,535)]
results={};env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
for name,actions in [('failure',start+wrong+[click(355,61)]*4+[{'op':'wait','ms':2500}]),('negative',start+wrong+[click(355,61)]*3+[{'op':'give_up'}]),('success',success),('reset',[{'op':'give_up'}])]:
 c=copy.deepcopy(cfg);c['id']=t+'-'+name;c['policy_script']=actions;c['limits']['max_steps']=len(actions)+2
 p=dest/'configs'/(t+'-'+name+'.json');p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
 r=subprocess.run([sys.executable,'scripts/run_one.py','--config',str(p.relative_to(dest)),'--policy','script'],cwd=dest,env=env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180);(base/(name+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf8');assert r.returncode==0,(name,r.stderr)
 paths=list((dest/'runs'/c['id']).rglob('summary.json'));assert paths;s=json.loads(sorted(paths)[-1].read_text(encoding='utf8'));results[name]={k:s.get(k) for k in ['ended_reason','failure_reached','failure_id','ending_reached','ending_tier','route_id','steps']};print(name,results[name],flush=True)
 if name=='failure':assert s['ended_reason']=='failure' and s['failure_reached'] and s['failure_id']=='loop_failure' and not s['ending_reached']
 elif name=='success':assert s['ending_reached'] and not s['failure_reached'] and s['route_id']=='bad'
 else:assert not s['ending_reached'] and not s['failure_reached']
(base/'verification.json').write_text(json.dumps({'status':'pass','manifest_verified':True,'unchanged_non_harness_files':True,'results':results},ensure_ascii=False,indent=2),encoding='utf8')
