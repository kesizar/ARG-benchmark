from pathlib import Path
import urllib.request,urllib.error,json,hashlib,concurrent.futures
out=Path('judge/guyi-jiuzhi/source');out.mkdir(parents=True,exist_ok=True)
names=['index.html','level1-2.html','level1-3.html','level1-4.html']
def fetch(n):
 u='https://frederickrrrrr-debug.github.io/guyixianzhi/'+n
 try:
  r=urllib.request.urlopen(u,timeout=30);b=r.read();(out/n).write_bytes(b)
  return {'url':u,'status':r.status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 except urllib.error.HTTPError as e:
  b=e.read();(out/(n+'.error.html')).write_bytes(b)
  return {'url':u,'status':e.code,'bytes':len(b)}
 except Exception as e:return {'url':u,'error':str(e)}
rows=list(concurrent.futures.ThreadPoolExecutor(4).map(fetch,names))
(out/'live-check.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rows,ensure_ascii=False))
