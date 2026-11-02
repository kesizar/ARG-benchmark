import asyncio,argparse,json,threading,http.server,functools,re
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[2];T='fengnian-gaiban';P=R/'tasks'/T;J=R/'judge'/T/'verification'
arg=argparse.ArgumentParser();arg.add_argument('--port',type=int,default=8822);A=arg.parse_args()
class Handler(http.server.SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path.split('?')[0]=='/__archived_entry__.html':
   b=(P/'entry.snapshot.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else:super().do_GET()
 def log_message(self,*args):pass
async def main():
 J.mkdir(parents=True,exist_ok=True);srv=http.server.ThreadingHTTPServer(('127.0.0.1',A.port),functools.partial(Handler,directory=str(P/'upstream')));threading.Thread(target=srv.serve_forever,daemon=True).start()
 report={'scope':'entry_only_not_full_flow','state_injection':False,'source_credential_only_private_diagnostic':True,'cases':[],'page_errors':[],'http_errors':[]}
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True,channel='msedge')
   report['browser_version']=browser.version
   for version,path in [('current','index.html'),('archived','__archived_entry__.html')]:
    ctx=await browser.new_context(viewport={'width':1366,'height':900},locale='zh-CN',timezone_id='Asia/Shanghai');page=await ctx.new_page()
    page.on('pageerror',lambda e:report['page_errors'].append(str(e)));page.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 and not r.url.endswith('favicon.ico') else None)
    await page.goto(f'http://127.0.0.1:{A.port}/{path}');await page.wait_for_timeout(900)
    lock=page.locator('#lockScreen');assert await lock.is_visible()
    visible=await lock.inner_text();await page.screenshot(path=str(J/f'{version}-initial.png'))
    checks=[]
    for value in ['','wrong','12345678']:
     await page.locator('#lockInput').fill(value);await page.locator('#lockBtn').click();await page.wait_for_timeout(150)
     tip=await page.locator('#lockTip').inner_text();assert '密码错误' in tip and await lock.is_visible();checks.append({'input':'blank' if not value else 'wrong','feedback':tip,'still_locked':True})
    assert '8 位生日数字' in checks[-1]['feedback']
    try:await page.locator('#startBtn').click(trial=True,timeout=700);intercepted=False
    except Exception:intercepted=True
    assert intercepted,'Start unexpectedly accessible before unlock'
    await page.screenshot(path=str(J/f'{version}-wrong.png'))
    source=(P/'upstream/index.html' if version=='current' else P/'entry.snapshot.html').read_text(encoding='utf-8');credential=re.search(r"CORRECT_PWD = '([^']+)'",source).group(1)
    await page.locator('#lockInput').fill(credential);await page.locator('#lockBtn').click();await page.wait_for_timeout(1600)
    assert not await lock.is_visible();assert await page.locator('#startBtn').is_visible();await page.screenshot(path=str(J/f'{version}-private-diagnostic-unlock.png'))
    await page.reload();await page.wait_for_timeout(350);assert not await lock.is_visible()
    await ctx.close();fresh=await browser.new_context();fp=await fresh.new_page();await fp.goto(f'http://127.0.0.1:{A.port}/{path}');assert await fp.locator('#lockScreen').is_visible();await fresh.close()
    report['cases'].append({'version':version,'visible_initial_lock_text':visible,'negative_checks':checks,'start_intercepted_by_lock':intercepted,'source_credential_unlock_diagnostic_only':True,'same_context_reload_remains_unlocked':True,'fresh_context_resets_to_lock':True,'downstream_flow_verified':False})
   await browser.close()
  assert report['page_errors']==["Cannot access 'lastUnzip' before initialization"]*2,report['page_errors']
  assert not report['http_errors'],report['http_errors']
  report['entry_diagnostic_passed']=True
  report['runtime_clean']=False
  report['runtime_blocker']='Both versions throw lastUnzip TDZ error on same-context unlocked reload. Startup calls budgetTick before let lastUnzip initializes, preventing remaining startup listener registration.'
 finally:srv.shutdown();(J/'entry-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('entry diagnostic passed; no full-flow readiness')
asyncio.run(main())
