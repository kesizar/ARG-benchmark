"""Pure independent Judge regression; UI evidence is separate, never a model solve."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from harness.judge import Judge
path=Path(__file__).with_name('judge.json');scores={}
for route in ['end_a','end_b','end_c','end_d','dragged']:
    j=Judge.load(path,'huicheng-317',ROOT);j.values={x:False for x in j.cfg['hooks']};j.update(0);assert not j.score()['ending_reached']
    j.values[route]=True;j.update(1);s=j.score();assert (s['failure_reached'] and s['failure_id']=='dragged' and not s['ending_reached']) if route=='dragged' else (s['route_id']==route and s['ending_tier']=='normal' and not s['good_ending']);scores[route]=s
j=Judge.load(path,'huicheng-317',ROOT);j.values={'archive_lock':True};j.update(1);j.values={'archive_lock':False};j.update(2);assert j.side=={'archive_lock':1} and j.checkpoints=={} and not j.score()['ending_reached'];scores['optional_latch']=j.score()
print(json.dumps(scores,ensure_ascii=False,indent=2))
