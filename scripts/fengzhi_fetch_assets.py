"""Optional recovery, only public original assets. Does not certify completion."""
from pathlib import Path
import json,urllib.request
R=Path(__file__).resolve().parents[1];T='fengzhi-juanyi';d=json.loads((R/f'judge/{T}/resource-check.json').read_text(encoding='utf-8'))
for asset in d['required_assets']:
 p=R/f'tasks/{T}/recovered-assets'/asset
 if p.exists():continue
 try:
  with urllib.request.urlopen('https://www.fengzhi.icu/'+asset,timeout=10) as r:
   if r.status!=200 or not r.headers.get('Content-Type','').startswith('image/'):raise ValueError('Not an image')
   payload=r.read()
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
 except Exception as e:
  print('Recovery stopped:',asset,type(e).__name__,str(e));break
