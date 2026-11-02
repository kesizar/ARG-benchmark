from pathlib import Path
import asyncio,json,traceback
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];A=R/'judge/kongguan/acceptance'
async def main():
 d={'actions':[],'errors':[],'missing':[]}
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True);c=await b.new_context(viewport={'width':1920,'height':1080},storage_state=str(A/'route-storage.json'));await c.tracing.start(screenshots=True,snapshots=True,sources=False)
  def watch(p):
   p.on('pageerror',lambda e:d['errors'].append(str(e)));p.on('response',lambda r:d['missing'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  c.on('page',watch);p=await c.new_page();await p.goto('http://127.0.0.1:8821/s1coffin/desktop/index-hanxiu.html')
  try:
   await p.locator('[data-app-id="chat"]').dblclick();ch=p.frame_locator('iframe[src*="apps/chat/chat.html"]');await ch.locator('[data-contact-id="notice"]').click();await ch.locator('.friend-request-agree').click(timeout=65000)
   for i in range(3):await ch.locator('#choiceButtons:not(.hidden) .choice-btn').first.click()
   await ch.locator('.msg-image').click();await p.locator('[data-app-id="chat"]').dblclick()
   for i in range(2):await ch.locator('#choiceButtons:not(.hidden) .choice-btn').first.click()
   await ch.locator('#lockOverlay:not(.hidden)').wait_for(timeout=30000);d['actions'].append('timed mystery contact and all dialogue choices complete; chat locked')
   await p.locator('[data-app-id="mail"]').dblclick();m=p.frame_locator('iframe[src*="mail.html"]');await m.get_by_text('写邮件',exact=True).click();await m.locator('[data-contact-id="xiaozhou"]').click();await m.locator('[data-option-id="xz-out-1-work"]').click();await m.locator('#composeSendBtn').click();await p.wait_for_timeout(7500);await m.locator('#navInbox').click();await m.locator('[data-thread-id="xiaozhou"]').click();await m.locator('[data-reply-option-id="xz-out-2-job"]').click();await m.locator('[id^="replySendBtn-"]:enabled').click();await p.wait_for_timeout(28500);await m.locator('[data-thread-id="xiaozhou"]').click();await m.locator('[data-thread-id="laoliu"]').click();d['actions'].append('both recommendation codes obtained via delayed mail')
   async with c.expect_page() as pp:await p.locator('[data-app-id="search"]').dblclick()
   s=await pp.value;await s.wait_for_load_state();await s.locator('#homeSearchInput').fill('天启科技');await s.locator('#homeSearchInput').press('Enter')
   async with c.expect_page() as pp:await s.get_by_text('天启科技 - 探索能源，启迪未来',exact=True).click()
   app=await pp.value;await app.wait_for_load_state();await app.get_by_role('link',name='立即申请',exact=True).click()
   for sel,val in [('birthYear','1995年'),('birthMonth','7月'),('birthDay','15日'),('graduationYear','2022年'),('education','博士')]:
    await app.locator('#'+sel+' .select-trigger').click();await app.locator('#'+sel+' .select-option').get_by_text(val,exact=True).click()
   for sel,val in [('email','hanxiu@mail.com'),('school','龙华大学'),('major','物理')]:await app.locator('#'+sel).fill(val)
   await app.locator('label:has(#agreeCheck)').click();await app.get_by_text('内部推荐',exact=True).click();await app.locator('#referrerName').fill('刘忙');await app.locator('#referralCode').fill('wrong');await app.locator('#submitBtn').click();assert await p.evaluate('localStorage.getItem("job_apply_done")!=="true"');await app.locator('#referralCode').fill('REF#DAT-2026A05');await app.locator('#submitBtn').click();assert await p.evaluate('localStorage.getItem("job_apply_done")==="true"');d['actions'].append('application wrong referral rejected; correct Liu referral accepted')
   await p.locator('[data-app-id="mail"]').dblclick();await p.wait_for_timeout(7500);await m.locator('#navInbox').click();await m.locator('[data-thread-id="tq-hr"]').click();await c.storage_state(path=str(A/'pre-exam-storage.json'));await m.locator('.exam-button').click();await p.wait_for_url('**/exam.html');d['exam_visible']=await p.locator('body').inner_text()
  except Exception as e:d['failure']=str(e);d['traceback']=traceback.format_exc()
  d['pages']=[{'url':z.url,'text':(await z.locator('body').inner_text())[-2000:]} for z in c.pages];d['storage']=await p.evaluate('JSON.parse(JSON.stringify(localStorage))');await c.storage_state(path=str(A/'exam-route-storage.json'));await c.tracing.stop(path=str(A/'exam-route-trace.zip'));await p.screenshot(path=str(A/'exam-route-last.png'));await b.close()
 (A/'exam-route-report.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:d[k] for k in ['actions','errors','missing','failure'] if k in d},ensure_ascii=True))
if __name__=='__main__':asyncio.run(main())
