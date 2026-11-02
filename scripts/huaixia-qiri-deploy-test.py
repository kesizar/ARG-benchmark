import hashlib, json, subprocess, sys, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

base=Path('runs/huaixia-qiri/deploy-check').resolve()
game=base/'game'; evaluation=base/'evaluation'
game.mkdir(parents=True,exist_ok=True); evaluation.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile('packs/huaixia-qiri.game.zip') as z: z.extractall(game)
with zipfile.ZipFile('packs/huaixia-qiri.prepared.zip') as z: z.extractall(evaluation)
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (game/'index.html',evaluation/'tasks/huaixia-qiri/mirror/index.html')}
for name in ('huaixia-qiri','huaixia-qiri-hidden'):
 cfg=evaluation/f'configs/{name}.json'; c=json.loads(cfg.read_text(encoding='utf-8'))
 c['entry_url']=c['entry_url'].replace('8811','8813');c['allow_hosts']=['127.0.0.1:8813']
 c['local_serve']['port']=8813;c['local_serve']['ready_url']=c['local_serve']['ready_url'].replace('8811','8813');c['local_serve']['command'][-1]='8813'
 cfg.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
res={'hashes':hashes,'test_config_change':'Only local test port changed 8811 to 8813 in extracted evaluator config.'}
p=subprocess.Popen([sys.executable,'-m','http.server','8812','--bind','127.0.0.1','--directory',str(game)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 time.sleep(1)
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='msedge',headless=True,args=['--no-proxy-server'])
  page=b.new_page(viewport={'width':1280,'height':1000})
  blocked=[]; page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8812/') else (blocked.append(r.request.url),r.abort()))
  resp=page.goto('http://127.0.0.1:8812/index.html',wait_until='domcontentloaded',timeout=12000)
  page.get_by_role('button',name='新的七日').click(timeout=6000)
  res['game']={'http_status':resp.status,'perspective_visible':page.get_by_text('选择视角').is_visible(),'blocked':blocked}
  b.close()
except Exception as e: res['game_error']=str(e)
finally: p.terminate()
try:
 res['evaluation']={}
 for name in ('huaixia-qiri','huaixia-qiri-hidden'):
  run=subprocess.run([sys.executable,'scripts/run_one.py','--config',f'configs/{name}.json','--policy','script'],cwd=evaluation,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
  res['evaluation'][name]={'exit_code':run.returncode,'stdout':run.stdout[-4000:],'stderr':run.stderr[-4000:]}
except Exception as e: res['evaluation_error']=str(e)
Path('runs/huaixia-qiri/deployment.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(res,ensure_ascii=True))
