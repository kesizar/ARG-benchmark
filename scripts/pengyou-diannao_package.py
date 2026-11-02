from pathlib import Path
import hashlib,json,subprocess,sys,uuid,zipfile
R=Path(__file__).resolve().parents[1];T='pengyou-diannao';J=R/f'judge/{T}';O=J/'verification'
for p in [O/'acceptance.json',O/'auxiliary/auxiliary-acceptance.json',O/'system/system-acceptance.json',O/'minimum/minimum-acceptance.json']:assert json.loads(p.read_text(encoding='utf-8'))['pass'],p
# Game-only bundle contains no answers, config, judge or credentials.
with zipfile.ZipFile(R/f'packs/{T}.resources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in (R/f'tasks/{T}/mirror').rglob('*'):
  if p.is_file():z.write(p,p.relative_to(R/f'tasks/{T}/mirror').as_posix())
resource_zip=R/f'packs/{T}.resources.zip';prov=json.loads((R/f'tasks/{T}/provenance.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(resource_zip) as z:
 assert z.testzip() is None and set(z.namelist())=={f['path'] for f in prov['files']}
 for f in prov['files']:assert hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256']
rm={'task_id':T,'runtime_layer':'L1','source':prov['origin'],'files':[{k:f[k] for k in ['path','bytes','sha256']} for f in prov['files']],'archive':resource_zip.relative_to(R).as_posix(),'archive_sha256':hashlib.sha256(resource_zip.read_bytes()).hexdigest(),'game_changes':[],'secrets_or_evaluator_files_in_resource_archive':False,'crc_verified':True};(R/f'packs/{T}.resources.manifest.json').write_text(json.dumps(rm,ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',T],cwd=R,check=True)
m=json.loads((R/f'packs/{T}.prepared.manifest.json').read_text(encoding='utf-8'));dest=R/'runs'/f'{T}-deploy-{uuid.uuid4().hex[:8]}';dest.mkdir()
with zipfile.ZipFile(R/f'packs/{T}.prepared.zip') as z:
 assert z.testzip() is None
 for n in z.namelist():assert (dest/n).resolve().is_relative_to(dest)
 z.extractall(dest)
def hashes():
 for f in m['files']:assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
hashes()
subprocess.run([sys.executable,str(dest/'scripts/run_one.py'),'--config',f'configs/{T}.json','--policy','script'],cwd=dest,check=True)
smokes=list((dest/f'runs/{T}/B').glob('*/summary.json'));assert smokes
smoke=json.loads(smokes[-1].read_text(encoding='utf-8'));assert smoke['ended_reason']=='give_up' and smoke['steps']==1 and smoke['model']['provider']=='script'
(O/'deployed-cli-smoke.json').write_text(json.dumps({'scope':'One-step startup/observe/judge/log/cleanup only; full flows proven separately.','summary':smoke,'summary_path':str(smokes[-1])},ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(dest/f'judge/{T}/verify_sample.py'),'--port','8823'],cwd=dest,check=True)
subprocess.run([sys.executable,str(dest/f'judge/{T}/verify_sample.py'),'--port','8823','--aux-only'],cwd=dest,check=True)
subprocess.run([sys.executable,str(dest/f'judge/{T}/verify_sample.py'),'--port','8823','--system-only'],cwd=dest,check=True)
subprocess.run([sys.executable,str(dest/f'judge/{T}/verify_sample.py'),'--port','8823','--minimum-only'],cwd=dest,check=True)
hashes()
for p in [f'judge/{T}/verification/acceptance.json',f'judge/{T}/verification/auxiliary/auxiliary-acceptance.json',f'judge/{T}/verification/system/system-acceptance.json',f'judge/{T}/verification/minimum/minimum-acceptance.json']:
 data=json.loads((dest/p).read_text(encoding='utf-8'));assert data['pass'];target=J/'verification'/('deployed-'+Path(p).name);target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
d={'status':'independent_full_ui_passed','deployment_root':str(dest),'archive_sha256':m['archive_sha256'],'hashes_verified_before_and_after':True,'crc_verified':True,'server_port':8823,'runtime_source':str(dest/'harness'),'prerequisites':'Existing Windows installed Python packages and browser reused; not clean OS or cross-platform installation.','acceptance':f'judge/{T}/verification/deployed-acceptance.json','auxiliary_acceptance':f'judge/{T}/verification/deployed-auxiliary-acceptance.json','paid_model_calls':0};(J/'deployment.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(d),flush=True)
