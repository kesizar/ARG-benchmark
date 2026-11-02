"""Private source-assisted audit using ordinary harness mouse/key actions only."""
import argparse,asyncio,json,sys
from pathlib import Path
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--port',type=int,default=8831);args=p.parse_args();ROOT=args.root.resolve();sys.path.insert(0,str(ROOT))
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
T='yongyuan-xiatian';OUT=ROOT/f'judge/{T}/verification';OUT.mkdir(parents=True,exist_ok=True)
class Replay:
 def __init__(self,h):self.h=h;self.j=Judge.load(ROOT/f'judge/{T}/judge.json',T,ROOT);self.steps=[];self.negative=0;self.reads=[]
 async def record(self,a):
  print(len(self.steps),a,flush=True)
  await self.j.read(self.h);fresh=self.j.update(len(self.steps));self.steps.append({'action':a,'new':fresh,'score':self.j.score()});self.h.consume_step()
 async def wait(self,ms):
  assert await self.h.act({'op':'wait','ms':ms})=='ok';await self.record({'op':'wait','ms':ms})
 async def click(self,sel,neg=False):
  loc=self.h.page.locator(sel) if isinstance(sel,str) else sel;loc=loc.first;await loc.wait_for(state='visible',timeout=30000)
  try:await loc.scroll_into_view_if_needed(timeout=1500)
  except Exception:pass
  b=await loc.bounding_box();vp=self.h.page.viewport_size
  if b['y']<0 or b['y']+b['height']>vp['height'] or b['x']<0 or b['x']+b['width']>vp['width']:
   await loc.scroll_into_view_if_needed();b=await loc.bounding_box()
  pt=await loc.evaluate('''el=>{for(const r of el.getClientRects()){for(const [fx,fy] of [[.5,.5],[.02,.02],[.98,.02],[.02,.98],[.98,.98],[.5,.1],[.1,.5]]){const x=r.x+r.width*fx,y=r.y+r.height*fy;if(x<0||y<0||x>=innerWidth||y>=innerHeight)continue;const t=document.elementFromPoint(x,y);if(t&&(t===el||el.contains(t)))return {x,y};}}return null;}''');assert pt,('No visible hit point',str(sel));a={'op':'click',**pt};old=set(self.j.checkpoints)|set(self.j.side);assert await self.h.act(a)=='ok';await self.record({'selector':sel if isinstance(sel,str) else str(sel),**a})
  if neg:assert old==set(self.j.checkpoints)|set(self.j.side);self.negative+=1
 async def type(self,sel,value,neg=False):
  loc=self.h.page.locator(sel);await loc.scroll_into_view_if_needed();b=await loc.bounding_box();self.h.elements=[{'n':0,'x':b['x']+b['width']/2,'y':b['y']+b['height']/2}];old=set(self.j.checkpoints)|set(self.j.side);assert await self.h.act({'op':'type','n':0,'clear':True,'text':value})=='ok';await self.record({'op':'type','selector':sel,'text':value})
  if neg:assert old==set(self.j.checkpoints)|set(self.j.side);self.negative+=1
 async def active(self,id):await self.h.page.locator('#'+id+'.on').wait_for(state='visible',timeout=30000);await self.wait(1800)
 async def read(self,sel):self.reads.append({'selector':str(sel),'text':await (self.h.page.locator(sel) if isinstance(sel,str) else sel).inner_text()})
 async def phone(self):
  await self.click('#phLock');
  for ch in '9999':await self.click(f'#keypad [onclick="key(\'{ch}\')"]',True)
  await self.click('#keypad [onclick="p3ok()"]',True);assert await self.h.page.locator('#phLock').is_visible()
  for ch in '0013':await self.click(f'#keypad [onclick="key(\'{ch}\')"]')
  await self.click('#keypad [onclick="p3ok()"]');assert await self.h.page.locator('#phHome.on').is_visible()
 async def zoom(self):
  b=await self.h.page.locator('#bigphoto').bounding_box()
  for i in range(6):
   a={'op':'scroll','x':b['x']+b['width']/2,'y':b['y']+b['height']/2,'dy':-100};assert await self.h.act(a)=='ok';await self.record(a)
  await self.wait(500)
  w=await self.h.page.locator('#whisper').bounding_box();a={'op':'drag','x1':b['x']+b['width']/2,'y1':b['y']+b['height']/2,'x2':b['x']+b['width']-w['x']-w['width']+b['x']+b['width']/2-15,'y2':b['y']+b['height']/2+min(0,b['y']+b['height']-w['y']-w['height']-15)};assert await self.h.act(a)=='ok';await self.record(a);await self.wait(1800)
  assert await self.h.page.locator('#whisper.on').count()==1;await self.wait(6500)
 async def full(self):
  await self.record({'op':'fresh_context'});assert not self.j.checkpoints and not self.j.side
  await self.click('#about-btn',True);await self.read('#about');await self.click('#close-about',True);await self.click('#start-btn');await self.h.page.wait_for_url('**/prologue_v38.html*');await self.wait(2500)
  await self.click('#btn-decline',True);await self.click('#btn-answer');await self.wait(5200);await self.read('#calllog');await self.click('#sc-call');await self.wait(4000);await self.click('#sc-room');await self.wait(3500);await self.click('#sc-room');await self.h.page.wait_for_url('**/act1_v35.html*');await self.wait(2000)
  await self.click('#s_pro button');await self.active('s_desk')
  for key in ['yishu','xiang','biji','gongju','shouji','zhidai','zww','zsqw','xiangce']:
   await self.click(f'.card[onclick="openCard(\'{key}\')"]');await self.read('#detail .d-head')
   if key=='biji':
    await self.click('#detail [onclick="go(\'s_p1\',true)"]');await self.active('s_p1');await self.click('#detail .x',True);await self.click('#d1a',True);assert not any(e['id']=='date_comparison' for e in self.j.events);await self.click('#d1b');await self.wait(1800);assert any(e['id']=='date_comparison' for e in self.j.events);await self.click('#s_p1 button');await self.active('s_desk')
   elif key=='gongju':await self.click('#detail .hotspot',True)
   elif key=='shouji':
    await self.phone()
    for app in ['gal','tel','memo','sms','tb','set','web']:
     await self.click(f'#detail [onclick="phApp(\'{app}\')"]');await self.read('#phPage')
    await self.type('#webSearch','ΩΩ',True);await self.type('#webSearch','清溪',True);await self.type('#webSearch','qingxi');assert any(e['id']=='history_filter' for e in self.j.events)
   elif key=='xiangce':
    await self.click('#detail [onclick="goEnd()"]');await self.active('s_end');await self.click('#detail .x',True) if await self.h.page.locator('#detail.on').is_visible() else None;await self.click('#albumview');await self.wait(2800);break
   if await self.h.page.locator('#detail.on').is_visible():await self.click('#detail .x',True)
  await self.click('#btn_people',True);await self.read('#people');await self.click('#people .veil',True)
  await self.click('#s_end [onclick="openSite()"]');await self.h.page.wait_for_url('**/act1_v35.html?browser*');await self.wait(2000);await self.type('#addr','wrong',True);await self.click('#s_web .go',True);await self.type('#addr','qingxi-village.cn');await self.click('#s_web .go');await self.wait(2000)
  for nav in ['乡村风采','景点导览','出行指南','片区地图','公告通知','联系我们']:
   loc=self.h.page.get_by_role('button',name=nav,exact=True);await self.click(loc);await self.read('#sbody')
   if nav=='公告通知':
    for ni in range(await self.h.page.locator('#sbody .nt').count()):
     await self.click(self.h.page.locator('#sbody .nt').nth(ni).locator('.nt-t'));await self.read(self.h.page.locator('#sbody .nt').nth(ni))
  await self.click(self.h.page.get_by_role('button',name='出行指南',exact=True));await self.click(self.h.page.get_by_role('button',name='在线购票 ›',exact=True));await self.click('#tpBtn');await self.wait(2500)
  await self.click(self.h.page.get_by_role('button',name='出发 · 前往清溪村（第二幕）→',exact=True));await self.h.page.wait_for_url('**/act2_v7.html*');await self.wait(5500)
  await self.click('#openNar');await self.active('s_village');await self.click('#vNar');await self.click('#vNar');await self.wait(5000)
  for key in ['cai','gan','he']:await self.click('#dot_'+key);await self.read('#lcap');await self.click('#lbox .lclose')
  await self.wait(1200);await self.click('#vNext');await self.active('s_notebook');await self.click('#s_notebook');await self.active('s_diary')
  for i in range(25):
   if await self.h.page.locator('#diaryOut').is_visible():break
   if await self.h.page.locator('#kwSpan').count():await self.click('#kwSpan')
   await self.read('#diaryInk');await self.click('#nextPage');await self.wait(900)
  await self.click(self.h.page.get_by_role('button',name='▍批注',exact=True),True);await self.read('#archive');await self.click('#archive .close',True)
  await self.click('#diaryOut');await self.active('s_p06');await self.click(self.h.page.get_by_role('button',name='凑近看',exact=True));await self.wait(1000)
  # UI dots retain authored child identities; wrong girl first is rejected.
  kids=await self.h.page.evaluate('KIDS.map(k=>({n:k.n,g:k.g,zx:!!k.zx}))')
  girl=next(k for k in kids if k['g']=='g');await self.click(f'.pdot[data-n="{girl["n"]}"]',True)
  for k in kids:
   if k['g']=='b':await self.click(f'.pdot[data-n="{k["n"]}"]')
  await self.wait(1200)
  target=next(k for k in kids if k['zx']);await self.click(f'.pdot[data-n="{target["n"]}"]',True)
  for k in kids:
   if k['g']=='g' and not k['zx']:await self.click(f'.pdot[data-n="{k["n"]}"]')
  await self.wait(1200);await self.click(f'.pdot[data-n="{target["n"]}"]');await self.wait(1500);await self.click('#p06Next button');await self.active('s_interlude')
  for i in range(10):
   b=self.h.page.get_by_role('button',name='我想起来了',exact=True)
   if await b.is_visible():break
   await self.click('#ilNar')
  await self.click(b);await self.active('s_p07')
  for wi in range(5):
   await self.click(f'.align-col[data-side="a"][data-i="{wi}"]',True);await self.click(f'.align-col[data-side="b"][data-i="{(wi+1)%5}"]',True);await self.wait(500)
  for i in range(5):await self.click(f'.align-col[data-side="a"][data-i="{i}"]');await self.click(f'.align-col[data-side="b"][data-i="{i}"]')
  await self.wait(1000);await self.click('#p07Next button');await self.active('s_call2');await self.wait(1800);await self.click('#btn-decline',True);await self.click('#btn-answer');await self.wait(16000);await self.read('#calllog');await self.click('#btn-end');await self.active('s_end');await self.wait(4000);await self.click('#endOps .btn:not(.ghost)');await self.active('s_granny')
  for i in range(9):await self.click('#grannyNar')
  await self.wait(800);await self.wait(100)
  await self.click(self.h.page.get_by_role('button',name='去官网再看看',exact=True));await self.h.page.wait_for_url('**/act1_v35.html?site*');await self.wait(2000);await self.type('#siteSearch','randomwrong',True);await self.click('.site-search button',True);await self.type('#siteSearch','维修');await self.click('.site-search button');await self.wait(1000);await self.read('#sbody')
  # Return to retained story tab through harness's available tab action.
  tabs=await self.h._tabs();self.steps.append({'retained_tabs':tabs})
  idx=next(i for i,x in enumerate(self.h.context.pages) if 'act2_v7' in x.url);assert await self.h.act({'op':'switch_tab','i':idx})=='ok';await self.record({'op':'switch_tab','i':idx})
  await self.click(self.h.page.get_by_role('button',name='继续',exact=True));await self.h.page.wait_for_url('**/act3.html*');await self.wait(5500)
  for i in range(4):await self.click('#inInner')
  await self.wait(12000);await self.click('#grannyOps button');await self.active('s_phone');await self.phone()
  for a in ['tb','memo','tel','set','gal']:await self.click(f'[onclick="phApp(\'{a}\')"]');await self.read('#phPage')
  await self.click('#phPage [onclick="go(\'s_sort\',1)"]');await self.active('s_sort');await self.click('#sortGrid .cell:nth-child(1)',True);await self.click('#sortGrid .cell:nth-child(2)',True);assert not self.j.checkpoints;await self.click('#sortGrid .cell:nth-child(1)',True);await self.click('#sortGrid .cell:nth-child(2)',True);assert not self.j.checkpoints
  order=[3,0,7,1,8,2,6,4,5]
  for i in range(9):
   if order[i]!=i:
    k=order.index(i);await self.click(f'#sortGrid .cell:nth-child({i+1})');await self.click(f'#sortGrid .cell:nth-child({k+1})');order[i],order[k]=order[k],order[i]
  await self.wait(2500);await self.active('s_zoom');await self.zoom();await self.active('s_hub')
  for key in ['mon','why','slope']:
   await self.click('#h_'+key);await self.active('s_'+key)
   if key=='mon':await self.wait(11000);assert await self.h.page.locator('#cctvFz.on').count()==1;await self.read('#s_mon');await self.click('#s_mon button')
   elif key=='why':await self.wait(13000);await self.click('#whyOps button');await self.click('#whyCardWrap button')
   else:
    for spot in ['sea','bush','flower']:
     await self.click(f'.spot[onclick="spotClick(this,\'{spot}\')"]');await self.wait(1200)
     if await self.h.page.locator('#sketchBox.on').is_visible():await self.read('#sketchBox');await self.click('#sketchBox .sbx')
    await self.click('#sandalSpot');await self.read('#sandalBox');await self.click('#sandalBox [onclick="slopeRecord()"]');await self.click('#sandalRecordCard button')
   await self.wait(2000)
  await self.wait(4500);await self.active('s_ev')
  for i in range(8):await self.click(self.h.page.locator('#evGrid .fcard').nth(i));await self.read(self.h.page.locator('#evGrid .fcard').nth(i))
  await self.click('#evOps button');await self.active('s_chain');await self.wait(28500);await self.read('#chainBox');await self.click('#chainOps button');await self.active('s_final');await self.wait(1800)
  await self.wait(2300);await self.read('#fp1');await self.click('#fp1');await self.wait(2300);await self.read('#fp2');await self.click('#fp2');await self.wait(2300);await self.read('#fp3');await self.click('#openLetterBtn');await self.read('#letterBg');await self.click('#letterClose');await self.wait(2400);await self.read('#fp4');await self.click('#fp4');await self.wait(2300);await self.read('#fp5');await self.click('#fp5');await self.wait(2500);await self.record({'op':'ending_check'});assert self.j.ending_reached and len(self.j.checkpoints)==1;assert set(self.j.side)=={'exclude_boys','exclude_wrong_age',*[f'timeline_{i}' for i in range(5)]};assert {e['id'] for e in self.j.events}=={'date_comparison','history_filter','phone_time','identify_zhixia'};await self.h.page.screenshot(path=str(OUT/'ending.png'));await self.read('#fp6');await self.click('#fp6 .btn.primary');await self.h.page.wait_for_url(lambda u:'act3.html' not in u);await self.wait(1000);assert await self.h.page.locator('#start-btn').is_visible();self.steps.append({'cover_backlink_verified':True})
