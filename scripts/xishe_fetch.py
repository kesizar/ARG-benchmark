from pathlib import Path
import re,json,urllib.request,urllib.parse,hashlib
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]; dest=root/'tasks/xishe-guaitan/mirror'
queue=['index.html','website.html']; seen=set(); rows=[]
pmanager=sync_playwright().start(); browser=pmanager.chromium.launch(channel='msedge',headless=True); ctx=browser.new_context(); page=ctx.new_page()
while queue:
 p=queue.pop(0)
 if p in seen: continue
 seen.add(p)
 url='https://xisheguaitan.pages.dev/'+urllib.parse.quote(p)
 try:
  local=dest/p
  if local.exists(): b=local.read_bytes(); status='historical'
  else:
   r=page.goto(url,wait_until='domcontentloaded',timeout=30000); b=r.body();status=r.status
   if status!=200: raise RuntimeError(f'HTTP {status}')
   local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(b)
  rows.append(dict(path=p,url=url,status=status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  if local.suffix in ['.html','.js','.css']:
   s=b.decode('utf-8'); refs=re.findall(r'''(?:src|href)\s*=\s*["']([^"'#]+)|url\(\s*['"]?([^)'"\s][^)'"\n]*)|["']([^"'\n]+\.(?:html|js|css|jpg|png|mp3|wav|webp|jpeg))["']''',s)
   for group in refs:
    ref=next(x for x in group if x).strip()
    u=urllib.parse.urljoin(url,ref)
    if urllib.parse.urlparse(u).netloc=='xisheguaitan.pages.dev': queue.append(urllib.parse.unquote(urllib.parse.urlparse(u).path).lstrip('/'))
 except Exception as e: rows.append(dict(path=p,url=url,error=str(e)))
 (root/'runs/xishe-guaitan/resource-fetch.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
browser.close();pmanager.stop()
print(json.dumps({'files':len(rows),'errors':[r for r in rows if 'error'in r]},ensure_ascii=True))
