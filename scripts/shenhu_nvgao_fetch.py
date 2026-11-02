import concurrent.futures,json,urllib.request,urllib.error,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'runs/shenhu-nvgao';M=R/'tasks/shenhu-nvgao/mirror'
names=[p.name for p in M.iterdir() if p.is_file()]+['ending1.html','endingzz.html','itou.jpg','puzzle1.jpg','puzzle2.jpg']
def fetch(n):
 u='https://heiziheizi123.github.io/kobehighschool/'+n
 try:
  with urllib.request.urlopen(u,timeout=30) as x:b=x.read();status=x.status
 except urllib.error.HTTPError as e:b=e.read();status=e.code
 except Exception as e:return {'file':n,'url':u,'error':repr(e)}
 if status==200:(M/n).write_bytes(b)
 return {'file':n,'url':u,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(fetch,names))
(O/'live-fetch.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'total':len(rows),'not200':[r for r in rows if r.get('status')!=200]},ensure_ascii=True))
