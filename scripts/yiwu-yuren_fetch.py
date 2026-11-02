from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
import urllib.request,re,json,hashlib,concurrent.futures
R=Path(__file__).resolve().parents[1];D=R/'judge/yiwu-yuren/source';base='https://liangd1129.github.io/relic1899/';seen=set();queue=['index.html','contact.html','001/window.html','001/youjian.html','001/mailbox.html'];log=[];external=set()
def fetch(rel):
 p=D/rel
 try:
  if p.exists():b=p.read_bytes()
  else:
   with urllib.request.urlopen(base+rel,timeout=25) as r:b=r.read()
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  return rel,b,None
 except Exception as e:return rel,b'',repr(e)
while queue:
 batch=[x for x in queue if x not in seen];queue=[];seen.update(batch)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  for rel,b,err in ex.map(fetch,batch):
   log.append(dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),error=err))
   if err or not rel.endswith(('.html','.js','.css')):continue
   s=b.decode('utf-8',errors='replace')
   links=re.findall(r'''["']([^"'<>\s]+\.(?:html|js|css|jpg|jpeg|png|gif|svg|webp|mp3|wav|ogg|mp4|woff2?|ttf)(?:\?[^"']*)?)["']''',s,re.I)
   links+=re.findall(r'''url\(['"]?([^'"\)]+)''',s)
   links+=re.findall(r'''(?:href|src)\s*=\s*([^\s"'<>]+)''',s)
   for link in links:
    u=urljoin(base+rel,link);q=urlsplit(u)
    if q.netloc!='liangd1129.github.io':external.add(u);continue
    if not q.path.startswith('/relic1899/'):external.add(u);continue
    dest=unquote(q.path[len('/relic1899/'):])
    if dest.startswith(('002/','003/')):continue
    if dest and dest not in seen:queue.append(dest)
(D.parent/'closure.json').write_text(json.dumps(dict(files=log,external=sorted(external),excluded_scope=['002','003']),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(files=len(log),bytes=sum(x['bytes'] for x in log),errors=[x for x in log if x['error']],external=sorted(external)),ensure_ascii=False))
