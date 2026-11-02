import asyncio,subprocess,sys
from playwright.async_api import async_playwright
async def main():
 s=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','runs/dianti-1-failure-migration/evaluation/tasks/dianti-1/mirror','--port','8831'])
 try:
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True);page=await b.new_page(viewport={'width':1366,'height':900});await page.goto('http://127.0.0.1:8831/');
   for sel in ['[data-close="m-phone"]','#o-panelbtn']:
    print(sel,await page.locator(sel).bounding_box(),flush=True);await page.locator(sel).click()
   for sel in ['#pwin','#btn-submitpw']:print(sel,await page.locator(sel).bounding_box(),flush=True)
   await b.close()
 finally:s.terminate();s.wait()
asyncio.run(main())
