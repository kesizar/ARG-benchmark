import asyncio,json,sys,subprocess
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from harness.judge import Judge
class Adapter:
 def __init__(self,p):self.p=p
 async def page_expr(self,e):return await self.p.evaluate(e)
async def main():
 port=int(sys.argv[1]) if len(sys.argv)>1 else 8811
 out=Path(sys.argv[2]) if len(sys.argv)>2 else R/'runs/xishe-guaitan/ui.json'
 game=Path(sys.argv[3]) if len(sys.argv)>3 else R/'tasks/xishe-guaitan/mirror'
 server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(game),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 report={'port':port,'game_root':str(game),'checks':[],'errors':[],'responses':[]};base=f'http://127.0.0.1:{port}/'
 await asyncio.sleep(1)
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1366,'height':900});p=await c.new_page();p.on('pageerror',lambda e:report['errors'].append(str(e)));p.on('response',lambda r:report['responses'].append({'url':r.url,'status':r.status}));p.on('dialog',lambda d:d.accept())
   await c.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
   j=Judge.load(R/'judge/xishe-guaitan/judge.json','xishe-guaitan',R);a=Adapter(p)
   async def check(label):
    await p.wait_for_timeout(200);await j.read(a);j.update(len(report['checks']));report['checks'].append({'label':label,'url':p.url,'score':j.score(),'storage':await p.evaluate('Object.fromEntries(Object.entries(localStorage))')})
   async def click(sel):await p.locator(sel).click();await p.wait_for_timeout(450)
   async def search(s):
    await p.locator('#search-kw').fill(s);await p.locator('#search-kw').press('Enter');await p.wait_for_timeout(250)
   async def committee_back():await click('a[href="village-committee.html"] >> nth=0')
   await p.goto(base+'index.html');await check('fresh')
   await click('#splash');box=await p.locator('#lock-screen').bounding_box();x=box['x']+100;y=box['y']+350
   await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x,y-40,steps=5);await p.mouse.up();await check('short-swipe-negative');assert await p.locator('#lock-screen').is_visible()
   await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x,y-180,steps=10);await p.mouse.up();await p.wait_for_timeout(650)
   for app in ['wechat','photos','settings']:await click('[data-app="'+app+'"]');assert await p.locator('#toast').inner_text()=='此功能暂未开放'
   await click('[data-app="memo"]')
   for n in ['3','2','1']:
    await click('[data-note="'+n+'"]');await p.locator('#note-'+n).evaluate('(e)=>e.scrollTop=e.scrollHeight');await p.screenshot(path=str(out.with_name('note-'+n+'.png')))
    if n!='1':await click('#note-'+n+' .note-nav-back')
   await click('[data-link="website"]');await click('#card-guantai');await click('#toast-close');await click('#review-expand-btn');await click('#yi-sliver');await check('yi-hint');await click('a[href="restaurant.html"]');await check('menu-signatures');await click('a[href="website.html"] >> nth=0');await click('a[href="village-committee.html"]')
   await search('wrong');await check('wrong-search');assert j.score()['checkpoints_reached']==0
   await search('2026/08');await check('date-solved');await click('button:has-text("下载此文件")');await check('victim-export');assert j.score()['checkpoints_reached']==1
   await click('#ep-bar');await click('#btn-report-bad');await check('insufficient-ending');assert not j.score()['ending_reached'] and not j.score()['failure_reached']; await click('button:has-text("返回继续调查")'); await check('insufficient-return'); assert p.url.endswith('search-202608.html'); await click('#ep-bar'); await click('#btn-report-bad')
   # Bad ending retry resets source state. New judge is required for a new episode.
   await click('button:has-text("重新开始")');assert await p.evaluate('localStorage.length')==0
   j=Judge.load(R/'judge/xishe-guaitan/judge.json','xishe-guaitan',R)
   await p.go_back();await p.go_back();await p.reload();await click('button:has-text("下载此文件")');await committee_back()
   for term in ['偏方','矿医院','赵德生']:
    await search(term);await check('search-'+term);await committee_back()
   await click('a[href="chen-family.html"]');await check('password-hint');await committee_back();await click('a[href="chief-transition.html"]');await check('succession-year');await committee_back()
   for i in range(5):await click('#nav-zhengwu')
   await check('hidden-login');await p.locator('#login-user').fill('赵德生');assert await p.locator('#login-user').input_value()=='zhaodesheng'
   await p.locator('#login-pass').fill('wrong');await click('button:has-text("登 录")');await check('wrong-password');assert not await p.evaluate("localStorage.getItem('zds_logged_in')")
   await p.locator('#login-pass').fill('xsc2005');await click('button:has-text("登 录")');await check('admin-solved')
   await click('a[href="zds-note.html"]');await check('personal-notes');await click('a[href="secret-zds.html"]');await click('a[href="medical-doc.html"]');await check('medical-diagnosis');await click('a[href="secret-zds.html"]')
   await click('[onclick*="ev_register_form"]');await click('[onclick="exportMessagesWarning()"]');await click('button:has-text("关闭")');await check('export-cancel-negative');assert 'ev_messages' not in json.loads(await p.evaluate("localStorage.getItem('xsg_evidence')"))
   await click('[onclick="exportMessagesWarning()"]');await click('button:has-text("仍然导出")');await click('#toggle-guestbook');await click('#toggle-guestbook');await click('#toggle-guestbook');await check('guestbook-enabled')
   await click('a[href="village-committee.html"] >> nth=0');await search('马建国');await click('button:has-text("保存举报渠道")');await check('police-export');await committee_back();await click('a[href="website.html"] >> nth=0');await click('#guestbook-link');await click('button:has-text("导出所有留言")');await check('guestbook-export')
   # Latch date checkpoint again in this fresh episode through ordinary search UI.
   await click('a[href="website.html"] >> nth=0');await click('a[href="village-committee.html"]');await search('202608');await check('date-again');await click('#ep-bar');await click('#btn-report-full');await check('good-ending');assert j.score()['good_ending'];await p.screenshot(path=str(out.with_name('good.png')),full_page=True)
   await click('button:has-text("重新开始")');assert await p.evaluate('localStorage.length')==0
   # Deadline test advances the browser clock only; gameplay state still comes from normal UI.
   j=Judge.load(R/'judge/xishe-guaitan/judge.json','xishe-guaitan',R);await p.go_back();await p.go_back();await p.reload();await click('button:has-text("下载此文件")');await check('timeout-start')
   await p.clock.install();await p.clock.fast_forward(48*3600000+2000);await click('#ep-bar');await click('#btn-report-dead');await check('timeout-ending');assert j.score()['failure_reached'] and j.score()['failure_id']=='timeout' and not j.score()['ending_reached'];await p.screenshot(path=str(out.with_name('timeout.png')),full_page=True)
   await click('button:has-text("重新开始")');assert await p.evaluate('localStorage.length')==0
   # Naked static ending URLs must never receive completion.
   j=Judge.load(R/'judge/xishe-guaitan/judge.json','xishe-guaitan',R)
   for name in ['report.html','report-bad.html','report-dead.html']:
    await p.goto(base+name);await check('direct-ending-negative-'+name);assert not j.score()['ending_reached']
   await b.close()
  report['passed']=True
 except Exception as e:report['failure']=repr(e);raise
 finally:
  out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');server.terminate();server.wait(timeout=10)
 print(json.dumps({'passed':report.get('passed'),'checks':len(report['checks']),'errors':report['errors'],'http_errors':[r for r in report['responses'] if r['status']>=400]},ensure_ascii=True))
asyncio.run(main())
