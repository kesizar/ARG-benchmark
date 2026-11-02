from pathlib import Path
import urllib.request,urllib.parse,json,hashlib,concurrent.futures,time
R=Path(__file__).resolve().parents[1];T=R/'tasks/shiguang-wenrou';M=T/'mirror';A=T/'audit';M.mkdir(exist_ok=True)
d=json.loads((A/'asset-manifest.json').read_text(encoding='utf-8'))
paths=[x['path'] for x in d]+['/service-worker.js','/shared/data/asset-manifest.json','/indexportrait.webp']
def get(p):
 f=M/p.lstrip('/');f.parent.mkdir(parents=True,exist_ok=True)
 try:
  with urllib.request.urlopen('https://cyclyq.netlify.app'+urllib.parse.quote(p,safe='/'),timeout=25) as r:b=r.read();typ=r.headers.get('Content-Type');status=r.status
  f.write_bytes(b);return dict(path=p,status=status,content_type=typ,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 except Exception as e:return dict(path=p,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:out=list(ex.map(get,paths))
(A/'resource-fetch.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(files=len(out),bytes=sum(x.get('bytes',0) for x in out),errors=[x for x in out if 'error'in x]),ensure_ascii=False))
