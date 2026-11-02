import json,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
p=subprocess.Popen([sys.executable,'-m','http.server','8812','--bind','127.0.0.1','--directory','tasks/huaixia-qiri/mirror'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 time.sleep(1)
 hooks=json.loads(Path('judge/huaixia-qiri/judge.json').read_text(encoding='utf-8'))['hooks']
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True,args=['--no-proxy-server']);page=b.new_page(viewport={'width':1280,'height':1000})
  page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8812/') else r.abort())
  page.goto('http://127.0.0.1:8812/index.html',wait_until='domcontentloaded',timeout=15000)
  page.get_by_role('button',name='设计文档 · 结局一览').click(timeout=8000)
  data={'body':page.locator('body').inner_text(),'hooks':{k:page.evaluate('() => Boolean('+v['expr']+')') for k,v in hooks.items()}}
  Path('runs/huaixia-qiri/mask-test.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  assert not any(data['hooks'].values())
  b.close()
finally:p.terminate()
