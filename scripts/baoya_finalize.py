"""Validate completed bundle evidence and write this record's exclusive result."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'judge/baoya/deployment.json';deployment=json.loads(p.read_text(encoding='utf-8'));dep=Path(deployment['deployment_root'])
full_dep=Path(deployment.get('previous_full_ui_deployment',{}).get('deployment_root',str(dep)))
acceptance=json.loads((full_dep/'judge/baoya/verification/acceptance.json').read_text(encoding='utf-8'))
numbered_path=dep/'judge/baoya/verification/numbered-navigation.json'
numbered=json.loads(numbered_path.read_text(encoding='utf-8')) if numbered_path.is_file() else None
if full_dep!=dep:
    assert numbered and numbered['pass'] and not numbered['coordinate_override_used']
    for rel in deployment['unchanged_game_config_judge_files']:
        assert (dep/rel).read_bytes()==(full_dep/rel).read_bytes(),rel
assert acceptance['pass'] and not acceptance['page_errors'] and not acceptance['http_errors']
assert len(acceptance['branches'])==3
assert [len(b['score']['diagnostic']) for b in acceptance['branches']]==[6,0,1]
assert all(b['score']['checkpoints_reached']==2 and b['score']['route_progress']==1 for b in acceptance['branches'])
assert len(set(p for b in acceptance['branches'] for p in b['visited_pages']))==18
assert not (dep/'.env').exists()
files=json.loads((dep/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'))['files']
for f in files:assert hashlib.sha256((dep/f['path']).read_bytes()).hexdigest()==f['sha256']
manifest=json.loads((ROOT/'packs/baoya.prepared.manifest.json').read_text(encoding='utf-8'))
for archive in manifest['archives']:
    path=ROOT/archive['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==archive['sha256']
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
proof=ROOT/'judge/baoya/verification';proof.mkdir(exist_ok=True)
shutil.copyfile(full_dep/'judge/baoya/verification/acceptance.json',proof/'acceptance.json')
for evidence_root in {full_dep,dep}:
    for f in (evidence_root/'judge/baoya/verification').glob('*.png'):shutil.copyfile(f,proof/f.name)
if numbered:shutil.copyfile(numbered_path,proof/'numbered-navigation.json')
deployment.update(status='independent_directory_full_ui_passed',port=8812,story_pages=18,ending_count=2,ui_paths=3,total_puzzle_points=8,required_points_per_route=2,optional_points=6,negative_checks=sum(b['negative_checks'] for b in acceptance['branches']),tested_archive_sha256=manifest['archives'][1]['sha256'],acceptance='judge/baoya/verification/acceptance.json',environment_limit='Installed Python packages and browser on Windows; not a clean OS or cross-platform test.')
p.write_text(json.dumps(deployment,ensure_ascii=False,indent=2),encoding='utf-8')
if full_dep!=dep:
    deployment['status']='full_ui_evidence_compatible_numbered_navigation_update_passed'
    deployment['full_ui_acceptance_root']=str(full_dep)
    deployment['full_ui_tested_archive_sha256']=deployment['previous_full_ui_deployment']['tested_archive_sha256']
    deployment['targeted_runtime_acceptance']='judge/baoya/verification/numbered-navigation.json'
    p.write_text(json.dumps(deployment,ensure_ascii=False,indent=2),encoding='utf-8')
latest=sorted((ROOT/'runs/baoya/B').glob('*/summary.json'))[-1];standard=json.loads(latest.read_text(encoding='utf-8'))
assert standard['ended_reason']=='give_up' and standard['steps']==2
result={'record_id':'base664:0032','task_id':'baoya','title':'宝亚保健有限公司','status':'engineering_ready_content_review_required','ready_for_local_execution':True,'ready_for_formal_scoring':False,'runtime_layer':'L1','account_requirement':'none_fictional_client_side_accounts_only','resource_status':'44_local_files_preserved_and_active_story_references_verified','integration_status':'standard_harness_script_run_passed','flow_status':'18_story_pages_2_endings_3_QTE_paths_ui_verified','judge_status':'8_points_verified_2_critical_6_optional','delivery_status':'resource_and_evaluator_archives_crc_and_hash_verified_independent_deployment_passed','content_status':'password_hint_ambiguity_and_weak_ordering_clues_require_review','evidence':['tasks/baoya/provenance.json','judge/baoya/resource-check.json','judge/baoya/flow.json','judge/baoya/checkpoint-spec.json','judge/baoya/verification/acceptance.json','judge/baoya/deployment.json','packs/baoya.prepared.manifest.json',latest.relative_to(ROOT).as_posix()],'deliverables':['packs/baoya.resources.zip','packs/baoya.prepared.zip','packs/baoya.acceptance.json'],'negative_or_unscored_checks':deployment['negative_checks'],'api_calls_made':0,'limitations':['Original live site revision equality not checked; snapshot origin and changes recorded.','External fonts replaced by existing CSS fallback fonts; original typography not preserved.','Independent deployment uses installed Python dependencies and browser, not a fresh OS.','Ending tiers unranked pending a general rubric.']}
if 'getClientRects' not in (dep/'harness/observe.py').read_text(encoding='utf-8'):
    result['shared_framework_followup']='wrapped_inline_link_numbered_click_fix_pending'
    result['limitations'].append('The packaged shared harness still uses a bounding-box centre for numbered clicks; a wrapped inline link may be omitted or missed. UI acceptance used actual text-rectangle coordinates. Root agent has been notified.')
elif numbered:
    result['shared_framework_followup']='resolved_numbered_wrapped_link_navigation_passed'
    result['evidence'].append('judge/baoya/verification/numbered-navigation.json')
    result['delivery_status']='updated_runtime_bundle_numbered_click_passed_with_unchanged_game_config_judge_and_previous_full_UI_evidence'
(ROOT/'data/preparation/results').mkdir(exist_ok=True)
(ROOT/'data/preparation/results/base664-0032.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'packs/baoya.acceptance.json').write_text(json.dumps({'record_id':result['record_id'],'tested_archive_sha256':deployment['tested_archive_sha256'],'independent_deployment':deployment,'result':result},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'story_pages':18,'points':8,'ui_paths':3,'endings':2,'negative_checks':deployment['negative_checks']}))
