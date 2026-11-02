from pathlib import Path
import sys,json,threading,functools,http.server,traceback
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from harness.judge import Judge
judge_config=json.loads((ROOT/'judge/guyi-jiuzhi/judge.json').read_text(encoding='utf-8'))
judge=Judge(judge_config,'guyi-jiuzhi',ROOT)
SITE=ROOT/'tasks/guyi-jiuzhi/mirror'
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/'verification'
OUT.mkdir(parents=True,exist_ok=True)
PORT=int(sys.argv[2]) if len(sys.argv)>2 else 8831
server=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(SITE)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{PORT}/'; report={'actions':[],'dialogs':[],'page_errors':[],'http_errors':[],'page_audit':[]}
def note(name,p):
 vals={}
 for k,h in judge_config['hooks'].items():
  vals[k]=any(page.evaluate('() => Boolean('+h['expr']+')') for page in p.context.pages if page.url.startswith(base))
 judge.values=vals;judge.update(len(report['actions']))
 report['actions'].append({'check':name,'url':p.url,'text':p.locator('body').inner_text()[-1800:],'judge_values':vals,'judge_score':judge.score()});p.screenshot(path=str(OUT/(str(len(report['actions']))+'.png')),full_page=True)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='msedge',headless=True)
  ctx=browser.new_context(viewport={'width':1366,'height':900},locale='zh-CN')
  def attach(p):
   p.on('pageerror',lambda e:report['page_errors'].append({'url':p.url,'error':str(e)}))
   p.on('dialog',lambda d:(report['dialogs'].append(d.message),d.accept()))
   p.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  ctx.on('page',attach)
  p=ctx.new_page();p.goto(base+'index.html');p.locator('#search-input').fill('不存在测试');p.locator('#search-btn').click();assert '未找到' in p.locator('#results-area').inner_text();note('negative_search',p)
  p.locator('#search-input').fill('古邑县');p.locator('#search-btn').click();p.locator('.result-item.clickable').click();p.wait_for_url('**/level1-1.html');note('entry_search_to_radio',p)
  with p.expect_popup() as po:p.locator('.date-box').click()
  clock=po.value;clock.wait_for_load_state();clock.locator('#calibrate-btn').click();assert clock.locator('#system-alert').is_visible();note('wrong_clock_rejected',clock);clock.locator('.alert-close').click()
  for k,v in [('year','2009'),('month','4'),('day','12'),('hour','17'),('minute','02')]:clock.locator('#input-'+k).fill(v)
  clock.locator('#calibrate-btn').click();assert clock.locator('#image-modal').is_visible();note('clock_success',clock);clock.close()
  p.locator('a[href="level1-yght.html"]').first.click();p.wait_for_url('**/level1-yght.html');p.locator('.login-btn').first.click();note('blank_login_rejected',p)
  p.locator('#employee-id').fill('wrong');p.locator('#secret-key').fill('wrong');p.locator('.login-btn').first.click();note('wrong_login_rejected',p)
  p.locator('button[type=reset]').click();assert p.locator('#employee-id').input_value()=='';assert p.locator('#secret-key').input_value()==''
  p.locator('#employee-id').fill('943851198907209213');p.locator('#secret-key').fill('YH82-GS71-LH36-CV94')
  with p.expect_popup() as po:p.locator('.login-btn').first.click()
  q=po.value;q.wait_for_load_state();note('employee_login',q)
  q.locator('a[href="level2-qftctz.html"]').click();q.locator('#submitStatsBtn').click();assert not q.locator('#imageModal').is_visible();note('blank_statistics_rejected',q)
  for y,v in [(2005,6),(2006,5),(2007,2),(2008,3),(2009,16)]:q.locator('#input'+str(y)).fill(str(v))
  q.locator('#submitStatsBtn').click();assert q.locator('#imageModal').is_visible();note('statistics_success',q)
  p.locator('#employee-id').fill('灁㵒瘞軎禷禩䫻䫹');p.locator('#secret-key').fill('G7s9-kR2p-Bt4n-Qm6z')
  with p.expect_popup() as po:p.locator('.login-btn').first.click()
  r=po.value;r.wait_for_load_state();r.locator('.lock-close').filter(has_text='我已了解').click();note('terminal_login',r)
  for code,value in [('gw','3461'),('yl','3538'),('ls','5779')]:
   r.locator('#pw-'+code).fill('0000');r.locator('#pw-'+code).locator('..').locator('button').click();assert '错误' in r.locator('#msg-'+code).inner_text()
   r.locator('#pw-'+code).fill(value);r.locator('#pw-'+code).locator('..').locator('button').click();assert 'unlocked' in r.locator('#body-'+code).get_attribute('class');note('archive_'+code+'_button_success',r)
  r.reload();r.locator('.lock-close').filter(has_text='我已了解').click();r.locator('#pw-gw').fill('0414');r.locator('#pw-gw').press('Enter');assert 'unlocked' in r.locator('#body-gw').get_attribute('class');note('enter_archive_bypass_0414',r)
  with r.expect_popup() as po:r.locator('[onclick*="level3-3.html"]').click()
  s=po.value;s.wait_for_load_state();note('login_records',s);s.locator('#delete-btn').click();s.wait_for_timeout(10500);note('delete_records_horror_branch',s)
  s.locator('#logout-btn').click();s.wait_for_url('**/level3-end.html');s.locator('#answer-btn').click();s.locator('.btn-agree').click();assert '祭品' in s.locator('#ending-title').inner_text();note('agree_failure_ending',s);assert judge.failure_id=='agree_failure' and not judge.ending_reached
  s.reload();judge=Judge(judge_config,'guyi-jiuzhi',ROOT);s.locator('#answer-btn').click();s.wait_for_timeout(5200);s.locator('#refuse-btn').click();assert '统治结束' in s.locator('#ending-title').inner_text();note('refuse_success_ending',s);assert judge.ending_reached and judge.failure_id is None
  s.locator('[onclick="endGame()"]').click();s.wait_for_url('**/level3-final.html');note('final_credits',s)
  audit=ctx.new_page()
  for f in sorted(SITE.glob('*.html')):
   before=len(report['page_errors']);audit.goto(base+f.name);audit.wait_for_timeout(30);report['page_audit'].append({'file':f.name,'title':audit.title(),'errors':report['page_errors'][before:]})
  fresh=browser.new_context();t=fresh.new_page();t.goto(base+'index.html');assert t.locator('#search-input').input_value()=='';report['fresh_context_reset']=True;fresh.close()
  report['ok']=True;browser.close()
except Exception as e:report['ok']=False;report['failure']=str(e);report['traceback']=traceback.format_exc()
finally:
 server.shutdown();(OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'ok':report.get('ok'),'failure':report.get('failure'),'checks':len(report['actions']),'errors':report['page_errors']},ensure_ascii=False))
