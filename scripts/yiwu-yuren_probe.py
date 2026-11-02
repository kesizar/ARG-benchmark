from pathlib import Path
import urllib.request,json,hashlib
R=Path(__file__).resolve().parents[1]; out=[]
for rel in ['', 'contact.html', '001/window.html']:
 u='https://liangd1129.github.io/relic1899/'+rel
 try:
  with urllib.request.urlopen(u,timeout=20) as r:b=r.read();status=r.status
  p=R/'judge/yiwu-yuren/source'/('index.html' if not rel else rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  out.append(dict(url=u,status=status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 except Exception as e:out.append(dict(url=u,error=repr(e)))
(R/'tasks/yiwu-yuren/evidence/live-probe.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
