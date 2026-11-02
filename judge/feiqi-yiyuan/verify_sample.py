"""Private auditor UI acceptance for archived offline hospital game."""
from pathlib import Path
import argparse,asyncio,json,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='feiqi-yiyuan';OUT=R/f'judge/{T}/verification'
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8821);a=p.parse_args()
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['settle_ms']=550;c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port)
 h=BrowserHarness(c,OUT);server=LocalServer();j=None;steps=[];report={'kind':'engineering_acceptance_not_model_score','page_errors':[],'http_errors':[],'rendered_routes':[],'ending_levels':[],'negative_checks':0}
 async def st():return await h.page.evaluate('JSON.parse(JSON.stringify(STATE))')
 async def rec(label):
  await j.read(h);j.update(len(steps)+1);steps.append({'action':label,'score':j.score()});h.consume_step()
  if len(steps)%25==0:print('hospital UI steps',len(steps),flush=True)
 async def click(sel,prompt=False):
  loc=h.page.locator(sel+':visible').first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b
  assert await h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok'
  if not prompt:await rec(sel)
 async def fill(sel,value):
  loc=h.page.locator(sel);await loc.scroll_into_view_if_needed();ob=await h.observe();b=await loc.bounding_box();assert b;cx=b['x']+b['width']/2;cy=b['y']+b['height']/2;e=min(ob['elements'],key=lambda e:(e['x']-cx)**2+(e['y']-cy)**2);assert abs(e['x']-cx)<5 and abs(e['y']-cy)<5
  assert await h.act({'op':'type','n':e['n'],'text':value,'clear':True})=='ok';await rec('type '+sel)
 async def go(route):
  assert await h.act({'op':'goto','url':c['entry_url']+'#'+route})=='ok';await rec('goto #'+route);report['rendered_routes'].append(route)
 async def dialog(value):
  assert h.pending;assert await h.act({'op':'dialog','accept':True,'text':value})=='ok';await rec('answer prompt')
 async def negative(action):
  before=set(j.checkpoints)|set(j.side);await action();assert before==(set(j.checkpoints)|set(j.side));report['negative_checks']+=1
 async def ending(name):
  await go('thread');assert j.score()['route_id']==name,(name,j.score());assert j.ending_reached;report['ending_levels'].append(name);await h.page.bring_to_front();await h.observe(name+'-ending.png')
 try:
  server.start(c,R,OUT/'server.log');assert server.owned;report['server_owned']=True;await h.start();await h.reset();j=Judge.load(R/c['judge_path'],T,R)
  h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append(r.url) if r.status>=400 and not r.url.endswith('/favicon.ico') else None)
  data=await h.page.evaluate('({boards:Object.keys(BOARDS),posts:Object.keys(POSTS),users:Object.keys(USERS),rooms:WARD_ROOMS,spaceTabs:SPACE_TABS,docs:INTRANET_DOCS,clues:CLUES})');(OUT.parent/'checkpoint-spec.json').write_text(json.dumps({'source_data':data,'puzzles':['Morse/name space password','accident date log password','patient name phone password','bed number and day drawer lock','Caesar shift OA password','founding year encrypted diary'],'flow':'Four cumulative ending levels, unlocked by space; space+phone; +intranet; +chen. Log and drawer are clue sources but not programmatically required. Three refreshes unlock hospital interactive areas.','unreachable':'c16 defined but never addClue(c16), therefore 16/16 key rank impossible in unchanged source.'},ensure_ascii=False,indent=2),encoding='utf-8')
  for route in ['space','phone','intranet','ward','thread']:
   await go(route);assert not j.checkpoints and not j.side and not j.ending_reached
  for kind in ['boards','posts','users']:
   for ident in data[kind]:await go({'boards':'board/','posts':'post/','users':'user/'}[kind]+ident)
  await go('hospital')
  for stage in range(4):
   for tab in ['home','intro','dept','doctor','history','contact']+(['duty','archive'] if stage==3 else []):await click('[onclick="setHospTab(\''+tab+'\')"]')
   if stage<3:await click('.refresh-btn')
  assert (await st())['refresh']==3
  await click('[onclick="setHospTab(\'contact\')"]');await click('[onclick="openChat()"]')
  for i in range(4):await click('[onclick="askQuick('+str(i)+')"]')
  for _ in range(3):await h.act({'op':'wait','ms':16000});await rec('wait scripted chat')
  for _ in range(6):
   if (await st())['chatDone']:break
   await h.act({'op':'wait','ms':5000});await rec('wait remaining original chat')
  assert (await st())['chatDone'] and (await st())['clues'].get('c05');await click('.chat-close')
  await go('ward')
  for room in data['rooms']:await click('[onclick="visitRoom(\''+room['id']+'\')"]')
  await click('[onclick="visitRoom(\'office\')"]');await fill('#drawer-key','0000');await negative(lambda:click('[onclick^="tryDrawer("]'));await fill('#drawer-key','0714');await click('[onclick^="tryDrawer("]');assert 'drawer' in j.side
  await go('hospital');await click('[onclick="setHospTab(\'archive\')"]');await click('[onclick="openArchive()"]');assert (await st())['archiveRead']
  await go('forum');await fill('#space-input','wrong');await negative(lambda:click('[onclick="tryEnterSpace()"]'));await fill('#space-input','suwanqing');await click('[onclick="tryEnterSpace()"]');assert 'space' in j.checkpoints
  for tab in data['spaceTabs']:await click('[onclick="setSpaceTab(\''+tab['id']+'\')"]')
  await click('[onclick="setSpaceTab(\'rizhi\')"]');await click('[onclick="tryLogUnlock()"]',prompt=True);await negative(lambda:dialog('wrong'));await click('[onclick="tryLogUnlock()"]',prompt=True);await dialog('0614');assert 'log' in j.side
  await ending('follow')
  await go('hospital');await click('[onclick="setHospTab(\'archive\')"]');await fill('#phone-key','wrong');await negative(lambda:click('[onclick^="tryPhoneKey("]'));await fill('#phone-key','林建国');await click('[onclick^="tryPhoneKey("]');await click('[onclick="finishTruth()"]');await ending('truth')
  await go('intranet');await fill('#oa-pass','wrong');await negative(lambda:click('[onclick="tryIntranetLogin()"]'));await fill('#oa-pass','guiling');await click('[onclick="tryIntranetLogin()"]')
  for doc in data['docs']:
   if not doc.get('locked'):await click('[onclick="toggleDoc(\''+doc['id']+'\')"]')
  await ending('deeper')
  await go('intranet');await click('[onclick="toggleDoc(\'chen\')"]',prompt=True);await negative(lambda:dialog('wrong'));await click('[onclick="toggleDoc(\'chen\')"]',prompt=True);await dialog('1988');await ending('final');assert len(j.checkpoints)+len(j.side)==6
  before=await st();await h.page.reload();await rec('reload');assert (await st())==before;report['resume_verified']=True;report['full_steps']=steps.copy();report['full_score']=j.score();report['clues_obtained']=len(before['clues']);assert not before['clues'].get('c16');report['unreachable_c16_confirmed']=True
  await h.reset();j=Judge.load(R/c['judge_path'],T,R);steps=[];await rec('fresh context');assert not j.checkpoints and not j.side;report['reset_verified']=True
  await fill('#space-input','suwanqing');await click('[onclick="tryEnterSpace()"]');await ending('follow');assert len(j.checkpoints)==1 and not j.side;report['minimal_follow_verified']=True
  report['blocked_requests']=h.blocked;assert not h.blocked and not report['page_errors'] and not report['http_errors'];report['pass']=True
 except Exception as e:
  report['failure']=str(e)
  if h.page and not h.pending:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('HOSPITAL ACCEPTANCE PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
