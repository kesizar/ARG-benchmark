import asyncio,json,re,subprocess,sys,time,pathlib,traceback
from playwright.async_api import async_playwright
sys.path.insert(0,str(pathlib.Path('.').resolve()))
from harness.judge import Judge
root=pathlib.Path('.').resolve(); out=root/'judge/guiyihui-meimei/verification';out.mkdir(exist_ok=True)
source=(root/'data/preparation/results/base664-0431-embed.html').read_text(encoding='utf-8')
levels=[{'id':int(i),'type':t,'answer':a} for i,t,a in re.findall(r'id:\s*(\d+),\s*chapter:.*?type:\s*"([^"]+)",\s*answer:\s*"([^"]+)"',source,re.S)]
assert len(levels)==50
class H:
 pending=None
 def __init__(self,page):self.page=page
 async def page_expr(self,expr):return await self.page.evaluate('(expr) => { try { return !!eval(expr) } catch(e) { return false } }',expr)
async def main():
 proc=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/guiyihui-meimei/mirror','--port','8822'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 log={'levels':[],'routes':{},'errors':[],'network_failures':[]};
 try:
  async with async_playwright() as p:
   browser=await p.chromium.launch(channel="msedge",headless=True); context=await browser.new_context(viewport={'width':1366,'height':900},locale='zh-CN')
   await context.route('**/*',lambda route: route.continue_() if route.request.url.startswith('http://127.0.0.1:8822/') else route.abort())
   page=await context.new_page(); page.on('requestfailed',lambda req:log['network_failures'].append({'url':req.url,'error':req.failure}))
   page.on('dialog',lambda d:d.accept())
   for x in range(30):
    try: await page.goto('http://127.0.0.1:8822/index.html',wait_until='load');break
    except Exception: await asyncio.sleep(.2)
   await page.wait_for_selector('#levels-quick-nav button'); judge=Judge.load(root/'judge/guiyihui-meimei/judge.json','guiyihui-meimei',root); h=H(page); await judge.read(h);judge.update(0)
   async def read(step):await judge.read(h);judge.update(step)
   async def number():return int((await page.locator('#panel-level-indicator').inner_text()).split('/')[0])
   async def answer(l,wrong=False):
    t=l['type'];a=l['answer']
    if t=='input': await page.locator('#solver-text-input').fill('WRONG' if wrong else a)
    elif t=='pattern':
     for n in ([2] if wrong else map(int,a.split('-'))): await page.locator(f'#dot-{n}').click()
    elif t=='frequency': await page.locator('#freq-range-slider').fill('100' if wrong else a)
    elif t=='roller':
     if not wrong:
      for i,d in enumerate(map(int,a)):
       up=d if d<=5 else -(10-d)
       for x in range(abs(up)): await page.locator(f'button[onclick="rotateRoller({i}, {1 if up>0 else -1})"]').click()
    await page.locator('#btn-validate').click();await page.wait_for_timeout(20)
   for l in levels:
    n=l['id']; assert await number()==n,('unexpected level',n,await number())
    if n==21:
     await page.locator("button[onclick=\"toggleWindow('win-photos')\"]").click(); await page.locator('div[onclick="inspectPhoto(3)"]').click(); await page.locator('#filter-invert').fill('100'); await page.locator('#filter-bright').fill('30'); await read(40); await page.locator("button[onclick=\"minimizeWindow('win-photos')\"]").click()
    if l['type']=='choice':
     await page.locator('#btn-choice-option1').click(); await read(n*2);log['levels'].append({'level':n,'type':'choice','positive':await number()==n+1});continue
    await answer(l,True);await read(n*2); assert await number()==n,('wrong advanced',n); assert f'p{n}' not in judge.checkpoints,('wrong scored',n)
    if l['type']=='pattern': await page.locator('button[onclick="resetPatternInput()"]').click()
    await answer(l);await read(n*2+1)
    passed=await number()==n+1 if n<50 else await page.locator('#ending-title').inner_text()
    assert passed,('correct failed',n); assert n not in [5,11,12,13,20,21,22,24,25,26,33,35,44,46,48,50] or f'p{n}' in judge.checkpoints,('candidate not scored',n);log['levels'].append({'level':n,'type':l['type'],'negative_no_advance':True,'positive':passed})
   log['routes']['D']=await page.locator('#ending-title').inner_text(); log['score_after_full']=judge.score()
   await page.screenshot(path=str(out/'ending-d.png'),full_page=False)
   await page.locator('button[onclick="restartGame()"]').click(); assert await number()==1
   before=await page.locator('#global-timer').inner_text();await page.wait_for_timeout(2200);after=await page.locator('#global-timer').inner_text();log['restart_timer']={'before':before,'after':after,'advances':before!=after}
   async def jump(n):await page.locator('#levels-quick-nav button').nth(n-1).click();await read(200+n)
   for name,choices in [('B',[1,1,2]),('C',[2,2,1])]:
    for n,c in zip([15,30,45],choices):await jump(n);await page.locator(f'#btn-choice-option{c}').click();await read(300+n)
    await jump(50);await answer(levels[49]);await read(400);title=await page.locator('#ending-title').inner_text();assert f'结局 {name}' in title;log['routes'][name]=title
    await page.locator('button[onclick="restartGame()"]').click()
   # Reset via UI and confirmation, verify baseline.
   await jump(20);await page.locator('button[onclick="confirmReset()"]').click();log['ui_reset_level']=await number();assert log['ui_reset_level']==1
   # Original 9900-second failure is verified separately in terminal-failure.json.
   # Fresh context for skip and hint exclusion.
   c3=await browser.new_context(viewport={'width':1366,'height':900});await c3.route('**/*',lambda route:route.continue_() if route.request.url.startswith('http://127.0.0.1:8822/') else route.abort());p3=await c3.new_page();p3.on('dialog',lambda d:d.accept());await p3.goto('http://127.0.0.1:8822/index.html');j3=Judge.load(root/'judge/guiyihui-meimei/judge.json','guiyihui-meimei',root);h3=H(p3);await j3.read(h3);j3.update(0)
   await p3.locator('#levels-quick-nav button').nth(10).click();await p3.locator('button[onclick="skipLevelEpiphany()"]').click();await p3.wait_for_timeout(100);await j3.read(h3);j3.update(1);log['skip_does_not_score']=not bool(j3.checkpoints);assert log['skip_does_not_score']
   await p3.locator('#levels-quick-nav button').nth(10).click();await p3.locator('button[onclick="toggleHint()"]').click();await p3.locator('#solver-text-input').fill('DEATH');await p3.locator('#btn-validate').click();await p3.wait_for_timeout(100);await j3.read(h3);j3.update(2);log['hint_does_not_score']=not bool(j3.checkpoints);assert log['hint_does_not_score'];await c3.close();await browser.close()
 except Exception as e: log['errors'].append(traceback.format_exc())
 finally:
  proc.terminate();proc.wait();(out/'all-points-acceptance.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'levels_completed':len(log['levels']),'routes':log['routes'],'errors':log['errors'][-1:]},ensure_ascii=True));
 if log['errors']:sys.exit(1)
asyncio.run(main())
