import json, zipfile, hashlib, difflib, shutil, sys
from pathlib import Path
r=Path.cwd(); j=r/'judge/xinshiji/judge.json'; old=j.read_text(encoding='utf8'); d=json.loads(old); assert d['routes'][0]['tier']=='good'; d['routes'][0]['tier']=None
new=json.dumps(d,ensure_ascii=False,indent=2)+'\n'; (r/'judge/xinshiji/recovery/judge-before-closeout.json').write_text(old,encoding='utf8'); j.write_text(new,encoding='utf8')
(r/'judge/xinshiji/recovery/ending-tier-closeout.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before',tofile='after')),encoding='utf8')
p=r/'packs/xinshiji.prepared.zip'; backup=r/'packs/xinshiji.prepared.before-closeout.zip'; shutil.copy2(p,backup); temp=r/'packs/xinshiji.prepared.closeout.tmp.zip'; name='judge/xinshiji/judge.json'
with zipfile.ZipFile(p) as src, zipfile.ZipFile(temp,'w') as dst:
 m=json.loads(src.read('BUNDLE-MANIFEST.json')); row=next(x for x in m['files'] if x['path']==name); data=j.read_bytes(); row.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)); m['readiness']='Formal scoring with documented clue ambiguities and shortcuts; ending is unclassified.'
 for info in src.infolist():
  payload=data if info.filename==name else json.dumps(m,ensure_ascii=False,indent=2).encode('utf8') if info.filename=='BUNDLE-MANIFEST.json' else src.read(info.filename)
  dst.writestr(info,payload)
temp.replace(p)
manifest=dict(m,archive='packs/xinshiji.prepared.zip',archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest()); (r/'packs/xinshiji.prepared.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
dest=r/'runs/xinshiji-independent/closeout'; dest.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None; z.extractall(dest)
 for row in m['files']:
  assert hashlib.sha256((dest/row['path']).read_bytes()).hexdigest()==row['sha256']
sys.path.insert(0,str(dest)); from harness.judge import Judge
k=Judge.load(dest/name,'xinshiji',dest); k.values={x:True for x in ['company-lock','garden','archive','chat','plan']}; k.update(1); before=k.score(); assert before['checkpoints_reached']==5 and not before['ending_reached']
k.values['final']=True; k.update(2); after=k.score(); assert after['ending_reached'] and after['ending_tier'] is None and not after['good_ending'] and after['route_progress']==1
out={'archive_sha256':manifest['archive_sha256'],'before_final':before,'after_final':after,'manifest_files_verified':len(m['files']),'archive_crc_pass':True,'scope':'Extracted packaged harness with synthetic hook values; prior normal UI covers hooks and ending. Only route tier changed.'}
(r/'judge/xinshiji/recovery/ending-tier-closeout-test.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8'); print(json.dumps(out,ensure_ascii=False))
