"""Aggregate only concrete UI evidence and source-proven unreachable route."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='qian-anon'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def write(p,o):p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 coll=read(f'tasks/{TASK}/collection.json');coverage={};allbranches=0;unscored=0
 for unit in coll['units']:
  key=unit['key'];report=read(f'judge/{TASK}/verification/{key}-acceptance.json');assert report['pass'];bs=report['branches'];ends=sorted({b['score']['route_id'] for b in bs});expected=[e for e in unit['endings'] if e!='draw_unreachable'];assert set(ends)==set(expected),(key,ends,expected);unit.update(status='engineering_ready_content_review_required',verified_endings=ends,evidence=f'judge/{TASK}/verification/{key}-acceptance.json');allbranches+=len(bs);unscored+=sum(b['unscored_checks'] for b in bs)
  data={'rounds':len(bs),'verified_endings':ends,'seeds':[b['seed'] for b in bs]}
  if key=='quiz':
   correct={x['id'] for b in bs for x in b['questions'] if x['correct']};assert len(correct)==22;data.update(pool=22,all_correctly_submitted=sorted(correct),sampling='with replacement; same question may reappear in one ten-round episode; denominator is ten actual player answer slots')
  elif key=='hunt':
   choices={(x['event'],x['choice']) for b in bs for x in b['events']};assert len(choices)==72;data.update(events=24,choices_verified=72,choice_pairs=sorted(choices),planning='Private original-rule deterministic event planning; each event matched live UI before actual selection.')
  elif key=='gal':
   choices={(x['day'],x['choice']) for b in bs for x in b['choices']};assert len(choices)==21;data.update(choices_verified=21,choice_pairs=sorted(choices),reasoning_points=0)
  elif key=='cross':data.update(unreachable='draw_unreachable: source induction proof in review.md, no state injection or fake live claim',dictionary_unique_words=2870)
  elif key=='maze':assert any(b['early_locked_exit_verified'] for b in bs);data.update(early_locked_exit=True,wall_or_boundary_rejection=True,reasoning_points=1,collectibles_are_events=True)
  elif key=='surf':data.update(reasoning_points=0,success_native=[b['native_final'] for b in bs if b['score']['route_id']=='escaped'],limitation='Real-time world continues during model API latency. Curator reads rendered-equivalent positions and issues normal long_press/wait; no model score.')
  else:data.update(paths=[b['label'] for b in bs],fictional_staff_no_real_messages=True)
  coverage[key]=data
 write(f'tasks/{TASK}/collection.json',coll);write(f'judge/{TASK}/flow.json',{'record_id':'base664:0521','version':'v1.4 frozen snapshot; original row v1.2','global_ending':None,'units':coll['units'],'coverage':coverage,'finite_reachable_settlements':18,'source_unreachable_settlements':1,'ui_audited_rounds':allbranches,'unscored_checks':unscored,'private_inventory':'judge/qian-anon/source-inventory.json','review':'judge/qian-anon/review.md'})
 result={'record_id':'base664:0521','task_id':TASK,'title':'千早爱音解谜社v1.2','runtime_layer':'L1','status':'engineering_ready_content_review_required','resource_status':'one_self_contained_html_hash_matches_original_catalogue','snapshot_version':'v1.4, 7 games; original row title v1.2 preserved','account_requirement':'none','integration_status':'seven_derived_units_shared_resource_collection','flow_status':'all18_reachable_outcomes_and_all_finite_question_event_choice_content_ui_verified; source_draw_route_proven_unreachable','judge_status':'native_acceptance_based; no luck points or narrative/reflex puzzles invented','delivery_status':'pending_independent_deployment','model_api_used':False,'collection_manifest':f'tasks/{TASK}/collection.json','review':f'judge/{TASK}/review.md','flow':f'judge/{TASK}/flow.json','source_provenance':f'tasks/{TASK}/provenance.json','coverage':coverage,'resources_bundle':f'packs/{TASK}.resources.zip','evaluation_bundle':f'packs/{TASK}.prepared.zip','limits':['No model ability score. Source answers and private planners/controller are curator-only.','Surf real-time API-latency fairness requires review; source no-pause physics preserved.','Some native riddle keys are ambiguous; no silent content changes.','Random permutations/procedural layouts/continuous worlds not enumerated.','GAL/reflex/simulation units need final ARG/reasoning scope review.','Independent deployment uses preinstalled Windows Python/browser, not clean-install/cross-OS.']}
 write('data/preparation/results/base664-0521.json',result);print('final coverage',allbranches,'rounds,',unscored,'unscored checks')
if __name__=='__main__':main()
