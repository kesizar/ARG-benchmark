import json,zipfile,pathlib,subprocess,sys,time,os,hashlib,urllib.request,asyncio,traceback,uuid
from playwright.async_api import async_playwright
root=pathlib.Path.cwd(); run=root/'runs'/('huisheng-deployment-'+uuid.uuid4().hex[:8]);run.mkdir(parents=True)
res=run/'resource';ev=run/'evaluator';res.mkdir();ev.mkdir()
proof={'directory':str(run),'results':{},'archives':{}}
for name,target in [('resources',res),('prepared',ev)]:
 archive=root/'packs'/('huisheng-weizhi.'+name+'.zip')
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None;z.extractall(target)
 proof['archives'][name]={'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size}
async def go():
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='msedge',headless=True)
  for label,directory,port in [('resource',res,8822),('evaluator',ev/'tasks/huisheng-weizhi/mirror',8824)]:
   server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(directory)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:
    await asyncio.sleep(1);assert server.poll() is None
    c=await browser.new_context();page=await c.new_page();errs=[]
    page.on('response',lambda r:errs.append(r.url) if r.status>=400 else None)
    await page.goto(f'http://127.0.0.1:{port}/index.html');await page.locator('#startButton').click();await page.locator('#enterButton').click();await page.wait_for_url('**/game.html');await page.locator('#filesIcon').click();await page.locator('.folder-card:has-text("文档")').click();await page.locator('.protected-file-row').click();await page.locator('#memoPassword').fill('NULL');await page.locator('#memoUnlock').click();await page.locator('#memoOpenOverlay.show').wait_for(state='visible')
    proof['results'][label]={'entry_to_memo_ui':'pass','errors':errs,'port':port};await c.close()
   finally: server.terminate();server.wait(timeout=5)
  await browser.close()
asyncio.run(go())
cfg=ev/'configs/huisheng-weizhi.json';j=json.loads(cfg.read_text(encoding='utf8'));j['entry_url']=j['entry_url'].replace('8823','8824');j['local_serve']['ready_url']=j['entry_url'];j['local_serve']['port']=8824;j['local_serve']['command'][-1]='8824';j['allow_hosts']=['127.0.0.1:8824'];cfg.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
proc=subprocess.run([sys.executable,'scripts/run_one.py','--config','configs/huisheng-weizhi.json','--policy','script'],cwd=ev,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace',timeout=90)
proof['results']['prepared_cli']={'exit_code':proc.returncode,'output':proc.stdout[-5000:]}
(root/'judge/huisheng-weizhi/deployment.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(proof['results'],ensure_ascii=False))
