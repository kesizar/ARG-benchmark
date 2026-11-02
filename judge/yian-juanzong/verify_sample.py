"""Private, deterministic UI auditor. Does not invoke model APIs or inject state."""
from pathlib import Path
import argparse,asyncio,json,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='yian-juanzong';OUT=R/f'judge/{T}/verification'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8821);a=p.parse_args()
async def main():
 OUT.mkdir(parents=True,exist_ok=True);cfg=load_config(R/f'configs/{T}.json');cfg['settle_ms']=450;cfg['entry_url']=f'http://127.0.0.1:{a.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve'].update(port=a.port,ready_url=cfg['entry_url']);cfg['local_serve']['command'][-1]=str(a.port)
 h=BrowserHarness(cfg,OUT);server=LocalServer();j=None;report={'kind':'engineering_acceptance_not_model_score','page_errors':[],'http_errors':[],'routes':[]};steps=[]
 async def state():return await h.page.evaluate('JSON.parse(localStorage.getItem("anyluo_save")||"{}")')
 async def rec(action):
  await j.read(h);j.update(len(steps)+1);steps.append({'action':action,'points':len(j.checkpoints)+len(j.side),'ending':j.ending_reached});h.consume_step()
 async def click(sel):
  loc=h.page.locator(sel).first;await loc.wait_for(state='visible',timeout=10000);await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b
  assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok';await rec(sel)
 async def nav(view):await click('#nav [data-view="'+view+'"]')
 async def readall():
  await nav('archives')
  for ar in data['archives']:
   loc=h.page.locator('#arch-grid [data-arch="'+ar['id']+'"]')
   if not await loc.count() or 'locked' in (await loc.get_attribute('class') or ''):continue
   if not (await state())['archivesRead'].get(ar['id']):await click('#arch-grid [data-arch="'+ar['id']+'"]')
 async def evidence(arch):await click('#btn-evidence');await click('#modal-evidence-body [data-arch="'+arch+'"]')
 async def conclusion(correct,variant=0):
  for key,plural in [('murderer','murderers'),('motive','motives'),('method','methods')]:
   indexes=[i for i,o in enumerate(data['verdict'][plural]) if (o['id']==truth[key])==correct];await click('#opts-'+key+' .opt:nth-child('+str(indexes[variant]+1)+')')
  await click('#btn-submit-verdict')
 try:
  server.start(cfg,R,OUT/'server.log');assert server.owned;report['server_owned']=True;await h.start()
  for full in [True,False]:
   await h.reset();j=Judge.load(R/cfg['judge_path'],T,R);steps=[];h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append(r.url) if r.status>=400 else None)
   data=await h.page.evaluate('JSON.parse(JSON.stringify(CASE))');truth=await h.page.evaluate('JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(CASE.TRUTH_B64),c=>c.charCodeAt(0))))')
   if full:(OUT.parent/'checkpoint-spec.json').write_text(json.dumps({'case':data,'truth':truth,'flow':'12 independent positions (any 10) + any first evidence break unlock verdict; 3 correct submitted conclusions complete. All 9 chain levels explored in full route.','failure':'Each suspect has 40 combined chat/evidence turns. After cap, evidence also rejected; all exhausted without any break can require reset. No death ending.'},ensure_ascii=False,indent=2),encoding='utf-8')
   await rec('initial');assert not j.ending_reached;await click('#btn-start');await click('#guide-close');await nav('verdict');assert not await h.page.locator('#view-verdict').evaluate('e=>e.classList.contains("active")')
   await readall();await nav('timeline')
   order=sorted(data['events'],key=lambda e:e['correctOrder'])
   if not full:order[-2:]=reversed(order[-2:])
   for ev in order:await click('#tl-pool [data-ev="'+ev['id']+'"]')
   await click('#tl-check');await nav('verdict');assert not await h.page.locator('#view-verdict').evaluate('e=>e.classList.contains("active")');assert not j.ending_reached
   await nav('interrogation')
   for who in ([0,1,2] if full else [1]):
    person=list(data['suspects'])[who];await click('#suspect-grid .suspect-card:nth-child('+str(who+1)+')');before=(await state())['breakLevel'][person]
    await evidence('arch_011');assert (await state())['breakLevel'][person]==before;assert not j.ending_reached
    chain=data['suspects'][person]['chain'] if full else data['suspects'][person]['chain'][:1]
    for step in chain:
     await evidence(step['evidence']);before+=1;assert (await state())['breakLevel'][person]==before
     if step.get('unlock'):
      await click('#btn-exit-iv');await readall();await nav('interrogation');await click('#suspect-grid .suspect-card:nth-child('+str(who+1)+')')
    await click('#btn-exit-iv')
   if full:await readall();assert len((await state())['archivesRead'])==31
   await nav('verdict');await click('#btn-submit-verdict');assert not j.ending_reached
   for variant in range(2):await conclusion(False,variant);assert not j.ending_reached;assert not any(k in j.checkpoints for k in ['murderer','motive','method'])
   # Draft correct options cannot score before an actual submission.
   for key,plural in [('murderer','murderers'),('motive','motives'),('method','methods')]:
    idx=next(i for i,o in enumerate(data['verdict'][plural]) if o['id']==truth[key]);await click('#opts-'+key+' .opt:nth-child('+str(idx+1)+')')
   assert not any(k in j.checkpoints for k in ['murderer','motive','method']);await click('#btn-submit-verdict');assert j.ending_reached;assert j.score()['route_progress']==1.0
   await h.page.bring_to_front();obs=await h.observe('full-ending.png' if full else 'minimal-ending.png');assert '案件告破' in obs['visible_text']
   st=await state();await h.page.reload();await rec('reload');assert (await state())['breakLevel']==st['breakLevel'];assert (await state())['verdict']==st['verdict']
   report['routes'].append({'full_optional':full,'steps':steps.copy(),'score':j.score(),'timeline_correct':12 if full else 10,'chains':st['breakLevel'],'archives_read':len(st['archivesRead']),'wrong_evidence_checks':3 if full else 1,'wrong_final_option_checks':6,'resume_verified':True})
  # Real in-game reset and new-trial evaluator reset.
  await click('#btn-start');await click('#btn-refresh');await click('#confirm-ok');assert not await h.page.evaluate('localStorage.getItem("benchmark_yian_verdict")');assert not (await state()).get('started');report['in_game_reset_verified']=True
  await h.reset();j=Judge.load(R/cfg['judge_path'],T,R);steps=[];await rec('new_context');assert not j.checkpoints and not j.side and not j.ending_reached;report['new_context_reset_verified']=True
  await click('#btn-start');await click('#guide-close');await click('#arch-grid [data-arch="arch_001"]');await nav('timeline');await click('#tl-pool [data-ev="ev_001"]');await nav('interrogation');await click('#suspect-grid .suspect-card:nth-child(1)')
  for _ in range(40):await click('#quick-asks button:first-child')
  assert (await state())['turns']['王建国']==40
  await evidence('arch_001');st=await state();assert st['breakLevel']['王建国']==0 and st['turns']['王建国']==40 and not j.ending_reached;report['forty_turn_evidence_lock_verified']=True
  report['blocked_requests']=h.blocked;assert not h.blocked and not report['page_errors'] and not report['http_errors'];report['pass']=True
 except Exception as e:
  report['failure']=str(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('YIAN ACCEPTANCE PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
