"""Replay observed hook values through the real Judge state machine, not a browser loop."""
import json, sys
from pathlib import Path
sys.path.insert(0,str(Path('.').resolve()))
from harness.judge import Judge
p=Path('runs/huaixia-qiri')
trace=json.loads((p/'route-hidden.json').read_text(encoding='utf-8'))['states']
def replay(judge_path,states):
 j=Judge(json.loads(Path(judge_path).read_text(encoding='utf-8')),'huaixia-qiri')
 events=[]
 for i,s in enumerate(states):
  j.values=s.get('hooks',{}); events.extend((i,*e) for e in j.update(i))
  if j.ending_reached or j.failure_id: break
 return {'step':i,'score':j.score(),'events':events}
normal=replay('judge/huaixia-qiri/judge.json',trace)
hidden=replay('judge/huaixia-qiri/judge-hidden.json',trace)
yang=replay('judge/huaixia-qiri/judge.json',json.loads((p/'route-death-yang.json').read_text(encoding='utf-8'))['states'])
hp=replay('judge/huaixia-qiri/judge.json',json.loads((p/'route-hp.json').read_text(encoding='utf-8'))['states'])
assert normal['score']['route_id']=='good' and hidden['score']['route_id']=='hidden' and hidden['step']>normal['step']
assert yang['score']['failure_id']=='death_yang' and not yang['score']['ending_reached']
assert hp['score']['failure_id']=='death_hp' and not hp['score']['ending_reached']
out={'normal':normal,'hidden':hidden,'yang':yang,'hp':hp,'scope':'Real Judge.update on recorded browser hook values; not a live harness loop.'}
(p/'judge-replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS normal-first-ending, hidden-after-second-playthrough, yang-failure')
