import json,zipfile,hashlib
from pathlib import Path
r=Path.cwd();p=r/'packs/feiqi-yiyuan.prepared.zip';t=p.with_suffix('.tmp.zip');n='scripts/feiqi_cumulative_loop_test.py';b=(r/n).read_bytes()
with zipfile.ZipFile(p) as a,zipfile.ZipFile(t,'w') as z:
 m=json.loads(a.read('BUNDLE-MANIFEST.json'));next(x for x in m['files'] if x['path']==n).update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 for info in a.infolist():z.writestr(info,b if info.filename==n else json.dumps(m,ensure_ascii=False,indent=2).encode('utf8') if info.filename=='BUNDLE-MANIFEST.json' else a.read(info.filename))
t.replace(p);dest=r/'runs/feiqi-yiyuan-cumulative-deploy';(dest/n).write_bytes(b);(dest/'BUNDLE-MANIFEST.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8');m.update(archive='packs/feiqi-yiyuan.prepared.zip',archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest());(r/'packs/feiqi-yiyuan.prepared.manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
with zipfile.ZipFile(p) as z: assert z.testzip() is None
for row in m['files']:assert hashlib.sha256((dest/row['path']).read_bytes()).hexdigest()==row['sha256']
print(m['archive_sha256'])
