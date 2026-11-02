import argparse,asyncio,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='liushi-fenzhong'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8812);p.add_argument('--quick',action='store_true');p.add_argument('--donation-only',action='store_true');p.add_argument('--start-target',type=int,default=0);a=p.parse_args();OUT=R/'judge'/T/'verification'/'closeout';OUT.mkdir(parents=True,exist_ok=True)
class Replay:
 def __init__(self,h):self.h=h;self.trace=[];self.j=Judge.load(R/f'judge/{T}/judge.json',T,R)
 async def read(self,label):
  await self.j.read(self.h);self.j.update(len(self.trace));self.trace.append({'action':label,'score':self.j.score(),'values':dict(self.j.values)})
 async def click(self,selector):
  loc=self.h.page.locator(selector).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);raw=await self.h.observe('current.png');box=await loc.bounding_box();assert box
  match=[e for e in raw['elements'] if box['x']<=e['x']<=box['x']+box['width'] and box['y']<=e['y']<=box['y']+box['height']]
  action={'op':'click','n':match[0]['n']} if match else {'op':'click','x':round(box['x']+box['width']/2),'y':round(box['y']+box['height']/2)}
  assert await self.h.act(action)=='ok';await self.read({'selector':selector,'action':action,'reason':'visible coordinate fallback when observation 80-element cap omits target' if not match else 'observed index'});self.h.consume_step()
 async def reset(self,test=False):
  await self.h.reset()
  if test:await self.h.page.goto(self.h.cfg['entry_url']+'?test')
  self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.trace=[];await self.read('fresh context');assert not self.j.ending_reached and not self.j.checkpoints
  await self.click('#btnStart');assert await self.h.page.locator('#clock').inner_text() in ['60:00','59:59','01:30','01:29'];return self
 async def person(self,i):await self.click(f'#sceneGrid .card:nth-child({i+1})')
 async def close(self,pane):await self.click('#'+pane+' .x')
 async def collect(self):
  # Two distinct first searches, ordinary UI. No state setters or solution actions.
  for i in [0,1]:await self.person(i);await self.click('#pActions .sr');await self.close('panePerson')
 async def accuse(self,i):await self.person(i);await self.click('#pActions .acc')
 async def answer(self,wrong=False):
  # Private oracle derived from audited source; source never added to model-visible observation.
  n=await self.h.page.evaluate('quizData[quizStep].opts.findIndex(x=>x'+('!==' if wrong else '===')+'quizData[quizStep].a)')
  await self.click(f'#quizOpts button:nth-child({n+1})')
 async def save(self,name):
  await self.h.page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
  (OUT/(name+'.json')).write_text(json.dumps(self.trace,ensure_ascii=False,indent=2),encoding='utf-8')
