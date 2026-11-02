import json,shutil,subprocess,sys,hashlib,zipfile,difflib
from pathlib import Path
r=Path.cwd(); j=r/'judge/feiqi-yiyuan/judge.json'; c=r/'configs/feiqi-yiyuan.json'; oldj=(r/'judge/feiqi-yiyuan/verification/judge-before-cumulative.json').read_text(encoding='utf8');oldc=(r/'judge/feiqi-yiyuan/verification/config-before-cumulative.json').read_text(encoding='utf8')
j.write_bytes((r/'judge/feiqi-yiyuan/judge-final-draft.json').read_bytes()); d=json.loads((r/'configs/feiqi-yiyuan-final-draft.json').read_text(encoding='utf8')); d['judge_path']='judge/feiqi-yiyuan/judge.json'; c.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');
for name,old,p in [('judge',oldj,j),('config',oldc,c)]: (r/f'judge/feiqi-yiyuan/verification/{name}-cumulative.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),p.read_text(encoding='utf8').splitlines(True),fromfile='before',tofile='after')),encoding='utf8')
subprocess.run([sys.executable,str(r/'scripts/build_prepared_bundle.py'),'--task','feiqi-yiyuan'],cwd=r,check=True)
p=r/'packs/feiqi-yiyuan.prepared.zip'; tmp=p.with_suffix('.tmp.zip'); extra=['scripts/feiqi_cumulative_loop_test.py','configs/feiqi-yiyuan-final-draft.json','judge/feiqi-yiyuan/judge-final-draft.json']+[f'{kind}/feiqi-yiyuan-{v}.json' if kind=='configs' else f'judge/feiqi-yiyuan/judge-{v}.json' for v in ['follow','truth','deeper'] for kind in ['configs','judge']]
with zipfile.ZipFile(p) as src,zipfile.ZipFile(tmp,'w') as dst:
 m=json.loads(src.read('BUNDLE-MANIFEST.json')); names=set(src.namelist());
 for info in src.infolist():
  if info.filename!='BUNDLE-MANIFEST.json': dst.writestr(info,src.read(info.filename))
 for n in extra:
  if n not in names:
   f=r/n; dst.write(f,n,compress_type=zipfile.ZIP_DEFLATED);m['files'].append({'path':n,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
 dst.writestr('BUNDLE-MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2),compress_type=zipfile.ZIP_DEFLATED)
tmp.replace(p);m.update(archive='packs/feiqi-yiyuan.prepared.zip',archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest());(r/'packs/feiqi-yiyuan.prepared.manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8'); dest=r/'runs/feiqi-yiyuan-cumulative-deploy';dest.mkdir(exist_ok=False)
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;z.extractall(dest)
for row in m['files']:assert hashlib.sha256((dest/row['path']).read_bytes()).hexdigest()==row['sha256']
print('EXTRACTED',len(m['files']),m['archive_sha256'])
