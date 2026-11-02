from pathlib import Path
import sys,json,asyncio,os
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from harness.judge import Judge
from playwright.async_api import async_playwright
class A:
 def __init__(self,p):self.p=p
 async def page_expr(self,x):return await self.p.evaluate(x)
async def main():
 url=sys.argv[1];out=Path(sys.argv[2]);rows=[]
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context();p=await c.new_page();j=Judge.load(R/'judge/guangying-she/judge.json','guangying-she',R)
  async def record(label):
   await p.wait_for_timeout(80);await j.read(A(p));j.update(len(rows)+1);rows.append({'label':label,'state':await p.evaluate('JSON.parse(localStorage.getItem("lhs2008save-v1"))'),'score':j.score()})
  await p.goto(url);await p.get_by_role('button',name='全自助观展').click();await p.get_by_role('button',name='展览墙排序',exact=True).first.click();await record('fresh');assert not j.score()['ending_reached']
  titles=['点灯之前','千灯齐明','人潮初起','灯谜长廊','河灯缓缓','鱼龙灯舞','压轴烟花','熄灯之后']
  async def arrange(names):
   for i,t in enumerate(names):await p.locator('button.tray-card').filter(has_text='《'+t+'》').click();await p.locator('button.wall-slot').nth(i).click()
  await arrange(titles[::-1]);await p.get_by_role('button',name='核对顺序',exact=True).click();await record('wrong');assert not j.score()['ending_reached'] and j.score()['checkpoints_reached']==0
  await p.get_by_role('button',name='全部摘回',exact=True).click();await arrange(titles);await p.get_by_role('button',name='核对顺序',exact=True).click();await record('wall');assert j.score()['checkpoints_reached']==1 and not j.score()['ending_reached']
  await p.get_by_role('button',name='前往开幕之夜',exact=True).click();await record('ending');assert j.score()['ending_reached'];await p.screenshot(path=str(out.with_suffix('.png')),full_page=True)
  await c.close();c=await b.new_context();p=await c.new_page();j=Judge.load(R/'judge/guangying-she/judge.json','guangying-she',R);await p.goto(url+'#/opening');await p.get_by_role('button',name='全自助观展').click();await record('fresh-context-reset');assert not j.score()['ending_reached']
  out.write_text(json.dumps({'passed':True,'evaluator_root':str(R),'url':url,'normal_ui_only':True,'events':rows},ensure_ascii=False,indent=2),encoding='utf8');print('Independent normal UI wrong/correct/ending/reset passed.',flush=True);os._exit(0)
asyncio.run(main())
