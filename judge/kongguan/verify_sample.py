from pathlib import Path
import argparse,asyncio,json,sys
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from playwright.async_api import async_playwright
from harness.config import load_config
from harness.judge import Judge
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8821);p.add_argument('--output',required=True);a=p.parse_args()
async def main():
 cfg=load_config(R/'configs/kongguan.json');d={'config_valid':True,'port':a.port,'errors':[],'missing':[],'requests':[],'evaluator_root':str(R)}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1920,'height':1080});c.on('page',lambda q:(q.on('pageerror',lambda e:d['errors'].append(str(e))),q.on('request',lambda r:d['requests'].append(r.url)),q.on('response',lambda r:d['missing'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)));page=await c.new_page();await page.clock.install();await page.goto(f'http://127.0.0.1:{a.port}/index.html');j=Judge.load(R/'judge/kongguan/judge.json','kongguan',R)
  async def read():await j.read(SimpleNamespace(page_expr=page.evaluate));j.update(1);return j.score()
  assert not any((await j.read(SimpleNamespace(page_expr=page.evaluate))).values());await page.locator('#btnStart').click();await page.clock.run_for(3500);await page.locator('#titleContainer.clickable').click();await page.clock.run_for(1000);await page.wait_for_url('**/index-hanxiu.html');await page.locator('[data-app-id="mail"]').dblclick();m=page.frame_locator('iframe[src*="mail.html"]');await m.locator('#mailPassword').fill('wrong');await m.locator('#mailPassword').press('Enter');assert not (await j.read(SimpleNamespace(page_expr=page.evaluate)))['mail_anniversary'];await m.locator('#mailPassword').fill('20220803');await m.locator('#mailPassword').press('Enter');assert (await j.read(SimpleNamespace(page_expr=page.evaluate)))['mail_anniversary'];d['mail_positive_negative']=True
  async with c.expect_page() as pp:await page.locator('[data-app-id="search"]').dblclick()
  s=await pp.value;await s.wait_for_load_state();await s.locator('#homeSearchInput').fill('异常');await s.locator('#homeSearchInput').press('Enter')
  async with c.expect_page() as pp:await s.get_by_text('Base64 在线编码解码工具',exact=True).click()
  tool=await pp.value;await tool.wait_for_load_state();await tool.locator('#input').fill('Zm9v');await tool.locator('#decode').click();assert await tool.locator('#output').input_value()=='foo';await tool.locator('#input').fill('foo');await tool.locator('#encode').click();assert await tool.locator('#output').input_value()=='Zm9v';await tool.locator('#input').fill('!');await tool.locator('#decode').click();assert '无法解码' in await tool.locator('#output').input_value();d['local_tool_rfc4648_positive_negative']=True
  await m.locator('[data-thread-id="tianqi"]').click();await m.locator('.attachment-link').click();f=page.frame_locator('iframe[src*="dingagreement.html"]');await f.get_by_role('button',name='拒绝签署',exact=True).click();await f.get_by_role('button',name='坚持拒绝',exact=True).click();await page.wait_for_url('**/e1ordinary.html');await read();assert not j.route_endings;d['hidden_title_negative']=True;await page.clock.run_for(60000);await page.clock.resume();await asyncio.sleep(3);d['score']=await read();d['ending_debug']=await page.evaluate('({title:document.querySelector("#endingTitle").outerHTML,opacity:getComputedStyle(document.querySelector("#endingTitle")).opacity,unlocked:localStorage.getItem("endings_unlocked")})');Path(a.output).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');assert d['score']['route_id']=='ordinary' and d['score']['ending_tier']=='bad';d['formal_ending_positive']=True
  for name in ['judge/kongguan/judge.json','configs/kongguan.json','BUNDLE-MANIFEST.json']:
   res=await page.request.get(f'http://127.0.0.1:{a.port}/'+name);assert res.status==404
  d['evaluator_not_served']=True;assert not d['missing'] and not d['errors'];assert all(u.startswith(f'http://127.0.0.1:{a.port}/') or u.startswith('data:') for u in d['requests']);d['external_requests']=[];await page.screenshot(path=a.output+'.png');await b.close()
 Path(a.output).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('independent probe passed',a.port)
if __name__=='__main__':asyncio.run(main())
