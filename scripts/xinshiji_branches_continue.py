import json,threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'judge/xinshiji/recovery/branches-continuation';out.mkdir(parents=True,exist_ok=True);events=[]
def mark(name,**kw):
 events.append(dict(name=name,**kw));(out/'ui.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf8');print(name,flush=True)
 if 'ctx' in globals():ctx.storage_state(path=str(out/'state.json'))
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',8823),functools.partial(Quiet,directory=str(root/'tasks/xinshiji/mirror')));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);ctx=b.new_context(storage_state=str(root/'judge/xinshiji/recovery/branches/state.json'),viewport={'width':1366,'height':900});p=ctx.new_page();p.set_default_timeout(10000);dialogs=[];p.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
 def wait(ms=850):p.wait_for_timeout(ms)
 def click(f,s):f.locator(s).click(force='answerQuestion' in s);wait(150)
 def dismiss(f):
  wait(2200)
  for _ in range(12):
   if f.locator('#innerThoughtOverlay').is_visible():f.locator('#innerThoughtOverlay').click();wait(100)
 def start():
  p.goto('http://127.0.0.1:8823/index.html');click(p,'[onclick="showNotice()"]');click(p,'[onclick="acknowledgeNotice()"]');wait(600)
  for _ in range(6):click(p,'#monologueScreen')
  click(p,'#flyerScreen');wait(1000)
 def chat():return p.frame_locator('#gameFrame').frame_locator('.page[data-tab="wechat"] iframe')
 def main():return p.frame_locator('#gameFrame')
 def search(term):
  click(main(),'.fake-search');main().locator('#searchInput').fill(term);click(main(),'.search-result-item');wait(700)
 def shot(name):p.screenshot(path=str(out/(name+'.png')))
 try:
  p.goto('http://127.0.0.1:8823/index.html');click(p,'#continueBtn');wait(1200);f=chat();mark('resumed_native_storage_manager8',step=p.evaluate("localStorage.getItem('sunStep')"))
  # Survey rejection, repeat-card loophole, all-yes and both information choices.
  click(f,'[onclick="goBack()"]');click(f,'[onclick="openSearch()"]');f.locator('#searchInput').fill('新世纪乐园');click(f,'#followBtn');wait();f=chat();click(f,'[onclick="openXiaoyouChat()"]')
  click(f,'#inputBox');f.locator('#inputText').fill('童心未泯');click(f,'[onclick="sendMessage()"]');wait(2100);click(f,'.survey-card')
  for i in range(8):click(f,'[onclick="answerQuestion('+('false' if i==0 else 'true')+')"]')
  wait();assert p.evaluate("localStorage.getItem('surveyDone')")=='true';assert p.evaluate("localStorage.getItem('surveyPassed')") is None;mark('survey_rejection_no_pass')
  click(f,'.survey-card')
  for _ in range(8):click(f,'[onclick="answerQuestion(true)"]')
  wait();assert p.evaluate("localStorage.getItem('surveyPassed')")=='true';mark('survey_card_replay_can_recover_after_rejection')
  click(f,'#optActivity');wait();click(f,'#optAccount');wait(2100);assert f.locator('#sendBtn').is_disabled();shot('survey-password-clue');mark('survey_information_both_choices_and_disable')
  # Member login gate and portrait order within existing legitimate tabs.
  search('新世纪乐园');f=main().frame_locator('.page[data-tab="leyuan"] iframe');click(f,'[onclick="showLoginModal()"]');f.locator('#loginAccount').fill('wrong');f.locator('#loginPassword').fill('wrong');click(f,'[onclick="memberLogin()"]');assert dialogs[-1]=='账号或密码错误';mark('member_wrong_no_navigation')
  f.locator('#loginAccount').fill('cp10040316');f.locator('#loginPassword').fill('19890825');click(f,'[onclick="memberLogin()"]');wait(700);f=main().frame_locator('.page[data-tab="member"] iframe');click(f,'.chatroom-box');assert f.locator('#gongsiText').inner_text()=='';click(f,'#archiveModal');mark('portrait_company_hidden_before_solution')
  click(f,'img[data-id="8"]');click(f,'img[data-id="1"]');assert f.locator('img.lit').count()==0;mark('portrait_wrong_resets')
  for i in [8,6,1,5,3,2,4,7]:click(f,'img[data-id="'+str(i)+'"]')
  assert f.locator('img.lit').count()==8;click(f,'.chatroom-box');assert f.locator('#gongsiText').inner_text()=='向阳花有限公司';shot('portrait-company-revealed');click(f,'#archiveModal');mark('member_and_portrait_correct_reveals_company')
  click(main(),'.browser-tab[data-tab="wechat"]');click(main(),'.browser-tab[data-tab="member"]');f=main().frame_locator('.page[data-tab="member"] iframe');assert f.locator('img.lit').count()==8;mark('portrait_tab_switch_retains_live_progress')
  p.reload();click(p,'#continueBtn');wait(900);assert p.evaluate("localStorage.getItem('sunStep')")=='8';assert p.evaluate("localStorage.getItem('surveyPassed')")=='true';mark('index_continue_preserves_manager_and_survey')
  mark('all_optional_scenarios_passed',dialogs=dialogs)
 except Exception as e:mark('error',error=str(e));shot('error');raise
 finally:b.close();server.shutdown()
