import json
from pathlib import Path

nodes=json.loads(Path('runs/huaixia-qiri/graph.json').read_text(encoding='utf-8'))
by_id={n['id']:n for n in nodes}
def refs(target):
 out=[]
 for n in nodes:
  for i,c in enumerate(n.get('choices',[])):
   if c.get('to')==target: out.append({'from':n['id'],'choice':c.get('text'),'cond':c.get('cond'),'effects':c.get('effects')})
  p=n.get('puzzle',{})
  for outcome in ('success','fail','giveUp'):
   if p.get(outcome)==target: out.append({'from':n['id'],'puzzle_outcome':outcome})
  m=n.get('map',{})
  for location in m.get('locations',[]):
   if location.get('to')==target: out.append({'from':n['id'],'location':location})
  if m.get('endNode')==target: out.append({'from':n['id'],'map_end':True})
  for event in m.get('events',[]):
   if event.get('node')==target: out.append({'from':n['id'],'random_event':event})
 return out
report={'node_count':len(nodes),'puzzles':[{'id':n['id'],'puzzle':n['puzzle'],'incoming':refs(n['id'])} for n in nodes if 'puzzle' in n], 'endings':[{'id':n['id'],'ending':n['ending'],'incoming':refs(n['id'])} for n in nodes if 'ending' in n], 'dynamic_ending':{'from':'c7_say_no','good':'bones_taken and hunshu_burned and thread_cut and ritual_correct and not evidence_burned','vigil':'otherwise bones_taken or affinity.axiu >= 5','bride':'otherwise'}, 'death_trigger':'on entering a node, unless already ending, sanity <= 0 then yang <= 0 then hp <= 0', 'deductions':[{'id':'d_axiu','requires':['paper_face','wen_words','zupu_gap']},{'id':'d_minghun','requires':['hunshu_clue','coffin_date','well_thread']},{'id':'d_touqi','requires':['rules','granny_words','ledger']},{'id':'d_self','requires':['no_shadow','news','dogs'],'ng_min':2}], 'status':'Static source audit; actual reachability, visible terminal states and shortcut safety require UI verification.'}
report['node_catalog']=[{'id':n['id'],'chapter':n.get('chapter'),'entry_effects':n.get('onEnter',[]),'choices':n.get('choices',[]),'map':n.get('map'),'puzzle':n.get('puzzle'),'ending':n.get('ending')} for n in nodes]
Path('runs/huaixia-qiri/content-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Audited',len(nodes),'nodes;',len(report['puzzles']),'puzzles;',len(report['endings']),'endings; 4 deductions')
