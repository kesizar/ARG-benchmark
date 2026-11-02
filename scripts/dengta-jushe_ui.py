from pathlib import Path
import json,threading,functools,http.server,importlib.util
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'runs/dengta-jushe';KEY='lighthouse-theater-save-v1'
J=json.loads((R/'judge/dengta-jushe/judge.json').read_text(encoding='utf8'))
class Q(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def serve(root,port):
 s=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Q,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s

def flow(browser,url,out,full=True):
 c=browser.new_context(viewport={'width':1440,'height':1000});p=c.new_page();errors=[];external=[];p.on('pageerror',lambda e:errors.append(str(e)));p.route('**/*',lambda r:r.continue_() if r.request.url.startswith(url.split('/index')[0]) else (external.append(r.request.url),r.abort())[-1]);p.goto(url);p.get_by_text('自力模式（挑战）',exact=False).click();rows=[]
 def check(name,expected=None):
  print(name,flush=True);p.wait_for_timeout(80);state=p.evaluate('(k)=>JSON.parse(localStorage.getItem(k))',KEY);text=p.locator('body').inner_text();h={k:p.evaluate(v['expr']) for k,v in J['hooks'].items()};rows.append(dict(case=name,hooks=h,state=state,text=text))
  if expected:
   for k,v in expected.items():assert h[k]==v,(name,k,h)
  return state
 check('fresh',dict(login=False,reconstruction=False,cue_order=False,ending=False))
 for nav in ['剧社简介 / 演出须知','公告栏','戏单 / 档期查询','演员与工作人员表','排练室笔记','演出售后相册','观众留言簿','海报 / 附件搬迁说明']:
  p.get_by_role('button',name=nav,exact=False).first.click()
  if full:
   while p.get_by_role('button',name='钉到告示板',exact=False).count():p.get_by_role('button',name='钉到告示板',exact=False).first.click()
  check('visit-'+nav)
 p.get_by_role('button',name='后台实习园地',exact=False).first.click();p.get_by_placeholder('姓名拼音（小写）').fill('wrong');p.get_by_placeholder('八位数字').fill('19941017');p.get_by_role('button',name='登录',exact=True).click();assert '用户名或口令不正确' in p.locator('body').inner_text();check('wrong-login',{'login':False})
 p.get_by_placeholder('姓名拼音（小写）').fill(' Lin An ');p.get_by_placeholder('八位数字').fill('1994-10-17');p.get_by_role('button',name='登录',exact=True).click();check('login-normalized',{'login':True})
 if full:
  while p.get_by_role('button',name='钉到告示板',exact=False).count():p.get_by_role('button',name='钉到告示板',exact=False).first.click()
 selects=p.locator('select');correct=['灯下小夜曲','10月17日','三号排练室','周砚秋导演']
 for i,v in enumerate(correct):selects.nth(i).select_option(label=v)
 boxes=p.locator('input[type=checkbox]')
 for i in [1,4,5,6,9]:boxes.nth(i).check()
 if full:
  for i in range(4):
   options=selects.nth(i).locator('option').all_text_contents();wrong=next(x for x in options if x not in ['请选择',correct[i]]);selects.nth(i).select_option(label=wrong);p.get_by_role('button',name='核对并复原',exact=False).click();check('wrong-field-'+str(i),{'reconstruction':False});selects.nth(i).select_option(label=correct[i])
  boxes.nth(0).check();p.get_by_role('button',name='核对并复原',exact=False).click();check('wrong-cast-extra',{'reconstruction':False});boxes.nth(0).uncheck();boxes.nth(9).uncheck();p.get_by_role('button',name='核对并复原',exact=False).click();check('wrong-cast-missing',{'reconstruction':False});boxes.nth(9).check()
  p.get_by_role('button',name='全体：老周，生日快乐',exact=False).click();assert '已排好：0/6' in p.locator('body').inner_text();check('wrong-cue',{'cue_order':False})
  for line in ['灯塔的灯，每天晚上是谁点的？','不是灯塔的灯，是排练室的灯。','那今晚我们早点来，把灯先点上。','「道具间盘点」','嘘，走廊有脚步声。','老周，生日快乐。']:
   p.get_by_role('button',name=line,exact=False).click()
  check('cue-success',{'cue_order':True});p.get_by_role('button',name='重新洗牌',exact=False).click();check('cue-latched-after-shuffle',{'cue_order':True})
 p.get_by_role('button',name='核对并复原',exact=False).click();check('reconstruction-success',{'reconstruction':True,'ending':False});p.get_by_role('button',name='前往「庆生彩排揭晓」',exact=False).click();check('ending-enter-only',{'ending':False});p.get_by_role('button',name='推开门',exact=False).click();p.get_by_role('button',name='下一句',exact=False).click();p.get_by_role('button',name='直接看完',exact=True).click();check('ending-complete',{'ending':True});p.screenshot(path=str(O/(out+'-ending.png')),full_page=True)
 if full:
  p.get_by_role('button',name='去留言簿给老周写句祝福',exact=False).click();check('ending-leave',{'reconstruction':True,'ending':False});p.get_by_role('button',name='后台实习园地',exact=False).first.click();p.get_by_role('button',name='前往「庆生彩排揭晓」',exact=False).click();check('ending-reentry-needs-read',{'ending':False})
 p.once('dialog',lambda d:d.dismiss());p.get_by_role('button',name='重置进度（再玩一次）',exact=True).click();check('reset-cancel',{'reconstruction':True});p.once('dialog',lambda d:d.accept());p.get_by_role('button',name='重置进度（再玩一次）',exact=True).click();p.get_by_text('帮助模式（推荐）',exact=False).click();s=check('reset-confirm-help',dict(login=False,reconstruction=False,cue_order=False,ending=False));assert not s['backstageUnlocked'] and not s['pinned'] and not s['reconstructed'] and not s['cueGameDone']
 p.reload();check('reload-reset',{'login':False});assert not errors,errors;assert not external,external
 (O/(out+'.json')).write_text(json.dumps({'url':url,'normal_ui_only':True,'cases':rows,'errors':errors,'external_requests':external},ensure_ascii=False,indent=2),encoding='utf8');c.close();return len(rows)
if __name__=='__main__':
 srv=serve(R/'tasks/dengta-jushe/mirror',8811)
 try:
  with sync_playwright() as w:
   b=w.chromium.launch(channel='msedge');print(flow(b,'http://127.0.0.1:8811/index.html','ui-evidence'));b.close()
 finally:srv.shutdown()
