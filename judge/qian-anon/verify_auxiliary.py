"""UI restart/numbered-entry acceptance for pending asynchronous phases."""
import asyncio,json
from verify_sample import ROOT,OUT,args,Replay,TASK
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.serve_local import LocalServer
async def main():
 cfg=load_config(ROOT/f'configs/{TASK}-quiz.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(args.port);cfg['local_serve']['port']=args.port;cfg['settle_ms']=10;h=BrowserHarness(cfg,OUT);server=LocalServer();report={'checks':{},'root':str(ROOT)}
 try:
  server.start(cfg,ROOT,OUT/'aux-server.log');await h.start();await h.reset();entry=None
  for i in range(5):
   obs=await h.observe(f'aux-hub-{i}.png');entry=next((e for e in obs['elements'] if '日谜对对碰' in e['label'] or '开始互砸' in e['label']),None)
   if entry:break
   await h.act({'op':'scroll','dy':400})
  assert entry,obs['elements'];assert await h.act({'op':'click','n':entry['n']})=='ok';assert await h.page.locator('#quiz-hand .q-card').count()==5;report['checks']['numbered_quiz_entry']=True
  r=Replay(h,'quiz');await r.record({'op':'existing_entry'});await r.click('#quiz-hand .q-card');await r.click('#quiz-throw');await r.click('#screen-quiz [onclick="show(\'hub\')"]');await r.click('button.card[onclick*="show(\'quiz\')"]');await r.wait(1200);assert await h.page.evaluate('QZ.round===1&&QZ.ps===0&&QZ.rs===0');assert await h.page.locator('#quiz-hand .q-card').count()==5;report['checks']['quiz_retired_phase_does_not_advance_new_round']=True
  await h.reset();r=Replay(h,'cross');await r.start();await r.click('[onclick="crossStumble(true)"]');await r.click('#screen-cross [onclick="show(\'hub\')"]');await r.click('button.card[onclick*="show(\'cross\')"]');await r.wait(1000);assert await h.page.evaluate('CX.aPos===0&&CX.sPos===0&&CX.turn===1&&!CX.busy');report['checks']['cross_retired_foe_timer_does_not_advance_new_round']=True
  await h.reset();r=Replay(h,'gal');await r.record({'op':'fresh_context'});assert not r.j.ending_reached and not r.j.checkpoints and not r.j.side and not await h.local_storage();report['checks']['fresh_context_has_no_stale_judge_or_saved_best']=True;assert not h.blocked;report['pass']=True
 finally:
  (OUT/'auxiliary-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('auxiliary passed')
if __name__=='__main__':asyncio.run(main())
