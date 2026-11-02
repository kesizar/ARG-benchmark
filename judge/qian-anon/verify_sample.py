"""Private UI curator replay. Source keys are never exposed to tested model."""
import argparse,asyncio,collections,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--port',type=int,default=8831);p.add_argument('--unit',required=True);p.add_argument('--deployment-smoke',action='store_true');args=p.parse_args();ROOT=args.root.resolve();sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
TASK='qian-anon';OUT=ROOT/f'judge/{TASK}/verification';OUT.mkdir(parents=True,exist_ok=True);INV=json.loads((ROOT/f'judge/{TASK}/source-inventory.json').read_text(encoding='utf-8'))
class Replay:
 def __init__(self,h,key):self.h=h;self.key=key;self.j=Judge.load(ROOT/f'judge/{TASK}/{key}.json',f'{TASK}-{key}',ROOT);self.steps=[];self.negative=0
 async def record(self,a):
  await self.j.read(self.h);fresh=self.j.update(len(self.steps));self.steps.append({'action':a,'new':fresh,'score':self.j.score()});self.h.consume_step()
 async def click(self,loc,negative=False):
  before=set(self.j.checkpoints)|set(self.j.side);loc=self.h.page.locator(loc) if isinstance(loc,str) else loc;loc=loc.first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();a={'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2};assert await self.h.act(a)=='ok';await self.record(a)
  if negative:assert before==set(self.j.checkpoints)|set(self.j.side),'Unscored action got credit';self.negative+=1
 async def type(self,sel,value):
  loc=self.h.page.locator(sel);await loc.scroll_into_view_if_needed();b=await loc.bounding_box();self.h.elements=[{'n':0,'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}];assert await self.h.act({'op':'type','n':0,'clear':True,'text':value})=='ok';await self.record({'op':'type','value':value})
 async def wait(self,ms):assert await self.h.act({'op':'wait','ms':ms})=='ok';await self.record({'op':'wait','ms':ms})
 async def press(self,k,negative=False):
  before=set(self.j.checkpoints)|set(self.j.side);assert await self.h.act({'op':'key','key':k})=='ok';await self.record({'op':'key','key':k})
  if negative:assert before==set(self.j.checkpoints)|set(self.j.side);self.negative+=1
 async def start(self):await self.record({'op':'fresh_context'});assert not self.j.checkpoints and not self.j.side;await self.click(f'button.card[onclick*="show(\'{self.key}\')"]')
 async def finish(self,label,extra=None):
  assert self.j.ending_reached or self.j.failure_id,self.j.score();await self.h.page.screenshot(path=str(OUT/f'{self.key}-{label}.png'));return {'key':self.key,'label':label,'seed':self.h.cfg['seed'],'score':self.j.score(),'steps':self.steps,'unscored_checks':self.negative,**(extra or {})}
 async def pipa(self,mode):
  await self.start();await self.type('#pipa-chant','wrong');await self.click('[onclick="pipaChant()"]',True);assert not self.j.side
  if mode=='buff':
   await self.type('#pipa-chant','PoPiPa');await self.click('[onclick="pipaChant()"]');assert 'star_buff' in self.j.side
   await self.type('#pipa-chant','popipa');await self.click('[onclick="pipaChant()"]',True);assert await self.h.page.evaluate('PP.buff')==3
   for _ in range(3):await self.click('[onclick="pipaCheat()"]')
  elif mode=='caught':
   while not self.j.ending_reached and not self.j.failure_id:
    if '巡视' in await self.h.page.locator('#pipa-lamp').inner_text():await self.click('[onclick="pipaCheat()"]',True)
    else:await self.wait(100)
   assert not self.j.checkpoints
  elif mode=='safe':
   while not self.j.ending_reached and not self.j.failure_id:
    if '背过身' in await self.h.page.locator('#pipa-lamp').inner_text():await self.click('[onclick="pipaCheat()"]')
    else:await self.wait(100)
  else:
   for _ in range(6):await self.click('[onclick="pipaHonest()"]')
  assert (self.j.failure_id=='caught' if mode=='caught' else self.j.score()['route_id']=='answer');return await self.finish(mode,{'native':await self.h.page.evaluate('({prog:PP.prog,strikes:PP.strikes,buff:PP.buff})')})
 async def gal(self,choices):
  await self.start();used=[]
  for day,choice in enumerate(choices):
   used.append({'day':day+1,'choice':choice,'text':INV['GAL_SCENES'][day]['c'][choice][0]});await self.click(self.h.page.locator('#gal-choices .opt').nth(choice))
   nxt=self.h.page.locator('#gal-choices .btn')
   if day<6:await self.click(nxt)
  return await self.finish(''.join(map(str,choices)),{'choices':used,'affection':await self.h.page.evaluate('GAL.aff')})
 async def cross(self,mode):
  await self.start();words=[];lock_checks=[]
  # Passive native-input boundary probe; never calls game handlers or mutates game state.
  await self.h.page.evaluate("""() => {window.__qianCrossInput=[]; for(const type of ['pointerdown','click']) document.addEventListener(type,e=>{const b=e.target.closest?.('[onclick=\"crossStumble(true)\"]');if(b)window.__qianCrossInput.push({type,busy:CX.busy,disabled:b.disabled,a:CX.aPos,s:CX.sPos,turn:CX.turn});},true);} """)
  await self.type('#cw-input','Q');before=await self.h.page.evaluate('CX.aPos');await self.click('[onclick="crossJump()"]',True);assert await self.h.page.evaluate('CX.aPos')==before
  for turn in range(80):
   if self.j.ending_reached or self.j.failure_id:break
   if mode=='lose':await self.click('[onclick="crossStumble(true)"]',True)
   else:
    cells=await self.h.page.locator('.cw-cell').evaluate_all("es=>es.map(e=>({text:e.textContent,here:e.classList.contains('hereA')}))");pos=next(i for i,x in enumerate(cells) if x['here']);track=''.join(x['text'][0] for x in cells);word=next((track[pos+1:pos+1+n] for n in [6,5,4,3] if len(track[pos+1:pos+1+n])==n and track[pos+1:pos+1+n] in INV['WORDS']),None)
    if word:words.append(word);await self.type('#cw-input',word.lower());await self.click('[onclick="crossJump()"]')
    else:await self.click('[onclick="crossStumble(true)"]',True)
   # Controls are disabled throughout foe turn; normal extra mouse click cannot advance player.
   if not self.j.ending_reached and not self.j.failure_id:
    offset=await self.h.page.evaluate('window.__qianCrossInput.length');loc=self.h.page.locator('[onclick="crossStumble(true)"]');b=await loc.bounding_box();assert await self.h.act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})=='ok'
    probe=await self.h.page.evaluate('(offset)=>({events:window.__qianCrossInput.slice(offset),afterA:CX.aPos})',offset);down=next((e for e in probe['events'] if e['type']=='pointerdown'),None);enabled_click=any(e['type']=='click' and not e['disabled'] and not e['busy'] for e in probe['events'])
    probe['proved_busy_rejection']=bool(down and down['busy'] and down['disabled'] and not enabled_click)
    if probe['proved_busy_rejection']:assert probe['afterA']==down['a'];self.negative+=1
    lock_checks.append(probe);await self.record({'op':'extra_click_at_native_turn_boundary','busy_rejection_verified':probe['proved_busy_rejection']})
    await self.wait(720)
  assert (self.j.ending_reached or self.j.failure_id) and any(c['proved_busy_rejection'] for c in lock_checks);return await self.finish(mode,{'words':words,'turn_lock_checks':lock_checks,'native':await self.h.page.evaluate('({a:CX.aPos,s:CX.sPos,turn:CX.turn})')})
 async def maze(self):
  await self.start();cells=await self.h.page.locator('#maze-grid .mz').evaluate_all("es=>es.map(e=>({wall:e.classList.contains('wall'),star:e.classList.contains('star'),text:e.textContent}))");walls={i for i,c in enumerate(cells) if c['wall']};stars={i:c['text'] for i,c in enumerate(cells) if c['star']};pos=0;visited=[]
  old=await self.h.page.evaluate('MZ.steps');await self.press('ArrowLeft',True);assert old==await self.h.page.evaluate('MZ.steps')
  def path(start,end):
   todo=collections.deque([start]);prev={start:None}
   while todo:
    cur=todo.popleft()
    if cur==end:break
    r,c=divmod(cur,15)
    for rr,cc in [(r+1,c),(r-1,c),(r,c+1),(r,c-1)]:
     n=rr*15+cc
     if 0<=rr<11 and 0<=cc<15 and n not in walls and n not in prev:prev[n]=cur;todo.append(n)
   p=[];cur=end
   while cur!=start:p.append(cur);cur=prev[cur]
   return p[::-1]
  async def walk(target):
   nonlocal pos
   for n in path(pos,target):
    dr,dc=divmod(n,15)[0]-divmod(pos,15)[0],divmod(n,15)[1]-divmod(pos,15)[1];key='ArrowDown' if dr==1 else 'ArrowUp' if dr==-1 else 'ArrowRight' if dc==1 else 'ArrowLeft';await self.press(key);pos=n;visited.append(n)
  direct=path(0,164);early_locked=len(set(direct)&set(stars))<4
  if early_locked:
   await walk(164);assert not self.j.ending_reached and '出口被锁' in await self.h.page.locator('#maze-main').inner_text()
  for target in stars:
   if target not in visited:await walk(target)
  await walk(164);assert len(self.j.checkpoints)==1;return await self.finish('escaped',{'initial_visible_grid':cells,'route':visited,'early_locked_exit_verified':early_locked,'native_steps':await self.h.page.evaluate('MZ.steps')})
 async def hunt(self,choices,coverage=None):
  await self.start();events=[];native_order=[]
  for day in range(10):
   if self.j.ending_reached or self.j.failure_id:break
   title=await self.h.page.locator('#hunt-main h3').inner_text();ei=next(i for i,e in enumerate(INV['H_EVENTS']) if title.endswith(e['t']));native_order.append(ei)
   if choices is None:
    candidates=[ci for ci in range(3) if (ei,ci) not in coverage] or list(range(3));ci=max(candidates,key=lambda i:INV['H_EVENTS'][ei]['c'][i][1].get('e',0))
   else:ci=choices[day]
   events.append({'event':ei,'choice':ci,'name':INV['H_EVENTS'][ei]['t']});await self.click(self.h.page.locator('#hunt-main .opt').nth(ci),True)
   await self.click('#hunt-main [onclick="huntRender()"]')
  from planners import hunt_order
  assert native_order==hunt_order(self.h.cfg['seed'])[:len(native_order)],(native_order,hunt_order(self.h.cfg['seed']))
  return await self.finish(str(self.h.cfg['seed']),{'events':events,'native':await self.h.page.evaluate('({c:H.c,l:H.l,e:H.e,r:H.r,day:H.day})')})

 async def quiz(self,mode):
  await self.start();questions=[]
  for round_index in range(10):
   await self.click('#quiz-hand .q-card');await self.click('#quiz-throw');await self.h.page.locator('#quiz-main .opt').first.wait_for(state='visible',timeout=6000)
   q=(await self.h.page.locator('#quiz-main > p').nth(1).inner_text()).strip();item=next(x for x in INV['NAZO'] if x['q']==q);question_id=INV['NAZO'].index(item);texts=await self.h.page.locator('#quiz-main .opt').all_text_contents();opts=[x.split('. ',1)[1] for x in texts]
   if mode=='win':correct=True
   elif mode=='lose':correct=False
   else:
    # Balance only the visible current score; no robot random outcome is fabricated.
    hud=await self.h.page.locator('#quiz-hud').inner_text();ps=int(re.search(r'千早爱音 (\d+) 分',hud).group(1));rs=int(re.search(r'机器人 (\d+) 分',hud).group(1));correct=ps-rs<=-1
   choice=next(i for i,x in enumerate(opts) if (x==item['a'])==correct);before=len(self.j.side);await self.click(self.h.page.locator('#quiz-main .opt').nth(choice),not correct);assert len(self.j.side)==before+int(correct)
   questions.append({'id':question_id,'q':q,'choice':opts[choice],'correct':correct});await self.wait(980)
  return await self.finish(str(self.h.cfg['seed']),{'questions':questions,'native':await self.h.page.evaluate('({ps:QZ.ps,rs:QZ.rs,round:QZ.round})')})

async def main():
 cfg=load_config(ROOT/f'configs/{TASK}-{args.unit}.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(args.port);cfg['local_serve']['port']=args.port;cfg['settle_ms']=30
 h=BrowserHarness(cfg,OUT);server=LocalServer();report={'unit':args.unit,'kind':'source_assisted_engineering_ui_audit_not_model_score','root':str(ROOT),'branches':[],'page_errors':[],'http_errors':[]};counter=0
 async def reset():
  nonlocal counter
  counter+=1;h.cfg['seed']=20261026+counter;await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda res:report['http_errors'].append({'url':res.url,'status':res.status}) if res.status>=400 else None);return Replay(h,args.unit)
 try:
  server.start(cfg,ROOT,OUT/f'{args.unit}-server.log');await h.start()
  if args.unit=='pipa':
   for mode in (['buff'] if args.deployment_smoke else ['honest','buff','safe','caught']):r=await reset();report['branches'].append(await r.pipa(mode));print(args.unit,mode,flush=True)
  elif args.unit=='gal':
   for choices in ([[0]*7] if args.deployment_smoke else [[0]*7,[1]*7,[2]*7,[1,1,1,2,2,2,2]]):r=await reset();report['branches'].append(await r.gal(choices));print(args.unit,choices,flush=True)
  elif args.unit=='maze':r=await reset();report['branches'].append(await r.maze());assert report['branches'][-1]['early_locked_exit_verified']
  elif args.unit=='cross':
   for mode in (['win'] if args.deployment_smoke else ['win','lose']):
    for trial in range(10):
     r=await reset();b=await r.cross(mode);report['branches'].append(b);print('cross requested',mode,'got',(b['score'].get('failure_id') or b['score']['route_id']),flush=True)
     if (b['score'].get('failure_id') or b['score']['route_id'])==mode:break
    else:raise AssertionError('No target cross outcome')
  elif args.unit=='quiz':
   got=set();correct_seen=set()
   for trial in range(40):
    mode='win' if args.deployment_smoke else 'lose' if 'lose' not in got else 'draw' if 'draw' not in got else 'win';r=await reset();b=await r.quiz(mode);report['branches'].append(b);got.add((b['score'].get('failure_id') or b['score']['route_id']));correct_seen.update(x['id'] for x in b['questions'] if x['correct']);print('quiz requested',mode,'got',(b['score'].get('failure_id') or b['score']['route_id']),len(correct_seen),'of22 correct',flush=True)
    if args.deployment_smoke or (len(got)==3 and len(correct_seen)==22):break
   assert args.deployment_smoke or (len(got)==3 and len(correct_seen)==22),(got,correct_seen)
  elif args.unit=='hunt':
   from planners import hunt_order,hunt_paths
   got=set();coverage=set()
   for trial in range(80):
    r=await reset();paths=hunt_paths(INV['H_EVENTS'],hunt_order(h.cfg['seed']));missing=[k for k in ['best','great','normal','flop','burnout'] if k not in got and k in paths];target=missing[0] if missing else None
    b=await r.hunt(paths[target] if target else None,coverage);report['branches'].append(b);got.add((b['score'].get('failure_id') or b['score']['route_id']));coverage.update((x['event'],x['choice']) for x in b['events']);print('hunt',(b['score'].get('failure_id') or b['score']['route_id']),len(coverage),'of72',flush=True)
    if args.deployment_smoke or (len(got)==5 and len(coverage)==72):break
   assert args.deployment_smoke or (len(got)==5 and len(coverage)==72),(got,coverage)
  else:raise NotImplementedError(args.unit)
  assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page:await h.page.screenshot(path=str(OUT/f'{args.unit}-failure.png'));report['body_at_failure']=await h.page.locator('body').inner_text()
  raise
 finally:
  (OUT/f'{args.unit}-deployment-acceptance.json' if args.deployment_smoke else OUT/f'{args.unit}-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
if __name__=='__main__':asyncio.run(main())
