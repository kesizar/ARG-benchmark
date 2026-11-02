from pathlib import Path
import asyncio,json
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1]/'runs/xishe-guaitan'
async def main():
 out=[]
 async with async_playwright() as p:
  b=await p.chromium.launch(channel='msedge',headless=True)
  for name in ['index.html','restaurant.html','evidence-panel.js']:
   page=await b.new_page(); row={'resource':name}
   try:
    r=await page.goto('https://xisheguaitan.pages.dev/'+name,wait_until='domcontentloaded',timeout=30000)
    row.update(status=r.status,url=page.url,text=(await page.locator('body').inner_text())[:3000],headers=await r.all_headers())
    (R/(name+'.response.txt')).write_bytes(await r.body())
    await page.screenshot(path=str(R/(name+'.png')))
   except Exception as e:row['error']=str(e)
   out.append(row);await page.close()
  await b.close()
 (R/'live-browser.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False)[:1500])
asyncio.run(main())
