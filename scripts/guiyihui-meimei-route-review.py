import asyncio,json,hashlib,pathlib,subprocess,sys,traceback,zipfile
from playwright.async_api import async_playwright
root=pathlib.Path('.').resolve();sys.path.insert(0,str(root));from harness.judge import Judge
out=root/'judge/guiyihui-meimei/verification/route-review.json'; log={'routes':{},'errors':[]}
class H:
 pending=None
 def __init__(self,page):self.page=page
 async def page_expr(self,e):return await self.page.evaluate('(e)=>{try{return !!eval(e)}catch(_){return false}}',e)
async def main():
 proc=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/guiyihui-meimei/mirror','--port','8821'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  with zipfile.ZipFile(root/'packs/guiyihui-meimei.resources.zip') as z:
   files=[f for f in (root/'tasks/guiyihui-meimei/mirror').rglob('*') if f.is_file()]
   assert all(z.read(f.relative_to(root/'tasks/guiyihui-meimei/mirror').as_posix())==f.read_bytes() for f in files);log['game_bytes_match_prior_resource_bundle']=True
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True)
   for route in 'ABCD':
    c=await b.new_context(viewport={'width':1366,'height':900});await c.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8821/') else r.abort());page=await c.new_page();page.on('dialog',lambda d:d.accept())
    if route=='A':await page.clock.install()
    for i in range(20):
     try:await page.goto('http://127.0.0.1:8821/index.html');break
     except:await asyncio.sleep(.2)
    j=Judge.load(root/'judge/guiyihui-meimei/judge.json','guiyihui-meimei',root);h=H(page);await j.read(h);j.update(0)
    if route=='A':
     await page.clock.run_for('02:45:01')
    else:
     choices={'B':[1,1,2],'C':[2,2,1],'D':[1,1,1]}[route]
     for level,choice in zip([15,30,45],choices):
      await page.locator('#levels-quick-nav button').nth(level-1).click();await j.read(h);j.update(level);await page.locator(f'#btn-choice-option{choice}').click();await j.read(h);j.update(level+1)
     await page.locator('#levels-quick-nav button').nth(49).click();await j.read(h);j.update(50);await page.locator('#solver-text-input').fill('WAKE_UP_MUYANG');await page.locator('#btn-validate').click()
    await page.wait_for_timeout(100);await j.read(h);j.update(100);score=j.score();title=await page.locator('#ending-title').inner_text();assert await page.locator('#ending-overlay').is_visible();assert f'结局 {route}' in title
    if route=='A':
     log['A_debug']={'score':score,'values':j.values,'prev_values':j.prev_values}; assert not score['ending_reached'] and score['ending_tier'] is None;assert any(e['id']=='failure_timeout_A' for e in score['events'])
    else: assert score['ending_reached'] and score['ending_tier']=='normal' and score['route_id']=='ending_'+route
    await page.locator('button[onclick="restartGame()"]').click();assert await page.locator('#panel-level-indicator').inner_text()=='01/50';start=await page.locator('#global-timer').inner_text()
    if route=='A':await page.clock.run_for(2100)
    else:await page.wait_for_timeout(2100)
    end=await page.locator('#global-timer').inner_text();assert start!=end
    log['routes'][route]={'title':title,'score':score,'restart_level':'01/50','timer_before':start,'timer_after':end,'clock':'Playwright virtual time' if route=='A' else 'real time'};await c.close()
   await b.close()
  log['status']='pass'
 except Exception:log['errors'].append(traceback.format_exc());log['status']='fail'
 finally:proc.terminate();proc.wait();out.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':log['status'],'routes':list(log['routes']),'errors':log['errors']},ensure_ascii=True));
 if log['errors']:sys.exit(1)
asyncio.run(main())
