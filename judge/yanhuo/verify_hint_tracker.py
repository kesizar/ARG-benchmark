import asyncio,json,sys,subprocess,pathlib,traceback
from playwright.async_api import async_playwright
root=pathlib.Path('.').resolve();sys.path.insert(0,str(root));from harness.judge import Judge
class H:
 pending=None
 def __init__(self,p):self.page=p
 async def page_expr(self,e):return await self.page.evaluate('(e)=>{try{return !!eval(e)}catch(_){return false}}',e)
async def main():
 proc=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/yanhuo/mirror','--port','8997'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);out={'checks':{},'errors':[]}
 try:
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1366,'height':900});page=await c.new_page();page.on('dialog',lambda d:d.accept())
   for _ in range(30):
    try:await page.goto('http://127.0.0.1:8997/index.html');break
    except:await asyncio.sleep(.2)
   h=H(page);j=Judge.load(root/'judge/yanhuo/judge.json','yanhuo',root)
   async def read():await page.wait_for_timeout(30);await j.read(h);j.update(1)
   async def click(s):await page.locator(s).first.click();await read()
   async def wrong(id):
    await click('[data-verify="'+id+'"]');await click('[data-book="xyjl"]');await click('[data-entry="e-bone"]');await click('[data-close="mask-shelf"]')
   async def right(id,book,entry):
    await click('[data-verify="'+id+'"]');await click('[data-book="'+book+'"]');await click('[data-entry="'+entry+'"]');await click('#btn-card-ok')
   await read();await click('#btn-start');await right('i1','xyjl','e-fire');assert 'clean_i1' in j.side;out['checks']['unhinted_scores']=True
   for _ in range(5):await wrong('i3')
   await page.reload();await read();await right('i3','mxsb','e-umb');assert 'clean_i3' not in j.side and 'i3' in j.side;out['checks']['hint_then_reload_then_correct_no_score']=True
   await page.reload();j=Judge.load(root/'judge/yanhuo/judge.json','yanhuo',root);await read();assert 'clean_i1' in j.side and 'clean_i3' not in j.side;out['checks']['post_success_reload_provenance']=True
   await page.evaluate("sessionStorage.removeItem('__yan_audit_v1')");await page.reload();j=Judge.load(root/'judge/yanhuo/judge.json','yanhuo',root);await read();assert 'clean_i1' not in j.side and 'clean_i3' not in j.side;out['checks']['untracked_historical_save_conservative']=True
   await click('#btn-reset');j=Judge.load(root/'judge/yanhuo/judge.json','yanhuo',root);await read();await click('#btn-start');await right('i1','xyjl','e-fire');assert 'clean_i1' in j.side;out['checks']['new_game_reset']=True
   for _ in range(3):await wrong('i3')
   await right('i3','mxsb','e-umb');assert 'clean_i3' not in j.side;out['checks']['three_errors_book_hint_no_score']=True
   await click('#btn-reset');j=Judge.load(root/'judge/yanhuo/judge.json','yanhuo',root);await read();await click('#btn-start')
   for _ in range(8):await wrong('i1')
   await wrong('i3');await right('i3','mxsb','e-umb');assert 'clean_i3' not in j.side;out['checks']['zero_day_first_error_hint_no_score']=True
   await b.close();out['pass']=True
 except Exception:out['errors'].append(traceback.format_exc());out['pass']=False
 finally:proc.terminate();proc.wait();(root/'judge/yanhuo/verification/hint-tracker.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=True))
 if not out['pass']:sys.exit(1)
asyncio.run(main())
