"""Judge-side sampling; read-only expressions; no game state mutation."""
import sys,json
from pathlib import Path
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r))
from harness.judge import Judge
class Probe:
 def __init__(self):self.j=Judge.load(r/'judge/xinshiji/judge.json','xinshiji',r);self.step=0
 def sample(self,page):
  values={}
  for k,h in self.j.cfg['hooks'].items():
   hits=[]
   for f in page.frames:
    try:hits.append(bool(f.evaluate(h['expr'])))
    except Exception:hits.append(False)
   values[k]=any(hits)
  self.j.values=values;self.step+=1;self.j.update(self.step)
  return {'hooks':values,'score':self.j.score()}
