from pathlib import Path
import zipfile,json,hashlib,subprocess,os,sys,shutil,traceback
root=Path('.').resolve();base=root/'runs/guiyihui-meimei-terminal-failure-final';base.mkdir(parents=True,exist_ok=True); log={'test_only_fixture':True,'test_only_timer_seconds':1,'errors':[]}
try:
 bundle=root/'packs/guiyihui-meimei.prepared.zip'; dest=base/'evaluation';dest.mkdir(exist_ok=True)
 with zipfile.ZipFile(bundle) as z:
  for info in z.infolist():assert (dest/info.filename).resolve().is_relative_to(dest.resolve())
  z.extractall(dest)
 manifest=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'));assert all(hashlib.sha256((dest/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest['files']);log['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest();log['manifest_verified']=True
 game=dest/'tasks/guiyihui-meimei/mirror'; fixture=dest/'tasks/guiyihui-meimei/fixture-short-timer';shutil.copytree(game,fixture,dirs_exist_ok=True)
 p=fixture/'index.html';s=p.read_text(encoding='utf-8');old='let bloodMoonTimeLeft = 9900;';new='let bloodMoonTimeLeft = 1;';assert s.count(old)==1;s=s.replace(old,new,1);p.write_text(s,encoding='utf-8');log['fixture_difference']={'file':'index.html','before':old,'after':new};assert (game/'index.html').read_bytes()!=p.read_bytes()
 cfg=dest/'configs/guiyihui-meimei.json';d=json.loads(cfg.read_text(encoding='utf-8'));d['entry_url']='http://127.0.0.1:8823/index.html';d['allow_hosts']=['127.0.0.1:8823'];d['local_serve'].update(command=['python','scripts/serve_static.py','--root','tasks/guiyihui-meimei/fixture-short-timer','--port','8823'],port=8823,ready_url=d['entry_url']);d['policy_script']=[{'op':'wait','ms':1000} for _ in range(10)];d['limits']={'max_steps':10,'max_seconds':60,'max_answer_submits':5};cfg.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 env=os.environ.copy();env['PYTHONIOENCODING']='utf-8';r=subprocess.run([sys.executable,'scripts/run_one.py','--config','configs/guiyihui-meimei.json','--policy','script'],cwd=dest,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120);(base/'run.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');log['exit_code']=r.returncode;assert r.returncode==0
 summaries=list((dest/'runs').rglob('summary.json'));assert len(summaries)==1;summary=json.loads(summaries[0].read_text(encoding='utf-8'));log['summary_path']=str(summaries[0].relative_to(root));log['summary']={k:summary.get(k) for k in ['ended_reason','failure_reached','failure_id','failure_step','ending_reached','ending_tier','steps']};assert summary.get('ended_reason')=='failure' and summary.get('failure_reached') is True and summary.get('failure_id')=='failure_timeout_A' and summary.get('failure_step') is not None and summary.get('ending_reached') is False
 log['status']='pass'
except Exception:log['errors'].append(traceback.format_exc());log['status']='fail'
(root/'judge/guiyihui-meimei/verification/terminal-failure.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(log,ensure_ascii=True,indent=2));sys.exit(0 if log['status']=='pass' else 1)
