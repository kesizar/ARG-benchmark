from pathlib import Path
import urllib.request,json,hashlib
J=Path(__file__).resolve().parents[1]/'judge/room-404/source';J.mkdir(parents=True,exist_ok=True)
urls=['https://room404.gamestrategists.com/','https://room404.gamestrategists.com/assets/index-DNjinArp.js','https://room404.gamestrategists.com/assets/index-B1xo1_zz.css']
out=[]
for i,u in enumerate(urls):
 try:
  with urllib.request.urlopen(u,timeout=25) as r:b=r.read();st=r.status;ct=r.headers.get('Content-Type')
  f=['live.html','index-DNjinArp.js','index-B1xo1_zz.css'][i];(J/f).write_bytes(b);out.append(dict(url=u,status=st,content_type=ct,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),file=f))
 except Exception as e:out.append(dict(url=u,error=str(e)))
(J/'live-access.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
