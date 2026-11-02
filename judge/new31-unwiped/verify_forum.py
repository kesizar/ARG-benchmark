import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT)); from harness.judge import Judge
class H:
 def __init__(self,p): self.p=p; self.pending=None
 async def page_expr(self,e): return await self.p.evaluate('()=>('+e+')')
async def main():
 r={}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe'); p=await b.new_page(viewport={'width':1280,'height':720}); await p.route('https://**/*',lambda x:x.abort()); await p.goto((ROOT/'tasks/new31-unwiped/mirror/index.html').as_uri()); h=H(p); j=Judge.load(ROOT/'judge/new31-unwiped/judge.json','new31-unwiped',ROOT)
  async def read(): await p.wait_for_timeout(300); await j.read(h); j.update(1)
  await p.get_by_role('button',name='Start',exact=True).click(); await p.get_by_text('click to skip').click(); await p.locator('#notesbtn').wait_for(timeout=20000); await p.wait_for_timeout(2200)
  for _ in range(2): await p.get_by_role('button',name='Hint',exact=False).click()
  while True:
   await p.get_by_role('button',name='Show me one answer').click()
   if await p.locator('.nbody .nfb').inner_text()=='Every blank is right. Press Check.': break
  await p.locator('.blank[data-k="p1:1"]').click(); await p.locator('.pop .chip').filter(has_text='Ruth Halloran').click(); await p.get_by_role('button',name='Check',exact=True).click(); await p.get_by_text('One answer is wrong.',exact=False).wait_for(); await read(); assert not j.checkpoints; r['wrong_case_page_no_points']=True
  await p.locator('#notesbtn').click(); await p.locator('#icons .icon[data-id=dialer]').dblclick(); await p.locator('.cbtn').click(); await p.get_by_text('Connected at 28,800 bps').wait_for(timeout=40000); await p.locator('#icons .icon[data-id=web]').dblclick(); await p.locator('.addr input').last.fill('http://www.hearthlight.org/board/inner/'); await p.locator('.addr input').last.press('Enter'); await p.locator('.loginbox').wait_for();
  await p.locator('.loginbox input').nth(0).fill('wrong'); await p.locator('.loginbox input').nth(1).fill('wrong'); await p.get_by_role('button',name='Log in',exact=True).click(); await p.get_by_text('Wrong name or password.',exact=False).wait_for(); await read(); assert 'login' not in j.side and not j.checkpoints; r['forum_wrong_no_points']=True
  await p.locator('.loginbox input').nth(0).fill('TomH_Orla'); await p.locator('.loginbox input').nth(1).fill('narrowdoor'); await p.get_by_role('button',name='Log in',exact=True).click(); await p.wait_for_timeout(500); await read(); assert 'login' in j.side and not j.checkpoints; r['forum_correct_optional_only']=True
  (ROOT/'judge/new31-unwiped/verification/forum.json').write_text(json.dumps(r,indent=2)); print(json.dumps(r)); await b.close()
asyncio.run(main())
