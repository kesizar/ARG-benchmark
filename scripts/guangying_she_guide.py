from pathlib import Path
import asyncio,json,sys,subprocess,time,urllib.request,os
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from harness.judge import Judge
O=R/'runs/guangying-she';URL='http://127.0.0.1:8812/index.html';server=subprocess.Popen([sys.executable,'-m','http.server','8812','--bind','0.0.0.0','--directory',str(R/'tasks/guangying-she/mirror')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
class A:
 def __init__(self,p):self.p=p
 async def page_expr(self,e):return await self.p.evaluate(e)
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context();p=await c.new_page();await p.goto(URL);await p.get_by_role('button',name='巡展向导同行').click();await p.get_by_role('button',name='展览墙排序',exact=True).first.click()
  titles=['点灯之前','千灯齐明','人潮初起','灯谜长廊','河灯缓缓','鱼龙灯舞','压轴烟花','熄灯之后']
  for i,t in enumerate(titles[::-1]):await p.locator('button.tray-card').filter(has_text='《'+t+'》').click();await p.locator('button.wall-slot').nth(i).click()
  await p.get_by_role('button',name='核对顺序',exact=True).click();await p.get_by_role('button',name='打开巡展向导提示').click();hints=[]
  for i in range(8):
   await p.wait_for_timeout(80);hints.append(await p.locator('aside').last.inner_text());more=p.get_by_role('button',name='再提示一点',exact=True)
   if not await more.is_visible():break
   await more.click()
  assert any('点灯之前 → 千灯齐明' in t for t in hints)
  await p.get_by_role('button',name='收起提示').click();await p.get_by_role('button',name='全部摘回',exact=True).click()
  for i,t in enumerate(titles):await p.locator('button.tray-card').filter(has_text='《'+t+'》').click();await p.locator('button.wall-slot').nth(i).click()
  await p.get_by_role('button',name='核对顺序',exact=True).click();await p.get_by_role('button',name='前往开幕之夜',exact=True).click();await p.wait_for_timeout(100)
  j=Judge.load(R/'judge/guangying-she/judge.json','guangying-she',R);await j.read(A(p));j.update(1);state=await p.evaluate('JSON.parse(localStorage.getItem("lhs2008save-v1"))');assert state['solved'] and state['hintMode']=='on' and not j.score()['ending_reached'] and j.score()['checkpoints_reached']==0
  result={'passed':True,'hints':hints,'state':state,'score':j.score(),'original_ending_visible':await p.locator('body').inner_text()};(O/'guide-route.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');await p.screenshot(path=str(O/'guide-ending.png'),full_page=True)
  print('Guide full-answer disclosure and original ending verified; benchmark score stays zero.',flush=True)
try:
 for _ in range(10):
  try:urllib.request.urlopen(URL,timeout=2);break
  except Exception:time.sleep(.2)
 asyncio.run(main())
finally:
 server.terminate();server.wait(timeout=5)
