"""Auditor-side UI acceptance; not a model policy or score."""
from pathlib import Path
import argparse,asyncio,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--port',type=int,default=8821);a=p.parse_args();ROOT=a.root.resolve();sys.path.insert(0,str(ROOT))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
OUT=ROOT/'judge/gongwei-404/verification'

class Replay:
 def __init__(self,h,j):self.h=h;self.j=j;self.steps=[];self.negatives=0;self.multi_tab_checks=[]
 async def record(self,action):
  await self.j.read(self.h);fresh=self.j.update(len(self.steps)+1);self.steps.append({'action':action,'new':fresh,'score':self.j.score()});self.h.consume_step()
 async def click(self,selector,negative=False):
  before=set(self.j.checkpoints)|set(self.j.side);loc=self.h.page.locator(selector).first;await loc.wait_for(state='visible',timeout=15000);await loc.scroll_into_view_if_needed();await loc.click(trial=True);box=await loc.bounding_box();assert box
  r=await self.h.act({'op':'click','x':box['x']+box['width']/2,'y':box['y']+box['height']/2});assert r=='ok',(selector,r)
  await self.h.page.wait_for_load_state('domcontentloaded');await self.record({'op':'click','selector':selector})
  if negative:assert before==(set(self.j.checkpoints)|set(self.j.side));assert not self.j.ending_reached;self.negatives+=1
 async def fill(self,selector,text):
  loc=self.h.page.locator(selector);await loc.scroll_into_view_if_needed();raw=await self.h.observe();box=await loc.bounding_box();assert box;cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
  e=min(raw['elements'],key=lambda e:(e['x']-cx)**2+(e['y']-cy)**2)
  assert abs(e['x']-cx)<5 and abs(e['y']-cy)<5,(selector,e)
  r=await self.h.act({'op':'type','n':e['n'],'text':text,'clear':True});assert r=='ok';await self.record({'op':'type','field':selector,'redacted':True})
 async def goto(self,name):
  r=await self.h.act({'op':'goto','url':f'http://127.0.0.1:{a.port}/'+name});assert r=='ok';await self.record({'op':'goto','file':name})
 async def desk(self):
  pages=self.h.context.pages;i=next(i for i,p in enumerate(pages) if p.url.endswith('/desk.html'));await self.h.act({'op':'switch_tab','i':i});await self.record({'op':'switch_tab','i':i})
  assert self.h.page.url.endswith('/desk.html')
 async def search(self,target):
  await self.desk()
  src=(ROOT/'tasks/gongwei-404/mirror/desk.html').read_text(encoding='utf-8')
  query=re.search(r'"([^"\n]+)"\s*:\s*\{\s*file:\s*"'+re.escape(target)+r'"',src)[1]
  await self.fill('#spotlight-input',query);assert self.h.page.url.endswith('/desk.html')
  await self.h.act({'op':'key','key':'Enter'});await self.record({'op':'key','key':'Enter'});assert self.h.page.url.endswith('/desk.html')
  if len(self.h.context.pages)>1:self.multi_tab_checks.append({'retained_tabs':len(self.h.context.pages),'selected_tab_retained_after_typing_and_key':True,'target_file':target})
  await self.click('#spotlight-results a')
 async def authenticate(self,kind,negative=True):
  tasks={
   'mailbox':('mailbox.html',[('#emailInput','CORRECT_EMAIL'),('#passwordInput','CORRECT_PASSWORD')],'button[onclick="attemptLogin()"]'),
   'weibo':('weibo.html',[('#username-input','correctUsername'),('#password-input','correctPassword')],'.login-btn'),
   'oa':('qyskoa.html',[('#username','correctUsername'),('#password','correctPassword')],'.login-button'),
   'financial':('changyuan.html',[('#accessNameInput','CORRECT_NAME'),('#accessCardInput','CORRECT_CARD_LAST_FOUR')],'button[onclick="checkFileAccess()"]')}
  file,fields,button=tasks[kind];s=(ROOT/'tasks/gongwei-404/mirror'/file).read_text(encoding='utf-8')
  if negative:
   for selector,var in fields:await self.fill(selector,'wrong')
   await self.click(button,negative=True)
  for selector,var in fields:
   answer=re.search(r'const\s+'+re.escape(var)+r'\s*=\s*"([^"\n]+)"',s)[1];await self.fill(selector,answer)
  await self.click(button);await self.record({'op':'successful_validation_read'})
 async def play(self,full):
  await self.record({'op':'reset'});assert not self.j.checkpoints and not self.j.side and not self.j.ending_reached
  await self.click('#loginBtn')
  if full:
   await self.click('a[href="mailbox.html"]');await self.authenticate('mailbox')
   for typ in ['meeting','encrypted','regular','gift','spam']:await self.click(f'[onclick="loadEmail(\'{typ}\')"]')
   await self.click('#folder-deleted');await self.click('#folder-inbox')
   await self.search('weibo.html');await self.authenticate('weibo')
   await self.search('wangpan.html');await self.click('[onclick="showPasswordPrompt()"]');await self.fill('#file-password','wrong');await self.click('#open-button',negative=True)
   s=(ROOT/'tasks/gongwei-404/mirror/wangpan.html').read_text(encoding='utf-8');code=re.search(r'const correctPassword\s*=\s*"([^"\n]+)"',s)[1];await self.fill('#file-password',code);await self.click('#open-button')
   await self.goto('qyskoa.html');await self.authenticate('oa')
  await self.search('changyuan.html');await self.authenticate('financial')
  await self.click('.sheet-tab[data-sheet-name="90天流水明细"]')
  await self.click('.sheet-tab[data-sheet-name="长垣发展有限公司"]')
  await self.h.act({'op':'wait','ms':16000});await self.record({'op':'wait','ms':16000})
  await self.click('#goNewPageLink');await self.h.act({'op':'wait','ms':1800});await self.record({'op':'wait','ms':1800});assert self.j.ending_reached;assert self.j.score()['route_progress']==1.0
  if full:assert len(self.j.side)==4
  await self.h.page.bring_to_front()
  observed=await self.h.observe('full-ending.png' if full else 'minimal-ending.png')
  assert 'BUG REPORT' in observed['visible_text'], 'Ending not present in player-visible observation'
  return {'full_optional_route':full,'steps':self.steps,'negative_checks':self.negatives,'multi_tab_checks':self.multi_tab_checks,'score':self.j.score()}

