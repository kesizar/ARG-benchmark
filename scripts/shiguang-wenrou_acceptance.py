from pathlib import Path
import subprocess,sys,time,json,os
from playwright.sync_api import sync_playwright
SOURCE=Path(__file__).resolve().parents[1];R=Path(os.environ.get('SHIGUANG_ROOT',str(SOURCE)));A=Path(os.environ.get('SHIGUANG_OUTPUT',str(SOURCE/'tasks/shiguang-wenrou/audit')));A.mkdir(parents=True,exist_ok=True);PORT=os.environ.get('SHIGUANG_PORT','8831');M=Path(os.environ.get('SHIGUANG_GAME_ROOT',str(R/'tasks/shiguang-wenrou/mirror')));log=[]
sys.path.insert(0,str(R));from harness.judge import Judge
j=Judge.load(R/'judge/shiguang-wenrou/judge.json','shiguang-wenrou',R)
def main():
 server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(M),'--port',PORT],cwd=R,stdout=open(A/'server.log','w'),stderr=subprocess.STDOUT)
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(channel="msedge",headless=True,timeout=15000);c=b.new_context(viewport={'width':1366,'height':900},service_workers='block');p=c.new_page();p.set_default_timeout(4000)
   c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(('http://127.0.0.1:'+PORT)) else r.abort())
   def dump(label):
    values={k:p.evaluate(v['expr']) for k,v in j.cfg['hooks'].items()};j.values=values;j.update(len(log))
    log.append({'stage':label,'judge':j.score(),'hook_values':values,'url':p.url,'state':p.evaluate('localStorage.getItem("totor_gameState_v2")'),'text':p.locator('body').inner_text(),'controls':p.locator('button,a,input,select').evaluate_all('(es)=>es.map(e=>({tag:e.tagName,id:e.id,text:e.textContent,title:e.title,cls:e.className,visible:!!(e.offsetWidth||e.offsetHeight)}))')});(A/'ui-trace.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
   try:
    p.goto('http://127.0.0.1:'+PORT+'/');p.get_by_text('我已了解，进入游戏',exact=True).click();p.get_by_text('开始游戏',exact=True).click();p.get_by_text('直接开始',exact=True).click();p.locator('#skip-btn').click();p.locator('body').click(position={'x':30,'y':30});p.wait_for_url('**/chapter1.html');p.locator('body').click();p.wait_for_url('**/room.html');p.locator('.inv-fab').click();p.wait_for_timeout(1000)
    p.get_by_text('过去・中学',exact=True).click();p.get_by_title('旧电脑',exact=True).click();p.locator('.inv-overlay__link').click();p.wait_for_url('**/computer-desktop.html')
    p.locator('#pw-input').fill('WRONG');p.locator('#pw-submit').click();assert '密码错误' in p.locator('#pw-error').inner_text();dump('boot_negative')
    p.locator('#pw-input').fill('CYCLYQ');p.locator('#pw-submit').click();p.wait_for_timeout(800);p.locator('.cd-mono-skip').click();p.locator('.cd-mono-overlay').click(position={'x':20,'y':20});dump('boot_positive')
    p.locator('#icon-folder').dblclick();p.locator('[data-action="password"]').click();p.locator('#txt-modal-close').click()
    for char in 'PASSWORD':p.locator('[data-char="'+char+'"]').click()
    p.locator('.fx-item').first.click();p.locator('#txt-modal-close').click();dump('password_path')
    for route in ['CYCLYQ','LANOTTE','GINO']:
     p.locator('.fx-crumb').first.click()
     for char in route:p.locator('[data-char="'+char+'"]').click()
     p.locator('[data-target-index]').first.wait_for(state='visible')
     for i in range(p.locator('[data-target-index]').count()):
      p.locator('[data-target-index]').nth(i).click()
      if p.locator('#img-modal-close').is_visible():p.locator('#img-modal-close').click()
      elif p.locator('#txt-modal-close').is_visible():p.locator('#txt-modal-close').click()
     dump('maze_'+route)

    p.locator('.wm-window__btn--close').click();p.locator('#icon-friendster').dblclick();p.wait_for_url('**/friendster.html')
    p.locator('[data-el="q-firstphoto"]').fill('WRONG');p.get_by_role('button',name='登入',exact=True).click();dump('friendster_negative')
    for sel,v in [('q-firstphoto','20110515'),('q-teacher','王老师'),('q-friend','许家俊')]:p.locator('[data-el="'+sel+'"]').fill(v)
    p.get_by_role('button',name='登入',exact=True).click();dump('friendster_positive')
    p.locator('[data-el="keyword-zhou"]').click();p.locator('[data-el="mono-skip"]').click();p.locator('[data-el="mono-overlay"]').click(position={'x':20,'y':20});p.wait_for_timeout(800)
    p.locator('.inv-fab').click();p.wait_for_timeout(800);p.get_by_text('过去・大学',exact=True).click();p.get_by_title('平板',exact=True).click()
    p.locator('[data-el="emoji-submit"]').click();dump('tablet_negative')
    for e in ['🌳','☔','☀️']:p.get_by_role('button',name=e,exact=True).click()
    p.locator('[data-el="emoji-submit"]').click();dump('tablet_positive')
    p.locator('[data-app="notes"]').first.click();p.locator('[data-note="secret"]').click();p.locator('#iw-secret-pw-input').fill('WRONG');p.locator('#iw-secret-pw-submit').click();dump('secret_negative')
    p.locator('#iw-secret-pw-input').fill('La Notte');p.locator('#iw-secret-pw-submit').click();p.locator('.iw-mono-skip').click();p.locator('.iw-mono-overlay').click(position={'x':20,'y':20});p.wait_for_timeout(700);dump('secret_positive')
    p.locator('#iw-secret-goto-link').click();p.locator('#iw-secret-goto-confirm').click();p.wait_for_url('**/chapter1end.html');p.locator('#start-gate').click();p.wait_for_timeout(1400);p.locator('#skip-btn').click();p.locator('body').click(position={'x':20,'y':20});p.wait_for_url('**/chapter2.html',timeout=12000);p.locator('body').click();p.wait_for_url('**/ring/index.html');dump('chapter2_start')
    p.get_by_text('时光胶囊服务',exact=True).click();p.wait_for_url('**/timecapsule.html');p.locator('#tc-submit').click();dump('capsule_negative')
    p.locator('#tc-q1-btn').click()
    while p.locator('#tc-cal-title').inner_text()!='2026年5月':p.locator('#tc-cal-prev').click()
    p.locator('[data-day="15"]').click();p.locator('#tc-q2').select_option('La Promesse');p.locator('#tc-q3').fill('032503122517');p.locator('#tc-submit').click();p.wait_for_url('**/CYC.html');p.locator('#cyc-gate').click();p.wait_for_timeout(1100);dump('capsule_positive')
    p.locator('#anon-comment').click();p.locator('#cyc-mono-skip').click();p.locator('#cyc-mono-overlay').click(position={'x':20,'y':20});p.wait_for_timeout(700);dump('capsule_comment')
    p.locator('#tc-logout').click();p.wait_for_url('**/story.html');p.get_by_text('了解时光胶囊服务 →',exact=True).click();p.wait_for_url('**/timecapsule.html');p.locator('#tc-q1-btn').click()
    # Original calendar opens May 2026.
    while p.locator('#tc-cal-title').inner_text()!='2026年9月':p.locator('#tc-cal-prev').click()
    p.locator('[data-day="9"]').click();p.locator('#tc-q2').select_option("L'Éternité");p.locator('#tc-q3').fill('WRONG');p.locator('#tc-submit').click();dump('yuqing_negative')
    p.locator('#tc-q3').fill('CYCLYQ');p.locator('#tc-submit').click();p.locator('#tc-mono-skip').click();p.locator('#tc-mono-overlay').click(position={'x':20,'y':20});p.wait_for_url('**/LYQ.html');p.locator('#lyq-gate').click();p.wait_for_timeout(1100);dump('yuqing_positive')
    p.locator('#lyq-bday-line').click();p.locator('#lyq-mono-skip').click();p.locator('#lyq-mono-overlay').click(position={'x':20,'y':20});p.wait_for_url('**/ending-select.html');dump('ending_select_locked')
    for char,name in [('xujiajun','wufa'),('zhangyunen','zhenxi'),('zhouyiheng','corner')]:
     p.locator('[data-char="'+char+'"]').click();p.locator('#es-chat-skip').click();p.locator('#es-chat-lyric').click();p.locator('#es-confirm-go').click();p.wait_for_url('**/ending-'+name+'.html');p.wait_for_timeout(1000)
     if name!='corner' and not p.locator('#es-content').evaluate('(e)=>e.classList.contains("es-content--show")'):p.locator('#es-gate-btn').click();p.wait_for_timeout(1400)
     if name=='corner':p.locator('#es-bridge-skip').click();p.locator('#es-bridge-overlay').click(position={'x':20,'y':20});p.wait_for_timeout(1100)
     assert p.locator('#es-content').evaluate('(e)=>e.classList.contains("es-content--show")');dump('ending_'+name);p.screenshot(path=str(A/('ending-'+name+'.png')),full_page=True)
     if name!='corner':p.get_by_text('返回',exact=True).click();p.wait_for_url('**/ending-select.html')





    for _ in range(12):
     if p.url.endswith('/LYQ.html'):break
     p.go_back()
    if p.locator('#lyq-gate').is_visible():p.locator('#lyq-gate').click();p.wait_for_timeout(1100)
    p.locator('.inv-fab').click();p.wait_for_timeout(800);p.get_by_text('设置',exact=True).click();p.once('dialog',lambda d:d.accept());p.locator('#inv-restart-btn').click();p.wait_for_url('**/prologue.html');assert p.evaluate('localStorage.length')==0;dump('ui_reset');assert not any(log[-1]['hook_values'].values())
    reset_j=Judge.load(R/'judge/shiguang-wenrou/judge.json','shiguang-wenrou',R);reset_j.values=log[-1]['hook_values'];reset_j.update(0);assert not reset_j.checkpoints and not reset_j.score()['ending_reached'];(A/'fresh-reset-judge.json').write_text(json.dumps(reset_j.score(),ensure_ascii=False,indent=2),encoding='utf-8')
   except Exception as e:dump('failure');raise
   b.close()
 finally:server.terminate()
if __name__=='__main__':main()
