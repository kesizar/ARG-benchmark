import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from harness.judge import Judge
OUT=ROOT/'judge/new31-unwiped/verification'
class H:
 def __init__(self,p): self.p=p; self.pending=None
 async def page_expr(self,expr): return await self.p.evaluate('() => ('+expr+')')
async def main():
 result={'routes':{},'negative':{},'errors':[]}; jpath=ROOT/'judge/new31-unwiped/judge.json'
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe'); p=await b.new_page(viewport={'width':1280,'height':720}); p.on('pageerror',lambda e:result['errors'].append(str(e))); await p.route('https://**/*',lambda r:r.abort()); await p.goto((ROOT/'tasks/new31-unwiped/mirror/index.html').as_uri()); h=H(p); j=Judge.load(jpath,'new31-unwiped',ROOT)
  async def read(): await p.wait_for_timeout(300); await j.read(h); j.update(1)
  await p.get_by_role('button',name='Start',exact=True).click(); await p.get_by_text('click to skip').click(); await p.locator('#notesbtn').wait_for(timeout=20000); await p.wait_for_timeout(2200); await read(); assert len(j.checkpoints)==0 and not j.ending_reached; assert await p.get_by_role('button',name='Check',exact=True).is_disabled(); result['negative']['empty_board_no_points']=True
  for i in range(1,6):
   await p.locator('.ntab').nth(i-1).click()
   for _ in range(2): await p.get_by_role('button',name='Hint',exact=False).click()
   while True:
    await p.get_by_role('button',name='Show me one answer').click()
    if await p.locator('.nbody .nfb').inner_text()=='Every blank is right. Press Check.': break
   await read(); assert len(j.checkpoints)==i-1
   await p.get_by_role('button',name='Check',exact=True).click(); await read(); assert len(j.checkpoints)==i
  result['negative']['reveals_before_check_no_points']=True; assert any(e['id']=='answer_revealed' for e in j.events)
  await p.locator('#notesbtn').click(); await p.locator('#icons .icon[data-id=mail]').dblclick(); await p.get_by_role('button',name='Connect',exact=True).click(); await p.get_by_text('Connected at 28,800 bps').wait_for(timeout=40000)
  await p.get_by_text('Ruthie PLEASE call me',exact=True).click(); await p.locator('.clue[data-w=carol]').click()
  await p.get_by_text('Deleted Items (1)',exact=True).click(); await p.get_by_text('Request to talk - Hearthlight Fellowship',exact=True).click(); await p.locator('.clue[data-w=soto]').click()
  await p.locator('#notesbtn').click()
  for who,title in [('soto','The Lights Stay On'),('carol','The Long Drive'),('kinney','Wipe It')]:
   if who!='soto':
    await p.get_by_role('button',name='Try the last page again',exact=False).click()
    j=Judge.load(jpath,'new31-unwiped',ROOT); await read()
   await p.locator('.nbody .blank').last.click(); await p.locator('.pop .chip').filter(has_text={'soto':'Lena Soto','carol':'Carol Mayer','kinney':'Dale Kinney'}[who]).click(); await p.get_by_role('button',name='Send to',exact=False).click(); await p.get_by_role('button',name='Send',exact=True).click()
   await p.locator('#ending .endcard .et').wait_for(timeout=70000); assert await p.locator('#ending .endcard .et').inner_text()==title; await read(); assert j.ending_reached and len(j.checkpoints)==5; result['routes'][who]={'title':title,'checkpoints':list(j.checkpoints),'route_endings':j.route_endings}; await p.screenshot(path=str(OUT/f'{who}.png'))
  await p.get_by_role('button',name='Back to the title screen').click(); await p.get_by_role('button',name='New game',exact=True).click(); await p.get_by_role('button',name='Yes, start over').click(); await p.get_by_text('click to skip').click(); await p.locator('#notesbtn').wait_for(timeout=20000); await p.wait_for_timeout(1500); j=Judge.load(jpath,'new31-unwiped',ROOT); await read(); assert len(j.checkpoints)==0 and not j.ending_reached; result['reset']='New game cleared case checkpoints'; result['pass']=not result['errors']; await b.close()
 OUT.mkdir(parents=True,exist_ok=True); (OUT/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(result,ensure_ascii=False))
asyncio.run(main())
