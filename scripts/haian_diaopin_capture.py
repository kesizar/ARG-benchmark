import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('judge/haian-diaopin/evidence')
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page()
 try:
  with page.expect_response(lambda r: '?embed=true' in r.url and r.status==200, timeout=45000) as info:
   page.goto('https://01a0724f-d103-7dde-ae53-8a43941e2038.arena.site/',wait_until='domcontentloaded',timeout=45000)
  response=info.value
  (out/'original-embed.html').write_bytes(response.body())
  print('bytes',len(response.body()))
 finally:b.close()
