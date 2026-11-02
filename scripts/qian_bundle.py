"""Package seven evaluator units sharing one isolated static resource directory."""
import hashlib,importlib.metadata,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='qian-anon'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(files):return [{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]
def main():
 out=ROOT/'packs';out.mkdir(exist_ok=True);resources=list((ROOT/f'tasks/{TASK}/mirror').glob('*'));versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
 path=out/f'{TASK}.resources.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for p in resources:z.write(p,p.relative_to(ROOT/f'tasks/{TASK}/mirror').as_posix())
 rm={'record_id':'base664:0521','files':manifest(resources),'archive_sha256':sha(path),'shared_by':list(json.loads((ROOT/f'tasks/{TASK}/collection.json').read_text(encoding='utf-8'))['units'])};(out/f'{TASK}.resources.manifest.json').write_text(json.dumps(rm,ensure_ascii=False,indent=2),encoding='utf-8')
 files=list((ROOT/'configs').glob(f'{TASK}*.json'))+[p for p in (ROOT/'harness').glob('*.py') if not p.name.startswith('test_')]+[ROOT/'scripts/run_one.py',ROOT/'scripts/serve_static.py']
 files+=[p for p in (ROOT/f'tasks/{TASK}').rglob('*') if p.is_file()]
 files+=[p for p in (ROOT/f'judge/{TASK}').rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('-server.log') and not p.name.endswith('-failure.png') and p.name not in ['PAUSED.json','deployment-latest-attempt.json','judge.json','probe_original.py','server.log','failure.png','merge-acceptance.json']]
 versions_text='\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n'
 m={'record_id':'base664:0521','task_id':TASK,'units':7,'runtime_layer':'L1','files':manifest(files),'prerequisites':{'python':'3.11+','python_packages':versions,'browser':'Playwright Chromium or installed Edge/Chrome'},'scope':'Collection manifest defines seven independently evaluated first-round episodes. Main config aliases GAL only. Engineering readiness does not approve content accuracy.'}
 path=out/f'{TASK}.prepared.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(set(files)):z.write(p,p.relative_to(ROOT).as_posix())
  z.writestr('requirements.txt',versions_text);z.writestr('BUNDLE-MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2));z.writestr('START-HERE.txt','Install Python3.11+ and pip install -r requirements.txt\nInstall a browser: python -m playwright install chromium\nRead tasks/qian-anon/README.md and collection.json\nChoose one of seven configs/qian-anon-<game>.json. Main config aliases GAL only.\nRun: python scripts/run_one.py --config configs/qian-anon-quiz.json --policy llm\nAPI credentials belong in the environment; none are included.\nOffline UI audit: python judge/qian-anon/verify_sample.py --unit quiz --port 8833\nNever serve bundle root: private answers and judges are outside tasks/qian-anon/mirror.\n')
 m.update(archive=path.relative_to(ROOT).as_posix(),archive_sha256=sha(path),crc_ok=zipfile.ZipFile(path).testzip() is None);(out/f'{TASK}.prepared.manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');print(m['archive_sha256'])
if __name__=='__main__':main()
