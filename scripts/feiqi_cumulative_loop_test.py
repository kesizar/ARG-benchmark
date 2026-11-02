import asyncio,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.loop import _episode
from harness.serve_local import LocalServer

class Policy:
 def __init__(self,steps):self.steps=steps;self.i=0;self.next={'op':'wait','ms':1}
 def act(self,obs):return self.next
class TestBrowser(BrowserHarness):
 def __init__(self,cfg,out,p):super().__init__(cfg,out);self.p=p
 async def observe(self,*args,**kw):
  raw=await super().observe(*args,**kw); p=self.p
  if p.i>=len(p.steps):p.next={'op':'give_up'};return raw
  step=p.steps[p.i]
  if 'selector' not in step:
   p.next=dict(step);p.i+=1;return raw
  loc=self.page.locator(step['selector']).first
  if not await loc.count(): raise RuntimeError('missing '+step['selector'])
  rect=await loc.evaluate('(e)=>{let r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}}')
  if rect['y']<0 or rect['y']+rect['h']>800:
   p.next={'op':'scroll','dy':max(-650,min(650,rect['y']-300)),'dx':0};return raw
  p.next={'op':'click','x':rect['x']+rect['w']/2,'y':rect['y']+rect['h']/2};p.i+=1;return raw

def actions(target):
 def go(route):return {'op':'goto','url':'http://127.0.0.1:8842/index.html#'+route}
 def click(s):return {'selector':s}
 def typ(s):return {'op':'type','text':s,'clear':True}
 steps=[go('forum'),click('#space-input'),typ('suwanqing'),click('[onclick="tryEnterSpace()"]'),{'op':'wait','ms':1500},go('thread')]
 if target=='follow':return steps
 steps += [go('phone'),click('#phone-key2'),typ('林建国'),click('[onclick^="tryPhoneKey("]'),{'op':'wait','ms':1000},go('thread')]
 if target=='truth':return steps
 steps += [go('intranet'),click('#oa-pass'),typ('guiling'),click('[onclick="tryIntranetLogin()"]'),go('thread')]
 if target=='deeper':return steps
 steps += [go('intranet'),click('[onclick="toggleDoc(\'chen\')"]'),{'op':'dialog','accept':True,'text':'1988'},go('thread')]
 return steps
async def main():
 print('MAIN',flush=True)
 out=R/'judge/feiqi-yiyuan/verification/cumulative-loop';out.mkdir(parents=True,exist_ok=True)
 print('DIR',flush=True)
 results={}
 for label in ['follow','truth','deeper','final','reset_follow']:
  target='follow' if label=='reset_follow' else label
  print('TARGET',target,flush=True)
  cfg=load_config(R/('configs/feiqi-yiyuan-final-draft.json' if target=='final' else 'configs/feiqi-yiyuan-'+target+'.json'))
  cfg['entry_url']='http://127.0.0.1:8842/index.html';cfg['allow_hosts']=['127.0.0.1:8842'];cfg['local_serve'].update(port=8842,ready_url=cfg['entry_url']);cfg['local_serve']['command'][-1]='8842';cfg['settle_ms']=100
  rd=out/label;rd.mkdir(exist_ok=True);p=Policy(actions(target));h=TestBrowser(cfg,rd,p);server=LocalServer()
  try:
   server.start(cfg,R,rd/'server.log'); await h.start();j=Judge.load(R/cfg['judge_path'],cfg['id'],R);s=await _episode(cfg,h,j,p,'script',rd,'test'); results[label]=s
   assert s['ended_reason']=='ending' and s['route_id']==target,(target,s)
   assert s['ending_reached'] and not s['failure_reached']
   if label=='reset_follow': assert s['checkpoints_reached']==1 and not s['events']
   if target=='final': assert set(s['events'])=={'follow_observed','truth_observed','deeper_observed'}
  finally:await h.close();server.stop()
 (out/'result.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
 print('ALL LOOP TARGETS PASS')
asyncio.run(main())
