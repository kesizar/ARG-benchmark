import json, subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
p=subprocess.Popen([sys.executable,'-m','http.server','8991','--bind','127.0.0.1','--directory','runs/huaixia-qiri/closeout-unpacked/tasks/huaixia-qiri/mirror'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 time.sleep(1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True,args=['--no-proxy-server'])
  ctx=browser.new_context(viewport={'width':1280,'height':1000});page=ctx.new_page()
  page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8991/') else r.abort())
  page.goto('http://127.0.0.1:8991/index.html',wait_until='domcontentloaded',timeout=15000)
  page.get_by_role('button',name='新的七日').wait_for(timeout=10000)
  cont=page.locator('button').filter(has_text='继续')
  out={'storage_count':page.evaluate('localStorage.length'),'continue_disabled':cont.is_disabled()}
  page.get_by_role('button',name='新的七日').click()
  out['ghost_disabled']=page.locator('button').filter(has_text='鬼魂视角').is_disabled()
  out['taoist_disabled']=page.locator('button').filter(has_text='道士视角').is_disabled()
  out['screen']=page.locator('body').inner_text()
  Path('runs/huaixia-qiri/closeout-reset-test.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
  browser.close()
finally:p.terminate()
