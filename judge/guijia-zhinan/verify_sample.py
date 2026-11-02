"""Private source-informed UI audit. Never inject state or invoke game functions."""
import argparse,asyncio,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='guijia-zhinan'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8812);a=p.parse_args();OUT=R/'judge'/T/'verification'
class Audit:
 def __init__(self,h):
  self.h=h;self.trace=[];self.nodes=set();self.negative=0;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.c=Judge.load(R/f'judge/{T}/collection-judge.json',T+'-collection',R)
 async def record(self,action):
  for j in [self.j,self.c]:await j.read(self.h);j.update(len(self.trace))
  node=await self.h.page.evaluate('S.n');self.nodes.add(node)
  self.trace.append({'action':action,'node':node,'score':self.j.score(),'collection_score':self.c.score()});self.h.consume_step()
 async def act(self,action,private=False):
  assert await self.h.act(action)=='ok'
  await self.record({**action,'text':'[private input]'} if private else action)
 async def choose(self,label=None,input=False):
  for i in range(15):
   obs=await self.h.observe('current.png')
   choices=[e for e in obs['elements'] if (e['kind']=='input' if input else e['kind']=='button' and (label is None or label in e['label']))]
   if choices:return choices[0]
   await self.act({'op':'scroll','dir':'down'});await self.h.page.wait_for_timeout(250)
  raise AssertionError('Control missing '+str(label))
 async def click(self,label=None):
  e=await self.choose(label);await self.act({'op':'click','n':e['n']})
 async def enter(self,text):
  e=await self.choose(input=True);await self.act({'op':'type','n':e['n'],'text':text,'clear':True,'enter':True},private=True)
 async def solve(self,node,answer,wrong):
  before=(set(self.j.checkpoints),set(self.j.side),self.j.ending_reached)
  await self.enter(wrong);assert await self.h.page.evaluate('S.n')==node
  assert await self.h.page.locator('.pzf.f').count()==1
  assert before==(set(self.j.checkpoints),set(self.j.side),self.j.ending_reached);self.negative+=1
  await self.h.page.screenshot(path=str(OUT/f'wrong-{node}.png'))
  await self.enter(answer)
  # latch the successful state even if the following scene timer fires during observation
  await self.act({'op':'wait','ms':1100});assert await self.h.page.evaluate('S.n')!=node
 async def search(self,good):
  before=set(self.j.checkpoints)|set(self.j.side)
  await self.enter('no_matching_record_7391');assert await self.h.page.locator('.sre').count()==1
  await self.enter(good);assert await self.h.page.locator('.sri').count()>=1
  assert before==set(self.j.checkpoints)|set(self.j.side);self.negative+=1
 async def play(self,letter,full=False):
  puzzle={'1-3':('HELLO CHENMO','invalid'),'1-6':('你是下一个','invalid'),'1-12':('20120317','20000101'),'2-2':('dark.home.onion','invalid.onion')}
  while True:
   node=await self.h.page.evaluate('S.n')
   if node in ['ea','eb','ec','ed']:break
   if node in puzzle:await self.solve(node,*puzzle[node]);continue
   if node=='1-2':
    if full:
     for label in ['床头的可乐','墙上的充电器','窗户']:await self.click(label)
     await self.click('书桌上的笔记本')
    else:await self.click('笔记本电脑')
   elif node=='1-7':await self.click('私聊' if full else '头像')
   elif node=='1-9':await self.click('历史头像' if full else '等待')
   elif node=='2-3':
    obs=await self.h.observe('tor-before.png');assert not any('输入地址' in x['label'] for x in obs['elements'])
    await self.click('下载 Tor');assert not self.h.blocked
    await self.click('输入地址')
   elif node=='5-5':await self.click(letter+'.')
   else:
    if full and node in ['2-1','3-1','4-1']:await self.search({'2-1':'水塔','3-1':'镜子','4-1':'种子'}[node])
    await self.click()
  key=dict(A='peace',B='curious',C='duty',D='watch')[letter]
  assert self.j.route_endings.keys()=={key};assert self.j.score()['route_progress']==1.0;assert self.j.score()['ending_tier'] is None
  assert len(self.j.checkpoints)==1;assert len(self.j.side)==int(full)
  assert self.c.ending_reached==(letter=='D');assert len(await self.h.page.locator('.ec.u').all())==ord(letter)-ord('A')+1
  await self.h.page.screenshot(path=str(OUT/f'ending-{letter}.png'),full_page=True)
  return {'ending':key,'full_optional':full,'score':self.j.score(),'collection_score':self.c.score()}
async def main():
 OUT.mkdir(parents=True,exist_ok=True);cfg=load_config(R/f'configs/{T}.json');cfg['entry_url']=f'http://127.0.0.1:{a.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve'].update(port=a.port,ready_url=cfg['entry_url']);cfg['local_serve']['command'][-1]=str(a.port)
 s=LocalServer();h=BrowserHarness(cfg,OUT);report={'deployment_root':str(R),'kind':'engineering_ui_audit_not_model_score','coordinate_overrides':False,'state_injection':False,'page_errors':[],'http_errors':[],'requests':[],'branches':[]}
 try:
  s.start(cfg,R,OUT/'server.log');await h.start();await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);h.context.on('request',lambda r:report['requests'].append(r.url))
  audit=Audit(h);await audit.record({'op':'reset'})
  assert not audit.j.ending_reached and not audit.j.checkpoints
  await audit.click('制 作 名 单');assert await h.page.locator('#credits').is_visible();assert not audit.j.ending_reached
  await audit.click('返 回');await audit.click('开 始')
  for i,letter in enumerate('ABCD'):
   if i:
    await audit.click('重新开始');assert await h.page.evaluate('S.n')=='1-1'
    assert await h.page.locator('#ec').inner_text()=='(0)'
    audit.j=Judge.load(R/f'judge/{T}/judge.json',T,R)
   report['branches'].append(await audit.play(letter,full=i==0));print('UI ending',letter,'passed',flush=True)
  assert await h.page.locator('.he').is_visible();assert len(audit.c.route_endings)==1
  report.update(nodes=sorted(audit.nodes),negative_checks=audit.negative,trace=audit.trace)
  assert len(audit.nodes)==49,(len(audit.nodes),audit.nodes)
  assert not report['page_errors'] and not report['http_errors'] and not h.blocked
  # A new browser context is the supported full reset, including ending collection.
  await h.reset();fresh=Audit(h);await fresh.record({'op':'new_context_reset'});assert await h.page.evaluate('S.end.size')==0;assert not fresh.j.checkpoints and not fresh.j.side and not fresh.j.ending_reached;assert not fresh.c.ending_reached
  report.update(full_reset_pass=True,pass_=True)
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  report['pass']=report.pop('pass_',False);(OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('GUIJIA COMPLETE UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
