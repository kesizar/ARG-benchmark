import asyncio,json,pathlib
from playwright.async_api import async_playwright
async def main():
 r={'scope':'anonymous original first normal branch click only','requests':[]};d=pathlib.Path('judge/youlun-xia/recovery')
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='msedge',headless=True);context=await browser.new_context(viewport={'width':1440,'height':1000});page=await context.new_page()
  page.on('request',lambda q:r['requests'].append(q.url) if 'playurl' in q.url or 'edgeinfo' in q.url else None)
  try:
   await page.goto('https://www.bilibili.com/video/BV1bJ411J7v6/',wait_until='domcontentloaded',timeout=45000);await page.wait_for_timeout(5000)
   intro=page.locator('.interact-dialog-exp .btn')
   if await intro.count():await intro.click()
   video=page.locator('video').first;await video.click();await page.wait_for_timeout(55000)
   await page.screenshot(path=str(d/'original-branch-before.png'))
   r['before']=await video.evaluate('(v)=>({src:v.currentSrc,time:v.currentTime,duration:v.duration,ended:v.ended})')
   box=await video.bounding_box();r['box']=box
   await page.mouse.click(box['x']+box['width']*.175,box['y']+box['height']*.90);await page.wait_for_timeout(6000)
   r['after']=await page.locator('video').first.evaluate('(v)=>({src:v.currentSrc,time:v.currentTime,duration:v.duration,ended:v.ended})')
   await page.screenshot(path=str(d/'original-branch-after.png'));r['body']=await page.locator('body').inner_text()
  except Exception as e:r['error']=str(e)
  (d/'original-branch.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in r.items() if k not in ['body','requests']});await browser.close()
asyncio.run(main())
