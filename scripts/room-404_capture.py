from pathlib import Path
import asyncio,json,hashlib,urllib.parse,re
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];J=R/'judge/room-404/source';D=J/'current';D.mkdir(parents=True,exist_ok=True)
async def main():
 report=[];jobs=[]
 async with async_playwright() as p:
  b=await p.chromium.launch(channel='msedge',headless=True);c=await b.new_context();page=await c.new_page()
  async def save(r):
   if urllib.parse.urlparse(r.url).hostname!='room404.gamestrategists.com':return
   try:
    body=await r.body();u=urllib.parse.urlparse(r.url);name=u.path.lstrip('/') or 'index.html';f=D/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(body);report.append({'url':r.url,'file':name,'bytes':len(body),'status':r.status,'sha256':hashlib.sha256(body).hexdigest()})
   except Exception as e:report.append({'url':r.url,'error':str(e)})
  page.on('response',lambda r:jobs.append(asyncio.create_task(save(r))))
  await page.goto('https://room404.gamestrategists.com/',wait_until='networkidle',timeout=45000)
  paths=['/images/'+n+'.jpg' for n in ['building','document','radio','server-room','surveillance','terminal','usb-drive']]+['/images/tenants/t%02d.webp'%i for i in range(1,13)]
  for path in paths:
   try: await page.goto('https://room404.gamestrategists.com'+path,wait_until='domcontentloaded',timeout=30000)
   except Exception as e: report.append({'url':path,'error':str(e)})
  # Preserve all declared game images; audio is synthesized WebAudio.
  await asyncio.gather(*jobs);await b.close()
 (J/'current-resources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True))
asyncio.run(main())
