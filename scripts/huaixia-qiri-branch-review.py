import json,re
from collections import Counter
from pathlib import Path

root=Path('runs/huaixia-qiri')
nodes=json.loads((root/'graph.json').read_text(encoding='utf-8'))
source=Path('tasks/huaixia-qiri/original.html').read_text(encoding='utf-8')
ids={n['id'] for n in nodes}; edges=[];conditions=Counter();unresolved=[];dynamic=[]
for n in nodes:
 def add(target,kind,cond=None):
  if not target:return
  e={'from':n['id'],'kind':kind,'to':target,'condition':cond}
  edges.append(e)
  if isinstance(cond,dict):conditions.update(cond.keys())
  if isinstance(target,str) and target.startswith('FUNCTION:'):dynamic.append(e)
  elif isinstance(target,str) and target.startswith('$'):dynamic.append(e)
  elif target not in ids:unresolved.append(e)
 for c in n.get('choices',[]):add(c.get('to'),'choice',c.get('cond'))
 for l in (n.get('map') or {}).get('locations',[]):add(l.get('to'),'map_location',l.get('cond'))
 m=n.get('map') or {};add(m.get('endNode'),'map_end')
 for ev in m.get('events',[]):add(ev.get('node'),'random_event')
 for k in ['success','fail','giveUp']:add((n.get('puzzle') or {}).get(k),'puzzle_'+k)
for x in nodes:
 if (x.get('puzzle') or {}).get('answer') == (x.get('puzzle') or {}).get('options') and x.get('puzzle'):
  trivial=x['id']
  break
else:trivial=None
hint_start=source.index('function OV({state:G,puzzle:O')
hint_end=source.index('O.kind==="code"',hint_start)
hint_logic=source[hint_start:hint_end]
review={
 'node_count':len(nodes),'edge_count':len(edges),'static_targets_missing':unresolved,
 'dynamic_target_count':len(dynamic),'dynamic_targets':dynamic,'condition_key_counts':dict(conditions),
 'edges':edges,
 'scoring_findings':[
  {'id':'zodiac_already_sorted','node':trivial,'severity':'blocks_formal_inference_scoring','evidence':'options equal answer in original source; following displayed order suffices','current_package':'shengxiao is critical'},
  {'id':'direct_puzzle_hints','severity':'scoring_policy_unresolved','evidence':'hint reveals exact correct sequences or year; no hint-use exclusion in current judge','mechanism':'Ln(state, missing hintCond) is true, or hintCond met, or puzzleAttempts >= 2','puzzles':[{'id':n['id'],'hint':n['puzzle'].get('hint'),'hintCond':n['puzzle'].get('hintCond')} for n in nodes if 'puzzle' in n]},
  {'id':'design_document','severity':'difficulty_risk','evidence':'title-screen design document reveals premise and selected route conditions; it is accessible to the player'},
  {'id':'branch_shortcut','severity':'verified_route_specificity','evidence':'real evaluator reached flee ending 0/7; no puzzle is a universal route gate'},
 ],
 'scope':'Mechanical edge/condition inventory plus targeted source review; dynamic conditions and all condition combinations have not been exhaustively simulated or UI-tested.'}
(root/'branch-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'hint-implementation.txt').write_text(hint_logic,encoding='utf-8')
print(json.dumps({'nodes':len(nodes),'edges':len(edges),'missing':len(unresolved),'dynamic':len(dynamic),'conditions':dict(conditions),'trivial':trivial},ensure_ascii=True))
