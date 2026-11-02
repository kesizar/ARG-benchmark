import asyncio,threading,http.server,functools
from playwright.async_api import async_playwright
async def go():
 s=http.server.ThreadingHTTPServer(('127.0.0.1',8832),functools.partial(http.server.SimpleHTTPRequestHandler,directory='tasks/binjiang-lanwei/mirror'));threading.Thread(target=s.serve_forever,daemon=True).start()
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True);p=await b.new_page();p.on('pageerror',lambda e:print(e.stack));p.on('dialog',lambda d:d.accept())
  for name in ['desk','raven','chengtou','linshu','qiongdinghui','shenmeng','xingyao']:
   print('PAGE',name);await p.goto(f'http://127.0.0.1:8832/{name}.html');await p.wait_for_timeout(1200)
   if name=='raven':
    for i in range(8):await p.locator('[onclick="loadMoreChat()"]').click()
   if name=='chengtou':await p.locator('#contactSearch').fill('不存在');await p.locator('#contactSearch').fill('');await p.locator('[onclick="downloadMemo()"]').click()
  await b.close()
 s.shutdown()
asyncio.run(go())
