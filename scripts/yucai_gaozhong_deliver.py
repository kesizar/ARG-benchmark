import json,hashlib,zipfile,importlib.metadata,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];task='yucai-gaozhong';packs=ROOT/'packs';packs.mkdir(exist_ok=True)
manifest={};versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
for kind in ['resources','prepared']:
 path=packs/f'{task}.{kind}.zip'
 if kind=='resources':files=[(f,f.relative_to(ROOT/'tasks'/task/'mirror').as_posix()) for f in (ROOT/'tasks'/task/'mirror').rglob('*') if f.is_file()]
 else:
  fs=[ROOT/'configs'/f'{task}.json',ROOT/'judge'/task/'judge.json',ROOT/'judge'/task/'checkpoint-spec.json',ROOT/'judge'/task/'CONTENT_AUDIT.md',ROOT/'judge'/task/'compatibility.diff',ROOT/'tasks'/task/'README.md',ROOT/'tasks'/task/'provenance.json',ROOT/'scripts/run_one.py',ROOT/'scripts/serve_static.py',ROOT/'scripts/yucai_gaozhong_verify.py']
  fs += list((ROOT/'judge'/task/'original').glob('*'))
  fs += [f for f in (ROOT/'harness').glob('*.py') if not f.name.startswith('test_')]
  fs += [f for f in (ROOT/'tasks'/task/'mirror').rglob('*') if f.is_file()]
  files=[(f,f.relative_to(ROOT).as_posix()) for f in fs]
 m={'task_id':task,'kind':kind,'prerequisites':{'python':'3.11+','packages':versions,'browser':'Installed Microsoft Edge; Windows only verified'},'files':[{'path':rel,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f,rel in files]}
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for f,rel in files:z.write(f,rel)
  z.writestr('BUNDLE-MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2))
  if kind=='prepared':
   z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n')
   z.writestr('START-HERE.txt','Install Python 3.11+ and requirements.txt; install Microsoft Edge.\nRun python scripts/run_one.py --config configs/yucai-gaozhong.json --policy script (give-up smoke only).\nFull normal UI acceptance: python scripts/yucai_gaozhong_verify.py . 8832 acceptance\nServe only tasks/yucai-gaozhong/mirror; never evaluator bundle root.\n')
 dep=ROOT/'runs'/task/'tier-review-deployments'/kind;dep.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None;z.extractall(dep)
  for item in m['files']:assert hashlib.sha256((dep/item['path']).read_bytes()).hexdigest()==item['sha256']
 m.update(archive=path.relative_to(ROOT).as_posix(),archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),deployment=str(dep))
 (packs/f'{task}.{kind}.manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');manifest[kind]=m
(ROOT/'judge'/task/'tier-review-deployment.json').write_text(json.dumps({k:{'archive':v['archive'],'deployment':v['deployment'],'files':len(v['files']),'hashes_passed':True} for k,v in manifest.items()},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:len(v['files']) for k,v in manifest.items()}))
