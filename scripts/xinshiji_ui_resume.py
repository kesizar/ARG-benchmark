import json,threading,http.server,functools,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1] if len(sys.argv)>1 else 'tasks/xinshiji/mirror').resolve();port=int(sys.argv[2])if len(sys.argv)>2 else 8821
out=Path('judge/xinshiji/recovery/resources-ui');out.mkdir(parents=True,exist_ok=True);events=[]
judge=json.loads(Path('judge/xinshiji/judge.json').read_text('utf8'))
def score(page):
 return any(frame.evaluate(judge['hooks']['final']['expr']) for frame in page.frames)
def mark(name,**kw):events.append(dict(name=name,**kw));(out/f'ui-{port}.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf8')
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True,args=['--no-proxy-server']);ctx=b.new_context(viewport={'width':1366,'height':900});p=ctx.new_page();p.on('dialog',lambda d:d.accept())
 try:
  p.goto(f'http://127.0.0.1:{port}/index.html');p.locator('[onclick="showNotice()"]').click();p.locator('[onclick="acknowledgeNotice()"]').click();p.wait_for_timeout(600)
  for i in range(6):p.locator('#monologueScreen').click();p.wait_for_timeout(100)
  p.locator('#flyerScreen').click();p.wait_for_timeout(1000)
  main=p.frame_locator('#gameFrame');main.locator('.fake-search').click();main.locator('#searchInput').fill('向阳花有限公司');main.locator('.search-result-item').click();p.wait_for_timeout(600)
  flower=main.frame_locator('iframe[src="sunflower-lock.html"]')
  for k in ['valDiamond','valStar','valHeart']:flower.locator('#'+k).select_option('0')
  flower.locator('.lock-btn').click();assert '密码错误' in flower.locator('#lockError').inner_text();mark('lock_negative_pass')
  for k,v in [('valDiamond','5'),('valStar','4'),('valHeart','8')]:flower.locator('#'+k).select_option(v)
  flower.locator('.lock-btn').click();p.wait_for_timeout(300)
  for k in ['flower3','flower4','flower5']:flower.locator('#'+k).click(force=True)
  for i in range(3):flower.locator('#sun').click(force=True)
  for i in range(3):flower.locator('#butterfly').click(force=True)
  p.wait_for_timeout(1000)
  dark=main.frame_locator('iframe[src="darkweb.html"]');dark.locator('#figuresSection').wait_for()
  thought=dark.locator('#innerThoughtOverlay')
  if thought.is_visible():thought.click();thought.click()
  dark.locator('[onclick="openFolder()"]').click();dark.locator('[onclick="openPlanKey()"]').click();assert '已加密' in dark.locator('#planLockTip').inner_text();mark('plan_prerequisites_block_pass')
  dark.locator('.folder-close').click();p.wait_for_timeout(350)
  for name,key,area in [('Archive','162039578','archiveArea'),('Chat','645','chatArea'),('Plan','thenewcentury','planFullscreen')]:
   dark.locator('[onclick="openFolder()"]').click();dark.locator(f'[onclick="open{name}Key()"]').click();dark.locator('#keyInput').fill('wrong');dark.locator('.key-submit').click();assert dark.locator('#keyError').inner_text();mark(name+'_negative_pass')
   dark.locator('#keyInput').fill(key);dark.locator('.key-submit').click();p.wait_for_timeout(500);assert dark.locator('#'+area).is_visible();mark(name+'_positive_pass')
   if name!='Plan':dark.locator('.folder-close').click();p.wait_for_timeout(350)
  assert not dark.locator('#endingFinal').is_visible();assert not score(p);mark('independent_judge_before_ending_zero')
  for i in range(4):dark.locator('#planFullscreen').click(position={'x':1000,'y':450});p.wait_for_timeout(100)
  p.wait_for_timeout(600)
  for i in range(18):dark.locator('#endingScreen').click();p.wait_for_timeout(50)
  assert dark.locator('#endingFinal').is_visible();assert score(p);mark('independent_judge_completed_one');mark('normal_ui_short_route_ending',body=dark.locator('#endingFinal').inner_text());p.screenshot(path=str(out/f'ending-{port}.png'))
  dark.locator('#endingScreen').click();p.wait_for_timeout(700)
  # index is now inside the replaced inner frame, original game reset clears both stores.
  vals=p.evaluate('({l:localStorage.length,s:sessionStorage.length})');assert vals=={'l':0,'s':0};assert not score(p);mark('independent_judge_reset_zero');mark('ending_reset_pass',storage=vals)
 except Exception as e:mark('error',error=str(e));p.screenshot(path=str(out/f'error-{port}.png'));raise
 finally:b.close();server.shutdown()
print(json.dumps(events,ensure_ascii=True))
