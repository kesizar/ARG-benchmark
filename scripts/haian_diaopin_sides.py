import json,threading,functools
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
srv=ThreadingHTTPServer(('127.0.0.1',8811),functools.partial(Quiet,directory='tasks/haian-diaopin/mirror'));threading.Thread(target=srv.serve_forever,daemon=True).start();r=[]
def ck(id,v):r.append({'id':id,'pass':bool(v)});assert v,id
def nav(p,s):p.locator('.nav-link').filter(has_text=s).first.click();p.wait_for_timeout(100)
def state(p):return p.evaluate("JSON.parse(localStorage.getItem('coastfm893_save_v1'))")
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True);p=b.new_page(viewport={'width':1366,'height':900});p.set_default_timeout(5000);p.goto('http://127.0.0.1:8811/index.html');p.get_by_text('不添加提示',exact=False).click()
  nav(p,'活动相册');p.get_by_role('button').filter(has_text='《双声道》开播合影').click();ck('album clue detail',p.get_by_role('button',name='📌 钉到导播笔记').count()>0);p.get_by_role('button',name='📌 钉到导播笔记').click();ck('album optional photo pinned','photo' in state(p)['pinned'])
  nav(p,'公益马拉松');p.get_by_role('button',name='▶ 试听').first.click();p.wait_for_timeout(100);ck('listen simulation action',not state(p)['endingSeen'])
  nav(p,'听众留言簿');p.locator('textarea').fill('夜航测试留言');p.get_by_role('button',name='发表留言').click();p.wait_for_timeout(100);ck('guestbook local posting',len(state(p)['guestPosts'])==1)
  nav(p,'点歌单');p.locator('input:not([type=checkbox])').nth(1).fill('测试曲');p.get_by_role('button',name='提交点歌').click();p.wait_for_timeout(100);ck('song request local posting',len(state(p)['requests'])==1)
  nav(p,'我的导播笔记');ck('notes optional clue',p.get_by_text('1996 年合影',exact=False).count()>0)
  ck('side actions do not unlock intern or ending',not state(p)['internUnlocked'] and not state(p)['endingSeen']);b.close()
except Exception as e:r.append({'error':str(e)})
finally:srv.shutdown();srv.server_close();Path('judge/haian-diaopin/evidence/side-branches.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
if any('error' in x for x in r):raise SystemExit(1)
