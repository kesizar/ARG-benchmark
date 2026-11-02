from pathlib import Path
import json,zipfile,hashlib,importlib.metadata,uuid
R=Path(__file__).resolve().parents[1];T='room-404';M=R/f'tasks/{T}/mirror';J=R/f'judge/{T}';public=[f for f in M.rglob('*') if f.is_file()]
private=[J/'judge.json',J/'verify_sample.py',J/'checkpoint-spec.json',J/'review.md']+[f for f in (J/'source').rglob('*') if f.is_file() and f.suffix not in ['.png']]+[f for f in (J/'verification').glob('*') if f.name=='acceptance.json' or f.name.startswith('ending-')]
extra=[R/f'configs/{T}.json',R/f'tasks/{T}/README.md',R/f'tasks/{T}/provenance.json']+[R/f'scripts/{n}.py' for n in ['run_one','serve_static','room-404_prepare','room-404_probe','room-404_capture','room-404_browser_probe','room-404_document','room-404_bundle']]+[f for f in (R/'harness').glob('*.py') if not f.name.startswith('test_')]
versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']};files=sorted(set(public+private+extra));manifest={'record_id':'base664:0002','task_id':T,'runtime_layer':'L1','config':f'configs/{T}.json','source_version':'official public current index-DyrrZ4RJ.js 2026-10-26','readiness':'Core engineering replay is separate from formal content approval; read review.md and deployment evidence.','prerequisites':{'python':'3.11+','python_packages':versions,'browser':'installed Edge or Playwright Chromium'},'files':[{'path':f.relative_to(R).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]};archives=[]
for kind,items in [('resources',public),('prepared',files)]:
 out=R/f'packs/{T}.{kind}.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for f in items:z.write(f,f.relative_to(R).as_posix())
  if kind=='prepared':
   z.writestr('BUNDLE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2));z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n');z.writestr('START-HERE.txt','Serve only tasks/room-404/mirror. Never serve the evaluation bundle root.\npython scripts/run_one.py --config configs/room-404.json --policy script\npython judge/room-404/verify_sample.py --port 8813\nFull reset: fresh browser context. Frozen current official SPA, not archived 2026-10-23 version.\nNo account, secret key, model API or OS/browser binaries are included.\n')
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
 archives.append({'path':out.relative_to(R).as_posix(),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
manifest['archives']=archives;(R/f'packs/{T}.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print('archives',[(a['path'],a['bytes']) for a in archives])