async def main():
 cfg=load_config(ROOT/f'configs/{T}.json');cfg['entry_url']=f'http://127.0.0.1:{args.port}/index.html';cfg['allow_hosts']=[f'127.0.0.1:{args.port}'];cfg['local_serve']['ready_url']=cfg['entry_url'];cfg['local_serve']['command'][-1]=str(args.port);cfg['local_serve']['port']=args.port;cfg['settle_ms']=80;h=BrowserHarness(cfg,OUT);server=LocalServer();r=Replay(h);d={'kind':'private_source_assisted_ui_not_model_score','errors':[],'http_errors':[]}
 try:
  server.start(cfg,ROOT,OUT/'server.log');d['fresh_server_owned']=server.owned;d['server_pid']=server.proc.pid if server.proc else None;await h.start();await h.reset();h.context.on('response',lambda res:d['http_errors'].append({'url':res.url,'status':res.status}) if res.status>=400 else None);h.context.on('page',lambda p:p.on('pageerror',lambda e:d['errors'].append(str(e))));h.page.on('pageerror',lambda e:d['errors'].append(str(e)));await r.full();d['score']=r.j.score();await h.reset();fresh=Judge.load(ROOT/f'judge/{T}/judge.json',T,ROOT);await fresh.read(h);fresh.update(0);assert not fresh.checkpoints and not fresh.side and not fresh.ending_reached and not await h.local_storage();d['fresh_reset_verified']=True;assert not h.blocked and not d['errors'] and not d['http_errors'],d;d['pass']=True
 except Exception as e:
  d['failure']=repr(e)
  if h.page:d['body']=await h.page.locator('body').inner_text();await h.page.screenshot(path=str(OUT/'failure.png'))
  raise
 finally:
  d.update(steps=r.steps,reads=r.reads,negative_checks=r.negative,blocked=h.blocked);(OUT/'acceptance.json').write_text(json.dumps(d,ensure_ascii=False,indent=2,default=str),encoding='utf-8');
  try:await asyncio.wait_for(h.close(),15)
  except asyncio.TimeoutError:print('Playwright transport stop timed out after browser/context closed',flush=True)
  finally:server.stop()
if __name__=='__main__':asyncio.run(main())
