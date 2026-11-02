"""Private source-informed replay; only real numbered UI controls, no state injection."""
import argparse,asyncio,json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='laopengyou'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8812);p.add_argument('--minimal-only',action='store_true');a=p.parse_args();OUT=R/'judge'/T/'verification';G=json.loads((R/f'judge/{T}/private-quiz.json').read_text(encoding='utf-8'))
class Audit:
 def __init__(self,h):self.h=h;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.trace=[];self.views=set();self.materials=[];self.negative=0
 async def record(self,action):
  await self.j.read(self.h);new=self.j.update(len(self.trace));view=await self.h.page.locator('.view.active').get_attribute('id');self.views.add(view);self.trace.append({'action':action,'view':view,'new':new,'score':self.j.score()});self.h.consume_step()
 async def act(self,a,private=False):
  assert await self.h.act(a)=='ok';await self.record({**a,'text':'[private test input]'} if private else a)
 async def ctrl(self,sel):
  loc=self.h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True)
  raw=await self.h.observe('current.png');b=await loc.bounding_box();assert b
  es=[e for e in raw['elements'] if b['x']<=e['x']<=b['x']+b['width'] and b['y']<=e['y']<=b['y']+b['height']];assert es,(sel,raw['elements']);return es[0]['n']
 async def click(self,sel):await self.act({'op':'click','n':await self.ctrl(sel)})
 async def type(self,sel,text,enter=False):await self.act({'op':'type','n':await self.ctrl(sel),'text':text,'clear':True,'enter':enter},private=True)
 async def nav(self,to):await self.click('.view.active [data-goto='+json.dumps(to)+']')
 async def material(self,key):
  text=await self.h.page.locator('.view.active').inner_text();assert text.strip();self.materials.append({'key':key,'characters':len(text),'text_sha256':hashlib.sha256(text.encode()).hexdigest()})
 async def login(self,app,inputs,button,view):
  before=set(self.j.checkpoints)|set(self.j.side)
  for sel,_ in inputs:await self.type(sel,'invalid')
  await self.click(button)
  if app=='wechat':assert await self.h.page.locator('#modal-wechat-wrong.show').count();await self.click('#modal-wechat-wrong-ok')
  assert before==set(self.j.checkpoints)|set(self.j.side);assert not self.j.ending_reached;self.negative+=1
  for sel,val in inputs:await self.type(sel,val)
  await self.click(button);assert await self.h.page.locator('#'+view+'.active').count()==1
 async def room(self,full):
  await self.record({'op':'reset'});assert not self.j.checkpoints and not self.j.side and not self.j.ending_reached
  await self.click('#btn-unlock');assert not self.j.ending_reached;await self.click('#modal-death-ok')
  if full:
   await self.nav('view-guide');await self.material('guide');await self.nav('view-home')
   await self.nav('view-memo')
   for i in range(await self.h.page.locator('#memo-list .memo-item').count()):
    await self.click(f'#memo-list .memo-item:nth-child({i+1})');await self.material('memo:'+str(i));await self.nav('view-memo')
   await self.nav('view-home');await self.nav('wechat-entry')
   await self.login('wechat',[('#wechat-pwd','xiangyungui')],'#wechat-login-btn','view-wechat-main')
   ids=await self.h.page.locator('#wechat-msg-list .wechat-list-item').evaluate_all('(es)=>es.map(e=>e.dataset.chat)')
   for id in ids:
    await self.click('#wechat-msg-list [data-chat='+json.dumps(id)+']');await self.material(id);await self.nav('view-wechat-main')
   await self.click('#view-wechat-main [data-tab="wechat-moments"]');await self.material('moments');await self.nav('view-home');await self.nav('qq-entry')
   await self.login('qq',[('#qq-account','728163549'),('#qq-pwd','20010177')],'#qq-login-btn','view-qq-main')
   for id in await self.h.page.locator('#view-qq-main .qq-list-item').evaluate_all('(es)=>es.map(e=>e.dataset.chat)'):
    await self.click('#view-qq-main [data-chat='+json.dumps(id)+']');await self.material(id);await self.nav('view-qq-main')
   await self.nav('view-home');await self.type('#search-input','unknown_keyword_7391',True);assert '未找到结果' in await self.h.page.locator('#search-result-body').inner_text();assert not self.j.ending_reached;self.negative+=1;await self.nav('view-home')
   keys=json.loads((R/f'judge/{T}/flow.json').read_text(encoding='utf-8'))['search_keys']
   for key in keys:
    await self.type('#search-input',key,True);await self.material('search:'+key)
    if key=='校园论坛':
     await self.click('#search-result-body [data-forum-tab="forum-me"]')
     for secret,modal in [('forget','modal-forget-me'),('love','modal-you-are-me')]:
      await self.click('#search-result-body [data-secret='+json.dumps(secret)+']');assert await self.h.page.locator('#'+modal+'.show').count();await self.click('#'+modal+'-ok')
     await self.click('#search-result-body [data-forum-tab="forum-home"]')
    await self.nav('view-home')
  await self.nav('view-settings');await self.click('#btn-advanced')
  for i in range(3):await self.type('#sys-name','invalid');await self.type('#sys-pwd','invalid');await self.click('#btn-do-switch');assert 'system' not in self.j.checkpoints
  assert await self.h.page.locator('#modal-forum-hint.show').count();self.negative+=3;await self.click('#modal-forum-hint-ok');await self.click('#btn-advanced');await self.type('#sys-name','nijiushiwo');await self.type('#sys-pwd','yaoaiziji');await self.click('#btn-do-switch');assert 'system' in self.j.checkpoints
  if full:
   await self.nav('view-sub-memo')
   for i in range(await self.h.page.locator('#sub-memo-list .memo-item').count()):
    await self.click(f'#sub-memo-list .memo-item:nth-child({i+1})');await self.material('sub-memo:'+str(i));await self.nav('view-sub-memo')
   await self.nav('view-sub-home');await self.nav('view-sub-diary');await self.login('diary',[('#diary-pwd','20200723')],'#diary-login-btn','view-sub-diary')
   for i in range(await self.h.page.locator('#sub-diary-list details').count()):await self.click(f'#sub-diary-list details:nth-child({i+1}) summary');await self.material('diary:'+str(i))
   await self.nav('view-sub-home');await self.nav('view-sub-qq');await self.login('subqq',[('#sub-qq-account','236678219'),('#sub-qq-pwd','565565565')],'#sub-qq-login-btn','view-sub-qq-main')
   for id in await self.h.page.locator('#view-sub-qq-main .qq-list-item').evaluate_all('(es)=>es.map(e=>e.dataset.chat)'):
    await self.click('#view-sub-qq-main [data-chat='+json.dumps(id)+']');await self.material(id);await self.nav('view-sub-qq-main')
   await self.nav('view-sub-home')
  await self.nav('view-sub-submit');await self.click('#quiz-submit-btn');assert not self.j.ending_reached and len(self.j.checkpoints)==1;self.negative+=1
 async def option(self,qi,oi):await self.click(f'#sub-submit-body .quiz-option[data-qi="{qi}"][data-oi="{oi}"]')
 async def pair(self,qi,li,ri):
  await self.click(f'.pair-name[data-qi="{qi}"][data-left="{li}"]');await self.click(f'.pair-opt[data-qi="{qi}"][data-right="{ri}"]')
 async def answer(self):
  for i,q in enumerate(G):
   if q.get('type')=='pair':
    for li,ri in q['correct'].items():await self.pair(i,li,ri)
   elif q.get('type')=='multi':
    for ri in q['correct']:await self.option(i,ri)
   else:await self.option(i,q['correct'])
  # Unsubmitted answers must earn no quiz points.
  assert len(self.j.checkpoints)==1
  await self.option(0,0);await self.click('#quiz-submit-btn');assert self.j.values['wrong_quiz'] and 'quiz_1' not in self.j.checkpoints and not self.j.ending_reached;assert len(self.j.checkpoints)==8;self.negative+=1;await self.click('#modal-quiz-wrong-ok');await self.option(0,G[0]['correct'])
  # Wrong pair, missing multi, extra multi all rejected, independently of latching.
  await self.pair(2,0,0);await self.click('#quiz-submit-btn');assert self.j.values['wrong_quiz'] and not self.j.values['quiz_3'] and not self.j.ending_reached;self.negative+=1;await self.click('#modal-quiz-wrong-ok');await self.pair(2,0,G[2]['correct']['0'])
  await self.option(7,4);await self.click('#quiz-submit-btn');assert self.j.values['wrong_quiz'] and not self.j.values['quiz_8'] and not self.j.ending_reached;self.negative+=1;await self.click('#modal-quiz-wrong-ok');await self.option(7,4)
  await self.option(7,1);await self.click('#quiz-submit-btn');assert self.j.values['wrong_quiz'] and not self.j.values['quiz_8'] and not self.j.ending_reached;self.negative+=1;await self.click('#modal-quiz-wrong-ok');await self.option(7,1)
  await self.click('#quiz-submit-btn');assert self.j.values['quiz_pass'] and len(self.j.checkpoints)==9 and not self.j.ending_reached
 async def run(self,full):
  await self.room(full);await self.answer();choice='yes' if full else 'no';route='wish' if full else 'accept';await self.click('#modal-revive-'+choice);assert self.j.ending_reached and route in self.j.route_endings;assert self.j.score()['ending_tier'] is None and self.j.score()['route_progress']==1.0;assert len(self.j.side)==(4 if full else 0)
  await self.h.page.screenshot(path=str(OUT/f'ending-{route}.png'))
  await self.click('#modal-revive-'+choice+'-agree');assert await self.h.page.locator('#modal-creator.show').count();await self.click('#modal-creator-ok');assert self.j.ending_reached
  return {'path':'full_materials_wish' if full else 'minimal_mechanical_accept','views':sorted(self.views),'materials':self.materials,'negative_checks':self.negative,'score':self.j.score(),'trace':self.trace}
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)
 s=LocalServer();h=BrowserHarness(c,OUT);report={'deployment_root':str(R),'kind':'engineering_not_model_score','state_injection':False,'coordinate_override':False,'page_errors':[],'http_errors':[],'branches':[]}
 try:
  s.start(c,R,OUT/'server.log');await h.start()
  for full in ([False] if a.minimal_only else [True,False]):
   await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);report['branches'].append(await Audit(h).run(full));print('Path passed',full,flush=True)
  if not a.minimal_only:assert len(report['branches'][0]['views'])==23
  await h.reset();fresh=Audit(h);await fresh.record({'op':'new_context_reset'});assert not fresh.j.checkpoints and not fresh.j.side and not fresh.j.ending_reached
  assert not h.blocked and not report['page_errors'] and not report['http_errors'];report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('LAOPENGYOU UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
