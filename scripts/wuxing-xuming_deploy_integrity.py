from pathlib import Path
import json,subprocess,sys,time,httpx,hashlib
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'runs/wuxing-xuming/delivery';G=D/'game-v3/tasks/wuxing-xuming/mirror';E=D/'evaluator-v3';out={'resource_hashes':[]}
p=subprocess.Popen([sys.executable,'-m','http.server','8831','--bind','127.0.0.1','--directory',str(G)],cwd=D/'game-v3',stdout=open(R/'runs/wuxing-xuming/deployment-media-server.log','w'),stderr=subprocess.STDOUT)
try:
 time.sleep(.6)
 for f in G.glob('*'):
  if not f.is_file():continue
  q=httpx.get('http://127.0.0.1:8831/'+f.name);assert q.status_code==200 and q.content==f.read_bytes(),f.name;out['resource_hashes'].append({'path':f.name,'sha256':hashlib.sha256(q.content).hexdigest(),'bytes':len(q.content)})
 out['not_served']={s:httpx.get('http://127.0.0.1:8831/'+s).status_code for s in ['configs/wuxing-xuming.json','judge/wuxing-xuming/judge.json','harness/judge.py']};assert all(x==404 for x in out['not_served'].values())
 manifest=json.loads((E/'BUNDLE-MANIFEST.json').read_text(encoding='utf8'));out['evaluator_hashed_files']=len(manifest['files']);assert all(hashlib.sha256((E/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in manifest['files'])
 with sync_playwright() as w:
  b=w.chromium.launch(channel='msedge',headless=True,timeout=15000);c=b.new_context();page=c.new_page();page.goto('http://127.0.0.1:8831/');page.wait_for_function("document.getElementById('vhsVideo').readyState>=1");out['video']=page.locator('#vhsVideo').evaluate('(v)=>({width:v.videoWidth,height:v.videoHeight,duration:v.duration,error:v.error,readyState:v.readyState})');assert out['video']['width']>0 and out['video']['error'] is None;out['browser']=b.version;b.close()
 out['passed']=True;(R/'judge/wuxing-xuming/deployment-integrity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('PASS resources',len(out['resource_hashes']),'video',out['video'])
finally:p.terminate();p.wait(timeout=10)
