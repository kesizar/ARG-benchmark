"""Auditor-only replay through BrowserHarness UI actions; not a model score."""
import argparse,asyncio,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--port',type=int,default=8831);args=p.parse_args();ROOT=args.root.resolve();sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
OUT=ROOT/'judge/sis/verification'

class Replay:
 def __init__(self,h,j):self.h=h;self.j=j;self.steps=[];self.negatives=[];self.screens=set()
 async def record(self,action):
  await self.j.read(self.h);fresh=self.j.update(len(self.steps)+1)
  storage=await self.h.local_storage();state=json.loads(storage.get('sis_game_progress_v1','{}'));self.screens.add(state.get('lastScreen','home'))
  visible=await self.h.page.evaluate("() => document.querySelector('.screen-label')?.textContent || (document.querySelector('.sister-reveal')?'sisterReveal':document.querySelector('.true-ending')?'endingTrue':document.querySelector('.normal-ending')?'endingNormal':document.querySelector('.title-screen')?'home':'other')")
  self.steps.append({'action':action,'new':fresh,'score':self.j.score(),'screen':state.get('lastScreen'),'visible_screen':visible,'flags':state.get('flags',{})});self.h.consume_step()
 async def click(self,locator,negative=False):
  before=set(self.j.checkpoints)|set(self.j.side)
  loc=self.h.page.locator(locator) if isinstance(locator,str) else locator;loc=loc.first;await loc.wait_for(state='visible',timeout=12000);await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b
  action={'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2};assert await self.h.act(action)=='ok';await self.record(action)
  if negative:
   assert before==set(self.j.checkpoints)|set(self.j.side),'Unscored action gave points'
   self.negatives.append(len(self.steps))
 async def button(self,name,negative=False):await self.click(self.h.page.get_by_role('button',name=name,exact=True),negative)
 async def type(self,locator,value):
  loc=self.h.page.locator(locator) if isinstance(locator,str) else locator;loc=loc.first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b
  self.h.elements=[{'n':0,'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}]
  assert await self.h.act({'op':'type','n':0,'clear':True,'text':value})=='ok';await self.record({'op':'type','value_redacted':True})
 async def search(self,query,result=0):
  await self.button('浏览器');await self.type('input[aria-label="搜索网页"]',query);await self.button('搜索');
  if result is not None:await self.click(self.h.page.locator('.search-result').nth(result))
 async def wait(self,ms):await self.h.act({'op':'wait','ms':ms});await self.record({'op':'wait','ms':ms})
 async def cover_documents(self):
  for query,count in [('林秀琴',2),('青禾',3),('周柏川',2),('归途',2),('安和',2)]:
   for i in range(count):await self.search(query,i)
  await self.search('不存在的检索词',None)
  assert await self.h.page.locator('.empty-web').count()==1
  await self.search('归途',0)
  for tab in ['首页','救助工作','创办理念','工作人员','影像志']:await self.click(self.h.page.locator('.guitu-site nav button').filter(has_text=tab))
 async def run(self,ending,full):
  await self.record({'op':'fresh_context'});assert not self.j.checkpoints and not self.j.side
  await self.button('开始');await self.click(self.h.page.get_by_role('button',name=re.compile('电子捐赠证明.pdf')))
  if full:
   await self.button('文件');await self.button('邮箱');await self.click(self.h.page.get_by_role('button',name=re.compile('捐赠资料存档')))
   await self.type('input[placeholder="捐献者的紧急联系人姓名"]','错误');await self.button('确认',True)
   await self.cover_documents()
   await self.button('内部入口')
   await self.type('.employee-login-card input:not([type=password])','wrong');await self.type('.employee-login-card input[type=password]','wrong');await self.click('.employee-login-card button',True)
   await self.type('.employee-login-card input:not([type=password])','GY-032');await self.type('.employee-login-card input[type=password]','CXY2013032');await self.click('.employee-login-card button')
   for tab in ['概览','救助档案','账号通知','团队活动']:await self.click(self.h.page.locator('.dashboard-grid aside button').filter(has_text=tab))
   await self.click('.system-back')
   await self.type('.admin-login-card input:not([type=password])','ID-ZBC-01');await self.type('.admin-login-card input[type=password]','wrong');await self.click('.admin-login-card button',True)
   await self.type('.admin-login-card input:not([type=password])','wrong');await self.click('.admin-login-card button',True)
   await self.type('.admin-login-card input:not([type=password])','GT001');await self.type('.admin-login-card input[type=password]','xiaoman2011');await self.click('.admin-login-card button')
   for tab in ['对象档案','转运记录','旧日志','业务对照']:await self.click(self.h.page.locator('.admin-tabs button').filter(has_text=tab))
   await self.button('对象档案');await self.button('查看完整档案')
   await self.click('.system-back');await self.click('.system-back')
   await self.search('安和',0);await self.type('input[aria-label="福利院档案查询"]','错误');await self.button('查询档案',True)
   await self.type('input[aria-label="福利院档案查询"]','林安宁');await self.button('查询档案')
  await self.button('邮箱');await self.click(self.h.page.get_by_role('button',name=re.compile('捐赠资料存档')))
  if not full:
   await self.type('input[placeholder="捐献者的紧急联系人姓名"]','错误');await self.button('确认',True)
  await self.type('input[placeholder="捐献者的紧急联系人姓名"]','岁安');await self.button('确认');await self.wait(4000);await self.button('开始确认')
  names=['relation','guitu','transfer','daughters','sender'];answers=[1,1,2,1,2]
  if full:
   for n in names:await self.click(self.h.page.locator('input[name="'+n+'"]').nth(0))
   await self.button('提交答案',True)
   for i,(n,correct) in enumerate(zip(names,answers)):
    await self.click(self.h.page.locator('input[name="'+n+'"]').nth(correct));await self.button('提交答案')
    assert len(self.j.checkpoints)==i+2
  else:
   for n,correct in zip(names,answers):await self.click(self.h.page.locator('input[name="'+n+'"]').nth(correct))
   await self.button('提交答案')
  await self.wait(5600);await self.button('我愿意' if ending=='true' else '到这里就够了');await self.wait(4300)
  assert self.j.ending_reached and len(self.j.checkpoints)==6
  assert len(self.j.side)==(3 if full else 0),self.j.score()
  await self.h.page.screenshot(path=str(OUT/f'{ending}.png'),animations='disabled')
  if full:
   storage=await self.h.local_storage();state=json.loads(storage['sis_game_progress_v1'])
   assert len(state['visited'])==11, state['visited']
   assert len(state['flags'])>=20,state['flags']
   await self.button('返回首页');await self.button('继续');await self.click('.brand-mark')
   await self.button('重新开始');await self.button('取消');await self.button('重新开始');await self.button('确认')
   storage=await self.h.local_storage();assert 'sis_true_end_forever_v1' not in storage and 'sis_game_progress_v1' not in storage
  return {'ending':ending,'full_investigation':full,'score':self.j.score(),'steps':self.steps,'unscored_checks':len(self.negatives),'screens':sorted(self.screens)}

async def main():
 OUT.mkdir(parents=True,exist_ok=True);cfg=load_config(ROOT/'configs/sis.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/SIS/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['port']=args.port;cfg['local_serve']['command'][-1]=str(args.port);cfg['settle_ms']=300
 server=LocalServer();h=BrowserHarness(cfg,OUT);report={'kind':'engineering_not_model_score','branches':[],'http_errors':[],'page_errors':[],'deployment_root':str(ROOT)}
 try:
  server.start(cfg,ROOT,OUT/'server.log');await h.start()
  for ending,full in [('true',True),('normal',False)]:
   await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);await h.page.reload();await h.page.wait_for_timeout(500)
   replay=Replay(h,Judge.load(ROOT/cfg['judge_path'],'sis',ROOT));report['branches'].append(await replay.run(ending,full));print('branch passed',ending,flush=True)
  report['blocked_requests']=h.blocked
  assert not report['http_errors'] and not report['page_errors'] and not report['blocked_requests'];report['pass']=True
 except Exception as exc:
  report['failure']=str(exc)
  if h.page:
   await h.page.screenshot(path=str(OUT/'failure.png'))
   report['failure_storage']=await h.local_storage()
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
if __name__=='__main__':asyncio.run(main())
