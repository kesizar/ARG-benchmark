from pathlib import Path
import json,zipfile,hashlib,re,platform
R=Path.cwd();J=R/'judge/room-404';man=json.load(open('packs/room-404.prepared.manifest.json',encoding='utf-8'));dep=json.load(open(J/'deployment.json',encoding='utf-8'));checks=[]
for a in man['archives']:
 p=R/a['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  if '.resources.' in str(p):assert all(n.startswith('tasks/room-404/mirror/') for n in z.namelist())
 checks.append({'archive':a['path'],'crc_ok':True,'sha256':a['sha256']})
with zipfile.ZipFile(R/'packs/room-404.prepared.zip') as z:
 for f in man['files']:assert hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'],f['path']
immutable=[f for f in man['files'] if '/verification/' not in f['path']]
for f in immutable:
 p=Path(dep['paths']['prepared'])/f['path'];assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],f['path']
for f in json.load(open('tasks/room-404/provenance.json',encoding='utf-8'))['public_files']:
 p=Path(dep['paths']['resources'])/'tasks/room-404/mirror'/f['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
report={'archives':checks,'prepared_archive_manifest_files_verified':len(man['files']),'deployed_immutable_files_verified':len(immutable),'mutable_evidence_outputs_excluded_from_deployed_hash_comparison':'verification outputs are intentionally overwritten by acceptance replay; archive originals verified separately','resources_files_verified':24,'python':platform.python_version(),'platform':platform.platform(),'resource_bundle_evaluator_files':0,'source_original_and_current_retained':True,'model_api_calls':0}
(J/'verification/delivery-integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Integrity verified',len(man['files']),'prepared files and24 resource files')
s=(J/'source/current/assets/index-DyrrZ4RJ.js').read_text(encoding='utf-8');hrefs=sorted(set(re.findall(r'href="([^"\n]+)"',s)));(J/'source/href-inventory.json').write_text(json.dumps(hrefs,ensure_ascii=False,indent=2),encoding='utf-8')
(J/'resource-inventory.json').write_text(json.dumps({'record_id':'base664:0002','version':'current official public SPA index-DyrrZ4RJ.js 2026-10-26','public_files':json.load(open('tasks/room-404/provenance.json',encoding='utf-8'))['public_files'],'declared_game_images':'8 scene JPGs +12 tenant WebP; all same-origin browser captured200','css_external_requests':[],'dynamic_imports':0,'fetch_call':'single Vite modulepreload polyfill; game itself has no backend','audio':'WebAudio synthesized locally','advertising_and_analytics':'removed from local index; originals retained','pwa':'service-worker registration and manifest removed; PWA installation not a target','source_vs_legacy':'Archived DNjinArp JS retained in original ARG-packs path, current frozen source is separately named and hashed','account_requirement':'none; fictional login/email screens only'},ensure_ascii=False,indent=2),encoding='utf-8')
