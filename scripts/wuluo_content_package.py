import json,zipfile,hashlib
from pathlib import Path
r=Path.cwd();p=r/'packs/wuluo-cun.prepared.zip';t=p.with_suffix('.tmp.zip');n='judge/wuluo-cun/verify_content_closeout.py';f=r/n
with zipfile.ZipFile(p) as a,zipfile.ZipFile(t,'w') as z:
 m=json.loads(a.read('BUNDLE-MANIFEST.json'))
 for i in a.infolist():
  if i.filename!='BUNDLE-MANIFEST.json':z.writestr(i,a.read(i.filename))
 z.write(f,n,compress_type=zipfile.ZIP_DEFLATED);m['files'].append({'path':n,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size});z.writestr('BUNDLE-MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2),compress_type=zipfile.ZIP_DEFLATED)
t.replace(p);m.update(archive='packs/wuluo-cun.prepared.zip',archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest());(r/'packs/wuluo-cun.prepared.manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8');dest=r/'runs/wuluo-cun-content-deploy-v3';dest.mkdir(exist_ok=False)
with zipfile.ZipFile(p) as z:assert z.testzip() is None;z.extractall(dest)
for x in m['files']:assert hashlib.sha256((dest/x['path']).read_bytes()).hexdigest()==x['sha256']
print('extracted',len(m['files']),m['archive_sha256'])
