import asyncio,subprocess,sys,time,urllib.request,json,pathlib,hashlib
from playwright.async_api import async_playwright
root=pathlib.Path('.').resolve();out=root/'judge/guiyihui-meimei/verification'; results={'ports':{}}
for port in (8821,8822,8823):
 try:
  with urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html',timeout=2) as res: results['ports'][port]={'status':res.status,'sha256':hashlib.sha256(res.read()).hexdigest()}
 except Exception as e: results['ports'][port]={'error':str(e)}
port=8822
if not port: raise RuntimeError('all ports in use')
proc=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/guiyihui-meimei/mirror','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for i in range(30):
  try:
   with urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html',timeout=2) as res: results['owned_server']={'port':port,'status':res.status,'sha256':hashlib.sha256(res.read()).hexdigest()};break
  except Exception:time.sleep(.2)
 async def run():
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True); page=await b.new_page(viewport={'width':1366,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));resp=await page.goto(f'http://127.0.0.1:{port}/index.html',wait_until='load',timeout=10000);await page.wait_for_timeout(1000);results['browser']={'status':resp.status,'url':page.url,'title':await page.title(),'pageerrors':errors,'nav_count':await page.locator('#levels-quick-nav button').count(),'indicator':await page.locator('#panel-level-indicator').inner_text(timeout=3000)};await page.screenshot(path=str(out/'initialization.png'));await b.close()
 asyncio.run(run())
finally:
 proc.terminate();proc.wait(timeout=5);(out/'port-diagnostics.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(results,ensure_ascii=False))
