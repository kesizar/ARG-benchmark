import json,threading,functools,hashlib
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
cases=[('resources',8812,'runs/haian-diaopin-deploy-resources'),('prepared',8813,'runs/haian-diaopin-deploy-prepared/tasks/haian-diaopin/mirror')]; results=[]
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True)
  for kind,port,folder in cases:
   srv=ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=folder));threading.Thread(target=srv.serve_forever,daemon=True).start()
   try:
    context=b.new_context(viewport={'width':1366,'height':900});p=context.new_page();p.set_default_timeout(5000);response=p.goto(f'http://127.0.0.1:{port}/index.html');p.get_by_text('不添加提示',exact=False).click();p.locator('.nav-link').filter(has_text='实习 DJ 园地').click();p.locator('input').last.fill('11111111');p.get_by_role('button',name='登录',exact=True).click();p.wait_for_timeout(150)
    s=lambda:p.evaluate("JSON.parse(localStorage.getItem('coastfm893_save_v1'))")
    assert not s()['internUnlocked'];p.locator('input').last.fill('19940240');p.get_by_role('button',name='登录',exact=True).click();p.wait_for_timeout(150);assert s()['internUnlocked'];assert p.get_by_role('button',name='🔓 恢复第 7 段存档').is_disabled();p.reload();assert s()['internUnlocked'];p.screenshot(path=f'judge/haian-diaopin/evidence/deploy-{kind}.png')
    results.append({'package':kind,'port':port,'http_status':response.status,'wrong_password':True,'correct_password':True,'threshold_locked':True,'reload_persists':True,'context':'fresh'})
    context.close()
   finally:srv.shutdown();srv.server_close()
  b.close()
except Exception as e:results.append({'error':str(e)})
Path('judge/haian-diaopin/evidence/deployment-ui.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(results,ensure_ascii=False))
if any('error' in x for x in results):raise SystemExit(1)
