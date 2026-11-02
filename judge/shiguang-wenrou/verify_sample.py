from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));from harness.judge import Judge
J=R/'judge/shiguang-wenrou';cases={}
for end,tier in [('cannot',None),('cherish',None),('corner','good')]:
 j=Judge.load(J/'judge.json','shiguang-wenrou',R);j.values={k:False for k in j.cfg['hooks']};j.update(0);assert not j.score()['ending_reached'];
 for k in ['boot','friendster','tablet','secret','yuqing_capsule']:j.values[k]=True
 j.update(1);assert j.score()['route_progress']==1 and not j.score()['ending_reached'];j.values={k:False for k in j.cfg['hooks']};j.update(2);assert len(j.checkpoints)==2
 j.values[end]=True;j.update(3);score=j.score();assert score['ending_reached']==(end=='corner') and score['ending_tier']==tier and score['good_ending']==(tier=='good');assert end=='corner' or end in score['diagnostic'];cases[end]=score
j=Judge.load(J/'judge.json','shiguang-wenrou',R);j.values={'identity_labels':True};j.update(1);assert not j.checkpoints and not j.score()['ending_reached'];cases['optional_only']=j.score()
(R/'tasks/shiguang-wenrou/audit').mkdir(parents=True,exist_ok=True)
(R/'tasks/shiguang-wenrou/audit/closeout-judge-regression.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2));print('Independent Judge: 2 returnable branches and final ending, 2 candidate locks, latch, negative and optional cases passed')
