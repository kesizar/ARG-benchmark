import asyncio,json,pathlib
from playwright.async_api import async_playwright
async def main():
 d=pathlib.Path('judge/youlun-xia/recovery'); result={'url':'https://www.bilibili.com/video/BV1bJ411J7v6/','requests_failed':[],'responses':[]}
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='msedge',headless=True)
  context=await browser.new_context(viewport={'width':1440,'height':1000})
  page=await context.new_page()
  page.on('requestfailed',lambda r:result['requests_failed'].append({'url':r.url,'error':r.failure}))
  page.on('response',lambda r:result['responses'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  try:
   r=await page.goto(result['url'],wait_until='domcontentloaded',timeout=45000);result['status']=r.status if r else None
   await page.wait_for_timeout(5000)
   intro=page.locator('.interact-dialog-exp .btn')
   if await intro.count(): await intro.click()
   await page.locator('video').first.click()
   await page.wait_for_timeout(55000)
   result['choice_buttons']=await page.get_by_text('A 调查案发现场',exact=True).count();result['videos']=await page.locator('video').evaluate_all('(vs)=>vs.map(v=>({currentTime:v.currentTime,duration:v.duration,paused:v.paused,ended:v.ended}))');result['title']=await page.title();result['body_text']=await page.locator('body').inner_text();result['final_url']=page.url
   await page.screenshot(path=str(d/'browser.png'),full_page=True)
   (d/'browser.html').write_text(await page.content(),encoding='utf-8')
  except Exception as e:
   result['error']=str(e)
   result['body_text']=await page.locator('body').inner_text()
   await page.screenshot(path=str(d/'browser.png'),full_page=True)
  (d/'browser.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({k:v for k,v in result.items() if k not in ['requests_failed','responses','body_text']},ensure_ascii=True));print('text',result.get('body_text','')[:100].encode('ascii','backslashreplace').decode());await browser.close()
asyncio.run(main())
