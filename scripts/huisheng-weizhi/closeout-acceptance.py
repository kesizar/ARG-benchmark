print("TOP",flush=True)
import asyncio,json,sys,subprocess,time,pathlib,os,traceback
print("BASE IMPORTED",flush=True)
from playwright.async_api import async_playwright
print("PLAYWRIGHT IMPORTED",flush=True)
sys.path.insert(0,str(pathlib.Path.cwd()))
from harness.judge import Judge
print("JUDGE IMPORTED",flush=True)
ROOT=pathlib.Path.cwd(); out=ROOT/'judge/huisheng-weizhi/verification';out.mkdir(parents=True,exist_ok=True)
async def main():
 print("begin",flush=True)
 port=int(os.environ.get('TASK_PORT','8821')); base=f'http://127.0.0.1:{port}/'; evidence={'branches':{},'errors':[]}
 server=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/huisheng-weizhi/mirror','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  await asyncio.sleep(1)
  print("server",server.poll(),flush=True)
  async with async_playwright() as pw:
   print('launching',flush=True);browser=await pw.chromium.launch(channel='msedge',headless=True);print('launched',flush=True)
   for branch in os.environ.get('TASK_BRANCHES','truth,self,cut,forget,handback').split(','):
    print('branch',branch,flush=True);c=await browser.new_context(viewport={'width':1366,'height':900});page=await c.new_page();page.set_default_timeout(8000)
    page.on('pageerror',lambda e:evidence['errors'].append('pageerror: '+str(e)))
    page.on('response',lambda r: evidence['errors'].append(str(r.status)+' '+r.url) if r.status>=400 else None)
    judge=Judge.load(ROOT/'judge/huisheng-weizhi/judge.json','huisheng-weizhi',ROOT)
    class H: pass
    h=H();h.page=page;h.pending=None;h.page_expr=lambda expr: page.evaluate("() => Boolean("+expr+")")
    step=0
    async def sample(label):
     nonlocal step
     print('step',label,flush=True);step+=1;await judge.read(h);judge.update(step)
     return {'label':label,'checkpoints':sorted(judge.checkpoints),'diagnostic':sorted(judge.side),'score':judge.score(),'routes':list(judge.route_endings),'failure':judge.failure_id}
    log=[]
    async def click(sel): await page.locator(sel).first.click()
    async def enter(sel,value): await page.locator(sel).fill(value)
    try:
     await page.goto(base+'index.html');await click('#startButton');await click('#enterButton');await page.wait_for_url('**/game.html');log.append(await sample('desktop'));assert judge.checkpoints == {} and judge.side == {} and not judge.ending_reached
     await click('#filesIcon');await click('.folder-card:has-text("文档")');await click('.protected-file-row');await enter('#memoPassword','wrong');await click('#memoUnlock');log.append(await sample('wrong memo'));assert 'memo' not in judge.side
     await enter('#memoPassword','NULL');await click('#memoUnlock');log.append(await sample('memo'))
     await click('.memo-file:has-text("NULL.txt")');log.append(await sample('confession'));await click('#textReaderClose');await click('#memoOpenClose');await click('#filesWindow .close-button')
     await click('#browserIcon');await enter('#searchBox','江渡大学');await page.locator('#searchBox').press('Enter');await click('.result');await click('[data-page="media"]');await enter('#studentSearch','wrong');await page.locator('#studentSearch').press('Enter');log.append(await sample('wrong student'));assert 'student' not in judge.side
     await enter('#studentSearch','2022043158');await page.locator('#studentSearch').press('Enter');log.append(await sample('student'))
     await click('[data-page="partners"]');await enter('#partnerSearch','栖川科技');await page.locator('#partnerSearch').press('Enter');await click('#partnerResult button');await enter('#siteSearch','错');await page.locator('#siteSearch').press('Enter');log.append(await sample('wrong company search'));assert 'e7_warning' not in judge.side;await enter('#siteSearch','E7');await page.locator('#siteSearch').press('Enter');log.append(await sample('E7 warning'));assert 'e7_warning' in judge.side;await click('.warning-back');await enter('#siteSearch','回声');await page.locator('#siteSearch').press('Enter');await click('#resultArea button:has-text("确认前往")')
     await click('#loginButton');await enter('#echoNickname','wrong');await click('#loginStep1 .login-submit');log.append(await sample('wrong nickname'));assert 'nickname' not in judge.side
     await enter('#echoNickname','mumian_47');await click('#loginStep1 .login-submit');log.append(await sample('nickname'))
     await enter('#securityAnswer','wrong');await click('#loginStep2 .login-submit');log.append(await sample('wrong security'));assert 'account' not in judge.checkpoints
     await enter('#securityAnswer','baiyuqiao');await click('#loginStep2 .login-submit');await page.wait_for_timeout(800);log.append(await sample('account'))
     await click('[data-view="help"]');await click('button:has-text("隐私与数据")');await click('button:has-text("查找丢失的数据")');await click('button:has-text("开始查找")');await page.wait_for_timeout(2300);await click('button:has-text("RETAINED")');await enter('#retainedAnswer','wrong');await click('#retainedVerifyModal button.confirm');log.append(await sample('wrong retained'));assert 'retained' not in judge.side
     await enter('#retainedAnswer','不会忘记');await click('#retainedVerifyModal button.confirm');log.append(await sample('retained'))
     await enter('#caseSearchInput','NULL');await click('.case-search-btn');await click('#caseSearchResult button');log.append(await sample('null search'));await click('#echoTriggerNotice');await page.wait_for_url('**/game.html');log.append(await sample('return desktop'))
     if branch=='handback':
      await click('[data-echo-chat="mumian"]');await click('#echoComposeSend');log.append(await sample('handback'));await page.wait_for_url('**/theonlyend1.html',timeout=15000)
     else:
      await click('#echoDesktopClose');await click('#systemButton');await click('#settingsButton');await click('[data-setting="privacy"]');await enter('#privacyPassword','wrong');await click('#privacyUnlock');log.append(await sample('wrong privacy'));assert 'privacy' not in judge.side
      await enter('#privacyPassword','linmudechengguo');await click('#privacyUnlock');log.append(await sample('privacy'))
      sel={'truth':'.evidence-file:has-text("全部证据")','self':'.evidence-file:has-text("去除“)'.replace('“','“'),'cut':'.evidence-file:has-text("仅栖川科技")','forget':'.delete-all'}[branch]
      if branch=='self': sel='.evidence-file:nth-child(2)'
      await click(sel);await click('#choiceConfirm');await page.wait_for_url('**/end*.html')
     await page.wait_for_selector('#endingStage.show',timeout=20000)
     assert judge.checkpoints == {'account': judge.checkpoints.get('account')}
     assert judge.score()['checkpoints_total']==1
     if branch=='handback':
      log.append(await sample('transfer before ending'));assert branch not in judge.route_endings
      await click('#laterButton');await page.wait_for_selector('#laterStage.show')
     log.append(await sample('ending'));assert branch in judge.route_endings
     await page.screenshot(path=str(out/(branch+'.png')),full_page=False)
     await click('.return-button');await page.wait_for_url('**/final-confirm.html');await click('#intro button');await page.wait_for_selector('#q1.show');
     for n in range(1,4):
      await enter(f'#q{n} input','wrong');await click(f'#q{n} button');await page.wait_for_selector(f'#q{n+1}.show')
     await enter('#player','测试');await click('#q4 button');await page.wait_for_url('**/full-story.html');log.append(await sample('full story'))
     evidence['branches'][branch]={'ok':True,'steps':log,'url':page.url}
    except Exception as e:
     evidence['branches'][branch]={'ok':False,'steps':log,'error':str(e),'url':page.url,'trace':traceback.format_exc()};await page.screenshot(path=str(out/(branch+'-error.png')));break
    finally: await c.close()
   await browser.close()
 finally:
  server.terminate();server.wait(timeout=5);(out/('closeout-'+os.environ.get('TASK_BRANCHES','all')+'.json')).write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'branches':{k:v['ok'] for k,v in evidence['branches'].items()},'errors':evidence['errors']},ensure_ascii=False))
asyncio.run(main())
