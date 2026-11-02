"""Private source-informed terminal/UI audit, no function calls or progress injection."""
import argparse,asyncio,json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='k7-dangan'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8812);a=p.parse_args();OUT=R/'judge'/T/'verification';INV=json.loads((R/f'judge/{T}/source-inventory.json').read_text(encoding='utf-8'));END={e['id']:e for e in INV['endings']};REACH={e['id'] for e in INV['endings'] if e['reachable']}
class Audit:
 def __init__(self,h):self.h=h;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.trace=[];self.negative=0;self.files=[];self.web=[];self.dialogs=[];self.last_dialogs=[]
 async def record(self,action):
  await self.j.read(self.h);new=self.j.update(len(self.trace));self.trace.append({'action':action,'fresh':new,'command_count':await self.h.page.evaluate('G.cmdCount'),'score':self.j.score()});self.h.consume_step()
 async def ctrl(self,sel):
  loc=self.h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True)
  b=await loc.bounding_box();assert b
  if sel=='#cmd':
   for e in self.h.elements:
    if b['x']<=e['x']<=b['x']+b['width'] and b['y']<=e['y']<=b['y']+b['height'] and await loc.evaluate('(el,p)=>document.elementFromPoint(p.x,p.y)===el',e):return e['n']
  obs=await self.h.observe('current.png');es=[e for e in obs['elements'] if b['x']<=e['x']<=b['x']+b['width'] and b['y']<=e['y']<=b['y']+b['height']];assert es,(sel,obs['elements']);return es[0]['n']
 async def click(self,sel):
  assert await self.h.act({'op':'click','n':await self.ctrl(sel)})=='ok';self.last_dialogs=self.h.dialogs_step();await self.record({'op':'click','selector':sel})
 async def type(self,sel,text,enter=False):
  assert await self.h.act({'op':'type','n':await self.ctrl(sel),'text':text,'clear':True,'enter':enter})=='ok'
 async def cmd(self,text,negative=False,auto_continue=True):
  await self.h.page.wait_for_function("!document.getElementById('cmd').disabled")
  before=set(await self.h.page.evaluate('Object.keys(G.endings)'));unlocked=await self.h.page.evaluate('G.unlocked')
  await self.type('#cmd',text,True);await self.h.page.wait_for_function("!document.getElementById('cmd').disabled",timeout=25000)
  assert '系統錯誤：' not in await self.h.page.locator('#out').inner_text()
  after=set(await self.h.page.evaluate('Object.keys(G.endings)'));fresh=after-before
  for end in fresh:
   await self.h.page.wait_for_function("(title)=>G.gameOver && document.getElementById('out').textContent.includes(title) && document.getElementById('out').textContent.includes('輸入 continue')",arg=END[end]['name'],timeout=15000)
  if text.split(' ')[0] in ['restart']:await self.h.page.wait_for_timeout(1800)
  await self.record({'op':'terminal_input','text':('[private key input]' if 'SILVERMOONBEACON' in text else text)})
  if negative:
   assert not fresh and unlocked==await self.h.page.evaluate('G.unlocked');self.negative+=1
  for end in fresh:await self.h.page.screenshot(path=str(OUT/f'ending-{end}.png'))
  if fresh and auto_continue:await self.cmd('continue')
  return fresh
 async def web_views(self):
  await self.cmd('www');assert await self.h.page.locator('#website.active').count()
  for page in INV['web_pages']:
   if page!='index':await self.click('#webBody a[onclick="webGo(\''+page+'\')"]')
   body=await self.h.page.locator('#webBody').inner_text();assert body.strip();self.web.append({'id':page,'characters':len(body),'sha256':hashlib.sha256(body.encode()).hexdigest()})
   if page=='bbs':
    for text in ['???','否','是','maybe']:
     await self.type('#bbsReply',text);await self.click('#webBody [onclick="bbsSubmit()"]');await self.h.page.wait_for_timeout(400);dialogs=self.last_dialogs or self.h.dialogs_step();assert dialogs and dialogs[-1]['type']=='alert'
     self.dialogs.append(dialogs[-1]['message']);await self.record({'op':'auto_accepted_alert','choice':text});assert len(self.j.route_endings)==len(await self.h.page.evaluate('Object.keys(G.endings)'))
   if page!='index':await self.click('#webBody a[onclick="webGo(\'index\')"]')
  await self.click('[onclick="closeWeb()"]')
 async def full(self):
  await self.h.page.wait_for_timeout(1800);await self.record({'op':'reset'});assert not self.j.ending_reached
  for text in ['unknown_command_7391','unlock wrong','unlock','ls /VAULT','cat /VAULT/MANIFEST.TXT','cat missing_file','base64 !!!','continue']:
   await self.cmd(text,negative=True)
  await self.cmd('help');await self.cmd('ls -a /');await self.cmd('cd /STAFF');await self.cmd('ls -a');await self.cmd('pwd');await self.cmd('cd ..')
  initial=await self.h.page.evaluate('Object.fromEntries(Object.entries(FILES).map(([k,v])=>[k,{empty:v==="",size:v.length}]))')
  for path,meta in sorted(initial.items()):
   for attempt in range(3):
    seen=set(await self.h.page.evaluate('Array.from(G.seen)'));await self.cmd('cat '+path)
    if meta['empty'] or path in await self.h.page.evaluate('Array.from(G.seen)'):break
   else:raise AssertionError('Failed to read file '+path)
   self.files.append({'path':path,**meta})
  for path in sorted(set(await self.h.page.evaluate('Object.keys(FILES)'))-set(initial)):
   await self.cmd('cat '+path);self.files.append({'path':path,'dynamic':True})
  for cmd in ['hex /SIGNAL/RAW.DAT','base64 U0lMVkVS','base64 QkVBQ09O','ps','whoami','42','47','monitor']:
   await self.cmd(cmd)
  await self.web_views();await self.cmd('call');await self.cmd('exit');assert 'E01' not in self.j.route_endings
  # Raw key yields H02 without unlocking; normal command requires unlock prefix.
  await self.cmd('SILVERMOONBEACON');assert 'H02' in self.j.route_endings and not await self.h.page.evaluate('G.unlocked')
  await self.cmd('unlock SILVERMOONBEACON');assert await self.h.page.evaluate('G.unlocked') and any(e['id']=='vault' for e in self.j.events)
  await self.cmd('ls /VAULT')
  for path in INV['vault_files']:
   for attempt in range(3):
    await self.cmd('cat '+path)
    if path in await self.h.page.evaluate('Array.from(G.seen)'):break
   else:raise AssertionError('Failed to read vault file '+path)
   self.files.append({'path':path,'vault':True})
  for c in ['report','publish','count','respond','destroy','investigate','decode','observe','excavate','collect','goodbye']:
   await self.cmd(c)
  await self.cmd('date');assert 'E09' in self.j.route_endings
  await self.cmd('listen');assert 'E10' not in self.j.route_endings
  await self.cmd('listen');assert 'E10' in self.j.route_endings
  for name in ['marshall','voss','ferrari','okonkwo','han','sorensen','delgado','k7','you','me','nobody']:await self.cmd('talk '+name)
  while 'H05' not in self.j.route_endings:await self.cmd('pwd')
  assert set(self.j.route_endings)==REACH,(set(self.j.route_endings),REACH)
  assert not ({'E01','H03'} & set(self.j.route_endings));assert not self.j.checkpoints and not self.j.side
  # Source restart, not injected state, must clear saved unlock and endings.
  await self.cmd('restart',auto_continue=False);assert await self.h.page.evaluate('!G.unlocked && Object.keys(G.endings).length===0');assert await self.h.page.evaluate('localStorage.length')==0
  return {'path':'all_reachable_endings_all_materials','score':self.j.score(),'endings':sorted(self.j.route_endings),'files':self.files,'web':self.web,'bbs_alerts':self.dialogs,'negative_checks':self.negative,'restart_reset_pass':True,'trace':self.trace}
