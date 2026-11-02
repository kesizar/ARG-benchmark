"""Create a self-contained evaluator bundle, separate from game-only assets.

Python packages and a Playwright browser are prerequisites, recorded explicitly.
Never include .env or old run directories. Do not serve this bundle's root.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--task', required=True)
    a=p.parse_args()
    if not a.task.replace('-','').isalnum(): raise ValueError('Invalid task ID')
    cfg=ROOT/'configs'/f'{a.task}.json'
    data=json.loads(cfg.read_text(encoding='utf-8'))
    if data.get('runtime_layer')!='L1': raise ValueError('Only local task bundles supported by this builder')
    command=(data.get('local_serve') or {}).get('command') or []
    if '--root' not in command: raise ValueError('This builder currently supports local static browser tasks, not interpreter or custom-server tasks')
    files=[cfg,ROOT/data['judge_path'],ROOT/'scripts/run_one.py',ROOT/'scripts/serve_static.py']
    files += [x for x in (ROOT/'harness').glob('*.py') if not x.name.startswith('test_')]
    files += [x for x in (ROOT/'tasks'/a.task/'mirror').rglob('*') if x.is_file()
              and x.name not in {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
              and '__MACOSX' not in x.parts and not x.name.startswith('._')]
    for rel in [f'tasks/{a.task}/README.md',f'tasks/{a.task}/provenance.json',f'judge/{a.task}/verify_sample.py',f'judge/{a.task}/checkpoint-spec.json']:
        if (ROOT/rel).is_file():files.append(ROOT/rel)
    versions={n:importlib.metadata.version(n) for n in ['playwright','jsonschema','httpx','python-dotenv']}
    manifest={'task_id':a.task,'runtime_layer':'L1','config':f'configs/{a.task}.json','readiness':'Package creation is not approval of game content or flow; use independent acceptance results.','prerequisites':{'python':'3.11+','python_packages':versions,'browser':'Playwright Chromium or installed Edge/Chrome'},'files':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in sorted(set(files))]}
    path=ROOT/'packs'/f'{a.task}.prepared.zip'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for x in sorted(set(files)):z.write(x,x.relative_to(ROOT).as_posix())
        z.writestr('requirements.txt','\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n')
        z.writestr('BUNDLE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        z.writestr('START-HERE.txt',f'Install Python dependencies: python -m pip install -r requirements.txt\nInstall browser if needed: python -m playwright install chromium\nRun: python scripts/run_one.py --config configs/{a.task}.json --policy script\nFor model evaluation use --policy llm and configure API credentials in the environment. No secrets are included.\nNever serve this directory as a web root: it includes evaluator-only judge data. The task config serves only tasks/{a.task}/mirror/.\n')
    manifest['archive']=path.relative_to(ROOT).as_posix();manifest['archive_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT/'packs'/f'{a.task}.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)


if __name__=='__main__': main()
