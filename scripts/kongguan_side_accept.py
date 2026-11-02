from pathlib import Path
import asyncio,json,sys,traceback
from types import SimpleNamespace
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));A=R/'judge/kongguan/acceptance'
from harness.judge import Judge
async def run(b,variant):
 d={'variant':variant,'errors':[]};c=await b.new_context(viewport={'width':1920,'height':1080},storage_state=str(A/'pre-accident-storage.json'));p=await c.new_page();p.on('pageerror',lambda e:d['errors'].append(str(e)));await c.tracing.start(screenshots=True,snapshots=True,sources=False)
 try:
  await p.clock.install();await p.goto('http://127.0.0.1:8821/s1coffin/desktop/index-hanxiu.html');await p.locator('[data-app-id="chat"]').dblclick();ch=p.frame_locator('iframe[src*="apps/chat/chat.html"]')
  for emp in ['wrong','TQ-OFC-LJL-A05','520']:
   await ch.locator('#addBtn').click();await ch.locator('[data-action="addfriend"]').click();await ch.locator('#addFriendInput').fill(emp);await ch.get_by_role('button',name='发送申请',exact=True).click();await p.clock.run_for(1000)
   pending=await p.evaluate('JSON.parse(localStorage.getItem("tqchat_state")||"{}").friendRequestPending===true');assert pending==(emp=='520')
  d['secret_520_shortcuts_audio_wait']=True;await ch.locator('[data-contact-id="notice"]').click();await ch.locator('.friend-request-agree').click();await p.clock.run_for(5000)
  await ch.locator('#choiceButtons .choice-btn').first.click();await p.clock.run_for(5000);await ch.locator('#choiceButtons .choice-btn').nth(1).click();await p.clock.run_for(5000);await ch.locator('#choiceButtons .choice-btn').nth(variant).click();await p.clock.run_for(5000);await ch.locator('.msg-image').click();await p.locator('[data-app-id="chat"]').dblclick();await ch.locator('#choiceButtons .choice-btn').nth(1).click();await p.clock.run_for(15000);await ch.locator('#choiceButtons .choice-btn').first.click();await p.clock.run_for(20000);assert await p.evaluate('localStorage.getItem("tqchat_locked")==="true"');d['all_alternative_choices_converge_to_chat_lock']=True;d['state']=await p.evaluate('JSON.parse(localStorage.getItem("tqchat_state"))')
 except Exception as e:d['failure']=str(e);d['traceback']=traceback.format_exc()
 await c.tracing.stop(path=str(A/f'mystery-alternative-{variant}-trace.zip'));await c.close();return d
async def main():
 out=[]
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True)
  for i in [1,2]:out.append(await run(b,i))
  reviews=[]
  for key,file in [('end05','e3funeral.html'),('end01','e1ordinary.html')]:
   c=await b.new_context(storage_state=str(A/'ending-good-A1-storage.json'));p=await c.new_page();await p.goto('http://127.0.0.1:8821/s1coffin/ending/'+file+'?review='+key);j=Judge.load(R/'judge/kongguan/judge.json','kongguan',R);await j.read(SimpleNamespace(page_expr=p.evaluate));j.update(1);assert not j.route_endings;reviews.append({'ending':key,'review_does_not_score':True,'score':j.score()});await c.close()
  await b.close()
 (A/'side-branches-report.json').write_text(json.dumps({'mystery_variants':out,'review_negatives':reviews,'timing':'Native UI; virtual clock advances authored timers only.'},ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'mystery':[{'variant':x['variant'],'failure':x.get('failure'),'errors':x['errors']} for x in out],'review_negatives':len(reviews)},ensure_ascii=True))
if __name__=='__main__':asyncio.run(main())
