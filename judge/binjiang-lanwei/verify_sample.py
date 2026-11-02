import asyncio,argparse,json,threading,http.server,functools,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from harness.judge import Judge
from playwright.async_api import async_playwright
T='binjiang-lanwei';J=R/'judge'/T
ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8832);ap.add_argument('--game-root');ap.add_argument('--output',default='acceptance.json');a=ap.parse_args()
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class Reader:
 pending=False
 def __init__(self,p):self.p=p
 async def page_expr(self,e):return await self.p.evaluate(e)
async def main():
 out=J/'verification';out.mkdir(exist_ok=True);root=Path(a.game_root) if a.game_root else R/'tasks'/T/'mirror'
 srv=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),functools.partial(Handler,directory=str(root)));threading.Thread(target=srv.serve_forever,daemon=True).start()
 report={'source_assisted':True,'model_solving_claim':False,'state_injection':False,'actions':0,'negatives':[],'gates':[],'visited':[],'page_errors':[],'http_errors':[],'blocked_requests':[],'dialogs':[],'endings':[]};base=f'http://127.0.0.1:{a.port}/'
 async def click(p,s):report['actions']+=1;await p.locator(s).click();await p.wait_for_timeout(120)
 async def fill(p,s,v):report['actions']+=1;await p.locator(s).fill(v)
 async def attach(p):
  p.set_default_timeout(7000);p.on('pageerror',lambda e:report['page_errors'].append({'url':p.url,'message':str(e),'stack':e.stack}));p.on('response',lambda r:report['http_errors'].append([r.url,r.status]) if r.status>=400 and not r.url.endswith('favicon.ico') else None)
  async def dialog(d):report['dialogs'].append(d.message);await d.accept()
  p.on('dialog',dialog)
 async def judge(p):
  q=Judge.load(J/'judge.json',T,R);await q.read(Reader(p));q.update(report['actions']);return q
 async def negative(p,name):
  q=await judge(p);assert not q.side and not q.route_endings,(name,q.side,q.route_endings);report['negatives'].append(name)
 async def search(p,key):await fill(p,'#searchInput',key);await p.locator('#searchInput').press('Enter');report['actions']+=1;await p.wait_for_timeout(160)
 async def login(ctx):
  p=await ctx.new_page();await attach(p);await p.goto(base+'index.html');await negative(p,'fresh_entry_no_score');report['entry_visible_text']=await p.locator('body').inner_text();await p.screenshot(path=str(out/f'{a.port}-entry.png'))
  for val in ['','123','000000']:
   await fill(p,'#passwordInput',val);await click(p,'#submitPassword');assert p.url.endswith('index.html');assert await p.locator('#passwordInput').input_value()=='';await negative(p,'entry_invalid_'+str(len(val)))
  await fill(p,'#passwordInput','051383');await click(p,'#submitPassword');await p.wait_for_url('**/desk.html');report['visited'].append('desk.html')
  async with ctx.expect_page() as popup:await click(p,".desktop-icon[onclick=\"openApp('wechat')\"]")
  w=await popup.value;await attach(w);await w.wait_for_load_state();report['visited'].append('wechat.html')
  # Each contact and application navigation stays on normal UI.
  for sel in ['.contact-item','.chat-item']:
   for i in range(await w.locator(sel).count()):
    if await w.locator(sel).nth(i).is_visible():await w.locator(sel).nth(i).click();report['actions']+=1
  report['wechat_contacts']=await w.locator('.chat-item').count();await w.close()
  await click(p,'[onclick="openNotepad()"].desktop-icon');await fill(p,'#textEditor','工程验收笔记');await click(p,'button[onclick="saveFile()"]');await click(p,'[onclick="toggleMaximizeNotepad()"]');await click(p,'[onclick="minimizeNotepad()"]');await p.wait_for_timeout(350);await click(p,'[onclick="openNotepad()"].desktop-icon');assert await p.locator('#textEditor').input_value()=='工程验收笔记';report['notepad_minimize_restore_bug']=True;await p.reload()
  async with ctx.expect_page() as popup:await click(p,".desktop-icon[onclick=\"openApp('evidence')\"]")
  e=await popup.value;await attach(e);await e.wait_for_load_state();await negative(e,'search_initial_no_score');return p,e
 async def gate(p,hook,inp,button,correct,success):
  assert not await p.locator(success).is_visible();await fill(p,inp,'00' if hook=='server' else '00000000');await click(p,button);assert not await p.locator(success).is_visible()
  q=await judge(p);assert hook not in q.side;report['negatives'].append(hook+'_wrong')
  await fill(p,inp,correct);await click(p,button);await p.locator(success).wait_for(state='visible');await p.wait_for_timeout(600);q=await judge(p);assert hook in q.side,(hook,q.side);assert not q.checkpoints;report['gates'].append(hook)
  await p.screenshot(path=str(out/f'{a.port}-{hook}.png'))
 try:
  async with async_playwright() as pw:
   b=await pw.chromium.launch(headless=True,channel='msedge');report['browser_version']=b.version
   ctx=await b.new_context(viewport={'width':1366,'height':900},locale='zh-CN',timezone_id='Asia/Shanghai')
   async def route(r):
    if r.request.url.startswith(base) or r.request.url.startswith('data:'):await r.continue_()
    else:report['blocked_requests'].append(r.request.url);await r.abort()
   await ctx.route('**/*',route);desk,e=await login(ctx)
   await search(e,'不存在的关键词');assert '未找到' in await e.locator('#evidenceList').inner_text();await negative(e,'unknown_keyword')
   keywords=['滨江新城烂尾楼案','定制袖扣','损坏的手机','十字星形压痕','江川','监控','秘密邮箱','牧羊人','穹顶会','渡鸦','沈梦','青州城投','星耀集团','林纾失踪案']
   for key in keywords:
    await search(e,key);await negative(e,'search_alone_'+key)
    async with ctx.expect_page() as pop:await click(e,'.evidence-item')
    p=await pop.value;await attach(p);await p.wait_for_load_state();name=p.url.rsplit('/',1)[-1];report['visited'].append(name);await negative(p,'open_alone_'+name)
    if key=='监控':
     for s in ['#public-camera','#graffiti-point','#private-camera']:await click(p,s)
     await gate(p,'camera','#cameraPassword','#decryptCameraButton','1041401','#evidenceVideoContainer');await click(p,'#playVideoButton');await p.wait_for_timeout(5200);assert not await p.locator('#playVideoButton').is_disabled()
    elif key=='秘密邮箱':
     await gate(p,'mail','#passwordInput','#loginButton','20200128','#emailContainer')
     count=await p.locator('#emailList .email-item').count();report['emails_read']=count
     for i in range(count):await p.locator('#emailList .email-item').nth(i).click();report['actions']+=1;await p.locator('#emailDetail').wait_for(state='visible');await click(p,'#backToList')
    elif key=='牧羊人':await gate(p,'shepherd','#passwordInput','#loginButton','RAVEN','#contentContainer')
    elif key=='穹顶会':
     await gate(p,'server','#serverPassword','[onclick="accessServer()"]','02','#serverContent');await gate(p,'ark','#arkPassword','[onclick="decryptArkFolder()"]','20200510','#arkContent')
    elif key=='沈梦':await gate(p,'daughter','#encryptionPassword','[onclick="decryptFiles()"]','20210913','#recoveredFiles')
    elif key=='星耀集团':
     for tab in ['business','culture','join','about','news']:await click(p,f'.nav-item[onclick="showPage(\'{tab}\')"]')
     await gate(p,'forum','#forumPassword','[onclick="accessForum()"]','0630','#forumContent')
    elif key=='林纾失踪案':await gate(p,'old_case','#passwordInput','#decryptButton','311542812128263','#decryptionResult')
    elif key=='渡鸦':
     await p.wait_for_timeout(1100)
     for i in range(8):await click(p,'[onclick="loadMoreChat()"]')
     await click(p,'[onclick="analyzePattern()"]');report['raven_messages_loaded']=await p.locator('#chatLog .chat-message').count()
    elif key=='青州城投':
     await fill(p,'#contactSearch','不存在');await p.locator('#contactSearch').press('x');await fill(p,'#contactSearch','');await p.locator('#contactSearch').press('Backspace');await click(p,'[onclick="downloadMemo()"]');report['mock_pdf_alert_only']=True
    if key in ['监控','秘密邮箱','牧羊人','穹顶会','沈梦','星耀集团','林纾失踪案']:
     await p.reload();await p.wait_for_timeout(150);await negative(p,'reload_clears_document_gate_'+key)
    await p.screenshot(path=str(out/f'{a.port}-{name}.png'));await p.close()
   # Full collection route, then three authored endings using report UI; retry intentionally preserves collection.
   for end,suspect,key in [(1,'赵翔宇','监控'),(2,'赵翔宇','定制袖扣'),(3,'沈梦','监控')]:
    await click(e,'#openReportBtn')
    if end==1:
     await click(e,'#submitReportBtn');assert await e.locator('#suspectError').is_visible();await negative(e,'blank_suspect')
     await fill(e,'#suspectInput','岳月');await click(e,'#submitReportBtn');assert await e.locator('#suspectError').is_visible();await negative(e,'blocked_suspect')
     await fill(e,'#suspectInput','赵翔宇');await click(e,'#submitReportBtn');await negative(e,'no_evidence_selected')
    await fill(e,'#suspectInput',suspect);await click(e,f'.evidence-select-item[data-keyword="{key}"] input');await click(e,'#submitReportBtn');await e.locator(f'#ending{end}').wait_for(state='visible');q=await judge(e);assert list(q.route_endings)==[f'ending{end}'];assert not q.side;report['endings'].append(end)
    await e.screenshot(path=str(out/f'{a.port}-ending{end}.png'));await click(e,f'#ending{end} .restart-btn');q=await judge(e);assert not q.route_endings;assert '14' in await e.locator('#openReportBtn').inner_text();report['negatives'].append(f'ending{end}_retry_clears_ending_preserves_collection')
   await ctx.close()
   # A fresh run can reach good ending without opening/decrypting footage: demonstrate bypass, do not call gate critical.
   ctx=await b.new_context(viewport={'width':1366,'height':900});await ctx.route('**/*',route);d,e=await login(ctx);assert await e.locator('#openReportBtn').inner_text()=='提交案件报告';await search(e,'监控');await click(e,'#openReportBtn');await fill(e,'#suspectInput','赵翔宇');await click(e,'.evidence-select-item input');await click(e,'#submitReportBtn');q=await judge(e);assert list(q.route_endings)==['ending1'] and not q.side;report['camera_gate_bypass_demonstrated']=True;await ctx.close();await b.close()
   assert len(set(report['visited']))==16,report['visited'];assert sorted(report['gates'])==sorted(['camera','old_case','mail','shepherd','server','ark','daughter','forum']);report['runtime_clean']=not report['page_errors'];assert not report['http_errors'],report['http_errors'];assert not report['blocked_requests'],report['blocked_requests'];report['passed']=True
 finally:
  srv.shutdown();(out/a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'passed':report.get('passed'), 'actions':report['actions'],'gates':report['gates'],'endings':report['endings'],'visited':len(set(report['visited']))}))
asyncio.run(main())
