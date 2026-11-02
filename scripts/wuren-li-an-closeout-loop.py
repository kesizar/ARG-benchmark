from pathlib import Path
import json,subprocess,sys,os,copy
R=Path(__file__).resolve().parents[1];T='wuren-li-an';base=R/'runs/wuren-li-an-failure-migration';dest=R/'runs/wuren-closeout-independent';cfg=json.loads((dest/f'configs/{T}.json').read_text(encoding='utf8'));cfg['entry_url']='http://127.0.0.1:8856/index.html';cfg['allow_hosts']=['127.0.0.1:8856'];cfg['local_serve'].update(command=['python','scripts/serve_static.py','--root',f'tasks/{T}/mirror','--port','8856'],port=8856,ready_url=cfg['entry_url']);cfg['settle_ms']=450;env=os.environ.copy();env['PYTHONIOENCODING']='utf8';results={}
for name in ['failure_pd','negative','success','reset']:
 actions=json.loads((base/(('failure_pd' if name=='negative' else name)+'-actions.json')).read_text(encoding='utf8')) if name!='reset' else [{'op':'give_up'}]
 if name=='negative':actions=actions[:-1]+[{'op':'give_up'}]
 c=copy.deepcopy(cfg);c['id']=T+'-'+name;c['policy_script']=actions;c['limits']['max_steps']=len(actions)+2;p=dest/'configs'/(c['id']+'.json');p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
 r=subprocess.run([sys.executable,'scripts/run_one.py','--config',str(p.relative_to(dest)),'--policy','script'],cwd=dest,env=env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180);(dest/'judge/wuren-li-an/verification'/('closeout-'+name+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf8');assert r.returncode==0
 paths=list((dest/'runs'/c['id']).rglob('summary.json'));assert paths;s=json.loads(sorted(paths)[-1].read_text(encoding='utf8'));results[name]={k:s.get(k) for k in ['ended_reason','failure_reached','failure_id','ending_reached','ending_tier','route_id','steps']};print(name,results[name],flush=True)
 if name=='failure_pd':assert s['ended_reason']=='failure' and s['failure_id']==name and s['failure_reached'] and not s['ending_reached']
 elif name=='success':assert s['ending_reached'] and not s['failure_reached'] and s['route_id']=='C'
 else:assert not s['ending_reached'] and not s['failure_reached']
(dest/'judge/wuren-li-an/verification/closeout-loop.json').write_text(json.dumps({'status':'pass','manifest_verified':True,'unchanged_non_harness_files':True,'results':results},ensure_ascii=False,indent=2),encoding='utf8')
