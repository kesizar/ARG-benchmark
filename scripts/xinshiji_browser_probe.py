import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('judge/xinshiji/recovery')
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,channel="msedge")
 page=browser.new_page(viewport={'width':1366,'height':900})
 try:
  r=page.goto('https://xinshijileyuan.pages.dev/',wait_until='domcontentloaded',timeout=45000)
  page.wait_for_timeout(5000)
  d={'status':r.status if r else None,'url':page.url,'title':page.title(),'body':page.locator('body').inner_text()[:6000]}
  page.screenshot(path=str(out/'remote-browser.png'),full_page=True)
 except Exception as e:d={'error':str(e)}
 (out/'remote-browser.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(d,ensure_ascii=True))
 browser.close()
