from pathlib import Path
import json,hashlib,zipfile,subprocess,sys,shutil,importlib.metadata
R=Path(__file__).resolve().parents[1];ID='wuxing-xuming';J=R/'judge'/ID;T=R/'tasks'/ID;P=R/'packs';D=R/'runs'/ID/'delivery';D.mkdir(parents=True,exist_ok=True)
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',ID],check=True,cwd=R)
zp=P/(ID+'.prepared.zip');extra=[R/'scripts'/f'{ID}_accept.py',J/'compatibility.diff',J/'snapshot-live.diff']
manifest_path=R/'packs'/f'{ID}.prepared.manifest.json';m=json.loads(manifest_path.read_text(encoding='utf8'));m.pop('archive',None);m.pop('archive_sha256',None)
for p in extra:m['files'].append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
tmp=zp.with_suffix('.tmp.zip')
with zipfile.ZipFile(zp) as src,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as dst:
 for n in src.namelist():
  if n!='BUNDLE-MANIFEST.json':dst.writestr(n,src.read(n))
 for p in extra:dst.write(p,p.relative_to(R).as_posix())
 dst.writestr('BUNDLE-MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2))
tmp.replace(zp);m['archive']=zp.relative_to(R).as_posix();m['archive_sha256']=hashlib.sha256(zp.read_bytes()).hexdigest();manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
g=P/(ID+'.game.zip')
with zipfile.ZipFile(g,'w',zipfile.ZIP_DEFLATED) as z:
 for p in (T/'mirror').rglob('*'):
  if p.is_file():z.write(p,p.relative_to(R).as_posix())
 z.writestr('START-HERE.txt','Serve only tasks/wuxing-xuming/mirror using Python 3.11+: python -m http.server 8832 --bind 127.0.0.1 --directory tasks/wuxing-xuming/mirror\nOpen http://127.0.0.1:8832/\nFour-act main case. Archive catalogue links are separately titled games and not included. No account required. Stop with Ctrl+C. New browser context resets gameplay.\n')
for p,target in [(g,D/'game-v3'),(zp,D/'evaluator-v3')]:
 if target.exists():raise RuntimeError('Do not overwrite independent deployment '+str(target))
 with zipfile.ZipFile(p) as z:z.extractall(target)
 print(p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
(J/'delivery-manifest.json').write_text(json.dumps({'archives':[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [g,zp]],'unpacked_game':str(D/'game-v3'),'unpacked_evaluator':str(D/'evaluator-v3'),'runtime':{'python':sys.version,'packages':{x:importlib.metadata.version(x) for x in ['playwright','jsonschema','httpx','python-dotenv']},'browser':'installed msedge; exact version recorded by deployment test'}},ensure_ascii=False,indent=2),encoding='utf8')
