import asyncio,json,sys,subprocess,zipfile,hashlib,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'judge/qingmiao-zhongxue/verification';D=R/'runs/qingmiao-zhongxue-independent';D.mkdir(exist_ok=True)
CODE=r'''
import asyncio,json,sys
from pathlib import Path
from harness.browser_harness import BrowserHarness
from harness.judge import Judge
async def main():
 r=Path.cwd();c=json.loads(Path('configs/qingmiao-zhongxue.json').read_text(encoding='utf8'));h=BrowserHarness(c,r/'ui');(r/'ui').mkdir(exist_ok=True);await h.start();await h.reset();j=Judge.load(r/c['judge_path'],c['id'],r);await j.read(h);j.update(0);assert not j.score()['ending_reached'];assert not j.score()['diagnostic'];await h.page.locator('.start-game-btn').click();await h.page.wait_for_timeout(500);h.page=h.context.pages[-1];await h.page.bring_to_front();await h.page.wait_for_load_state();await h.page.locator('#closeEmailBtn').click();await h.page.wait_for_timeout(500);await j.read(h);j.update(1);assert not j.score()['diagnostic'];await h.page.locator('#messageInput').fill('wrong');await h.page.locator('#sendButton').click();await j.read(h);j.update(2);assert not j.score()['diagnostic'];await h.page.screenshot(path=str(r/'ui/entry.png'));await h.reset();j=Judge.load(r/c['judge_path'],c['id'],r);await j.read(h);j.update(0);assert not j.score()['diagnostic'];assert not j.score()['ending_reached'];await h.close();print(json.dumps({'pass':True,'cwd':str(r),'entry':c['entry_url'],'judge_import':str(__import__('harness.judge',fromlist=['']).__file__),'fresh_reset':True}))
asyncio.run(main())
'''
results=[]
for typ,archive,port in [('game','qingmiao-zhongxue.zip',8812),('prepared','qingmiao-zhongxue.prepared.zip',8813)]:
 dest=D/typ;dest.mkdir(exist_ok=True)
 with zipfile.ZipFile(R/'packs'/archive) as z:
  z.extractall(dest);names=z.namelist()
  if typ=='game':assert all(n.startswith('tasks/qingmiao-zhongxue/mirror/') for n in names)
 if typ=='prepared':
  m=json.loads((dest/'BUNDLE-MANIFEST.json').read_text(encoding='utf8'));assert all(hashlib.sha256((dest/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in m['files'])
 else:
  import shutil
  for folder in ['harness','configs','judge','scripts']:
   if folder=='harness':shutil.copytree(R/folder,dest/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','tests','test_*'))
   else:(dest/folder).mkdir(exist_ok=True)
  shutil.copy2(R/'configs/qingmiao-zhongxue.json',dest/'configs');(dest/'judge/qingmiao-zhongxue').mkdir(exist_ok=True);shutil.copy2(R/'judge/qingmiao-zhongxue/judge.json',dest/'judge/qingmiao-zhongxue');shutil.copy2(R/'scripts/serve_static.py',dest/'scripts')
 cfg=dest/'configs/qingmiao-zhongxue.json';c=json.loads(cfg.read_text(encoding='utf8'));c['entry_url']=c['entry_url'].replace('8811',str(port));c['allow_hosts']=[f'127.0.0.1:{port}'];cfg.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8');(dest/'check.py').write_text(CODE,encoding='utf8')
 log=(E/f'{typ}-independent-server.log').open('w');proc=subprocess.Popen([sys.executable,'scripts/serve_static.py','--root','tasks/qingmiao-zhongxue/mirror','--port',str(port)],cwd=dest,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 try:
  import time;time.sleep(1);p=subprocess.run([sys.executable,'check.py'],cwd=dest,capture_output=True,text=True,encoding='utf8',timeout=90);results.append({'type':typ,'pass':p.returncode==0,'stdout':p.stdout,'stderr':p.stderr,'archive_sha256':hashlib.sha256((R/'packs'/archive).read_bytes()).hexdigest(),'file_count':len(names),'game_only_evaluator_note':'Game archive contains assets only; external evaluator copied separately for deployment verification.' if typ=='game' else 'Evaluator imported from extracted prepared bundle.'})
 finally:proc.terminate();proc.wait();log.close()
(E/'independent-deployment.json').write_text(json.dumps({'pass':all(x['pass'] for x in results),'results':results,'scope':'Independent directories/ports and fresh contexts on same Windows Python/installed Edge; not cross-OS certification.'},ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(results,ensure_ascii=False))
