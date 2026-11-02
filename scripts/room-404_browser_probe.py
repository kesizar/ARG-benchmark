from pathlib import Path
import asyncio,json
from playwright.async_api import async_playwright
J=Path(__file__).resolve().parents[1]/'judge/room-404/source'
async def main():
 report={'responses':[],'errors':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(channel='msedge',headless=True);c=await b.new_context();page=await c.new_page()
  page.on('response',lambda r:report['responses'].append({'url':r.url,'status':r.status}));page.on('pageerror',lambda e:report['errors'].append(str(e)))
  try:
   r=await page.goto('https://room404.gamestrategists.com/',wait_until='domcontentloaded',timeout=45000);await page.wait_for_timeout(3000);report.update(url=page.url,title=await page.title(),text=(await page.locator('body').inner_text())[:5000]);await page.screenshot(path=str(J/'live-browser.png'),full_page=True);(J/'live-browser.html').write_text(await page.content(),encoding='utf-8')
  except Exception as e:report['error']=str(e)
  await b.close()
 (J/'live-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False)[:7000])
asyncio.run(main())
