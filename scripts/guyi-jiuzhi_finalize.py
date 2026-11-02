from pathlib import Path
import json,hashlib,zipfile,shutil,socket
R=Path(__file__).resolve().parents[1];T='guyi-jiuzhi';J=R/'judge'/T;D=R/'tasks'/T
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
catalogue=load(R/'data/preparation/catalogue.json')
def find(v):
 if isinstance(v,dict):
  if v.get('record_id')=='base664:0310':return v
  for x in v.values():
   r=find(x)
   if r:return r
 elif isinstance(v,list):
  for x in v:
   r=find(x)
   if r:return r
write(J/'source/catalogue-record.json',find(catalogue))
shutil.copy2(R/'ARG-packs/verify-416/bodies/310.html',J/'source/historical-index.html')
with zipfile.ZipFile(D/'upstream.zip') as z:
 root=z.namelist()[0]
 equal=all((D/'mirror'/n[len(root):]).read_bytes()==z.read(n) for n in z.namelist() if not n.endswith('/'))
assert equal
acceptance=load(J/'verification/acceptance.json');deployment=load(J/'deployment.json');audit=load(J/'resource-audit.json')
assert acceptance['ok'] and deployment['cli_smoke_exit_code']==0
actions={x['check']:x for x in acceptance['actions']}
assert actions['agree_failure_ending']['judge_score']['ending_tier']=='bad'
assert actions['refuse_success_ending']['judge_score']['ending_tier']=='good'
assert not actions['enter_archive_bypass_0414']['judge_values']['archive_gw']
result={'record_id':'base664:0310','task_id':T,'title':'古邑旧志','status':'blocked_resource_and_content_review','runtime_layer':'L1','account_requirement':'none','ready_for_local_execution':False,'ready_for_formal_scoring':False,'candidate_local_execution_verified':True,'resource_status':'73 pinned upstream files recovered byte-identically; five unresolved referenced targets; historical entrance differs from current pinned origin','integration_status':'candidate config and isolated judge available; tabs supported; standard extracted CLI startup passed','flow_status':'normal UI entry, clock, two fictional logins, five-field statistics, three button passwords, Enter bypass, record deletion/logout, two endings and credits verified; full clue derivations and missing content unresolved','judge_status':'seven candidate input gates enumerated; terminal login critical; six optional; excludes archive0414 bypass; good/refuse and bad/agree verified','delivery_status':'separate game-only and evaluator candidate archives extracted; resources8833 and evaluator8832; full UI evidence8831 reused on byte-identical files','content_status':'blocked pending original missing resources and media/PDF inference review','config':f'configs/{T}.json','resources_bundle':f'packs/{T}.resources.zip','evaluation_bundle':f'packs/{T}.prepared.zip','resource_manifest':f'packs/{T}.resources.manifest.json','bundle_manifest':f'packs/{T}.prepared.manifest.json','acceptance':f'judge/{T}/verification/acceptance.json','resource_audit':f'judge/{T}/resource-audit.json','source_revalidation':f'judge/{T}/source/live-check.json','deployment_evidence':f'judge/{T}/deployment.json','flow':f'judge/{T}/checkpoint-spec.json','review':f'judge/{T}/review.md','provenance':f'tasks/{T}/provenance.json','archives':deployment['archives'],'checks':{'unchanged_upstream_files':equal,'source_files':len(audit['files']),'html_page_loads_without_script_error':len(acceptance['page_audit']),'normal_ui_checks':len(acceptance['actions']),'fresh_context_reset':acceptance['fresh_context_reset'],'candidate_judge_good_and_bad_endings':True,'archive_enter_bypass_excluded':True,'independent_bundle_hashes':deployment['manifest_hashes_pass'],'independent_cli_smoke_exit_code':deployment['cli_smoke_exit_code']},'model_api_used':False,'model_api_calls':0,'game_changes':[],'blockers':[{'id':'missing_resources','evidence':f'judge/{T}/resource-audit.json','detail':'level1-2.html, level1-pplm.html, level1-ttqd.html, level1-lxwm.html, level2-glxj.html absent. Some links intentionally alert404; other internal-query links perform real navigation. Main tested route remains playable but full resource coverage cannot pass.'},{'id':'archive_enter_bypass','evidence':f'judge/{T}/verification/acceptance.json','detail':'Three real button passwords3461/3538/5779 are bypassed by0414 Enter path. Original preserved; optional judge excludes it.'},{'id':'inference_and_media_review','evidence':f'judge/{T}/checkpoint-spec.json','detail':'All code validators enumerated, but all media/PDF clue-to-answer derivations and normal screenshot-harness access to these clues remain unverified; cannot call every input a validated reasoning point.'}],'limits':['Existing Windows Python/Edge prerequisites reused, no clean OS or cross-platform installation test.','Full UI actions were source-planned by auditor with no state injection or timer acceleration. No actual model performance or calibrated difficulty claimed.','Extracted standard CLI give_up smoke verifies startup/observe/judge/log/cleanup, not solving.','Formal success/refuse and failure/agree preserve authored semantics; common credits never count as successful ending.'],'next_actions':['Obtain author-confirmed missing files or confirmation that all missing links are intentional.','Reconstruct every PDF/image/audio/video inference chain and verify media readability through allowed evaluator actions.','Resolve or explicitly accept original archive Enter ambiguity before formal scoring.']}
write(R/'data/preparation/results/base664-0310.json',result)
print(json.dumps({'result':'data/preparation/results/base664-0310.json','status':result['status'],'ready':False,'ui_checks':len(acceptance['actions']),'files':len(audit['files'])},ensure_ascii=False))
