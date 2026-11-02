from pathlib import Path
import asyncio,json,traceback,sys
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];A=R/'judge/kongguan/acceptance'
async def main():
 d={'actions':[],'errors':[],'missing':[]}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1920,'height':1080},storage_state=str(A/'storage.json'));await c.tracing.start(screenshots=True,snapshots=True,sources=False)
  def watch(p):
   p.on('pageerror',lambda e:d['errors'].append(str(e)));p.on('response',lambda r:d['missing'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  c.on('page',watch);p=await c.new_page();await p.goto('http://127.0.0.1:8821/s1coffin/desktop/index-hanxiu.html');s=None
  async def search(q,title):
   nonlocal s
   if s is None:
    async with c.expect_page() as pp:await p.locator('[data-app-id="search"]').dblclick()
    s=await pp.value;await s.wait_for_load_state()
   inp=s.locator('input:visible').first;await inp.fill(q);await inp.press('Enter')
   async with c.expect_page() as pp:await s.get_by_text(title,exact=True).click()
   page=await pp.value;await page.wait_for_load_state();return page
  try:
   await p.locator('[data-app-id="mail"]').dblclick();m=p.frame_locator('iframe[src*="mail.html"]');await m.locator('[data-thread-id="dingwenqian-mail"]').click();await m.locator('.attachment-link').click();au=p.frame_locator('iframe[src*="apps/audio/audio.html"]');await au.locator('#btnPlay').click();d['actions'].append('farewell audio opened and played')
   ll=await search('三问','三问天启科技：不回答、不表态、不负责。');await ll.locator('#contactCard').click();await ll.locator('#contactModalConfirm').click();d['actions'].append('Liu contact collected')
   xz=await search('求职','求职求助！天启探索者计划值得去吗？');await xz.locator('.user-side[data-user="xiaozhou"]').first.click();await xz.locator('#profileEmailLink').click();await xz.locator('#mailModalConfirm').click();d['actions'].append('Zhou contact collected')
   home=await search('天启科技','天启科技 - 探索能源，启迪未来');await home.get_by_role('link',name='立即申请',exact=True).click();apply=home
   for sel,val in [('birthYear','1995年'),('birthMonth','7月'),('birthDay','15日'),('graduationYear','2022年'),('education','博士')]:
    await apply.locator('#'+sel+' .select-trigger').click();await apply.locator('#'+sel+' .select-option').get_by_text(val,exact=True).click()
   for sel,val in [('email','hanxiu@mail.com'),('school','龙华大学'),('major','物理')]:await apply.locator('#'+sel).fill(val)
   await apply.locator('label:has(#agreeCheck)').click();await apply.locator('#submitBtn').click();assert await p.evaluate('localStorage.getItem("job_apply_attempted")==="true" && localStorage.getItem("job_apply_done")!=="true"');d['actions'].append('application rejects missing referral')
   await c.storage_state(path=str(A/'pre-negotiation-storage.json'))
   if '--fixture' in sys.argv:
    await c.tracing.stop(path=str(A/'negotiation-fixture-trace.zip'));await b.close();print('pre-negotiation fixture saved from normal UI');return
   await p.locator('[data-app-id="mail"]').dblclick();await m.get_by_text('写邮件',exact=True).click();await m.locator('[data-contact-id="laoliu"]').click();await m.locator('[data-option-id="ll-out-1-cautious"]').click();await m.locator('#composeSendBtn').click();await p.wait_for_timeout(7500);await m.locator('#navInbox').click();await m.locator('[data-thread-id="laoliu"]').click();await m.locator('[data-reply-option-id="ll-out-2-truth"]').click();await m.locator('[id^="replySendBtn-"]:enabled').click();await p.wait_for_timeout(7500);await m.locator('[data-thread-id="laoliu"]').click();await m.locator('[data-reply-option-id="ll-out-3-agree"]').click();await m.locator('[id^="replySendBtn-"]:enabled').click();d['actions'].append('Liu truthful negotiation accepted')
   await p.locator('[data-app-id="chat"]').dblclick();ch=p.frame_locator('iframe[src*="apps/chat/chat.html"]');await ch.locator('[data-contact-id="notice"]').click();d['chat_visible']=await ch.locator('body').inner_text()
  except Exception as e:d['failure']=str(e);d['traceback']=traceback.format_exc()
  d['pages']=[{'url':z.url,'text':(await z.locator('body').inner_text())[-2500:]} for z in c.pages];d['storage']=await p.evaluate('JSON.parse(JSON.stringify(localStorage))');await c.storage_state(path=str(A/'route-storage.json'));await c.tracing.stop(path=str(A/'route-trace.zip'));await p.screenshot(path=str(A/'route-last.png'));await b.close()
 (A/'route-report.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:d[k] for k in ['actions','errors','missing','failure'] if k in d},ensure_ascii=True))
if __name__=='__main__':asyncio.run(main())
