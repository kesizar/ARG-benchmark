"""Real-time UI control audit. Reads rendered-equivalent native positions, never writes state.
This is a private engineering controller, not model ability or API-latency fairness proof.
"""
import asyncio,json
from verify_sample import ROOT,OUT,args,Replay,TASK
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.serve_local import LocalServer
async def main():
 cfg=load_config(ROOT/f'configs/{TASK}-surf.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(args.port);cfg['local_serve']['port']=args.port;cfg['settle_ms']=0
 h=BrowserHarness(cfg,OUT);server=LocalServer();report={'kind':'private_source_assisted_realtime_controller_not_model_score','root':str(ROOT),'branches':[],'page_errors':[]}
 try:
  server.start(cfg,ROOT,OUT/'surf-server.log');await h.start()
  for target in ['swallowed','escaped']:
   for trial in range(8):
    h.cfg['seed']=20261026+trial+(100 if target=='escaped' else 0);await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));r=Replay(h,'surf');await r.start();trace=[];await h.page.locator('#surf-up').scroll_into_view_if_needed()
    while not r.j.ending_reached and not r.j.failure_id:
     st=await h.page.evaluate('({t:SF.t,y:SF.y,waveX:SF.waveX,score:SF.score,inv:SF.inv,over:SF.over,obs:SF.obs,lts:SF.lts})');action={'op':'wait','ms':110}
     if target=='escaped':
      from surf_planner import choose_y
      dest=choose_y(st)
      diff=dest-st['y']
      if abs(diff)>5:
       sel='#surf-down' if diff>0 else '#surf-up';loc=h.page.locator(sel);box=await loc.bounding_box();action={'op':'long_press','x':box['x']+box['width']/2,'y':box['y']+box['height']/2,'ms':max(25,min(130,int(abs(diff)/300*1000)))}
     assert await h.act(action)=='ok';await r.record(action);trace.append({'before':st,'action':action})
     if len(trace)%70==0:await h.page.screenshot(path=str(OUT/f'surf-{target}-{trial}-{len(trace)}.png'))
     assert len(trace)<900,'controller timed out'
    b=await r.finish(f'{target}-{trial}',{'controller_trace':trace,'native_final':await h.page.evaluate('({t:SF.t,score:SF.score,waveX:SF.waveX,y:SF.y})')});report['branches'].append(b);print('surf requested',target,'got',(b['score'].get('failure_id') or b['score']['route_id']),b['native_final'],flush=True)
    if (b['score'].get('failure_id') or b['score']['route_id'])==target:break
   else:raise AssertionError('Unable to reach surf outcome '+target)
  assert not report['page_errors'] and not h.blocked;report['pass']=True
 finally:
  (OUT/'surf-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
if __name__=='__main__':asyncio.run(main())
