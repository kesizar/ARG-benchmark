import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT)); from harness.judge import Judge
class H:
 def __init__(self,p): self.p=p; self.pending=None
 async def page_expr(self,e): return await self.p.evaluate('()=>('+e+')')
async def main():
 r={};
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe'); p=await b.new_page(viewport={'width':1280,'height':720}); await p.route('https://**/*',lambda x:x.abort()); await p.goto((ROOT/'tasks/new31-unwiped/mirror/index.html').as_uri()); h=H(p); j=Judge.load(ROOT/'judge/new31-unwiped/judge.json','new31-unwiped',ROOT)
  async def read(): await p.wait_for_timeout(300); await j.read(h); j.update(1)
  await p.get_by_role('button',name='Start',exact=True).click(); await p.get_by_text('click to skip').click(); await p.locator('#notesbtn').wait_for(timeout=20000); await p.wait_for_timeout(2200); await p.locator('#notesbtn').click()
  await p.locator('#icons .icon[data-id=mydocs]').dblclick(); await p.locator('.fview .icon[data-id=f_jenny]').dblclick(); await p.locator('.fview .icon[data-id=privatezip]').dblclick(); await p.get_by_text('journal.txt (encrypted)').dblclick()
  await p.locator('.modal input[type=password]').fill('wrong'); await p.get_by_role('button',name='OK',exact=True).click(); await p.get_by_text('Incorrect password.',exact=False).wait_for(); await read(); assert 'zip' not in j.side and not j.checkpoints; r['zip_wrong_no_points']=True; await p.get_by_role('button',name='OK',exact=True).click()
  await p.get_by_text('journal.txt (encrypted)').dblclick(); await p.locator('.modal input[type=password]').fill('meatball'); await p.get_by_role('button',name='OK',exact=True).click(); await p.get_by_text('Password accepted.',exact=False).wait_for(); await read(); assert 'zip' in j.side and not j.checkpoints; r['zip_correct_optional_only']=True
  print(json.dumps(r)); (ROOT/'judge/new31-unwiped/verification/zip.json').write_text(json.dumps(r,indent=2)); await b.close()
asyncio.run(main())
