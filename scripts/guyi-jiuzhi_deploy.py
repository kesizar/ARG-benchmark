from pathlib import Path
import zipfile,json,hashlib,subprocess,sys,http.server,threading,functools,urllib.request
R=Path(__file__).resolve().parents[1];T='guyi-jiuzhi';D=R/'runs'/f'{T}-deployment';D.mkdir(parents=True,exist_ok=True)
report={'candidate_only':True,'deployments':{},'archives':{}}
for kind in ['resources','prepared']:
 p=R/'packs'/f'{T}.{kind}.zip';target=D/kind;target.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  for n in z.namelist():assert (target/n).resolve().is_relative_to(target.resolve())
  z.extractall(target)
 report['archives'][kind]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
 report['deployments'][kind]=str(target.relative_to(R))
site=D/'resources';server=http.server.ThreadingHTTPServer(('127.0.0.1',8833),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(site)))
threading.Thread(target=server.serve_forever,daemon=True).start()
report['resource_http']={'url':'http://127.0.0.1:8833/index.html','sha256':hashlib.sha256(urllib.request.urlopen('http://127.0.0.1:8833/index.html').read()).hexdigest()}
server.shutdown()
e=D/'prepared';manifest=json.loads((e/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((e/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in manifest['files']);report['manifest_hashes_pass']=True
cp=e/'configs'/f'{T}.json';cfg=json.loads(cp.read_text(encoding='utf-8'));cfg['entry_url']=cfg['entry_url'].replace(':8831',':8832');cfg['allow_hosts']=['127.0.0.1:8832'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['port']=8832;cfg['local_serve']['command'][-1]='8832';cp.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
with (D/'cli-smoke.log').open('w',encoding='utf-8') as out:
 res=subprocess.run([sys.executable,'scripts/run_one.py','--config',f'configs/{T}.json','--policy','script'],cwd=e,stdout=out,stderr=subprocess.STDOUT,timeout=180)
report['cli_smoke_exit_code']=res.returncode
report['scope']='Game files identical; independent resource server8833 and extracted evaluator CLI on8832. Existing Windows Python/Edge prerequisites reused. One-step give_up is startup/observe/judge/log/cleanup only; complete UI trace is separate.'
(R/'judge'/T/'deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
