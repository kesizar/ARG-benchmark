import asyncio,subprocess,sys,pathlib,json
from playwright.async_api import async_playwright
sys.path.insert(0,str(pathlib.Path('.').resolve()))
from harness.judge import Judge
root=pathlib.Path('.').resolve()
class H:
 pending=None
 def __init__(self,p):self.p=p
 async def page_expr(self,e):return await self.p.evaluate('(e)=>{try{return !!eval(e)}catch(_){return false}}',e)
async def main():
 proc=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/guiyihui-meimei/mirror','--port','8821'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  async with async_playwright() as q:
   b=await q.chromium.launch(channel='msedge',headless=True);p=await b.new_page();await p.goto('http://127.0.0.1:8821/index.html');j=Judge.load(root/'judge/guiyihui-meimei/judge.json','guiyihui-meimei',root);h=H(p);await j.read(h);j.update(0)
   await p.locator('#levels-quick-nav button').nth(20).click();await p.locator('#solver-text-input').fill('RUNES');await p.locator('#btn-validate').click();await p.wait_for_timeout(50);await j.read(h);j.update(1);assert 'p21' not in j.checkpoints
   for n in [1,4,8,9]:await p.locator(f'#dot-{n}').click()
   await p.locator('#btn-validate').click();await p.wait_for_timeout(50);await j.read(h);j.update(2);assert 'p22' not in j.checkpoints
   (root/'judge/guiyihui-meimei/verification/photo-negative.json').write_text(json.dumps({'p21_guessed_without_photo':False,'p22_pattern_without_photo':False,'status':'pass'},indent=2),encoding='utf-8');await b.close();print('photo precondition negative pass')
 finally:proc.terminate();proc.wait()
asyncio.run(main())
