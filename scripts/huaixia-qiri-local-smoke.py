import http.server,threading,json
from playwright.sync_api import sync_playwright
class H(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory='tasks/huaixia-qiri',**kw)
import subprocess,sys,time
s=subprocess.Popen([sys.executable,'-m','http.server','8821','--bind','127.0.0.1','--directory','tasks/huaixia-qiri'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True,args=['--no-proxy-server']);page=b.new_page(); errors=[]; req=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8821/') else (req.append(r.request.url),r.abort()))
 page.goto('http://127.0.0.1:8821/original.html');page.wait_for_timeout(1500)
 title=page.locator('body').inner_text();buttons=page.get_by_role('button').all_text_contents()
 page.get_by_role('button').nth(0).click();page.wait_for_timeout(1500)
 opened=page.locator('body').inner_text(); buttons2=page.get_by_role('button').all_text_contents()
 open('runs/huaixia-qiri/local-smoke.json','w',encoding='utf-8').write(json.dumps({'title':title,'buttons':buttons,'after_first_button':opened,'after_buttons':buttons2,'errors':errors,'blocked_requests':req},ensure_ascii=False,indent=2)); b.close()
s.terminate()
