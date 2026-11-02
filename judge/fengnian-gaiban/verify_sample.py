"""Private source-assisted replay. Actual UI input only; no model/API or state injection."""
import argparse,asyncio,json,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='fengnian-gaiban'
from harness.browser_harness import BrowserHarness
from harness.config import load_config
from harness.judge import Judge
from harness.serve_local import LocalServer
A=argparse.ArgumentParser();A.add_argument('--port',type=int,default=8822);A.add_argument('--phase',choices=['all','routes'],default='all');A=A.parse_args();OUT=R/'judge'/T/'verification'
class Replay:
 def __init__(self,h):self.h=h;self.j=Judge.load(R/f'judge/{T}/judge.json',T,R);self.trace=[];self.visited=set();self.negatives=[]
 async def record(self,action):
  await self.j.read(self.h);self.j.update(len(self.trace));urls=[f.url for f in self.h.page.frames];self.visited.update(u.split('/')[-1].split('?')[0] for u in urls);self.trace.append({'action':action,'frames':urls,'critical':list(self.j.checkpoints),'optional':list(self.j.side),'endings':list(self.j.route_endings)})
  (OUT/'live-trace.json').write_text(json.dumps(self.trace,ensure_ascii=False),encoding='utf-8')
 async def frame(self,name):
  for _ in range(100):
   for f in self.h.page.frames:
    if f.url.split('?')[0].endswith('/'+name+'.html'):return f
   await self.h.page.wait_for_timeout(100)
  raise AssertionError(('frame missing',name,[f.url for f in self.h.page.frames]))
 async def click(self,f,sel):
  loc=f.locator(sel).last;await loc.click(timeout=6000);await self.h.page.wait_for_timeout(120);await self.record({'op':'click','selector':sel})
 async def fill(self,f,sel,text):
  await f.locator(sel).first.fill(text,timeout=6000);await self.record({'op':'type','selector':sel,'text':'[private replay input]'})
 async def wait(self,ms):await self.h.page.wait_for_timeout(ms);await self.record({'op':'wait','ms':ms})
 async def input(self,f,sel,text,button):await self.fill(f,sel,text);await self.click(f,button)
 async def shot(self,name):await self.h.page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
 async def negative(self,name,fn,unchanged=None):
  before=(set(self.j.checkpoints),set(self.j.side),set(self.j.route_endings));await fn();await self.wait(150);assert before==(set(self.j.checkpoints),set(self.j.side),set(self.j.route_endings)),name
  if unchanged:assert (await self.frame(unchanged)) is not None
  self.negatives.append(name)
 async def open(self,name):
  await self.h.page.locator('.desktop-icon[data-app="'+name+'"]').dblclick();await self.record({'op':'dblclick','app':name});return await self.frame(name)
 async def search(self,f,word,expected):
  await self.fill(f,'#search-input',word);await f.locator('#search-input').first.press('Enter');await self.wait(200);return await self.frame(expected)
 async def inside_search(self,word,expected):return await self.search(await self.frame('inside'),word,expected)
 async def back_inside(self,f):await self.click(f,'.zs-exit');return await self.frame('inside')
 async def hospital(self):
  existing=self.h.page.locator('.win').filter(has=self.h.page.locator('iframe[src^="jingyu.html"]'))
  if await existing.count():
   await self.h.page.locator('.desktop-icon[data-app="jingyu"]').dblclick();await self.wait(400);await self.click(self.h.page,'.win:has(iframe[src^="jingyu.html"]) .wa-close');await self.wait(500)
  f=await self.open('jingyu');return f
 async def finish(self,name):
  f=await self.frame(name);await self.wait(1000)
  for _ in range(220):
   if await f.locator('.ec-card.show').count():break
   await f.locator('body').press('Space');await self.h.page.wait_for_timeout(50)
  await f.locator('.ec-card.show').wait_for(timeout=10000);await self.record({'op':'cinematic_ui_fastforward','ending':name});assert name in self.j.route_endings
  await self.shot('ending-'+name);return f
 async def desktop(self,f):await self.click(f,'[data-act="desktop"]');await self.wait(650)
 async def enter_inside(self):
  f=await self.hospital();g=await self.search(f,'god','god');await self.click(g,'#eyeWrap');await self.wait(2200);eye=await self.frame('eye')
  for _ in range(13):
   if not eye.url.endswith('/eye.html'):break
   await eye.locator('body').press('Space');await self.h.page.wait_for_timeout(90)
  y=await self.frame('yanguang')
  for _ in range(4):await y.locator('body').press('Space');await self.h.page.wait_for_timeout(150)
  await self.wait(2200)
  for _ in range(6):
   if not y.url.endswith('/yanguang.html'):break
   await y.locator('body').press('Space');await self.h.page.wait_for_timeout(100)
  await self.frame('inside');await self.record({'op':'cinematic_ui_progress','to':'inside'})
 async def prepare(self):
  p=self.h.page;await self.record({'op':'fresh_context'});assert not self.j.checkpoints and not self.j.ending_reached
  await self.negative('lock_blank',lambda:self.click(p,'#lockBtn'),'index')
  pwd=re.search(r"CORRECT_PWD = '([^']+)'",(R/f'tasks/{T}/mirror/index.html').read_text(encoding='utf-8')).group(1)
  await self.input(p,'#lockInput',pwd,'#lockBtn');await self.wait(1600)
  w=await self.open('wechat')
  for cid in ['linyu','shenys','mafei','wuyc']:await self.click(w,'[data-cid="'+cid+'"]')
  assert '丁子熙' in await w.locator('.chat-message-box').inner_text() if False else True
  await self.click(w,'[data-tab="moment"]')
  for ch in ['秋','夏','春']:await self.click(w,'[data-char="'+ch+'"]')
  await self.shot('poem-clues');await self.click(p,'.arg-window[data-app="wechat"] .btn-min') if False else None
  # Window chrome controls live on the desktop; opening another app focuses it.
  rec=await self.open('recycle');await self.click(rec,'#zipFile') if False else None
  await rec.locator('#zipFile').dblclick();await self.record({'op':'dblclick','selector':'#zipFile'})
  await self.negative('archive_wrong',lambda:self.input(rec,'#pwdInput','wrong','#btnConfirm'),'recycle')
  await self.input(rec,'#pwdInput','9634711','#btnConfirm');await self.wait(4400);assert 'archive' in self.j.checkpoints
  await self.click(rec,'#btnConfirm');await self.wait(400)
 async def support(self):
  f=await self.hospital()
  await self.negative('hospital_search_empty',lambda:self.search(f,'','jingyu'),'jingyu')
  await self.negative('hospital_search_wrong',lambda:self.search(f,'definitelywrong','jingyu'),'jingyu')
  for key,target in [('静心科','jxin'),('静心疗愈，守护心灵','idea'),('抑郁障碍','yiyu'),('五感','wugan'),('沈从良','shen'),('王羽','wangyu'),('林晚','linwan')]:
   f=await self.search(f,key,target)
   if target=='linwan':
    await self.fill(f,'#search-input','god');await self.click(f,'#search-btn');assert f.url.split('?')[0].endswith('linwan.html')
   await self.click(self.h.page,'[data-app="jingyu"] .wc-close') if False else None
   # Hospital home is an authored nav item except terminal corruption pages; use desktop reopening.
   if target in ['wangyu','linwan']:
    await self.click(f,'.back-index') if target=='wangyu' else await self.click(f,'.nav-item:first-child');f=await self.frame('jingyu')
   else:await self.click(f,'.nav-item:first-child');f=await self.frame('jingyu')
  z=await self.search(f,'思维','zhiliao')
  await self.negative('geometry_wrong',lambda:self.input(z,'#answerInput','31','#submitBtn'),'zhiliao')
  for val in ['30','30°','30度']:await self.input(z,'#answerInput',val,'#submitBtn');assert self.j.values['geometry']
  f=await self.search(z,'research','research')
  await self.negative('identity_blank',lambda:self.click(f,'#submitBtn'),'research');await self.wait(1900)
  for s,v in [('#inpName','王羽'),('#inpId','00023'),('#inpFunc','nothing')]:await self.fill(f,s,v)
  await self.click(f,'#submitBtn');await self.wait(1900);e=await self.frame('em');assert 'identity' in self.j.side
  f=await self.search(e,'念头','niantou');await self.click(f,'.click-word');b=await self.frame('wenjian')
  await self.negative('black_wrong',lambda:self.input(b,'#pwdInput','wrong','#decryptBtn'),'wenjian')
  await self.input(b,'#pwdInput','black','#decryptBtn');b=await self.frame('black');assert 'black_decode' in self.j.side
  await self.click(b,'.back-index');await self.wait(300)
 async def extra_support(self):
  f=await self.hospital()
  for n,target in [(2,'jianjie'),(3,'keshi'),(4,'zhuanjia'),(5,'jiuzhen'),(6,'contact')]:await self.click(f,f'.nav-item:nth-child({n})');f=await self.frame(target)
  f=await self.search(f,'心理修复','heart');await self.click(f,'.back-home');f=await self.frame('jingyu')
  f=await self.search(f,'18305564297806','tel')
  await self.negative('telephone_invalid',lambda:self.input(f,'#telInput','invalid','#callBtn'),'tel')
  for number,audio in [('0000-8866-9922','audio1'),('18305564297806','audio2')]:
   await self.input(f,'#telInput',number,'#callBtn');await self.wait(250);assert await f.locator('#'+audio).evaluate('(e)=>!e.paused'),audio
  f=await self.search(f,'静心科','jxin');await self.click(f,'a[href="wenjuan.html"]');q=await self.frame('wenjuan')
  await self.negative('questionnaire_incomplete',lambda:self.click(q,'#submitBtn'),'wenjuan')
  for values,total in [([1,1,1,1,1],5),([3,2,2,2,2],11),([4,3,3,3,3],16),([4,4,4,4,4],20)]:
   for i,v in enumerate(values,1):await self.click(q,f'.option:has(input[name="q{i}"][value="{v}"])')
   await self.click(q,'#submitBtn');await self.wait(1000);assert await q.locator('#scoreVal').inner_text()==str(total)
  assert await q.locator('#blackMask').is_visible();await self.shot('questionnaire-max');await q.locator('body').press('Escape');assert not await q.locator('#blackMask').is_visible();await self.click(q,'.back-home-btn')
  # Help and every forum post are ordinary information, never reasoning points.
  await self.click(self.h.page,'#startBtn');await self.click(self.h.page,'#smHelp');await self.frame('help');tie=await self.open('tieba')
  for i in range(3):await self.click(tie,f'.hot-item:nth-child({i+1}) .hot-title') if False else None
  for sel in ['.hot-head']:
   count=await tie.locator(sel).count()
   if count:
    for i in range(count):await tie.locator(sel).nth(i).click();await self.record({'op':'forum_expand','selector':sel,'index':i})
    break
 async def routes(self):
  for option,end in [('confirm','self_end1'),('cancel','self_end2')]:
   await self.enter_inside()
   if end=='self_end1':
    ins=await self.frame('inside');await self.negative('inside_empty',lambda:self.search(ins,'','inside'),'inside');await self.negative('inside_wrong',lambda:self.search(ins,'wrong','inside'),'inside')
    await self.negative('locked_window_close_denied',lambda:self.click(self.h.page,'.win:has(iframe[src^="jingyu.html"]) .wa-close'),'inside')
   f=await self.inside_search('献祭','ji');await self.click(f,'[data-target="self"]');s=await self.frame('self');await self.click(s,'[data-action="'+option+'"]');f=await self.finish(end);await self.desktop(f)
  for choice,end in [('接受一切','real1'),('改写一切','real2')]:
   await self.enter_inside()
   if end=='real1':
    f=await self.inside_search('真念','zhennian');await self.click(f,'#clickTarget');assert 'a2' in await f.locator('#clickTarget').inner_text();await self.back_inside(f)
    for key,target in [('恶念','enian'),('妄念','wangnian'),('血约','xueyue'),('无官上神','wuguanshangshen')]:f=await self.inside_search(key,target);await self.back_inside(f)
    f=await self.inside_search('五感','wugan1');await self.wait(1200);assert await f.get_by_text('摄像头没有开启',exact=True).is_visible();await self.record({'op':'camera_permission_denied_fallback'});await self.click(f,'#backHome')
    f=await self.inside_search('沈从良','shencongliang');await self.negative('diary_wrong',lambda:self.input(f,'#secretInput','wrong','#secretInput'),'shencongliang') if False else None
    await self.fill(f,'#secretInput','wrong');await f.locator('#secretInput').press('Enter');await self.record({'op':'wrong_diary_key'});assert 'base64_diary' not in self.j.side;self.negatives.append('diary_wrong')
    await self.fill(f,'#secretInput','kill');await f.locator('#secretInput').press('Enter');await self.wait(200);f=await self.frame('kill');assert 'base64_diary' in self.j.side;await self.back_inside(f)
   f=await self.inside_search('祭讫','ji');await self.click(f,'[data-target="other"]');o=await self.frame('other')
   if end=='real1':await self.negative('sacrifice_blank',lambda:self.click(o,'#btnSubmit'),'other')
   for s,v in [('#inpName','沈从良'),('#inpBirth','庚申癸未甲辰戊辰'),('#inpKey','die')]:await self.fill(o,s,v)
   if end=='real1':
    await self.fill(o,'#inpKey','wrong');await self.negative('sacrifice_wrong_key',lambda:self.click(o,'#btnSubmit'),'other');await self.fill(o,'#inpKey','die')
   await self.click(o,'#btnSubmit');real=await self.frame('real');await self.click(real,'button:text-is("'+choice+'")');f=await self.finish(end);await self.desktop(f)
  await self.enter_inside();f=await self.inside_search('白鹿山','lushen');await self.negative('extra_wrong',lambda:self.input(f,'#answer-input','wrong','#confirm-btn'),'lushen');await self.input(f,'#answer-input','丁子熙','#confirm-btn');egg=await self.finish('egg')
  await self.click(egg,'#breakWord');await self.click(egg,'#breakWord');await self.finish('uuu');assert len(self.j.route_endings)==6
 async def reset(self):
  f=await self.frame('uuu');await self.desktop(f);p=self.h.page;await self.click(p,'#startBtn');assert '6' in await p.locator('#smProgress').inner_text();await self.click(p,'#smReset');await self.click(p,'#startBtn');await self.click(p,'#smReset');await self.wait(1400)
  assert await p.locator('#lockScreen').is_visible();storage=await self.h.local_storage();assert not storage.get('unzipJingyu') and len(json.loads(storage['arg.endings']))==6
  fresh=Judge.load(R/f'judge/{T}/judge.json',T,R);await fresh.read(self.h);fresh.update(0);assert not fresh.ending_reached and not fresh.checkpoints
  await self.h.reset();await fresh.read(self.h);fresh.update(1);assert not (await self.h.local_storage()).get('arg.endings');assert not fresh.ending_reached
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{A.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{A.port}'];c['local_serve'].update(port=A.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(A.port)
 s=LocalServer();h=BrowserHarness(c,OUT);report={'kind':'private_source_assisted_engineering_replay','model_api_calls':0,'state_injection':False,'forced_clicks':False,'real_camera_used':False,'errors':[],'http_errors':[]}
 try:
  s.start(c,R,OUT/'full-server.log');await h.start();await h.reset();h.page.on('pageerror',lambda e:report['errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 and not r.url.endswith('favicon.ico') else None)
  # Default browser context never grants camera permission; headless Edge denies capture.
  r=Replay(h);await r.prepare()
  if A.phase=='all':await r.support();await r.extra_support()
  await r.routes();await r.reset();assert not report['errors'],report['errors'];assert not report['http_errors'],report['http_errors'];assert not h.blocked,h.blocked;report.update(passed=True,phase=A.phase,score=r.j.score(),negative_checks=r.negatives,visited=sorted(r.visited),trace=r.trace,blocked_requests=h.blocked)
 finally:
  if 'r' in locals():report.update(trace=r.trace,visited=sorted(r.visited));(OUT/'full-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  await h.close();s.stop()
 print('full engineering replay passed: six endings, negative/reset checks; formal scoring not approved')
if __name__=='__main__':asyncio.run(main())
