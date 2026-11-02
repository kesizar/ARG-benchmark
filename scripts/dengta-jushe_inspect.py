from pathlib import Path
import json,threading,functools,http.server
from playwright.sync_api import sync_playwright
R=Path('.');O=R/'runs/dengta-jushe'
class Q(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',8811),functools.partial(Q,directory=str(R/'tasks/dengta-jushe/mirror')));threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as w:
 b=w.chromium.launch(channel='msedge');c=b.new_context();p=c.new_page();p.goto('http://127.0.0.1:8811/index.html');p.get_by_text('自力模式（挑战）',exact=False).click();print(p.get_by_role('button').all_text_contents());p.get_by_role('button',name='后台实习园地',exact=False).click();print(p.locator('body').inner_text()[-2200:]);b.close()
srv.shutdown()
