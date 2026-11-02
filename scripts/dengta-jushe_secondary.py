from pathlib import Path
import re,json,threading,functools,http.server
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'runs/dengta-jushe'
class Q(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',8811),functools.partial(Q,directory=str(R/'tasks/dengta-jushe/mirror')));threading.Thread(target=s.serve_forever,daemon=True).start()
rows=[]
with sync_playwright() as w:
 b=w.chromium.launch(channel='msedge');c=b.new_context();p=c.new_page();p.goto('http://127.0.0.1:8811/index.html');p.get_by_text('帮助模式（推荐）',exact=False).click()
 def rec(name):rows.append({'case':name,'text':p.locator('body').inner_text(),'state':p.evaluate('JSON.parse(localStorage.getItem("lighthouse-theater-save-v1"))')})
 def nav(name):p.get_by_role('button',name=name,exact=False).first.click()
 nav('戏单 / 档期查询');p.get_by_placeholder('剧名 / 场次编号 / 演员').fill('不存在ZZZ');p.get_by_role('button',name='查询',exact=False).last.click();assert '没有找到匹配' in p.locator('body').inner_text();rec('search-no-results');p.get_by_role('button',name='清空',exact=True).click();p.get_by_placeholder('剧名 / 场次编号 / 演员').fill('2004-06');p.get_by_role('button',name='查看',exact=True).click();rec('withdrawn-playbill');p.get_by_role('button',name='钉到告示板',exact=False).click();p.get_by_role('button',name='清空',exact=True).click();p.locator('select').select_option(label='1994');p.get_by_role('button',name='查看',exact=True).first.click();rec('year-filter-existing-detail')
 nav('公告栏');titles=p.locator('li > button').filter(has_text=re.compile(r'^2004-'))
 assert titles.count()>0
 for i in range(titles.count()):titles.nth(i).click()
 rec('notice-toggle-all');nav('演出售后相册')
 for cat in ['演出剧照','后台花絮','道具间杂物','老照片','全部']:
  p.get_by_role('button',name=cat,exact=True).click()
  photos=p.locator('button').filter(has=p.locator('svg')).all()
  for photo in photos:photo.click()
  rec('album-category-'+cat)
 nav('我的告示板');p.get_by_role('button',name='取下',exact=True).first.click();rec('unpin');nav('观众留言簿');p.get_by_role('button',name='提交留言',exact=False).click();assert '留言至少写两个字' in p.locator('body').inner_text();rec('guestbook-empty');p.locator('textarea').fill('祝福');p.get_by_role('button',name='提交留言',exact=False).click();assert '匿名观众' in p.locator('body').inner_text();rec('guestbook-anonymous');p.reload();assert '祝福' in str(p.evaluate('localStorage.getItem("lighthouse-theater-save-v1")'));rec('guestbook-persist');nav('新朋友指南');
 for i in range(4):p.get_by_role('button',name='再给我一条提示',exact=False).click()
 rec('all-help-hints');b.close()
s.shutdown();(O/'secondary-ui.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print('secondary cases',len(rows))
