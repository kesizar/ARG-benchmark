"""Evaluator-only UI acceptance. No solution/state injection, no model APIs."""
from pathlib import Path
import asyncio,argparse,json,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.serve_local import LocalServer
from harness.judge import Judge
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8811);p.add_argument('--resource-root');p.add_argument('--out');p.add_argument('--delivery',action='store_true');p.add_argument('--skip-materials',action='store_true');p.add_argument('--route',type=int,default=0);a=p.parse_args();T='yiwu-yuren';O=Path(a.out) if a.out else R/'judge'/T/'verification';O.mkdir(parents=True,exist_ok=True)
async def main():
 c=load_config(R/'configs'/f'{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/001/window.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve']['command'][-1]=str(a.port);c['local_serve'].update(port=a.port,ready_url=c['entry_url'])
 if a.resource_root:c['local_serve']['command'][3]=str(Path(a.resource_root).resolve())
 h=BrowserHarness(c,O);sv=LocalServer();j=None;rep={'kind':'engineering_ui_acceptance_no_model','steps':[],'errors':[],'http_errors':[],'routes':[],'negative_checks':[]};des=None
 async def rec(label):
  await j.read(h);j.update(len(rep['steps'])+1);rep['steps'].append({'action':label,'url':h.page.url,'checkpoints':list(j.checkpoints),'score':j.score()});h.consume_step()
 async def click(sel,text=False):
  loc=h.page.get_by_text(sel,exact=True).first if text else h.page.locator(sel).first
  await loc.wait_for(state='visible')
  if sel!='#clickTarget':await loc.scroll_into_view_if_needed()
  b=await loc.bounding_box();assert b,sel
  result=await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2});assert result=='ok',(sel,result)
  await asyncio.sleep(2.0 if text else .75);await rec('click '+sel)
 async def fill(sel,value):
  await h.page.locator(sel).fill(value);await rec('type '+sel+' '+value)
 async def snap(name):
  await h.page.screenshot(path=str(O/(name+'.png')),full_page=True);(O/(name+'.txt')).write_text(await h.page.locator('body').inner_text(),encoding='utf-8')
 async def tab(pg):
  h.page=pg;await pg.bring_to_front();await rec('switch_tab')
  if pg==des:
   for other in list(h.context.pages):
    if other!=pg:await other.close()
 async def search(word):
  await tab(des);await fill('#searchInput',word);await click('.suggestion-item');await snap('clue-'+word)
 async def new():
  nonlocal j,des
  await h.reset();j=Judge.load(R/c['judge_path'],T,R);des=h.page;await rec('fresh_context');assert not j.checkpoints and not j.ending_reached
  h.context.on('page',lambda pg:pg.on('pageerror',lambda e:rep['errors'].append({'error':str(e),'stack':e.stack,'step':len(rep['steps'])})))
  h.context.on('response',lambda rr:rep['http_errors'].append(rr.url) if rr.status>=400 and not rr.url.endswith('favicon.ico') else None)
 async def login_student():
  await search('教务处');await fill('#username','wrong');await fill('#password','bad');await click('#loginBtn');assert not j.checkpoints;rep['negative_checks'].append('student wrong credentials no reasoning credit')
  await fill('#username','24071225');await fill('#password','20250225');await click('#loginBtn');assert h.page.url.endswith('xuesheng.html')
 async def reply(answer,wrong=None):
  before=list(j.checkpoints);await click('.message-item[data-reply-enabled=true] >> nth=-1')
  if wrong:
   await click(wrong,True);assert list(j.checkpoints)==before;assert await h.page.locator('.reply-error-msg:visible').count();rep['negative_checks'].append('dialogue wrong '+wrong)
  await click(answer,True)
 try:
  sv.start(c,R,O/'server.log');assert sv.owned;await h.start();await new();await snap('initial')
  if not (a.delivery or a.skip_materials):
   await click('a[href="jishiben.html"]');await click('.note-header');await snap('clue-notepad');await click('a.back-link');des=h.page
   await search('沈沁');
   for su in await h.page.locator('details summary').all():await su.click()
   await snap('clue-resume-expanded')
   await search('周毅');await search('同海大学');await fill('#searchInput','于晓丽');await click('#searchBtn');await snap('clue-professor')
   await search('航海公园');await click('a[href="zhuye.html"]');await snap('clue-park-diary')
   await search('年糕');
   for hd in await h.page.locator('.foldable-header').all():await hd.click()
   await snap('clue-feeder-expanded')
   await search('青岚第二医院');await click('#gotoQueryBtn');await fill('#patientName','沈沁');await fill('#birthDate','2001-10-05');await fill('#admitDate','2025-03-02');await click('#searchRecordBtn');assert h.page.url.endswith('yiyuan.html');rep['negative_checks'].append('hospital wrong date no navigation');await fill('#admitDate','2025-03-01');await click('#searchRecordBtn');await snap('clue-hospital')
   await tab(des);await click('a[href="weixindenglu.html"]');await fill('#wechatAccountInput','wrong');await fill('#passwordInput','bad');await click('#loginMainBtn');assert not j.checkpoints;await click('#forgotPasswordLink')
   for wx,phone in [('wrong','183794677'),('alexshen0110','123'),('alexshen0110','138112805'),('alexshen0110','111111111')]:
    await fill('#forgotWechatInput',wx);await fill('#phoneInput',phone);await click('#verifyBtn');assert not await h.page.locator('#loginAfterVerifyBtn').is_visible();rep['negative_checks'].append('wechat rejected '+phone)
   await fill('#phoneInput','183794677');await click('#verifyBtn');await click('#loginAfterVerifyBtn');assert h.page.url.endswith('weixin.html');await snap('clue-wechat')
   for row in await h.page.locator('.chat-item').all():await row.click();await rec('read_wechat_chat')
   await tab(des);await click('a[href="youjian.html"]');await fill('#emailInput','a@b.co');await fill('#passwordInput','bad');await click('#loginBtn');assert '错误' in await h.page.locator('#errorMessage').inner_text();await click('#forgotPasswordBtn')
   await fill('#modalAccount','alex.shen@outlook.com');await fill('#modalIdNumber','wrong');await fill('#modalPhone','183794677');await click('#verifyIdentityBtn');assert h.page.url.endswith('youjian.html');rep['negative_checks'].append('mail wrong identity no navigation');await fill('#modalIdNumber','2132001100576');await click('#verifyIdentityBtn');await snap('clue-mail')
   for folder in ['inbox','sent']:
    await click('.folder-item[data-folder="'+folder+'"]')
    for row in await h.page.locator('.email-item').all():await row.click();await rec('read_mail_'+folder)
   await search('教务处');await click('#roleTeacherBtn');await fill('#username','TH2021LA086');await fill('#password','19780315');await click('#loginBtn');await snap('clue-teacher')
  await login_student()
  for n,(choice,ans) in enumerate(zip(['该死','不该死','who cares？'],['我觉得俩人一样该死','死亡对他这种人来说太轻了。','我不想毁了我的信誉 今天我就当没见过你']),1):
   if a.route and a.route!=n:continue
   if a.delivery and n>1:break
   if n>1 and not a.route:await new();await login_student()
   await click('#targetMessage');await click('真闹鬼了？',True);assert not j.checkpoints;rep['negative_checks'].append('identity wrong');await click('你是陈屿。',True)
   await reply('你只需要告诉我你这样做是为了什么。','因为我很聪明。');await reply('嫉妒她的周毅','她自己');await reply(choice)
   # Every branch has a wrong fifth-round option, then the valid option.
   wrong=['我觉得周毅更该死','他死了你给我结钱啊？','看看猫喵喵喵喵'][n-1];await reply(ans,wrong);assert set(j.checkpoints)=={'identity','intent','killer',f'branch{n}'}
   await click('[data-final=true]');assert h.page.url.endswith(f'jj{n}.html');assert j.ending_reached;rep['routes'].append(j.score());await snap(f'ending{n}')
   if n==3:
    await click('#clickTarget');assert await h.page.locator('#scoreValue').inner_text()=='1';await click('#resetGameBtn');assert await h.page.locator('#scoreValue').inner_text()=='0';rep['moon_game_reset']=True
   await click('.fixed-end-btn');await snap(f'summary{n}');await click('.jump-btn');assert await h.page.evaluate('JSON.parse(localStorage.caseCompleted)[0]') is True
   await fill('#passInput','bad');await click('#unlockBtn');assert not await h.page.locator('#questContainer').is_visible();await fill('#passInput','CORVUS_1899');await click('#unlockBtn');await click('[data-case-index="0"]');await click('#confirmCancelBtn');assert await h.page.evaluate('JSON.parse(localStorage.caseCompleted)[0]') is True
   await click('[data-case-index="0"]');await click('#confirmOkBtn');assert h.page.url.endswith('window.html');assert await h.page.evaluate('JSON.parse(localStorage.caseCompleted)[0]') is False;assert await h.page.evaluate('!localStorage.wechatLogged && !localStorage.outlookLogged');rep['ui_replay_reset_verified']=True
  await new();assert await h.page.evaluate('localStorage.length')==0;rep['fresh_context_reset']=True
  # Auditor-only direct ending negative, outside normal solution replay.
  await h.page.goto(f'http://127.0.0.1:{a.port}/001/jj1.html');await rec('auditor_direct_ending');assert not j.checkpoints and not j.ending_reached and j.score()['route_progress']<1;rep['direct_ending_cannot_full_score']=True
  rep['blocked_requests']=h.blocked;assert not rep['http_errors'] and not h.blocked;rep['pass']=True
 except Exception as e:
  rep['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(O/'failure.png'),full_page=True)
  raise
 finally:
  (O/'acceptance.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();sv.stop()
asyncio.run(main())
