from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from harness.judge import Judge
rows=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True)
 for keys,tier in [(['江楠'],'bad'),(['李阳'],'bad'),(['赔偿协议'],'normal'),(['李阳','赔偿协议'],'good')]:
  c=b.new_context();c.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8831') else r.abort());p=c.new_page();p.on('dialog',lambda d:d.accept());p.goto('http://127.0.0.1:8831/index.html');p.locator('#passwordInput').fill('xdemydmm');p.locator('#submitPassword').click();p.wait_for_url('**/desk.html')
  with c.expect_page() as pop:p.get_by_text('证据检索',exact=True).first.click()
  e=pop.value;e.wait_for_load_state();e.on('dialog',lambda d:d.accept())
  for key in keys:e.locator('#searchInput').fill(key);e.locator('#searchBtn').click()
  j=Judge.load(R/'judge/mingde-zhuilou/judge.json','mingde-zhuilou',R)
  def score():
   expr='({' + ','.join(json.dumps(k)+':('+v['expr']+')' for k,v in j.cfg['hooks'].items()) + '})';j.values=e.evaluate(expr);j.update(0);return j.score()
  assert not score()['ending_reached'];e.locator('#openReportBtn').click()
  for key in keys:e.locator('[data-keyword="'+key+'"] input').check()
  e.locator('#submitReportBtn').click();s=score();assert s['ending_tier']==tier and not s['diagnostic'];rows.append({'selection':keys,'score':s,'puzzle_documents_opened':0});e.screenshot(path=str(R/'runs/mingde-zhuilou'/('shortcut-'+tier+str(len(keys))+'.png')),full_page=True);e.locator('.ending-page:visible .restart-btn').click();fresh=Judge.load(R/'judge/mingde-zhuilou/judge.json','mingde-zhuilou',R);fresh.values=e.evaluate('({' + ','.join(json.dumps(k)+':('+v['expr']+')' for k,v in fresh.cfg['hooks'].items()) + '})');fresh.update(0);assert not fresh.checkpoints and not fresh.score()['ending_reached'];c.close()
 b.close()
(R/'runs/mingde-zhuilou/minimal-route-proof.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS 4 minimal routes without document puzzle gates')
