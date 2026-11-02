"""Source-assisted normal-UI acceptance; never inject game state or call a model."""
from pathlib import Path
import asyncio,argparse,json,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='wuren-li-an';OUT=R/f'judge/{T}/verification'
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8821);p.add_argument('--phase',choices=['all','core','negative','reset'],default='all');a=p.parse_args()
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port);c['settle_ms']=80
 h=BrowserHarness(c,OUT);server=LocalServer();j=None;steps=[];report={'kind':'engineering_acceptance_not_model_score','page_errors':[],'http_errors':[],'negative_checks':[],'formal_endings':[],'failure_causes':[],'mode_views':{},'document_reads':{},'accepted_decode_aliases':[]}
 async def rec(label):
  await j.read(h);j.update(len(steps)+1);steps.append({'action':label,'score':j.score()});h.consume_step()
  if len(steps)%30==0:
   print('UNFILED UI',len(steps),label,flush=True);(OUT/'progress.json').write_text(json.dumps({'steps':len(steps),'last':label},ensure_ascii=False),encoding='utf-8')
 async def act(x,label=None):assert await h.act(x)=='ok',x;await rec(label or str(x))
 async def click(sel):
  loc=h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b;await act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2},'click '+sel)
 async def fill(sel,value):
  await click(sel);old=await h.page.locator(sel).input_value();await act({'op':'key','key':'End'})
  for _ in old:await act({'op':'key','key':'Backspace'})
  await act({'op':'type','text':value});assert await h.page.locator(sel).input_value()==value
 async def reset():
  await h.reset();nonlocal j;j=Judge.load(R/c['judge_path'],T,R);h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append(r.url) if r.status>=400 and not r.url.endswith('/favicon.ico') else None);await h.observe();await rec('fresh browser context');assert not j.checkpoints and not j.side and not j.ending_reached
 async def login(name,mail_read=False):
  await fill('#lawyer-name',name);await click('button[onclick="boot()"]')
  if name.strip()!='王笑':
   if mail_read and name.strip()=='陈慎言':
    report['truth_mail_reads']=[]
    for i in range(1,6):await click(f'.mail-item[onclick="openMailDetail({i})"]');report['truth_mail_reads'].append(await h.page.locator('#mail-detail').inner_text());await click('#mail-detail button[onclick="showInbox()"]')
    await click('.mail-item[onclick="openMailDetail(0)"]')
   else:await click('.mail-item')
   await click('#mail-detail button[onclick="accept()"]')
  assert await h.page.locator('#view-main').evaluate('(e)=>e.classList.contains("active")')
 async def nav(pane):await click('#nav button[onclick="go(\''+pane+'\')"]')
 async def good(pid):await click('button[onclick="answer(\''+pid+'\',this,true)"]')
 async def bad(pid,i=0):await click('button[onclick="answer(\''+pid+'\',this,false)"] >> nth='+str(i))
 async def decode(word):await nav('p-evidence');await click('#ev-will3');await fill('#clue-input',word);await click('button[onclick="tryDecode()"]')
 async def sorting(wrong=False,partial=False):
  await nav('p-timeline')
  if partial:
   await click('.sort-opt[data-id="e"]');await click('.sort-opt[data-id="d"]');assert 'sort' not in j.checkpoints;await click('button[onclick="resetSort()"]');assert await h.page.evaluate('sortChosen.length')==0;report['partial_sort_reset_no_credit']=True
  for value in (['b','a','e','c','d'] if wrong else ['e','d','c','b','a']):await click('.sort-opt[data-id="'+value+'"]')
 async def failcheck(pid,point=None):
  assert await h.page.locator('#view-bad').evaluate('(e)=>e.classList.contains("active")');assert j.score()['failure_reached'] and j.score()['failure_id']=='failure_'+pid and not j.score()['ending_reached'];assert not point or point not in j.checkpoints and point not in j.side;report['failure_causes'].append(pid);report['negative_checks'].append({'cause':pid,'score':j.score()})
 async def chat(target):
  await click('button[onclick="openChat(\''+target+'\')"]');texts=[await h.page.locator('#chat-title').inner_text()]
  if target=='chen':assert '陈慎言' in texts[0];report['full_identity_visible_in_surface_chat_title']=True
  for _ in range(8):
   texts.append(await h.page.locator('#chat-box').inner_text())
   if not await h.page.locator('#chat-opts .opt').count():break
   await click('#chat-opts .opt')
  else:raise AssertionError('chat did not terminate')
  await click('#chat-opts .btn');return texts
 try:
  server.start(c,R,OUT/'server.log');assert server.owned;report['server_owned']=True;await h.start()
  if a.phase in ['all','core']:
   await reset();await click('button[onclick="boot()"]');assert '请输入' in await h.page.locator('#boot-err').inner_text();assert not j.checkpoints;report['blank_login_no_credit']=True
   await login('调查员');assert await h.page.evaluate('state.mode')=='surface';report['mode_views']['surface']=await h.page.locator('#nav').inner_text();report['surface_chats']={target:await chat(target) for target in ['shen','chen','wang','zhao']};await nav('p-mail');assert not (await h.page.locator('#mail-list-box').inner_text()).strip();report['original_empty_main_mail_pane_verified']=True;await click('#view-main button[onclick="show(\'view-boot\')"]');await login('王笑');assert await h.page.evaluate('state.mode')=='intern';report['mode_views']['intern']=await h.page.locator('#nav').inner_text()
   for doc in ['d-contract','d-approval','d-authorization','d-agency','d-risk']:
    await nav('p-dossier');await click('.evidence-item[onclick="toggleEv(\''+doc+'\')"]');report['document_reads']['intern/'+doc]=await h.page.locator('#'+doc).inner_text()
   await nav('p-staff');report['intern_history']=await h.page.locator('#staff-history').inner_text();report['intern_chats']={target:await chat(target) for target in ['shen','chen','wang','zhao']}
   # Full narrative path, including optional legal questions and every document.
   await reset();await login('陈慎言',True);report['mode_views']['truth']=await h.page.locator('#nav').inner_text();await good('pd');await good('pd2');assert set(j.side)=={'will_priority','duress_evidence'}
   for pane in ['p-wills','p-overview','p-people','p-mail']:await nav(pane);report['document_reads'][pane]=await h.page.locator('#'+pane).inner_text()
   for pane,ids in [('p-evidence',['e-ledger','e-diary','e-photo','e-tape','e-will3']),('p-dossier',['d-contract','d-approval','d-authorization','d-agency','d-risk','d-firsttalk','d-meet'])]:
    await nav(pane)
    for doc in ids:
     await click('.evidence-item[onclick="toggleEv(\''+doc+'\')"]');report['document_reads'][doc]=await h.page.locator('#'+doc).inner_text()
     if doc=='e-photo':await click('.photo-frame');assert await h.page.locator('.photo-frame').evaluate('(e)=>e.classList.contains("flipped")');await click('.photo-frame')
   for k,word in enumerate(['煤气阀门动了手脚','煤气阀门动手脚','煤气阀门被动了手脚','燃气阀门动了手脚','燃气阀门动手脚']):
    if k:await reset();await login('陈慎言')
    await decode(word);assert 'decode' in j.checkpoints;report['accepted_decode_aliases'].append(word);await sorting(partial=k==0);assert 'sort' in j.checkpoints;await nav('p-people');await good('pw');assert 'witness' in j.side;await good('pf');assert 'final' in j.side and not j.ending_reached;report['pre_choice_not_completed']=True;choice=['C','A','B','A','C'][k];await click('.ending-opt[onclick="ending(\''+choice+'\')"]');assert j.score()['route_id']==choice and j.score()['route_progress']==1;report['formal_endings'].append({'choice':choice,'score':j.score()});await h.observe('ending-'+choice+'.png')
    if k:assert set(j.side)=={'witness','final'}
  if a.phase in ['all','negative']:
   # Every wrong MCQ option, plus both decoding failures and wrong complete order.
   for pid in ['pd','pd2','pw','pf']:
    for i in range(3):
     await reset();await login('陈慎言')
     if pid=='pd2':await good('pd')
     elif pid in ['pw','pf']:
      await decode('煤气阀门动了手脚');await sorting();await nav('p-people')
      if pid=='pf':await good('pw')
     await bad(pid,i);await failcheck(pid,{'pd':'will_priority','pd2':'duress_evidence','pw':'witness','pf':'final'}[pid])
   for word in ['', '阀门坏了']:
    await reset();await login('陈慎言');await decode(word);await failcheck('decode','decode')
   await reset();await login('陈慎言');await decode('煤气阀门动了手脚');await sorting(True);await failcheck('sort','sort');await h.observe('failure-sort.png');await click('#view-bad button[onclick="restart()"]');assert not await h.page.evaluate('localStorage.getItem("wlb_decoded")');assert await h.page.locator('#lawyer-name').input_value()=='陈慎言';report['failure_restart_clears_puzzle_progress_preserves_name']=True
  if a.phase in ['all','reset']:
   await reset();await login('陈慎言');await decode(' 煤 气 阀 门 动 了 手 脚 ');assert 'decode' in j.checkpoints;report['decode_internal_whitespace_accepted']=True;await h.page.reload();j=Judge.load(R/c['judge_path'],T,R);await rec('reload retains stale key but resets DOM');assert await h.page.evaluate('localStorage.getItem("wlb_decoded")==="1"');assert not j.checkpoints and not j.ending_reached;report['stale_decoded_storage_not_scored_after_reload']=True
   await reset();await login('陈慎言');await decode('煤气阀门动了手脚');await sorting();await nav('p-people');await good('pw');await good('pf');await click('.ending-opt[onclick="ending(\'C\')"]');await h.page.reload();j=Judge.load(R/c['judge_path'],T,R);await rec('reload stale finished flag');assert await h.page.evaluate('localStorage.getItem("wlb_finished")==="1"');assert not j.ending_reached and not j.checkpoints;report['stale_finished_key_not_completion_after_reload']=True
  await reset();report['fresh_context_reset_verified']=True;report['blocked_requests']=h.blocked;assert not h.blocked and not report['page_errors'] and not report['http_errors'];report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page and not h.pending:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  report['steps']=steps;(OUT/('acceptance.json' if a.phase=='all' else a.phase+'-acceptance.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('UNFILED FULL UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
