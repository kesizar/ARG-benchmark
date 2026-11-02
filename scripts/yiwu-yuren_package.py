from pathlib import Path
import json,zipfile,hashlib,sys,subprocess,uuid
R=Path(__file__).resolve().parents[1];T='yiwu-yuren';B=R/'tasks'/T;J=R/'judge'/T
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in (B/'mirror').rglob('*') if p.is_file()]
with zipfile.ZipFile(R/'packs'/f'{T}.resources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(B/'mirror').as_posix())
rm={'task_id':T,'scope':'case001','files':[{'path':p.relative_to(B/'mirror').as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'archive_sha256':sha(R/'packs'/f'{T}.resources.zip')}
(R/'packs'/f'{T}.resources.manifest.json').write_text(json.dumps(rm,ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',T],cwd=R,check=True)
# Add evaluator evidence and original-source provenance, while keeping it outside served mirror.
f=R/'packs'/f'{T}.prepared.zip';tmp=f.with_suffix('.building.zip');pm=json.loads((R/'packs'/f'{T}.prepared.manifest.json').read_text(encoding='utf-8'));existing={x['path'] for x in pm['files']};extras=[p for p in J.rglob('*') if p.is_file() and p.relative_to(R).as_posix() not in existing and '__pycache__' not in p.parts]
for p in extras:pm['files'].append({'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
pm.pop('archive_sha256',None)
with zipfile.ZipFile(f) as src,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as dst:
 for name in src.namelist():
  if name!='BUNDLE-MANIFEST.json':dst.writestr(name,src.read(name))
 for p in extras:dst.write(p,p.relative_to(R).as_posix())
 dst.writestr('BUNDLE-MANIFEST.json',json.dumps(pm,ensure_ascii=False,indent=2))
tmp.replace(f);pm['archive_sha256']=sha(f);(R/'packs'/f'{T}.prepared.manifest.json').write_text(json.dumps(pm,ensure_ascii=False,indent=2),encoding='utf-8')
base=R/'runs'/('yiwu-yuren-delivery-'+uuid.uuid4().hex[:8]);base.mkdir();res=base/'resources';pre=base/'prepared';res.mkdir();pre.mkdir()
for kind,dest,manifest in [('resources',res,rm),('prepared',pre,pm)]:
 arc=R/'packs'/f'{T}.{kind}.zip'
 with zipfile.ZipFile(arc) as z:
  assert z.testzip() is None
  for name in z.namelist():assert (dest/name).resolve().is_relative_to(dest.resolve())
  z.extractall(dest)
 for ent in manifest['files']:assert sha(dest/ent['path'])==ent['sha256']
state={'root':str(base),'resources':str(res),'prepared':str(pre),'resources_sha256':rm['archive_sha256'],'prepared_sha256':pm['archive_sha256'],'crc_and_all_hashes_verified':True}
(B/'evidence/delivery-locations.json').write_text(json.dumps(state,indent=2),encoding='utf-8');print(json.dumps(state))
