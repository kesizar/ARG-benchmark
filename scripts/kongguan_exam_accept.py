from pathlib import Path
import asyncio,json,traceback,sys
from types import SimpleNamespace
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));A=R/'judge/kongguan/acceptance'
from harness.judge import Judge
FAST='--fast' in sys.argv
V={'q1':'新闻媒体','q2':'科研项目','q3':'专业功底','q4':'能源研究','q5':'陌生人','q6':'陌生人','q7':'获取情报','q8':'目标','q9':'多维实体','q10':'φ能量','q11':'额外维度中','q12':'相信','q13':'我的妻子','q14':'爱','q15':'确定','q16':'onlytruth','q17':'丁文倩的信条','q18':'真相','q19':'happybirthday','q20':'生日快乐','q21':'多维实体','q22':'是的','q23':'因为爱','q24':'爱','q26':'相信','q27':['健康','财富','自由','尊严'],'q28':'韩休','q29':'真相','q30':'多维实体的秘密','q31':'生命'}
async def run(browser,mode):
 d={'mode':mode,'actions':[],'errors':[],'missing':[]};c=await browser.new_context(viewport={'width':1920,'height':1080},storage_state=str(A/'pre-exam-storage.json'));await c.tracing.start(screenshots=True,snapshots=True,sources=False);p=await c.new_page();p.on('pageerror',lambda e:d['errors'].append(str(e)));p.on('response',lambda r:d['missing'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);j=Judge.load(R/'judge/kongguan/judge.json','kongguan',R)
 async def rec(label):
  await j.read(SimpleNamespace(page_expr=p.evaluate));j.update(len(d['actions']));d['actions'].append({'label':label,'values':dict(j.values),'score':j.score()});(A/f'exam-{mode}-report.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
 async def delay(ms):
  if FAST:await p.clock.run_for(ms)
  else:await p.wait_for_timeout(ms)
 try:
  if FAST:await p.clock.install()
  await p.goto('http://127.0.0.1:8821/s1coffin/desktop/index-hanxiu.html');await p.locator('[data-app-id="mail"]').dblclick();m=p.frame_locator('iframe[src*="mail.html"]');await m.locator('[data-thread-id="tq-hr"]').click();await m.locator('.exam-button').click();await p.wait_for_url('**/exam.html');await rec('exam entered from invitation');await p.locator('#btnStart').click()
  if FAST:await delay(30000)
  for ix,(qid,value) in enumerate(V.items()):
   await p.wait_for_function('(i)=>currentIndex===i&&!isLocked',arg=ix,timeout=40000)
   await p.locator('.opts-container.show').wait_for(timeout=40000);qtype=await p.evaluate('QUESTIONS[currentIndex].type')
   if mode=='bad' and qid in ['q5','q6','q7','q8','q9','q10','q11','q16','q18','q19','q27']:
    value={'q5':'朋友','q6':'亲属','q7':'出于善意','q8':'六边形','q9':'wrong','q10':'水中','q11':'意识中','q16':'wrong','q18':'wrong','q19':'wrong','q27':['健康']}[qid]
   if mode=='quit' and qid=='q31':value='退出测试'
   if qtype=='text':await p.locator('#textAnswer').fill(value);await p.locator('#btnNext').click()
   elif qid=='q21':
    if mode=='bad':await p.locator('.option[data-value="罗建立"]').click();await delay(1200);await rec('q21 rejected wrong option without advancing')
    box=await p.locator('.hex-clickable').bounding_box();await p.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2);await p.locator('#hexContainer.activated').wait_for();box=await p.locator('.hex-center-option').bounding_box();await p.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
   elif qtype=='multiple':
    for val in value:await p.locator('.option').filter(has=p.locator('.opt-label',has_text=val)).click()
    await p.locator('#btnNext').click()
   else:
    if qid=='q29':
     await delay(15500)
     if mode=='bad':await p.locator('.option[data-value="能源研究"]').click();await delay(1200);await rec('q29 rejected wrong option without advancing')
    await p.locator('.option[data-value='+json.dumps(value,ensure_ascii=False)+']').click()
   await delay(350);await rec(qid+' answer via UI')
   if FAST:await delay(30000)
   if mode=='quit' and qid=='q31':await p.wait_for_url('**/index-hanxiu.html');assert await p.evaluate('!localStorage.getItem("exam_passed")');await rec('authored quit returns desktop without exam result');break
   await p.wait_for_function('(i)=>currentIndex>i||document.querySelector("#resultPage")',arg=ix,timeout=40000)
   if ix%5==0:print(mode,qid,flush=True)
  if mode!='quit':
   await p.locator('#resultPage').wait_for();assert await p.evaluate('localStorage.getItem("exam_passed")')==('true' if mode=='good' else 'false');await rec('graded exam result');await p.screenshot(path=str(A/f'exam-{mode}-result.png'));await p.locator('body.can-continue').wait_for();await p.keyboard.press('Space');await p.wait_for_url('**/e3funeral.html');await c.storage_state(path=str(A/f'prefuneral-{mode}-storage.json'));await rec('funeral entered from graded exam')
 except Exception as e:d['failure']=str(e);d['traceback']=traceback.format_exc()
 d['last_url']=p.url;d['visible']=(await p.locator('body').inner_text())[-3000:];d['storage']=await p.evaluate('JSON.parse(JSON.stringify(localStorage))');await c.tracing.stop(path=str(A/f'exam-{mode}-trace.zip'));await c.close();(A/f'exam-{mode}-report.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');return {k:d[k] for k in ['mode','failure','errors','missing'] if k in d}
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(channel='msedge',headless=True)
  async def delayed(i,m):
   await asyncio.sleep(i*3);return await run(b,m)
  modes=[x for x in sys.argv[1:] if not x.startswith('--')] or ['good','bad','quit'];print(json.dumps(await asyncio.gather(*(delayed(i,m) for i,m in enumerate(modes))),ensure_ascii=True));await b.close()
if __name__=='__main__':asyncio.run(main())
