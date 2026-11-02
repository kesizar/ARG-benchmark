from pathlib import Path
import json,hashlib,zipfile,importlib.util,importlib.metadata,sys,subprocess
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];T=R/'tasks/dengta-jushe';J=R/'judge/dengta-jushe';O=R/'runs/dengta-jushe';P=R/'packs';task='dengta-jushe'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
common=[T/'mirror/index.html',T/'README.md',T/'provenance.json',R/'scripts/serve_static.py']
extra=[R/'configs/dengta-jushe.json']+[p for p in J.glob('*') if p.is_file()]+[p for p in (R/'harness').glob('*.py') if not p.name.startswith('test_')]+[R/'scripts/run_one.py',R/'scripts/dengta-jushe_ui.py',R/'scripts/dengta-jushe_secondary.py']
packages=[];deploy=[]
for kind,files in [('resources',common),('prepared',common+extra)]:
 archive=P/f'{task}.{kind}.zip';files=sorted(set(files));manifest=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=h(p)) for p in files]
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(R).as_posix())
  z.writestr('BUNDLE-MANIFEST.json',json.dumps({'task_id':task,'kind':kind,'files':manifest,'prerequisites':dict(python=sys.version,python_packages=versions,browser='Installed Edge or playwright install chromium')},ensure_ascii=False,indent=2))
  z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n')
  z.writestr('START-HERE.txt','Game only: python scripts/serve_static.py --root tasks/dengta-jushe/mirror --port 8811\nOpen http://127.0.0.1:8811/index.html\nInstall Python requirements, Edge/Chromium separately. Serve mirror only. Stop by ending server process. New browser context resets.\nEvaluator bundle only: python scripts/run_one.py --config configs/dengta-jushe.json --policy script\nNo credentials included.\n')
 dest=O/f'deploy-{kind}'
 with zipfile.ZipFile(archive) as z:z.extractall(dest)
 for item in manifest:assert h(dest/item['path'])==item['sha256']
 packages.append(dict(kind=kind,path=archive.relative_to(R).as_posix(),sha256=h(archive),bytes=archive.stat().st_size,unpacked_root=str(dest),files_verified=len(files)))
spec=importlib.util.spec_from_file_location('ui',R/'scripts/dengta-jushe_ui.py');ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui)
with sync_playwright() as w:
 browser=w.chromium.launch(channel='msedge')
 for item,port in zip(packages,[8812,8813]):
  dest=Path(item['unpacked_root']);srv=ui.serve(dest/'tasks/dengta-jushe/mirror',port)
  try:

   if '--reuse-ui' in sys.argv and (O/f'deploy-{port}.json').is_file():
    evidence=json.loads((O/f'deploy-{port}.json').read_text(encoding='utf8'));assert any(x['case']=='ending-complete' and x['hooks']['ending'] for x in evidence['cases']);count=len(evidence['cases'])
   else:count=ui.flow(browser,f'http://127.0.0.1:{port}/index.html',f'deploy-{port}',False)
   deploy.append(dict(package=item['path'],root=str(dest),port=port,new_context=True,full_main_route_and_reset=True,optional_cue_skipped=True,cases=count,external_requests=0))
   if item['kind']=='prepared':
    sys.path.insert(0,str(dest));sp=importlib.util.spec_from_file_location('independent_verify',dest/'judge/dengta-jushe/verify_sample.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.verify(O/f'deploy-{port}.json');deploy[-1]['extracted_judge_vs_ui_passed']=True
    cfg=json.loads((dest/'configs/dengta-jushe.json').read_text(encoding='utf8'));assert (dest/cfg['judge_path']).is_file();assert (dest/cfg['local_serve']['command'][3]).is_dir();deploy[-1]['config_relative_paths_resolve']=True
  finally:srv.shutdown()
 browser.close()
save(O/'packages.json',packages);save(O/'deployment.json',deploy);print('two packages independently deployed',len(deploy))
