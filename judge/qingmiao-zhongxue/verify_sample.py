import asyncio,json,sys,subprocess,time,urllib.request,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
T='qingmiao-zhongxue';EV=R/'judge'/T/'verification';EV.mkdir(parents=True,exist_ok=True)
REPORT=['英材培育计划','YC基因','500','YC-08营养液','青苗农场','英材良品']
WORDS=['好','350','2510','乳糖不耐','5201','YC001','20101123','英才2301班','营养不良性贫血','CHOICE','CHOICE','？','......','青苗论坛','CHOICE','农场办公室档案柜','20250308','CHOICE','CHOICE','QM230617001','幼苗共育','QM251123489','吃植物人','牛奶','CHOICE','砧木','接穗','成材','我要举报']
async def main():
 cfg=json.loads((R/'configs'/f'{T}.json').read_text(encoding='utf-8'));h=BrowserHarness(cfg,EV);rows=[];errors=[];step=0
 log=(EV/'server.log').open('w');proc=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(R/'tasks'/T/'mirror'),'--port','8811'],stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 async def check(j,label):
  nonlocal step
  step+=1;await j.read(h);j.update(step);s=j.score();rows.append({'label':label,'score':s});(EV/'ui-progress.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');return s
 async def shot(name):await h.page.screenshot(path=str(EV/(name+'.png')),full_page=False)
 async def ready():await h.page.wait_for_function("!isWaitingForResponse",timeout=60000);await h.page.wait_for_timeout(1700)
 async def send(w):
  await ready();await h.page.locator('#messageInput').fill(w);await h.page.locator('#sendButton').click();await ready()
 async def open_game():
  await h.reset();await h.page.locator('.start-game-btn').click();await asyncio.sleep(.5);h.page=h.context.pages[-1];await h.page.wait_for_load_state();h.page.on('pageerror',lambda e:errors.append(str(e)));h.page.on('dialog',lambda d:asyncio.create_task(d.accept()));await h.page.locator('#closeEmailBtn').click();await ready()
 try:
  for _ in range(50):
   try:urllib.request.urlopen(cfg['entry_url'],timeout=1);break
   except Exception:await asyncio.sleep(.1)
  await h.start()
  for choice,ending in [('1','gentle'),('2','harsh')]:
   await open_game();j=Judge.load(R/'judge'/T/'judge.json',T,R)
   assert not (await check(j,ending+'-reset'))['diagnostic']
   await h.page.locator('#messageInput').fill('350');assert not (await check(j,ending+'-typed-unsubmitted'))['diagnostic']
   await h.page.locator('#messageInput').fill('wrong');await h.page.locator('#sendButton').click();assert not (await check(j,ending+'-wrong'))['diagnostic']
   for n,w in enumerate(WORDS):
    w=choice if w=='CHOICE' else w
    before=(await check(j,f'{ending}-before-{n:02d}'))['diagnostic'];await send('invalid');assert (await check(j,f'{ending}-invalid-{n:02d}'))['diagnostic']==before
    payload=(w+' '+ ' '.join(WORDS[2:])) if n==1 else w
    await send(payload);s=await check(j,f'{ending}-chat-{n:02d}-{w}')
    if n==1:assert set(s['diagnostic'])=={'k01'}
    (EV/(ending+'-history.json')).write_text(json.dumps(await h.page.evaluate('conversationHistory'),ensure_ascii=False,indent=2),encoding='utf8')
    if n==2 and ending=='gentle':
     mainpage=h.page
     await h.page.locator('a[href*="Official-Site"]').first.click();await asyncio.sleep(.3);h.page=h.context.pages[-1];await h.page.wait_for_load_state()
     for keyword,target in [('张晓苗','detail-zhangxiaomiao-labor'),('张晓苗','detail-zhangxiaomiao-report')]:
      await h.page.locator('#searchInput').fill(keyword);await h.page.locator('#searchButton').click();await h.page.locator(f'a.search-result-link[data-target="{target}"]').click()
      if target.endswith('labor'):
       for idx,answer in [(1,'7205'),(2,'NASAL')]:
        await h.page.locator(f'#passwordInput{idx}').fill('wrong');await h.page.locator(f'#passwordSection{idx} button').click();assert not await h.page.locator(f'#imageContainer{idx+1}').is_visible();await check(j,f'labor-{idx}-wrong')
        await h.page.locator(f'#passwordInput{idx}').fill(answer);await h.page.locator(f'#passwordSection{idx} button').click();assert await h.page.locator(f'#imageContainer{idx+1}').is_visible();await check(j,f'labor-{idx}-correct');await shot(f'labor-{idx}')
      else:
       await h.page.locator('#reportPassword').fill('wrong');await h.page.locator('#reportPassword').press('Enter')
       # The original page uses a button, not an Enter handler.
       await h.page.locator('button[onclick="checkReportPassword()"]').click();assert not await h.page.locator('#encryptedContent').is_visible();await check(j,'report-decrypt-wrong')
       await h.page.locator('#reportPassword').fill('0630');await h.page.locator('button[onclick="checkReportPassword()"]').click();await h.page.locator('#encryptedContent').wait_for(state='visible');await check(j,'report-decrypt-correct');await shot('report-decrypt')
      await h.page.locator(f'#{target} .back-to-home').click()
     # Search surfaces and every reachable result are preserved as visible evidence.
     documents=[]
     for kw in ['林昭','英才班','青苗班','林又','学生手册','王梅','YC230617001','YC251123489','食堂','校医院','张晓苗','青苗论坛']:
      await h.page.locator('#searchInput').fill(kw);await h.page.locator('#searchButton').click()
      targets=await h.page.locator('a.search-result-link').evaluate_all('(a)=>a.map(x=>({id:x.dataset.target,text:x.textContent}))')
      for target in targets:
       await h.page.locator(f'a.search-result-link[data-target="{target["id"]}"]').click();documents.append({'query':kw,'target':target,'visible_text':await h.page.locator('#'+target['id']).inner_text()});await h.page.locator(f'#{target["id"]} .back-to-home').click();await h.page.locator('#searchInput').fill(kw);await h.page.locator('#searchButton').click()
      await h.page.locator('.back-to-home:visible').first.click()
     (EV/'school-visible-documents.json').write_text(json.dumps(documents,ensure_ascii=False,indent=2),encoding='utf-8')
     h.page=mainpage;await mainpage.bring_to_front();await h.context.pages[-1].close()
   await h.page.locator('#reportModal').wait_for(state='visible')
   if ending=='gentle':
    for bad in range(1,7):
     for idx,answer in enumerate(REPORT,1):await h.page.locator(f'#blank{idx}').fill('wrong' if idx==bad else answer)
     await h.page.locator('#submitReportBtn').click();assert 'report' not in (await check(j,f'report-field-{bad}-wrong'))['diagnostic']
   for idx,answer in enumerate(REPORT,1):await h.page.locator(f'#blank{idx}').fill(answer if idx!=6 else 'wrong')
   await h.page.locator('#submitReportBtn').click();s=await check(j,ending+'-report-wrong');assert 'report' not in s['diagnostic'];await shot(ending+'-report-wrong')
   await h.page.locator('#blank6').fill(REPORT[-1]);await h.page.locator('#submitReportBtn').click();assert 'report' in (await check(j,ending+'-report-correct'))['diagnostic']
   await h.page.get_by_text('点击继续',exact=True).wait_for(timeout=180000);await h.page.get_by_text('点击继续',exact=True).click();await h.page.locator('#closeTerrorPopup').click();await h.page.locator('#policePage').wait_for(state='visible',timeout=30000);await shot(ending+'-police');await h.page.locator('#backToChatBtn').click();await send('你还好吗？收到请回复');await send('期待我们下次见面' if ending=='gentle' else '食人族如何补充膳食纤维？')
   element='typewriterEndTypedText' if ending=='gentle' else 'animationEndTypedText';await h.page.wait_for_function('(id)=>document.getElementById(id)?.textContent==="END"',arg=element,timeout=90000);s=await check(j,ending+'-ending');assert s['ending_reached'] and s['route_id']==ending;await shot(ending+'-ending')
  # Original bypass is independently reproduced through UI from a fresh game.
  await open_game();j=Judge.load(R/'judge'/T/'judge.json',T,R);await send('期待我们下次见面');await h.page.wait_for_function('document.getElementById("typewriterEndTypedText")?.textContent==="END"',timeout=90000);s=await check(j,'fresh-start-ending-bypass');assert s['ending_reached'] and not s['diagnostic'];await shot('ending-bypass')
  await open_game();j=Judge.load(R/'judge'/T/'judge.json',T,R);s=await check(j,'final-reset');assert not s['ending_reached'] and not s['diagnostic'];await shot('final-reset')
  out={'pass':True,'rows':rows,'page_errors':errors,'evidence_scope':'Normal Playwright UI actions; source-derived inputs used for engineering acceptance, not proof of independent puzzle solving. No page state writes or answer API. Original animation waiting preserved.'}
 except Exception as e:
  out={'pass':False,'error':repr(e),'traceback':traceback.format_exc(),'rows':rows,'page_errors':errors};await shot('failure')
 finally:
  await h.close();proc.terminate();proc.wait(timeout=10);log.close()
 (EV/'ui-acceptance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k not in ['rows']},ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
