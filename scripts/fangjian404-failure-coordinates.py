import asyncio,subprocess,sys
from playwright.async_api import async_playwright
async def main():
 s=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/fangjian-404-yingzi/mirror','--port','8832'])
 try:
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True);page=await b.new_page(viewport={'width':1366,'height':900});await page.goto('http://127.0.0.1:8832/');await page.locator('#search-engine button').click();await page.locator('.search-result').first.click()
   for sel in ['#login-user','#login-pass','[onclick="doLogin()"]']:print(sel,await page.locator(sel).bounding_box(),flush=True)
   await b.close()
 finally:s.terminate();s.wait()
asyncio.run(main())
