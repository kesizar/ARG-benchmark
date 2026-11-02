import asyncio,json,subprocess,sys,pathlib
from playwright.async_api import async_playwright
sys.path.insert(0,str(pathlib.Path.cwd()))
from harness.judge import Judge
async def main():
 root=pathlib.Path.cwd();port=8851;s=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/huisheng-weizhi/mirror','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  await asyncio.sleep(1)
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True);c=await b.new_context();page=await c.new_page();j=Judge.load(root/'judge/huisheng-weizhi/judge.json','huisheng-weizhi',root)
   class H: pass
   h=H();h.page=page;h.pending=None;h.page_expr=lambda expr: page.evaluate('() => Boolean('+expr+')')
   async def check(n): await j.read(h);j.update(n);return j.score()
   await page.goto(f'http://127.0.0.1:{port}/index.html');await page.locator('#startButton').click();await page.locator('#enterButton').click();await page.wait_for_url('**/game.html');before=await check(1)
   await page.locator('#systemButton').click();await page.locator('#settingsButton').click();await page.locator('[data-setting="privacy"]').click();await page.locator('#privacyPassword').fill('linmudechengguo');await page.locator('#privacyUnlock').click();unlocked=await check(2)
   await page.locator('.evidence-file').first.click();await page.locator('#choiceConfirm').click();await page.wait_for_url('**/end2.html');await page.wait_for_selector('#endingStage.show',timeout=20000);ending=await check(3)
   assert before['checkpoints_reached']==0 and unlocked['checkpoints_reached']==0 and 'privacy' in unlocked['diagnostic'] and ending['checkpoints_reached']==0 and ending['ending_reached'] and ending['route_id']=='truth'
   out={'fresh':before,'privacy':unlocked,'truth_ending':ending,'pass':True};(root/'judge/huisheng-weizhi/verification/closeout-shortcut.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('shortcut 0/1, truth ending: pass',flush=True);await b.close()
 finally:s.terminate();s.wait()
asyncio.run(main())
