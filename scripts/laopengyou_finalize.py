"""Join immutable full walkthrough and stronger current-package negative checks."""
from pathlib import Path
import hashlib,json,zipfile,shutil,re
R=Path(__file__).resolve().parents[1];T='laopengyou';J=R/'judge'/T
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
d=read(J/'deployment.json');root=Path(d['deployment_root']);old=Path(d['compatible_full_ui_evidence']);full=read(old);current=root/'judge'/T/'verification';new=read(current/'acceptance.json');assert full['pass'] and new['pass']
assert len(full['branches'][0]['views'])==23 and len(full['branches'][0]['materials'])==57
assert [b['score']['route_id'] for b in full['branches']]==['wish','accept']
assert all(b['score']['checkpoints_reached']==9 for b in full['branches'])
assert [len(b['score']['diagnostic']) for b in full['branches']]==[4,0]
assert len(new['branches'])==1 and new['branches'][0]['negative_checks']==8 and new['branches'][0]['score']['route_id']=='accept'
assert not full['page_errors'] and not full['http_errors'] and not new['page_errors'] and not new['http_errors']
m=read(R/f'packs/{T}.prepared.manifest.json')
for arc in m['archives']:
 p=R/arc['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==arc['sha256'];assert zipfile.ZipFile(p).testzip() is None
assert d['archive_sha256']==m['archives'][1]['sha256']
for f in m['files']:assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256']
previous=Path(d['previous_full_deployment']['deployment_root']);before={f['path']:f['sha256'] for f in read(previous/'BUNDLE-MANIFEST.json')['files']}
assert {f['path'] for f in m['files'] if before.get(f['path'])!=f['sha256']}=={'judge/laopengyou/review.md','judge/laopengyou/verify_sample.py'}
out=J/'verification';out.mkdir(exist_ok=True);shutil.copyfile(old,out/'full-acceptance.json');shutil.copyfile(current/'acceptance.json',out/'strong-negative-acceptance.json')
for name in ['ending-wish.png','ending-accept.png']:shutil.copyfile(old.parent/name,out/name)
smoke=sorted((root/'runs'/T/'B').glob('*/summary.json'))[-1];assert read(smoke)['steps']==2
src=R/'ARG-packs/verify-84/bodies/83.html';game=R/'tasks'/T/'mirror/index.html';assert src.read_bytes()==game.read_bytes();s=game.read_text(encoding='utf-8');assets=re.findall(r'<(?:script|img|link|audio|video|iframe)\b[^>]*(?:src|href)=[\"\']([^\"\']+)',s,re.I);assert not assets
write(J/'resource-check.json',{'record_id':'added84:0083','resource_files':1,'bytes':game.stat().st_size,'sha256':hashlib.sha256(game.read_bytes()).hexdigest(),'matches_catalogue_sha256':True,'external_assets':[],'account_requirement':'none; all credentials fictional and local','changes':[],'source_version':'frozen imported snapshot; live site not compared'})
d.update(status='full_ui_compatible_with_stronger_current_negative_assertions_passed',full_ui=f'judge/{T}/verification/full-acceptance.json',current_ui=f'judge/{T}/verification/strong-negative-acceptance.json',standard_runner_smoke=str(smoke),views_covered=23,material_records_opened=57,negative_checks_full_paths=21,current_extra_negative_checks=8,reasoning_points={'critical':9,'optional':4},limitations=['Existing Windows Python/browser used, not fresh OS/cross-platform install.','Source-informed engineering replay, not autonomous model solving.']);write(J/'deployment.json',d)
a={'record_id':'added84:0083','status':'engineering_ready_content_review_required','archives':m['archives'],'full_ui_evidence':d['full_ui'],'current_negative_evidence':d['current_ui'],'deployment_evidence':f'judge/{T}/deployment.json','source_unchanged':True,'views':23,'material_records':57,'endings':2,'full_negative_checks':21,'additional_current_checks':8,'model_api_calls':0};write(R/f'packs/{T}.acceptance.json',a)
r={'record_id':'added84:0083','task_id':T,'title':'老朋友之死','status':'engineering_ready_content_review_required','runtime_layer':'L1','account_requirement':'none','ready_for_local_execution':True,'ready_for_formal_scoring':False,'resources_bundle':f'packs/{T}.resources.zip','evaluation_bundle':f'packs/{T}.prepared.zip','deployment_evidence':f'judge/{T}/deployment.json','acceptance':f'packs/{T}.acceptance.json','archives':m['archives'],'coverage':{'views':23,'material_records_opened':57,'formal_endings':2,'terminal_failure_endings':0,'critical_reasoning_gates':9,'optional_reasoning_gates':4,'final_quiz_questions':8,'negative_checks_full_paths':21,'additional_current_negative_checks':8},'judge_changes':['Hidden static result texts require visible modal before ending credit.','System credential gate and eight submitted question checks scored separately.','Four mechanically bypassable fictional logins optional, not universal route gates.','Question answers are sampled only on submitted complete quiz result modals, never mere unsubmitted selection. Correct submitted questions latch while other questions may be wrong.','Both revival choices completion, no invented good/bad tier.'],'content_limitations':['Narrative evidence sufficiency and story use of psychiatric concepts need independent content review.','Original impossible date2020.6.31 preserved as authored.','Correct credentials/facts can mechanically bypass optional evidence collection; classified explicitly.','Live source parity, fresh OS/cross-platform installation and model solving performance not verified.'],'evidence':[f'judge/{T}/flow.json',f'judge/{T}/checkpoint-spec.json',f'judge/{T}/review.md',f'judge/{T}/resource-check.json',d['full_ui'],d['current_ui']],'model_api_calls':0};write(R/'data/preparation/results/added84-0083.json',r)
print('LAOPENGYOU FINALIZED: 23 views, 57 materials, 2 endings, 9 critical + 4 optional gates')
