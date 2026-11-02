from pathlib import Path
import hashlib,importlib.metadata,json,zipfile
R=Path(__file__).resolve().parents[1];T='liushi-fenzhong';P=R/'tasks'/T;J=R/'judge'/T
public=list((P/'mirror').glob('*'))
private=[x for x in J.glob('*') if x.is_file() and x.name!='deployment.json']+[P/'README.md',P/'provenance.json',P/'resource-audit.json',R/f'configs/{T}.json',R/'scripts/run_one.py',R/'scripts/serve_static.py']
runtime=[x for x in (R/'harness').glob('*.py') if not x.name.startswith('test_')]
versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
manifest={'record_id':'base664:0361','task_id':T,'runtime_layer':'L1','missing_soft_asset':'optional donation 收款码.jpg unavailable in frozen source collection','prerequisites':{'python':'3.11+','python_packages':versions,'browser':'Playwright Chromium or installed Edge/Chrome'},'readiness':'engineering acceptance and formal scoring suitability are separate; see result0361','files':[{'path':x.relative_to(R).as_posix(),'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(set(public+private+runtime))]}
for kind,files in [('resources',public),('prepared',public+private+runtime)]:
 out=R/'packs'/f'{T}.{kind}.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for x in sorted(set(files)):z.write(x,x.relative_to(R).as_posix())
  if kind=='prepared':
   z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n');z.writestr('BUNDLE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2));z.writestr('START-HERE.txt',f'Install requirements.txt and Playwright browser.\nRun python scripts/run_one.py --config configs/{T}.json --policy script\nPrivate acceptance python judge/{T}/verify_sample.py --port 8813\nServe only tasks/{T}/mirror. Never expose judge files or bundle root.\n')
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
manifest['archives']=[{'path':f'packs/{T}.{k}.zip','bytes':(R/'packs'/f'{T}.{k}.zip').stat().st_size,'sha256':hashlib.sha256((R/'packs'/f'{T}.{k}.zip').read_bytes()).hexdigest()} for k in ['resources','prepared']]
(R/'packs'/f'{T}.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Two bundles built')
