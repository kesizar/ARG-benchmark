from pathlib import Path
import subprocess,sys,time,json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];A=R/'tasks/shiguang-wenrou/audit';log=[]
def main():
 server=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/shiguang-wenrou/mirror','--port','8831'],cwd=R,stdout=open(A/'server.log','w'),stderr=subprocess.STDOUT)
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(channel="msedge",headless=True,timeout=15000);c=b.new_context(viewport={'width':1366,'height':900},service_workers='block');p=c.new_page();p.set_default_timeout(4000)
   c.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8831') else r.abort())
   def dump(label):
    log.append({'stage':label,'url':p.url,'state':p.evaluate('localStorage.getItem("totor_gameState_v2")'),'text':p.locator('body').inner_text(),'controls':p.locator('button,a,input,select').evaluate_all('(es)=>es.map(e=>({tag:e.tagName,id:e.id,text:e.textContent,title:e.title,cls:e.className,visible:!!(e.offsetWidth||e.offsetHeight)}))')});(A/'branch-ui-trace.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
   try:
    p.goto('http://127.0.0.1:8831/');p.get_by_text('我已了解，进入游戏',exact=True).click();p.get_by_text('开始游戏',exact=True).click();p.get_by_text('直接开始',exact=True).click();p.locator('#skip-btn').click();p.locator('body').click(position={'x':30,'y':30});p.wait_for_url('**/chapter1.html');p.locator('body').click();p.wait_for_url('**/room.html');p.locator('.inv-fab').click();p.wait_for_timeout(1000)
    p.get_by_text('过去・中学',exact=True).click();p.get_by_title('旧电脑',exact=True).click();p.locator('.inv-overlay__link').click();p.wait_for_url('**/computer-desktop.html')
    p.locator('#pw-input').fill('WRONG');p.locator('#pw-submit').click();assert '密码错误' in p.locator('#pw-error').inner_text();dump('boot_negative')
    p.locator('#pw-input').fill('CYCLYQ');p.locator('#pw-submit').click();p.wait_for_timeout(800);p.locator('.cd-mono-skip').click();p.locator('.cd-mono-overlay').click(position={'x':20,'y':20});dump('boot_positive')
    p.locator('#icon-folder').dblclick();p.locator('[data-action="password"]').click();p.locator('#txt-modal-close').click()
    for char in 'PASSWORD':p.locator('[data-char="'+char+'"]').click()
    p.locator('.fx-item').first.click();p.locator('#txt-modal-close').click();dump('password_path')
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
    p.locator('.inv-fab').click();p.wait_for_timeout(800);p.get_by_text('现在',exact=True).click();p.get_by_title('手机',exact=True).click();p.locator('[data-app="wechat"]').first.click();p.locator('[data-contact="xujiajun"]').click();p.locator('#pw-chat-draft-send').click();dump('jiajun_draft_sent')
    p.locator('.pw-close').click();p.wait_for_timeout(800);p.get_by_text('过去・中学',exact=True).click();p.get_by_title('旧电脑',exact=True).click();p.locator('.inv-overlay__link').click();p.wait_for_url('**/computer-desktop.html');p.locator('#icon-forum').dblclick();p.wait_for_url('**/school.html');dump('school')
    def mono():
     if p.locator('.forum-mono-skip').is_visible():p.locator('.forum-mono-skip').click();p.locator('.forum-mono-overlay').click(position={'x':20,'y':20});p.wait_for_timeout(700)
    mono();p.get_by_role('button',name='《小兔子》',exact=True).click();p.wait_for_timeout(900);mono();dump('rabbit_thread')
    for uid,answer in [('user_8814','周以恒'),('user_1350','许家俊'),('user_6427','陈奕辰'),('user_3059','林语晴'),('user_5192','马文哲'),('user_0538','陈思妤'),('user_1966','唐雨桐')]:
     box=p.locator('[data-author-id="'+uid+'"] .id-tag-box').first;box.click();p.locator('.id-tag-box input').fill(answer);p.locator('.id-tag-box input').press('Enter');p.wait_for_timeout(100);mono()
    dump('identity_all_correct')
    p.locator('.inv-fab').click();p.wait_for_timeout(800);p.get_by_text('现在',exact=True).click();p.get_by_title('手机',exact=True).click();p.locator('[data-app="wechat"]').first.click();p.locator('[data-tab="contacts"]').click();p.locator('[data-shortcut="addfriend"]').click()
    for number in ['000','041862743','043672158','042751862']:
     p.locator('#pw-addfriend-input').fill(number);p.locator('#pw-addfriend-submit').click();dump('phone_'+number)
    p.locator('#pw-addfriend-confirm').click();p.locator('#pw-addfriend-back').click();p.locator('[data-tab="chat"]').click();p.locator('[data-contact="zhouyiheng"]').click();p.locator('#pw-chat-draft-send').click();p.wait_for_timeout(16000);dump('zhou_rabbit_link')
    p.locator('.pw-chat-bubble__link').click();p.get_by_role('button',name='确定',exact=True).click();p.wait_for_url('**/chapter2end.html');p.locator('#start-gate').click();p.wait_for_timeout(1400);p.locator('#skip-btn').click();p.locator('body').click(position={'x':20,'y':20});p.wait_for_url('**/chapter3.html',timeout=12000);p.locator('body').click();p.wait_for_url('**/xiaotuzi.html');p.locator('.xtz-animal-btn').first.click();p.locator('#xtz-onboarding-enter').click();p.wait_for_timeout(1200);p.locator('#xtz-mono-skip').click();p.locator('#xtz-mono-overlay').click(position={'x':20,'y':20});p.wait_for_timeout(1100);dump('chapter3_forest')
    for post in ['1','2','3','4','5','6','7']:
     card=p.locator('.xtz-archive-card[data-post="'+post+'"]')
     if card.count():
      card.click();dump('forest_post_'+post);p.locator('.xtz-active [data-back]').click()
    dump('forest_complete')


   except Exception as e:dump('failure');raise
   b.close()
 finally:server.terminate()
if __name__=='__main__':main()
