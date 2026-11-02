from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess,sys,time,json
out=Path('judge/haian-diaopin/evidence')
s=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/haian-diaopin/mirror','--port','8811'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 time.sleep(2)
 with sync_playwright() as p:
  b=p.chromium.launch(channel='msedge',headless=True); page=b.new_page(viewport={'width':1366,'height':900})
  page.goto('http://127.0.0.1:8811/index.html'); page.wait_for_timeout(500)
  buttons=page.get_by_role('button').all_text_contents(); print('initial buttons',buttons)
  page.get_by_text('不添加提示',exact=False).first.click(timeout=3000)
  for nav in ['本台简介 / 收听频率','公告栏','节目表','DJ 专栏','听众留言簿','点歌单 / 播放列表查询','公益马拉松专题','录音室 / 带库维护','活动相册','实习 DJ 园地','我的导播笔记','新手指南']:
   try:
    page.get_by_text(nav,exact=False).first.click(timeout=2000); page.wait_for_timeout(100)
    (out/('view-'+str(len(list(out.glob('view-*'))))+'.txt')).write_text(nav+'\n'+page.locator('body').inner_text(),encoding='utf8')
    print(nav,'OK',page.get_by_role('button').all_text_contents())
   except Exception as e: print(nav,'ERROR',str(e)[:250])
  b.close()
finally: s.terminate();s.wait()
