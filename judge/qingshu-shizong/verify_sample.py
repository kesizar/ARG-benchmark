"""Private source-assisted UI replay. Game mutations only mouse/keyboard through harness."""
import argparse,asyncio,json,sys,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--port',type=int,default=8831);p.add_argument('--phase',choices=['full','forum','endings'],default='full');a=p.parse_args();R=a.root.resolve();sys.path.insert(0,str(R))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
T='qingshu-shizong';OUT=R/f'judge/{T}/verification';OUT.mkdir(parents=True,exist_ok=True)
class Replay:
 def __init__(self,h):self.h=h;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.steps=[];self.reads=[];self.neg=0
 async def record(self,act,neg=False):
  print(len(self.steps),act,flush=True)
  before=set(self.j.checkpoints)|set(self.j.side);await self.j.read(self.h);fresh=self.j.update(len(self.steps));self.steps.append({'action':act,'fresh':fresh});self.h.consume_step()
  if neg:assert before==set(self.j.checkpoints)|set(self.j.side),(act,fresh);self.neg+=1
 async def click(self,s,neg=False):
  e=(self.h.page.locator(s) if isinstance(s,str) else s).first;await e.wait_for(state='visible');await e.scroll_into_view_if_needed();b=await e.bounding_box();assert b;assert await e.evaluate('(e)=>{let r=e.getBoundingClientRect();let t=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return t===e||e.contains(t)}');assert await self.h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok';await self.record({'click':str(s)},neg)
 async def type(self,s,v):
  e=self.h.page.locator(s);await e.scroll_into_view_if_needed();b=await e.bounding_box();self.h.elements=[{'n':0,'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}];assert await self.h.act({'op':'type','n':0,'clear':True,'text':v})=='ok';await self.record({'type':s,'value':v})
 async def key(self,k):
  k={'ENTER':'Enter','CTRL+A':'Control+a'}.get(k,k);assert await self.h.act({'op':'key','key':k})=='ok';await self.record({'key':k})
 async def wait(self,ms):assert await self.h.act({'op':'wait','ms':ms})=='ok';await self.record({'wait':ms})
 async def read(self,s):self.reads.append({'url':self.h.page.url,'selector':s,'text':await self.h.page.locator(s).inner_text()})
 async def nav(self,id):await self.click(f'[onclick="showPage(\'{id}\')"]');await self.read('#page_'+id)
 async def search(self,v):await self.type('#searchInput',v);await self.key('ENTER')
 async def post(self,id):
  await self.search(id);await self.click(f'#searchResultContent [onclick="openPost(\'{id}\')"]')
  if id=='p71':
   await self.type('#keyInput','wrong');await self.key('ENTER');await self.record({'p71_wrong':True},True);assert not await self.h.page.locator('#p71.active').count();await self.type('#keyInput','后退三步');await self.key('ENTER')
  count=await self.h.page.locator('#'+id+' .floorPage').count()
  for n in range(count):
   await self.read('#'+id+' .floorPage.active');await self.key('CTRL+A');await self.h.page.screenshot(path=str(OUT/f'{id}-floor{n+1}.png'))
   if n+1<count:await self.click('#next-'+id,True)
  for n in range(count-1):await self.click('#prev-'+id,True)
  await self.click('#'+id+' [onclick="backToList()"]')
 async def volume(self):
  await self.click('[onclick="openVolumeKeyPopup()"]');await self.type('#volumeKeyInput','wrong');await self.key('ENTER');await self.record({'wrong_volume':True},True);assert await self.h.page.locator('#volumeKeyPopup').is_visible();await self.type('#volumeKeyInput','invisiblet');await self.key('ENTER');await self.h.page.locator('#choiceMask').wait_for(state='visible',timeout=30000);await self.record({'choice_visible':True})
 async def focused_type(self,id,value):
  for _ in range(30):
   if await self.h.page.evaluate('document.activeElement.id')==id:break
   await self.key('Tab')
  assert await self.h.page.evaluate('document.activeElement.id')==id
  await self.key('Control+a');await self.key('Backspace');assert await self.h.act({'op':'type','text':value})=='ok';await self.record({'focused_keyboard_type':id,'text':value})
 async def choice(self,value):await self.type('#finalChoiceInput',value);await self.click('[onclick="submitFinalChoice()"]')
 async def terminal(self,value):await self.type('#terminalInput',value);await self.key('Enter')
 async def full(self):
  await self.record({'fresh':True});assert not self.j.checkpoints and not self.j.side
  if a.phase=='endings':await self.endings();return
  if a.phase=='full':
   # Original entry has independently accessible public posts, plus timed chat route.
   await self.click('.msg-entry');await self.click('#chatSendBtn');await self.wait(26000);await self.click('#postLink');await self.read('#detailBody');await self.read('#detailReply');await self.click('#detailReply .link');await self.wait(1000)
   tabs=await self.h._tabs();idx=next(i for i,p in enumerate(self.h.context.pages) if p.url.endswith('school.html'));assert await self.h.act({'op':'switch_tab','i':idx})=='ok';await self.record({'switch_tab':idx});await self.read('#page_index');await self.key('CTRL+A');await self.h.page.screenshot(path=str(OUT/'school-hidden.png'))
   for id in ['schoolinfo','class61','teacher','missing','message','cipher','repairlog','contact','forumIntro']:
    await self.nav(id)
    if id=='class61':await self.click('[onclick="showClassDetail(\'61\')"]');await self.read('#classDetailArea')
    if id=='repairlog':
     await self.type('#repairPwdInput','0000');await self.click('[onclick="checkRepairPassword()"]',True);assert await self.h.page.locator('#repairPwdErr').is_visible();await self.type('#repairPwdInput','0516');await self.click('[onclick="checkRepairPassword()"]');await self.read('#repairLogUnlockedArea')
    if id=='contact':
     for v in ['wrong','camemale','hart cat']:
      await self.type('#chatInput',v);await self.click('[onclick="sendChat()"]',True)
     await self.type('#chatInput','came male');await self.click('[onclick="sendChat()"]');await self.wait(9500);await self.type('#chatInput','wrong');await self.click('[onclick="sendChat()"]',True);await self.type('#chatInput','hart cat');await self.click('[onclick="sendChat()"]');await self.wait(8000);await self.read('#chatLog')
    if id=='forumIntro':await self.click('[onclick="showPage(\'forum\')"]');await self.read('#page_forum');await self.type('#forumSearch','wrong');await self.click('[onclick="renderForum()"]',True);await self.type('#forumSearch','范明磊');await self.click('[onclick="renderForum()"]');await self.read('#forumResult')
   await self.h.page.clock.set_fixed_time(datetime.datetime(2026,10,26,18,tzinfo=datetime.timezone.utc))
   await self.click('[onclick="openForumKeyPopup()"]');await self.type('#forumKeyInput','wrong');await self.key('ENTER');await self.record({'wrong_forum':True},True);await self.type('#forumKeyInput','memorialfile');await self.key('ENTER');await self.h.page.wait_for_url('**/forum.html');await self.record({'forum_arrival':True,'environment_clock':'02:00 Asia/Shanghai for night_owl'})
  else:
   await self.h.page.clock.set_fixed_time(datetime.datetime(2026,10,26,18,tzinfo=datetime.timezone.utc))
   await self.click('[onclick="openForumKeyPopup()"]');await self.type('#forumKeyInput','memorialfile');await self.key('ENTER');await self.h.page.wait_for_url('**/forum.html');await self.record({'resume_forum_after_charset_fix':True})
  await self.search('wrong');await self.record({'no_search_result':True},True);assert await self.h.page.locator('.no-result').is_visible()
  for id in ['top1','top2','top3','p21','p47','p53','p58','p62','p68','p71']:await self.post(id)
  for name,id in [('庄军','h1'),('范明磊','h2'),('王师傅','h3'),('顾千','h4')]:
   await self.search(name);await self.click(f'#searchResultContent [onclick="openPost(\'{id}\')"]');await self.read('#'+id);await self.click('#'+id+' [onclick="backToList()"]')
  await self.search('神秘访客');await self.read('#searchResultContent');await self.search('676767');await self.click('[onclick="trigger676767EasterEgg()"]');await self.h.act({'op':'dialog','accept':True});await self.record({'easter_egg_dialog':True})
  for n in range(3):await self.post('top1')
  for n in range(6):await self.key('I')
  if await self.h.page.locator('#achievementListModal').is_visible():await self.click('[onclick="closeAchievementList()"]')
  for n in range(10):
   await self.click('[onclick^="handleNavClick"]');await self.h.act({'op':'dialog','accept':True});await self.record({'unavailable_nav':True},True)
  await self.click('body');await self.key('I');await self.read('#achievementListModal');await self.h.page.screenshot(path=str(OUT/'achievements.png'));await self.click('[onclick="closeAchievementList()"]');storage=await self.h.local_storage();assert not storage.get('fragments_collected');ach=json.loads(storage.get('ach_data','{}'));self.steps.append({'achievement_storage':ach});assert len([k for k,v in ach.items() if v])==12,ach
  assert await self.h.act({'op':'back'})=='ok';await self.record({'back_to_school':True});await self.endings()
 async def endings(self):
  await self.volume();await self.choice('');await self.record({'empty_choice':True},True);assert await self.h.page.locator('#choiceErr').is_visible();await self.choice('anything');await self.wait(300);assert 'silent_darkness' in self.j.route_endings;await self.h.page.screenshot(path=str(OUT/'bad.png'));await self.click('[onclick="resetAll()"]');assert await self.h.page.locator('#page_index').is_visible()
  await self.volume();await self.choice('help');await self.terminal('wrong');await self.record({'unknown_command':True},True);await self.terminal('status');await self.read('#terminalOutput');assert '0/10' in await self.h.page.locator('#terminalOutput').inner_text();await self.terminal('clear');await self.terminal('help');await self.read('#terminalOutput');await self.terminal('surrender');await self.wait(300);assert await self.h.page.locator('#endingOverlay.bad-ending').is_visible();await self.click('[onclick="resetAll()"]')
  await self.volume();await self.choice('help');await self.terminal('trust yourself');await self.wait(3100);assert 'dawn' in self.j.route_endings;await self.h.page.screenshot(path=str(OUT/'good.png'));assert set(self.j.checkpoints)=={'volume'};assert set(self.j.side)==({'repair','caesar','morse','p71','terminal'} if a.phase=='full' else {'terminal'} if a.phase=='endings' else {'p71','terminal'})
async def main():
 cfg=load_config(R/f'configs/{T}.json');cfg['entry_url']=f'http://127.0.0.1:{a.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(a.port);cfg['local_serve']['port']=a.port;cfg['settle_ms']=80;cfg['entry_url']=cfg['entry_url'].replace('index.html','school.html') if a.phase in {'forum','endings'} else cfg['entry_url'];h=BrowserHarness(cfg,OUT);s=LocalServer();r=Replay(h);d={'kind':'source_assisted_normal_UI_not_model_score','errors':[],'http_errors':[]}
 try:
  s.start(cfg,R,OUT/'server.log');d['fresh_server_owned']=s.owned;await h.start();await h.reset();h.context.on('response',lambda x:d['http_errors'].append({'url':x.url,'status':x.status}) if x.status>=400 else None);h.context.on('page',lambda p:p.on('pageerror',lambda e:d['errors'].append(str(e))));h.page.on('pageerror',lambda e:d['errors'].append(str(e)));await r.full();d['score']=r.j.score();await h.reset();j=Judge.load(R/f'judge/{T}/judge.json',T,R);await j.read(h);j.update(0);assert not j.checkpoints and not j.side and not await h.local_storage();d['reset']=True;assert not h.blocked and not d['errors'] and not d['http_errors'];d['pass']=True
 except Exception as e:
  d['failure']=repr(e)
  if h.page:d['body']=await h.page.locator('body').inner_text();await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  d.update(steps=r.steps,reads=r.reads,negative_checks=r.neg,blocked=h.blocked);(OUT/'acceptance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
  try:await asyncio.wait_for(h.close(),15)
  except asyncio.TimeoutError:pass
  finally:s.stop()
if __name__=='__main__':asyncio.run(main())
