from pathlib import Path
import json
p=Path('data/preparation/results/base664-0446.json')
d=json.loads(p.read_text(encoding='utf-8'))
d['ready_for_local_execution']=True
d['prepared']=False
d['ready_for_formal_scoring']=False
d['runtime_layer']='L1'
d['account_requirement']='none'
d['stages']['resources']='captured_inline_html; multiple_local_routes_with_external_requests_blocked; completeness_unverified'
d['stages']['integration']='draft_config_judge; independent_unpack_smoke_passed; final_acceptance_pending'
d['stages']['content']='167_source_nodes_4_puzzles_4_deductions_10_endings; all_ending_nodes_ui'
d['stages']['judge']='ui_checks_passed; formal_scoring_hold_zodiac_answer_order_and_hint_policy'
d['stages']['ui']='seven_narrative_endings_three_deaths_four_puzzles_four_deductions_fresh_context_reset; branch_exhaustiveness_pending'
d['stages']['delivery']='separate_draft_game_and_evaluation_zips_unpacked_and_smoke_tested; final_acceptance_pending'
d['stages']['review']='296_edges_catalogued; dynamic_contexts_overapproximated; scoring_blockers_identified; condition_combinations_incomplete'
d['evidence']=list(dict.fromkeys(d['evidence']+['runs/huaixia-qiri/local-smoke.json','runs/huaixia-qiri/graph.json','runs/huaixia-qiri/content-audit.json','runs/huaixia-qiri/explore-negative.json','runs/huaixia-qiri/route-good.json','runs/huaixia-qiri/route-vigil.json','runs/huaixia-qiri/route-double.json','runs/huaixia-qiri/route-sacrifice.json','runs/huaixia-qiri/route-flee-negative.json','runs/huaixia-qiri/route-hidden.json','runs/huaixia-qiri/route-death-sanity.json','runs/huaixia-qiri/route-death-yang.json','runs/huaixia-qiri/route-hp.json','runs/huaixia-qiri/reset-test.json','runs/huaixia-qiri/deployment.json','runs/huaixia-qiri/trace-verification.json','runs/huaixia-qiri/judge-replay.json','runs/huaixia-qiri/mask-test.json']))
d['packages']=['packs/huaixia-qiri.game.zip','packs/huaixia-qiri.prepared.zip']
d['evidence']=list(dict.fromkeys(d['evidence']+['runs/huaixia-qiri/resource-audit.json','runs/huaixia-qiri/harness-failure/summary.json','runs/huaixia-qiri/harness-flee/summary.json','runs/huaixia-qiri/deploy-check/evaluation/runs/huaixia-qiri/harness-flee/summary.json','runs/huaixia-qiri/deploy-check/evaluation/runs/huaixia-qiri/harness-failure/summary.json','runs/huaixia-qiri/hidden-loop-final/summary.json','runs/huaixia-qiri/bundle-verification.json','runs/huaixia-qiri/deploy-equivalence.json','runs/huaixia-qiri/harness-versions.json','runs/huaixia-qiri/branch-review.json','runs/huaixia-qiri/context-graph.json','runs/huaixia-qiri/deduction-exhaustive.json','judge/huaixia-qiri/review.md','judge/huaixia-qiri/scoring-review-supplement.md']))
d['limitations']=['Original iframe HTML is preserved unchanged; all ending UI paths ran with external requests blocked, but dynamic dependencies on unvisited branches are not definitively excluded.', 'The zodiac options are already in answer order, but the verified judge counts them as a critical reasoning checkpoint; formal scoring must remain on hold.', 'Game hints reveal answers or calculation methods; the judge does not distinguish hinted solutions. A hint-use policy and renewed validation are required.', 'Four puzzle failures and all four deductions were UI-tested; one wrong clue combination was UI-tested and all 455 possible three-clue sets were checked against source rules, not exhaustively in UI.', 'All seven story endings and three deaths were UI-tested; 296 transitions and dynamic contexts were catalogued, but over-approximate context reachability ignores conditions, resources, stats and RNG.', 'Independent unpacked evaluator loops reached normal ending, terminal failure and hidden ending; the verified package remains unchanged and is not approved for formal scoring.', 'The original design document exposes story and route information; its effect on difficulty remains a scoring risk.', 'The evaluation bundle pins two tested harness modules because shared versions changed after verification; version hashes and diffs are recorded.']
d['next_action']='Decide hint-use and scoring policy, revise the zodiac checkpoint and any hint handling, then rerun affected positive/negative tests, evaluator loops and independent package acceptance.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
