"""Private auditor replay. No state injection, time acceleration or model API."""
from pathlib import Path
import argparse,asyncio,json,sys,time
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='duoluoleisi';OUT=R/f'judge/{T}/verification'
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8821);p.add_argument('--skip-idle',action='store_true');a=p.parse_args()
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['settle_ms']=550;c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)
 h=BrowserHarness(c,OUT);server=LocalServer();j=None;steps=[];report={'kind':'engineering_acceptance_not_model_score','page_errors':[],'http_errors':[],'threads':[],'hidden_pages':[],'negative_checks':0,'ending_variants':[]}
 async def rec(label):
  await j.read(h);j.update(len(steps)+1);steps.append({'action':label,'score':j.score()});h.consume_step()
  if len(steps)%30==0:
   print('academy UI steps',len(steps),flush=True)
   (OUT/'progress.json').write_text(json.dumps({'phase':'core_ui','steps':len(steps),'last_action':label},ensure_ascii=False),encoding='utf-8')
 async def click(sel):
  loc=h.page.locator(sel+':visible').first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b
  assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok';await rec(sel)
 async def fill(sel,value):
  loc=h.page.locator(sel);await loc.scroll_into_view_if_needed();ob=await h.observe();b=await loc.bounding_box();assert b;cx=b['x']+b['width']/2;cy=b['y']+b['height']/2;e=min(ob['elements'],key=lambda e:(e['x']-cx)**2+(e['y']-cy)**2);assert abs(e['x']-cx)<5 and abs(e['y']-cy)<5
  assert await h.act({'op':'type','n':e['n'],'text':value,'clear':True})=='ok';await rec('type '+sel)
 async def search(q,kind='hidden',key=None):
  await fill('#searchInput',q);await click('#searchBtn')
  if key is None:key=q
  await click('.search-result-item[onclick="handleResult(\''+kind+'\', \''+key+'\')"]')
 async def wait(ms):assert await h.act({'op':'wait','ms':ms})=='ok';await rec('wait '+str(ms))
 async def scrollend():
  for _ in range(100):
   pos=await h.page.evaluate('({y:scrollY,max:document.documentElement.scrollHeight-innerHeight})')
   if pos['y']>=pos['max']-3:break
   assert await h.act({'op':'scroll','dy':680})=='ok';await rec('read narrative scroll')
  else:raise AssertionError('Narrative never reached end')
 async def snap(name):await h.page.bring_to_front();await h.observe(name+'.png')
 try:
  server.start(c,R,OUT/'server.log');assert server.owned;report['server_owned']=True;await h.start();await h.reset();j=Judge.load(R/c['judge_path'],T,R)
  def bind():
   h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append(r.url) if r.status>=400 and not r.url.endswith('/favicon.ico') else None)
  bind();data=await h.page.evaluate('({threads:THREADS,hidden:HIDDEN,wheel:WHEEL_CORRECT,trueEnding:TRUE_ENDING})');(OUT.parent/'checkpoint-spec.json').write_text(json.dumps({'source_data':data,'scored_puzzles':['four-symbol death-order wheel','Observator inferred keyword','observer reassurance phrase','stop/abandon semantic search','nightowl archive name key'],'flow':'Terminal failure for wrong observer phrase; good ending via four equivalent search words; true ending via correct observer phrase; secret archive lore after name; 20-minute focus-triggered warm-castle easter egg. All collection/search page visits diagnostic only.','bypasses':'No enforced need to collect pages or solve wheel before Observator. Search can reveal locked archive before its board is shown. Reload resets all game memory.'},ensure_ascii=False,indent=2),encoding='utf-8')
  # Wrong final phrase is an explicit authored bad ending, not a success point.
  await search('Observator');await fill('#observerCode','wrong');await click('[onclick="checkObserver()"]');await wait(4600);assert j.score()['failure_id']=='bad' and not j.score()['ending_reached'] and 'phrase' not in j.checkpoints;report['negative_checks']+=1;report['ending_variants'].append('bad');await snap('bad-ending');await click('[onclick="location.reload()"]');assert not await h.page.evaluate('window.observerFound===true');report['bad_restart_verified']=True
  j=Judge.load(R/c['judge_path'],T,R);steps=[];t0=time.monotonic();await rec('fresh after bad restart')
  await fill('#searchInput','NONEXISTENT-TEST-KEY');await click('#searchBtn');assert not j.checkpoints and not j.side;report['negative_checks']+=1
  for key,thread in data['threads'].items():
   await search(thread['title'],'thread',key);report['threads'].append(key)
   if not thread.get('archived') and not thread.get('locked') and 'reply_tested' not in report:
    for text in ['?','test','循环']:await fill('#replyInput',text);await click('[onclick="submitReply()"]')
    assert await h.page.evaluate('replyCountPerThread[currentThread]===3');report['reply_tested']=True
  for key,page in data['hidden'].items():
   await search(key);report['hidden_pages'].append(key)
   if key=='地下室':
    for _ in range(4):await click('#basement-game')
    await wait(3400);await click('#basement-game');assert await h.page.evaluate('basementStep===0');report['basement_loop_verified']=True
  # Wrong wheel order resets without scoring; same UI then solves exact death order.
  wheel_page=next(k for k,v in data['hidden'].items() if 'id="wheel"' in v['content']);await search(wheel_page)
  for key in ['candle','crown','rabbit','skull']:await click('.wheel-symbol[data-key="'+key+'"]')
  await wait(700);assert not await h.page.evaluate('playerProgress.wheel');report['negative_checks']+=1
  for key in data['wheel']:await click('.wheel-symbol[data-key="'+key+'"]')
  await wait(800);assert 'wheel' in j.side
  await click('#closeBtn');assert '真正的词是 Observator' in await h.page.locator('#content').inner_text();report['full_collection_hint_verified']=True
  # All semantic alternatives are accepted good endings; read one through its bottom jump scare.
  for word in ['停下','放弃','累了','别走']:
   await search(word);assert await h.page.evaluate('currentPage==="good-ending"')
  await scrollend();await wait(1900);await snap('good-ending-bottom');report['ending_variants'].append('good')
  # Hidden archive accepts only matching name; full text is an optional lore epilogue.
  await search(data['threads']['t0']['title'],'thread','t0');await fill('#archiveKey','wrong');before=set(j.side);await click('[onclick="checkArchiveKey()"]');assert set(j.side)==before;report['negative_checks']+=1
  await fill('#archiveKey','夜枭');await click('[onclick="checkArchiveKey()"]');assert 'archive' in j.side;await snap('archive');report['archive_epilogue_verified']=True
  await search('Observator');await fill('#observerCode','你已经够好了');await click('[onclick="checkObserver()"]');assert j.score()['route_id']=='true' and j.score()['route_progress']==1;report['ending_variants'].append('true');await snap('true-ending-top');await scrollend();await snap('true-ending-bottom');report['true_narrative_read_to_end']=True
  report['full_score']=j.score();report['full_steps']=steps.copy()
  if not a.skip_idle:
   # Keep the original 1,200,000ms timer; do not modify Date, timeouts or game flags.
   while True:
    elapsed=time.monotonic()-t0
    if elapsed>=1205:break
    print('academy waiting original 20min branch; remaining_seconds',round(1205-elapsed),flush=True)
    (OUT/'progress.json').write_text(json.dumps({'phase':'original_idle_timer','remaining_seconds':round(1205-elapsed)},ensure_ascii=False),encoding='utf-8')
    await h.act({'op':'wait','ms':min(45000,int((1205-elapsed)*1000)+1)})
   await click('#closeBtn');await click('#searchInput');await wait(1300);assert await h.page.evaluate('currentPage==="warm-castle"');await snap('warm-castle');await click('[onclick="goHome()"]');assert await h.page.evaluate('currentPage==="home"');report['original_twenty_minute_easter_egg_verified']=True;report['real_elapsed_seconds']=round(time.monotonic()-t0,2)
  else:report['original_twenty_minute_easter_egg_verified']=False
  await h.page.reload();j=Judge.load(R/c['judge_path'],T,R);steps=[];await rec('reload reset');assert not await h.page.evaluate('window.observerFound===true');assert not await h.page.evaluate('playerProgress.wheel');assert not j.checkpoints and not j.side;report['reload_reset_verified']=True
  await h.reset();j=Judge.load(R/c['judge_path'],T,R);steps=[];await rec('new_context');assert not j.checkpoints and not j.side;report['fresh_context_reset_verified']=True
  report['blocked_requests']=h.blocked;assert not h.blocked and not report['page_errors'] and not report['http_errors'];report['pass']=True
 except Exception as e:
  report['failure']=str(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('ACADEMY ACCEPTANCE PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
