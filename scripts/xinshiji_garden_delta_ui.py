import json,threading,http.server,functools,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from xinshiji_judge_probe import Probe
probe=Probe()
root=Path(sys.argv[1] if len(sys.argv)>1 else 'tasks/xinshiji/mirror').resolve();port=int(sys.argv[2])if len(sys.argv)>2 else 8821
out=Path('judge/xinshiji/recovery/garden-delta');out.mkdir(parents=True,exist_ok=True);events=[]
judge=json.loads(Path('judge/xinshiji/judge.json').read_text('utf8'))
def score(page):
 return any(frame.evaluate(judge['hooks']['final']['expr']) for frame in page.frames)
def mark(name,**kw):
 kw['judge']=probe.sample(p)
 if name=='independent_judge_completed_one':assert probe.j.score()['checkpoints_reached']==5
 if name.endswith('negative_pass'):
  k={'Archive':'archive','Chat':'chat','Plan':'plan','lock':'company-lock'}.get(name.split('_')[0]);assert k is None or not probe.j.values[k]
 events.append(dict(name=name,**kw));(out/f'ui-{port}.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf8')
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);ctx=b.new_context(viewport={'width':1366,'height':900});p=ctx.new_page();p.on('dialog',lambda d:d.accept())
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
  for _ in range(3):flower.locator('#butterfly').click(force=True)
  assert not probe.sample(p)['hooks']['garden'];mark('garden_wrong_all_closed_no_credit')
  for k in ['flower1','flower3','flower4','flower5']:flower.locator('#'+k).click(force=True)
  for _ in range(3):flower.locator('#sun').click(force=True)
  for _ in range(3):flower.locator('#butterfly').click(force=True)
  assert not probe.sample(p)['hooks']['garden'];mark('garden_wrong_pink_open_no_credit')
  flower.locator('#flower1').click(force=True)
  for _ in range(2):flower.locator('#butterfly').click(force=True)
  assert not probe.sample(p)['hooks']['garden'];mark('garden_change_resets_butterfly_and_two_insufficient')
  flower.locator('#butterfly').click(force=True);p.wait_for_timeout(1000)
  assert probe.sample(p)['hooks']['garden'];mark('garden_correct_only_third_after_state_repair')
 except Exception as e:mark('error',error=str(e));p.screenshot(path=str(out/f'error-{port}.png'));raise
 finally:b.close();server.shutdown()
print(json.dumps(events,ensure_ascii=True))
