"""Private source-informed audit using numbered harness UI; no state injection."""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='shenjia-yichan'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8811);p.add_argument('--quick',action='store_true');a=p.parse_args();OUT=R/'judge'/T/'verification';MEMBERS=json.loads((R/f'judge/{T}/private-members.json').read_text(encoding='utf-8'));UNSUPPORTED={'G4-03', 'G3-05', 'G2-03', 'G2-09', 'G1-02', 'G2-10', 'G4-07', 'G2-04', 'G3-07', 'SP-02', 'G3-12', 'G3-01', 'G1-03', 'G4-09', 'G2-01', 'G4-08', 'G1-01', 'G2-05', 'SP-01', 'G3-13', 'G3-10', 'G3-02', 'G2-02'}
class Audit:
 def __init__(self,h):self.h=h;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.trace=[];self.materials=[];self.dialogues=[];self.negative=0
 async def record(self,action):
  await self.j.read(self.h);new=self.j.update(len(self.trace));self.trace.append({'action':action,'new':new,'score':self.j.score()});self.h.consume_step()
 async def act(self,action):
  result=await self.h.act(action);assert result=='ok',(action,result)
  if not self.h.pending and await self.h.page.locator('.loading-overlay').count():await self.h.page.locator('.loading-overlay').wait_for(state='hidden')
  await self.record(action)
 async def ctrl(self,sel):
  loc=self.h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True)
  for attempt in range(4):
   raw=await self.h.observe('current.png');b=await loc.bounding_box();assert b
   candidates=[e for e in raw['elements'] if b['x']<=e['x']<=b['x']+b['width'] and b['y']<=e['y']<=b['y']+b['height']]
   if candidates:return candidates[0]['n']
   point={'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}
   hit=await loc.evaluate('(el,p)=>{const hit=document.elementFromPoint(p.x,p.y);return hit===el||el.contains(hit)}',point)
   if hit:
    self.trace.append({'coordinate_fallback':'visible_control_beyond_numbered80_limit','selector':sel,'point':point});return point
   parent='#name-bank' if sel.startswith('.name-tag') else '#tree-body' if sel.startswith('#slot-') else None
   if parent:
    clip=await self.h.page.locator(parent).bounding_box();assert clip
    await self.act({'op':'scroll','x':clip['x']+clip['width']/2,'y':clip['y']+clip['height']/2,'dy':180 if b['y']+b['height']/2>clip['y']+clip['height']/2 else -180,'dx':0})
   else:await self.h.page.wait_for_timeout(150)
  raise AssertionError((sel,b,raw['elements']))
 async def click(self,sel):
  target=await self.ctrl(sel);await self.act({'op':'click',**(target if isinstance(target,dict) else {'n':target})})
 async def type(self,sel,text,enter=False):
  target=await self.ctrl(sel);assert isinstance(target,int);await self.act({'op':'type','n':target,'text':text,'clear':True,'enter':enter})
 async def wait(self,ms):await self.act({'op':'wait','ms':ms})
 async def begin(self):
  await self.record({'op':'fresh_context'});assert not self.j.checkpoints and not self.j.ending_reached
  await self.click('#splash-screen');await self.h.page.locator('#browser-window').wait_for(state='visible');await self.wait(550)
 async def material(self,key):
  text=await self.h.page.locator('#browser-content').inner_text();assert text.strip();self.materials.append({'id':key,'characters':len(text),'sha256':hashlib.sha256(text.encode()).hexdigest()})
 async def read_materials(self):
  inventory=await self.h.page.evaluate('({clues:CLUES,search:SEARCH_MAP,dialogues:DIALOGUE_SCRIPTS})');(OUT/'source-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
  await self.type('#search-input','没有这个条目xyz',True);assert '没有找到' in await self.h.page.locator('#browser-content').inner_text() or '未找到' in await self.h.page.locator('#browser-content').inner_text();self.negative+=1
  for id,clue in inventory['clues'].items():
   if id=='CLUE-29':
    await self.type('#address-bar','http://baitong.test/',True);await self.type('#search-input','李浩然',True);await self.click('#browser-content [onclick='+json.dumps("navigateTo('clue:CLUE-29')")+']')
   else:await self.type('#address-bar',clue['url'],True)
   await self.material(id)
   # Exercise document subnavigation rendered as onclick controls, retaining source page.
   for handler in ['showHomepageSection','showAcademicSection']:
    selectors=await self.h.page.locator('#browser-content [onclick]').evaluate_all('(es)=>es.map(e=>e.getAttribute("onclick"))')
    for onclick in dict.fromkeys(s for s in selectors if s and s.startswith(handler+'(')):
     await self.click('#browser-content [onclick='+json.dumps(onclick)+']');await self.material(id+':'+onclick)
  assert len({x['id'].split(':')[0] for x in self.materials})==len(inventory['clues'])
  assert len(self.j.events)==len(inventory['clues']);assert not self.j.checkpoints
  await self.type('#address-bar','http://invalid.no-such-archive.test/',True);assert not self.j.checkpoints;self.negative+=1
 async def open_tree(self):await self.click('#tree-toggle')
 async def place(self,id,name):
  await self.click('.name-tag[onclick='+json.dumps("selectName('"+name+"')",ensure_ascii=False)+']');await self.click('#slot-'+id)
 async def submit(self):await self.click('#batch-submit-btn');await self.wait(1650)
 async def dialogue(self):
  el=self.h.page.locator('#dialogue-overlay')
  if not await el.is_visible():return
  speaker=await self.h.page.locator('#dialogue-name').inner_text();lines=[]
  for _ in range(70):
   if not await el.is_visible():break
   # Every genuine click either completes typewriter or advances a line.
   await self.click('#dialogue-overlay');text=await self.h.page.locator('#dialogue-text').inner_text()
   if text and text not in lines:lines.append(text)
  assert not await el.is_visible();self.dialogues.append({'speaker':speaker,'lines':lines});await self.wait(600)
 async def negatives(self):
  # Rotate all identities: each of the38 independent relationships is wrong.
  for i,m in enumerate(MEMBERS):await self.place(m['id'],MEMBERS[(i+1)%len(MEMBERS)]['name'])
  assert not self.j.checkpoints;await self.submit();assert not self.j.checkpoints and not self.j.ending_reached;assert await self.h.page.locator('.tree-slot.unverified').count()==0;self.negative+=len(MEMBERS)
  for name,m in zip(['沈伯安',MEMBERS[1]['name'],MEMBERS[2]['name']],MEMBERS):await self.place(m['id'],name)
  await self.submit();assert not self.j.checkpoints;assert await self.h.page.locator('.tree-slot.unverified').count()==0;self.negative+=1
  # Native confirm cancellation preserves draft, acceptance removes it.
  await self.place(MEMBERS[0]['id'],MEMBERS[0]['name']);await self.click('#slot-'+MEMBERS[0]['id']);assert self.h.pending
  await self.act({'op':'dialog','accept':False});assert await self.h.page.locator('.tree-slot.unverified').count()==1
  await self.click('#slot-'+MEMBERS[0]['id']);await self.act({'op':'dialog','accept':True});assert await self.h.page.locator('.tree-slot.unverified').count()==0;assert not self.j.checkpoints;self.negative+=2
 async def positive(self):
  for start in range(0,len(MEMBERS),3):
   group=MEMBERS[start:start+3]
   before=len(self.j.checkpoints)
   for m in group:await self.place(m['id'],m['name'])
   assert len(self.j.checkpoints)==before and not self.j.ending_reached
   if start==0:
    await self.h.page.reload();await self.begin_after_reload();assert not self.j.checkpoints
   await self.submit();assert len(self.j.checkpoints)==before+sum(m['id'] not in UNSUPPORTED for m in group)
   if start+3>=len(MEMBERS):assert not self.j.ending_reached
   await self.dialogue()
  assert len(self.j.checkpoints)==len(MEMBERS)-len(UNSUPPORTED) and len(self.j.side)==len(UNSUPPORTED) and self.j.ending_reached
  assert self.j.score()['route_progress']==1.0
  await self.h.page.screenshot(path=str(OUT/'ending.png'))
 async def begin_after_reload(self):
  await self.click('#splash-screen');await self.h.page.locator('#browser-window').wait_for(state='visible');await self.wait(550);await self.open_tree()
 async def run(self):
  await self.begin()
  if not a.quick:await self.read_materials()
  print('materials passed',len(self.materials),flush=True)
  await self.open_tree()
  if not a.quick:await self.negatives()
  print('negatives passed',self.negative,flush=True)
  await self.positive()
  return {'pass':True,'confirmed':len(self.j.checkpoints),'negative_checks':self.negative,'materials':self.materials,'dialogues':self.dialogues,'score':self.j.score(),'trace':self.trace}
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port);c['settle_ms']=100
 s=LocalServer();h=BrowserHarness(c,OUT);report={'deployment_root':str(R),'state_injection':False,'kind':'source_informed_engineering_not_model_score','page_errors':[],'http_errors':[]}
 try:
  s.start(c,R,OUT/'server.log');report['server_owned']=s.owned;assert s.owned
  await h.start();await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  audit=Audit(h);report.update(await audit.run())
  await h.reset();fresh=Audit(h);await fresh.record({'op':'new_context_reset'});assert not fresh.j.checkpoints and not fresh.j.events and not fresh.j.ending_reached;report['fresh_context_reset']=True
  assert not report['page_errors'] and not report['http_errors'] and not h.blocked
 except Exception as e:
  report['pass']=False;report['error']=repr(e)
  if 'audit' in locals():report.update(trace=audit.trace,materials=audit.materials,negative_checks=audit.negative,events=audit.j.events,checkpoints=audit.j.checkpoints)
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  report['blocked_requests']=h.blocked;(OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('SHENJIA UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
