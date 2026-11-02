import json, threading, http.server, socketserver, functools
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path('ARG-packs/verify-416/bodies').resolve()
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
class Server(socketserver.TCPServer): allow_reuse_address=True
with Server(('127.0.0.1',8831),handler) as server:
 threading.Thread(target=server.serve_forever,daemon=True).start()
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True)
  page=browser.new_page(viewport={'width':1366,'height':900}); errors=[]; requests=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:requests.append(r.url))
  page.goto('http://127.0.0.1:8831/434.html',wait_until='domcontentloaded')
  page.locator('#enterBtn').click(); page.wait_for_timeout(700)
  for d in '0000': page.locator(f'[data-digit="{d}"]').click()
  bad=page.locator('#lockError').inner_text(); page.wait_for_timeout(800)
  for d in '0416': page.locator(f'[data-digit="{d}"]').click()
  page.wait_for_timeout(300); unlocked=page.locator('#homeScreen').get_attribute('class')
  page.screenshot(path='judge/haihe-shiguang/verification/phone.png')
  print(json.dumps({'bad_pin':bad,'home_class':unlocked,'errors':errors,'requests':requests},ensure_ascii=False,indent=2))
  browser.close()
 server.shutdown()
