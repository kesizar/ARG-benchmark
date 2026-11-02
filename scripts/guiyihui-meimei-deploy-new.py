import pathlib,zipfile,json,hashlib,subprocess,sys,os,asyncio,traceback
from playwright.async_api import async_playwright
root=pathlib.Path('.').resolve(); test=root/'runs/guiyihui-meimei-independent-4'; test.mkdir(parents=True,exist_ok=True); game=test/'game'; evaldir=test/'evaluation';game.mkdir(exist_ok=True);evaldir.mkdir(exist_ok=True);log={}
try:
 for name,dest in [('resources',game),('prepared',evaldir)]:
  zpath=root/f'packs/guiyihui-meimei.{name}.zip'
  with zipfile.ZipFile(zpath) as z:
   for info in z.infolist():
    target=(dest/info.filename).resolve();assert target.is_relative_to(dest.resolve())
   z.extractall(dest)
  log[name+'_archive_sha256']=hashlib.sha256(zpath.read_bytes()).hexdigest()
 # Verify every member against embedded manifest.
 m=json.loads((game/'RESOURCE-MANIFEST.json').read_text(encoding='utf-8'));assert all(hashlib.sha256((game/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in m['files']); log['resource_hashes_match']=True
 m=json.loads((evaldir/'BUNDLE-MANIFEST.json').read_text(encoding='utf-8'));assert all(hashlib.sha256((evaldir/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in m['files']);log['prepared_hashes_match']=True
 proc=subprocess.Popen([sys.executable,'-m','http.server','8822','--bind','127.0.0.1','--directory',str(game)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 async def visit():
  async with async_playwright() as p:
   b=await p.chromium.launch(channel='msedge',headless=True);c=await b.new_context();page=await c.new_page();bad=[]
   await c.route('**/*',lambda route:route.continue_() if route.request.url.startswith('http://127.0.0.1:8822/') else route.abort())
   page.on('requestfailed',lambda req:bad.append(req.url))
   for i in range(20):
    try:await page.goto('http://127.0.0.1:8822/index.html',wait_until='load');break
    except:await asyncio.sleep(.2)
   assert await page.locator('#panel-level-indicator').inner_text()=='01/50'; assert await page.locator('#btn-validate').is_visible()
   await page.locator('#solver-text-input').fill('0911');await page.locator('#btn-validate').click();assert (await page.locator('#panel-level-indicator').inner_text())=='02/50'
   log['resource_independent_ui']='level 1 normal input and validation pass';log['resource_failed_requests']=bad;await b.close()
 try:asyncio.run(visit())
 finally:proc.terminate();proc.wait()
 cfg=evaldir/'configs/guiyihui-meimei.json';data=json.loads(cfg.read_text(encoding='utf-8'));data['entry_url']=data['entry_url'].replace('8821','8823');data['allow_hosts']=['127.0.0.1:8823'];data['local_serve']['port']=8823;data['local_serve']['ready_url']=data['entry_url'];data['local_serve']['command'][-1]='8823';cfg.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 env=os.environ.copy();env['PYTHONIOENCODING']='utf-8';res=subprocess.run([sys.executable,'scripts/run_one.py','--config','configs/guiyihui-meimei.json','--policy','script'],cwd=evaldir,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=120);(test/'prepared-run.log').write_text(res.stdout+'\n'+res.stderr,encoding='utf-8');log['prepared_run_exit']=res.returncode;assert res.returncode==0
 summaries=list((evaldir/'runs').rglob('summary.json'));assert len(summaries)==1;summary=json.loads(summaries[0].read_text(encoding='utf-8'));log['prepared_summary']=str(summaries[0].relative_to(root));log['prepared_ended_reason']=summary.get('ended_reason');log['prepared_judge_error']=summary.get('judge_error');assert log['prepared_ended_reason']!='error';log['status']='pass'
except Exception:log['status']='fail';log['error']=traceback.format_exc()
(root/'judge/guiyihui-meimei/deployment.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(log,ensure_ascii=True,indent=2));sys.exit(0 if log['status']=='pass' else 1)
