"""Documentation/evidence-only final archive update with runtime byte equivalence check."""
from pathlib import Path
import json,hashlib,zipfile,uuid,subprocess,sys,shutil
R=Path(__file__).resolve().parents[1];T='fengnian-gaiban';J=R/'judge'/T;P=R/'tasks'/T
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
for p in [P/'README.md',R/f'scripts/{T}_prepare.py']:
 p.write_text(p.read_text(encoding='utf-8').replace('633条','647条'),encoding='utf-8')
spec=json.loads((J/'checkpoint-spec.json').read_text(encoding='utf-8'));spec['optional_reasoning_candidates']['black_decode']='Geometry output kujlt-9 is a Caesar -9 shift -> black. Separate from the geometry calculation; typed at encrypted file gate.';spec['identity_image_clue']='Clicking obituary photo toggles to wangyu_2.jpg; 00023 is visibly printed on coat.';put(J/'checkpoint-spec.json',spec)
entry=json.loads((J/'verification/entry-acceptance.json').read_text(encoding='utf-8'));entry.update(runtime_clean=False,runtime_blocker='Both versions show lastUnzip TDZ error on unlocked same-context reload; source-order defect preserved.');put(J/'verification/entry-acceptance.json',entry)
ev=R/f'packs/{T}.prepared.zip'
with zipfile.ZipFile(ev) as z:old={n:z.read(n) for n in z.namelist()}
runtime={n:sha(b) for n,b in old.items() if n.startswith(('harness/',f'tasks/{T}/mirror/','configs/')) or n in [f'judge/{T}/judge.json',f'judge/{T}/verify_sample.py','scripts/run_one.py','scripts/serve_static.py']}
data=dict(old)
for p in [P/'README.md',J/'checkpoint-spec.json',J/'review.md',J/'verify_media.py',J/'verification/entry-acceptance.json',J/'verification/deployed-full-acceptance.json']:
 data[p.relative_to(R).as_posix()]=p.read_bytes()
assert all(sha(data[n])==h for n,h in runtime.items())
bm=json.loads(data['BUNDLE-MANIFEST.json']);bm['files']=[{'path':n,'bytes':len(b),'sha256':sha(b)} for n,b in sorted(data.items()) if n!='BUNDLE-MANIFEST.json'];data['BUNDLE-MANIFEST.json']=json.dumps(bm,ensure_ascii=False,indent=2).encode()
with zipfile.ZipFile(ev,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in data.items():z.writestr(n,b)
bm.update(archive=ev.relative_to(R).as_posix(),archive_sha256=sha(ev.read_bytes()));put(R/f'packs/{T}.prepared.manifest.json',bm)
deploy=R/'runs'/f'{T}-final-deploy-{uuid.uuid4().hex[:8]}';deploy.mkdir()
with zipfile.ZipFile(ev) as z:assert z.testzip() is None;z.extractall(deploy)
for f in bm['files']:assert sha((deploy/f['path']).read_bytes())==f['sha256'],f['path']
assert all(sha((deploy/n).read_bytes())==h for n,h in runtime.items())
media=subprocess.run([sys.executable,str(deploy/f'judge/{T}/verify_media.py'),'--port','8823'],cwd=deploy,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
(J/'verification/deployed-media.log').write_text(media.stdout+media.stderr,encoding='utf-8');assert media.returncode==0,media.stderr
for name in ['media-acceptance.json','obituary-ID-reveal.png']:shutil.copyfile(deploy/f'judge/{T}/verification/{name}',J/'verification'/('deployed-'+name))
smoke=subprocess.run([sys.executable,str(deploy/'scripts/run_one.py'),'--config',f'configs/{T}.json','--policy','script'],cwd=deploy,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
(J/'verification/deployed-cli-smoke.log').write_text(smoke.stdout+smoke.stderr,encoding='utf-8');assert smoke.returncode==0,smoke.stderr
dep=json.loads((J/'deployment.json').read_text(encoding='utf-8'));dep.update(final_root=str(deploy),final_evaluation_sha256=sha(ev.read_bytes()),runtime_files_unchanged_since_full_replay=len(runtime),final_hashes_and_crc_pass=True,final_photo_ui_pass=True,final_standard_cli_smoke_pass=True,evidence_reuse='Final archive changes only documentation/evidence plus a new supplemental verifier. Game, harness, config, judge and full replay verifier exactly match the independently tested full deployment.');put(J/'deployment.json',dep)
print('final archive runtime-equivalent; independent photo UI and standard CLI smoke passed')
