from pathlib import Path
import sys,json,subprocess,time,urllib.request
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from harness.judge import Judge
results=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(channel='msedge',headless=True)
 for kind,port in [('prepared',8832),('game',8833)]:
  root=R/'runs/shiguang-wenrou'/('unpacked-'+kind);game=root/'tasks/shiguang-wenrou/mirror' if kind=='prepared' else root
  out=R/'runs/shiguang-wenrou'/('independent-'+kind);trace=json.loads((out/'ui-trace.json').read_text(encoding='utf-8'));last=next(x for x in reversed(trace) if x['stage']=='ending_corner');state=last['state'];server=subprocess.Popen([sys.executable,str(R/'scripts/serve_static.py'),'--root',str(game),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
   for _ in range(50):
    try:
     urllib.request.urlopen(f'http://127.0.0.1:{port}/',timeout=.5).close();break
    except Exception:time.sleep(.1)
   c=b.new_context(viewport={'width':1366,'height':900},service_workers='block',storage_state={'cookies':[],'origins':[{'origin':f'http://127.0.0.1:{port}','localStorage':[{'name':'totor_gameState_v2','value':state}]}]})
   p=c.new_page();c.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:') else r.abort());p.goto(f'http://127.0.0.1:{port}/pages/ring/LYQ.html');p.locator('#lyq-gate').click();p.wait_for_timeout(1100)
   p.locator('.inv-fab').click();p.wait_for_timeout(800);p.get_by_text('设置',exact=True).click();p.once('dialog',lambda d:d.accept());p.locator('#inv-restart-btn').click();p.wait_for_url('**/prologue.html')
   result=dict(kind=kind,url=p.url,storage=p.evaluate('localStorage.getItem("totor_gameState_v2")'))
   assert result['storage'] is None
   judge=Judge.load(R/'judge/shiguang-wenrou/judge.json','shiguang-wenrou',R);judge.values={k:p.evaluate(v['expr']) for k,v in judge.cfg['hooks'].items()};judge.update(0);assert not judge.checkpoints and not judge.score()['ending_reached'];result['fresh_judge']=judge.score();result['setup']='Completion state seeded from recorded normal UI ending solely to verify reset; reset itself uses normal settings/confirm controls.'
   results.append(result);c.close()
  finally:server.terminate()
 b.close()
(R/'tasks/shiguang-wenrou/audit/reset-delta-verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print('Both independently extracted games: normal UI reset clears completed state; fresh Judge has zero progress/no ending')
