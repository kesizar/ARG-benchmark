"""Close acceptance only after independent-package real UI audit succeeds."""
from pathlib import Path
import hashlib,json,shutil,zipfile,re
R=Path(__file__).resolve().parents[1];T='guijia-zhinan';J=R/'judge'/T
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
d=read(J/'deployment.json');deployed=Path(d['deployment_root']);proof=deployed/'judge'/T/'verification';a=read(proof/'acceptance.json')
assert a['pass'] and a['full_reset_pass'] and len(a['nodes'])==49
assert len(a['branches'])==4 and a['branches'][-1]['collection_score']['route_id']=='guide'
assert a['branches'][-1]['collection_score']['ending_reached']
assert a['negative_checks']==16,a['negative_checks']
assert not a['page_errors'] and not a['http_errors']
assert a['coordinate_overrides'] is False and a['state_injection'] is False
manifest=read(R/f'packs/{T}.prepared.manifest.json')
for arc in manifest['archives']:
 p=R/arc['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==arc['sha256']
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
assert d['archive_sha256']==manifest['archives'][1]['sha256']
for f in manifest['files']:
 assert hashlib.sha256((deployed/f['path']).read_bytes()).hexdigest()==f['sha256']
for name in ['acceptance.json','ending-A.png','ending-B.png','ending-C.png','ending-D.png','wrong-1-3.png','wrong-1-6.png','wrong-1-12.png','wrong-2-2.png']:
 (J/'verification').mkdir(exist_ok=True);shutil.copyfile(proof/name,J/'verification'/name)
smokes={}
for task in [T,T+'-collection']:
 reports=sorted((deployed/'runs'/task/'B').glob('*/summary.json'));assert reports
 v=read(reports[-1]);assert v['steps']==2,v
 smokes[task]={'path':str(reports[-1]),'steps':2,'policy':'script','purpose':'integration smoke, not completion'}
d.update(status='independent_bundle_complete_ui_pass',acceptance=f'judge/{T}/verification/acceptance.json',verified_nodes=49,verified_endings=5,negative_checks=16,numbered_actions_only=True,standard_runner_smokes=smokes,limitations=['Uses existing Windows Python environment and installed browser; not a fresh operating system or cross-platform install test.','Scripted engineering acceptance, no paid model API calls.'])
write(J/'deployment.json',d)
html=(R/'tasks'/T/'mirror/index.html').read_text(encoding='utf-8')
assets=re.findall(r'<(?:script|img|link|iframe|audio|video|source)\b[^>]*(?:src|href)=[\"\']([^\"\']+)',html,re.I)
assert assets==[]
write(J/'resource-check.json',{'record_id':'base664:0426','runtime_layer':'L1','account_requirement':'none','source_equals_deployed_resource':hashlib.sha256((R/'tasks'/T/'mirror/index.html').read_bytes()).hexdigest()==read(R/'tasks'/T/'provenance.json')['source_sha256'],'asset_references':assets,'resource_files':1,'modifications':[],'external_game_requests_or_dependencies':'none in source; UI full walkthrough generated no blocked external requests or HTTP errors','graphics':'inline SVG','audio':'WebAudio synthesis','fictional_online_actions':'Tor download and .onion navigation are local UI state transitions only','live_origin_parity':'not verified'})
acceptance={'record_id':'base664:0426','task_id':T,'status':'engineering_ready_content_review_required','source_snapshot_unchanged':True,'archives':manifest['archives'],'ui_evidence':f'judge/{T}/verification/acceptance.json','deployment_evidence':f'judge/{T}/deployment.json','nodes_covered':49,'endings_covered':5,'negative_checks':16,'standard_runner_smokes':smokes,'model_api_calls':0}
write(R/f'packs/{T}.acceptance.json',acceptance)
result={'record_id':'base664:0426','task_id':T,'title':'归家指南','status':'engineering_ready_content_review_required','runtime_layer':'L1','account_requirement':'none','ready_for_local_execution':True,'ready_for_formal_scoring':False,'resources_bundle':f'packs/{T}.resources.zip','evaluation_bundle':f'packs/{T}.prepared.zip','deployment_evidence':f'judge/{T}/deployment.json','acceptance':f'packs/{T}.acceptance.json','config':f'configs/{T}.json','collection_config':f'tasks/{T}/collection.json','judge':f'judge/{T}/judge.json','collection_judge':f'judge/{T}/collection-judge.json','archives':manifest['archives'],'coverage':{'story_nodes':49,'formal_endings':4,'hidden_endings':1,'terminal_failures':0,'retryable_wrong_inputs':4,'negative_checks':16,'critical_reasoning_points':1,'optional_reasoning_points':1},'endings_classification':'All four labelled endings plus hidden guide are completion; no quality rank. Credits/menu are navigation; D is fictional closing screen, not exit.','changes':'None to original resource. New private judges remove answer-copy inputs from reasoning score and split first-ending versus collection objectives.','limitations':['Original Chinese Base64 hint says four characters but answer has five.','Memo password and darkweb address directly exposed in visible hints; recorded only as events, not reasoning.','Mostly linear narrative after chapter2; hidden ending requires four repeated playthroughs.','Live source parity, fresh OS installation, other observation modes, and model solving performance not verified.'],'evidence':[f'judge/{T}/flow.json',f'judge/{T}/checkpoint-spec.json',f'judge/{T}/resource-check.json',f'judge/{T}/review.md',f'judge/{T}/verification/acceptance.json'],'model_api_calls':0}
write(R/'data/preparation/results/base664-0426.json',result)
print('GUIJIA FINALIZED: independent UI 49 nodes, 5 endings, 16 negative checks; two bundles verified.')
