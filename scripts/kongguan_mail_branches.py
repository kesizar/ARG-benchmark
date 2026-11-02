from pathlib import Path
import asyncio,json,traceback,sys
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];A=R/'judge/kongguan/acceptance'
CASES=[('laoliu','cautious','truth','agree'),('laoliu','half','truth','disagree'),('laoliu','reveal','half','agree'),('laoliu','cautious','half','disagree'),('laoliu','reveal','inquiry',None)]+[('xiaozhou',a,z,None) for a in ['work','process'] for z in ['job','truth']]
async def run(b,case):
 person,first,second,last=case;d={'case':case,'errors':[]};c=await b.new_context(viewport={'width':1920,'height':1080},storage_state=str(A/'pre-negotiation-storage.json'));p=await c.new_page();p.on('pageerror',lambda e:d['errors'].append(str(e)))
 try:
  await p.goto('http://127.0.0.1:8821/s1coffin/desktop/index-hanxiu.html');await p.locator('[data-app-id="mail"]').dblclick();m=p.frame_locator('iframe[src*="mail.html"]');await m.get_by_text('写邮件',exact=True).click();await m.locator('[data-contact-id="'+person+'"]').click();prefix='ll' if person=='laoliu' else 'xz';await m.locator('[data-option-id="'+prefix+'-out-1-'+first+'"]').click();await m.locator('#composeSendBtn').click();await p.wait_for_timeout(7300);await m.locator('#navInbox').click();await m.locator('[data-thread-id="'+person+'"]').click();await m.locator('[data-reply-option-id="'+prefix+'-out-2-'+second+'"]').click();await m.locator('[id^="replySendBtn-"]:enabled').click();await p.wait_for_timeout(7300);await m.locator('[data-thread-id="'+person+'"]').click()
  if last:
   await m.locator('[data-reply-option-id="ll-out-3-'+last+'"]').click();await m.locator('[id^="replySendBtn-"]:enabled').click();await p.wait_for_timeout(7300);await m.locator('[data-thread-id="laoliu"]').click()
  state=await p.evaluate('(k)=>JSON.parse(localStorage.getItem("mail_state")||"{}").threads[k]',person);ready=await p.evaluate('(k)=>JSON.parse(localStorage.getItem("mail_code_ready")||"{}")[k]===true',person);expected=person=='xiaozhou' or last=='agree';assert ready==expected;d.update(state=state,code_ready=ready,visible=(await m.locator('body').inner_text())[-1800:],passed=True)
 except Exception as e:d['failure']=str(e);d['traceback']=traceback.format_exc()
 await c.close();return d
async def main():
 all=[]
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True)
  if '--retry' in sys.argv:
   all=json.loads((A/'mail-branches-report.json').read_text(encoding='utf8'))
   for i,old in enumerate(all):
    if not old.get('passed'):
     new=await run(b,old['case']);new['prior_attempt']=old;all[i]=new
   (A/'mail-branches-report.json').write_text(json.dumps(all,ensure_ascii=False,indent=2),encoding='utf8');print('retried failures',sum(not x.get('passed') for x in all));await b.close();return
  async def delayed(i,c):await asyncio.sleep(i*3);return await run(b,c)
  for k in range(0,len(CASES),3):
   all.extend(await asyncio.gather(*(delayed(i,c) for i,c in enumerate(CASES[k:k+3]))));(A/'mail-branches-report.json').write_text(json.dumps(all,ensure_ascii=False,indent=2),encoding='utf8');print('completed',len(all),'failed',sum(not x.get('passed') for x in all),flush=True)
  await b.close()
if __name__=='__main__':asyncio.run(main())
