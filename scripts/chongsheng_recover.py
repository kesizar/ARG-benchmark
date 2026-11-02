"""Read-only original-origin recovery; never substitutes an HTML fallback for assets."""
import hashlib,json,re,urllib.request,urllib.error
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'runs/chongsheng'; M=R/'tasks/chongsheng/recovery'
O.mkdir(parents=True,exist_ok=True); M.mkdir(parents=True,exist_ok=True)
origin='https://be-reborn.pages.dev/'
paths=['','assets/index-MdzLVmuf.js','assets/index-CkOq6uhz.css','game/config.txt','game/scene/start.txt','manifest.json']
rows=[]
for p in paths:
 u=origin+p
 try:
  with urllib.request.urlopen(u,timeout=25) as response: b=response.read(); status=response.status; ct=response.headers.get('Content-Type'); final=response.url
  dest=M/(p or 'index.html'); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(b)
  rows.append(dict(url=u,status=status,content_type=ct,final_url=final,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),saved=str(dest.relative_to(R))))
 except Exception as e: rows.append(dict(url=u,error=repr(e)))
(O/'network-recovery.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=True,indent=2))
