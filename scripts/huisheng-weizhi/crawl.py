import urllib.request, urllib.parse, re, pathlib, json, hashlib
base='https://yzxcc616.github.io/echoes-remain/'
root=pathlib.Path('tasks/huisheng-weizhi/game'); root.mkdir(parents=True,exist_ok=True)
queue=['index.html','game.html']; seen={}
while queue:
 p=queue.pop(0).split('?')[0].split('#')[0]
 if p in seen or not p or '..' in p: continue
 try:
  with urllib.request.urlopen(base+p,timeout=20) as r: data=r.read(); status=r.status
  out=root/p; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(data)
  seen[p]={'status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
  if p.endswith(('.html','.css','.js')):
   s=data.decode('utf-8',errors='replace')
   for x in re.findall(r'''["'`](?:\.?/)?([\w\-/\.]+\.(?:html|js|css|png|jpg|jpeg|webp|gif|mp3|wav|svg|woff2?))''',s,re.I):
    resolved=urllib.parse.urljoin(p,x)
    if resolved not in seen: queue.append(resolved)
 except Exception as e: seen[p]={'error':str(e)}
pathlib.Path('data/preparation/results').mkdir(parents=True,exist_ok=True)
pathlib.Path('data/preparation/results/base664-0452-crawl.json').write_text(json.dumps(seen,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(seen,ensure_ascii=False,indent=2))