async def main():
 OUT.mkdir(parents=True,exist_ok=True);cfg=load_config(ROOT/'configs/gongwei-404.json');cfg['settle_ms']=500;cfg['entry_url']=f'http://127.0.0.1:{a.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{a.port}'];cfg['local_serve'].update({'ready_url':cfg['entry_url'],'port':a.port});cmd=cfg['local_serve']['command'];cmd[cmd.index('--port')+1]=str(a.port)
 server=LocalServer();h=BrowserHarness(cfg,OUT);report={'kind':'engineering_acceptance_not_model_score','deployment_root':str(ROOT),'rendered_pages':[],'page_errors':[],'http_errors':[],'routes':[]}
 try:
  server.start(cfg,ROOT,OUT/'server.log');assert server.owned, 'Independent verification requires a freshly started task server';report['server_owned']=True;await h.start();await h.reset()
  def bind():
   h.context.on('page',lambda p:p.on('pageerror',lambda e:report['page_errors'].append(str(e))))
   h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
   h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 and not r.url.endswith('/favicon.ico') else None)
  bind();j=Judge.load(ROOT/cfg['judge_path'],'gongwei-404',ROOT);audit=Replay(h,j)
  report['exploration_states']=[]
  for p in sorted((ROOT/'tasks/gongwei-404/mirror').glob('*.html')):
   await audit.goto(p.name);assert not j.ending_reached and not j.checkpoints and not j.side
   report['rendered_pages'].append(p.name)
   if p.name=='wechat.html':
    names=await h.page.locator('.chat-preview').evaluate_all("es=>es.map(e=>e.getAttribute('onclick'))")
    for i,onclick in enumerate(names):
     await audit.click('[onclick="'+onclick+'"]')
     report['exploration_states'].append({'page':p.name,'state':'chat_'+str(i+1)})
    await audit.click('#moments-icon');report['exploration_states'].append({'page':p.name,'state':'moments'})
   if p.name=='qingmiao.html':
    pages=await h.page.locator('.nav-links a').evaluate_all("es=>es.map(e=>e.getAttribute('data-page'))")
    for page in pages:
     await audit.click('[data-page="'+page+'"]');report['exploration_states'].append({'page':p.name,'state':page})
  for full in [True,False]:
   await h.reset();bind();j=Judge.load(ROOT/cfg['judge_path'],'gongwei-404',ROOT);r=Replay(h,j);report['routes'].append(await r.play(full));print('route_pass',full,flush=True)
  await h.reset();j=Judge.load(ROOT/cfg['judge_path'],'gongwei-404',ROOT);r=Replay(h,j);await r.record({'op':'reset'});assert not j.checkpoints and not j.side;report['reset_verified']=True
  report['blocked_requests']=h.blocked
  assert not report['page_errors'] and not report['http_errors'] and not report['blocked_requests'],(report['page_errors'],report['http_errors'],report['blocked_requests'])
  report['pass']=True
 except Exception as e:
  report['failure']=str(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'),full_page=True)
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('ACCEPTANCE PASS',len(report['rendered_pages']),'pages',flush=True)
if __name__=='__main__':asyncio.run(main())
