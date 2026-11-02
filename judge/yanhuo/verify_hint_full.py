"""Private auditor UI replay, no model calls or in-page state injection."""
from pathlib import Path
import argparse,asyncio,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8821);a=p.parse_args();OUT=ROOT/'judge/yanhuo/verification'
async def main():
 OUT.mkdir(parents=True,exist_ok=True);cfg=load_config(ROOT/'configs/yanhuo.json');cfg['settle_ms']=80;cfg['entry_url']=f'http://127.0.0.1:{a.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve'].update(port=a.port,ready_url=cfg['entry_url']);cfg['local_serve']['command'][-1]=str(a.port)
 h=BrowserHarness(cfg,OUT);server=LocalServer();j=Judge.load(ROOT/cfg['judge_path'],'yanhuo',ROOT);report={'kind':'engineering_acceptance_not_model_score','steps':[],'page_errors':[],'http_errors':[],'negative_checks':0,'partial_checks':0,'books_visited':[]}
 async def record(label):
  await j.read(h);j.update(len(report['steps'])+1);report['steps'].append({'action':label,'checkpoints':len(j.checkpoints),'ending':j.ending_reached});h.consume_step()
 async def click(sel):
  loc=h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b
  r=await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2});assert r=='ok',(sel,r);await record(sel)
 async def state():return await h.page.evaluate('JSON.parse(JSON.stringify(S))')
 async def choose(it,pair):
  await click('[data-verify="'+it['id']+'"]');await click('[data-book="'+pair['book']+'"]');await click('[data-entry="'+pair['entry']+'"]')
 async def slot(sl,correct,variant=0):
  opts=await h.page.locator('[data-slot="'+sl['id']+'"]').count();idx=[i for i,o in enumerate(sl['opts']) if o['ok']==correct][variant]
  assert opts==3;await click('[data-slot="'+sl['id']+'"]:nth-child('+str(idx+1)+')')
 try:
  server.start(cfg,ROOT,OUT/'closeout-server.log');assert server.owned;report['server_owned']=True;await h.start();await h.reset()
  h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append(r.url) if r.status>=400 and not r.url.endswith('/favicon.ico') else None)
  data=await h.page.evaluate('({items:ITEMS,slots:SLOTS,books:BOOKS})');(OUT/'closeout-spec.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  await record('initial');assert not j.checkpoints and not j.side and not j.ending_reached;await click('#btn-start');assert await h.page.locator('[data-verify="i5"]').is_disabled();report['volume_lock_verified']=True
  # Exhaust day budget and verify retry remains possible; visit every reference book.
  it=data['items'][0];await click('[data-verify="i1"]')
  for b in data['books']:await click('[data-book="'+b['id']+'"]');report['books_visited'].append(b['id'])
  await click('[data-close="mask-shelf"]')
  wrong={'book':'xyjl','entry':'e-bone'}
  for _ in range(8):
   before=len(j.checkpoints);await choose(it,wrong);assert len(j.checkpoints)==before and not j.ending_reached;report['negative_checks']+=1
   await click('[data-close="mask-shelf"]')
  st=await state();assert st['day']==0 and st['miss']==8;report['zero_day_not_failure_verified']=True
  for it in data['items']:
   for k,pair in enumerate(it['need']):
    await choose(it,pair)
    if k+1<len(it['need']):assert it['id'] not in j.side;report['partial_checks']+=1
    await click('#btn-card-ok')
    if k+1<len(it['need']):
     before=await state();await choose(it,pair);after=await state();assert before['miss']==after['miss'] and it['id'] not in j.side;await click('[data-close="mask-shelf"]');report.setdefault('duplicate_partial_checks',0);report['duplicate_partial_checks']+=1
   assert it['id'] in j.side
  assert len(j.checkpoints)==0 and len(j.side)==23 and 'clean_i1' not in j.side
  # Saved progress survives a real page reload, without evaluator writes.
  await h.page.reload();await record('reload');assert len((await state())['facts'])==12;report['resume_verified']=True
  # Wrong drafts and submitted wrong verdict, followed by correction.
  for variant in range(2):
   for sl in data['slots']:await slot(sl,False,variant)
   assert len(j.checkpoints)==0 and len(j.side)==23;await click('#btn-verdict');assert not j.ending_reached and len(j.checkpoints)==0 and len(j.side)==23;report['negative_checks']+=1;await click('#btn-back')
  report['wrong_slot_options_verified']=14
  for sl in data['slots']:await slot(sl,True)
  assert len(j.checkpoints)==0 and len(j.side)==23;report['drafts_not_scored_verified']=True
  await click('#btn-verdict');assert j.ending_reached and len(j.checkpoints)==0 and len(j.side)==30;report['score']=j.score();await h.page.bring_to_front();obs=await h.observe('ending.png');assert '他杀焚尸' in obs['visible_text']
  await click('#btn-again');assert not (await state())['facts'];report['in_game_reset_verified']=True
  await h.reset();j=Judge.load(ROOT/cfg['judge_path'],'yanhuo',ROOT);await record('fresh_context');assert not j.checkpoints and (await state()) is None;report['fresh_context_verified']=True
  report['blocked_requests']=h.blocked;assert not h.blocked and not report['page_errors'] and not report['http_errors'];report['pass']=True
 except Exception as e:
  report['failure']=str(e)
  if h.page:await h.page.screenshot(path=str(OUT/'closeout-failure.png'))
  raise
 finally:
  (OUT/'hint-full-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('YANHUO ACCEPTANCE PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
