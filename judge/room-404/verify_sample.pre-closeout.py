from pathlib import Path
import asyncio,argparse,json,sys
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R));T='room-404';OUT=R/f'judge/{T}/verification'
from harness.config import load_config
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from harness.serve_local import LocalServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8811);p.add_argument('--game-root');p.add_argument('--evidence-dir');a=p.parse_args()
if a.evidence_dir:OUT=Path(a.evidence_dir)
async def main():
 OUT.mkdir(parents=True,exist_ok=True);c=load_config(R/f'configs/{T}.json');c['entry_url']=f'http://127.0.0.1:{a.port}/index.html';c['allow_hosts']=[f'127.0.0.1:{a.port}'];c['local_serve'].update(port=a.port,ready_url=c['entry_url']);c['local_serve']['command'][-1]=str(a.port);c['settle_ms']=60
 if a.game_root:c['local_serve']['command'][3]=str(Path(a.game_root).resolve())
 h=BrowserHarness(c,OUT);server=LocalServer();j=None;steps=[];report={'page_errors':[],'http_errors':[],'pages':{},'endings':[],'negative':[]}
 async def rec(label):
  await j.read(h);j.update(len(steps)+1);steps.append({'action':label,'score':j.score()});h.consume_step()
 async def act(action,label=None):assert await h.act(action)=='ok',action;await rec(label or str(action))
 async def click(loc):
  if isinstance(loc,str):loc=h.page.locator(loc)
  loc=loc.first;await loc.wait_for(state='visible');await loc.scroll_into_view_if_needed();await loc.click(trial=True);b=await loc.bounding_box();assert b;await act({'op':'click','x':b['x']+b['width']/2,'y':b['y']+b['height']/2},'click '+str(loc))
 async def button(text):await click(h.page.get_by_role('button',name=text,exact=True))
 async def fill(loc,text):
  await click(loc);old=await loc.input_value();await act({'op':'key','key':'End'})
  for _ in old:await act({'op':'key','key':'Backspace'})
  await act({'op':'type','text':text})
 async def save():return await h.page.evaluate('JSON.parse(localStorage.getItem("room404-save")||"{}")')
 async def reset():
  nonlocal j
  await h.reset();j=Judge.load(R/c['judge_path'],T,R);h.page.on('pageerror',lambda e:report['page_errors'].append(str(e)));h.context.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 and not r.url.endswith('/favicon.ico') else None);await h.observe();await rec('fresh browser context');assert not j.checkpoints and not j.side and not j.ending_reached
  await click('input[type=checkbox]');await click(h.page.get_by_role('button',name='进入游戏'));await button('开始调查')
 async def explore():
  visited=set()
  for sweep in range(4):
   for i in range(10):
    loc=h.page.locator('aside button').nth(i)
    if not await loc.is_enabled():continue
    await click(loc)
    ids=await h.page.locator('.site-nav a').evaluate_all('(es)=>es.map(e=>e.dataset.pageId)')
    for pid in ids:
     if pid in visited:continue
     await click(f'.site-nav a[data-page-id="{pid}"]');visited.add(pid);texts=[]
     while True:
      texts.append(await h.page.locator('.page-content').first.inner_text())
      nxt=h.page.get_by_role('button',name='下一页',exact=True)
      if not await nxt.count() or not await nxt.is_enabled():break
      await click(nxt)
     report['pages'][pid]=texts
  report['exploration_state']=await save();assert len(report['exploration_state']['clues'])>=16
 async def site(index):await click(h.page.locator('aside button').nth([0,6,1,2,3,4,9,5,7,8][index]))
 async def openp(title,index):await site(index);await button(title)
 async def solve(pid,title,index,answer,redacted=False):
  await openp(title,index)
  if redacted:
   spans=h.page.locator('div[class*="z-[70]"] span.cursor-pointer');assert await spans.count()==5
   for i in range(5):await click(spans.nth(i))
  inp=h.page.locator('div[class*="z-[70]"] input');await fill(inp,'invalid404');await act({'op':'key','key':'Enter'});assert pid not in (await save())['solvedPuzzles'];report['negative'].append(pid)
  await fill(inp,answer);await act({'op':'key','key':'Enter'});await act({'op':'wait','ms':1700});assert pid in (await save())['solvedPuzzles']
 async def auxiliary():
  await button('邮件');report['emails']=[]
  for i in range(await h.page.locator('.email-item').count()):
   await click(h.page.locator('.email-item').nth(i));report['emails'].append(await h.page.locator('div[class*="z-[60]"]').inner_text());await click('div[class*="z-[60]"] button')
  await click('div.fixed.inset-0.z-50 button')
  await click(h.page.get_by_role('button',name='证据 (18/18)',exact=True));assert await h.page.locator('.evidence-card').count()==18;await click(h.page.get_by_role('button',name='住客名册 · 十二名实验对象'))
  cards=h.page.locator('.tenant-card');assert await cards.count()==12
  for i in range(12):await cards.nth(i).scroll_into_view_if_needed()
  assert await h.page.locator('.tenant-card img').count()==12;report['tenant_records']=12;await click('.tenant-close');await click('div.fixed.inset-0.z-50 button')
  report['browser_views']=[]
  for index in [2,3,4,5,1,6,9]:
   await site(index);await click('.browser-launch-btn');assert await h.page.locator('.browser-content').inner_text();await click('.fake-browser-overlay .nav-btn.reload');await click('.fake-browser-overlay .window-btn.close');report['browser_views'].append(index)
  await site(9);await click('.site-nav a[data-page-id="darkweb-main"]');before=await save();await click('.page-content .file-name');assert (await save())==before;report['authored_mock_file_list_noninteractive']=True
  await site(0);inp=h.page.get_by_placeholder('输入关键词搜索...');await fill(inp,'qzxvbnmklp');await act({'op':'key','key':'Enter'});assert not await h.page.locator('.search-result').count();await fill(inp,'404');await act({'op':'key','key':'Enter'});assert await h.page.locator('.search-result').count();await click('.search-result');report['search_positive_negative']=True
 async def choice(value,title='最后的选择'):
  await site(8);await button(title);await button(value);await act({'op':'wait','ms':1700})
 async def ending(expected):
  assert (await save())['ending']==expected;await rec('ending '+expected);assert expected in j.route_endings,j.score();report['endings'].append({'id':expected,'score':j.score(),'state':await save()});await h.observe('ending-'+expected+'.png');await button('返回调查')
 try:
  server.start(c,R,OUT/'server.log');report['owned_server']=server.owned;await h.start();await reset();await explore();await auxiliary();print('ROOM404 EXPLORED',len(report['pages']),flush=True)
  # Both optional outcome branches are locked before their actual requirements.
  await openp('最后的选择',8)
  for text in ['下到地下三层，拔掉电源','把十二个名字念出去']:
   loc=h.page.get_by_role('button',name=text);assert '🔒' in await loc.inner_text();await click(loc);assert not (await save())['ending'];report['negative'].append('locked '+text)
  await button('取消');await choice('报警，把证据交出去');await ending('normal');assert not j.checkpoints
  # The author permits the final choice directly, without the separate identity puzzle.
  report['identity_bypass_normal_verified']=True
  data=[('p1-usb','U盘密码恢复',0,'1998404',False),('p2-redacted','涂黑文件解密',5,'GNS-404',True),('p3-years','第 404 天',4,'404',False),('p4-frequency','音频频率解码',6,'87.9',False),('p5-employee','员工ID验证',7,'GNS-404',False),('p6-timeline','监控时间线',8,'1998-2003-2011-2024-2026',False),('p7-darkweb','暗网访问码',9,'1G48',False),('p8-server','服务器密码',9,'TIDE',False),('p10-hidden','身份验证',8,'ROOM404',False)]
  for pid,title,index,answer,redacted in data:
   await solve(pid,title,index,answer,redacted);print('ROOM404 SOLVED',pid,flush=True)
   # Identity success immediately opens final choice.
   if pid=='p10-hidden':await button('取消')
  for expected,text in [('hidden','接入系统，下去找哥哥'),('secret','下到地下三层，拔掉电源'),('true','把十二个名字念出去')]:
   j=Judge.load(R/c['judge_path'],T,R)
   await site(8);await click('[data-puzzle="p10-hidden"]');await button(text);await act({'op':'wait','ms':1700});await ending(expected)
  before=await save();await button('退出');await h.page.reload();await h.observe();j=Judge.load(R/c['judge_path'],T,R);await rec('reload retains save but hides stale ending');assert not j.ending_reached;await button('重新开始');assert h.pending;await act({'op':'dialog','accept':False});assert (await save())['solvedPuzzles']==before['solvedPuzzles'];await button('重新开始');await act({'op':'dialog','accept':True});after=await save();assert not after.get('clues') and not after.get('solvedPuzzles') and not after.get('ending') and after.get('act',0)==0;report['authored_reset_verified']=True;report['post_author_reset_state']=after
  for expected,text in [('hidden','接入系统，下去找哥哥'),('secret','下到地下三层，拔掉电源')]:
   await reset();await explore()
   if expected=='secret':
    await solve('p7-darkweb','暗网访问码',9,'1G48');await solve('p8-server','服务器密码',9,'TIDE')
   await choice(text);await ending(expected);report.setdefault('minimal_routes',[]).append({'route':expected,'solvedPuzzles':(await save())['solvedPuzzles']})
  await reset();report['fresh_context_reset_verified']=True;report['blocked_requests']=h.blocked;assert not report['page_errors'] and not report['http_errors'] and not h.blocked;report['pass']=True
 except Exception as e:
  report['failure']=repr(e)
  if h.page and not h.pending:await h.page.screenshot(path=str(OUT/'failure.png'));report['failure_text']=(await h.page.locator('body').inner_text())[:10000]
  raise
 finally:
  report['steps']=steps;(OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');await h.close();server.stop()
 print('ROOM404 FULL UI PASS',flush=True)
if __name__=='__main__':asyncio.run(main())
