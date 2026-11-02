import json
from playwright.sync_api import sync_playwright
url='https://01a06cd1-d760-7e8d-9f38-5c84d285a9bf.arena.site/'
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page()
 responses=[]
 page.on('response',lambda r: responses.append({'url':r.url,'status':r.status}))
 try:
  page.goto(url,wait_until='domcontentloaded',timeout=30000)
  page.wait_for_timeout(6000)
  page.screenshot(path='runs/huaixia-qiri/origin.png')
  result={'title':page.title(),'url':page.url,'frames':[{'url':f.url,'body':f.locator('body').inner_text(timeout=3000)[:1500]} for f in page.frames], 'responses':responses}
 except Exception as e: result={'error':str(e),'responses':responses}
 open('runs/huaixia-qiri/browser-probe.json','w',encoding='utf8').write(json.dumps(result,ensure_ascii=False,indent=2))
 b.close()
