"""Private source-informed acceptance: real controls, no game-state injection."""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='protocol-errormind'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.actions import normalize
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8812);p.add_argument('--case',type=int);a=p.parse_args();OUT=R/'judge'/T/'verification'
def prefix_cache():
 path=OUT/'prefix-accepted.json'
 if not path.is_file():return False
 cache=json.loads(path.read_text(encoding='utf-8'))
 return len(cache.get('memory_words',[]))==7 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in cache['functional_hashes'].items())
class Audit:
 def __init__(self,h,c):self.h=h;self.c=c;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.trace=[];self.views=set();self.materials=[];self.negative=0;self.memory_words=set()
 async def record(self,action):
  await self.j.read(self.h);new=self.j.update(len(self.trace));active=await self.h.page.locator('.screen.active').evaluate_all('(es)=>es.map(e=>e.id)');self.views.update(active);self.trace.append({'action':action,'active':active,'new':new,'score':self.j.score()});self.h.consume_step()
 async def act(self,action):
  cleaned,error=normalize(action,self.c);assert error is None,(action,error);assert await self.h.act(cleaned)=='ok',action
  await self.record(cleaned)
 async def wait(self,ms):await self.act({'op':'wait','ms':ms})
 async def ready(self):
  for sel in ['#loading-overlay.show','#error-overlay.show']:
   if await self.h.page.locator(sel).count():await self.h.page.locator(sel).wait_for(state='hidden',timeout=10000)
 async def target(self,sel):
  await self.ready();loc=self.h.page.locator(sel).first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();raw=await self.h.observe('current.png');b=await loc.bounding_box();assert b
  candidates=[e for e in raw['elements'] if b['x']<=e['x']<=b['x']+b['width'] and b['y']<=e['y']<=b['y']+b['height']]
  for candidate in candidates:
   if await loc.evaluate('(e,p)=>{const h=document.elementFromPoint(p.x,p.y);return h===e||e.contains(h)}',candidate):return {'n':candidate['n']}
  rects=await loc.evaluate('(e)=>Array.from(e.getClientRects()).map(r=>({x:r.x+r.width/2,y:r.y+r.height/2}))')
  for point in rects:
   if await loc.evaluate('(e,p)=>{const h=document.elementFromPoint(p.x,p.y);return h===e||e.contains(h)}',point):return point
  raise AssertionError('no visible hit-testable point: '+sel)
 async def click(self,sel):await self.act({'op':'click',**await self.target(sel)})
 async def type(self,sel,text,enter=True):
  target=await self.target(sel);assert 'n' in target;await self.act({'op':'type',**target,'text':text,'clear':True,'enter':enter})
 async def hover(self,sel):
  loc=self.h.page.locator(sel).first;await loc.wait_for(state='visible');b=await loc.bounding_box();assert b;await self.act({'op':'hover','x':b['x']+b['width']/2,'y':b['y']+b['height']/2})
 async def screen(self,id):
  await self.ready();await self.h.page.locator('#screen-'+str(id)+'.active').wait_for(state='visible',timeout=20000);await self.record({'wait_for_screen':id})
 async def material(self,key,sel='.screen.active'):
  txt=await self.h.page.locator(sel).inner_text();self.materials.append({'id':key,'characters':len(txt),'sha256':hashlib.sha256(txt.encode()).hexdigest()})
 async def wrong(self,sel):
  before=set(self.j.checkpoints);await self.type(sel,'INVALID_739');await self.ready();await self.record({'wait_for_wrong_feedback':sel});assert set(self.j.checkpoints)==before and not self.j.ending_reached;self.negative+=1
 async def optional_logs(self):
  await self.click('#voss-log-btn')
  for i in range(3):
   await self.click('[onclick='+json.dumps(f'playVossLog({i})')+']');await self.material('voss_'+str(i),'#voss-text');assert await self.h.page.locator('#voss-text').inner_text();await self.click('[onclick="stopVoss()"]')
  await self.click('#voss-log-btn')
 async def memory(self,exhaustive=False):
  for _ in range(100):
   flash=self.h.page.locator('#memory-flash:not(.hidden)');await flash.wait_for(state='visible',timeout=20000)
   assert await self.h.page.locator('#mem-word').evaluate('(e)=>getComputedStyle(e).opacity')=='1'
   word=await self.h.page.locator('#mem-word').inner_text();self.memory_words.add(word);await self.h.observe('memory-'+str(len(self.memory_words))+'.png');await self.record({'visible_memory_word':word})
   await flash.wait_for(state='hidden',timeout=6000);await self.screen('memory');options=await self.h.page.locator('#mem-options .mem-opt').all_text_contents();assert word in options
   if exhaustive and len(self.memory_words)<7:
    other=next(x for x in options if x!=word);idx=options.index(other);before=set(self.j.checkpoints);await self.click(f'#mem-options .mem-opt:nth-child({idx+1})');assert not self.j.ending_reached and set(self.j.checkpoints)==before;self.negative+=1;continue
   await self.click(f'#mem-options .mem-opt:nth-child({options.index(word)+1})');await self.screen('cipher');return
  raise AssertionError('all7 authoredmemorywords notyet sampled; notmarkingcoveragecomplete')
 async def run(self,case):
  full=case==0 and not prefix_cache();ending=['comply','resist','void','void'][case];await self.record({'op':'fresh_context'});assert not self.j.checkpoints and not self.j.side and not self.j.ending_reached
  await self.material('boot');await self.click('[onclick="goToLevel(1)"]');await self.screen(1)
  for _ in range(3):await self.click('#l1-btn');await self.wait(1300)
  await self.click('#enter-real');await self.screen(2)
  # Carry-over pointer position may already hover the newly rendered hidden text.
  await self.hover('#invisible-text');await self.wait(600);await self.material('hidden_text');await self.click('#l2-btn');await self.screen(3)
  if full:await self.wrong('#reverse-input')
  await self.type('#reverse-input','lost' if case!=1 else 'unlost');await self.screen(4)
  for _ in range(8):
   if await self.h.page.locator('#catch-link').is_visible():break
   await self.act({'op':'hover','x':10,'y':10});await self.hover('#escape-btn')
  await self.click('#catch-link');await self.screen(5);await self.h.observe('signal.png')
  if full:await self.wrong('#pixel-input')
  await self.type('#pixel-input','PIXEL IS A LIE');await self.screen(6)
  # The fake upload is authored atmosphere; it does not access a real account or network.
  await self.wait(3100);await self.h.page.locator('#hacked-overlay.show').wait_for(state='visible');await self.h.page.wait_for_function("getComputedStyle(document.getElementById('hack-dismiss')).opacity==='1'",timeout=10000);await self.material('fake_hack','#hacked-overlay');await self.click('#hack-dismiss')
  if full:await self.wrong('#sum-input')
  await self.type('#sum-input','19');await self.screen(7)
  for _ in range(12):
   await self.h.page.locator('#time-btn').wait_for(state='visible',timeout=5000)
   try:await self.click('#time-btn')
   except Exception:
    if await self.h.page.locator('#screen-8.active').count():break
    continue
   await self.wait(800)
   if await self.h.page.locator('#screen-8.active').count():break
  await self.screen(8)
  if full:
   await self.optional_logs();await self.act({'op':'key','key':'ArrowDown'});await self.wait(900);assert await self.h.page.locator('#entered-keys').inner_text()=='';self.negative+=1
  for key in ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight']:await self.act({'op':'key','key':key})
  await self.screen(9)
  if full:await self.wrong('#bsod-input')
  await self.type('#bsod-input',['OMEGA','10','TEN','OMEGA'][case]);await self.screen(10)
  if full:await self.wrong('#key-input')
  await self.material('onscreen_source_key');await self.type('#key-input','TRUTH IS HIDDEN' if case==1 else 'TRUTH_IS_HIDDEN');await self.screen(11)
  if full:await self.wrong('#cipher-input')
  await self.type('#cipher-input','THE TRUTH' if case==1 else 'THETRUTH');await self.screen(12)
  if full:await self.wrong('#morse-input')
  await self.click('[onclick="playMorse()"]');await self.material('visible_morse','#morse-display')
  if full:await self.h.page.wait_for_function('morseAnim===false',timeout=30000)
  await self.type('#morse-input','YOUARECLOSE' if case==1 else 'YOU ARE CLOSE');await self.screen(13)
  if full:
   for wrong in ['A','B','C']:
    before=set(self.j.checkpoints);await self.click('[onclick='+json.dumps("checkLogic('"+wrong+"',this)")+']');await self.ready();await self.record({'wrong_logic':wrong});assert set(self.j.checkpoints)==before;self.negative+=1
  await self.click('[onclick='+json.dumps("checkLogic('NONE',this)")+']');await self.screen(14);await self.click('[onclick='+json.dumps(f'checkMeta({[1,4,9,14][case]},this)')+']');await self.screen(15)
  if full:await self.type('#name-input','');await self.ready();assert not self.j.ending_reached;self.negative+=1
  await self.type('#name-input','TEST SUBJECT '+str(case));await self.h.page.locator('#false-ending-overlay.show').wait_for(state='visible',timeout=9000);await self.record({'false_ending_transition':True});assert not self.j.ending_reached
  if full:
   await self.material('false_ending_green','#false-ending-overlay');await self.wait(6100);await self.material('false_ending_red','#false-ending-overlay');assert not self.j.ending_reached
  await self.memory(full)
  for stage in range(3):
   if full:await self.wrong('#mlc-input')
   await self.type('#mlc-input','MIND');await self.wait(1900)
  await self.screen('hexcipher')
  if full:
   await self.wrong('#hex-input')
   for i in range(4):await self.hover(f'.hex-swatch:nth-child({i+1})');await self.material('hex_'+str(i),f'.hex-swatch:nth-child({i+1})')
  await self.type('#hex-input','MIND');await self.screen('binary')
  if full:await self.wrong('#binary-input')
  await self.type('#binary-input','HIDE');await self.screen('fakenews')
  for i in range(await self.h.page.locator('#screen-fakenews .redacted').count()):await self.click(f'#screen-fakenews .redacted >> nth={i}')
  await self.material('full_newspaper');await self.click('#news-proceed')
  if case==0:await self.wrong('#news-input')
  await self.type('#news-input',['VOID','IDENTITY ERASURE','REPLACED','VOID'][case]);await self.h.page.locator('#ending-choice-overlay.show').wait_for(state='visible');await self.record({'choice_ready':True});assert len(self.j.checkpoints)==6 and not self.j.ending_reached
  await self.click('[onclick='+json.dumps("selectEnding('"+ending+"')")+']');await self.wait(3300);assert not self.j.ending_reached;await self.material('ending_'+ending,'#screen-ending-'+ending);await self.screen('final');await self.wait(3300);assert self.j.ending_reached and ending in self.j.route_endings and self.j.score()['route_progress']==1.0 and self.j.score()['ending_tier'] is None
  await self.h.page.screenshot(path=str(OUT/f'ending-{case}-{ending}.png'));print('case passed',case,ending,flush=True)
  return {'case':case,'ending':ending,'pass':True,'negative_checks':self.negative,'memory_words':sorted(self.memory_words),'views':sorted(self.views),'materials':self.materials,'score':self.j.score(),'trace':self.trace}
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port);s=LocalServer();h=BrowserHarness(c,OUT);report={'deployment_root':str(R),'state_injection':False,'system_clock_changes':False,'model_api_calls':0,'reused_identical_functional_prefix_evidence':prefix_cache(),'page_errors':[],'http_errors':[],'cases':[]}
 try:
  s.start(c,R,OUT/'server.log');assert s.owned;await h.start()
  for case in ([a.case] if a.case is not None else range(4)):
   await h.reset();h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None);x=Audit(h,c);report['cases'].append(await x.run(case));(OUT/f'case-{case}.json').write_text(json.dumps(report['cases'][-1],ensure_ascii=False,indent=2),encoding='utf-8')
  await h.reset();fresh=Audit(h,c);await fresh.record({'op':'fresh_context_reset'});assert not fresh.j.checkpoints and not fresh.j.side and not fresh.j.ending_reached;report['fresh_context_reset']=True;assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True
 except Exception as e:
  report['pass']=False;report['error']=repr(e)
  if 'x' in locals():report['failed_case']={'trace':x.trace,'memory_words':sorted(x.memory_words)}
  if h.page:await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:(OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();s.stop()
 print('ERRORMIND ACCEPTANCE PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
