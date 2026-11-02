import argparse,asyncio,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='zhengming-renlei'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8812);a=p.parse_args();OUT=R/'judge'/T/'verification'
class Replay:
 def __init__(self,h):self.h=h;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.trace=[];self.titles=set()
 async def record(self,action):
  await self.j.read(self.h);self.j.update(len(self.trace));title=await self.h.page.locator('#wrap h2').all_text_contents();self.titles.update(title);self.trace.append({'action':action,'title':title,'score':self.j.score()});self.h.consume_step()
 async def act(self,a,private=False):
  assert await self.h.act(a)=='ok';await self.record({**a,'text':'[test input]'} if private else a)
 async def control(self,selector):
  loc=self.h.page.locator(selector).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True)
  raw=await self.h.observe('current.png');box=await loc.bounding_box();assert box
  matching=[e for e in raw['elements'] if box['x']<=e['x']<=box['x']+box['width'] and box['y']<=e['y']<=box['y']+box['height']];assert matching,(selector,raw['elements']);return matching[0]['n']
 async def click(self,selector):await self.act({'op':'click','n':await self.control(selector)})
 async def go(self,label):await self.click('#wrap button:text-is('+json.dumps(label,ensure_ascii=False)+')');await self.h.page.wait_for_timeout(350)
 async def grids(self,mode):
  count=await self.h.page.locator('#wrap .cell').count()
  for i in (range(count) if mode==1 else [0,4] if mode==2 else []):await self.click(f'#wrap .cell:nth-child({i+1}) canvas')
 async def run(self,k):
  await self.record({'op':'reset'});assert not self.j.ending_reached
  await self.click('#startBtn');await self.h.page.wait_for_timeout(550);await self.click('#sound')
  await self.click('#wrap .checkbox');await self.h.page.wait_for_timeout(1000);await self.go('下一步')
  await self.grids(k);await self.go('确认');await self.go('继续')
  await self.grids(k);await self.go('确认');await self.go('下一步')
  await self.grids(k);await self.go('确认');await self.go('下一步')
  if k:
   n=await self.control('#wrap input');await self.act({'op':'type','n':n,'text':'deliberately_wrong_word','clear':True},private=True)
  await self.go('提交');await self.go('下一步')
  await self.click(f'#wrap .duo:nth-child({1 if k%2==0 else 2}) canvas');await self.go('继续')
  await self.grids(k);await self.go('确认');await self.go('下一步')
  identities=['是','不是','我不确定','问题本身就是答案'];fears=['屏幕','身后','记忆','它']
  await self.go(identities[k]);await self.h.page.wait_for_timeout(550);await self.go(fears[k]);await self.h.page.wait_for_timeout(600);await self.go('继续')
  assert not self.j.ending_reached and not self.j.checkpoints and not self.j.side
  await self.go('点击以证明');await self.h.page.wait_for_timeout(1100);await self.record({'op':'wait','ms':1100})
  assert self.j.ending_reached and self.j.score()['checkpoints_total']==0 and self.j.score()['route_progress']==1.0
  await self.h.page.screenshot(path=str(OUT/f'completion-{k}.png'),full_page=True)
  await self.go('继续伪装');assert self.j.ending_reached and not self.j.values['complete'] and self.j.values['mask'];assert any(e['id']=='mask' for e in self.j.events)
  assert len(self.titles)==9,(len(self.titles),self.titles)
  await self.h.page.screenshot(path=str(OUT/f'mask-{k}.png'),full_page=True)
  await self.go('重新开始');await self.h.page.wait_for_timeout(300);assert await self.h.page.locator('#intro').is_visible();fresh=Judge.load(R/f'judge/{T}/judge.json',T,R);await fresh.read(self.h);fresh.update(0);assert not fresh.ending_reached
  return {'grid_mode':['empty','all','subset','empty'][k],'word_mode':'blank' if k==0 else 'wrong','image':'A' if k%2==0 else 'B','identity':identities[k],'fear':fears[k],'titles':sorted(self.titles),'score':self.j.score(),'reload_reset_pass':True,'trace':self.trace}
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)
 s=LocalServer();h=BrowserHarness(c,OUT);report={'deployment_root':str(R),'kind':'engineering_not_model_score','coordinate_override':False,'state_injection':False,'page_errors':[],'http_errors':[],'branches':[]}
 try:
  s.start(c,R,OUT/'server.log');await h.start()
  for k in range(4):
   await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
   report['branches'].append(await Replay(h).run(k));print('Replay',k,'passed',flush=True)
  assert not h.blocked and not report['page_errors'] and not report['http_errors'];report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('ZHENGMING UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
