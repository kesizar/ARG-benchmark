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
   if not self.j.ending_reached:
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
 h=BrowserHarness(cfg,OUT);server=LocalServer();out=[]
 try:
  server.start(cfg,ROOT,OUT/f'closeout-{args.unit}-server.log');await h.start()
  for target in ({'pipa':['caught','honest'],'quiz':['lose','win'],'cross':['lose','win'],'hunt':['burnout','flop','best']}[args.unit]):
   for trial in range(15):
    h.cfg['seed']=20261027+trial;await h.reset();r=Replay(h,args.unit)
    if args.unit=='pipa':b=await r.pipa(target)
    elif args.unit=='quiz':b=await r.quiz(target)
    elif args.unit=='cross':b=await r.cross(target)
    else:
     from planners import hunt_order,hunt_paths
     paths=hunt_paths(INV['H_EVENTS'],hunt_order(h.cfg['seed']))
     if target not in paths:continue
     b=await r.hunt(paths[target])
    score=b['score'];actual=score.get('failure_id') or score.get('route_id')
    if actual==('answer' if target=='honest' else target):
     assert score['failure_reached']==(target in ('caught','lose','burnout')) and score['ending_reached'] != score['failure_reached'],score
     out.append({'target':target,'score':score,'native':b.get('native'),'seed':h.cfg['seed']});print(target,score,flush=True);break
   else:raise AssertionError('could not reach '+target)
  await h.reset();r=Replay(h,args.unit);await r.record({'op':'fresh_context'});assert not r.j.failure_id and not r.j.ending_reached and not r.j.checkpoints
  (OUT/f'closeout-{args.unit}.json').write_text(json.dumps({'pass':True,'results':out,'fresh_reset':True},ensure_ascii=False,indent=2),encoding='utf-8')
 finally:
  await h.close();server.stop()
if __name__=='__main__':asyncio.run(main())
