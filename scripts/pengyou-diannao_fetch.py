from pathlib import Path
import httpx,json,re,hashlib
from urllib.parse import urljoin,urlsplit,unquote
R=Path(__file__).resolve().parents[1];T='pengyou-diannao';D=R/f'judge/{T}/source/live';D.mkdir(parents=True,exist_ok=True);base='https://myfriendpc2005.pages.dev/';queue=['index.html'];seen=set();report=[]
with httpx.Client(timeout=30,follow_redirects=True) as c:
 while queue:
  name=queue.pop(0)
  if name in seen:continue
  seen.add(name);u=urljoin(base,name)
  try:
   x=c.get(u);row={'path':name,'url':u,'final_url':str(x.url),'status':x.status_code,'bytes':len(x.content),'sha256':hashlib.sha256(x.content).hexdigest()}
   if x.status_code==200:
    target=D/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(x.content)
    if name.endswith(('.html','.css','.js')):
     links=re.findall(r'''["']([^"'<>\s]+\.(?:html|js|css|png|jpe?g|gif|webp|svg|mp3|ogg|wav|woff2?)(?:\?[^"'\s]*)?)["']''',x.text,re.I)+re.findall(r'''url\(["']?([^\)"']+)''',x.text)
     for link in links:
      nu=urljoin(u,link);p=urlsplit(nu)
      if p.netloc==urlsplit(base).netloc:
       path=unquote(p.path.lstrip('/'))
       if path not in seen:queue.append(path)
      elif not nu.startswith('data:'):row.setdefault('external',[]).append(nu)
  except Exception as e:row={'path':name,'url':u,'error':str(e)}
  report.append(row);print(row,flush=True)
(R/f'judge/{T}/source/live-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
