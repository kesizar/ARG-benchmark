"""Supplemental normal UI coverage; private source reads choose tests, never mutate game."""
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_sample import Replay,R,T,OUT,a,BrowserHarness,load_config,LocalServer
async def main():
 c=load_config(R/f'configs/{T}.json');c['seed']=1;c['settle_ms']=50;c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)
 s=LocalServer();h=BrowserHarness(c,OUT);report={'normal_ui':True,'state_injection':False,'coverage':{}}
 try:
  s.start(c,R,OUT/'exploration-server.log');await h.start();r=Replay(h)
  if a.donation_only:
   report=json.loads((OUT/'exploration-panels-complete.json').read_text(encoding='utf-8'));report.pop('failure',None);report['prior_panels_evidence']='exploration-panels-complete.json; completion only adds intro donation check';await h.reset();await r.click('button[onclick="openDonate()"]');report['donation_missing']=await h.page.locator('#donateMask img').evaluate('(e)=>!e.complete || e.naturalWidth===0');await r.save('donation-soft-missing');report['pass']=True;return
  for _ in range(30):
   await r.reset()
   if await h.page.evaluate('CORE.includes(state.killer)'):break
  else:raise AssertionError('No core killer in30 fresh random draws')
  report['wechat_condition']='standard harness seed1 gives core killer; peripheral undefined-message source defect remains';report['harness_random_seed']=1
  if a.quick:
   prior=json.loads((OUT/'exploration-notes-complete.json').read_text(encoding='utf-8'));report['coverage'].update(prior['coverage']);report['notes']=prior['notes'];report['prior_notes_evidence']='exploration-notes-complete.json + all-notes.json';await r.collect()
  for i in range(0 if a.quick else 18):
   await r.person(i);qs=await h.page.evaluate(f'PEOPLE[ALL_PEOPLE[{i}]].talk?.map((q,i)=>!q.hot?i:null).filter(i=>i!==null)||[]')
   for q in qs:await r.click(f'#pOpts button:nth-child({q+1})')
   if not qs:await r.click('#pOpts button:nth-child(1)')
   await r.click('#pActions .sr');await r.close('panePerson')
  if not a.quick:
   await r.click('button[onclick="openScenes()"]')
   for scene in [3,2]:
    await r.click(f'#sceneMap .card:nth-child({scene+1})');await r.click('#sceneDetail .sitem')
   await r.close('paneScenes');assert not r.j.checkpoints
   rules=await h.page.evaluate('misleadDone');assert len(rules)==4,rules;report['coverage']['misleads']=rules
   await r.click('button[onclick="openNotes()"]');report['notes']=await h.page.locator('#noteList .nitem').count();await r.save('all-notes');await r.close('paneNotes')
  await r.click('button[onclick="openWeb()"]')
  edges=await h.page.locator('#webSvg .wlink').count();edge_details=[]
  for i in range(edges):
   line=h.page.locator(f'#webSvg .wlink[data-link="{i}"]');await line.scroll_into_view_if_needed()
   point=await line.evaluate('''e=>{const x1=+e.getAttribute('x1'),x2=+e.getAttribute('x2'),y1=+e.getAttribute('y1'),y2=+e.getAttribute('y2');for(let t=.15;t<.9;t+=.05){const p=new DOMPoint(x1+(x2-x1)*t,y1+(y2-y1)*t).matrixTransform(e.getScreenCTM());if(document.elementFromPoint(p.x,p.y)===e)return {x:p.x,y:p.y};}return null;}''')
   if point:
    assert await h.act({'op':'click',**point})=='ok';await r.read({'relation_line':i,'point':point});edge_details.append({'index':i,'clicked':True,'text':await h.page.locator('#webSide').inner_text()})
   else:edge_details.append({'index':i,'clicked':False,'reason':'no exposed line point; zero-length, overlapped or clipped original geometry'})
  await r.save('relationships');await r.close('paneWeb');report['coverage']['relation_edges']=edge_details
  await r.click('button[onclick="openWx()"]')
  for i in range(5):
   await r.click(f'#wxBody .wx-chat:nth-child({i+1})');await r.save(f'chat-{i}');await r.click('#wxBody .wx-back')
  await r.close('paneWx');report['coverage']['wechat_chats']=5
  # Explicitly target actual killer; this source read selects the test case only.
  idx=await h.page.evaluate('ALL_PEOPLE.indexOf(state.killer)');await r.accuse(idx)
  for _ in range(5):await r.answer()
  assert r.j.ending_reached and r.j.values['genuine'];await r.save('genuine-confirmed');report['coverage']['genuine_killer_win']=True
  # A default clock decreases in real time, separate from ?test expiry coverage.
  await r.reset();before=await h.page.locator('#clock').inner_text();await h.page.wait_for_timeout(2200);after=await h.page.locator('#clock').inner_text();assert before!=after and after.startswith('59:');report['default_clock']={'before':before,'after':after,'elapsed_wait_ms':2200,'full_hour_expiry_verified':False}
  # Donation soft asset failure is observed through its normal UI.
  await h.page.reload();await r.click('button[onclick="openDonate()"]');await h.page.wait_for_timeout(100);report['donation_missing']=await h.page.locator('#donateMask img').evaluate('(e)=>!e.complete || e.naturalWidth===0');await r.save('donation-soft-missing');report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/'exploration-failure.png'),full_page=True)
  raise
 finally:
  (OUT/'exploration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('exploration passed',flush=True)
if __name__=='__main__':asyncio.run(main())
