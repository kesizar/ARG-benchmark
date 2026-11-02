from pathlib import Path
import json,re,hashlib,urllib.parse
from playwright.sync_api import sync_playwright
root=Path('tasks/xinshiji/original');root.mkdir(parents=True,exist_ok=True); rows=[];todo=['index.html'];seen=set()
base='https://xinshijileyuan.pages.dev/'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,channel='msedge');ctx=b.new_context();page=ctx.new_page()
 while todo and len(seen)<300:
  name=todo.pop(0)
  if name in seen:continue
  seen.add(name);url=base+('' if name=='index.html' else name)
  try:
   r=page.goto(url,wait_until='domcontentloaded',timeout=30000);data=r.body();ct=r.headers.get('content-type','');status=r.status
   out=root/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
   row={'path':name,'url':url,'status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'type':ct}
   if 'text' in ct or 'javascript' in ct:
    s=data.decode('utf8','replace');refs=set(re.findall(r'''["']([^"'<>\s]+\.(?:html|js|css|jpg|jpeg|png|gif|webp|mp3|wav|mp4|svg)(?:\?[^"'<>\s]*)?)["']''',s,re.I))
    refs.update(re.findall(r'''url\(["']?([^\)"']+)["']?\)''',s))
    local=[];external=[]
    for ref in refs:
     resolved=urllib.parse.urljoin(base+name,ref);u=urllib.parse.urlparse(resolved)
     if u.netloc=='xinshijileyuan.pages.dev':
      nm=urllib.parse.unquote(u.path.lstrip('/'));local.append(nm)
      if nm not in seen:todo.append(nm)
     else:external.append(resolved)
    row.update(refs=local,external=external)
   rows.append(row)
  except Exception as e:rows.append({'path':name,'error':str(e)})
  Path('judge/xinshiji/recovery/browser-crawl.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
 b.close()
print(json.dumps({'files':len(rows),'failures':[r for r in rows if r.get('status',200)!=200 or 'error'in r],'remaining':todo},ensure_ascii=True))
