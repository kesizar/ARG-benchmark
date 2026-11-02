from pathlib import Path
import json,sys,importlib.util
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from harness.judge import Judge
J=Path(__file__).parent
spec=importlib.util.spec_from_file_location('audit',J/'audit_judge.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def verify(path):
 data=json.loads(Path(path).read_text(encoding='utf8'));cfg=json.loads((J/'judge.json').read_text(encoding='utf8'));rows=[]
 for n,item in enumerate(data['cases']):
  a=m.evaluate(item['state'],item['text']);expected=dict(login=a['login'],reconstruction=a['reconstruction'],cue_order=a['optional_cue'],ending=a['success']);assert expected==item['hooks'],item['case'];j=Judge(cfg,'dengta-jushe',R);j.values=item['hooks'];j.update(n);score=j.score();assert score['ending_reached']==a['success'];assert score['checkpoints_reached']==sum([a['login'],a['reconstruction']]);rows.append(dict(case=item['case'],score=score))
 # Side evidence and help mode cannot turn a false result into success.
 assert not m.evaluate({'hintMode':True,'backstageUnlocked':True,'reconstructed':True,'seenEnding':True},'—— 幕落 · 灯亮着 ——')['success']
 assert not m.evaluate({'hintMode':False,'seenEnding':True},'—— 幕落 · 灯亮着 ——')['success']
 return rows
if __name__=='__main__':
 out=verify(R/'runs/dengta-jushe/ui-evidence.json');(R/'runs/dengta-jushe/judge-tests.json').write_text(json.dumps({'passed':True,'independent_audit_vs_ui_hooks_and_harness':out,'synthetic_negative_cases':2},ensure_ascii=False,indent=2),encoding='utf8');print('judge tests',len(out)+2)
