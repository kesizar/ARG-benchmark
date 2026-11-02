import json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'data/preparation/results/base664-0315.json'
d=json.loads(p.read_text('utf8'))
d.update(status='partial_recovery_full_coverage_pending',integration_status='both_independent_extracted_game_roots_short_route_ui_and_current_judge_pass_at_8823',judge_status='current_final_screen_and_three_session_flags_verified_zero_before_ending_one_at_ending_zero_after_reset',delivery_status='two_partial_archives_crc_and_extraction_hashes_pass_both_game_roots_short_route_ui_pass_fresh_contexts',resume_note='Both extracted game roots passed current judge short-route UI in separate browser contexts sequentially at8823. Port8822 timed out for urllib and Edge. Do not recrawl; use91-file provenance whitelist. No paid API, purchase,personal account or push.')
d['formal_scoring_hold']='Missing decorative asset disposition; manager/member/portrait/survey and clue-image sufficiency unverified. Both archive game roots passed short-route UI but evaluator CLI/config self-contained execution was not tested. Recovery packages remain explicitly partial.'
d['evidence'] += ['judge/xinshiji/recovery/ui-8823.json','judge/xinshiji/recovery/resources-ui/ui-8823.json','judge/xinshiji/recovery/ending-8823.png']
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
p=r/'judge/xinshiji/recovery/resume-audit.json';d=json.loads(p.read_text('utf8'))
d['later_ui_verification']={'port':8823,'sequential_fresh_contexts':True,'evaluation_game_root':'judge/xinshiji/recovery/ui-8823.json','resources_game_root':'judge/xinshiji/recovery/resources-ui/ui-8823.json','coverage':'short route only; all optional branches pending','shared_current_and_extracted_judge_sha256':hashlib.sha256((r/'judge/xinshiji/judge.json').read_bytes()).hexdigest(),'evaluator_cli_tested':False}
for row in d['http_deployments']:row['browser_ui']='Later short-route UI passed at8823 in fresh context; see later_ui_verification.8822 transport failure preserved.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
print('Saved partial result and corrected deployment evidence; no prepared claim.')
