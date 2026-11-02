from pathlib import Path
import json,threading,http.server,functools,os
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'runs/guangying-she';M=R/'tasks/guangying-she/mirror'
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context();p=c.new_page();p.goto('http://127.0.0.1:8812');p.get_by_role('button',name='全自助观展').click()
 rows=[]
 for name in ['社团简介','公告栏','影展列表','相册浏览','文件名索引','暗房园地','影友留言簿','迁移说明','展览墙排序']:
  p.get_by_role('button',name=name,exact=True).first.click();p.wait_for_timeout(80)
  rows.append({'page':name,'text':p.locator('body').inner_text(),'controls':p.locator('button,input,textarea').evaluate_all('(els)=>els.map(e=>({tag:e.tagName,text:e.innerText,placeholder:e.placeholder,title:e.title,type:e.type}))')})
 (O/'ui-pages.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');p.screenshot(path=str(O/'local-wall.png'),full_page=True)
 print(json.dumps([{'page':r['page'],'controls':r['controls']} for r in rows],ensure_ascii=True),flush=True);os._exit(0)
