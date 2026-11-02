from pathlib import Path
import hashlib,json,subprocess,sys,uuid,zipfile
R=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task','feiqi-yiyuan'],cwd=R,check=True)
archive=R/'packs/feiqi-yiyuan.prepared.zip';m=json.loads((R/'packs/feiqi-yiyuan.prepared.manifest.json').read_text(encoding='utf-8'));dest=R/'runs'/('feiqi-yiyuan-deploy-'+uuid.uuid4().hex[:8]);dest.mkdir()
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name in z.namelist():assert (dest/name).resolve().is_relative_to(dest)
 z.extractall(dest)
for f in m['files']:assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
subprocess.run([sys.executable,str(dest/'judge/feiqi-yiyuan/verify_sample.py'),'--port','8822'],cwd=dest,check=True)
for f in m['files']:assert hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256']
out=R/'judge/feiqi-yiyuan/verification';out.mkdir(exist_ok=True)
for name in ['acceptance.json','follow-ending.png','truth-ending.png','deeper-ending.png','final-ending.png']:(out/('deployed-'+name)).write_bytes((dest/'judge/feiqi-yiyuan/verification'/name).read_bytes())
d={'status':'independent_full_ui_passed','deployment_root':str(dest),'archive_sha256':m['archive_sha256'],'hashes_verified_before_and_after':True,'crc_verified':True,'server_port':8822,'runtime_source':str(dest/'harness'),'prerequisites':'Existing installed Python packages and browser reused, not clean OS installation.','acceptance':'judge/feiqi-yiyuan/verification/deployed-acceptance.json'}
(R/'judge/feiqi-yiyuan/deployment.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(d))
