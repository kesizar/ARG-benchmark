import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('judge/haian-diaopin/evidence')
url='https://01a0724f-d103-7dde-ae53-8a43941e2038.arena.site/'
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page(viewport={'width':1366,'height':900})
 responses=[]
 page.on('response',lambda r: responses.append({'url':r.url,'status':r.status}) if 'arena.site' in r.url else None)
 try:
  r=page.goto(url,wait_until='domcontentloaded',timeout=45000)
  page.wait_for_timeout(7000)
  d={'status':r.status if r else None,'url':page.url,'title':page.title(),'body':page.locator('body').inner_text()[:4000], 'frames':[{'url':f.url,'body':f.locator('body').inner_text()[:1500] if f.locator('body').count() else ''} for f in page.frames], 'responses':responses[:50]}
  page.screenshot(path=str(out/'edge.png'),full_page=True)
 except Exception as e:d={'error':str(e),'responses':responses[:50]}
 (out/'edge.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(d,ensure_ascii=False))
 b.close()
