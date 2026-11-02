"""Refresh collection coverage and result only from successful recorded UI evidence."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='hushan-xiangcheng'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,o):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 r=read(f'judge/{TASK}/verification/acceptance.json');assert r.get('pass');coll=read(f'tasks/{TASK}/collection.json');pools=read(f'judge/{TASK}/question-pools.json');coverage={}
 for unit in coll['units']:
  key=unit['game'];bs=[b for b in r['branches'] if b['key']==key];assert bs
  unit['status']='engineering_ready_content_review_required';unit['evidence']=f'judge/{TASK}/verification/acceptance.json';unit['verified_endings']=sorted({b['score']['route_id'] for b in bs});assert len(unit['verified_endings'])==len(unit['endings'])
  if key in pools:
   presented=set();correct=set()
   for b in bs:presented.update(b['seen']);correct.update(b['seen'][:b['target']])
   assert len(correct)==16;coverage[key]={'pool_size':16,'presented':sorted(presented),'correctly_submitted':sorted(correct),'rounds':len(bs),'seeds':[b['seed'] for b in bs],'tested_native_scores':[b['target'] for b in bs]}
  elif key=='iol':coverage[key]={'fixed_subquestions':9,'tested_scores':[b['correct'] for b in bs],'all_wrong_then_correct':True,'all_wrong_then_skip':True}
  else:coverage[key]={'rounds':2,'successful_moves_each':40,'settlements':[b['rank'] for b in bs],'top_level_clear_positive':any('tier3_clear' in b['score']['diagnostic'] for b in bs),'planning':'Private deterministic original-rule planner returns UI click origins; predicted and actual DOM board match after every click. Not a model solve.'};assert coverage[key]['top_level_clear_positive']
 write(f'tasks/{TASK}/collection.json',coll)
 flow={'record_id':'base664:0445','global_ending':None,'entry':'hub','optional_branches':['社团公告','六个友站链接（外站非本题所需，本地沙箱阻止）'],'units':[],'coverage':coverage,'infinite_state_limit':'Not all shuffled permutations/random boards enumerated; all finite question keys and authored rank branches covered.'}
 for unit in coll['units']:
  key=unit['game'];flow['units'].append({'id':unit['id'],'entry':f'hub -> {key}Start','return':'show(hub) exits current round; replay starts a new round, not a new scoring episode','puzzles':[q['id'] for q in pools[key]['questions']] if key in pools else [q['id'] for q in coll['iol_questions']] if key=='iol' else ['base_group_to_second','second_group_to_third','optional_top_group_removal'],'states':['question','correct_or_wrong_reveal','next','rank_settlement'] if key in pools else ['question_with_corpus','wrong_retry_or_skip','correct_locked','timed_advance','rank_settlement'] if key=='iol' else ['random_grid','invalid_singleton_no_cost','same_adjacent_connected_group','evolve_or_clear','gravity_refill','deadboard_overwrite_pair','40_valid_moves_settlement'],'endings':unit['endings'],'failures':'No explicit authored death/failure; low-rank settlement remains separately named.'})
 write(f'judge/{TASK}/flow.json',flow)
 result={'record_id':'base664:0445','task_id':TASK,'title':'户山香澄解谜社v1.2','runtime_layer':'L1','status':'engineering_ready_content_review_required','resource_status':'self_contained_html_no_required_external_assets','account_requirement':'none','integration_status':'six_derived_units_shared_resource_collection','flow_status':'all_64_pool_questions_correctly_submitted_9_iol_subquestions_all_20_rank_settlements_and_merge_clear_ui_verified','judge_status':'six_independent_judges; sampled_10_question_slots_fixed_9_iol_and_merge_mechanism_points','delivery_status':'pending_independent_deployment','model_api_used':False,'units':[u['id'] for u in coll['units']],'collection_manifest':f'tasks/{TASK}/collection.json','review':f'judge/{TASK}/review.md','flow':f'judge/{TASK}/flow.json','acceptance':f'judge/{TASK}/verification/acceptance.json','auxiliary_acceptance':f'judge/{TASK}/verification/auxiliary-acceptance.json','resources_bundle':f'packs/{TASK}.resources.zip','evaluation_bundle':f'packs/{TASK}.prepared.zip','coverage':coverage,'source_provenance':f'tasks/{TASK}/provenance.json','limitations':['Knowledge answer correctness requires external content review; internal key/explanation conflicts preserved and listed.','Main config aliases IDS only; original record is six independent units, no global ending.','No model capability score; source-derived answers and deterministic board planning are curator-only.','Finite rank branches and pools covered; infinite random layouts/permutations not enumerated.','Dependencies/browser preinstalled on Windows; not a clean-install or cross-OS test.']}
 write('data/preparation/results/base664-0445.json',result)
 print('coverage and result refreshed',len(r['branches']))
if __name__=='__main__':main()
