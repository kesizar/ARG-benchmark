from pathlib import Path
import hashlib,json,zipfile,subprocess,sys,os,copy
R=Path(__file__).resolve().parents[1];base=R/'runs/dianti-1-failure-migration';dest=base/'evaluation';bundle=R/'packs/dianti-1.prepared.zip';old=R/'packs/dianti-1.pre-failure-migration.prepared.zip'
with zipfile.ZipFile(bundle) as z:
 for i in z.infolist():assert (dest/i.filename).resolve().is_relative_to(dest.resolve())
 z.extractall(dest)
m=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf8'))
for f in m['files']: assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
with zipfile.ZipFile(bundle) as a,zipfile.ZipFile(old) as b:
 for n in b.namelist():
  if not n.startswith('harness/') and n not in ['BUNDLE-MANIFEST.json', 'judge/dianti-1/judge.json', 'judge/dianti-1/checkpoint-spec.json', 'tasks/dianti-1/README.md', 'scripts/dianti-1_accept.py']:assert a.read(n)==b.read(n),n
cfg=json.loads((dest/'configs/dianti-1.json').read_text(encoding='utf8'));cfg['entry_url']='http://127.0.0.1:8831/';cfg['allow_hosts']=['127.0.0.1:8831'];cfg['local_serve'].update(command=['python','scripts/serve_static.py','--root','tasks/dianti-1/mirror','--port','8831'],port=8831,ready_url=cfg['entry_url']);cfg['settle_ms']=1100
start=[{'op':'click','x':978,'y':296},{'op':'click','x':557,'y':786},{'op':'click','x':683,'y':456}]
def typepw(s):return {'op':'type','text':s,'clear':True,'enter':True}
results={};env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
for name,actions in [('failure',[typepw('WRONG')]*3),('negative',[typepw('WRONG')]*2+[{'op':'give_up'}]),('success',[typepw('KEYS'),{'op':'wait','ms':1800}]),('reset',[{'op':'give_up'}])]:
 c=copy.deepcopy(cfg);c['id']='dianti-1-'+name;c['policy_script']=start+actions if name!='reset' else actions;c['limits']['max_steps']=len(c['policy_script'])+2
 p=dest/'configs'/('dianti-1-'+name+'.json');p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
 r=subprocess.run([sys.executable,'scripts/run_one.py','--config',str(p.relative_to(dest)),'--policy','script'],cwd=dest,env=env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=120);(base/(name+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf8');assert r.returncode==0,(name,r.stderr)
 paths=list((dest/'runs'/c['id']).rglob('summary.json'));assert len(paths)==1,(name,paths);s=json.loads(paths[0].read_text(encoding='utf8'));results[name]={k:s.get(k) for k in ['ended_reason','failure_reached','failure_id','ending_reached','ending_tier','route_id','steps']}
 print(name,results[name],flush=True)
 if name=='failure':assert s['ended_reason']=='failure' and s['failure_reached'] and s['failure_id']=='fall' and not s['ending_reached']
 elif name=='success':assert s['ending_reached'] and not s['failure_reached'] and s['route_id']=='escape'
 else:assert not s['ending_reached'] and not s['failure_reached']
(base/'verification.json').write_text(json.dumps({'status':'pass','manifest_verified':True,'unchanged_non_harness_files':True,'results':results},ensure_ascii=False,indent=2),encoding='utf8')
