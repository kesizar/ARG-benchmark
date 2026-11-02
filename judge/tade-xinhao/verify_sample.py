import argparse,asyncio,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='tade-xinhao'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8831);p.add_argument('--game-root');p.add_argument('--out',default=str(R/'runs'/T/'partial-ui'));a=p.parse_args();OUT=Path(a.out);OUT.mkdir(parents=True,exist_ok=True)
async def main():
 c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)

 if a.game_root:c['local_serve']['command'][3]=str(Path(a.game_root).resolve())
 s=LocalServer();h=BrowserHarness(c,OUT);report={'scope':'PARTIAL ONLY: first gate wrong/right and UI reset. Endpoint unit checks bypass normal progression and are NOT full-route acceptance.','root':str(R),'port':a.port,'trace':[],'errors':[]}
 j=Judge.load(R/f'judge/{T}/judge.json',T,R)
 async def rec(label):
  await j.read(h);j.update(len(report['trace']));report['trace'].append({'action':label,'values':dict(j.values),'score':j.score()});h.consume_step()
 async def act(v):
  assert await h.act(v)=='ok',v
  await rec({k:('[private QA input]' if k=='text' else x) for k,x in v.items()})
 async def control(sel):
  loc=h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);o=await h.observe('current.png');b=await loc.bounding_box();m=[e for e in o['elements'] if b['x']<=e['x']<=b['x']+b['width'] and b['y']<=e['y']<=b['y']+b['height']];assert m,sel;return m[0]['n']
 async def click(sel):await act({'op':'click','n':await control(sel)})
 async def submit(v):
  await click('[data-cmd="verify"]');await act({'op':'type','n':await control('#cmd-input'),'text':v,'clear':True});await act({'op':'key','key':'Enter'})
 try:
  s.start(c,R,OUT/'server.log');await h.start();await h.reset();h.page.on('pageerror',lambda e:report['errors'].append(str(e)));await rec('fresh');assert not any(j.values.values())
  await click('#introHelpBtn');assert '共有5个结局' in await h.page.locator('#intro-help-panel').inner_text();await click('#introCloseHelpBtn');await h.page.wait_for_timeout(800)
  await click('[data-cmd="probe"]');await h.page.wait_for_timeout(900)
  for k in range(3):
   await h.page.locator('#signalViewport iframe').wait_for();await h.page.screenshot(path=str(OUT/f'node07-clue-{k}.png'))
   if k<2:await click('#signalNext')
  await click('#signalClose');await submit('错误地点');assert not j.values['place_07'];assert not j.ending_reached
  await submit('宜阳');assert j.values['place_07'];assert not j.ending_reached;assert j.score()['checkpoints_total']==0
  await h.page.screenshot(path=str(OUT/'first-gate-positive.png'));await click('[data-cmd="reset"]');assert h.pending;await act({'op':'dialog','accept':True});await h.page.wait_for_timeout(700)
  fresh=Judge.load(R/f'judge/{T}/judge.json',T,R);await fresh.read(h);fresh.update(0);assert not any(fresh.values.values());assert await h.page.locator('#terminal-intro').is_visible();report['ui_reset']=True
  # Judge-only endpoint unit tests; deliberately excluded from route completion evidence.
  report['endpoint_units']=[]
  for i,f in enumerate(['cache-a91f.html','cache-b42d.html','cache-c08e.html','cache-d64c.html','cache-f7b2.html'],1):
   await h.page.goto(f'http://127.0.0.1:{a.port}/assets/{f}');unit=Judge.load(R/f'judge/{T}/judge.json',T,R);await unit.read(h);unit.update(0);assert unit.values[f'E{i:02}'];report['endpoint_units'].append({'id':f'E{i:02}','recognized':True,'direct_navigation':True})
  report.update(partial_pass=True,full_route_acceptance=False,blocked_requests=h.blocked,request_count=len(h.all_requests));assert not h.blocked;assert not report['errors'];print('PARTIAL UI PASS',a.port,flush=True)
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');await h.close();s.stop()
if __name__=='__main__':asyncio.run(main())
