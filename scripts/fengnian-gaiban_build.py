"""Build separate game/evaluator archives and validate the evaluator after extraction."""
from pathlib import Path
import json,hashlib,zipfile,sys,subprocess,uuid,shutil
R=Path(__file__).resolve().parents[1];T='fengnian-gaiban';P=R/'tasks'/T;J=R/'judge'/T
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
res=R/f'packs/{T}.resources.zip';manifest=[]
with zipfile.ZipFile(res,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((P/'mirror').iterdir()):
  if p.is_file():z.write(p,p.name);manifest.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
put(R/f'packs/{T}.resources.manifest.json',{'task_id':T,'files':manifest,'archive_sha256':sha(res),'ready_for_formal_scoring':False})
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',T],cwd=R,check=True,capture_output=True,text=True)
ev=R/f'packs/{T}.prepared.zip'
with zipfile.ZipFile(ev) as z:data={n:z.read(n) for n in z.namelist()}
for rel in ['flow.json','resource-check.json','review.md','verification/entry-acceptance.json']:
 p=J/rel
 if p.exists():data[p.relative_to(R).as_posix()]=p.read_bytes()
bm=json.loads(data['BUNDLE-MANIFEST.json']);bm['files']=[{'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(data.items()) if n!='BUNDLE-MANIFEST.json'];data['BUNDLE-MANIFEST.json']=json.dumps(bm,ensure_ascii=False,indent=2).encode()
with zipfile.ZipFile(ev,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in data.items():z.writestr(n,b)
bm.update(archive=ev.relative_to(R).as_posix(),archive_sha256=sha(ev));put(R/f'packs/{T}.prepared.manifest.json',bm)
deploy=R/'runs'/f'{T}-deploy-{uuid.uuid4().hex[:8]}';deploy.mkdir()
with zipfile.ZipFile(ev) as z:assert z.testzip() is None;z.extractall(deploy)
for f in bm['files']:assert sha(deploy/f['path'])==f['sha256'],f['path']
proc=subprocess.run([sys.executable,str(deploy/f'judge/{T}/verify_sample.py'),'--port','8823'],cwd=deploy,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=700)
(J/'verification/deployed-full.log').write_text(proc.stdout+proc.stderr,encoding='utf-8')
source=deploy/f'judge/{T}/verification/full-acceptance.json'
if source.exists():shutil.copyfile(source,J/'verification/deployed-full-acceptance.json')
assert proc.returncode==0,proc.stderr
accept=json.loads(source.read_text(encoding='utf-8'));assert accept['passed'] and accept['phase']=='all'
put(J/'deployment.json',{'kind':'independent_extracted_full_ui_engineering_replay','root':str(deploy),'port':8823,'zip_crc_pass':True,'file_hashes_pass':True,'game_entry_byte_identical_snapshot':sha(deploy/f'tasks/{T}/mirror/index.html')=='734872ecd5e3b42b5c1736e0ef99b0d79f3a3f73c127d97d841c929ec04b70a0','full_engineering_flow_pass':True,'formal_scoring_approved':False,'cross_os_acceptance':False,'source_assisted':True,'model_api_calls':0,'resources_sha256':sha(res),'evaluation_sha256':sha(ev)})
print('independent extracted full engineering replay passed; formal scoring remains unapproved')
