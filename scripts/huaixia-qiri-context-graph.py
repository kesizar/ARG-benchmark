"""Over-approximate map/return contexts; does not evaluate state predicates or AP."""
import collections,json
from pathlib import Path
nodes=json.loads(Path('runs/huaixia-qiri/graph.json').read_text(encoding='utf-8'));g={x['id']:x for x in nodes}
start=('c1_start',None,None);todo=collections.deque([start]);seen={start};transitions=[]
while todo:
 node,map_id,pending=todo.popleft();n=g[node]
 if n.get('map'):map_id=node
 def visit(target,why,next_pending=pending):
  if not target:return
  if target=='$map':target=map_id or 'c1_start'
  elif target=='$return':target=pending or map_id or 'c1_start';next_pending=None
  if isinstance(target,str) and target.startswith('FUNCTION:'):
   for x in ['end_good','end_vigil','end_bride']:visit(x,'conditional_ending',next_pending)
   return
  if target not in g:raise ValueError((node,target))
  state=(target,map_id,next_pending);transitions.append({'from':node,'to':target,'map':map_id,'pending':pending,'via':why})
  if state not in seen:seen.add(state);todo.append(state)
 for c in n.get('choices',[]):visit(c.get('to'),'choice')
 for k in ['success','fail','giveUp']:visit((n.get('puzzle') or {}).get(k),'puzzle_'+k)
 m=n.get('map') or {}
 visit(m.get('endNode'),'map_end')
 for loc in m.get('locations',[]):
  visit(loc.get('to'),'location')
  for ev in m.get('events',[]):visit(ev['node'],'event_on_location',loc.get('to'))
 # tA redirects a non-ending node to one of these on a depleted stat.
 if not n.get('ending'):
  for death in ['death_sanity','death_yang','death_hp']:visit(death,'stat_depletion')
reached={s[0] for s in seen}
out={'states':len(seen),'transitions':len(transitions),'node_count':len(g),'reached_nodes':len(reached),'not_reached':sorted(set(g)-reached),'dynamic_resolutions':[t for t in transitions if t['from'].startswith('ev_') or t['via']=='conditional_ending'],'scope':'Over-approximation: conditions, AP, stats, RNG probabilities, ownership, unlocks and one-shot effects ignored; context reachability is not a playable-route proof.'}
Path('runs/huaixia-qiri/context-graph.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:out[k] for k in ['states','transitions','node_count','reached_nodes','not_reached']},ensure_ascii=True))
