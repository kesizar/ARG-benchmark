from pathlib import Path
import asyncio,json,sys,traceback
from types import SimpleNamespace
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));A=R/'judge/kongguan/acceptance'
from harness.judge import Judge
async def run(b,mode):
 d={'mode':mode,'errors':[]};save='pre-accident-storage.json' if mode=='detective' else 'pre-negotiation-storage.json';c=await b.new_context(viewport={'width':1920,'height':1080},storage_state=str(A/save) if mode=='detective' else None);await c.tracing.start(screenshots=True,snapshots=True,sources=False);p=await c.new_page();p.on('pageerror',lambda e:d['errors'].append(str(e)));j=Judge.load(R/'judge/kongguan/judge.json','kongguan',R)
 async def rec():await j.read(SimpleNamespace(page_expr=p.evaluate));j.update(1);return j.score()
 try:
  if mode=='ordinary':
   await p.goto('http://127.0.0.1:8821/');await p.locator('#btnStart').click();await p.locator('#titleContainer.clickable').click();await p.wait_for_url('**/index-hanxiu.html');await p.locator('[data-app-id="mail"]').dblclick();m=p.frame_locator('iframe[src*="mail.html"]');await m.locator('#mailPassword').fill('20220803');await m.locator('#mailPassword').press('Enter');await m.locator('[data-thread-id="tianqi"]').click();await m.locator('.attachment-link').click();a=p.frame_locator('iframe[src*="dingagreement.html"]');await a.get_by_role('button',name='拒绝签署',exact=True).click();await a.get_by_role('button',name='坚持拒绝',exact=True).click();await p.wait_for_url('**/e1ordinary.html')
  else:
   await p.goto('http://127.0.0.1:8821/s1coffin/desktop/index-hanxiu.html');await p.locator('[data-app-id="chat"]').dblclick();ch=p.frame_locator('iframe[src*="apps/chat/chat.html"]');await ch.locator('[data-contact-id="luojianli"]').click();await ch.locator('#sendBtn').click();assert await p.evaluate('!JSON.parse(localStorage.getItem("endings_unlocked")||"{}").end02');d['empty_send_rejected']=True;await ch.locator('#messageInput').fill('你好');await ch.locator('#sendBtn').click();await p.get_by_role('button',name='确 认',exact=True).click();await p.wait_for_url('**/e2detective.html')
  d['early_score']=await rec();assert not j.route_endings
  for i in range(80):
   await p.wait_for_timeout(600);await rec()
   if mode in j.route_endings:break
  assert mode in j.route_endings,j.score();d['score']=j.score();await p.screenshot(path=str(A/f'failure-{mode}.png'));await p.get_by_role('button',name='时 光 回 溯',exact=True).click();await p.wait_for_url('**/index-hanxiu.html');d['time_rewind_returns_desktop']=True
  fresh=await b.new_context();f=await fresh.new_page();await f.goto('http://127.0.0.1:8821/s1coffin/desktop/index-hanxiu.html');assert await f.evaluate('!localStorage.getItem("endings_unlocked")&&!localStorage.getItem("mail_state")');await fresh.close();d['fresh_context_reset']=True
 except Exception as e:d['failure']=str(e);d['traceback']=traceback.format_exc()
 await c.tracing.stop(path=str(A/f'failure-{mode}-trace.zip'));await c.close();(A/f'failure-{mode}-report.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(d,ensure_ascii=True)[:1700])
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True)
  for m in ['ordinary','detective']:await run(b,m)
  await b.close()
if __name__=='__main__':asyncio.run(main())
