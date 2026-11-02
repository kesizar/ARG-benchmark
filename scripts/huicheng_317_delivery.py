from pathlib import Path
import asyncio,hashlib,json,subprocess,sys,tempfile,zipfile
import urllib.request
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from playwright.async_api import async_playwright
from harness.judge import Judge
from huicheng_317_accept import H
T=R/'tasks/huicheng-317';A=T/'audit';ID='huicheng-317'

def package():
    manifest=[]
    for p in (T/'mirror').rglob('*'):
        if p.is_file():manifest.append(dict(path=p.relative_to(T/'mirror').as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    provenance=dict(record_id='base664:0358',task_id=ID,original_entry='https://ftkcme7t.html2.link/',snapshot='ARG-packs/verify-416/bodies/358.html',snapshot_bytes=52534,snapshot_sha256=hashlib.sha256((A/'original.html').read_bytes()).hexdigest(),dependencies=json.loads((A/'resource-probe.json').read_text(encoding='utf-8')),modifications='Cosmetic installed-font fallback; publisher chrome/SDK/telemetry/favicon/CSP removed; media URLs localized. Game IIFE unchanged.',assets=manifest,account_requirement='none',model_api_used=False)
    (T/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(R/'packs'/f'{ID}.resources.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in (T/'mirror').rglob('*'):
            if p.is_file():z.write(p,p.relative_to(T/'mirror').as_posix())
    subprocess.run([sys.executable,str(R/'scripts/build_prepared_bundle.py'),'--task',ID],check=True)

async def main():
    results=[]
    async with async_playwright() as pw:
      browser=await pw.chromium.launch(channel='msedge',headless=True)
      for kind,port in [('resources',8822),('prepared',8823)]:
        archive=R/'packs'/f'{ID}.{kind}.zip';dest=Path(tempfile.mkdtemp(prefix=f'{ID}-{kind}-'))
        with zipfile.ZipFile(archive) as z:z.extractall(dest)
        web=dest if kind=='resources' else dest/'tasks'/ID/'mirror'
        server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(web)],cwd=str(dest),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
          try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/index.html',timeout=1) as ready:assert ready.status==200
            break
          except Exception:await asyncio.sleep(.1)
        ctx=await browser.new_context(viewport={'width':1366,'height':900},reduced_motion='reduce');p=await ctx.new_page();requests=[];errors=[]
        p.on('request',lambda req:requests.append(req.url));p.on('pageerror',lambda e:errors.append(str(e)))
        try:
          await p.clock.install();await p.goto(f'http://127.0.0.1:{port}/index.html');await p.clock.run_for(2500)
          async def c(t):await p.get_by_role('button',name=t,exact=True).click();await p.clock.run_for(25000)
          await p.locator('#boot').click();await p.clock.run_for(25000);await c('02走向大厅')
          judge=Judge.load((R if kind=='resources' else dest)/'judge'/ID/'judge.json',ID,dest);assert not any((await judge.read(H(p))).values())
          await c('③维修间 · 档案室');await c('①输入四位密码');await p.locator('#miniInput').fill('0000');await p.locator('#miniOk').click();assert not (await judge.read(H(p)))['archive_lock']
          await p.locator('#miniInput').fill('2600');await p.locator('#miniOk').click();assert (await judge.read(H(p)))['archive_lock'];await p.clock.run_for(25000);await c('③只看，不碰')
          await c('②大厅尽头 · 结着雾的窗');await c('擦开玻璃，看出去');await c('②转身离开，不再看');await c('→我感觉知道得够多了');await c('①走向车门');await c('它朝你伸出手');await c('C烧掉中枢站总档，掐断循环')
          vals=await judge.read(H(p));assert vals['end_c'];judge.update(1);score=judge.score();assert score['route_id']=='end_c' and score['ending_tier']=='normal';await p.screenshot(path=str(A/f'{kind}-independent-C.png'))
          await c('重头再来');assert not any((await judge.read(H(p))).values())
          for filename in ['../judge/huicheng-317/judge.json','/judge/huicheng-317/judge.json','/configs/huicheng-317.json']:
              response=await p.request.get(f'http://127.0.0.1:{port}/{filename.lstrip("/")}');assert response.status==404
          assert not errors and all(u.startswith(f'http://127.0.0.1:{port}/') or u.startswith('data:') for u in requests)
          integrity=[]
          for x in json.loads((T/'provenance.json').read_text(encoding='utf-8'))['assets']:integrity.append(hashlib.sha256((web/x['path']).read_bytes()).hexdigest()==x['sha256'])
          assert all(integrity)
          results.append(dict(kind=kind,port=port,extraction=str(dest),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),asset_hashes_match=True,initial_negative=True,wrong_negative=True,password_positive=True,end_c_positive=True,replay_negative=True,judge_not_served=True,external_requests=[],page_errors=errors,score=score,prerequisites='Windows Python3.11 / installed Edge; not cross-OS'))
        finally:await ctx.close();server.terminate()
      await browser.close()
    (A/'independent-delivery.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print('Independent packages passed',len(results))

if __name__=='__main__':
    if '--package' in sys.argv:package()
    else:asyncio.run(main())
