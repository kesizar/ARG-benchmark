"""Correct a private explanatory count after full UI acceptance; retain exact runtime evidence."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,uuid,zipfile
R=Path(__file__).resolve().parents[1];T='pengyou-diannao';J=R/f'judge/{T}';P=R/'packs';flow=f'judge/{T}/checkpoint-spec.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(J/'deployment.json');oldroot=Path(d['deployment_root']);m=read(P/f'{T}.prepared.manifest.json');oldm=json.loads(json.dumps(m));archive=P/f'{T}.prepared.zip';oldarchive=P/f'{T}.prepared.before-metadata-fix.zip';assert sha(archive)==m['archive_sha256']==d['archive_sha256'];assert not oldarchive.exists();shutil.copyfile(archive,oldarchive);(P/f'{T}.prepared.before-metadata-fix.manifest.json').write_text(json.dumps(oldm,ensure_ascii=False,indent=2),encoding='utf-8')
spec=read(R/flow);assert any('Album9 search keys' in x for x in spec['optional_flows']);spec['optional_flows']=[x.replace('Album9 search keys','Album8 search keys') for x in spec['optional_flows']];(R/flow).write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8');newbytes=(R/flow).read_bytes()
for row in m['files']:
 if row['path']==flow:row.update(sha256=hashlib.sha256(newbytes).hexdigest(),bytes=len(newbytes))
changes=[v['path'] for u,v in zip(oldm['files'],m['files']) if u!=v];assert changes==[flow]
embedded={k:v for k,v in m.items() if k not in {'archive','archive_sha256'}};temp=P/f'{T}.prepared.metadata-tmp.zip'
with zipfile.ZipFile(oldarchive) as src,zipfile.ZipFile(temp,'w') as dst:
 for info in src.infolist():
  b=newbytes if info.filename==flow else json.dumps(embedded,ensure_ascii=False,indent=2).encode('utf-8') if info.filename=='BUNDLE-MANIFEST.json' else src.read(info.filename)
  dst.writestr(info,b)
with zipfile.ZipFile(temp) as z:assert z.testzip() is None
temp.replace(archive);m['archive_sha256']=sha(archive);(P/f'{T}.prepared.manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');dest=R/'runs'/f'{T}-deploy-metadata-{uuid.uuid4().hex[:8]}';dest.mkdir()
with zipfile.ZipFile(archive) as z:z.extractall(dest)
for f in m['files']:
 assert sha(dest/f['path'])==f['sha256']
 if f['path']!=flow:assert (dest/f['path']).read_bytes()==(oldroot/f['path']).read_bytes()
subprocess.run([sys.executable,str(dest/'scripts/run_one.py'),'--config',f'configs/{T}.json','--policy','script'],cwd=dest,check=True)
summary=next((dest/f'runs/{T}/B').glob('*/summary.json'));smoke=read(summary);assert smoke['steps']==1 and smoke['ended_reason']=='give_up' and smoke['model']['provider']=='script'
proof={'change':'One private flow explanation corrected Album9 to Album8; no gameplay, config, judge, verifier or runtime changes.','previous_archive':oldarchive.relative_to(R).as_posix(),'previous_archive_sha256':oldm['archive_sha256'],'previous_full_ui_deployment_root':str(oldroot),'new_archive_sha256':m['archive_sha256'],'new_deployment_root':str(dest),'changed_manifest_files':changes,'all_other_72_manifest_files_byte_identical_to_full_ui_tested_deployment':True,'new_archive_crc_and_all_extracted_hashes_verified':True,'new_standard_cli_smoke':smoke,'full_ui_acceptance_reused_only_for_identical_game_config_judge_verifier_runtime':True,'model_api_calls':0};(J/'verification/metadata-only-revalidation.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
d.update(deployment_root=str(dest),archive_sha256=m['archive_sha256'],runtime_source=str(dest/'harness'),full_ui_source_deployment_root=str(oldroot),metadata_only_revalidation=f'judge/{T}/verification/metadata-only-revalidation.json',previous_full_ui_archive_sha256=oldm['archive_sha256']);(J/'deployment.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(proof,ensure_ascii=False),flush=True)
