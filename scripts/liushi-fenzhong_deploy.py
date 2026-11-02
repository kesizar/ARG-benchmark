"""Independent extraction and UI verification of both package boundaries."""
import asyncio,hashlib,json,subprocess,sys,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));T='liushi-fenzhong';D=R/'runs'/f'{T}-deployment'/str(int(time.time()));D.mkdir(parents=True)
from harness.browser_harness import BrowserHarness
from harness.serve_local import LocalServer
async def main():
 report={'deployment_root':str(D),'same_os':'Windows; not cross-OS test','base_environment':'external Python3.11 environment, installed Playwright and Edge; not bundled','packages':{}}
 for kind in ['resources','prepared']:
  root=D/kind;root.mkdir();archive=R/'packs'/f'{T}.{kind}.zip'
  with zipfile.ZipFile(archive) as z:
   assert z.testzip() is None;assert all(not p.startswith(('/','\\')) and '..' not in Path(p).parts for p in z.namelist());z.extractall(root)
  report['packages'][kind]={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'extract_root':str(root),'html_sha256':hashlib.sha256((root/f'tasks/{T}/mirror/index.html').read_bytes()).hexdigest()}
  if kind=='prepared':
   manifest=json.loads((root/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'))
   for f in manifest['files']:assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
   report['packages'][kind]['manifest_verified_files']=len(manifest['files'])
  else:assert not (root/'judge').exists() and not (root/'configs').exists()
 # Resource-only archive uses the explicitly external generic static server and browser tester.
 root=D/'resources';c=json.loads((R/f'configs/{T}.json').read_text(encoding='utf-8'));c['entry_url']='http://127.0.0.1:8811/index.html';c['settle_ms']=30;c['local_serve']['command'][1]=str(R/'scripts/serve_static.py');s=LocalServer();h=BrowserHarness(c,D/'resources-ui')
 try:
  s.start(c,root,D/'resource-server.log');await h.start();await h.reset();page=h.page;await page.locator('#btnStart').click()
  for i in [0,1]:
   await page.locator(f'#sceneGrid .card:nth-child({i+1})').click();await page.locator('#pActions .sr').click();await page.locator('#panePerson .x').click()
  await page.locator('#sceneGrid .card:nth-child(1)').click();await page.locator('#pActions .acc').click()
  for _ in range(5):
   n=await page.evaluate('quizData[quizStep].opts.findIndex(x=>x===quizData[quizStep].a)');await page.locator(f'#quizOpts button:nth-child({n+1})').click()
  assert await page.locator('#endTitle').inner_text()=='你抓住了凶手';await page.screenshot(path=str(D/'resources-win.png'),full_page=True)
  await page.reload();await page.locator('#btnStart').click();assert await page.evaluate('state.notes.length===0 && quizTarget===null && state.round===1')
  private=await h.context.request.get('http://127.0.0.1:8811/judge/liushi-fenzhong/judge.json');assert private.status==404
  report['packages']['resources'].update(ui_win=True,fresh_reload_reset=True,judge_not_served_status=private.status,mode='normal locator.click; private read-only answer oracle; no state or clock mutation')
 finally:await h.close();s.stop()
 # Actual runner and private verifier execute from the independent evaluator tree.
 root=D/'prepared';log=D/'prepared-acceptance.log'
 with log.open('w',encoding='utf-8') as stream:
  proc=subprocess.run([sys.executable,f'judge/{T}/verify_sample.py','--port','8813','--quick'],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
 report['packages']['prepared']['verifier_exit_code']=proc.returncode
 acc=root/f'judge/{T}/verification/acceptance.json';report['packages']['prepared']['acceptance_path']=str(acc)
 if acc.exists():report['packages']['prepared']['acceptance']=json.loads(acc.read_text(encoding='utf-8'))
 report['pass']=proc.returncode==0 and report['packages']['prepared'].get('acceptance',{}).get('pass') is True
 (R/'judge'/T/'deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');assert report['pass'],str(log)
 print('Independent packages verified',D,flush=True)
if __name__=='__main__':asyncio.run(main())