def cfg_for(window):
 c=load_config(R/f'configs/{T}.json');target=2 if window=='night' else 12;offset=(target-datetime.now(timezone.utc).hour+12)%24-12;c['timezone']='Etc/GMT'+('+'+str(-offset) if offset<0 else '-'+str(offset) if offset>0 else '');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port);return c
async def main():
 OUT.mkdir(parents=True,exist_ok=True);s=LocalServer();h=None;report={'deployment_root':str(R),'kind':'engineering_not_model_score','state_injection':False,'coordinate_override':False,'page_errors':[],'http_errors':[],'branches':[]}
 try:
  c=cfg_for('night');s.start(c,R,OUT/'server.log');h=BrowserHarness(c,OUT);await h.start();await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);hour=await h.page.evaluate('new Date().getHours()');assert hour<5 or hour>=23;report['night_timezone']=c['timezone'];report['night_hour']=hour
  report['branches'].append(await Audit(h).full());assert not h.blocked;await h.close();h=None
  c=cfg_for('day');h=BrowserHarness(c,OUT);await h.start();await h.reset();hour=await h.page.evaluate('new Date().getHours()');assert 5<=hour<23;report['day_timezone']=c['timezone'];report['day_hour']=hour;b=Audit(h);await b.record({'op':'fresh_day_context'});await b.cmd('date',negative=True);assert not b.j.ending_reached;await b.cmd('report');assert set(b.j.route_endings)=={'E02'};assert not await h.page.evaluate('G.unlocked');report['branches'].append({'path':'day_date_negative_then_unconditional_report','negative_checks':b.negative,'score':b.j.score(),'trace':b.trace})
  assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h and h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  (OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  if h:await h.close()
  s.stop()
 print('K7 FULL UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
