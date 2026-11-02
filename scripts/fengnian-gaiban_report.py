from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];T='fengnian-gaiban';J=R/'judge'/T
def put(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
full=json.loads((J/'verification/deployed-full-acceptance.json').read_text(encoding='utf-8'));media=json.loads((J/'verification/deployed-media-acceptance.json').read_text(encoding='utf-8'));dep=json.loads((J/'deployment.json').read_text(encoding='utf-8'))
assert full['passed'] and full['phase']=='all' and media['passed'];assert set(full['score']['diagnostic'])=={'geometry','identity','black_decode','base64_diary','birth'}
assert set(full['trace'][-1]['endings'])=={'self_end1','self_end2','real1','real2','egg','uuu'}
archives=[]
for kind in ['resources','prepared']:
 p=R/f'packs/{T}.{kind}.zip'
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  if kind=='resources':
   assert not any(n.startswith(('judge/','configs/','harness/')) or n.endswith('.py') for n in z.namelist())
   for f in (R/f'tasks/{T}/mirror').iterdir():
    if f.is_file():assert hashlib.sha256(z.read(f.name)).hexdigest()==sha(f)
  else:
   bm=json.loads(z.read('BUNDLE-MANIFEST.json'))
   for f in bm['files']:assert hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256']
 archives.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
dep['full_replay_evaluation_sha256']=dep['evaluation_sha256'];dep['evaluation_sha256']=archives[1]['sha256'];put(J/'deployment.json',dep)
smokes=list((Path(dep['final_root'])/'runs'/T).rglob('summary.json'));smoke=json.loads(smokes[-1].read_text(encoding='utf-8'));assert smoke['steps']==2 and not smoke['ending_reached'] and not smoke['blocked_requests'];put(J/'verification/deployed-cli-smoke.json',smoke)
report={'record_id':'base664:0417','task_id':T,'title':'奉念（改版）','status':'engineering_replay_verified_entry_clue_review_required','category':'web_puzzle','runtime_layer':'L1','account_requirement':'none','ready_for_local_execution':True,'ready_for_formal_scoring':False,
 'resource_status':'91_frozen_public_files_647_local_references_no_missing_dependencies; original_81792_byte_entry_preserved; current_entry_normalized_equal_CRLF_only',
 'integration_status':'source_assisted_actual_UI_replay_and_standard_scripted_CLI_startup; initial_unassisted_entry_clue_missing',
 'flow_status':'six_authored_endings_and_50_reachable_HTML_pages; four_survey_bands; two_phone_audio_branches; camera_denial_fallback; all_main_wrong_input_types; menu_and_fresh_context_reset_verified',
 'judge_status':'independent_private_DOM_judge; one_common_critical_and_five_optional_reasoning_candidates; no_credit_for_stale_storage_or_plain_navigation; formal_content_review_required',
 'config':f'configs/{T}.json','judge':f'judge/{T}/judge.json','resources_bundle':archives[0]['path'],'evaluation_bundle':archives[1]['path'],'archives':archives,'deployment_evidence':f'judge/{T}/deployment.json','acceptance':f'judge/{T}/verification/deployed-full-acceptance.json','checkpoint_spec':f'judge/{T}/checkpoint-spec.json','review':f'judge/{T}/review.md','provenance':f'tasks/{T}/provenance.json',
 'coverage':{'formal_authored_endings':6,'visited_reachable_html_pages':50,'legacy_unlinked_html_not_claimed_playable':['open.html'],'full_UI_actions':len(full['trace']),'negative_checks':len(full['negative_checks']),'critical_reasoning_candidates':1,'optional_reasoning_candidates':5,'questionnaire_score_bands':[5,11,16,20],'phone_audio_numbers':2,'source_context_runtime_errors':0,'full_deployment_runtime_errors':len(full['errors']),'full_deployment_http_errors':len(full['http_errors']),'full_deployment_blocked_requests':len(full['blocked_requests']),'obituary_photo_flip_and_restore':True,'menu_reset_preserves_endings':True,'fresh_context_clears_all':True,'stale_storage_not_scored':True,'final_archive_runtime_equivalent_files':dep['runtime_files_unchanged_since_full_replay'],'standard_CLI_smoke_steps':smoke['steps']},
 'ending_classification':'self_end1/self_end2 are BAD END; real1/real2 are REAL END with authored bad tone; egg EXTRA and uuu TRUE. All six recorded as authored completion outcomes without invented quality ranks. Retryable wrong inputs are not endings.',
 'source_assisted':True,'model_solving_claim':False,'game_modifications':[],'shared_harness_modifications':[],'model_api_calls':0,'real_camera_used':False,
 'limitations':['Initial lock only offers an eight-digit birthday hint; no supplied pre-entry identity/date clue. Private source credential never inserted into model prompt.','All six routes were engineering replays with private source-audited inputs, not unaided model solves.','Plaintext AES external-tool URL and calendrical birth conversion utility are not deployed as local player tools; clue sufficiency and tool policy require review before formal scoring.','Original unlocked same-context reload raises lastUnzip TDZ error; preserved and evidenced. Use a fresh context for each evaluation.','Public current entry matches the snapshot after line-ending normalization; historical child pages unavailable, current child-source bytes frozen with hashes.','Final archive doc/evidence additions reused full UI evidence only after verifying 119 game/harness/config/judge/replay runtime files byte-equivalent, plus final extracted photo and CLI UI smoke.','No cross-OS or real-camera acceptance; legacy open.html has no incoming game navigation and was not called reachable.'],
 'evidence':[f'judge/{T}/resource-check.json',f'judge/{T}/flow.json',f'judge/{T}/checkpoint-spec.json',f'judge/{T}/verification/entry-acceptance.json',f'judge/{T}/verification/full-acceptance.json',f'judge/{T}/verification/deployed-full-acceptance.json',f'judge/{T}/verification/deployed-media-acceptance.json',f'judge/{T}/verification/deployed-cli-smoke.json',f'judge/{T}/deployment.json']}
put(R/'data/preparation/results/base664-0417.json',report)
print(report['status'],report['coverage']['full_UI_actions'],'actions;',len(archives),'archives verified')
