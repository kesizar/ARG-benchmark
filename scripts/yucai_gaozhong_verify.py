"""Normal UI route acceptance. Evaluator reads state, never writes/injects it."""
import asyncio,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from playwright.async_api import async_playwright
from harness.judge import Judge
from harness.serve_local import LocalServer
class Adapter:
 def __init__(self,page):self.page=page
 async def page_expr(self,expr):return await self.page.evaluate(expr)
async def verify(root,port,out):
 targeted=len(sys.argv)>5 and sys.argv[5]=='tier'
 resource_root=root if not (root/'configs/yucai-gaozhong.json').exists() else None
 if resource_root:root=ROOT
 cfg=json.loads((root/'configs/yucai-gaozhong.json').read_text(encoding='utf-8'));cfg['entry_url']=f'http://127.0.0.1:{port}/';cfg['local_serve']['command'][-1]=str(port);cfg['local_serve']['ready_url']=cfg['entry_url']
 if resource_root:cfg['local_serve']['command'][cfg['local_serve']['command'].index('--root')+1]=str(resource_root)
 server=LocalServer();server.start(cfg,root)
 results=[];out.mkdir(parents=True,exist_ok=True)
 try:
  async with async_playwright() as p:
   browser=await p.chromium.launch(channel='msedge',headless=True)
   for route in (sys.argv[4].split(',') if len(sys.argv)>4 else ['minute13','restore','witness13']):
    c=await browser.new_context(viewport={'width':1366,'height':900});page=await c.new_page();j=Judge.load(root/'judge/yucai-gaozhong/judge.json','yucai-gaozhong',root);events=[];errors=[];page.on('pageerror',lambda e:errors.append(str(e)));step=0
    async def record(label):
     nonlocal step
     step+=1;await j.read(Adapter(page));j.update(step)
     events.append({'step':step,'label':label,'score':j.score(),'state':await page.evaluate("JSON.parse(localStorage.getItem('yc_state_v1')||'null')")})
    async def click(sel):
     await page.locator(sel).click();await page.wait_for_timeout(70);await record(sel)
    async def btn(txt):
     if targeted and txt in ['墙上的黑白合影','看铁门和锁链','抬头看三楼的窗','车筐','掀开座垫-again','走到西南角','双杠与沙坑','检查封条','用手机照布告栏的残纸','推开101教室的门','照向三楼拐角的阴角','检查二楼半的扶手','看墙上的身高刻度','看301的门','查看门口的封条','看那张反放的课桌','看窗台']:return
     await page.get_by_role('button',name=txt,exact=True).click();await page.wait_for_timeout(70);await record(txt)
    async def close():
     await click('.yc-mask.show .yc-x');await page.wait_for_timeout(260)
    async def search(t):
     await page.locator('#searchInput').fill(t);await page.locator('#searchInput').press('Enter');await page.wait_for_timeout(80);await record('search '+t)
    async def nav(n):
     await click(f'#navList [data-nav="{n}"]')
    async def bag(tab):
     await click('#ycBagBtn');await click(f'#ycBag [data-tab="{tab}"]')
    async def bagclose():await click('#ycBag .ycd-h .yc-x')
    try:
     await page.goto(cfg['entry_url']);await record('initial-empty');assert not j.checkpoints
     await search('林苑');await click('#ycMailBtn');await click('#ycCineGo');await click('#ycBag [data-tab="mail"]');await btn('告诉我该怎么做。');await bagclose()
     await search('旧校区');await click('#ycSnap2013')
     if route!='restore':
      await click('#ycXjLink');await page.locator('#ycXjQ').fill('1328');await click('#ycXjBtn');assert 'school-number' not in j.side
      await page.locator('#ycXjQ').fill('1329');await click('#ycXjBtn');assert 'school-number' in j.side;await close()
     else:await close()
     await search('旧校区');await page.locator('#newsList .it').filter(has_text='关于旧校区围墙').click();await record('read-monitor-notice');await click('#modalClose')
     await page.locator('#calH').click(click_count=3,delay=70);await click('#ycCalGhost')
     await nav('teach');await click('#ycKetiLink');await close()
     await nav('student');await click('#ycNetdiskLink');await page.locator('#ycNdPwd').fill('000000');await click('#ycNdGo');assert 'netdisk-code' not in j.side
     await page.locator('#ycNdPwd').fill('201321');await click('#ycNdGo');assert 'netdisk-code' in j.side;await close()
     if route=='witness13' and not targeted:
      await nav('home');g=page.locator('#homeGallery .g').filter(has_text='校园全景');await g.scroll_into_view_if_needed();box=await g.bounding_box();await page.mouse.move(box['x']+20,box['y']+20);await page.mouse.down();await page.wait_for_timeout(820);await page.mouse.up();await record('hold panorama EXIF');await close()
      await bag('mail');await btn('我找到了一些东西（提交线索）');await bagclose()
      # Verify the compatibility fix through an ordinary page reload.
      await page.reload();await bag('mail');assert '林苑，是我儿子' in await page.locator('#ycBagBody').inner_text();await record('reload-reconstructed-mail');await bagclose()
      await nav('affairs');await page.locator('#ycMbTxt').fill('2011年林苑晚自习的事');await click('#ycMbGo');await page.wait_for_timeout(2000);await record('zhou-mail')
     if route=='witness13' and targeted:
      await bag('mail');await btn('我找到了一些东西（提交线索）');await bagclose()
     await bag('prog');await click('#ycGoNight')
     if route!='minute13':
      await btn('敲传达室的窗');await btn('张建国');assert 'guard-teacher' not in j.side
      await btn('周国栋');await close();assert 'guard-teacher' in j.side
      await btn('去传达室坐坐');await btn('翻值班记录本（2026年）');await close()
      if route=='witness13' and not targeted:
       await btn('书架上的旧值班本（2011年）');await btn('借走桌上的铅笔和白纸');h=page.get_by_role('button',name='用铅笔拓印压痕（按住2秒）',exact=True);await h.scroll_into_view_if_needed();box=await h.bounding_box();await page.mouse.move(box['x']+20,box['y']+10);await page.mouse.down();await page.wait_for_timeout(2150);await page.mouse.up();await record('hold rubbing')
      await btn('墙上的黑白合影');await btn('回大门')
      if route=='witness13' and not targeted:
       for t in ['沿围墙走到旧操场外侧','走近旧教学楼','走侧门','上楼梯','下楼上三楼','推门进入305','检查讲台']:await btn(t)
       st=await page.evaluate("JSON.parse(localStorage.getItem('yc_state_v1'))");assert not st['clues'].get('A')
       for t in ['出教室','下楼','回一楼','出楼','回操场方向','回大门']:await btn(t)
     await btn('看铁门和锁链');await btn('抬头看三楼的窗');await btn('车棚（大门内侧）');await btn('车筐');await btn('掀开座垫');await close();await btn('掀开座垫');await btn('回大门');await btn('沿围墙走到旧操场外侧');await btn('蹲下来看水泥地面');await btn('走到西南角');await btn('双杠与沙坑');await btn('走近旧教学楼');await btn('检查封条')
     if route=='minute13':
      await btn('隔着门缝往里看')
     else:
      await btn('走侧门');await btn('用手机照布告栏的残纸');await btn('推开101教室的门');await btn('上楼梯')
      if not targeted:await btn('照向三楼拐角的阴角');await close()
      await btn('检查二楼半的扶手');await btn('看墙上的身高刻度');await btn('下楼上三楼');await btn('看301的门')
      if not targeted:await btn('查看门口的封条');await close()
      await btn('推门进入305');await btn('检查讲台');await close();await btn('看那张反放的课桌');await btn('看窗台')
      if route=='witness13':await btn('趴下看讲台底下的地板缝');await close()
     await click('#ycScExit');await page.wait_for_timeout(300)
     if route=='witness13' and not targeted:
      for night in range(2):
       await bag('prog');await click('#ycGoNight');await record('repeat-night-'+str(night+2));await click('#ycScExit');await page.wait_for_timeout(300)
      st=await page.evaluate("JSON.parse(localStorage.getItem('yc_state_v1'))");assert st['flags']['metLin305']
     await bag('prog');await click('#ycGoReport');await click('#ycRpGo');assert 'report-five' not in j.side
     for i,v in enumerate([0,2,0,2,1]):
      await page.locator(f'#ycRp{i}').select_option(str(v))
      if i<4:await click('#ycRpGo');assert 'report-five' not in j.side
     await click('#ycRpGo');assert 'report-five' in j.side
     await click('#ycGoFinal');await click('#ycFinYes');await record('finale-start-not-completed');assert not j.ending_reached
     for k in range(80):
      if await page.locator('#ycEndT').is_visible():break
      await page.locator('#ycEnd').click(position={'x':20,'y':20});await page.wait_for_timeout(20)
     await record('finale-complete');s=await page.evaluate("JSON.parse(localStorage.getItem('yc_state_v1'))");assert s['ending']==route,(route,s['ending']);assert j.ending_reached
     if route=='witness13' and not targeted:assert len(s['clues'])==20,s['clues']
     assert j.score()['ending_tier']=='normal' and j.score()['good_ending'] is False,j.score()
     authored=next(x for x in j.cfg['routes'] if x['id']==route)
     assert authored['authored_label'] in await page.locator('#ycEndS').inner_text()
     await page.screenshot(path=str(out/f'{route}.png'),full_page=True)
     score=j.score();page.once('dialog',lambda d:d.accept());await btn('重新开始调查');await page.wait_for_timeout(500)
     fresh=Judge.load(root/'judge/yucai-gaozhong/judge.json','yucai-gaozhong',root);await fresh.read(Adapter(page));fresh.update(0);assert not fresh.checkpoints and not fresh.side and not fresh.ending_reached
     assert not await page.evaluate("JSON.parse(localStorage.getItem('yc_state_v1')||'{}').ended")
     results.append({'route':route,'passed':True,'score':score,'authored_classification':authored['authored_classification'],'authored_label':authored['authored_label'],'targeted_tier_review':targeted,'ui_reset_clean':True,'errors':errors,'steps':step})
    except Exception as e:
     await page.screenshot(path=str(out/f'{route}-error.png'),full_page=True);results.append({'route':route,'passed':False,'error':str(e),'traceback':traceback.format_exc(),'errors':errors});raise
    finally:
     (out/f'{route}.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8');(out/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');await c.close()
   await browser.close()
 finally:server.stop()
 return results
if __name__=='__main__':
 root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT;port=int(sys.argv[2]) if len(sys.argv)>2 else 8831;out=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else ROOT/'judge/yucai-gaozhong/acceptance'
 print(json.dumps(asyncio.run(verify(root,port,out)),ensure_ascii=False))
