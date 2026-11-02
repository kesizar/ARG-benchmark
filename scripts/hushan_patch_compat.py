"""Minimal IOL input lock and pending-timer cancellation; preserve all puzzle keys."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];TASK='hushan-xiangcheng'
def main():
 original=(ROOT/f'judge/{TASK}/source/445.original.html').read_bytes();s=original.decode('utf-8')
 changes=[('let IOL = null;','let IOL = null;\nlet iolTimer = null;'),('function iolStart(){','function iolStart(){\n  clearTimeout(iolTimer); iolTimer = null;'),('function iolCheck(){',"function iolCheck(){\n  if(!$('iol-input') || $('iol-input').disabled) return;"),('function iolSkip(){',"function iolSkip(){\n  if(!$('iol-input') || $('iol-input').disabled) return;"),('setTimeout(() => iolNext(), 1500);','iolTimer = setTimeout(() => { iolTimer = null; iolNext(); }, 1500);')]
 for old,new in changes:
  assert old in s;s=s.replace(old,new)
 out=s.encode('utf-8');(ROOT/f'tasks/{TASK}/mirror/index.html').write_bytes(out)
 p=ROOT/f'tasks/{TASK}/provenance.json';data=json.loads(p.read_text(encoding='utf-8'));data['compatibility_changes']=[{'reason':'Original accepted repeated submit on a disabled correct input, double-counting one question and scheduling multiple advances; restart could retain a previous advance timer. Lock resolved inputs and cancel pending timer on restart.','evidence':'judge/hushan-xiangcheng/verification/original-probe.json','changes':[{'from':a,'to':b,'occurrences':original.decode('utf-8').count(a)} for a,b in changes]}];data['runtime_sha256']=hashlib.sha256(out).hexdigest();p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(data['runtime_sha256'])
if __name__=='__main__':main()
