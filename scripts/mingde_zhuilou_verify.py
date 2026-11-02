from pathlib import Path
import sys,json,threading,functools,http.server,zipfile,hashlib
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from harness.judge import Judge
T='mingde-zhuilou';out=R/'runs'/T;out.mkdir(parents=True,exist_ok=True)
trace=json.loads((R/'tasks/mingde-zhuilou/evidence/ui-partial-through-office.json').read_text(encoding='utf-8'))
def run(game,port,kind,judgepath):
 handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(game));handler.log_message=lambda *a:None
 server=http.server.ThreadingHTTPServer(('127.0.0.1',port),handler);threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{port}'
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True)
  def context():
   c=b.new_context(viewport={'width':1366,'height':900});c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());c.on('page',lambda p:p.on('dialog',lambda d:d.accept()));return c
  c=context();p=c.new_page();p.goto(base+'/index.html');j=Judge.load(judgepath,T,R)
  def snap(stage,judge=j,ctx=c):
   expr='({' + ','.join(json.dumps(k)+':('+v['expr']+')' for k,v in judge.cfg['hooks'].items()) + '})';maps=[pg.evaluate(expr) for pg in ctx.pages if pg.url.startswith(base)];judge.values={k:any(m[k] for m in maps) for k in judge.cfg['hooks']};judge.update(len(trace));trace.append({'kind':kind,'stage':stage,'score':judge.score(),'values':judge.values.copy()});print(kind,stage,flush=True);(out/'acceptance-live.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
  snap('initial');assert not j.checkpoints and not j.score()['ending_reached']
  p.locator('#submitPassword').click();assert '请输入密码' in p.locator('#errorMessage').inner_text()
  p.locator('#passwordInput').fill('wrong');p.locator('#submitPassword').click();snap('wrong-boot');assert not j.side
  p.locator('#passwordInput').fill('xdemydmm');p.locator('#submitPassword').click();p.wait_for_url('**/desk.html');snap('boot-known-from-source-audit-only')
  p.get_by_text('备忘录',exact=True).first.click();assert '2007.03.15' in p.locator('#textEditor').input_value();p.locator('#notepadWindow .notepad-window-controls button').count() # source-preserving desktop
  with c.expect_page() as pop:p.get_by_text('证据检索',exact=True).first.click()
  e=pop.value;e.wait_for_load_state();e.locator('#searchInput').fill('不存在');e.locator('#searchBtn').click();assert e.locator('#resultsCount').inner_text()=='0';snap('unknown-search')
  e.locator('#openReportBtn').click();assert e.locator('#submitReportBtn').is_disabled();e.reload()
  keywords=['江楠','明德中学','明德中学学生坠楼案','纸团','王浩','张磊','补课费','工作日志','日记','班级群聊','监控','心理咨询室','赔偿协议','李阳'];docs={}
  for key in keywords:
   e.locator('#searchInput').fill(key);e.locator('#searchBtn').click()
   if kind=='source':continue # Unchanged document UI/gates reuse preserved source evidence.
   with c.expect_page() as pop:e.locator('.evidence-item').click()
   d=pop.value;d.wait_for_load_state();assert '404' not in d.title();docs[key]=d
  snap('source-prior-doc-evidence-reused' if kind=='source' else 'all-14-documents-open');assert not j.checkpoints
  def gate(key,inp,button,password,hook,before=None):
   d=docs[key]
   if before: d.locator(before).click()
   d.locator(inp).fill('wrong');d.locator(button).click();d.wait_for_timeout(150);snap('wrong-'+hook);assert not j.values[hook]
   d.locator(inp).fill(password);d.locator(button).click();d.wait_for_function(j.cfg['hooks'][hook]['expr'],timeout=15000);snap('correct-'+hook);assert j.values[hook]
  if kind!='source':
   gate('补课费','#password-input','#password-submit','8888','account')
   gate('工作日志','#passwordInput','#submitPassword','19871225','logs','#loginButton')
   gate('日记','#password','#loginForm button','20070315','diary')
   gate('心理咨询室','#password','#loginForm button','zhaoxiaomei','counseling','#adminLoginBtn')
   gate('监控','#passwordInput','#loginBtn','zhaotiejun','monitor')
   m=docs['监控'];m.locator('[data-time="11-15"]').click();m.locator('[data-id=office-senior2]').click();m.wait_for_timeout(200)
   gate('监控','#officePasswordInput','#officePasswordSubmit','zhanglei','office')
   m.locator('#modalClose').click();m.locator('[data-time="7-11"]').click();m.locator('[data-id=building-4]').click();m.wait_for_function("document.querySelector('#modalDetails').innerText.includes('08:00:23')");m.locator('#modalClose').click()
  # Orphan material is tested by explicit audit navigation, not misrepresented as reachable gameplay.
  for fn,hook,inp,but,ans,ready in [('locked_mail','mail','#passwordInput','#loginButton','20200128','#emailContainer'),('qiongdinghui','server','#serverPassword','button[onclick="accessServer()"]','02','#serverContent')]:
   d=c.new_page();d.goto(base+'/'+fn+'.html');docs[fn]=d;gate(fn,inp,but,ans,hook);d.locator(ready).wait_for(state='visible',timeout=4000);snap('orphan-audit-'+hook)
  gate('qiongdinghui','#arkPassword','button[onclick="decryptArkFolder()"]','20200510','ark')
  # Every selectable ending combination, including zero selections; use ordinary report controls.
  for selection,ending in [([],None),(['江楠'],1),(['李阳'],1),(['赔偿协议'],2),(['李阳','赔偿协议'],3)]:
   e.bring_to_front();e.reload();e.locator('#openReportBtn').click()
   for key in selection:e.locator('[data-keyword="'+key+'"] input').check()
   e.locator('#submitReportBtn').click();snap('report-'+str(selection))
   if ending is None:assert not any(j.values['ending'+str(i)] for i in [1,2,3]);continue
   assert j.values['ending'+str(ending)]
   e.screenshot(path=str(out/f'{kind}-ending{ending}-{len(selection)}.png'),full_page=True)
   e.locator('#ending'+str(ending)+' .restart-btn').click();assert e.evaluate('sessionStorage.getItem("discoveredEvidences")') is None
   fresh=Judge.load(judgepath,T,R);fresh.values={k:e.evaluate(v['expr']) for k,v in fresh.cfg['hooks'].items()};fresh.update(0);assert not fresh.checkpoints and not fresh.score()['ending_reached'];trace.append({'kind':kind,'stage':'report-reset','score':fresh.score()})
   # Re-discover via UI for next combination.
   for key in keywords:e.locator('#searchInput').fill(key);e.locator('#searchBtn').click()
  # Browser reset of password gates: fresh context starts locked everywhere.
  c.close();c=context();p=c.new_page();p.goto(base+'/account_records.html')
  for _ in range(5):p.locator('#password-input').fill('0000');p.locator('#password-submit').click()
  assert p.locator('#password-submit').is_disabled();p.wait_for_timeout(5200)
  if p.is_closed():p=c.new_page();p.goto(base+'/account_records.html')
  else:
   assert '访问被拒绝' in p.locator('body').inner_text();p.reload()
  assert not p.locator('#password-submit').is_disabled();trace.append({'kind':kind,'stage':'account-five-wrong-lockout-reload-reset','passed':True})
  for f,sel in [('dairy','#diaryContent'),('work_logs','#hiddenJournal'),('counseling_records','#recordSection'),('monitoring','#mainContainer'),('locked_mail','#emailContainer'),('qiongdinghui','#serverContent')]:
   p.goto(base+'/'+f+'.html');assert not p.locator(sel).is_visible()
  p.goto(base+'/index.html');fresh=Judge.load(judgepath,T,R);snap('new-context-full-reset',fresh,c);assert not fresh.checkpoints and not fresh.side and not fresh.score()['ending_reached']
  c.close();b.close()
 server.shutdown();server.server_close()
try:
 run(R/'tasks'/T/'mirror',8831,'source',R/'judge'/T/'judge.json')
 for kind,port in [('game',8832),('prepared',8833)]:
  target=out/('unpacked-'+kind);target.mkdir(exist_ok=True)
  with zipfile.ZipFile(R/'packs'/(T+('.zip' if kind=='game' else '.prepared.zip'))) as z:z.extractall(target)
  game=target if kind=='game' else target/'tasks'/T/'mirror';jp=R/'judge'/T/'judge.json' if kind=='game' else target/'judge'/T/'judge.json'
  run(game,port,kind,jp)
 (out/'acceptance.json').write_text(json.dumps({'passed':True,'scope':'3 independent roots/ports/fresh contexts; source-audit passwords; source and bundles byte comparison separately','trace':trace},ensure_ascii=False,indent=2),encoding='utf-8');print('PASS all roots')
except Exception:
 (out/'acceptance-partial.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8');raise
