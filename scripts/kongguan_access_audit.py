from pathlib import Path
import asyncio, json, hashlib, shutil, urllib.request
from datetime import datetime, timezone
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1]; S=R/'judge/kongguan/source'; S.mkdir(parents=True,exist_ok=True)
URLS=['https://duoweishiti.pages.dev/','https://duoweishiti.pages.dev/s1coffin/desktop/index-hanxiu.html']
async def main():
 d={'record_id':'base664:0029','timestamp_utc':datetime.now(timezone.utc).isoformat(),'http':[],'browser':[]}
 b=(R/'ARG-packs/verify-416/bodies/29.html').read_bytes();(S/'archived-entry.html').write_bytes(b)
 d['snapshot']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'has_html_close':b'</html>' in b,'required_navigation':'s1coffin/desktop/index-hanxiu.html','has_desktop':False}
 for i,u in enumerate(URLS):
  try:
   with urllib.request.urlopen(u,timeout=15) as q:
    body=q.read();d['http'].append({'url':u,'status':q.status,'bytes':len(body)});(S/f'http-{i}.html').write_bytes(body)
  except Exception as e:d['http'].append({'url':u,'error':repr(e)})
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,channel='msedge'); page=await browser.new_page()
  for i,u in enumerate(URLS):
   row={'url':u};d['browser'].append(row)
   try:
    q=await page.goto(u,wait_until='domcontentloaded',timeout=20000);row.update(status=q.status if q else None,title=await page.title(),body=(await page.locator('body').inner_text())[:1200]);(S/f'browser-{i}.html').write_text(await page.content(),encoding='utf8');await page.screenshot(path=str(S/f'browser-{i}.png'))
   except Exception as e:row['error']=str(e)
  await browser.close()
 (S/'access-audit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(d,ensure_ascii=True))
if __name__=='__main__':asyncio.run(main())
