import asyncio,json,subprocess,sys,pathlib,traceback,urllib.request,time,hashlib
from playwright.async_api import async_playwright
sys.path.insert(0,str(pathlib.Path('.').resolve()))
from harness.judge import Judge
root=pathlib.Path('.').resolve();out=root/'judge/guiyihui-meimei/verification'; port=8822
points={5:('input','ASCEND'),12:('input','EYE'),20:('input','SOUL'),24:('input','AETHER'),25:('frequency','432'),26:('input','3-1-4'),35:('input','ECLIPSE'),44:('input','5000000'),46:('input','MUYANG'),48:('input','OVERLOAD'),50:('input','WAKE_UP_MUYANG')}
class H:
 pending=None
 def __init__(self,page):self.page=page
 async def page_expr(self,expr):return await self.page.evaluate('(expr)=>{try{return !!eval(expr)}catch(e){return false}}',expr)
async def main():
 log={'results':[],'errors':[]};proc=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/guiyihui-meimei/mirror','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(30):
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html',timeout=1) as res: assert hashlib.sha256(res.read()).digest()==hashlib.sha256((root/'tasks/guiyihui-meimei/mirror/index.html').read_bytes()).digest(); break
   except Exception: await asyncio.sleep(.2)
  else: raise RuntimeError('owned server unavailable or hash mismatch')
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True)
   for n,(typ,answer) in points.items():
    row={'level':n};log['results'].append(row)
    for mode in ('wrong_correct','hint','skip'):
     c=await b.new_context(viewport={'width':1366,'height':900});page=await c.new_page();page.on('dialog',lambda d:d.accept());await page.goto(f'http://127.0.0.1:{port}/index.html',wait_until='load',timeout=10000); await page.locator('#levels-quick-nav button').nth(n-1).click(); j=Judge.load(root/'judge/guiyihui-meimei/judge.json','guiyihui-meimei',root);h=H(page);await j.read(h);j.update(0)
     async def read():await page.wait_for_timeout(30);await j.read(h);j.update(1)
     async def fill(v):
      if typ=='frequency':await page.locator('#freq-range-slider').fill(v)
      else:await page.locator('#solver-text-input').fill(v)
     if mode=='skip':
      await page.locator('button[onclick="skipLevelEpiphany()"]').click();await read();row['skip_no_score']=f'p{n}' not in j.checkpoints;assert row['skip_no_score']
     else:
      if mode=='hint':await page.locator('button[onclick="toggleHint()"]').click()
      if mode=='wrong_correct':
       await fill('100' if typ=='frequency' else 'WRONG');await page.locator('#btn-validate').click();await read();row['wrong_no_score']=f'p{n}' not in j.checkpoints;row['wrong_stays']=int((await page.locator('#panel-level-indicator').inner_text()).split('/')[0])==n;assert row['wrong_no_score'] and row['wrong_stays']
      await fill(answer);await page.locator('#btn-validate').click();await read();scored=f'p{n}' in j.checkpoints
      if mode=='hint':row['hint_no_score']=not scored;assert not scored
      else:row['correct_scores']=scored;assert scored
     await c.close()
    (out/'new-points-acceptance.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
   await b.close()
 except Exception:log['errors'].append(traceback.format_exc())
 finally:
  proc.terminate();proc.wait(timeout=5);(out/'new-points-acceptance.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(log,ensure_ascii=False));
 if log['errors']:sys.exit(1)
asyncio.run(main())
