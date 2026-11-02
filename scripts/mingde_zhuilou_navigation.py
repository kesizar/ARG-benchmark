from pathlib import Path
import json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];rows=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True);c=b.new_context();c.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8831') else r.abort());p=c.new_page();p.on('dialog',lambda d:d.accept())
 p.goto('http://127.0.0.1:8831/wechat.html')
 for i in range(p.locator('.chat-item').count()):
  p.locator('.chat-item').nth(i).click();rows.append({'wechat':p.locator('.chat-content.active').get_attribute('id'),'body_characters':len(p.locator('.chat-content.active').inner_text())})
 p.goto('http://127.0.0.1:8831/mingde.html')
 for i in range(p.locator('.nav-item').count()):
  p.locator('.nav-item').nth(i).click();rows.append({'school':p.locator('.page-content.active').get_attribute('id'),'characters':len(p.locator('.page-content.active').inner_text())})
  for button in p.locator('[onclick^="toggleExpand"]:visible').all():
   button.click();button.click()
  for button in p.locator('[onclick^="viewComplaint"]:visible').all():button.click()
 p.goto('http://127.0.0.1:8831/class_chat.html');p.wait_for_timeout(4200);assert p.locator('.send-btn').is_disabled();assert '群公告' in p.locator('#chatMessages').inner_text();rows.append({'class_chat':'disabled sending; two delayed system notices visible'})
 p.goto('http://127.0.0.1:8831/monitoring.html');p.locator('#passwordInput').fill('zhaotiejun');p.locator('#loginBtn').click()
 for slot in ['7-11','11-15']:
  p.locator('[data-time="'+slot+'"]').click()
  for i in range(p.locator('.monitor-card').count()):
   p.locator('.monitor-card').nth(i).click();rows.append({'slot':slot,'monitor':p.locator('#modalTitle').inner_text(),'details':p.locator('#modalDetails').inner_text()});p.locator('#modalClose').click()
 b.close()
(R/'runs/mingde-zhuilou/navigation-coverage.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS',len(rows),'navigation branches')
