from pathlib import Path
import json,zipfile,hashlib,importlib.metadata
R=Path(__file__).resolve().parents[1];T='xuexiao-zaotang'
def build(kind,files):
 dest=R/'packs'/f'{T}.{kind}.zip';rows=[]
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(set(files)):
   rel=p.relative_to(R).as_posix();z.write(p,rel);rows.append({'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  z.writestr('BLOCKED-NOT-READY.txt','Incomplete archived entry. Required profile.html and start.html absent. Entry UI pass is not whole-game readiness. See tasks/xuexiao-zaotang/README.md in recovery bundle.\n')
  if kind=='recovery':z.writestr('requirements.txt','\n'.join(n+'=='+importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv'])+'\n')
  z.writestr('BUNDLE-MANIFEST.json',json.dumps({'task_id':T,'record_id':'added84:0075','status':'blocked_incomplete_resources','kind':kind,'files':rows},indent=2))
 manifest={'path':dest.relative_to(R).as_posix(),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':rows,'ready':False};(dest.with_suffix('.manifest.json')).write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 extract=R/'runs'/T/('unpacked-'+kind);extract.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None;z.extractall(extract)
 for row in rows:assert hashlib.sha256((extract/row['path']).read_bytes()).hexdigest()==row['sha256']
 return manifest
res=build('resources',[R/f'tasks/{T}/mirror/index.html'])
files=[p for p in (R/f'tasks/{T}').rglob('*') if p.is_file()]+[p for p in (R/f'judge/{T}').rglob('*') if p.is_file()]+[R/f'configs/{T}.json',R/f'configs/samples/{T}-blocked.json',R/'scripts/run_one.py',R/'scripts/serve_static.py']+[p for p in (R/'harness').glob('*.py') if not p.name.startswith('test_')]+[R/f'scripts/{T}_{s}.py' for s in ['prepare','probe','verify','bundle']]
rec=build('recovery',files)
print(json.dumps({'resources':res['bytes'],'recovery':rec['bytes'],'hash_crc':'pass'}))
