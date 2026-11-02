from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess,sys,time,json
out=Path('judge/haian-diaopin/evidence'); results=[]
s=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/haian-diaopin/mirror','--port','8811'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def state(page): return page.evaluate("JSON.parse(localStorage.getItem('coastfm893_save_v1'))")
try:
 time.sleep(2)
 with sync_playwright() as p:
  b=p.chromium.launch(channel='msedge',headless=True); page=b.new_page(viewport={'width':1366,'height':900}); page.set_default_timeout(4000); page.goto('http://127.0.0.1:8811/index.html'); page.get_by_text('不添加提示',exact=False).click()
  def nav(x): page.locator('.nav-link').filter(has_text=x).first.click();page.wait_for_timeout(150)
  def record(x): results.append({'step':x,'state':state(page),'body':page.locator('body').inner_text()[-5000:]})
  nav('实习 DJ 园地'); page.locator('input').last.fill('11111111');page.get_by_role('button',name='登录',exact=True).click();record('wrong password')

  nav('DJ 专栏');page.get_by_role('button',name='📌 钉到导播笔记').first.click();record('pin zhou')
  nav('听众留言簿');record('guestbook');page.get_by_role('button',name='📌 钉到导播笔记').first.click();record('pin ids')
  nav('点歌单');page.get_by_role('button',name='📌 钉到导播笔记').first.click();page.get_by_role('button',name='📌 钉到导播笔记').first.click();record('pin playlist')
  nav('录音室');page.get_by_role('button',name='📌 钉到导播笔记').first.click();record('pin moved')
  nav('实习 DJ 园地');page.locator('input').last.fill('19940240');page.get_by_role('button',name='登录',exact=True).click();record('threshold intern');page.get_by_text('恢复第 7 段',exact=False).last.click();page.wait_for_timeout(1000);record('restore')
  page.wait_for_timeout(25000);record('ending');page.screenshot(path=str(out/'ending.png'),full_page=True);page.on('dialog',lambda d:d.accept());page.get_by_role('button',name='🔄 重置存档站，再玩一次').click();page.wait_for_timeout(300);record('reset')
  b.close()
except Exception as e: results.append({'error':str(e)})
finally:
 (out/'flow.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');s.terminate();s.wait()