async def main():
 c=load_config(R/f'configs/{T}.json');c['settle_ms']=50;c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)
 s=LocalServer();h=BrowserHarness(c,OUT);report={'root':str(R),'normal_ui':'harness.observe element index and harness.act click, no state mutation','answer_oracle':'private quizData read used only by verification','clock':'real wall-clock, no Date/performance/setInterval monkeypatch or Playwright clock','full_3600second_expiry_verified':False,'page_errors':[],'http_errors':[],'cases':[]}
 try:
  s.start(c,R,OUT/'server.log');await h.start();r=Replay(h)
  async def fresh(test=False):
   await r.reset(test);h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda x:report['http_errors'].append({'url':x.url,'status':x.status}) if x.status>=400 else None)
  # All 18 targets and five exact answer gates, including knowingly non-killer targets.
  if a.start_target:
   prefixpath=OUT/('prefix-18-fatal-seed-failure.json' if a.start_target==18 else 'prefix-16.json');prefix=json.loads(prefixpath.read_text(encoding='utf-8'));report['cases']=[x for x in prefix['cases'] if 'target_index' in x];report['prefix_evidence']=prefixpath.name;report['next_memory']=json.loads((OUT/'prefix-16.json').read_text(encoding='utf-8')).get('next_memory');report['resumed_after']='Observer80-element cap fixed by visible coordinate clicks; fatal hot branch uses standard harness seed1 instead of repeatedly resetting the same deterministic seed.'
  for i in range(a.start_target,1 if a.quick else 18):
   await fresh();await r.collect();await r.accuse(i)
   for k in range(5):await r.answer();assert len(r.j.checkpoints)==0 and len(r.j.side)==k+1
   assert r.j.ending_reached;kind='genuine' if r.j.values['genuine'] else 'bypass';assert r.j.values[kind]
   report['cases'].append({'target_index':i,'ending':kind,'score':r.j.score()});await r.save(f'win-{i:02}')
   if i==0:
    await r.click('#btnConfirm');assert r.j.values['twist'] and r.j.ending_reached;await r.save('twist')
    await r.click('#btnNext');await r.click('#btnStart');before=await h.page.locator('#roundInfo').inner_text();assert '第 2 世' in before
    report['next_memory']=await h.page.evaluate('({round:state.round,scenario:state.scen,confirm:state.confirmN,notes:state.notes.length,confirmed:!!window._confirmed})')
  # Wrong answer at every depth: only earlier answers score, target becomes locked.
  for depth in range(5):
   await fresh();await r.collect();await r.accuse(0)
   for k in range(depth):await r.answer()
   await r.answer(True);assert len(r.j.checkpoints)==0 and len(r.j.side)==depth and not r.j.ending_reached and r.j.values['failed'];await r.person(0)
   assert '不再信任' in await h.page.locator('#pOpts').inner_text();assert await h.page.locator('#pActions .acc').count()==0
   await r.save(f'failure-q{depth+1}');report['cases'].append({'wrong_question':depth+1,'points':len(r.j.checkpoints),'locked':True})
  # The main list requires five notes, while person shortcut accepts two.
  await fresh();await r.click('button[onclick="openAccuse()"]');await r.click('#accGrid .card:nth-child(1)');assert not await h.page.locator('#paneQuiz').is_visible();await r.close('paneAccuse');report['cases'].append({'zero_notes_main_list_block':True})
  # Trigger fatal hot question by observing randomly chosen killer and choosing core on a fresh draw if necessary.
  h.cfg['seed']=1;report['fatal_hot_branch_seed']=1
  for _ in range(30):
   await fresh();idx=await h.page.evaluate('ALL_PEOPLE.indexOf(state.killer)')
   if idx<6:break
  else:raise AssertionError('No core killer after 30 random draws')
  await r.person(idx);hot=await h.page.evaluate('PEOPLE[state.killer].talk.findIndex(x=>x.hot)');await r.click(f'#pOpts button:nth-child({hot+1})');await h.page.wait_for_timeout(1600);await r.read('real 1600ms wait');assert r.j.values['stir'] and r.j.failure_id=='stir' and not r.j.ending_reached;await r.save('death-stir')
  # All seven scene items in two separate lives, including both hall items.
  for indexes in [[(0,0),(0,1),(1,0),(3,0),(2,0)],[(4,0),(5,0),(0,0)]]:
   await fresh();await r.click('button[onclick="openScenes()"]')
   for scene,item in indexes:
    await r.click(f'#sceneMap .card:nth-child({scene+1})');await r.click(f'#sceneDetail .sitem:nth-of-type({item+1})')
   await h.page.wait_for_timeout(2000);await r.read('real 2000ms wait');assert r.j.values['alert'] and r.j.failure_id=='alert' and not r.j.ending_reached
   await r.save('death-alert-'+str(indexes[0][0]))
  # Original test parameter, real elapsed >90s. Timed messages and timeout observed in ordinary UI.
  await fresh(True);started=time.monotonic();await r.click('button[onclick="openWx()"]');await r.click('#wxBody .wx-chat:nth-child(3)');await r.save('wechat-initial');await r.close('paneWx')
  while time.monotonic()-started<92:await h.page.wait_for_timeout(1000)
  await r.read('real 92 seconds elapsed');assert r.j.values['timeup'] and r.j.failure_id=='timeup' and not r.j.ending_reached
  report['timer_test']={'query':'?test','nominal_seconds':90,'elapsed_seconds':round(time.monotonic()-started,3),'clock':await h.page.locator('#clock').inner_text(),'chat_trigger_ids':await h.page.evaluate('wxState.done'),'killer_message_sent':await h.page.evaluate('wxState.killerSent')};await r.save('death-timeup-test90')
  # Full reload resets everything, including private globals and scoring.
  await fresh();assert await h.page.evaluate('state.round===1 && state.deaths===0 && state.notes.length===0 && state.alert===0 && !window._confirmed');report['reset_pass']=True
  report['pass']=True;assert not h.blocked and not report['page_errors'],report['page_errors']
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'),full_page=True)
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('LIUSHI UI PASS',len(report['cases']),flush=True)
if __name__=='__main__':asyncio.run(main())
