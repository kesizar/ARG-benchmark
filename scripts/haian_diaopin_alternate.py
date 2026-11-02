import json,threading,functools
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',8811),functools.partial(Quiet,directory='tasks/haian-diaopin/mirror'));threading.Thread(target=server.serve_forever,daemon=True).start()
r={'checks':[]}
def check(k,v):r['checks'].append({'id':k,'pass':bool(v)});assert v,k
def nav(p,s):p.locator('.nav-link').filter(has_text=s).first.click();p.wait_for_timeout(100)
def state(p):return p.evaluate("JSON.parse(localStorage.getItem('coastfm893_save_v1'))")
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True);p=b.new_page(viewport={'width':1366,'height':900});p.set_default_timeout(5000);p.goto('http://127.0.0.1:8811/index.html');p.get_by_text('不添加提示',exact=False).click()
  nav(p,'点歌单');p.locator('input').first.fill('双声道');p.wait_for_timeout(200);check('search finds removed song',p.get_by_text('已下架',exact=False).count()>0);p.get_by_role('button',name='📌 钉到导播笔记').first.click();check('sixth clue pinned','shuangshengdao' in state(p)['pinned'])
  p.locator('input').first.fill('');p.get_by_role('button',name='📌 钉到导播笔记').nth(0).click();p.get_by_role('button',name='📌 钉到导播笔记').first.click()
  nav(p,'录音室');p.get_by_role('button',name='📌 钉到导播笔记').click()
  nav(p,'DJ 专栏');p.get_by_role('button',name='📌 钉到导播笔记').click()
  check('five without ids',set(state(p)['pinned'])=={'gap','guihang','shuangshengdao','moved','zhou'})
  nav(p,'实习 DJ 园地');p.locator('input').last.fill('19940240');p.get_by_role('button',name='登录',exact=True).click();check('five without ids restore enabled',p.get_by_role('button',name='🔓 恢复第 7 段存档').is_enabled());p.get_by_role('button',name='🔓 恢复第 7 段存档').click();p.wait_for_timeout(900);check('alternate reaches ending',state(p)['endingSeen'])
  nav(p,'听众留言簿');check('hidden posts revealed',p.get_by_text('#1189',exact=False).count()>0)
  nav(p,'实习 DJ 园地');p.get_by_role('button',name='📌 钉到导播笔记').click();check('six after intern pin','ids' in state(p)['pinned'] and len(state(p)['pinned'])==6)
  b.close()
except Exception as e:r['error']=str(e)
finally:server.shutdown();server.server_close();Path('judge/haian-diaopin/evidence/alternate.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(r,ensure_ascii=False))
if 'error' in r:raise SystemExit(1)
