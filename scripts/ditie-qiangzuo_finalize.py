from pathlib import Path
import json,hashlib,zipfile,platform,sys
R=Path(__file__).resolve().parents[1];T=R/'tasks/ditie-qiangzuo';A=T/'audit'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for kind in ['prepared','resources']:
 p=R/f'packs/ditie-qiangzuo.{kind}.zip'
 with zipfile.ZipFile(p) as z:
  assert not any(x.startswith(('.env','runs/')) for x in z.namelist())
  if kind=='resources':assert z.namelist()==['index.html']
  else:
   m=read(A/'unpacked-prepared/BUNDLE-MANIFEST.json')
   assert all(sha(A/'unpacked-prepared'/f['path'])==f['sha256'] for f in m['files'])
  game=A/'unpacked-prepared/tasks/ditie-qiangzuo/mirror/index.html' if kind=='prepared' else A/'unpacked-resources/index.html'
  assert sha(game)==sha(T/'mirror/index.html')
 checks[kind]={'archive':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'game_bytes_identical':True,'manifest_hashes_valid':kind=='prepared'}
accept={label:read(A/(label+'-summary.json')) for label in ['workspace','prepared','resources']};assert all(x['passed'] for x in accept.values())
branch=read(A/'branches-summary.json');assert branch['passed']
arrivals=[];ignored=False
for label in accept:
 for stage in read(A/(label+'-ui-trace.json')):
  ignored |= (stage['state'].get('ignored') or 0)>0
  if stage['stage']=='easy_seated_arrival':
   st=stage['state'];expected=int(st['energy']*.6+st['moral']*.2+max(0,100-st['clashes']*4)*.2)
   assert f'最终评分: {expected}' in stage['visible_text'];arrivals.append({'label':label,'expected_score':expected,'verified':True})
assert ignored
smoke=sorted((A/'unpacked-prepared/runs/ditie-qiangzuo/B').glob('*/summary.json'))[-1];h=read(smoke);assert not h['ending_reached']
audit={'packages':checks,'success_original_score_checks':arrivals,'priority_ignore_observed':ignored,'runtime':{'python':sys.version,'platform':platform.platform(),'browser':'installed Microsoft Edge via Playwright channel=msedge'},'harness_smoke':smoke.relative_to(R).as_posix(),'same_runtime_only':True}
(A/'delivery-verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
result={'record_id':'base664:0400','task_id':'ditie-qiangzuo','title':'地铁抢座大作战','runtime_layer':'L1','account_requirement':'none','status':'engineering_complete_not_reasoning_game','resource_status':'complete','integration_status':'complete','content_status':'all_mechanics_source_mapped_main_flows_and_random_action_branches_UI_verified','judge_status':'complete_zero_reasoning_checkpoints','ui_status':'passed_19_stages_each_workspace_and_two_extracts_plus_4_action_branch_stages','delivery_status':'passed','flow_status':'three_difficulties_exhaustion_easy_arrival_menu_pause_speed_reset_custom_import_save_load_delete_priority_yield_ignore_orange_seat_collision','formal_scoring_suitability':'unsuitable_realtime_motor_timing_and_randomness_without_reasoning_gates','evidence':{'readme':'tasks/ditie-qiangzuo/README.md','spec':'judge/ditie-qiangzuo/checkpoint-spec.json','source_audit':'tasks/ditie-qiangzuo/audit/static-audit.json','diff':'tasks/ditie-qiangzuo/audit/localization.diff','provenance':'tasks/ditie-qiangzuo/provenance.json','ui_summaries':[f'tasks/ditie-qiangzuo/audit/{x}-summary.json' for x in accept],'ui_traces':[f'tasks/ditie-qiangzuo/audit/{x}-ui-trace.json' for x in accept],'branches':'tasks/ditie-qiangzuo/audit/branches-summary.json','delivery':'tasks/ditie-qiangzuo/audit/delivery-verification.json','harness_smoke':smoke.relative_to(R).as_posix()},'packages':list(checks.values()),'independent_acceptance':accept,'limits':['Windows and installed Edge only; no cross-OS test.','No paid API/model calls.','All star thresholds are source-audited; UI observed three-star arrival, not separate one/two-star runs. They are weighted arcade score variants, not new narrative routes or reasoning points.','Medium/hard positive arrivals not separately executed; common terminal predicate and all three difficulty failures verified.','Route import supports CSV/TSV/TXT/JSON; normal UI tests JSON valid/too-few input; remaining utility parser branches mapped from source.','Random priority yield/ignore and automatic free-seat resolution observed without state injection; original Math.random preserved.','Only analytics removed; source snapshot original/diff retained.','Original server availability not rechecked because complete L1 snapshot is the evaluation target.'],'all_required_dimensions_complete':True,'formal_benchmark_ready':False,'ready_for_local_execution':True,'ready_for_formal_scoring':False,'resources_bundle':'packs/ditie-qiangzuo.resources.zip','evaluation_bundle':'packs/ditie-qiangzuo.prepared.zip'}
(R/'data/preparation/results/base664-0400.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(T/'HANDOFF.md').write_text('HANDOFF base664:0400 / ditie-qiangzuo\nResult: data/preparation/results/base664-0400.json\nL1 execution ready; formal reasoning scoring not ready (arcade only, zero reasoning checkpoints).\nWorkspace + both independent extracts passed 19 normal UI stages each; 4 extra action branches passed; independent prepared harness give-up smoke negative.\nNo shared progress files modified. Ports 8831–8833 released by test scripts.\nLimits: explicit in result; no one/two-star UI run or medium/hard positive run; not claimed.\n',encoding='utf-8')
print(json.dumps({'result':'data/preparation/results/base664-0400.json','ready_for_local_execution':True,'ready_for_formal_scoring':False,'stages':sum(x['stages'] for x in accept.values())+len(branch['traces'])},ensure_ascii=False))
