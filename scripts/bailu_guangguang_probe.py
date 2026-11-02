import asyncio,json,pathlib
from playwright.async_api import async_playwright
async def main():
 d=pathlib.Path('runs/bailu-guangguang');result={'url':'https://01a07250-46a6-78fd-99a4-fed9c9c272e0.arena.site/?embed=true','responses':[],'failures':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='msedge',headless=True)
  context=await browser.new_context(viewport={'width':1440,'height':1000})
  page=await context.new_page()
  page.on('requestfailed',lambda r:result['failures'].append({'url':r.url,'error':r.failure}))
  page.on('response',lambda r:result['responses'].append({'url':r.url,'status':r.status}))
  try:
   r=await page.goto(result['url'],wait_until='domcontentloaded',timeout=45000);result['status']=r.status if r else None
   await page.wait_for_timeout(2500)
  except Exception as e:result['error']=str(e)
  result['title']=await page.title();result['text']=await page.locator('body').inner_text();result['final_url']=page.url
  result['frames']=[]
  for n,f in enumerate(page.frames):
   result['frames'].append({'url':f.url,'text':await f.locator('body').inner_text(timeout=5000)})
   (d/('frame-'+str(n)+'.html')).write_text(await f.content(),encoding='utf8')
  (d/'browser.html').write_text(await page.content(),encoding='utf8');await page.screenshot(path=str(d/'browser.png'),full_page=True)
  (d/'browser.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');await browser.close()
  print(json.dumps(result,ensure_ascii=True)[:2500])
asyncio.run(main())
