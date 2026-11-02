from pathlib import Path
import hashlib,importlib.metadata,json,zipfile
R=Path(__file__).resolve().parents[1];T='qingshu-shizong';pub=R/'tasks'/T/'mirror'
files=[p for p in pub.rglob('*') if p.is_file()];private=[p for p in (R/'judge'/T).rglob('*') if p.is_file() and 'verification' not in p.parts and p.suffix not in {'.log','.png'} and p.name!='HANDOFF.json']
private += [p for p in (R/'judge'/T/'source').glob('asset-*') if p not in private]
private += [p for p in (R/'judge'/T/'verification').glob('*') if p.suffix in {'.json','.png'} and p.name!='delivery-integrity.json']
extra=[R/f'configs/{T}.json',R/f'tasks/{T}/README.md',R/f'tasks/{T}/provenance.json']+[R/f'scripts/{x}.py' for x in ['run_one','serve_static','qingshu_serve','qingshu_bundle']]+[p for p in (R/'harness').glob('*.py') if not p.name.startswith('test_')]
versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
manifest={'record_id':'base664:0528','task_id':T,'runtime_layer':'L1','config':f'configs/{T}.json','prerequisites':{'python':'3.11+','packages':versions,'browser':'Playwright Chromium or installed Edge/Chrome'},'files':[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(files+private+extra))]}
archives=[]
for name,items in [('resources',files),('prepared',files+private+extra)]:
 out=R/f'packs/{T}.{name}.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(set(items)):z.write(p,p.relative_to(R).as_posix())
  if name=='prepared':
   z.writestr('BUNDLE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2));z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n');z.writestr('START-HERE.txt','Serve only tasks/qingshu-shizong/mirror. Official historical forum version; read task README.\npython scripts/run_one.py --config configs/qingshu-shizong.json --policy script\npython judge/qingshu-shizong/verify_sample.py --port 8832\n')
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
 archives.append({'path':out.relative_to(R).as_posix(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size})
manifest['archives']=archives;(R/f'packs/{T}.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print([(x['path'],x['bytes']) for x in archives])
