"""Minimal source compatibility: enforce crossword turns and isolate pending quiz timers."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='qian-anon'
def main():
 raw=(ROOT/f'judge/{TASK}/source/521.original.html').read_bytes();s=raw.decode('utf-8');changes=[
 ("CX = { track:'', aPos:0, sPos:0, over:false, turn:1 };", "CX = { track:'', aPos:0, sPos:0, over:false, turn:1, busy:false };"),
 ('function crossJump(){\r\n  if(CX.over) return;', 'function crossJump(){\r\n  if(CX.over || CX.busy) return;'),
 ('function crossStumble(manual){', 'function crossStumble(manual){\n  if(!CX || CX.over || CX.busy) return;'),
 ('function crossFoe(){\r\n  if(CX.over) return;\r\n  setTimeout(() => {\r\n    if(CX.over) return;', 'function crossFoe(){\r\n  if(CX.over) return;\n  CX.busy = true; const session = CX;\n  document.querySelectorAll("#cross-main button,#cross-main input").forEach(x => x.disabled = true);\r\n  setTimeout(() => {\r\n    if(CX !== session || CX.over) return;\n    CX.busy = false;'),
 ('  function step(){\r\n    if(idx >= puzzles.length)', '  const session = QZ;\n  function step(){\n    if(QZ !== session) return;\r\n    if(idx >= puzzles.length)'),
 ('function quizRobotTurn(){', 'function quizRobotTurn(){\n  const session = QZ;'),
 ('setTimeout(quizNext, 900);','setTimeout(() => { if(QZ === session) quizNext(); }, 900);')]
 for old,new in changes:
  assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
 out=s.encode('utf-8');(ROOT/f'tasks/{TASK}/mirror/index.html').write_bytes(out)
 p=ROOT/f'tasks/{TASK}/provenance.json';d=json.loads(p.read_text(encoding='utf-8'));d['runtime_sha256']=hashlib.sha256(out).hexdigest();d['compatibility_changes']=[{'reason':'Crossword original accepts extra player moves while foe timers are queued; lock one player action per turn, expose disabled controls, and isolate old round timers. Quiz delayed phases similarly ignore retired round sessions. No puzzle keys, movement lengths, random probabilities, thresholds or delays changed.','evidence':'judge/qian-anon/verification/original-cross-probe.json','exact_replacements':[{'from':a,'to':b} for a,b in changes]}];p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(d['runtime_sha256'])
if __name__=='__main__':main()
