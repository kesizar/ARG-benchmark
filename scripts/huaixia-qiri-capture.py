from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True); page=b.new_page()
 def save(r):
  if '?embed=true' in r.url and r.status==200:
   try: open('tasks/huaixia-qiri/original.html','w',encoding='utf8').write(r.text())
   except Exception as e: print(e)
 page.on('response',save)
 page.goto('https://01a06cd1-d760-7e8d-9f38-5c84d285a9bf.arena.site/',wait_until='load',timeout=30000); page.wait_for_timeout(3000); b.close()
