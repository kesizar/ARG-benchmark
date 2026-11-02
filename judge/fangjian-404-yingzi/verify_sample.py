"""Curator-only normal browser actions. Source-derived answers are private."""
import argparse,asyncio,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--port',type=int,default=8831);p.add_argument('--probe-original',action='store_true');p.add_argument('--branch',default='all');args=p.parse_args();ROOT=args.root.resolve();sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
TASK='fangjian-404-yingzi';OUT=ROOT/f'judge/{TASK}/verification';OUT.mkdir(parents=True,exist_ok=True);INV=json.loads((ROOT/f'judge/{TASK}/source-inventory.json').read_text(encoding='utf-8'))
class Replay:
 def __init__(self,h):self.h=h;self.j=Judge.load(ROOT/f'judge/{TASK}/judge.json',TASK,ROOT);self.steps=[];self.negative=0;self.posts=[];self.dialogs=[]
 async def record(self,a):await self.j.read(self.h);fresh=self.j.update(len(self.steps));self.steps.append({'action':a,'new':fresh,'score':self.j.score()});self.h.consume_step()
 async def click(self,loc,negative=False):
  before=set(self.j.checkpoints)|set(self.j.side);loc=self.h.page.locator(loc) if isinstance(loc,str) else loc;loc=loc.first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();a={'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2};assert await self.h.act(a)=='ok';await self.record(a)
  if negative:assert before==set(self.j.checkpoints)|set(self.j.side),'Unscored action gave points';self.negative+=1
 async def type(self,sel,value):
  loc=self.h.page.locator(sel);await loc.scroll_into_view_if_needed();b=await loc.bounding_box();self.h.elements=[{'n':0,'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}];assert await self.h.act({'op':'type','n':0,'clear':True,'text':value})=='ok';await self.record({'op':'type','selector':sel,'value':value})
 async def wait(self,ms):assert await self.h.act({'op':'wait','ms':ms})=='ok';await self.record({'op':'wait','ms':ms})
 async def dialog(self,accept=True,text=''):
  assert self.h.pending;obs=await self.h.observe();self.dialogs.append({'before':obs.get('pending_dialog'),'accept':accept,'text':text});assert await self.h.act({'op':'dialog','accept':accept,'text':text})=='ok';await self.record({'op':'dialog','accept':accept,'text':text})
 async def enter(self):
  await self.record({'op':'fresh_context'});assert not self.j.checkpoints and not self.j.side and not self.j.ending_reached;await self.click('#search-engine button');await self.click('.search-result')
 async def search(self,kw,open_result=True):
  await self.type('#forum-search-input',kw);await self.click('[onclick="forumSearch()"]',True)
  if open_result:await self.click('#search-results-list tr',True)
 async def login(self,user,password):
  await self.type('#login-user',user);await self.type('#login-pass',password);await self.click('[onclick="doLogin()"]')
 async def close_pm(self):
  if await self.h.page.locator('#pm-modal').is_visible():
   await self.click('#pm-modal button')
   if self.h.pending:await self.dialog(True)
 async def original_probe(self):
  await self.enter();await self.search('李伯');await self.search('工号');before={'title':await self.h.page.locator('#post-title').inner_text(),'content':await self.h.page.locator('#post-content').inner_text()};await self.wait(4200);after={'title':await self.h.page.locator('#post-title').inner_text(),'content':await self.h.page.locator('#post-content').inner_text()};assert before['title']==after['title'] and before['content']!=after['content'];return {'before':before,'after':after,'stale_edit_confirmed':True,'steps':self.steps}
 async def inspect_all_posts(self):
  for board in ['announce','neighbor','chat','factory','strange','basement']:
   await self.click(f'.forum-nav [onclick="showBoard(\'{board}\',this)"]',True)
   assert await self.h.page.locator('#post-list-body tr').count()==len(INV['posts'][board])
   for index,item in enumerate(INV['posts'][board]):
    await self.click(self.h.page.locator('#post-list-body tr').nth(index),True)
    if item.get('forbidden'):
     assert await self.h.page.locator('#forbidden-screen').is_visible();await self.click('#forbidden-screen',True);self.posts.append({'id':item['id'],'board':board,'kind':'forbidden_overlay'})
    else:
     assert await self.h.page.locator('#post-title').text_content()==item['title'];expected=item['content']
     if item.get('editable'):await self.wait(4200);expected=item['editContent']
     assert await self.h.page.locator('#post-content').text_content()==expected
     self.posts.append({'id':item['id'],'board':board,'kind':'rendered_content_matches_source'});await self.click('[onclick="backToBoard()"]',True)
  for index,item in enumerate(INV['posts']['deleted']):
   await self.click('[onclick="showAdminPanel(this)"]',True);await self.click(self.h.page.locator('.deleted-post').nth(index),True);assert await self.h.page.locator('#post-content').text_content()==item['content'];self.posts.append({'id':item['id'],'board':'deleted','kind':'admin_archive'})
 async def inspect_searches(self):
  for key,value in INV['search_keywords'].items():
   await self.search(key)
   if value.get('cult'):assert await self.h.page.locator('#cult-site').is_visible();await self.click('[onclick="backToForum()"]',True)
   else:
    item=next(x for x in INV['posts'][value['board']] if x['id']==value['postId']);assert await self.h.page.locator('#post-title').text_content()==item['title']
    if item.get('editable'):await self.wait(4200)
  for key in INV['fake_keywords']+['不存在的关键词']:
   await self.search(key,False);assert await self.h.page.locator('#search-results-view').is_visible()
 async def admin(self):
  await self.login('menghua','031789');await self.wait(10600);await self.close_pm();assert 'admin_login' in self.j.side
 async def cult(self,full=False):
  await self.click('.ad[onclick="goToCult()"]',True)
  if full:
   for key in ['intro','ritual','roster','altar','contact']:await self.click(f'.cult-nav [onclick="showCultPage(\'{key}\',this)"]',True)
  else:await self.click('.cult-nav [onclick="showCultPage(\'contact\',this)"]',True)
 async def cancel(self,full=False):
  await self.h.observe('contact-before-native-dialog.png')
  if full:
   for answer,confirm in [(None,None),('wrong',None),('往生自在',False)]:
    old=set(self.j.checkpoints);await self.click('#cancel-offering-btn');assert self.h.pending and self.h.pending.type=='prompt';await self.dialog(answer is not None,answer or '')
    if confirm is not None:assert self.h.pending and self.h.pending.type=='confirm';await self.dialog(confirm)
    assert old==set(self.j.checkpoints) and not await self.h.page.evaluate('offeringCanceled');self.negative+=1
  await self.click('#cancel-offering-btn');assert self.h.pending and self.h.pending.type=='prompt';await self.dialog(True,' 往生自在 ');assert self.h.pending and self.h.pending.type=='confirm';await self.dialog(True);assert 'offering_cancelled' in self.j.side;await self.wait(9000)
  assert await self.h.page.locator('#choice-modal').is_visible()
 async def run(self,ending,full=False):
  await self.enter()
  if ending=='loop_failure':
   for _ in range(5):await self.login('menghui19','wrong')
   await self.wait(2300);assert not self.j.checkpoints and not self.j.side
  else:
   if full:
    await self.login('missing-user','wrong');assert not self.j.checkpoints and not self.j.side
    await self.login('menghui19','wrong');assert not self.j.checkpoints and not self.j.side
    await self.login('menghui19','19710903');assert 'brother_login' in self.j.side;await self.click('[onclick="doLogout()"]',True)
    await self.login('chenshouyi','000160');await self.wait(1800);await self.close_pm();assert 'guardian_login' in self.j.side;await self.click('.guardian-only',True);assert await self.h.page.locator('#guardian-logs .log-entry').count()==15;await self.click('#nav-basement',True);assert '仅管理员可见' in await self.h.page.locator('#toast').text_content();await self.click('[onclick="doLogout()"]',True)
   await self.admin()
   if full:await self.inspect_all_posts();await self.inspect_searches()
   await self.cult(full);await self.cancel(full)
   await self.click({'true':'[onclick="trueEnding()"]','bad':'[onclick="badEnding()"]','hidden':'[onclick="hiddenEnding()"]'}[ending]);
   if ending=='true':await self.wait(5500)
  assert (self.j.score()['failure_reached'] and self.j.score()['failure_id']=='loop_failure' and not self.j.ending_reached) if ending=='loop_failure' else (self.j.ending_reached and self.j.score()['route_id']==ending),self.j.score();assert len(self.j.checkpoints)==0;await self.h.page.screenshot(path=str(OUT/f'{ending}.png'))
  report={'ending':ending,'full_investigation':full,'score':self.j.score(),'steps':self.steps,'unscored_checks':self.negative,'posts':self.posts,'native_dialogs':self.dialogs,'source_view_exposed':False}
  if ending=='true':
   assert (await self.h.local_storage()).get('zy_cleared')=='1';await self.click('#ending-modal button');await self.wait(100);fresh=Judge.load(ROOT/f'judge/{TASK}/judge.json',TASK,ROOT);await fresh.read(self.h);fresh.update(0);assert not fresh.ending_reached and not fresh.checkpoints;report['saved_clear_does_not_award_new_episode']=True;await self.click('#search-engine button');await self.click('.search-result');assert '已重启' in await self.h.page.locator('#forum-title').inner_text();await self.click('.forum-nav [onclick="showBoard(\'chat\',this)"]');await self.click(self.h.page.locator('#post-list-body tr').filter(has_text='给那个陌生人'));assert '我和弟弟走了' in await self.h.page.locator('#post-content').inner_text();report['post_clear_epilogue_rendered']=True
  if ending=='loop_failure':
   await self.click('#ending-modal button');assert not await self.h.page.locator('#ending-modal').is_visible();assert await self.h.page.evaluate('Object.values(loginAttempts).every(n=>n===0)');report['loop_restart_resets_attempts']=True
  return report

async def main():
 cfg=load_config(ROOT/f'configs/{TASK}.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(args.port);cfg['local_serve']['port']=args.port;cfg['settle_ms']=30;h=BrowserHarness(cfg,OUT);server=LocalServer();report={'kind':'private_source_assisted_engineering_replay_not_model_score','root':str(ROOT),'page_errors':[],'http_errors':[],'branches':[]}
 try:
  server.start(cfg,ROOT,OUT/'server.log');await h.start();await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));r=Replay(h)
  if args.probe_original:report['probe']=await r.original_probe()
  else:
   for ending in (['true','bad','hidden','loop_failure'] if args.branch=='all' else [args.branch]):
    await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda res:report['http_errors'].append({'url':res.url,'status':res.status}) if res.status>=400 else None);r=Replay(h);report['branches'].append(await r.run(ending,ending=='true'));print('branch',ending,'passed',flush=True)
   assert not report['page_errors'] and not report['http_errors'] and not h.blocked
   await h.reset();fresh=Replay(h);await fresh.record({'op':'fresh_reset'});assert not fresh.j.checkpoints and not fresh.j.side and not fresh.j.ending_reached and not await h.local_storage();report['fresh_reset_verified']=True
  report['pass']=True
 except Exception as e:
  report['failure']=repr(e);report['partial_trace']=r.steps;report['partial_posts']=r.posts;report['partial_dialogs']=r.dialogs
  if h.page and not h.pending:await h.page.screenshot(path=str(OUT/'failure.png'));report['body_at_failure']=await h.page.locator('body').inner_text()
  raise
 finally:
  (OUT/('original-probe.json' if args.probe_original else 'acceptance.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
if __name__=='__main__':asyncio.run(main())
