import json,zipfile,hashlib
from pathlib import Path
r=Path.cwd();p=r/'packs/haian-diaopin.prepared.zip';t=p.with_suffix('.tmp.zip');n='scripts/haian_diaopin_ending_closeout.py';b=(r/n).read_bytes()
with zipfile.ZipFile(p) as a,zipfile.ZipFile(t,'w') as z:
 m=json.loads(a.read('BUNDLE-MANIFEST.json'));next(x for x in m['files'] if x['path']==n).update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 for i in a.infolist(): z.writestr(i,b if i.filename==n else json.dumps(m,ensure_ascii=False,indent=2).encode('utf8') if i.filename=='BUNDLE-MANIFEST.json' else a.read(i.filename))
t.replace(p);dest=r/'runs/haian-diaopin-ending-deploy';(dest/n).write_bytes(b);(dest/'BUNDLE-MANIFEST.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8');m.update(archive='packs/haian-diaopin.prepared.zip',archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest());(r/'packs/haian-diaopin.prepared.manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
with zipfile.ZipFile(p) as z:assert z.testzip() is None
for row in m['files']:assert hashlib.sha256((dest/row['path']).read_bytes()).hexdigest()==row['sha256']
print(m['archive_sha256'])
