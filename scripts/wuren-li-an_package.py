from pathlib import Path
import hashlib,json,subprocess,sys,uuid,zipfile
R=Path(__file__).resolve().parents[1];T='wuren-li-an';J=R/f'judge/{T}';O=J/'verification'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
for phase in ['core','negative','reset']:assert read(O/f'{phase}-acceptance.json')['pass']
assets=list((R/f'tasks/{T}/mirror').rglob('*'));assets=[x for x in assets if x.is_file()]
with zipfile.ZipFile(R/f'packs/{T}.resources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in assets:z.write(p,p.relative_to(R/f'tasks/{T}/mirror').as_posix())
rm={'task_id':T,'files':[{'path':p.relative_to(R/f'tasks/{T}/mirror').as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in assets],'archive_sha256':hashlib.sha256((R/f'packs/{T}.resources.zip').read_bytes()).hexdigest()};(R/f'packs/{T}.resources.manifest.json').write_text(json.dumps(rm,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',T],cwd=R,check=True,stdout=subprocess.DEVNULL)
m=read(R/f'packs/{T}.prepared.manifest.json');dest=R/'runs'/f'{T}-deploy-{uuid.uuid4().hex[:8]}';dest.mkdir()
with zipfile.ZipFile(R/f'packs/{T}.prepared.zip') as z:
 assert z.testzip() is None
 for n in z.namelist():assert (dest/n).resolve().is_relative_to(dest)
 z.extractall(dest)
def hashes():
 for f in m['files']:assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
hashes()
with (O/'deployed-cli.log').open('w',encoding='utf-8') as log:subprocess.run([sys.executable,str(dest/'scripts/run_one.py'),'--config',f'configs/{T}.json','--policy','script'],cwd=dest,check=True,stdout=log,stderr=subprocess.STDOUT)
p=next((dest/f'runs/{T}/B').glob('*/summary.json'));smoke=read(p);assert smoke['steps']==1 and smoke['ended_reason']=='give_up' and smoke['model']['provider']=='script';(O/'deployed-cli-smoke.json').write_text(json.dumps({'scope':'Startup/observe/judge/log/cleanup only; not full solving or model score.','summary':smoke},ensure_ascii=False,indent=2),encoding='utf-8')
with (O/'deployed-ui.log').open('w',encoding='utf-8') as log:subprocess.run([sys.executable,str(dest/f'judge/{T}/verify_sample.py'),'--port','8823'],cwd=dest,check=True,stdout=log,stderr=subprocess.STDOUT)
hashes();a=read(dest/f'judge/{T}/verification/acceptance.json');assert a['pass'];(O/'deployed-acceptance.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
d={'status':'independent_full_ui_passed','deployment_root':str(dest),'archive_sha256':m['archive_sha256'],'hashes_verified_before_and_after':True,'crc_verified':True,'server_port':8823,'runtime_source':str(dest/'harness'),'prerequisites':'Existing installed Windows Python packages/browser reused, not clean OS or cross-platform installation.','acceptance':f'judge/{T}/verification/deployed-acceptance.json','standard_cli_smoke':f'judge/{T}/verification/deployed-cli-smoke.json','model_api_calls':0};(J/'deployment.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print('UNFILED INDEPENDENT PASS',m['archive_sha256'],flush=True)
