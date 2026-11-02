"""Non-scoring source recovery and UI audit; never supplies invented puzzle gates."""
from pathlib import Path
import json, hashlib, re, shutil, threading, functools, http.server, zipfile
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]; T=R/'tasks/beiyu-zhaoming'; O=R/'runs/beiyu-zhaoming'; J=R/'judge/beiyu-zhaoming'
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def server(root,port):
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 s=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
def main():
 O.mkdir(parents=True,exist_ok=True);J.mkdir(parents=True,exist_ok=True)
 shutil.copytree(T/'upstream/beiyuarg-main',T/'mirror',dirs_exist_ok=True)
 shutil.copyfile(R/'ARG-packs/verify-416/bodies/377.html',O/'historical-377.html')
 files=[p for p in (T/'mirror').iterdir() if p.is_file()]; missing=[];external=[];edges=[]
 for p in files:
  if p.suffix!='.html':continue
  text=p.read_text(encoding='utf-8')
  refs=re.findall(r'(?:href|src)=["\']([^"\']+)',text)+re.findall(r'["\']([A-Za-z0-9_]+\.html)["\']',text)
  for ref in sorted(set(refs)):
   if ref.startswith('#'):continue
   if urlsplit(ref).scheme:external.append([p.name,ref]);continue
   target=unquote(ref.split('#')[0].split('?')[0]);edges.append([p.name,target])
   if not (T/'mirror'/target).is_file():missing.append([p.name,target])
 save(O/'resource-audit.json',{'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in files],'missing':missing,'external':external,'edges':edges,'upstream_sha256':sha(T/'upstream.zip'),'historical_index_identical':sha(O/'historical-377.html')==sha(T/'mirror/index.html')})
 assert not external
 srv=server(T/'mirror',8821); evidence=[];errors=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True)
  c=b.new_context(viewport={'width':1366,'height':900});p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:(evidence.append({'dialog':d.message}),d.accept()))
  def visit(name):p.goto('http://127.0.0.1:8821/'+name);p.wait_for_timeout(80)
  def snap(label):
   p.screenshot(path=str(O/(label+'.png')),full_page=True);evidence.append({'label':label,'url':p.url,'text':p.locator('body').inner_text()})
  def search(term):p.locator('#searchInput').fill(term);p.get_by_role('button',name='搜索',exact=True).click();p.wait_for_timeout(80)
  visit('index.html');search('不存在的线索');assert p.url.endswith('index.html');snap('unknown-search')
  # Locked final pages reject without the three visited profiles; no storage writes.
  visit('lsy1.html');assert p.url.endswith('index.html');visit('only_end.html');assert p.url.endswith('index.html')
  search('王浩然');assert p.url.endswith('whr.html');snap('ordinary-profile')
  search('环境监测终端');p.locator('.log-tag').first.click();snap('undefined-attachment-handler')
  p.get_by_role('link',name='归档',exact=True).click()
  for row in p.locator('.entry-head').all():row.click()
  snap('logs-expanded');search('实验楼');snap('lab');search('监控');snap('monitor');p.locator('.attach').click();snap('undefined-monitor-handler')
  # Query controls are inert in the original, not puzzle validation.
  p.get_by_role('button',name='查询',exact=True).click();search('王浩然');assert p.url.endswith('clue_dossier.html');snap('dossier')
  for link,filename in [('whr1.html','王浩然'),('zyy1.html','张明远'),('zjg1.html','赵建国')]:
   p.locator('a[href="'+link+'"]').click();snap(filename);p.go_back()
  p.locator('a[href="lsy1.html"]').click()
  for _ in range(15):p.locator('body').click(position={'x':10,'y':10})
  snap('lsy-revealed');assert 'jiaotiju.html' in p.locator('body').inner_text()
  # Explicit author filename hint: normal address navigation, not a source-derived credential.
  visit('jiaotiju.html');p.get_by_role('button',name='提交举报').click();assert p.url.endswith('jiaotiju.html');snap('empty-report-rejected')
  p.locator('#school').select_option(label='北榆市第一中学');p.locator('#teacher').fill('无关教师');p.get_by_role('button',name='清空重填').click();assert p.locator('#teacher').input_value()==''
  p.locator('#school').select_option(label='北榆市第一中学');p.locator('#teacher').fill('无关教师');p.get_by_role('button',name='提交举报').click();assert p.url.endswith('only_end.html')
  for _ in range(9):p.locator('body').click(position={'x':10,'y':10})
  snap('incorrect-report-still-advances');assert 'fugao.html' in p.locator('body').inner_text()
  visit('fugao.html');snap('original-ending');assert '调查结束，你查明了事情的真相，仅此而已' in p.locator('body').inner_text()
  # Reset all session and local state via a genuinely fresh context.
  c.close();c=b.new_context();p=c.new_page();p.on('dialog',lambda d:d.accept());visit('lsy1.html');assert p.url.endswith('index.html');snap('fresh-reset')
  # Ordinary positive report path, preconditions achieved by visible profile links again.
  search('线索')
  for filename in ['whr1.html','zyy1.html','zjg1.html']:
   p.locator('a[href="'+filename+'"]').click();p.go_back()
  p.locator('a[href="lsy1.html"]').click()
  for _ in range(15):p.locator('body').click(position={'x':10,'y':10})
  visit('jiaotiju.html');p.locator('#school').select_option(label='北榆市·昭明中学');p.locator('#teacher').fill('张明远');p.locator('#detail').fill('2025年11月15日实验楼三层东侧楼梯间，王浩然遭霸凌，监控缺失45分钟，节点后被拆除。');p.get_by_role('button',name='提交举报').click()
  for _ in range(9):p.locator('body').click(position={'x':10,'y':10})
  snap('positive-report');visit('fugao.html');snap('positive-ending');c.close();b.close()
 srv.shutdown();save(O/'ui-evidence.json',{'actions':'normal UI, author-hinted URL navigation only; no storage injection or JS mutation','evidence':evidence,'pageerrors':errors,'paid_api_calls':0})
 print('Resource and UI audit saved; formal scoring ineligible.')
if __name__=='__main__':main()
