"""Package Guijia resources and its private, reproducible evaluator separately."""
from pathlib import Path
import hashlib,importlib.metadata,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
task='guijia-zhinan';pub=ROOT/'tasks'/task/'mirror'
resources=ROOT/'packs/guijia-zhinan.resources.zip'
public_files=[x for x in pub.rglob('*') if x.is_file() and x.name not in {'.DS_Store','Thumbs.db','desktop.ini'} and not x.name.startswith('._')]
with zipfile.ZipFile(resources,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for x in sorted(public_files):z.write(x,x.relative_to(ROOT).as_posix())
private=[ROOT/f'judge/guijia-zhinan/{n}' for n in ['judge.json','collection-judge.json','flow.json','checkpoint-spec.json','verify_sample.py','review.md'] if (ROOT/f'judge/guijia-zhinan/{n}').is_file()]
runtime=[x for x in (ROOT/'harness').glob('*.py') if not x.name.startswith('test_')]
files=public_files+private+runtime+[ROOT/'configs/guijia-zhinan.json',ROOT/'scripts/run_one.py',ROOT/'scripts/serve_static.py',ROOT/'tasks/guijia-zhinan/README.md',ROOT/'tasks/guijia-zhinan/provenance.json',ROOT/'tasks/guijia-zhinan/collection.json']
versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
manifest={'record_id':'base664:0426','task_id':task,'runtime_layer':'L1','config':'configs/guijia-zhinan.json','prerequisites':{'python':'3.11+','packages':versions,'browser':'Playwright Chromium or installed Edge/Chrome'},'readiness':'Bundle existence does not certify flow/content; see acceptance and results.','files':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in sorted(set(files))]}
bundle=ROOT/'packs/guijia-zhinan.prepared.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for x in sorted(set(files)):z.write(x,x.relative_to(ROOT).as_posix())
    z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n')
    z.writestr('BUNDLE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    z.writestr('START-HERE.txt','Install requirements.txt and a Playwright browser if needed.\nRun python scripts/run_one.py --config configs/guijia-zhinan.json --policy script\nPrivate acceptance: python judge/guijia-zhinan/verify_sample.py --port 8812\nOnly serve tasks/guijia-zhinan/mirror, never the bundle root. API secrets are not bundled.\n')
for archive in [resources,bundle]:
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
manifest['archives']=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [resources,bundle]]
(ROOT/'packs/guijia-zhinan.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('guijia-zhinan bundles',[(x['path'],x['bytes']) for x in manifest['archives']])
