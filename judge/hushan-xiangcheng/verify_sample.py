"""Private curator replay: UI-only moves and source-derived answers, no model API."""
import argparse,asyncio,html,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--port',type=int,default=8831);p.add_argument('--original-probe',action='store_true');p.add_argument('--only-merge',action='store_true');p.add_argument('--deployment-smoke',action='store_true');args=p.parse_args();ROOT=args.root.resolve();sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
TASK='hushan-xiangcheng';OUT=ROOT/'judge'/TASK/'verification';OUT.mkdir(parents=True,exist_ok=True)
def norm(s):return re.sub(r'\s+','',html.unescape(re.sub('<[^>]*>','',s)))
POOLS=json.loads((ROOT/'judge'/TASK/'question-pools.json').read_text(encoding='utf-8'))
IOL=json.loads((ROOT/'tasks'/TASK/'collection.json').read_text(encoding='utf-8'))['iol_questions']
class Replay:
 def __init__(self,h,key):self.h=h;self.key=key;self.j=Judge.load(ROOT/f'judge/{TASK}/{key}.json',f'{TASK}-{key}',ROOT);self.steps=[];self.negative=0
 async def read(self,a):
  await self.j.read(self.h);fresh=self.j.update(len(self.steps));self.steps.append({'action':a,'new':fresh,'score':self.j.score()});self.h.consume_step()
 async def click(self,loc,unscored=False):
  before=set(self.j.checkpoints)|set(self.j.side)
  loc=self.h.page.locator(loc) if isinstance(loc,str) else loc;loc=loc.first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b
  a={'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2};assert await self.h.act(a)=='ok';await self.read(a)
  if unscored:assert before==set(self.j.checkpoints)|set(self.j.side),'Unscored click gave credit';self.negative+=1
 async def type(self,value):
  loc=self.h.page.locator('#iol-input');await loc.scroll_into_view_if_needed();b=await loc.bounding_box();self.h.elements=[{'n':0,'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}];assert await self.h.act({'op':'type','n':0,'clear':True,'text':value})=='ok';await self.read({'op':'type','value':value})
 async def wait(self,ms):await self.h.act({'op':'wait','ms':ms});await self.read({'op':'wait','ms':ms})
 async def start(self):
  await self.read({'op':'fresh'});assert not self.j.checkpoints and not self.j.side;await self.click(f'button.card[onclick*="show(\'{self.key}\')"]')
 async def quiz(self,target):
  await self.start();seen=[]
  for i in range(10):
   q=await self.h.page.locator(f'#{self.key}-main .quiz-q').inner_text();item=next(x for x in POOLS[self.key]['questions'] if norm(x['q'])==norm(q));seen.append(item['id']);correct=item['opts'][item['a']];wanted=correct if i<target else next(v for v in item['opts'] if v!=correct)
   opts=self.h.page.locator(f'#{self.key}-main .opt');texts=await opts.all_text_contents();idx=next(j for j,v in enumerate(texts) if norm(v)==norm(wanted));await self.click(opts.nth(idx),unscored=i>=target)
   assert len(self.j.checkpoints)==0 and len(self.j.side)==min(i+1,target),(q,self.j.score())
   # Native engine exposes correct option even after a wrong answer; judge must ignore this reveal.
   assert await self.h.page.locator(f'#{self.key}-main .opt.ok').count()==1
   await self.click(f'#{self.key}-next',unscored=True)
  assert self.j.ending_reached and len(self.j.checkpoints)==0 and len(self.j.side)==target,self.j.score()
  title=await self.h.page.locator(f'#{self.key}-main .ending p b').inner_text();await self.h.page.screenshot(path=str(OUT/f'{self.key}-{target}.png'))
  return {'key':self.key,'target':target,'seen':seen,'rank':title,'score':self.j.score(),'unscored_checks':self.negative,'steps':self.steps,'native_submission_log':await self.h.page.evaluate('window.__hushanJudge.attempts')}
 async def iol(self,correct_count):
  await self.start()
  for i,item in enumerate(IOL):
   await self.type('incorrect');await self.click('[onclick="iolCheck()"]',unscored=True)
   assert len(self.j.checkpoints)==min(i,correct_count,3)
   if i<correct_count:
    await self.type(item['answer_private'].upper().replace(' ',' – '));await self.click('[onclick="iolCheck()"]');assert len(self.j.checkpoints)==min(i+1,3)
    # Repeated submit is ignored while answer is disabled.
    await self.click('[onclick="iolCheck()"]',unscored=True);assert await self.h.page.evaluate('IOL.score')==i+1
   else:await self.click('[onclick="iolSkip()"]',unscored=True)
   await self.wait(1600)
  assert self.j.ending_reached and len(self.j.checkpoints)==min(correct_count,3),self.j.score()
  title=await self.h.page.locator('#iol-main .ending p b').inner_text();await self.h.page.screenshot(path=str(OUT/f'iol-{correct_count}.png'))
  return {'key':'iol','correct':correct_count,'rank':title,'score':self.j.score(),'steps':self.steps,'unscored_checks':self.negative,'native_submission_log':await self.h.page.evaluate('window.__hushanJudge.attempts')}
 async def merge(self,policy):
  await self.start();boards=[];negative_done=False;planned=None
  if policy in ['practice','triple']:
   sys.path.insert(0,str(ROOT/f'judge/{TASK}'));from merge_planner import plan
   initial=await self.h.page.locator('.mg-cell').all_text_contents();planned=await asyncio.to_thread(plan,initial,self.h.cfg['seed'],500,policy);print(policy,'UI path planned',planned['offset'],planned['clears'],flush=True)
  def groups(board):
   todo=set(range(36));out=[]
   while todo:
    n=min(todo);todo.remove(n);g={n};q=[n]
    while q:
     n=q.pop();r,c=divmod(n,6)
     for rr,cc in [(r+1,c),(r-1,c),(r,c+1),(r,c-1)]:
      k=rr*6+cc
      if 0<=rr<6 and 0<=cc<6 and k in todo and board[k]==board[n]:todo.remove(k);g.add(k);q.append(k)
    out.append(sorted(g))
   return out
  for move in range(40):
   board=await self.h.page.locator('.mg-cell').all_text_contents();gs=groups(board);single=next((g[0] for g in gs if len(g)==1),None)
   if not negative_done and single is not None:
    old=await self.h.page.locator('#merge-hud').inner_text();await self.click(self.h.page.locator('.mg-cell').nth(single),unscored=True);assert old==await self.h.page.locator('#merge-hud').inner_text();negative_done=True
   options=[g for g in gs if len(g)>=2];assert options
   # Only visible board and known rules guide these auditor actions.
   if planned:
    n=planned['path'][move][0];g=next(g for g in options if n in g);g=[n]+[k for k in g if k!=n]
   else:
    clear=[g for g in options if board[g[0]] in '森众品晶焱淼垚叒三'];g=clear[0] if clear and 'tier3_clear' not in self.j.side else max(options,key=lambda x:(2 if board[x[0]] in '林从吕昌炎沝圭双二' else 0 if board[x[0]] in '木人口日火水土又一' else -1,len(x),-x[0]))
   boards.append({'before':board,'clicked':g[0],'group':g,'char':board[g[0]]});await self.click(self.h.page.locator('.mg-cell').nth(g[0]))
   if planned:assert await self.h.page.locator('.mg-cell').all_text_contents()==planned['path'][move][1],f'Planned board diverged at move {move+1}'
  assert self.j.ending_reached,self.j.score();title=await self.h.page.locator('#merge-main .ending p b').inner_text();assert ('合体练习生' in title)==(policy=='practice'),title
  finalboard=await self.h.page.locator('.mg-cell').all_text_contents();best=await self.h.local_storage();await self.h.page.screenshot(path=str(OUT/f'merge-{policy}.png'))
  # Ended board cannot be changed by another ordinary cell click.
  await self.click('.mg-cell',unscored=True);assert finalboard==await self.h.page.locator('.mg-cell').all_text_contents()
  return {'key':'merge','policy':policy,'planner':None if planned is None else {'kind':'private source and configured RNG audit; live board compared after every ordinary UI click','initial_rng_offset':planned['offset'],'beam_width':planned['width'],'top_level_clears':planned['clears']},'rank':title,'score':self.j.score(),'boards':boards,'final_board':finalboard,'storage':best,'steps':self.steps,'unscored_checks':self.negative,'native_submission_log':await self.h.page.evaluate('window.__hushanJudge.attempts')}
async def main():
 cfg=load_config(ROOT/f'configs/{TASK}-ids.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['port']=args.port;cfg['local_serve']['command'][-1]=str(args.port);cfg['settle_ms']=60
 server=LocalServer();h=BrowserHarness(cfg,OUT);report={'kind':'engineering_curator_replay_not_model_score','root':str(ROOT),'branches':[],'page_errors':[],'http_errors':[]};counter=0
 async def reset(key):
  nonlocal counter
  counter+=1;h.cfg['seed']=20261026+counter;await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);return Replay(h,key)
 try:
  server.start(cfg,ROOT,OUT/'server.log');await h.start()
  if args.original_probe:
   r=await reset('iol');await r.start();await r.type(IOL[0]['answer_private']);await r.click('[onclick="iolCheck()"]');await r.click('[onclick="iolCheck()"]');report['duplicate_submit_native_hud']=await h.page.locator('#iol-hud').inner_text();report['duplicate_submit_private_native_score']=await h.page.evaluate('IOL.score');report['duplicate_confirmed']=report['duplicate_submit_private_native_score']==2;assert report['duplicate_confirmed'];return
  for key in ([] if args.only_merge else POOLS):
   seen=set();accepted=set()
   for target in ([10] if args.deployment_smoke else [10,6,3,0]+[10]*8):
    r=await reset(key);branch=await r.quiz(target);seen.update(branch['seen']);accepted.update(branch['seen'][:target]);branch['seed']=h.cfg['seed'];report['branches'].append(branch);print(key,target,len(seen),'seen,',len(accepted),'correct of16',flush=True)
    if len([b for b in report['branches'] if b['key']==key])>=4 and len(accepted)==16:break
   if not args.deployment_smoke:assert len(accepted)==16,(key,seen,accepted)
  for correct in ([] if args.only_merge else [9] if args.deployment_smoke else [9,0]):r=await reset('iol');report['branches'].append(await r.iol(correct));print('iol',correct,flush=True)
  report['merge_policy_attempts']=[]
  for policy in (['triple'] if args.deployment_smoke else ['triple','practice']):
   for trial in range(12):
    r=await reset('merge')
    try:
     branch=await r.merge(policy);branch['seed']=h.cfg['seed'];report['branches'].append(branch);print('merge',policy,flush=True);break
    except AssertionError as e:
     report['merge_policy_attempts'].append({'policy':policy,'seed':h.cfg['seed'],'failure':str(e),'steps':r.steps});print('merge policy retry',policy,trial,str(e),flush=True)
   else:raise AssertionError('No complete merge route '+policy)
  report['blocked_requests']=h.blocked;assert not report['page_errors'] and not report['http_errors'] and not report['blocked_requests'];report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'));report['body_at_failure']=await h.page.locator('body').inner_text()
  raise
 finally:
  (OUT/('original-probe.json' if args.original_probe else 'deployment-acceptance.json' if args.deployment_smoke else 'merge-acceptance.json' if args.only_merge else 'acceptance.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
if __name__=='__main__':asyncio.run(main())
