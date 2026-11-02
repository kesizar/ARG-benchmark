from pathlib import Path
import zipfile,json,hashlib,io
R=Path(__file__).resolve().parents[1];D=R/'tasks/xishe-guaitan';P=R/'packs';run=R/'runs/xishe-guaitan'
with zipfile.ZipFile(P/'xishe-guaitan.game.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in (D/'mirror').rglob('*'):
  if p.is_file():z.write(p,p.relative_to(D/'mirror').as_posix())
extra=[D/'compatibility.diff',D/'vendor-provenance.json',D/'originals/village-committee.html',R/'scripts/xishe_accept.py']
archive=P/'xishe-guaitan.prepared.zip'
with zipfile.ZipFile(archive) as z:contents={n:z.read(n) for n in z.namelist()}
for p in extra:contents[p.relative_to(R).as_posix()]=p.read_bytes()
manifest=json.loads(contents['BUNDLE-MANIFEST.json'])
manifest['files']=[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(contents.items()) if n not in ['BUNDLE-MANIFEST.json','START-HERE.txt','requirements.txt']]
contents['BUNDLE-MANIFEST.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in sorted(contents.items()):z.writestr(n,b)
archive.write_bytes(buf.getvalue());manifest.update(archive='packs/xishe-guaitan.prepared.zip',archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest());(P/'xishe-guaitan.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(P/'xishe-guaitan.game.zip') as z:z.extractall(run/'isolated-game')
with zipfile.ZipFile(P/'xishe-guaitan.prepared.zip') as z:z.extractall(run/'isolated-prepared')
for p in [run/'game-accept',run/'prepared-accept']:p.mkdir(exist_ok=True)
rows=[]
for name in ['xishe-guaitan.game.zip','xishe-guaitan.prepared.zip']:
 p=P/name;rows.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(P/'xishe-guaitan.delivery.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
