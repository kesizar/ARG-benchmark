from pathlib import Path
import json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parents[1];T='zhengming-renlei';J=R/'judge'/T
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
d=read(J/'deployment.json');root=Path(d['deployment_root']);proof=root/'judge'/T/'verification';a=read(proof/'acceptance.json');assert a['pass'] and len(a['branches'])==4
assert all(len(b['titles'])==9 and b['reload_reset_pass'] and b['score']['checkpoints_total']==0 for b in a['branches'])
m=read(R/f'packs/{T}.prepared.manifest.json')
for archive in m['archives']:
 p=R/archive['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==archive['sha256'];assert zipfile.ZipFile(p).testzip() is None
assert d['archive_sha256']==m['archives'][1]['sha256']
for f in m['files']:assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256']
(J/'verification').mkdir(exist_ok=True)
for p in proof.glob('*.json'):shutil.copyfile(p,J/'verification'/p.name)
for p in proof.glob('*.png'):
 if p.name.startswith(('completion-','mask-')):shutil.copyfile(p,J/'verification'/p.name)
smoke=sorted((root/'runs'/T/'B').glob('*/summary.json'))[-1];assert read(smoke)['steps']==2
write(J/'resource-check.json',{'resource_files':1,'source_sha256_matches_catalogue':True,'external_dependencies':[],'account_requirement':'none','modifications':[],'canvas_web_audio':'local generated; four random visual phrases, no route randomness','UI_http_errors':a['http_errors'],'UI_page_errors':a['page_errors']})
d.update(status='independent_bundle_ui_pass',acceptance=f'judge/{T}/verification/acceptance.json',standard_runner_smoke=str(smoke),verified_stages=9,full_replays=4,question_option_coverage=8,limitations=['existing Windows Python/browser used, not fresh OS install','four question pairs tested, not all16 cross-product combinations']);write(J/'deployment.json',d)
accept={'record_id':'base664:0658','status':'engineering_ready_content_unsuitable_for_reasoning','archives':m['archives'],'ui_evidence':f'judge/{T}/verification/acceptance.json','deployment_evidence':f'judge/{T}/deployment.json','stages':9,'full_replays':4,'model_api_calls':0};write(R/f'packs/{T}.acceptance.json',accept)
r={'record_id':'base664:0658','task_id':T,'title':'证明你不是人类','status':'engineering_ready_content_unsuitable_for_reasoning','runtime_layer':'L1','account_requirement':'none','ready_for_local_execution':True,'ready_for_formal_scoring':False,'resources_bundle':f'packs/{T}.resources.zip','evaluation_bundle':f'packs/{T}.prepared.zip','deployment_evidence':f'judge/{T}/deployment.json','acceptance':f'packs/{T}.acceptance.json','archives':m['archives'],'coverage':{'stages':9,'full_ui_replays':4,'question_options':8,'reasoning_points':0,'formal_completions':1,'post_completion_states':1,'terminal_failures':0},'content_finding':'All grids and word input unchecked; wrong image A and all question options proceed. Old optional checkpoints downgraded to events. No meaningful reasoning score possible.','model_api_calls':0,'limitations':['No fresh OS/cross-platform verification','No live origin parity or model solving test','Visuals/phrase/humanity random; route unaffected'],'evidence':[f'judge/{T}/flow.json',f'judge/{T}/review.md',f'judge/{T}/checkpoint-spec.json',f'judge/{T}/verification/acceptance.json']};write(R/'data/preparation/results/base664-0658.json',r)
print('ZHENGMING FINALIZED: 9 stages, 4 full replays, zero inference gates')
