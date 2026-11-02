"""Package K7 resources and its private, reproducible evaluator separately."""
from pathlib import Path
import hashlib,importlib.metadata,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
task='k7-dangan';pub=ROOT/'tasks'/task/'mirror'
resources=ROOT/'packs/k7-dangan.resources.zip'
public_files=[x for x in pub.rglob('*') if x.is_file() and x.name not in {'.DS_Store','Thumbs.db','desktop.ini'} and not x.name.startswith('._')]
with zipfile.ZipFile(resources,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for x in sorted(public_files):z.write(x,x.relative_to(ROOT).as_posix())
private=[ROOT/f'judge/k7-dangan/{n}' for n in ['judge.json','source-inventory.json','flow.json','checkpoint-spec.json','verify_sample.py','verify_bbs.py','review.md','source/original.html','compatibility.diff'] if (ROOT/f'judge/k7-dangan/{n}').is_file()]
runtime=[x for x in (ROOT/'harness').glob('*.py') if not x.name.startswith('test_')]
files=public_files+private+runtime+[ROOT/'configs/k7-dangan.json',ROOT/'scripts/k7_run.py',ROOT/'scripts/run_one.py',ROOT/'scripts/serve_static.py',ROOT/'tasks/k7-dangan/README.md',ROOT/'tasks/k7-dangan/provenance.json']
versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
manifest={'record_id':'added84:0024','task_id':task,'runtime_layer':'L1','config':'configs/k7-dangan.json','prerequisites':{'python':'3.11+','packages':versions,'browser':'Playwright Chromium or installed Edge/Chrome'},'readiness':'Bundle existence does not certify flow/content; see acceptance and results.','files':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in sorted(set(files))]}
bundle=ROOT/'packs/k7-dangan.prepared.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for x in sorted(set(files)):z.write(x,x.relative_to(ROOT).as_posix())
    z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n')
    z.writestr('BUNDLE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    z.writestr('START-HERE.txt','Install requirements.txt and a Playwright browser if needed.\nRun python scripts/run_one.py --config configs/k7-dangan.json --policy script\nPrivate acceptance: python judge/k7-dangan/verify_sample.py --port 8812\nOnly serve tasks/k7-dangan/mirror, never the bundle root. API secrets are not bundled.\n')
for archive in [resources,bundle]:
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
manifest['archives']=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [resources,bundle]]
(ROOT/'packs/k7-dangan.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('k7-dangan bundles',[(x['path'],x['bytes']) for x in manifest['archives']])
