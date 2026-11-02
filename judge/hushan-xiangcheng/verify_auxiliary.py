"""Numbered observations, Enter submission, pending timer reset, fresh context."""
import asyncio,hashlib,json
from verify_sample import ROOT,OUT,args,Replay,IOL,TASK
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.serve_local import LocalServer
async def main():
 cfg=load_config(ROOT/f'configs/{TASK}-iol.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['port']=args.port;cfg['local_serve']['command'][-1]=str(args.port);cfg['settle_ms']=40
 server=LocalServer();h=BrowserHarness(cfg,OUT);r={'checks':{},'root':str(ROOT),'model_api_used':False}
 try:
  server.start(cfg,ROOT,OUT/'aux-server.log');await h.start();await h.reset();entry=None
  for attempt in range(5):
   obs=await h.observe(f'aux-hub-{attempt}.png');entry=next((e for e in obs['elements'] if 'IOL' in e['label'] or '开始推规律' in e['label']),None)
   if entry:break
   await h.act({'op':'scroll','dy':500})
  assert entry,obs['elements'];assert await h.act({'op':'click','n':entry['n']})=='ok';assert await h.page.locator('#screen-iol.on').count()==1;r['checks']['numbered_hub_entry']=True
  replay=Replay(h,'iol');await replay.read({'op':'begin_existing_ui'});await replay.type(IOL[0]['answer_private']);assert await h.act({'op':'key','key':'Enter'})=='ok';await replay.read({'op':'key','key':'Enter'});assert len(replay.j.checkpoints)==1 and await h.page.evaluate('IOL.score')==1;r['checks']['enter_submission_scores_exactly_once']=True
  await replay.click('[onclick="iolCheck()"]',unscored=True);assert await h.page.evaluate('IOL.score')==1;r['checks']['duplicate_submit_native_score_unchanged']=True
  await replay.click('#screen-iol [onclick="show(\'hub\')"]');await replay.click('button.card[onclick*="show(\'iol\')"]');await replay.wait(1700);assert await h.page.evaluate('IOL.lv===0 && IOL.q===0 && IOL.score===0');r['checks']['restart_cancels_old_advance_timer']=True
  await h.reset();fresh=Replay(h,'iol');await fresh.read({'op':'new_context'});assert not fresh.j.checkpoints and not fresh.j.side and not await h.local_storage();assert await h.page.locator('#screen-hub.on').count()==1;r['checks']['fresh_episode_empty_storage_and_judge']=True
  r['runtime_hashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['harness/observe.py','harness/browser_harness.py','harness/judge.py']};assert not h.blocked;r['pass']=True
 finally:
  (OUT/'auxiliary-acceptance.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('auxiliary checks passed')
if __name__=='__main__':asyncio.run(main())
