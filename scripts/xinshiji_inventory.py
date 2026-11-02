from pathlib import Path
import json,hashlib,shutil,re
root=Path('tasks/xinshiji');audit=Path('judge/xinshiji/recovery');rows=json.loads((audit/'browser-crawl.json').read_text('utf8'));idx=rows[0]['sha256'];files=[];bad=[]
for r in rows:
 if 'sha256' not in r:continue
 if r['path']!='index.html' and r['sha256']==idx:
  bad.append(r['path']);continue
 p=root/'original'/r['path'];q=root/'mirror'/r['path'];q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);files.append(r)
# Delete only crawler-generated SPA-fallback files after exact hash checking.
for r in rows:
 p=root/'original'/r['path']
 if r.get('sha256')==idx and r['path']!='index.html' and p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==idx:p.unlink()
# Only beijing is referenced by an authentic page; all nested paths came from false SPA responses.
(root/'source').mkdir(exist_ok=True)
if (root/'source/config-l3.original.json').exists():raise RuntimeError('Recovery inventory already finalized; do not overwrite provenance originals')
shutil.copy2('configs/xinshiji.json',root/'source/config-l3.original.json');shutil.copy2('judge/xinshiji/judge.json',root/'source/judge.original.json');shutil.copy2('ARG-packs/verify-416/bodies/315.html',root/'source/snapshot-315.html')
a={'record_id':'base664:0315','task_id':'xinshiji','files':files,'bytes':sum(r['bytes'] for r in files),'missing':[{'path':'wangzhan/beijing.jpg','evidence':'HTTP200 text/html identical SHA256 to index; original decorative body background, not an image'}],'external_dependencies':[],'crawler_spa_false_positives':bad,'snapshot_sha256':hashlib.sha256((root/'source/snapshot-315.html').read_bytes()).hexdigest(),'modifications':'none; original assets unchanged; fallback HTML excluded from mirror','account_requirement':'none; member credentials are in-game fictional puzzle'}
(root/'provenance.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'real_files':len(files),'bytes':a['bytes'],'missing':a['missing']}))
