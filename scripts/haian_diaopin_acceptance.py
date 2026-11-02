import json,sys,threading,functools
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path.cwd()))
from harness.judge import Judge
out=Path('judge/haian-diaopin/evidence'); report={'checks':[]}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',8811),functools.partial(Quiet,directory='tasks/haian-diaopin/mirror'));threading.Thread(target=server.serve_forever,daemon=True).start()
def check(label,cond,details=None):
 report['checks'].append({'id':label,'pass':bool(cond),'details':details}); assert cond,label
def snap(page,judge,step):
 judge.values={k:bool(page.evaluate(v['expr'])) for k,v in judge.cfg['hooks'].items()};judge.update(step);return judge.score()
def nav(page,text): page.locator('.nav-link').filter(has_text=text).first.click();page.wait_for_timeout(100)
def new(p,hints=False):
 b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page(viewport={'width':1366,'height':900});page.set_default_timeout(5000);page.goto('http://127.0.0.1:8811/index.html');page.get_by_text('添加提示（推荐首次游玩）' if hints else '不添加提示',exact=False).click();page.wait_for_timeout(200);return b,page
def storage(page):return page.evaluate("JSON.parse(localStorage.getItem('coastfm893_save_v1'))")
def login(page,answer):
 nav(page,'实习 DJ 园地');page.locator('input').last.fill(answer);page.get_by_role('button',name='登录',exact=True).click();page.wait_for_timeout(200)
try:
 with sync_playwright() as p:
  cfg=json.loads(Path('judge/haian-diaopin/judge.json').read_text(encoding='utf8'))
  b,page=new(p);j=Judge(cfg,'haian-diaopin');check('initial no scoring',snap(page,j,0)['checkpoints_reached']==0)
  nav(page,'听众留言簿');check('before login hidden gap',page.get_by_text('编号 #1189—#1191 缺失',exact=False).count()>0)
  login(page,'11111111');check('wrong password no score',not storage(page)['internUnlocked'] and snap(page,j,1)['checkpoints_reached']==0)
  login(page,'19940240');score=snap(page,j,2);check('correct no-hint login scores',score['checkpoints_reached']==1 and not score['ending_reached'],score)
  check('below threshold restore disabled',page.get_by_role('button',name='🔓 恢复第 7 段存档').is_disabled())
  check('after login intern can pin ids',page.get_by_text('被隐藏的留言 #1189—#1191').count()>0)
  page.get_by_role('button',name='📌 钉到导播笔记').first.click();page.wait_for_timeout(100);check('ids pin after login', 'ids' in storage(page)['pinned'])
  nav(page,'听众留言簿');check('after login hidden posts visible',page.get_by_text('#1189',exact=False).count()>0 and page.get_by_text('编号 #1189—#1191 缺失',exact=False).count()==0)
  nav(page,'点歌单');page.get_by_role('button',name='📌 钉到导播笔记').nth(0).click();page.get_by_role('button',name='📌 钉到导播笔记').first.click()
  nav(page,'录音室');page.get_by_role('button',name='📌 钉到导播笔记').first.click()
  nav(page,'DJ 专栏');page.get_by_role('button',name='📌 钉到导播笔记').first.click();check('five keys reached',len(storage(page)['pinned'])==5,storage(page)['pinned'])
  nav(page,'实习 DJ 园地');page.get_by_role('button',name='🔓 恢复第 7 段存档').click();page.wait_for_timeout(900);score=snap(page,j,3);check('ending reached after recovery',score['ending_reached'] and score['ending_tier']=='normal',score)
  page.wait_for_timeout(25000);check('transcript complete',page.get_by_text('真相拼图',exact=False).count()>0)
  page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='🔄 重置存档站，再玩一次').click();page.wait_for_timeout(300);s=storage(page);check('reset clears state',not s['pinned'] and not s['internUnlocked'] and not s['endingSeen'] and not s['hintChosen'],s)
  fresh=Judge(cfg,'haian-diaopin');check('fresh judge after reset has no score',snap(page,fresh,0)['checkpoints_reached']==0 and not fresh.score()['ending_reached'])
  b.close()
  b,page=new(p,True);j=Judge(cfg,'haian-diaopin');nav(page,'实习 DJ 园地');page.get_by_role('button',name='忘记密码？').click();check('hint exposes formula',page.get_by_text('开播那年',exact=False).count()>0)
  page.locator('input').last.fill('19940240');page.get_by_role('button',name='登录',exact=True).click();page.wait_for_timeout(200);score=snap(page,j,1);check('hint mode login not scored',storage(page)['internUnlocked'] and score['checkpoints_reached']==0 and any(e['id']=='hint_mode' for e in score['events']),score)
  b.close()
except Exception as e:
 report['error']=str(e)
finally:
 server.shutdown();server.server_close();(out/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
if 'error' in report:sys.exit(1)
